from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.crisis import Crisis
from app.models.operational_picture import OperationalPicture
from app.models.dispatch import DispatchOrder
from app.models.simulation import Simulation
from app.ws.manager import manager
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from datetime import datetime, timezone

router = APIRouter()

DEMO_CRISIS_ID = "CRS_DEMO_G10_FLOOD"


@router.post("/inject-scenario")
async def inject_scenario(payload: dict, db: Session = Depends(get_db)):
    scenario = payload.get("scenario", "g10_flood")
    if scenario != "g10_flood":
        return {"error": f"Unknown scenario: {scenario}"}

    now = datetime.now(timezone.utc)

    # Wipe any previous run of the same demo so it's idempotent
    db.query(Simulation).filter(Simulation.crisis_id == DEMO_CRISIS_ID).delete()
    db.query(DispatchOrder).filter(DispatchOrder.crisis_id == DEMO_CRISIS_ID).delete()
    db.query(OperationalPicture).filter(OperationalPicture.crisis_id == DEMO_CRISIS_ID).delete()
    existing = db.query(Crisis).filter(Crisis.id == DEMO_CRISIS_ID).first()
    if existing:
        db.delete(existing)
    db.commit()

    # ── Stage 1: Crisis detected ──────────────────────────────────────────────
    crisis = Crisis(
        id               = DEMO_CRISIS_ID,
        type             = "urban_flooding",
        location         = from_shape(Point(73.0479, 33.6844), srid=4326),
        location_name    = "G-10, Islamabad",
        affected_radius  = 2.5,
        severity         = 4,
        confidence       = 0.89,
        confidence_label = "high",
        reasoning        = (
            "3 corroborating signals detected: social media reports of flooding, "
            "heavy rainfall sensor spike, and traffic congestion on Srinagar Highway."
        ),
        status           = "detected",
        detected_at      = now,
        updated_at       = now,
    )
    db.add(crisis)
    db.commit()
    await manager.broadcast({"stage": "detected", "crisis_id": DEMO_CRISIS_ID}, DEMO_CRISIS_ID)

    # ── Stage 2: Operational picture (→ analyzed) ─────────────────────────────
    op_pic = OperationalPicture(
        crisis_id          = DEMO_CRISIS_ID,
        road_closures      = [
            {
                "road": "Srinagar Highway",
                "status": "blocked",
                "lat": 33.688,
                "lng": 73.055,
                "source": "simulated",
            }
        ],
        nearby_facilities  = [
            {
                "type": "rescue_unit",
                "name": "F-8 Rescue Station",
                "lat": 33.708,
                "lng": 73.0479,
                "distance_km": 3.1,
                "status": "available",
            },
            {
                "type": "hospital",
                "name": "PIMS Hospital",
                "lat": 33.7161,
                "lng": 73.0738,
                "distance_km": 4.2,
                "status": "operational",
            },
        ],
        population_at_risk = 12000,
        data_gaps          = [],
        generated_at       = now,
    )
    db.add(op_pic)
    crisis.status     = "analyzed"
    crisis.updated_at = now
    db.commit()
    await manager.broadcast({"stage": "analyzed", "crisis_id": DEMO_CRISIS_ID}, DEMO_CRISIS_ID)

    # ── Stage 3: Dispatch (→ dispatched) ─────────────────────────────────────
    order = DispatchOrder(
        id              = "ORD_DEMO_001",
        crisis_id       = DEMO_CRISIS_ID,
        unit_name       = "F-8 Rescue Unit Alpha",
        unit_type       = "water_rescue",
        destination     = "G-10, Islamabad",
        destination_geo = from_shape(Point(73.0479, 33.6844), srid=4326),
        reason          = (
            "Urban flooding requires water rescue. Srinagar Highway blocked — "
            "dispatching via Margalla Road alternate route."
        ),
        eta_minutes     = 12,
        status          = "en_route",
        created_at      = now,
    )
    db.add(order)
    crisis.status     = "dispatched"
    crisis.updated_at = now
    db.commit()
    await manager.broadcast({"stage": "dispatched", "crisis_id": DEMO_CRISIS_ID}, DEMO_CRISIS_ID)

    # ── Stage 4: Simulation (→ simulated) ────────────────────────────────────
    sim = Simulation(
        crisis_id                = DEMO_CRISIS_ID,
        routes                   = [
            {
                "order_id": "ORD_DEMO_001",
                "unit": "F-8 Rescue Unit Alpha",
                "route": {
                    "via": "Margalla Road",
                    "waypoints": [
                        [33.708,  73.0479],
                        [33.72,   73.045],
                        [33.6844, 73.0479],
                    ],
                    "distance_km": 5.2,
                    "duration_min": 12,
                },
                "route_reasoning": (
                    "Srinagar Highway fully blocked by flooding. "
                    "Margalla Road selected — 61% congestion reduction vs. direct route."
                ),
            }
        ],
        traffic_before           = {
            "congestion_index": 87,
            "blocked_roads": ["Srinagar Highway"],
            "flow_segments": [],
        },
        traffic_after            = {
            "congestion_index": 34,
            "blocked_roads": ["Srinagar Highway"],
            "flow_segments": [],
        },
        congestion_reduction_pct = 61,
        emergency_ticket_id      = "EMT_2841",
        public_alerts            = [
            {
                "channel": "app_push",
                "target_area": "G-10, Islamabad",
                "message": (
                    "Urban flooding detected in G-10. Avoid Srinagar Highway. "
                    "Use Margalla Road as alternate route."
                ),
            },
            {
                "channel": "SMS",
                "target_area": "G-10, Islamabad",
                "message": "CIRO ALERT: Flooding in G-10. Rescue unit dispatched. ETA 12 min.",
            },
        ],
        created_at               = now,
    )
    db.add(sim)
    crisis.status     = "simulated"
    crisis.updated_at = now
    db.commit()
    await manager.broadcast({"stage": "simulated", "crisis_id": DEMO_CRISIS_ID}, DEMO_CRISIS_ID)

    return {
        "ok": True,
        "crisis_id": DEMO_CRISIS_ID,
        "scenario": scenario,
        "stages_completed": ["detected", "analyzed", "dispatched", "simulated"],
        "emergency_ticket": "EMT_2841",
        "congestion_reduction_pct": 61,
    }
