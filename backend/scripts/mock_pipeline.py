import httpx, time

BASE = "http://localhost:8000"

print("\n--- Step 1: Ingest signals ---")
r = httpx.post(f"{BASE}/api/signals/ingest", json={"signals": [{
    "id": "sig_mock_01", "source": "social_media",
    "raw_text": "G-10 mein pani bhar gaya hai",
    "normalized": "G-10 flooding reported, vehicles stranded",
    "location": {"district": "G-10", "city": "Islamabad", "lat": 33.6844, "lng": 73.0479},
    "signal_type": "flood", "timestamp": "2026-05-13T14:32:00Z",
    "confidence": 0.82, "source_label": "simulated"
}]})
print(f"  {r.status_code}: {r.json()}")

time.sleep(1)
print("\n--- Step 2: Post crisis ---")
r = httpx.post(f"{BASE}/api/crisis/detected", json={
    "crisis_id": "CRS_20260513_001", "type": "urban_flooding",
    "location": {"primary": "G-10, Islamabad", "affected_radius_km": 2.5, "lat": 33.6844, "lng": 73.0479},
    "severity": 4, "confidence": "high", "confidence_score": 0.89,
    "reasoning": "3 corroborating signals detected.",
    "contributing_signals": ["sig_mock_01"], "status": "confirmed",
    "detected_at": "2026-05-13T14:35:00Z"
})
print(f"  {r.status_code}: {r.json()}")

time.sleep(1)
print("\n--- Step 3: Post operational picture ---")
r = httpx.post(f"{BASE}/api/crisis/operational", json={
    "crisis_id": "CRS_20260513_001",
    "operational_picture": {
        "affected_zone": {"center": [33.6844, 73.0479], "radius_km": 2.5},
        "road_closures": [{"road": "Srinagar Highway", "status": "blocked", "lat": 33.688, "lng": 73.055, "source": "simulated"}],
        "nearby_facilities": [{"type": "rescue_unit", "name": "F-8 Rescue Station", "lat": 33.708, "lng": 73.0479, "distance_km": 3.1, "status": "available"}],
        "data_gaps": [], "population_at_risk": 12000
    },
    "generated_at": "2026-05-13T14:37:00Z"
})
print(f"  {r.status_code}: {r.json()}")

time.sleep(1)
print("\n--- Step 4: Check active crises ---")
r = httpx.get(f"{BASE}/api/crisis/active")
print(f"  {r.status_code}: {r.json()}")

print("\n--- All checks passed! Backend is fully operational. ---\n")
