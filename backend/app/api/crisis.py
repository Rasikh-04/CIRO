from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.crisis import CrisisEventSchema, OperationalPictureSchema
from app.schemas.simulation import SimulationResultSchema
from app.models.crisis import Crisis
from app.models.operational_picture import OperationalPicture
from app.models.dispatch import DispatchOrder
from app.models.simulation import Simulation
from app.ws.manager import manager
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from datetime import datetime, timezone

# In-memory cache for complete dashboard states posted by Agent 6
_dashboard_snapshots: dict = {}

router = APIRouter()

VALID_TRANSITIONS = {
    "initiated":  ["detected"],
    "detected":   ["analyzed"],
    "analyzed":   ["dispatched"],
    "dispatched": ["simulated"],
    "simulated":  ["resolved"],
}

@router.post("/crisis/detected")
def crisis_detected(payload: CrisisEventSchema, db: Session = Depends(get_db)):
    existing = db.query(Crisis).filter(Crisis.id == payload.crisis_id).first()
    if existing:
        return {"crisis_id": payload.crisis_id, "skipped": True}
    point = from_shape(Point(payload.location.lng, payload.location.lat), srid=4326)
    db_crisis = Crisis(
        id               = payload.crisis_id,
        type             = payload.type,
        location         = point,
        location_name    = payload.location.primary,
        affected_radius  = payload.location.affected_radius_km,
        severity         = payload.severity,
        confidence       = payload.confidence_score,
        confidence_label = payload.confidence,
        reasoning        = payload.reasoning,
        status           = "detected",
        detected_at      = payload.detected_at,
        updated_at       = datetime.now(timezone.utc),
    )
    db.add(db_crisis)
    db.commit()
    return {"crisis_id": payload.crisis_id}

@router.get("/crisis/latest")
def get_latest_crisis(db: Session = Depends(get_db)):
    crisis = db.query(Crisis).order_by(Crisis.detected_at.desc()).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="No crisis found")
    shape = to_shape(crisis.location) if crisis.location else None
    lat = shape.y if shape else 33.6844
    lng = shape.x if shape else 73.0479
    return {
        "crisis_id":        crisis.id,
        "type":             crisis.type,
        "severity":         crisis.severity,
        "confidence":       crisis.confidence_label or "high",
        "confidence_score": crisis.confidence or 0.89,
        "reasoning":        crisis.reasoning or "",
        "contributing_signals": [],
        "status":           "confirmed",
        "detected_at":      crisis.detected_at.isoformat() if crisis.detected_at else "",
        "location": {
            "primary":            crisis.location_name,
            "lat":                lat,
            "lng":                lng,
            "affected_radius_km": crisis.affected_radius or 2.5,
        },
    }

@router.post("/crisis/operational")
async def crisis_operational(payload: OperationalPictureSchema, db: Session = Depends(get_db)):
    crisis = db.query(Crisis).filter(Crisis.id == payload.crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    if "analyzed" not in VALID_TRANSITIONS.get(crisis.status, []):
        raise HTTPException(status_code=400, detail=f"Cannot transition from '{crisis.status}' to 'analyzed'")
    op_pic = OperationalPicture(
        crisis_id          = payload.crisis_id,
        road_closures      = [rc.dict() for rc in payload.operational_picture.road_closures],
        nearby_facilities  = [f.dict() for f in payload.operational_picture.nearby_facilities],
        population_at_risk = payload.operational_picture.population_at_risk,
        data_gaps          = payload.operational_picture.data_gaps,
        generated_at       = payload.generated_at,
    )
    db.add(op_pic)
    crisis.status = "analyzed"
    crisis.updated_at = datetime.now(timezone.utc)
    db.commit()
    await manager.broadcast({"stage": "analyzed", "crisis_id": payload.crisis_id}, payload.crisis_id)
    return {"ok": True}

@router.post("/crisis/dispatch")
async def crisis_dispatch(payload: dict, db: Session = Depends(get_db)):
    crisis_id = payload.get("crisis_id")
    crisis = db.query(Crisis).filter(Crisis.id == crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    if "dispatched" not in VALID_TRANSITIONS.get(crisis.status, []):
        raise HTTPException(status_code=400, detail=f"Cannot transition from '{crisis.status}' to 'dispatched'")
    for order in payload.get("dispatch_plan", {}).get("dispatch_orders", []):
        dest_geo = None
        if order.get("destination_lat") and order.get("destination_lng"):
            dest_geo = from_shape(Point(order["destination_lng"], order["destination_lat"]), srid=4326)
        db_order = DispatchOrder(
            id              = order["order_id"],
            crisis_id       = crisis_id,
            unit_name       = order["unit"],
            unit_type       = order["unit_type"],
            destination     = order["destination"],
            destination_geo = dest_geo,
            reason          = order["reason"],
            eta_minutes     = order["eta_minutes"],
            status          = "pending",
            created_at      = datetime.now(timezone.utc),
        )
        db.add(db_order)
    crisis.status = "dispatched"
    crisis.updated_at = datetime.now(timezone.utc)
    db.commit()
    await manager.broadcast({"stage": "dispatched", "crisis_id": crisis_id}, crisis_id)
    return {"ok": True}

@router.post("/crisis/simulation")
async def crisis_simulation(payload: SimulationResultSchema, db: Session = Depends(get_db)):
    crisis = db.query(Crisis).filter(Crisis.id == payload.crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    if "simulated" not in VALID_TRANSITIONS.get(crisis.status, []):
        raise HTTPException(status_code=400, detail=f"Cannot transition from '{crisis.status}' to 'simulated'")
    sim = Simulation(
        crisis_id                = payload.crisis_id,
        routes                   = [r.dict() for r in payload.simulation.routes],
        traffic_before           = payload.simulation.traffic_state.before,
        traffic_after            = payload.simulation.traffic_state.after,
        congestion_reduction_pct = payload.simulation.traffic_state.congestion_reduction_pct,
        emergency_ticket_id      = payload.simulation.emergency_ticket.ticket_id,
        public_alerts            = [a.dict() for a in payload.simulation.public_alerts],
        created_at               = payload.created_at,
    )
    db.add(sim)
    crisis.status = "simulated"
    crisis.updated_at = datetime.now(timezone.utc)
    db.commit()
    await manager.broadcast({"stage": "simulated", "crisis_id": payload.crisis_id}, payload.crisis_id)
    return {"ok": True}

@router.post("/crisis/complete")
async def crisis_complete(payload: dict, db: Session = Depends(get_db)):
    crisis_id = payload.get("crisis_id")
    if crisis_id:
        _dashboard_snapshots[crisis_id] = payload
    crisis = db.query(Crisis).filter(Crisis.id == crisis_id).first()
    if crisis:
        crisis.status = "simulated"
        crisis.updated_at = datetime.now(timezone.utc)
        db.commit()
    await manager.broadcast(payload, crisis_id)
    return {"ok": True}

@router.get("/crisis/active")
def get_active_crises(db: Session = Depends(get_db)):
    active = db.query(Crisis).filter(Crisis.status.notin_(["resolved"])).all()
    result = []
    for c in active:
        shape = to_shape(c.location) if c.location else None
        lat = shape.y if shape else 33.6844
        lng = shape.x if shape else 73.0479
        op_pic = db.query(OperationalPicture).filter(OperationalPicture.crisis_id == c.id).first()
        result.append({
            "crisis_id":          c.id,
            "type":               c.type,
            "location_name":      c.location_name,
            "location": {
                "primary":            c.location_name,
                "lat":                lat,
                "lng":                lng,
                "affected_radius_km": c.affected_radius or 2.5,
            },
            "severity":           c.severity,
            "stage":              c.status,
            "detected_at":        c.detected_at.isoformat() if c.detected_at else "",
            "affected_population": op_pic.population_at_risk if op_pic else 12000,
            "timestamp":          c.detected_at.isoformat() if c.detected_at else "",
        })
    return result

@router.get("/crisis/full/{crisis_id}")
def get_full_crisis(crisis_id: str, db: Session = Depends(get_db)):
    # Return the complete snapshot if Agent 6 has already posted it
    if crisis_id in _dashboard_snapshots:
        return _dashboard_snapshots[crisis_id]

    crisis = db.query(Crisis).filter(Crisis.id == crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Not found")

    shape = to_shape(crisis.location) if crisis.location else None
    lat = shape.y if shape else 33.6844
    lng = shape.x if shape else 73.0479

    op_pic = db.query(OperationalPicture).filter(OperationalPicture.crisis_id == crisis_id).first()
    orders = db.query(DispatchOrder).filter(DispatchOrder.crisis_id == crisis_id).all()
    sim    = db.query(Simulation).filter(Simulation.crisis_id == crisis_id).first()

    return {
        "crisis_id": crisis.id,
        "stage":     crisis.status,
        "crisis": {
            "crisis_id":  crisis.id,
            "type":       crisis.type,
            "severity":   crisis.severity,
            "confidence": crisis.confidence_label or "high",
            "confidence_score": crisis.confidence or 0.89,
            "reasoning":  crisis.reasoning or "",
            "contributing_signals": [],
            "status":     "confirmed",
            "detected_at": crisis.detected_at.isoformat() if crisis.detected_at else "",
            "location": {
                "primary":            crisis.location_name,
                "lat":                lat,
                "lng":                lng,
                "affected_radius_km": crisis.affected_radius or 2.5,
            },
        },
        "operational_picture": {
            "crisis_id": crisis.id,
            "operational_picture": {
                "affected_zone":    {"center": [lat, lng], "radius_km": crisis.affected_radius or 2.5},
                "road_closures":    op_pic.road_closures if op_pic else [],
                "nearby_facilities": op_pic.nearby_facilities if op_pic else [],
                "data_gaps":        op_pic.data_gaps if op_pic else [],
                "population_at_risk": op_pic.population_at_risk if op_pic else 0,
            },
            "generated_at": op_pic.generated_at.isoformat() if op_pic and op_pic.generated_at else "",
        } if op_pic else {},
        "dispatch_plan": {
            "crisis_id": crisis.id,
            "dispatch_plan": {
                "priority_ranking": [],
                "dispatch_orders": [
                    {
                        "order_id":        o.id,
                        "unit":            o.unit_name,
                        "unit_type":       o.unit_type,
                        "destination":     o.destination,
                        "destination_lat": 0,
                        "destination_lng": 0,
                        "origin_lat":      0,
                        "origin_lng":      0,
                        "reason":          o.reason,
                        "eta_minutes":     o.eta_minutes,
                    }
                    for o in orders
                ],
                "resource_gaps": [],
            },
            "generated_at": "",
        } if orders else {},
        "simulation": {
            "crisis_id": crisis.id,
            "simulation": {
                "routes":  sim.routes if sim else [],
                "traffic_state": {
                    "before": sim.traffic_before if sim else {},
                    "after":  sim.traffic_after  if sim else {},
                    "congestion_reduction_pct": sim.congestion_reduction_pct if sim else 0,
                },
                "emergency_ticket": {
                    "ticket_id": sim.emergency_ticket_id if sim else "",
                    "created_at": sim.created_at.isoformat() if sim and sim.created_at else "",
                    "status": "issued",
                    "units": [],
                },
                "public_alerts": sim.public_alerts if sim else [],
            },
            "created_at": sim.created_at.isoformat() if sim and sim.created_at else "",
        } if sim else {},
        "sitrep_text": "",
        "agent_trace_summary": [],
        "last_updated": crisis.updated_at.isoformat() if crisis.updated_at else "",
    }

@router.get("/crisis/{crisis_id}")
def get_crisis(crisis_id: str, db: Session = Depends(get_db)):
    if crisis_id in _dashboard_snapshots:
        return _dashboard_snapshots[crisis_id]

    crisis = db.query(Crisis).filter(Crisis.id == crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Not found")

    shape = to_shape(crisis.location) if crisis.location else None
    lat = shape.y if shape else 33.6844
    lng = shape.x if shape else 73.0479

    return {
        "crisis_id": crisis.id,
        "stage":     crisis.status,
        "crisis": {
            "crisis_id":  crisis.id,
            "type":       crisis.type,
            "severity":   crisis.severity,
            "confidence": crisis.confidence_label or "high",
            "confidence_score": crisis.confidence or 0.89,
            "reasoning":  crisis.reasoning or "",
            "contributing_signals": [],
            "status":     "confirmed",
            "detected_at": crisis.detected_at.isoformat() if crisis.detected_at else "",
            "location": {
                "primary":            crisis.location_name,
                "lat":                lat,
                "lng":                lng,
                "affected_radius_km": crisis.affected_radius or 2.5,
            },
        },
        "operational_picture": {},
        "dispatch_plan": {},
        "simulation": {},
        "sitrep_text": "",
        "agent_trace_summary": [],
        "last_updated": crisis.updated_at.isoformat() if crisis.updated_at else "",
    }
