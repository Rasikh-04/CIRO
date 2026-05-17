import axios from "axios";
import type { ActiveCrisisSummary, DashboardState } from "../types";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const client = axios.create({ baseURL: BASE_URL, timeout: 10000 });

export async function fetchActiveCrises(): Promise<ActiveCrisisSummary[]> {
  const { data } = await client.get("/api/v2/crisis/active");
  return Array.isArray(data) ? data : [];
}

export async function fetchCrisis(id: string): Promise<DashboardState> {
  const { data } = await client.get(`/api/v2/crisis/${id}`);
  return data;
}

export async function fetchFullCrisis(id: string): Promise<DashboardState> {
  const { data } = await client.get(`/api/v2/crisis/${id}`);
  return data;
}

export async function triggerDemo(): Promise<void> {
  await client.post("/api/v2/debug/inject-scenario", { scenario: "g10_flood" });
}
