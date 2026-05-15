from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CrisisLocationSchema(BaseModel):
    primary: str
    affected_radius_km: float
    lat: float
    lng: float

class CrisisEventSchema(BaseModel):
    crisis_id: str
    type: str
    location: CrisisLocationSchema
    severity: int
    confidence: str              # low | medium | high
    confidence_score: float
    reasoning: str
    contributing_signals: List[str]
    status: str
    detected_at: datetime

class RoadClosureSchema(BaseModel):
    road: str
    status: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: str

class FacilitySchema(BaseModel):
    type: str
    name: str
    lat: float
    lng: float
    distance_km: float
    status: str

class AffectedZoneSchema(BaseModel):
    center: List[float]
    radius_km: float

class OperationalPictureDataSchema(BaseModel):
    affected_zone: AffectedZoneSchema
    road_closures: List[RoadClosureSchema]
    nearby_facilities: List[FacilitySchema]
    data_gaps: List = []
    population_at_risk: int

class OperationalPictureSchema(BaseModel):
    crisis_id: str
    operational_picture: OperationalPictureDataSchema
    generated_at: datetime