from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class RouteSchema(BaseModel):
    via: str
    waypoints: List[List[float]]
    distance_km: float
    duration_min: int

class SimulationRouteSchema(BaseModel):
    order_id: str
    unit: str
    route: RouteSchema
    route_reasoning: str

class TrafficStateSchema(BaseModel):
    before: Dict[str, str]
    after: Dict[str, str]
    congestion_reduction_pct: float

class EmergencyTicketSchema(BaseModel):
    ticket_id: str
    created_at: datetime
    status: str
    units: List[str]

class PublicAlertSchema(BaseModel):
    channel: str
    target_area: str
    message: str

class SimulationDataSchema(BaseModel):
    routes: List[SimulationRouteSchema]
    traffic_state: TrafficStateSchema
    emergency_ticket: EmergencyTicketSchema
    public_alerts: List[PublicAlertSchema]

class SimulationResultSchema(BaseModel):
    crisis_id: str
    simulation: SimulationDataSchema
    created_at: datetime