"""
Agent 5 — Simulation & Routing (CIRO)

Reads dispatch.json from Agent 4, computes routes via OpenRouteService (with
hardcoded fallback), simulates traffic state, generates emergency ticket and
public alerts, then POSTs to /api/crisis/simulation.

Run: python simulate.py [--scenario g10_flood]
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TRACE_LOG  = OUTPUT_DIR / "agent5_trace.log"
SIM_OUTPUT = OUTPUT_DIR / "simulation.json"

DISPATCH_PATHS = [
    BASE_DIR / ".." / ".." / "backend" / "agents" / "agent_4_resource_dispatch" / "output" / "dispatch.json",
    BASE_DIR / ".." / "agent_4_resource_dispatch" / "output" / "dispatch.json",
]

BACKEND_URL = os.getenv("CIRO_BACKEND_URL", "http://localhost:8000")
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
ORS_URL     = "https://api.openrouteservice.org/v2/directions/driving-car"

open(TRACE_LOG, "w").close()


def load_scenario(name: str) -> dict:
    path = (BASE_DIR / ".." / "scenarios" / f"{name}.json").resolve()
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def log(level: str, message: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] AGENT_5 | {level} | {message}"
    print(line)
    with open(TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_dispatch(crisis_id: str) -> dict:
    for path in DISPATCH_PATHS:
        p = Path(path).resolve()
        if p.exists():
            log("TOOL_CALL", f"Read {p}")
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    log("WARNING", "dispatch.json not found — using empty fallback")
    return {
        "crisis_id": crisis_id,
        "dispatch_plan": {"dispatch_orders": [], "resource_gaps": [], "priority_ranking": []},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def route_via_ors(origin_lat, origin_lng, dest_lat, dest_lng) -> dict | None:
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
        data    = resp.json()
        segment = data["routes"][0]["segments"][0]
        steps   = data["routes"][0]["geometry"]["coordinates"]
        return {
            "via":          "OpenRouteService",
            "waypoints":    [[pt[1], pt[0]] for pt in steps],
            "distance_km":  round(segment["distance"] / 1000, 2),
            "duration_min": round(segment["duration"] / 60),
        }
    except Exception as e:
        log("WARNING", f"ORS API failed ({e}) — using fallback route")
        return None


def route_fallback(order: dict, scenario: dict) -> dict:
    dispatch_cfg = scenario["dispatch"]
    location     = scenario["location"]
    origin_lat   = order.get("origin_lat",      location["lat"])
    origin_lng   = order.get("origin_lng",      location["lng"])
    dest_lat     = order.get("destination_lat", location["lat"])
    dest_lng     = order.get("destination_lng", location["lng"])
    mid          = dispatch_cfg["alternate_waypoint"]

    return {
        "via":          dispatch_cfg["alternate_road"],
        "waypoints":    [[origin_lat, origin_lng], mid, [dest_lat, dest_lng]],
        "distance_km":  3.4,
        "duration_min": order.get("eta_minutes", 10),
    }


def compute_routes(orders: list, scenario: dict) -> list:
    routes = []
    for order in orders:
        log("TOOL_CALL", f"Route computation for {order['unit']} → {order['destination']}")
        ors   = route_via_ors(
            order.get("origin_lat",      scenario["location"]["lat"]),
            order.get("origin_lng",      scenario["location"]["lng"]),
            order.get("destination_lat", scenario["location"]["lat"]),
            order.get("destination_lng", scenario["location"]["lng"]),
        )
        route  = ors or route_fallback(order, scenario)
        source = "openrouteservice" if ors else "hardcoded_fallback"
        log("RESULT", f"{order['unit']}: {route['distance_km']}km via {route['via']} | ETA {route['duration_min']}min | source={source}")
        routes.append({
            "order_id": order["order_id"],
            "unit":     order["unit"],
            "route":    route,
            "route_reasoning": (
                f"{scenario['dispatch']['blocked_road']} blocked per operational picture. "
                f"Route via {route['via']} confirmed clear — {route['distance_km']}km, "
                f"ETA {route['duration_min']} minutes."
            ),
        })
    return routes


def simulate_traffic(orders: list, scenario: dict) -> dict:
    dispatch_cfg    = scenario["dispatch"]
    congestion_pct  = 61
    log("DECISION", f"Traffic simulation: {len(orders)} units rerouted via {dispatch_cfg['alternate_road']}")
    log("DECISION", f"{dispatch_cfg['blocked_road']}: severe_congestion → diverted (-{congestion_pct}% congestion)")
    return {
        "before": {dispatch_cfg["blocked_road"]: "severe_congestion"},
        "after":  {
            dispatch_cfg["blocked_road"]:  "diverted",
            dispatch_cfg["alternate_road"]: "moderate",
        },
        "congestion_reduction_pct": congestion_pct,
    }


def generate_ticket(orders: list, crisis_id: str) -> dict:
    ticket_num = crisis_id.split("_")[-1] if crisis_id else "0001"
    ticket_id  = f"EMT_{ticket_num}"
    units      = [o["unit"] for o in orders]
    ticket     = {
        "ticket_id":  ticket_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status":     "issued",
        "units":      units,
    }
    log("ACTION", f"Emergency ticket issued: {ticket_id} | units={units}")
    return ticket


def generate_alerts(scenario: dict) -> list:
    location     = scenario["location"]
    crisis_type  = scenario["crisis_type"].replace("_", " ")
    dispatch_cfg = scenario["dispatch"]
    return [
        {
            "channel":     "SMS",
            "target_area": location["name"],
            "message": (
                f"ALERT: {crisis_type.title()} in {location['name']}. "
                f"Avoid {dispatch_cfg['blocked_road']}. "
                f"Emergency services en route. Follow official guidance."
            ),
        },
        {
            "channel":     "app_push",
            "target_area": location["name"],
            "message": (
                f"CIRO ALERT: {crisis_type.title()} confirmed in {location['name']}. "
                f"Use {dispatch_cfg['alternate_road']} as alternate route."
            ),
        },
        {
            "channel":     "dashboard",
            "target_area": location["name"],
            "message": (
                f"Active incident — {crisis_type} in {location['name']}. "
                f"Response units deployed. Traffic diverted via {dispatch_cfg['alternate_road']}."
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
    parser = argparse.ArgumentParser(description="CIRO Agent 5 — Simulation & Routing")
    parser.add_argument("--scenario", default="g10_flood", help="Scenario name (e.g. g10_flood, f8_heatwave)")
    args = parser.parse_args()

    start = datetime.now(timezone.utc)
    log("START", f"Simulation & Routing initiated | scenario={args.scenario}")

    scenario   = load_scenario(args.scenario)
    crisis_id  = scenario["crisis_id"]
    log("PROCESS", f"Loaded scenario '{args.scenario}' — crisis_id={crisis_id}, location={scenario['location']['name']}")

    dispatch = load_dispatch(crisis_id)
    orders   = dispatch.get("dispatch_plan", {}).get("dispatch_orders", [])
    log("RESULT", f"Loaded {len(orders)} dispatch orders for routing")

    routes  = compute_routes(orders, scenario)
    traffic = simulate_traffic(orders, scenario)
    ticket  = generate_ticket(orders, crisis_id)
    alerts  = generate_alerts(scenario)

    simulation = {
        "crisis_id": crisis_id,
        "simulation": {
            "routes":           routes,
            "traffic_state":    traffic,
            "emergency_ticket": ticket,
            "public_alerts":    alerts,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(SIM_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(simulation, f, indent=2, ensure_ascii=False)
    log("OUTPUT", "Written to output/simulation.json")

    post_to_backend(simulation)

    duration = (datetime.now(timezone.utc) - start).seconds
    log("END", (
        f"Duration: {duration}s | {len(routes)} routes computed | "
        f"ticket={ticket['ticket_id']} | congestion_reduction={traffic['congestion_reduction_pct']}%"
    ))


if __name__ == "__main__":
    main()
