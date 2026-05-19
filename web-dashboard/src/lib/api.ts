import axios from "axios";
import type { ActiveCrisisSummary, DashboardState } from "../types";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const client = axios.create({ baseURL: BASE_URL, timeout: 10000 });

export async function fetchActiveCrises(): Promise<ActiveCrisisSummary[]> {
  const { data } = await client.get("/api/crisis/active");
  return data;
}

export async function fetchCrisis(id: string): Promise<DashboardState> {
  const { data } = await client.get(`/api/crisis/full/${id}`);
  return data;
}

export async function fetchFullCrisis(id: string): Promise<DashboardState> {
  const { data } = await client.get(`/api/crisis/full/${id}`);
  return data;
}

export type DemoScenario = "g10_flood" | "i8_heat" | "f10_accident";

export async function triggerDemo(scenario: DemoScenario = "g10_flood"): Promise<void> {
  await client.post("/api/demo/trigger", { scenario });
}
