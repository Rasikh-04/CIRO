from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.signal import SignalIngestRequest
from app.models.signal import Signal
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from datetime import datetime, timezone

router = APIRouter()

@router.post("/signals/ingest")
def ingest_signals(payload: SignalIngestRequest, db: Session = Depends(get_db)):
    count = 0
    for sig in payload.signals:
        # Check if signal already exists (idempotent)
        existing = db.query(Signal).filter(Signal.id == sig.id).first()
        if existing:
            continue

        point = from_shape(Point(sig.location.lng, sig.location.lat), srid=4326)

        db_signal = Signal(
            id          = sig.id,
            source      = sig.source,
            raw_text    = sig.raw_text,
            normalized  = sig.normalized,
            signal_type = sig.signal_type,
            location    = point,
            district    = sig.location.district,
            city        = sig.location.city,
            confidence  = sig.confidence,
            timestamp   = sig.timestamp,
        )
        db.add(db_signal)
        count += 1

    db.commit()
    return {"accepted": count}

@router.get("/signals/latest")
def get_latest_signals(db: Session = Depends(get_db)):
    from geoalchemy2.shape import to_shape
    signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(20).all()
    result = []
    for s in signals:
        shape = to_shape(s.location) if s.location else None
        result.append({
            "id":          s.id,
            "source":      s.source,
            "raw_text":    s.raw_text,
            "normalized":  s.normalized,
            "signal_type": s.signal_type,
            "confidence":  s.confidence,
            "timestamp":   s.timestamp.isoformat() if s.timestamp else "",
            "crisis_id":   s.crisis_id,
            "location": {
                "lat":      shape.y if shape else 33.6844,
                "lng":      shape.x if shape else 73.0479,
                "district": s.district or "",
                "city":     s.city or "",
            }
        })
    return result