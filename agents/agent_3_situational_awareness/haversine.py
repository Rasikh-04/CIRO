"""
Haversine distance calculator for CIRO Agent 3.
Importable as a module or run standalone:
  python haversine.py <lat1> <lng1> <lat2> <lng2>
  python haversine.py --from-crisis <facility_lat> <facility_lng>
"""
import json
import sys
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

CRISIS_LAT = 33.6844
CRISIS_LNG = 73.0479

FACILITIES_DB = Path(__file__).parent.parent.parent / "backend" / "data" / "facilities_db.json"


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in km between two lat/lng points."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return round(2 * R * asin(sqrt(a)), 3)


def distance_from_crisis(facility_lat: float, facility_lng: float) -> float:
    """Distance in km from the fixed crisis center (G-10, 33.6844, 73.0479)."""
    return haversine(CRISIS_LAT, CRISIS_LNG, facility_lat, facility_lng)


def rank_facilities(crisis_lat: float = CRISIS_LAT, crisis_lng: float = CRISIS_LNG) -> list:
    """Load facilities_db.json, compute distance from crisis center, return sorted list."""
    with open(FACILITIES_DB, encoding="utf-8") as f:
        facilities = json.load(f)
    results = []
    for fac in facilities:
        dist = haversine(crisis_lat, crisis_lng, fac["lat"], fac["lng"])
        results.append({
            "id": fac["id"],
            "type": fac["type"],
            "name": fac["name"],
            "lat": fac["lat"],
            "lng": fac["lng"],
            "distance_km": dist,
            "status": fac.get("status", "unknown"),
        })
    results.sort(key=lambda x: x["distance_km"])
    return results


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python haversine.py <lat1> <lng1> <lat2> <lng2>")
        print("  python haversine.py --from-crisis <facility_lat> <facility_lng>")
        print("  python haversine.py --rank-facilities")
        sys.exit(0)

    if args[0] == "--rank-facilities":
        results = rank_facilities()
        print(json.dumps(results, indent=2))
        return

    if args[0] == "--from-crisis" and len(args) == 3:
        lat, lng = float(args[1]), float(args[2])
        dist = distance_from_crisis(lat, lng)
        print(f"Distance from crisis center ({CRISIS_LAT}, {CRISIS_LNG}) to ({lat}, {lng}): {dist} km")
        return

    if len(args) == 4:
        lat1, lng1, lat2, lng2 = map(float, args)
        dist = haversine(lat1, lng1, lat2, lng2)
        print(f"Distance from ({lat1}, {lng1}) to ({lat2}, {lng2}): {dist} km")
        return

    print("Error: unrecognised arguments. Run without arguments for usage.")
    sys.exit(1)


if __name__ == "__main__":
    main()
