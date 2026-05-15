// Canonical types matching schemas in docs/06_shared_integration_contract.md

export interface SignalLocation {
  district: string;
  city: string;
  lat: number;
  lng: number;
}

export interface SignalEvent {
  id: string;
  source: "social_media" | "weather" | "traffic";
  raw_text: string;
  normalized: string;
  location: SignalLocation;
  signal_type: "flood" | "heatwave" | "accident" | "road_blockage" | "infrastructure_failure";
  timestamp: string;
  confidence: number;
  source_label: "simulated" | "real";
}

export interface CrisisLocation {
  primary: string;
  affected_radius_km: number;
  lat: number;
  lng: number;
}

export interface CrisisEvent {
  crisis_id: string;
  type: "urban_flooding" | "heatwave" | "accident" | "road_blockage" | "infrastructure_failure";
  location: CrisisLocation;
  severity: 1 | 2 | 3 | 4 | 5;
  confidence: "low" | "medium" | "high";
  confidence_score: number;
  reasoning: string;
  contributing_signals: string[];
  status: "confirmed";
  detected_at: string;
}

export interface RoadClosure {
  road: string;
  status: "blocked" | "partial" | "clear";
  lat: number;
  lng: number;
  source: "traffic_api" | "osm" | "simulated";
}

export interface NearbyFacility {
  type: "rescue_unit" | "hospital" | "fire_station" | "depot";
  name: string;
  lat: number;
  lng: number;
  distance_km: number;
  status: "available" | "deployed" | "unavailable" | "operational";
}

export interface OperationalPicture {
  crisis_id: string;
  operational_picture: {
    affected_zone: { center: [number, number]; radius_km: number };
    road_closures: RoadClosure[];
    nearby_facilities: NearbyFacility[];
    data_gaps: unknown[];
    population_at_risk: number;
  };
  generated_at: string;
}

export interface DispatchOrder {
  order_id: string;
  unit: string;
  unit_type: "water_rescue" | "ambulance" | "fire" | "police" | "supplies";
  destination: string;
  destination_lat: number;
  destination_lng: number;
  origin_lat: number;
  origin_lng: number;
  reason: string;
  eta_minutes: number;
}

export interface ResourceGap {
  item: string;
  required: number;
  available: number;
  gap: number;
  mitigation: string;
}

export interface DispatchPlan {
  crisis_id: string;
  dispatch_plan: {
    priority_ranking: Array<{ zone: string; priority_score: number; reason: string }>;
    dispatch_orders: DispatchOrder[];
    resource_gaps: ResourceGap[];
  };
  generated_at: string;
}

export interface RouteResult {
  order_id: string;
  unit: string;
  route: {
    via: string;
    waypoints: [number, number][];
    distance_km: number;
    duration_min: number;
  };
  route_reasoning: string;
}

export interface SimulationResult {
  crisis_id: string;
  simulation: {
    routes: RouteResult[];
    traffic_state: {
      before: Record<string, string>;
      after: Record<string, string>;
      congestion_reduction_pct: number;
    };
    emergency_ticket: {
      ticket_id: string;
      created_at: string;
      status: string;
      units: string[];
    };
    public_alerts: Array<{
      channel: "SMS" | "app_push" | "dashboard";
      target_area: string;
      message: string;
    }>;
  };
  created_at: string;
}

export interface AgentTraceSummary {
  agent: string;
  key_decision: string;
  timestamp: string;
}

export interface DashboardState {
  crisis_id: string;
  stage: "detected" | "analyzed" | "dispatched" | "simulated" | "resolved";
  crisis: CrisisEvent;
  operational_picture: OperationalPicture;
  dispatch_plan: DispatchPlan;
  simulation: SimulationResult;
  sitrep_text: string;
  agent_trace_summary: AgentTraceSummary[];
  last_updated: string;
}

// UI-only types

export type CrisisStage = DashboardState["stage"];

export interface ActiveCrisisSummary {
  crisis_id: string;
  type: string;
  location_name: string;
  severity: number;
  stage: CrisisStage;
  detected_at: string;
}

export type BottomTab = "trace" | "dispatch" | "resources" | "sitrep";

export type TrafficView = "before" | "after";
