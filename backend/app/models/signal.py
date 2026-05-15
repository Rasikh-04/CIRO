from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography
from app.db.session import Base

class Signal(Base):
    __tablename__ = "signals"

    id           = Column(String(50), primary_key=True)
    source       = Column(String(30))       # social_media | weather | traffic
    raw_text     = Column(Text)
    normalized   = Column(Text)
    signal_type  = Column(String(30))       # flood | accident | heatwave etc.
    location     = Column(Geography("POINT", srid=4326))
    district     = Column(String(100))
    city         = Column(String(100))
    confidence   = Column(Float)
    timestamp    = Column(DateTime(timezone=True))
    crisis_id    = Column(String(50))       # filled in later when crisis is confirmed