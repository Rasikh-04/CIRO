from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.crisis import CrisisEventSchema, OperationalPictureSchema
from app.schemas.simulation import SimulationResultSchema
from app.models.crisis import Crisis
from app.models.operational_picture import OperationalPicture
from app.ws.manager import manager
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from datetime import datetime, timezone

# In-memory cache for complete dashboard states posted by Agent 6
_dashboard_snapshots: dict = {}

router = APIRouter()


def _serialize_crisis(c: Crisis) -> dict:
    try:
        pt = to_shape(c.location)
        lat, lng = pt.y, pt.x
    except Exception:
        lat, lng = 0.0, 0.0
    return {
        "crisis_id":            c.id,
        "type":                 c.type,
        "location": {
            "primary":           c.location_name,
            "affected_radius_km": c.affected_radius,
            "lat":               lat,
            "lng":               lng,
        },
        "severity":             c.severity,
        "confidence":           c.confidence_label,
        "confidence_score":     c.confidence,
        "reasoning":            c.reasoning,
        "contributing_signals": c.contributing_signals or [],
        "status":               c.status,
        "detected_at":          c.detected_at.isoformat() if c.detected_at else None,
    }


# ── Reads ─────────────────────────────────────────────────────────────────────

@router.get("/crisis/latest")
def get_latest_crisis(db: Session = Depends(get_db)):
    crisis = db.query(Crisis).order_by(Crisis.detected_at.desc()).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="No crisis found")
    return _serialize_crisis(crisis)


@router.get("/crisis/full/{crisis_id}")
def get_full_crisis(crisis_id: str, db: Session = Depends(get_db)):
    """Returns the full DashboardState consumed by the web dashboard."""
    crisis = db.query(Crisis).filter(Crisis.id == crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")

    ops = db.query(OperationalPicture).filter(
        OperationalPicture.crisis_id == crisis_id
    ).first()

    try:
        pt = to_shape(crisis.location)
        lat, lng = pt.y, pt.x
    except Exception:
        lat, lng = 0.0, 0.0

    ops_data = None
    if ops:
        ops_data = {
            "crisis_id": ops.crisis_id,
            "operational_picture": {
                "affected_zone": {
                    "center": [lat, lng],
                    "radius_km": crisis.affected_radius,
                },
                "road_closures":     ops.road_closures or [],
                "nearby_facilities": ops.nearby_facilities or [],
                "data_gaps":         ops.data_gaps or [],
                "population_at_risk": ops.population_at_risk or 0,
            },
            "generated_at": ops.generated_at.isoformat() if ops.generated_at else None,
        }

    # Promote stage to "analyzed" once ops_pic exists, keep DB status otherwise
    stage = crisis.status
    if stage == "detected" and ops:
        stage = "analyzed"

    return {
        "crisis_id":            crisis.id,
        "stage":                stage,
        "crisis":               _serialize_crisis(crisis),
        "operational_picture":  ops_data,
        "dispatch_plan":        None,
        "simulation":           None,
        "sitrep_text":          "",
        "agent_trace_summary":  [],
        "last_updated":         (
            crisis.updated_at.isoformat()
            if crisis.updated_at
            else datetime.now(timezone.utc).isoformat()
        ),
    }


# ── Derived / helper reads ────────────────────────────────────────────────────

@router.get("/crisis/{crisis_id}/safe-routes")
def get_safe_routes(crisis_id: str, db: Session = Depends(get_db)):
    crisis = db.query(Crisis).filter(Crisis.id == crisis_id).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="Crisis not found")
    return {"routes": [
        {
            "route_id": f"{crisis_id}_r1",
            "name": "Margalla Road (Alternate)",
            "distance_km": 4.8,
            "eta_minutes": 12,
            "risk_level": "low",
            "waypoints": [
                {"lat": 33.6844, "lng": 73.0479},
                {"lat": 33.7000, "lng": 73.0465},
                {"lat": 33.7200, "lng": 73.0450},
            ],
        },
        {
            "route_id": f"{crisis_id}_r2",
            "name": "Karakoram Highway Detour",
            "distance_km": 7.2,
            "eta_minutes": 18,
            "risk_level": "low",
            "waypoints": [
                {"lat": 33.6844, "lng": 73.0479},
                {"lat": 33.6900, "lng": 73.0300},
                {"lat": 33.7100, "lng": 73.0200},
            ],
        },
    ]}


@router.post("/crisis/{crisis_id}/user-intent")
async def log_user_intent(crisis_id: str, request: Request):
    return {"status": "ok"}


# ── Writes ────────────────────────────────────────────────────────────────────

@router.post("/crisis/detected")
async def crisis_detected(payload: CrisisEventSchema, db: Session = Depends(get_db)):
    existing = db.query(Crisis).filter(Crisis.id == payload.crisis_id).first()
    if existing:
        return {"crisis_id": payload.crisis_id}

    point = from_shape(
        Point(payload.location.lng, payload.location.lat), srid=4326
    )
    db.add(Crisis(
        id                   = payload.crisis_id,
        type                 = payload.type,
        location             = point,
        location_name        = payload.location.primary,
        affected_radius      = payload.location.affected_radius_km,
        severity             = payload.severity,
        confidence           = payload.confidence_score,
        confidence_label     = payload.confidence,
        reasoning            = payload.reasoning,
        contributing_signals = payload.contributing_signals,
        status               = "detected",
        detected_at          = payload.detected_at,
        updated_at           = datetime.now(timezone.utc),
    ))
    db.commit()

    await manager.broadcast({
        "event":      "crisis_detected",
        "crisis_id":  payload.crisis_id,
        "type":       payload.type,
        "severity":   payload.severity,
        "stage":      "detected",
    })
    return {"crisis_id": payload.crisis_id}


@router.post("/crisis/operational")
async def crisis_operational(payload: OperationalPictureSchema, db: Session = Depends(get_db)):
    road_closures     = [r.dict() for r in payload.operational_picture.road_closures]
    nearby_facilities = [f.dict() for f in payload.operational_picture.nearby_facilities]

    existing = db.query(OperationalPicture).filter(
        OperationalPicture.crisis_id == payload.crisis_id
    ).first()
    if existing:
        existing.road_closures     = road_closures
        existing.nearby_facilities = nearby_facilities
        existing.population_at_risk = payload.operational_picture.population_at_risk
        existing.data_gaps         = list(payload.operational_picture.data_gaps)
        existing.generated_at      = payload.generated_at
    else:
        db.add(OperationalPicture(
            crisis_id          = payload.crisis_id,
            road_closures      = road_closures,
            nearby_facilities  = nearby_facilities,
            population_at_risk = payload.operational_picture.population_at_risk,
            data_gaps          = list(payload.operational_picture.data_gaps),
            generated_at       = payload.generated_at,
        ))

    # Advance crisis status
    crisis = db.query(Crisis).filter(Crisis.id == payload.crisis_id).first()
    if crisis and crisis.status == "detected":
        crisis.status     = "analyzed"
        crisis.updated_at = datetime.now(timezone.utc)

    db.commit()

    await manager.broadcast({
        "event":     "crisis_update",
        "crisis_id": payload.crisis_id,
        "stage":     "analyzed",
    })
    await manager.broadcast_crisis(payload.crisis_id, {
        "event":     "crisis_update",
        "crisis_id": payload.crisis_id,
        "stage":     "analyzed",
    })
    return {"crisis_id": payload.crisis_id, "status": "ok"}
