from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LocationSchema(BaseModel):
    district: str
    city: str
    lat: float
    lng: float

class SignalEventSchema(BaseModel):
    id: str
    source: str                  # social_media | weather | traffic
    raw_text: str
    normalized: str
    location: LocationSchema
    signal_type: str             # flood | heatwave | accident | road_blockage
    timestamp: datetime
    confidence: float
    source_label: Optional[str] = "simulated"

class SignalIngestRequest(BaseModel):
    signals: list[SignalEventSchema]
    ingest_timestamp: Optional[datetime] = None