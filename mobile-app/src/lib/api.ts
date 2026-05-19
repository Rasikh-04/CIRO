import axios from "axios";
import { DashboardState, CrisisAlert, SafeRoute } from "../types";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BACKEND_URL,
  timeout: 10000,
});

// Fetch active crises
export async function fetchActiveCrises(): Promise<CrisisAlert[]> {
  try {
    const res = await api.get("/api/crisis/active");
    return Array.isArray(res.data) ? res.data : [];
  } catch (err) {
    console.error("Failed to fetch active crises:", err);
    return [];
  }
}

// Fetch full crisis state by ID
export async function fetchCrisisDetail(crisisId: string): Promise<DashboardState | null> {
  try {
    const res = await api.get(`/api/crisis/full/${crisisId}`);
    return res.data;
  } catch (err) {
    console.error(`Failed to fetch crisis ${crisisId}:`, err);
    return null;
  }
}

// Fetch safe routes for a crisis
export async function fetchSafeRoutes(crisisId: string): Promise<SafeRoute[]> {
  try {
    const res = await api.get(`/api/crisis/${crisisId}/safe-routes`);
    return res.data.routes || [];
  } catch (err) {
    console.error(`Failed to fetch safe routes for ${crisisId}:`, err);
    return [];
  }
}

// Log user intent (safe route taken, alert dismissed, etc.)
export async function logUserIntent(crisisId: string, intentType: string, data: Record<string, unknown>): Promise<boolean> {
  try {
    await api.post(`/api/crisis/${crisisId}/user-intent`, {
      intent_type: intentType,
      timestamp: new Date().toISOString(),
      ...data,
    });
    return true;
  } catch (err) {
    console.error("Failed to log user intent:", err);
    return false;
  }
}

export default api;
