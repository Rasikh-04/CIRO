"""
Agent 3 — Situational Awareness (CIRO)

Reads crisis.json from Agent 2, queries road network and facilities,
estimates population at risk, writes ops_pic.json, and POSTs to backend.

Run: python situational.py
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

BASE_DIR = Path(__file__).parent
AGENT2_OUTPUT = BASE_DIR / ".." / "agent_2_crisis_detection" / "output" / "crisis.json"
FACILITIES_DB = BASE_DIR / ".." / ".." / "backend" / "data" / "facilities_db.json"
POPULATION_DB = BASE_DIR / ".." / ".." / "backend" / "data" / "population_density.json"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TRACE_LOG = OUTPUT_DIR / "agent3_trace.log"
OPS_PIC_OUTPUT = OUTPUT_DIR / "ops_pic.json"
BACKEND_URL = os.getenv("CIRO_BACKEND_URL", "http://localhost:8000")

# Add agent_3 dir to path so we can import our helper modules
sys.path.insert(0, str(BASE_DIR))
from haversine import haversine, rank_facilities  # noqa: E402
from osm_query import query_roads, DEFAULT_BBOX   # noqa: E402

open(TRACE_LOG, "w").close()


def log(level: str, message: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] AGENT_3 | {level} | {message}"
    print(line)
    with open(TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_crisis() -> dict:
    url = f"{BACKEND_URL}/api/crisis/latest"
    if _HAS_REQUESTS:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                log("TOOL_CALL", f"GET {url} -> 200 OK")
                return resp.json()
        except Exception:
            pass
    log("TOOL_CALL", f"Read {AGENT2_OUTPUT} (backend not available)")
    with open(AGENT2_OUTPUT, encoding="utf-8") as f:
        return json.load(f)


def build_road_closures(roads: list) -> list:
    """Filter to blocked/partial roads and map to Schema C road_closures format."""
    closures = []
    for road in roads:
        if road["status"] not in ("blocked", "partial"):
            continue
        closures.append({
            "road": road["name"],
            "status": road["status"],
            "lat": road["lat"],
            "lng": road["lng"],
            "source": road.get("source", "simulated"),
        })
    return closures


def build_nearby_facilities(crisis_lat: float, crisis_lng: float) -> list:
    """Load facilities_db, compute distances, return sorted by proximity."""
    with open(FACILITIES_DB, encoding="utf-8") as f:
        facilities = json.load(f)
    results = []
    for fac in facilities:
        dist = haversine(crisis_lat, crisis_lng, fac["lat"], fac["lng"])
        results.append({
            "type": fac["type"],
            "name": fac["name"],
            "lat": fac["lat"],
            "lng": fac["lng"],
            "distance_km": dist,
            "status": fac.get("status", "unknown"),
        })
    results.sort(key=lambda x: x["distance_km"])
    return results


def estimate_population_at_risk(district: str, radius_km: float) -> int:
    """Estimate affected population from density data and affected radius."""
    try:
        with open(POPULATION_DB, encoding="utf-8") as f:
            density = json.load(f)
        import math
        area_km2 = math.pi * radius_km ** 2
        key = district.split(",")[0].strip()
        density_per_km2 = density.get(key, {}).get("density_per_km2", 8200)
        raw = int(area_km2 * density_per_km2 * 0.08)
        return min(raw, density.get(key, {}).get("population", 45000))
    except Exception:
        return 12000


def identify_data_gaps(roads: list, facilities: list) -> list:
    gaps = []
    if all(r.get("source") == "simulated" for r in roads):
        gaps.append("road_network: live OSM data unavailable — using simulated fallback")
    real_time_fac = [f for f in facilities if f.get("status") not in ("available", "operational", "deployed")]
    if real_time_fac:
        gaps.append("facility_status: real-time status unavailable for some units")
    return gaps


def post_to_backend(ops_pic: dict):
    url = f"{BACKEND_URL}/api/crisis/operational"
    log("ACTION", f"POST {url}")
    if not _HAS_REQUESTS:
        log("WARNING", "requests not installed — skipping POST, ops_pic saved locally")
        return
    try:
        resp = requests.post(url, json=ops_pic, timeout=5)
        resp.raise_for_status()
        log("ACTION", f"POST {url} -> {resp.status_code} OK | crisis_id={ops_pic['crisis_id']}")
    except Exception as e:
        log("WARNING", f"Backend not available ({e}) — ops_pic saved locally")


def main():
    start = datetime.now(timezone.utc)
    log("START", "Situational Awareness initiated")

    crisis = load_crisis()
    crisis_id = crisis["crisis_id"]
    crisis_lat = crisis["location"]["lat"]
    crisis_lng = crisis["location"]["lng"]
    affected_radius = crisis["location"]["affected_radius_km"]
    district = crisis["location"]["primary"]
    log("RESULT", f"Crisis loaded: {crisis_id} | {crisis['type']} | {district} | severity={crisis['severity']}")

    log("TOOL_CALL", "python osm_query.py — querying Overpass API for road network")
    roads, road_source = query_roads(DEFAULT_BBOX)
    log("RESULT", f"Road network: {len(roads)} roads | source={road_source}")

    road_closures = build_road_closures(roads)
    blocked = [r for r in road_closures if r["status"] == "blocked"]
    partial = [r for r in road_closures if r["status"] == "partial"]
    log("DECISION", f"Road closures: {len(blocked)} blocked, {len(partial)} partial")
    for r in road_closures:
        log("DECISION", f"  {r['status'].upper()}: {r['road']} ({r['lat']}, {r['lng']})")

    log("TOOL_CALL", "python haversine.py — ranking facilities by distance from crisis center")
    facilities = build_nearby_facilities(crisis_lat, crisis_lng)
    log("RESULT", f"Facilities ranked: {len(facilities)} facilities loaded")
    for fac in facilities[:3]:
        log("DECISION", f"  {fac['name']}: {fac['distance_km']}km | status={fac['status']}")

    population = estimate_population_at_risk(district, affected_radius)
    log("DECISION", f"Population at risk estimate: ~{population:,} people within {affected_radius}km radius")

    data_gaps = identify_data_gaps(roads, facilities)
    if data_gaps:
        for gap in data_gaps:
            log("WARNING", f"Data gap: {gap}")
    else:
        log("DECISION", "No data gaps identified")

    ops_pic = {
        "crisis_id": crisis_id,
        "operational_picture": {
            "affected_zone": {
                "center": [crisis_lat, crisis_lng],
                "radius_km": affected_radius,
            },
            "road_closures": road_closures,
            "nearby_facilities": facilities,
            "data_gaps": data_gaps,
            "population_at_risk": population,
        },
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open(OPS_PIC_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(ops_pic, f, indent=2, ensure_ascii=False)
    log("OUTPUT", f"Written to output/ops_pic.json | {len(road_closures)} closures | {len(facilities)} facilities")

    post_to_backend(ops_pic)

    duration = (datetime.now(timezone.utc) - start).seconds
    log("END", f"Duration: {duration}s | crisis_id={crisis_id} | pop_at_risk={population:,}")


if __name__ == "__main__":
    main()
