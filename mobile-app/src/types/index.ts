// Schema A — Signal Events (Layer 1)
export interface SignalEvent {
  signal_id: string;
  source: "twitter" | "facebook" | "weather_api" | "traffic_api" | "simulated";
  signal_type: "social_media_post" | "weather_alert" | "traffic_anomaly";
  content: string;
  location?: {
    latitude: number;
    longitude: number;
    area?: string;
  };
  timestamp: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

// Schema B — Crisis Event
export interface CrisisLocation {
  primary: string;
  latitude: number;
  longitude: number;
  affected_radius_km?: number;
}

export interface CrisisEvent {
  crisis_id: string;
  type: string;
  severity: number;
  confidence: number;
  location: CrisisLocation;
  timestamp: string;
  trigger_signal_ids: string[];
  source: "simulated" | "detected";
}

// Schema C — Operational Picture
export interface RoadClosure {
  closure_id: string;
  location: {
    latitude: number;
    longitude: number;
  };
  severity: "low" | "medium" | "high";
  estimated_duration_minutes: number;
}

export interface NearbyFacility {
  facility_id: string;
  name: string;
  type: "hospital" | "rescue_station" | "police" | "fire" | "distribution_center";
  location: {
    latitude: number;
    longitude: number;
  };
  distance_km: number;
  capacity?: number;
  availability_score?: number;
}

export interface OperationalPicture {
  crisis_id: string;
  timestamp: string;
  affected_population_estimate: number;
  road_closures: RoadClosure[];
  nearby_facilities: NearbyFacility[];
  traffic_state: {
    blockage_location?: {
      latitude: number;
      longitude: number;
    };
    congestion_level: number;
  };
  source: "simulated" | "live";
}

// Schema D — Dispatch Plan
export interface DispatchOrder {
  order_id: string;
  unit_id: string;
  unit_type: string;
  destination: {
    latitude: number;
    longitude: number;
  };
  destination_name: string;
  eta_minutes: number;
  resource_allocation: Record<string, number>;
  priority: number;
  reason: string;
  status: "pending" | "en_route" | "arrived" | "complete";
}

export interface ResourceGap {
  resource_type: string;
  required: number;
  available: number;
  gap: number;
}

export interface DispatchPlan {
  crisis_id: string;
  dispatch_plan: {
    dispatch_orders: DispatchOrder[];
    resource_gaps: ResourceGap[];
    total_units_deployed: number;
    estimated_outcome_confidence: number;
  };
  source: "simulated" | "planned";
}

// Schema E — Simulation Result
export interface RouteResult {
  unit_id: string;
  destination: string;
  route: {
    waypoints: Array<{
      latitude: number;
      longitude: number;
    }>;
    distance_km: number;
    duration_minutes: number;
  };
  eta: string;
}

export interface SimulationResult {
  crisis_id: string;
  timestamp: string;
  simulation: {
    routes: RouteResult[];
    traffic_state: {
      blockage_location: {
        latitude: number;
        longitude: number;
      };
      congestion_reduction_pct: number;
    };
    emergency_ticket: {
      ticket_id: string;
      status: "issued" | "acknowledged" | "in_progress" | "resolved";
    };
  };
  source: "simulated";
}

// Schema F — Dashboard State
export interface AgentTraceSummary {
  agent_id: string;
  agent_name: string;
  stage: string;
  status: "idle" | "running" | "success" | "error";
  trace_lines: string[];
}

export interface DashboardState {
  crisis_id: string;
  stage: string;
  crisis: CrisisEvent;
  operational_picture: OperationalPicture;
  dispatch_plan: DispatchPlan;
  simulation: SimulationResult;
  sitrep_text: string;
  agent_trace_summary: AgentTraceSummary[];
  last_updated: string;
}

// Mobile App — UI-specific types
export interface CrisisAlert {
  crisis_id: string;
  type: string;
  severity: number;
  location: CrisisLocation;
  affected_population: number;
  timestamp: string;
}

export interface SafeRoute {
  route_id: string;
  name: string;
  distance_km: number;
  eta_minutes: number;
  risk_level: "low" | "medium" | "high";
  waypoints: Array<{
    latitude: number;
    longitude: number;
  }>;
}

export type BottomTab = "home" | "alerts" | "routes" | "profile";

export interface UserProfile {
  user_id: string;
  name: string;
  location?: {
    latitude: number;
    longitude: number;
  };
  alert_preferences: {
    severity_threshold: number;
    push_enabled: boolean;
    sms_enabled: boolean;
  };
}
