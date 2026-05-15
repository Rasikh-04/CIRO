from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geography
from app.db.session import Base

class Resource(Base):
    __tablename__ = "resources"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(100))
    type       = Column(String(50))         # rescue_unit | supplies | vehicle
    depot_name = Column(String(100))
    location   = Column(Geography("POINT", srid=4326))
    status     = Column(String(30))         # available | deployed | unavailable
    quantity   = Column(Integer)