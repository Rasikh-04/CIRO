import json, math, os, sys
from datetime import datetime, timezone
from haversine import haversine

# ── Fixed demo scenario values ──────────────────────────────────────────────
CRISIS_ID   = "CRS_20260513_001"
CRISIS_LAT  = 33.6844
CRISIS_LNG  = 73.0479
SEVERITY    = 4

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── OCHA standard rates ──────────────────────────────────────────────────────
def calculate_requirements(population_at_risk):
    return {
        "tents":        math.ceil(population_at_risk / 5),
        "food_packs":   population_at_risk * 3,
        "medical_kits": math.ceil(population_at_risk / 50),
        "water_rescue": math.ceil(population_at_risk / 500),
    }

# ── Gap calculation ──────────────────────────────────────────────────────────
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
                "mitigation": f"Request additional {item_type} from nearest depot or mutual aid"
            })
    return gaps

# ── Priority score formula ───────────────────────────────────────────────────
def priority_score(severity, distance_km, population_at_risk):
    if distance_km == 0:
        distance_km = 0.1
    return round(severity * (1 / distance_km) * math.log(max(population_at_risk, 1)), 2)

# ── Main dispatch logic ──────────────────────────────────────────────────────
def run_dispatch():
    # Load ops_pic from file (written by Agent 3)
    ops_pic_path = os.path.join(os.path.dirname(__file__), "..", "agent_3_situational_awareness", "output", "ops_pic.json")

    if os.path.exists(ops_pic_path):
        with open(ops_pic_path) as f:
            ops_pic = json.load(f)
        pop_at_risk = ops_pic["operational_picture"]["population_at_risk"]
        print(f"[INFO] Loaded ops_pic — population at risk: {pop_at_risk}")
    else:
        # Fallback to hardcoded demo values if Agent 3 hasn't run yet
        print("[WARN] ops_pic.json not found — using hardcoded demo values")
        pop_at_risk = 12000

    # Load inventory
    inventory_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "data", "inventory.json")
    if not os.path.exists(inventory_path):
        inventory_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "inventory.json")

    with open(inventory_path) as f:
        inventory = json.load(f)
    print(f"[INFO] Loaded {len(inventory)} inventory items")

    # Calculate requirements
    required = calculate_requirements(pop_at_risk)
    print(f"[INFO] Requirements calculated: {required}")

    # Calculate gaps
    gaps = calculate_gaps(required, inventory)
    print(f"[INFO] {len(gaps)} resource gaps identified")

    # Build dispatch orders — pick nearest available unit per type
    dispatch_orders = []
    used_units = set()
    order_num = 1

    # Priority 1: water rescue units (flood scenario)
    rescue_units = [
        r for r in inventory
        if r["type"] == "water_rescue" and r["status"] == "available"
    ]
    rescue_units.sort(key=lambda u: haversine(u["lat"], u["lng"], CRISIS_LAT, CRISIS_LNG))

    for unit in rescue_units:
        if unit["name"] in used_units:
            continue
        dist = haversine(unit["lat"], unit["lng"], CRISIS_LAT, CRISIS_LNG)
        eta  = round((dist / 30) * 60)  # 30 km/h average speed
        score = priority_score(SEVERITY, dist, pop_at_risk)

        dispatch_orders.append({
            "order_id":        f"DO_{order_num:03d}",
            "unit":            unit["name"],
            "unit_type":       unit["type"],
            "destination":     "G-10 Sector, Islamabad",
            "destination_lat": CRISIS_LAT,
            "destination_lng": CRISIS_LNG,
            "origin_lat":      unit["lat"],
            "origin_lng":      unit["lng"],
            "reason": (
                f"Urban flooding requires water rescue capability. "
                f"{unit['name']} is the nearest available water rescue unit at {dist}km from crisis center. "
                f"Routed via Margalla Road — Srinagar Highway is blocked per operational picture."
            ),
            "eta_minutes": eta
        })
        used_units.add(unit["name"])
        order_num += 1
        print(f"[INFO] Dispatching {unit['name']} — {dist}km away, ETA {eta} min")

    # Priority 2: ambulance
    ambulances = [
        r for r in inventory
        if r["type"] == "ambulance" and r["status"] == "available"
    ]
    ambulances.sort(key=lambda u: haversine(u["lat"], u["lng"], CRISIS_LAT, CRISIS_LNG))

    for unit in ambulances[:1]:  # dispatch 1 ambulance
        dist = haversine(unit["lat"], unit["lng"], CRISIS_LAT, CRISIS_LNG)
        eta  = round((dist / 30) * 60)
        dispatch_orders.append({
            "order_id":        f"DO_{order_num:03d}",
            "unit":            unit["name"],
            "unit_type":       unit["type"],
            "destination":     "G-10 Sector, Islamabad",
            "destination_lat": CRISIS_LAT,
            "destination_lng": CRISIS_LNG,
            "origin_lat":      unit["lat"],
            "origin_lng":      unit["lng"],
            "reason": (
                f"Medical support required for flood victims. "
                f"{unit['name']} dispatched from {unit['depot']} at {dist}km distance. "
                f"Proceeding via alternate route due to Srinagar Highway blockage."
            ),
            "eta_minutes": eta
        })
        order_num += 1
        print(f"[INFO] Dispatching {unit['name']} — {dist}km away, ETA {eta} min")

    # Priority ranking
    priority_ranking = [{
        "zone":           "G-10, Islamabad",
        "priority_score": priority_score(SEVERITY, 2.62, pop_at_risk),
        "reason": (
            "Highest severity flood event with 3 corroborating signals. "
            "G-10 has highest population density in affected area. "
            "Main artery (Srinagar Highway) blocked — alternate via Margalla Road confirmed clear."
        )
    }]

    # Build final dispatch plan
    dispatch_plan = {
        "crisis_id": CRISIS_ID,
        "dispatch_plan": {
            "priority_ranking": priority_ranking,
            "dispatch_orders":  dispatch_orders,
            "resource_gaps":    gaps
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    # Write output
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "dispatch.json")

    with open(output_path, "w") as f:
        json.dump(dispatch_plan, f, indent=2)
    print(f"[INFO] dispatch.json written to {output_path}")

    # POST to backend
    try:
        import httpx
        resp = httpx.post(f"{BACKEND_URL}/api/crisis/dispatch", json=dispatch_plan, timeout=10)
        print(f"[INFO] Backend response: {resp.status_code} — {resp.text}")
    except Exception as e:
        print(f"[WARN] Could not POST to backend: {e}")
        print("[INFO] dispatch.json still written — POST manually if needed")

    return dispatch_plan

if __name__ == "__main__":
    print(f"[{datetime.now(timezone.utc).isoformat()}] AGENT_4 | START | Resource dispatch initiated")
    result = run_dispatch()
    print(f"[{datetime.now(timezone.utc).isoformat()}] AGENT_4 | END | {len(result['dispatch_plan']['dispatch_orders'])} units dispatched")
