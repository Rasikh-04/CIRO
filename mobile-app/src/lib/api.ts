import type {
  CrisisEvent,
  CrisisDetail,
  SafeRoute,
  CitizenReport,
  PublicAlert,
} from '../types';

const BACKEND_URL =
  process.env.EXPO_PUBLIC_BACKEND_URL || 'http://192.168.100.4:8000';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export async function fetchActiveCrises(): Promise<CrisisEvent[]> {
  try {
    const data = await get<CrisisEvent[]>('/api/v2/crisis/active');
    return Array.isArray(data) ? data.map((c: any) => ({ ...c, id: c.crisis_id || c.id })) : [];
  } catch {
    return [];
  }
}

export async function fetchCrisisDetail(id: string): Promise<CrisisDetail | null> {
  try {
    return await get<CrisisDetail>(`/api/v2/crisis/full/${id}`);
  } catch {
    return null;
  }
}

export async function fetchSafeRoutes(crisisId: string): Promise<SafeRoute[]> {
  try {
    const data = await get<any>(`/api/v2/crisis/full/${crisisId}`);
    const routes: any[] = data?.simulation?.simulation?.routes ?? [];
    return routes.map((r: any) => ({
      name: r.unit ?? 'Unit',
      via: r.route?.via ?? '',
      distance_km: r.route?.distance_km ?? 0,
      eta_minutes: r.route?.duration_min ?? 0,
      extra_minutes: 0,
      risk_level: 'monitor' as SafeRoute['risk_level'],
      waypoints: (r.route?.waypoints ?? []).map(([lat, lng]: [number, number]) => ({ lat, lng })),
    }));
  } catch {
    return [];
  }
}

export async function fetchNearbyAlerts(
  lat: number,
  lng: number,
  radiusKm = 10
): Promise<PublicAlert[]> {
  try {
    const data = await get<PublicAlert[]>('/api/v2/crisis/active');
    return Array.isArray(data) ? data.map((c: any) => ({ ...c, id: c.crisis_id || c.id })) : [];
  } catch {
    return [];
  }
}

export async function fetchVoiceAlertUrl(crisisId: string): Promise<string | null> {
  return null;
}

export async function submitCitizenReport(
  report: CitizenReport
): Promise<{ report_id: string; status: string } | null> {
  try {
    return await post('/api/crisis/detected', report);
  } catch {
    return null;
  }
}

export async function triggerDemo(): Promise<void> {
  await post('/api/v2/debug/inject-scenario', { scenario: 'g10_flood' });
}
