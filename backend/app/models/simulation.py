from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base

class Simulation(Base):
    __tablename__ = "simulations"

    id                       = Column(Integer, primary_key=True, autoincrement=True)
    crisis_id                = Column(String(50))
    routes                   = Column(JSONB)        # route data per unit
    traffic_before           = Column(JSONB)
    traffic_after            = Column(JSONB)
    congestion_reduction_pct = Column(Float)
    emergency_ticket_id      = Column(String(50))
    public_alerts            = Column(JSONB)
    created_at               = Column(DateTime(timezone=True))