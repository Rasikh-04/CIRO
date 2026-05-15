# CIRO — Supplementary Reference
## Mock Data Templates, Antigravity Tips, API References, Submission Notes

---

## 1. Complete Mock Data Files

### `data/mock_social_media.json`
```json
[
  {
    "id": "sm_001",
    "platform": "Twitter/X",
    "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain #G10 #Islamabad",
    "timestamp": "2026-05-13T14:30:00Z",
    "user_location": "Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_002",
    "platform": "Twitter/X",
    "text": "Flash flood happening at G-10 for past 30 mins, roads completely blocked near the park",
    "timestamp": "2026-05-13T14:31:00Z",
    "user_location": "G-10, Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_003",
    "platform": "WhatsApp (forwarded)",
    "text": "Bhai G-10 sector mein sari galiyaan doob gayi hain, ambulance bhi nahi aa sakti",
    "timestamp": "2026-05-13T14:32:00Z",
    "user_location": null,
    "source": "simulated"
  },
  {
    "id": "sm_004",
    "platform": "Twitter/X",
    "text": "Srinagar Highway band ho gaya hai G-10 ke paas, traffic jam har jagah",
    "timestamp": "2026-05-13T14:33:00Z",
    "user_location": "Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_005",
    "platform": "Twitter/X",
    "text": "Cars stranded on main road near G-10 markaz, water level rising fast",
    "timestamp": "2026-05-13T14:34:00Z",
    "user_location": "G-10",
    "source": "simulated"
  },
  {
    "id": "sm_006",
    "platform": "Facebook",
    "text": "G-9 mein bhi paani aa gaya, G-10 wali situation zyada kharab lag rahi hai",
    "timestamp": "2026-05-13T14:35:00Z",
    "user_location": "G-9, Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_007",
    "platform": "Twitter/X",
    "text": "When will Islamabad fix its drainage system? This happens every monsoon. G-10 flooded AGAIN",
    "timestamp": "2026-05-13T14:36:00Z",
    "user_location": "Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_008",
    "platform": "Twitter/X",
    "text": "F-8 mein sab theek hai abhi, G-10 waale relatives se contact nahi ho raha",
    "timestamp": "2026-05-13T14:37:00Z",
    "user_location": "F-8, Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_009",
    "platform": "Twitter/X",
    "text": "Just a normal Tuesday in Islamabad lol picnic in G-10",
    "timestamp": "2026-05-13T14:20:00Z",
    "user_location": "Islamabad",
    "source": "simulated",
    "note": "Noise/sarcasm — Agent 2 should not cluster this as crisis signal"
  },
  {
    "id": "sm_010",
    "platform": "Twitter/X",
    "text": "G-10 flooding update: rescue teams reportedly deployed but situation still critical, avoid area",
    "timestamp": "2026-05-13T14:40:00Z",
    "user_location": "G-10",
    "source": "simulated"
  }
]
```

### `data/facilities_db.json`
```json
[
  {
    "id": "fac_001",
    "type": "rescue_unit",
    "name": "F-8 Rescue Station",
    "lat": 33.7080,
    "lng": 73.0479,
    "status": "available",
    "units": [
      { "id": "res_001", "name": "F-8 Rescue Unit Alpha", "type": "water_rescue", "status": "available" },
      { "id": "res_002", "name": "F-8 Rescue Unit Beta", "type": "water_rescue", "status": "available" }
    ],
    "source": "simulated"
  },
  {
    "id": "fac_002",
    "type": "hospital",
    "name": "PIMS Hospital",
    "lat": 33.7161,
    "lng": 73.0738,
    "status": "operational",
    "capacity_remaining": 120,
    "source": "simulated"
  },
  {
    "id": "fac_003",
    "type": "fire_station",
    "name": "I-8 Fire Station",
    "lat": 33.6950,
    "lng": 73.0650,
    "status": "available",
    "source": "simulated"
  },
  {
    "id": "fac_004",
    "type": "depot",
    "name": "G-9 Emergency Supply Depot",
    "lat": 33.7006,
    "lng": 73.0322,
    "status": "operational",
    "inventory_summary": "tents: 50, food_packs: 300, medical_kits: 20",
    "source": "simulated"
  },
  {
    "id": "fac_005",
    "type": "police",
    "name": "G-10 Police Station",
    "lat": 33.6910,
    "lng": 73.0450,
    "status": "deployed",
    "note": "Already at scene managing traffic",
    "source": "simulated"
  }
]
```

### `data/inventory.json`
```json
[
  {
    "id": "inv_001",
    "name": "F-8 Rescue Unit Alpha",
    "type": "water_rescue",
    "depot": "F-8 Rescue Station",
    "lat": 33.7080,
    "lng": 73.0479,
    "status": "available",
    "quantity": 1,
    "source": "simulated"
  },
  {
    "id": "inv_002",
    "name": "F-8 Rescue Unit Beta",
    "type": "water_rescue",
    "depot": "F-8 Rescue Station",
    "lat": 33.7080,
    "lng": 73.0479,
    "status": "available",
    "quantity": 1,
    "source": "simulated"
  },
  {
    "id": "inv_003",
    "name": "Rescue Ambulance Unit 1",
    "type": "ambulance",
    "depot": "PIMS Hospital",
    "lat": 33.7161,
    "lng": 73.0738,
    "status": "available",
    "quantity": 1,
    "source": "simulated"
  },
  {
    "id": "inv_004",
    "name": "Emergency Tent Pack",
    "type": "supplies",
    "subtype": "tents",
    "depot": "G-9 Emergency Supply Depot",
    "lat": 33.7006,
    "lng": 73.0322,
    "status": "available",
    "quantity": 50,
    "unit": "units",
    "source": "simulated"
  },
  {
    "id": "inv_005",
    "name": "Food Relief Packs",
    "type": "supplies",
    "subtype": "food_packs",
    "depot": "G-9 Emergency Supply Depot",
    "lat": 33.7006,
    "lng": 73.0322,
    "status": "available",
    "quantity": 300,
    "unit": "packs",
    "source": "simulated"
  },
  {
    "id": "inv_006",
    "name": "Rubber Rescue Boats",
    "type": "equipment",
    "subtype": "rubber_boats",
    "depot": "F-8 Rescue Station",
    "lat": 33.7080,
    "lng": 73.0479,
    "status": "available",
    "quantity": 2,
    "source": "simulated"
  }
]
```

---

## 2. Antigravity Power Tips

### Setting Up Agent Workspaces
1. Open Antigravity → Agent Manager
2. Click "Add Workspace" for each agent folder
3. Name each workspace clearly: "CIRO — Agent 1: Signal Ingestion"
4. Keep all 6 workspaces visible in the Manager — this is your demo's visual proof of multi-agent orchestration

### Getting the Best Results from Agents
- **Be explicit in prompts**: list every step numbered. Agents follow numbered lists reliably.
- **Specify output format**: always say "Return JSON only" or "Write to output/filename.json"
- **Test one step at a time**: if a prompt has 10 steps, test steps 1-3 first, then expand
- **Use @filename references**: in the prompt, reference `@mock_social_media.json` — Antigravity will read it
- **Knowledge Base**: save your Gemini prompts as Knowledge Base snippets in Antigravity — makes them reusable across agents

### For the Demo Recording
- Set terminal execution to "Always Proceed" — no permission prompts during recording
- Set review policy to "Agent Decides" — smooth flow
- Pre-test the full pipeline once; if it works, immediately record. Don't keep tweaking.
- Keep Agent Manager visible alongside the running output — judges want to see both

### Extracting Trace Logs
After each agent run, export the conversation as a text file:
- Agent Manager → select the conversation → Export → Text/Markdown
- Name each export `agent_N_trace.txt`
- Concatenate into `CIRO_agent_trace.log` for submission

---

## 3. OpenRouteService Routing — Code Template

```python
# agents/agent_5_simulation/route_engine.py
import httpx
import os

ORS_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY")

def get_route(origin_lat, origin_lng, dest_lat, dest_lng, avoid_coords=None):
    """
    Returns route from origin to destination.
    avoid_coords: list of [lng, lat] pairs defining a polygon to avoid
    """
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "coordinates": [
            [origin_lng, origin_lat],
            [dest_lng, dest_lat]
        ]
    }
    
    if avoid_coords:
        body["options"] = {
            "avoid_polygons": {
                "type": "Polygon",
                "coordinates": [avoid_coords]
            }
        }
    
    response = httpx.post(
        "https://api.openrouteservice.org/v2/directions/driving-car",
        headers=headers,
        json=body
    )
    
    if response.status_code != 200:
        # Fallback: straight-line distance
        return {
            "via": "Direct route (API unavailable)",
            "waypoints": [[origin_lat, origin_lng], [dest_lat, dest_lng]],
            "distance_km": haversine(origin_lat, origin_lng, dest_lat, dest_lng),
            "duration_min": round(haversine(origin_lat, origin_lng, dest_lat, dest_lng) / 0.5),
            "fallback": True
        }
    
    route = response.json()["routes"][0]
    summary = route["summary"]
    
    # Decode geometry
    waypoints = decode_polyline(route["geometry"])
    
    return {
        "via": "OpenRouteService",
        "waypoints": waypoints[:10],  # Sample 10 waypoints
        "distance_km": round(summary["distance"] / 1000, 2),
        "duration_min": round(summary["duration"] / 60),
        "fallback": False
    }

def haversine(lat1, lng1, lat2, lng2):
    from math import radians, cos, sin, asin, sqrt
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return round(2 * R * asin(sqrt(a)), 2)

def decode_polyline(encoded):
    """Decode Google/ORS encoded polyline to list of [lat, lng]"""
    # Simple implementation — install polyline package for production
    # pip install polyline
    import polyline
    return [[lat, lng] for lat, lng in polyline.decode(encoded)]
```

---

## 4. SITREP Template (Agent 6 Gemini Prompt)

```
Generate a professional situation report (SITREP) in the following format.
Use the crisis data provided. Be concise and factual. No fluff.

Crisis Data:
{crisis_json}

Dispatch Data:
{dispatch_json}

Simulation Data:
{simulation_json}

---
SITUATION REPORT
Date/Time: {datetime}
Crisis ID: {crisis_id}
Prepared by: CIRO Automated System

1. SITUATION
   Type: {type} | Location: {location} | Severity: {severity}/5
   [2-3 sentences describing the current situation based on confirmed signals]

2. AFFECTED AREA
   [1-2 sentences on geographic scope and population at risk]

3. ACTIONS TAKEN
   [Bulleted list of dispatch orders with unit name, destination, and ETA]

4. RESOURCES DEPLOYED
   [List of all units and supplies dispatched]

5. SIMULATED OUTCOME
   Congestion reduction: {pct}%
   Units on scene: {count}
   Emergency ticket: {ticket_id}

6. PUBLIC GUIDANCE
   [2-3 actionable sentences for affected residents]

7. NEXT UPDATE
   Scheduled: +30 minutes

---
Return this as formatted markdown. Do not add any text outside the report template.
```

---

## 5. README Structure (Copy and Fill In)

```markdown
# CIRO — Crisis Intelligence & Response Orchestrator

## What It Does
[2-3 sentences]

## System Architecture
[Paste architecture diagram from 02_system_architecture.md]

## Agent Pipeline
[Brief description of each agent]

## Google Antigravity Usage
CIRO uses Antigravity as the central orchestration layer. All 6 agents run as 
separate workspaces in Antigravity's Agent Manager. Antigravity's browser tool 
enables agents to call external APIs (Open-Meteo, Overpass, OpenRouteService). 
Gemini 3.1 Pro handles natural language tasks: Urdu/English normalization (Agent 1), 
confidence reasoning (Agent 2), and SITREP generation (Agent 6). Additional LLMs 
were not used — all AI workloads run through Antigravity's built-in Gemini access.

## Tools & APIs Used
| Tool | Purpose | Real/Simulated |
|---|---|---|
| Open-Meteo | Weather data | Real |
| Overpass API | OSM road network | Real |
| OpenRouteService | Route optimization | Real |
| Google Maps | Mobile map display | Real |
| Gemini 3.1 Pro | Text tasks via Antigravity | Real |
| Social media posts | Signal inputs | **Simulated** |
| Emergency inventory | Resource data | **Simulated** |
| Traffic state | Simulation output | **Simulated** |

## Assumptions
- Crisis scenario is limited to G-10, Islamabad for the prototype
- Emergency resource inventory reflects a plausible but simulated dataset
- Population at risk estimates are district-level approximations
- Routing avoidance polygons are approximated from traffic reports, not real-time sensors

## Privacy Note
No real personal data is used. All social media posts are synthetically generated.
No real user location data is collected or stored.

## Cost Estimate
- Open-Meteo: Free (no cost)
- Overpass API: Free (no cost)
- OpenRouteService: Free tier, ~6 calls per demo run (~$0)
- Google Maps: Free tier covers 1,000+ demo runs
- Gemini via Antigravity: Covered by Antigravity's free preview quota
- Google Cloud Run: ~$0.002 per demo run (minimal compute)
- **Total cost per demo run: ~$0.002**

## Scalability
- Cloud Run auto-scales to handle 10x concurrent crises
- Agent pipeline is stateless — each crisis runs independently
- At 100x scale: database needs connection pooling (PgBouncer); agents need a queue (Cloud Tasks)
- Latency: ~50s end-to-end pipeline for a single crisis event

## Baseline Comparison
| Metric | Without CIRO | With CIRO |
|---|---|---|
| Time to crisis detection | 20-45 min (manual) | <2 min (automated) |
| Dispatch decision | Committee process | <5 min (agent-ranked) |
| Coordination | Phone calls, fragmented | Unified dashboard, auto-SITREP |
| Public alerts | Delayed, manually drafted | Automated, within pipeline |

## Limitations
- Simulated inventory does not reflect real NDMA resource data
- Agent pipeline requires manual trigger (automation possible with Cloud Scheduler)
- Mobile app uses polling; production would use native push notifications
- SITREP format does not match official NDMA template (would require field validation)

## Setup Instructions
[See 07_integration_guide.md Section 3]

## Team
- [Team Lead]: Antigravity orchestration, web dashboard, mobile app
- [Member 2]: Signal ingestion, crisis detection, Gemini prompts
- [Member 3]: Backend, database, routing simulation, Cloud Run
```

---

## 6. Robustness Scenarios to Document

The hackathon requires "at least one failure, edge case, contradiction, missing data, or fallback scenario demonstrated."

**Recommended scenario for demo:** OpenRouteService returns 429 (rate limit) during Agent 5.

What the agent should do:
1. Log: `[WARN] OpenRouteService rate limited — activating fallback routing`
2. Switch to straight-line distance + fixed speed assumption
3. Note in simulation output: `"route_source": "fallback_haversine"` + `"note": "ORS unavailable; straight-line estimate used"`
4. Continue pipeline — do not halt

This is a realistic, demonstrable failure that shows the system is resilient. Build it intentionally.
