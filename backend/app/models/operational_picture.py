from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base

class OperationalPicture(Base):
    __tablename__ = "operational_pictures"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    crisis_id          = Column(String(50))
    road_closures      = Column(JSONB)
    nearby_facilities  = Column(JSONB)
    population_at_risk = Column(Integer)
    data_gaps          = Column(JSONB)
    affected_zone      = Column(JSONB)
    generated_at       = Column(DateTime(timezone=True))