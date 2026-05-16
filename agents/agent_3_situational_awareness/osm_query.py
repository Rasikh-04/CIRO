"""
OSM / Overpass API road network query for CIRO Agent 3.
Queries roads within the G-10 crisis bounding box, identifies closures,
and writes output/road_network.json.

Usage:
  python osm_query.py
  python osm_query.py --bbox <south> <west> <north> <east>
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

ROAD_OUTPUT = OUTPUT_DIR / "road_network.json"

# Fixed G-10 bounding box (south, west, north, east)
DEFAULT_BBOX = (33.6744, 73.0379, 33.6944, 73.0579)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Hardcoded road data for G-10 crisis zone — used when Overpass is unavailable.
# Based on OSM road data + crisis signal overlay.
FALLBACK_ROADS = [
    {
        "osm_id": "sim_001",
        "name": "Srinagar Highway",
        "highway": "primary",
        "lat": 33.6880,
        "lng": 73.0550,
        "status": "blocked",
        "closure_reason": "flooding",
        "source": "simulated",
    },
    {
        "osm_id": "sim_002",
        "name": "Jinnah Avenue",
        "highway": "primary",
        "lat": 33.6900,
        "lng": 73.0400,
        "status": "partial",
        "closure_reason": "traffic_diversion",
        "source": "simulated",
    },
    {
        "osm_id": "sim_003",
        "name": "Margalla Road",
        "highway": "secondary",
        "lat": 33.7200,
        "lng": 73.0450,
        "status": "clear",
        "closure_reason": None,
        "source": "simulated",
    },
    {
        "osm_id": "sim_004",
        "name": "G-10 Markaz Road",
        "highway": "residential",
        "lat": 33.6844,
        "lng": 73.0479,
        "status": "blocked",
        "closure_reason": "flooding",
        "source": "simulated",
    },
    {
        "osm_id": "sim_005",
        "name": "G-10/1 Internal Road",
        "highway": "residential",
        "lat": 33.6830,
        "lng": 73.0460,
        "status": "blocked",
        "closure_reason": "flooding",
        "source": "simulated",
    },
]


def _build_overpass_query(south: float, west: float, north: float, east: float) -> str:
    return (
        f"[out:json][timeout:25];"
        f"way[highway]({south},{west},{north},{east});"
        f"out center;"
    )


def _parse_overpass_response(data: dict) -> list:
    roads = []
    for element in data.get("elements", []):
        if element.get("type") != "way":
            continue
        tags = element.get("tags", {})
        center = element.get("center", {})
        roads.append({
            "osm_id": str(element.get("id", "unknown")),
            "name": tags.get("name", tags.get("ref", "Unnamed Road")),
            "highway": tags.get("highway", "unclassified"),
            "lat": center.get("lat", 0.0),
            "lng": center.get("lon", 0.0),
            "status": "unknown",
            "closure_reason": None,
            "source": "osm_live",
        })
    return roads


def _overlay_crisis_closures(roads: list) -> list:
    blocked_keywords = ["srinagar", "g-10 markaz", "g-10/1", "g-9/1"]
    partial_keywords = ["jinnah"]
    for road in roads:
        name_lower = road["name"].lower()
        if any(kw in name_lower for kw in blocked_keywords):
            road["status"] = "blocked"
            road["closure_reason"] = "flooding"
        elif any(kw in name_lower for kw in partial_keywords):
            road["status"] = "partial"
            road["closure_reason"] = "traffic_diversion"
        elif road["status"] == "unknown":
            road["status"] = "clear"
    return roads


def query_roads(bbox: tuple = DEFAULT_BBOX) -> tuple[list, str]:
    """
    Query Overpass API for roads in bbox.
    Returns (roads, source) where source is 'osm_live' or 'simulated'.
    """
    if not _HAS_REQUESTS:
        return FALLBACK_ROADS, "simulated"

    south, west, north, east = bbox
    query = _build_overpass_query(south, west, north, east)
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=15)
        resp.raise_for_status()
        roads = _parse_overpass_response(resp.json())
        if roads:
            roads = _overlay_crisis_closures(roads)
            return roads, "osm_live"
        # Empty result — fall back
        return FALLBACK_ROADS, "simulated"
    except Exception as exc:
        print(f"[osm_query] Overpass API unavailable ({exc}) — using fallback road data")
        return FALLBACK_ROADS, "simulated"


def main():
    args = sys.argv[1:]
    if "--bbox" in args:
        idx = args.index("--bbox")
        try:
            south, west, north, east = map(float, args[idx + 1:idx + 5])
            bbox = (south, west, north, east)
        except (ValueError, IndexError):
            print("Error: --bbox requires four floats: south west north east")
            sys.exit(1)
    else:
        bbox = DEFAULT_BBOX

    print(f"[osm_query] Querying road network for bbox {bbox} ...")
    roads, source = query_roads(bbox)

    output = {
        "bbox": {"south": bbox[0], "west": bbox[1], "north": bbox[2], "east": bbox[3]},
        "road_count": len(roads),
        "data_source": source,
        "roads": roads,
        "queried_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with open(ROAD_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    blocked = [r for r in roads if r["status"] == "blocked"]
    partial = [r for r in roads if r["status"] == "partial"]
    print(f"[osm_query] {len(roads)} roads found | {len(blocked)} blocked | {len(partial)} partial | source={source}")
    print(f"[osm_query] Written to {ROAD_OUTPUT}")
    return output


if __name__ == "__main__":
    main()
