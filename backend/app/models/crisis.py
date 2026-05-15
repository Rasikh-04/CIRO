from sqlalchemy import Column, String, Float, Integer, Text, DateTime
from geoalchemy2 import Geography
from app.db.session import Base

class Crisis(Base):
    __tablename__ = "crises"

    id                = Column(String(50), primary_key=True)
    type              = Column(String(50))
    location          = Column(Geography("POINT", srid=4326))
    location_name     = Column(String(200))
    affected_radius   = Column(Float)           # km
    severity          = Column(Integer)          # 1-5
    confidence        = Column(Float)
    confidence_label  = Column(String(10))       # low | medium | high
    reasoning         = Column(Text)
    status            = Column(String(30))       # detected | analyzed | dispatched | simulated | resolved
    detected_at       = Column(DateTime(timezone=True))
    updated_at        = Column(DateTime(timezone=True))