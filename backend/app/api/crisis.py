from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.crisis import CrisisEventSchema, OperationalPictureSchema
from app.models.crisis import Crisis
from app.models.operational_picture import OperationalPicture
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from datetime import datetime, timezone

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
    point = from_shape(
        Point(payload.location.lng, payload.location.lat), srid=4326
    )
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

@router.get("/crisis/active")
def get_active_crises(db: Session = Depends(get_db)):
    crises = (
        db.query(Crisis)
        .filter(Crisis.status != "resolved")
        .order_by(Crisis.detected_at.desc())
        .all()
    )
    return [
        {
            "crisis_id":     c.id,
            "type":          c.type,
            "location_name": c.location_name,
            "severity":      c.severity,
            "stage":         c.status,
            "detected_at":   c.detected_at.isoformat() if c.detected_at else None,
        }
        for c in crises
    ]


@router.get("/crisis/latest")
def get_latest_crisis(db: Session = Depends(get_db)):
    crisis = db.query(Crisis).order_by(Crisis.detected_at.desc()).first()
    if not crisis:
        raise HTTPException(status_code=404, detail="No crisis found")
    return crisis