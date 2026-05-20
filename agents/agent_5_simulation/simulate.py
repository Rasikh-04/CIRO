"""
Agent 5 — Simulation & Routing (CIRO)

Reads dispatch.json from Agent 4, computes routes via OpenRouteService (with
hardcoded fallback), simulates traffic state, generates emergency ticket and
public alerts, then POSTs to /api/crisis/simulation.

Run: python simulate.py
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE_DIR      = Path(__file__).parent
OUTPUT_DIR    = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TRACE_LOG     = OUTPUT_DIR / "agent5_trace.log"
SIM_OUTPUT    = OUTPUT_DIR / "simulation.json"

# Agent 4 writes here (backend/agents/...) — also try local path as fallback
DISPATCH_PATHS = [
    BASE_DIR / ".." / ".." / "backend" / "agents" / "agent_4_resource_dispatch" / "output" / "dispatch.json",
    BASE_DIR / ".." / "agent_4_resource_dispatch" / "output" / "dispatch.json",
]

BACKEND_URL   = os.getenv("CIRO_BACKEND_URL", "http://localhost:8000")
ORS_API_KEY   = os.getenv("ORS_API_KEY", "")
ORS_URL       = "https://api.openrouteservice.org/v2/directions/driving-car"

# Fixed demo values
CRISIS_ID     = "CRS_20260513_001"
TICKET_ID     = "EMT_2841"

open(TRACE_LOG, "w").close()


def log(level: str, message: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] AGENT_5 | {level} | {message}"
    print(line)
    with open(TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_dispatch() -> dict:
    for path in DISPATCH_PATHS:
        p = Path(path).resolve()
        if p.exists():
            log("TOOL_CALL", f"Read {p}")
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    log("WARNING", "dispatch.json not found in any expected path — using hardcoded demo order")
    return {
        "crisis_id": CRISIS_ID,
        "dispatch_plan": {
            "dispatch_orders": [{
                "order_id":        "DO_001",
                "unit":            "F-8 Rescue Unit Alpha",
                "unit_type":       "water_rescue",
                "destination":     "G-10 Sector, Islamabad",
                "destination_lat": 33.6844,
                "destination_lng": 73.0479,
                "origin_lat":      33.7080,
                "origin_lng":      73.0479,
                "reason":          "Nearest water rescue unit dispatched to G-10 flood.",
                "eta_minutes":     7,
            }],
            "resource_gaps": [],
            "priority_ranking": [],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def route_via_ors(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> dict | None:
    if not ORS_API_KEY:
        return None
    try:
        resp = httpx.post(
            ORS_URL,
            headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
            json={"coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]]},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        segment = data["routes"][0]["segments"][0]
        steps   = data["routes"][0]["geometry"]["coordinates"]
        waypoints = [[pt[1], pt[0]] for pt in steps]   # ORS returns [lng, lat]
        return {
            "via":          "OpenRouteService",
            "waypoints":    waypoints,
            "distance_km":  round(segment["distance"] / 1000, 2),
            "duration_min": round(segment["duration"] / 60),
        }
    except Exception as e:
        log("WARNING", f"ORS API failed ({e}) — using hardcoded fallback route")
        return None


def route_fallback(order: dict) -> dict:
    """
    Hardcoded demo route: F-8 Rescue Station → Margalla Road → G-10
    Srinagar Highway is blocked — alternate via Margalla Road.
    """
    origin_lat = order.get("origin_lat", 33.7080)
    origin_lng = order.get("origin_lng", 73.0479)
    dest_lat   = order.get("destination_lat", 33.6844)
    dest_lng   = order.get("destination_lng", 73.0479)

    waypoints = [
        [origin_lat, origin_lng],
        [33.7200, 73.0450],   # Margalla Road junction
        [dest_lat, dest_lng],
    ]
    return {
        "via":          "Margalla Road",
        "waypoints":    waypoints,
        "distance_km":  3.4,
        "duration_min": 7,
    }


def compute_routes(orders: list) -> list:
    routes = []
    for order in orders:
        log("TOOL_CALL", f"Route computation for {order['unit']} → {order['destination']}")
        ors = route_via_ors(
            order.get("origin_lat", 33.7080),
            order.get("origin_lng", 73.0479),
            order.get("destination_lat", 33.6844),
            order.get("destination_lng", 33.0479),
        )
        route = ors or route_fallback(order)
        source = "openrouteservice" if ors else "hardcoded_fallback"
        log("RESULT", f"{order['unit']}: {route['distance_km']}km via {route['via']} | ETA {route['duration_min']}min | source={source}")
        routes.append({
            "order_id": order["order_id"],
            "unit":     order["unit"],
            "route":    route,
            "route_reasoning": (
                f"Srinagar Highway blocked per operational picture. "
                f"Route via {route['via']} confirmed clear — distance {route['distance_km']}km, "
                f"ETA {route['duration_min']} minutes."
            ),
        })
    return routes


def simulate_traffic(orders: list) -> dict:
    congestion_pct = 61  # demo scenario fixed value
    log("DECISION", f"Traffic simulation: {len(orders)} units rerouted via Margalla Road")
    log("DECISION", f"Srinagar Highway: severe_congestion → diverted (-{congestion_pct}% congestion)")
    return {
        "before": {
            "Srinagar Highway": "severe_congestion",
        },
        "after": {
            "Srinagar Highway": "diverted",
            "Margalla Road":    "moderate",
        },
        "congestion_reduction_pct": congestion_pct,
    }


def generate_ticket(orders: list) -> dict:
    units = [o["unit"] for o in orders]
    ticket = {
        "ticket_id":  TICKET_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status":     "issued",
        "units":      units,
    }
    log("ACTION", f"Emergency ticket issued: {TICKET_ID} | units={units}")
    return ticket


def generate_alerts() -> list:
    return [
        {
            "channel":     "SMS",
            "target_area": "G-10, Islamabad",
            "message":     (
                "ALERT: Urban flooding in G-10. Avoid Srinagar Highway. "
                "Emergency services en route. Move to higher ground if possible."
            ),
        },
        {
            "channel":     "app_push",
            "target_area": "G-10, Islamabad",
            "message":     (
                "CIRO ALERT: Flooding confirmed in G-10. F-8 Rescue Unit dispatched. "
                "Use Margalla Road as alternate route."
            ),
        },
        {
            "channel":     "dashboard",
            "target_area": "G-10, Islamabad",
            "message":     (
                "Active incident — urban flooding G-10. Rescue units deployed. "
                "Traffic diverted via Margalla Road. Ticket: EMT_2841."
            ),
        },
    ]


def post_to_backend(simulation: dict):
    url = f"{BACKEND_URL}/api/crisis/simulation"
    log("ACTION", f"POST {url}")
    try:
        resp = httpx.post(url, json=simulation, timeout=10)
        resp.raise_for_status()
        log("RESULT", f"POST {url} → {resp.status_code} OK")
    except Exception as e:
        log("WARNING", f"Backend POST failed ({e}) — simulation.json saved locally")


def main():
    start = datetime.now(timezone.utc)
    log("START", "Simulation & Routing initiated")

    dispatch = load_dispatch()
    orders   = dispatch.get("dispatch_plan", {}).get("dispatch_orders", [])
    log("RESULT", f"Loaded {len(orders)} dispatch orders for routing")

    routes       = compute_routes(orders)
    traffic      = simulate_traffic(orders)
    ticket       = generate_ticket(orders)
    alerts       = generate_alerts()

    simulation = {
        "crisis_id": CRISIS_ID,
        "simulation": {
            "routes":         routes,
            "traffic_state":  traffic,
            "emergency_ticket": ticket,
            "public_alerts":  alerts,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(SIM_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(simulation, f, indent=2, ensure_ascii=False)
    log("OUTPUT", f"Written to output/simulation.json")

    post_to_backend(simulation)

    duration = (datetime.now(timezone.utc) - start).seconds
    log("END", (
        f"Duration: {duration}s | {len(routes)} routes computed | "
        f"ticket={ticket['ticket_id']} | congestion_reduction={traffic['congestion_reduction_pct']}%"
    ))


if __name__ == "__main__":
    main()
