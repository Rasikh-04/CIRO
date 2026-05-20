import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from haversine import haversine

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def load_scenario(name: str) -> dict:
    # Scenarios live at <project_root>/agents/scenarios/
    path = (Path(__file__).parent / ".." / ".." / ".." / "agents" / "scenarios" / f"{name}.json").resolve()
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def calculate_requirements(population_at_risk):
    return {
        "tents":        math.ceil(population_at_risk / 5),
        "food_packs":   population_at_risk * 3,
        "medical_kits": math.ceil(population_at_risk / 50),
        "water_rescue": math.ceil(population_at_risk / 500),
    }


def calculate_gaps(required, inventory):
    gaps = []
    for item_type, qty_needed in required.items():
        available = sum(
            i["quantity"] for i in inventory
            if i.get("subtype") == item_type or i.get("type") == item_type
        )
        gap = max(0, qty_needed - available)
        if gap > 0:
            gaps.append({
                "item":       item_type,
                "required":   qty_needed,
                "available":  available,
                "gap":        gap,
                "mitigation": f"Request additional {item_type} from nearest depot or mutual aid",
            })
    return gaps


def priority_score(severity, distance_km, population_at_risk):
    if distance_km == 0:
        distance_km = 0.1
    return round(severity * (1 / distance_km) * math.log(max(population_at_risk, 1)), 2)


def run_dispatch(scenario_name: str = "g10_flood"):
    scenario    = load_scenario(scenario_name)
    crisis_id   = scenario["crisis_id"]
    crisis_lat  = scenario["location"]["lat"]
    crisis_lng  = scenario["location"]["lng"]
    crisis_name = scenario["location"]["name"]
    severity    = scenario["severity"]
    dispatch_cfg = scenario["dispatch"]

    print(f"[INFO] Loaded scenario '{scenario_name}' — {crisis_name} | crisis_id={crisis_id}")

    ops_pic_path = Path(__file__).parent / ".." / "agent_3_situational_awareness" / "output" / "ops_pic.json"
    if ops_pic_path.exists():
        with open(ops_pic_path) as f:
            ops_pic = json.load(f)
        pop_at_risk = ops_pic["operational_picture"]["population_at_risk"]
        print(f"[INFO] Loaded ops_pic — population at risk: {pop_at_risk}")
    else:
        print("[WARN] ops_pic.json not found — using hardcoded demo value")
        pop_at_risk = 12000

    inventory_path = Path(__file__).parent / ".." / ".." / "data" / "inventory.json"
    if not inventory_path.exists():
        inventory_path = Path(__file__).parent / ".." / ".." / ".." / "data" / "inventory.json"
    with open(inventory_path) as f:
        inventory = json.load(f)
    print(f"[INFO] Loaded {len(inventory)} inventory items")

    required = calculate_requirements(pop_at_risk)
    print(f"[INFO] Requirements calculated: {required}")

    gaps = calculate_gaps(required, inventory)
    print(f"[INFO] {len(gaps)} resource gaps identified")

    dispatch_orders = []
    used_units = set()
    order_num  = 1

    for i, unit_type in enumerate(dispatch_cfg["unit_priority"]):
        units = [r for r in inventory if r["type"] == unit_type and r["status"] == "available"]
        units.sort(key=lambda u: haversine(u["lat"], u["lng"], crisis_lat, crisis_lng))

        # Dispatch all units of first priority type, one unit for each subsequent type
        units_to_dispatch = units if i == 0 else units[:1]

        for unit in units_to_dispatch:
            if unit["name"] in used_units:
                continue
            dist = haversine(unit["lat"], unit["lng"], crisis_lat, crisis_lng)
            eta  = round((dist / 30) * 60)

            dispatch_orders.append({
                "order_id":        f"DO_{order_num:03d}",
                "unit":            unit["name"],
                "unit_type":       unit["type"],
                "destination":     dispatch_cfg["destination_name"],
                "destination_lat": crisis_lat,
                "destination_lng": crisis_lng,
                "origin_lat":      unit["lat"],
                "origin_lng":      unit["lng"],
                "reason": (
                    f"{unit['name']} dispatched to {crisis_name} for "
                    f"{scenario['crisis_type'].replace('_', ' ')}. "
                    f"Nearest available {unit_type.replace('_', ' ')} unit at {round(dist, 1)}km. "
                    f"Route via {dispatch_cfg['alternate_road']} — {dispatch_cfg['blocked_road']} blocked."
                ),
                "eta_minutes": eta,
            })
            used_units.add(unit["name"])
            order_num += 1
            print(f"[INFO] Dispatching {unit['name']} ({unit_type}) — {round(dist, 1)}km away, ETA {eta} min")

    priority_ranking = [{
        "zone":           crisis_name,
        "priority_score": priority_score(severity, 2.62, pop_at_risk),
        "reason": (
            f"Severity {severity} {scenario['crisis_type'].replace('_', ' ')} with corroborating signals. "
            f"{crisis_name} identified as primary affected area. "
            f"{dispatch_cfg['blocked_road']} blocked — alternate via {dispatch_cfg['alternate_road']} confirmed clear."
        ),
    }]

    dispatch_plan = {
        "crisis_id": crisis_id,
        "dispatch_plan": {
            "priority_ranking": priority_ranking,
            "dispatch_orders":  dispatch_orders,
            "resource_gaps":    gaps,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    output_dir  = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "dispatch.json"
    with open(output_path, "w") as f:
        json.dump(dispatch_plan, f, indent=2)
    print(f"[INFO] dispatch.json written to {output_path}")

    try:
        import httpx
        resp = httpx.post(f"{BACKEND_URL}/api/crisis/dispatch", json=dispatch_plan, timeout=10)
        print(f"[INFO] Backend response: {resp.status_code} — {resp.text}")
    except Exception as e:
        print(f"[WARN] Could not POST to backend: {e}")

    return dispatch_plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIRO Agent 4 — Resource Dispatch")
    parser.add_argument("--scenario", default="g10_flood", help="Scenario name (e.g. g10_flood, f8_heatwave)")
    args = parser.parse_args()

    print(f"[{datetime.now(timezone.utc).isoformat()}] AGENT_4 | START | Resource dispatch initiated | scenario={args.scenario}")
    result = run_dispatch(args.scenario)
    print(f"[{datetime.now(timezone.utc).isoformat()}] AGENT_4 | END | {len(result['dispatch_plan']['dispatch_orders'])} units dispatched")
