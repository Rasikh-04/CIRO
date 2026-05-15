from sqlalchemy import Column, String, Integer, Text, DateTime
from geoalchemy2 import Geography
from app.db.session import Base

class DispatchOrder(Base):
    __tablename__ = "dispatch_orders"

    id              = Column(String(50), primary_key=True)
    crisis_id       = Column(String(50))
    unit_name       = Column(String(100))
    unit_type       = Column(String(50))
    destination     = Column(String(200))
    destination_geo = Column(Geography("POINT", srid=4326))
    reason          = Column(Text)
    eta_minutes     = Column(Integer)
    status          = Column(String(30))    # pending | en_route | on_scene
    created_at      = Column(DateTime(timezone=True))