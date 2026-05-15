# CIRO — Complete System Architecture
## Base Truth Document (v1.0 — May 13, 2026)

> **This is the authoritative reference for all architectural decisions.**  
> Any deviation from this document must be discussed with the team lead and reflected here before implementation.

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CIRO SYSTEM                              │
│                                                                 │
│  ┌─────────────┐    ┌──────────────────────────────────────┐   │
│  │  LAYER 1    │    │              LAYER 2                  │   │
│  │  Crisis     │───▶│       Response Orchestration          │   │
│  │Intelligence │    │                                       │   │
│  └─────────────┘    └──────────────────────────────────────┘   │
│         │                          │                            │
│         ▼                          ▼                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ANTIGRAVITY AGENT MANAGER                  │   │
│  │         (Orchestration Layer — 6 Agents)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  FastAPI     │   │  PostgreSQL   │   │  Google Cloud    │   │
│  │  Backend     │   │  + PostGIS   │   │  Run             │   │
│  └──────────────┘   └──────────────┘   └──────────────────┘   │
│         │                                                       │
│    ┌────┴────┐                                                  │
│    ▼         ▼                                                  │
│  Web App   Mobile App                                           │
│ (Dashboard)(Public)                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Architecture

### Agent 1 — Signal Ingestion Agent
**Owner:** Member 2  
**Runs in:** Antigravity Agent Manager (separate workspace)

**Inputs:**
- Simulated social media posts (JSON mock dataset — Urdu/English)
- Open-Meteo weather API (real)
- Google Maps Traffic API or simulated traffic data

**Processing:**
- Normalizes all incoming signals into a standard `SignalEvent` schema
- Handles noisy/informal Urdu text via Gemini 3.1 Pro prompt
- Tags each signal with: source, location, timestamp, signal_type, raw_text

**Output (JSON artifact):**
```json
{
  "signals": [
    {
      "id": "sig_001",
      "source": "social_media",
      "raw_text": "G-10 mein pani bhar gaya hai",
      "normalized": "G-10 flooding reported, vehicles stranded",
      "location": { "district": "G-10", "city": "Islamabad", "lat": 33.6844, "lng": 73.0479 },
      "signal_type": "flood",
      "timestamp": "2026-05-13T14:32:00Z",
      "confidence": 0.82
    }
  ],
  "ingest_timestamp": "2026-05-13T14:33:00Z"
}
```

**Triggers Agent 2** when: ≥2 signals within 5km radius of the same type within 30 minutes

---

### Agent 2 — Crisis Detection & Classification Agent
**Owner:** Member 2  
**Runs in:** Antigravity Agent Manager

**Inputs:**
- Output from Agent 1 (`SignalEvent[]`)
- Threshold configuration (configurable: min signals, time window, radius)

**Processing:**
- Clusters related signals by location + type
- Cross-references weather + traffic signals for corroboration
- Classifies crisis: `flood | heatwave | accident | road_blockage | infrastructure_failure`
- Generates confidence score + natural language reasoning explanation
- Gemini 3.1 Pro generates the explanation text

**Output (JSON artifact):**
```json
{
  "crisis_id": "CRS_20260513_001",
  "type": "urban_flooding",
  "location": {
    "primary": "G-10, Islamabad",
    "affected_radius_km": 2.5,
    "lat": 33.6844,
    "lng": 73.0479
  },
  "severity": 4,
  "confidence": "high",
  "confidence_score": 0.89,
  "reasoning": "3 corroborating signals detected: social media report (G-10 flooding), heavy rainfall alert from Open-Meteo, traffic congestion spike on Srinagar Highway. Signals cluster within 2.5km radius over 28 minutes.",
  "contributing_signals": ["sig_001", "sig_002", "sig_003"],
  "status": "confirmed",
  "detected_at": "2026-05-13T14:35:00Z"
}
```

**Triggers Agent 3** when: `status == "confirmed"`

---

### Agent 3 — Situational Awareness Agent
**Owner:** Member 2 (prompts) + Member 3 (data APIs)  
**Runs in:** Antigravity Agent Manager

**Inputs:**
- Output from Agent 2 (`CrisisEvent`)
- OSM road network data (Overpass API)
- Simulated hospital/facility locations
- Simulated emergency unit registry

**Processing:**
- Queries affected zone boundary from crisis lat/lng + radius
- Fetches road closure data for affected area
- Identifies nearby facilities: hospitals, fire stations, police, emergency depots
- Builds operational ground truth for affected zone
- Flags data gaps (areas with no confirmed reports)

**Output (JSON artifact):**
```json
{
  "crisis_id": "CRS_20260513_001",
  "operational_picture": {
    "affected_zone": { "center": [33.6844, 73.0479], "radius_km": 2.5 },
    "road_closures": [
      { "road": "Srinagar Highway (G-10 section)", "status": "blocked", "source": "traffic_api" }
    ],
    "nearby_facilities": [
      { "type": "rescue_unit", "name": "F-8 Rescue Station", "distance_km": 3.1, "status": "available" },
      { "type": "hospital", "name": "PIMS Hospital", "distance_km": 4.2, "status": "operational" }
    ],
    "data_gaps": [],
    "population_at_risk": 12000
  },
  "generated_at": "2026-05-13T14:37:00Z"
}
```

**Triggers Agent 4** immediately on completion.

---

### Agent 4 — Resource Gap & Dispatch Agent
**Owner:** Member 3  
**Runs in:** Antigravity Agent Manager

**Inputs:**
- Output from Agent 3 (`OperationalPicture`)
- Simulated resource inventory DB (trucks, rescue units, supplies)
- OCHA standard consumption rates (food, tents, medicine per capita/day)

**Processing:**
- Calculates resource requirements vs. available inventory per zone
- Ranks response priorities by: severity × accessibility score × population at risk
- Determines which units to dispatch where and why
- Generates dispatch orders with full visible reasoning

**Output (JSON artifact):**
```json
{
  "crisis_id": "CRS_20260513_001",
  "dispatch_plan": {
    "priority_ranking": [
      { "zone": "G-10", "priority_score": 87, "reason": "Highest severity, road partially accessible" }
    ],
    "dispatch_orders": [
      {
        "order_id": "DO_001",
        "unit": "F-8 Rescue Unit Alpha",
        "unit_type": "water_rescue",
        "destination": "G-10 Sector, Islamabad",
        "reason": "Water rescue capability required; nearest available unit at 3.1km",
        "eta_minutes": 12
      }
    ],
    "resource_gaps": [
      { "item": "rubber_boats", "required": 3, "available": 2, "gap": 1, "mitigation": "Request from I-8 depot" }
    ]
  },
  "generated_at": "2026-05-13T14:39:00Z"
}
```

**Triggers Agent 5** with dispatch plan.

---

### Agent 5 — Route & Action Simulation Agent
**Owner:** Member 3  
**Runs in:** Antigravity Agent Manager

**Inputs:**
- Dispatch plan from Agent 4
- Road network from Agent 3
- Simulated traffic state

**Processing:**
- Calls OpenRouteService API for optimal routing per convoy/unit
- Simulates units moving along routes (waypoints at 30s intervals)
- Updates mock traffic state (congestion before → after)
- Generates emergency ticket in simulated ticket system
- Generates simulated public alerts (SMS/WhatsApp format)
- Records before/after state for outcome visualization

**Output (JSON artifact):**
```json
{
  "crisis_id": "CRS_20260513_001",
  "simulation": {
    "routes": [
      {
        "unit": "F-8 Rescue Unit Alpha",
        "route": { "via": "Margalla Road", "waypoints": [...], "distance_km": 3.1, "duration_min": 12 },
        "route_reasoning": "Srinagar Highway blocked; Margalla Road clear per OSM + traffic data"
      }
    ],
    "traffic_state": {
      "before": { "Srinagar Highway": "severe_congestion" },
      "after": { "Srinagar Highway": "diverted", "Margalla Road": "moderate" },
      "congestion_reduction_pct": 61
    },
    "emergency_ticket": {
      "ticket_id": "EMT_2841",
      "created_at": "2026-05-13T14:40:00Z",
      "status": "dispatched",
      "units": ["F-8 Rescue Unit Alpha"]
    },
    "public_alerts": [
      {
        "channel": "SMS",
        "target_area": "G-10, G-9, I-10",
        "message": "ALERT: Severe flooding in G-10. Avoid Srinagar Highway. Use Margalla Road. Rescue services en route."
      }
    ]
  }
}
```

**Triggers Agent 6** with complete simulation state.

---

### Agent 6 — Command & Public Dashboard Agent
**Owner:** Team Lead  
**Runs in:** Antigravity Agent Manager

**Inputs:**
- All previous agent outputs (aggregated crisis record)
- Gemini 3.1 Pro for SITREP text generation

**Processing:**
- Synthesizes all agent outputs into unified dashboard state
- Generates SITREP document (standard NDMA format) via Gemini
- Produces two data views: command (full detail) and public (simplified)
- Pushes state to FastAPI backend via REST API
- Logs full agent reasoning chain for judge inspection

**Outputs:**
- SITREP document (markdown/PDF)
- Dashboard state JSON (consumed by web + mobile)
- Agent trace log (submitted as deliverable)

---

## 3. Data Layer

| Data | Real or Simulated | Source | Owner |
|---|---|---|---|
| Weather | **Real** | Open-Meteo free API | Member 2 |
| Social media posts | **Simulated** | Hardcoded JSON — realistic Urdu + English | Member 2 |
| Google Maps traffic | **Real (free tier)** | Google Maps JS API | Member 3 |
| Road network | **Real** | OSM via Overpass API | Member 3 |
| Emergency unit locations | **Simulated** | Mock DB — realistic Islamabad coordinates | Member 3 |
| Resource inventory | **Simulated** | Internal PostgreSQL table | Member 3 |
| Hospital/facility locations | **Simulated** | Hardcoded realistic coordinates | Member 3 |
| Routing | **Real** | OpenRouteService API (free) | Member 3 |
| SITREP generation | **Real** | Gemini 3.1 Pro via Antigravity | Team Lead |

All synthetic data is clearly labeled in the README. This is explicitly permitted by the hackathon rules.

---

## 4. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| IDE & Agent Orchestration | **Google Antigravity** | All 6 agents run here — mandatory |
| Primary LLM | **Gemini 3.1 Pro** | Via Antigravity's built-in rate limits |
| Backend API | **FastAPI (Python)** | REST + WebSocket |
| Database | **PostgreSQL + PostGIS** | Geospatial queries |
| Geospatial routing | **OpenRouteService API** | Free, open-source |
| OSM data | **Overpass API** | Road network queries |
| Web dashboard | **React + Leaflet.js** | Map rendering |
| Mobile app | **React Native** | iOS + Android (mandatory) |
| Hosting | **Google Cloud Run** | Containerized FastAPI |
| Real-time updates | **WebSocket** | Dashboard live updates |
| PDF parsing (optional) | **PyMuPDF** | If NDMA reports ingested |
| Weather | **Open-Meteo** | Free, no key required |

---

## 5. API Contracts (Between Backend and Agents)

### Agent → Backend: POST `/api/crisis/update`
```json
{
  "crisis_id": "string",
  "stage": "detected | analyzed | dispatched | simulated | resolved",
  "payload": { ... }  // Stage-specific agent output
}
```

### Backend → Dashboard: WebSocket `/ws/crisis/{crisis_id}`
Pushes state updates to connected web/mobile clients in real time.

### Backend → Mobile: GET `/api/crisis/active`
Returns list of active crises with public-safe summary for mobile display.

---

## 6. Deployment Architecture

```
Google Cloud Run
    └── FastAPI container
            ├── REST endpoints (agent → backend, backend → clients)
            ├── WebSocket server (real-time dashboard)
            └── PostgreSQL connection (Cloud SQL or local)

Antigravity Agent Manager (local)
    └── 6 agents running in parallel workspaces
            └── Calls backend REST endpoints to push state

Web Dashboard (React)
    └── Connects to WebSocket for live updates
    └── Hosted on Cloud Run or Firebase Hosting

Mobile App (React Native)
    └── Polls /api/crisis/active every 30s
    └── Connects to WebSocket for active crisis detail
```

---

## 7. Key Constraints and Decisions

- **Mobile app is mandatory** — scope it to: crisis alert view, map of affected zone, safe route suggestion, status updates
- **Google Antigravity must be central** — do not bypass agents for any core logic; the routing decision, dispatch reasoning, and SITREP must come through Antigravity agents
- **Agent traces are a submission deliverable** — every agent must log its reasoning steps. Design for this from day 1
- **Simulated data must be labeled** — every mock dataset has a `"source": "simulated"` field and is documented in README
- **One scenario end-to-end** — all build decisions optimize for the G-10 flooding demo scenario working flawlessly
