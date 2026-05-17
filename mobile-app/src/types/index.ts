import type { ThemeKey } from '../theme/colors';

// v2 types — matches Supabase schema (v2_06_backend_v2.md §3)

export type CrisisType =
  | 'urban_flooding'
  | 'heatwave'
  | 'accident'
  | 'road_blockage'
  | 'infrastructure_failure';

export type CrisisStatus =
  | 'monitoring'
  | 'detected'
  | 'analyzed'
  | 'dispatched'
  | 'simulated'
  | 'resolved'
  | 'archived';

export type ConfidenceLabel = 'low' | 'medium' | 'high';

export interface CrisisEvent {
  id: string;
  type: CrisisType;
  location: { lat: number; lng: number };
  location_name: string;
  affected_radius_km: number;
  severity: 1 | 2 | 3 | 4 | 5;
  confidence_score: number;
  confidence_label: ConfidenceLabel;
  reasoning?: string;
  status: CrisisStatus;
  track: 1 | 2;
  track2_activated: boolean;
  detected_at: string;
  updated_at: string;
  resolved_at?: string;
  alert_audio_url?: string;
}

export interface DispatchOrder {
  id: string;
  crisis_id: string;
  unit_id: string;
  unit_name: string;
  unit_type: string;
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  destination_name: string;
  reason: string;
  eta_minutes: number;
  status: 'pending' | 'en_route' | 'on_scene' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface RoadClosure {
  road: string;
  lat: number;
  lng: number;
  severity: 'low' | 'medium' | 'high';
}

export interface NearbyFacility {
  name: string;
  type: 'hospital' | 'rescue_station' | 'police' | 'fire' | 'clinic';
  lat: number;
  lng: number;
  distance_km: number;
}

export interface OperationalPicture {
  crisis_id: string;
  road_closures: RoadClosure[];
  nearby_facilities: NearbyFacility[];
  flood_extent?: unknown;
  population_at_risk: number;
  data_gaps: string[];
  generated_at: string;
}

export interface SimulationResult {
  crisis_id: string;
  routes: RouteResult[];
  traffic_before: TrafficState;
  traffic_after: TrafficState;
  congestion_reduction_pct: number;
  emergency_ticket_id: string;
  civilian_safe_routes: SafeRoute[];
  created_at: string;
}

export interface RouteResult {
  unit_id: string;
  unit_name: string;
  waypoints: Array<{ lat: number; lng: number }>;
  distance_km: number;
  duration_min: number;
  fallback?: boolean;
}

export interface TrafficState {
  congestion_index: number;
  blocked_roads: string[];
  flow_segments: Array<{ lat: number; lng: number; level: number }>;
}

export interface SafeRoute {
  name: string;
  via: string;
  distance_km: number;
  eta_minutes: number;
  extra_minutes: number;
  risk_level: 'clear' | 'monitor' | 'avoid';
  waypoints: Array<{ lat: number; lng: number }>;
  maps_deep_link?: string;
}

export interface PublicAlert {
  id: string;
  crisis_id: string;
  severity: number;
  text_english: string;
  text_urdu: string;
  audio_url_urdu?: string;
  audio_url_en?: string;
  safe_routes: SafeRoute[];
  status: 'active' | 'expired';
  created_at: string;
  expires_at?: string;
}

export interface AgentTraceEntry {
  timestamp: string;
  agent: string;
  level: 'TOOL' | 'RESULT' | 'DECISION' | 'ACTION' | 'OUTPUT' | 'ERROR' | 'WARNING';
  message: string;
}

// Full crisis detail response (GET /api/v2/crisis/{id})
export interface CrisisDetail {
  crisis: CrisisEvent;
  operational_picture?: OperationalPicture;
  dispatch_orders: DispatchOrder[];
  simulation?: SimulationResult;
  public_alerts: PublicAlert[];
  agent_trace: AgentTraceEntry[];
  last_updated: string;
}

// Citizen report (POST /api/v2/reports)
export interface CitizenReport {
  text?: string;
  location: { lat: number; lng: number };
  type_guess?: CrisisType;
  photo_base64?: string;
}

// User preferences (stored in AsyncStorage)
export interface UserPreferences {
  alert_radius_km: 2 | 5 | 10 | 100;
  notification_sound: 'silent' | 'vibrate' | 'sound' | 'voice';
  language: 'english' | 'urdu' | 'both';
  voice_language: 'urdu' | 'english' | 'both';
  auto_play_voice: boolean;
  pre_download_alerts: boolean;
  theme?: ThemeKey; // undefined → treated as 'navalCommand'
}

export type BottomTab = 'home' | 'alerts' | 'routes' | 'report' | 'profile';
