# CIRO — Development Plan
## Role-Based Tasks: May 13–20, 2026

---

## Overview

| Phase | Days | Goal |
|---|---|---|
| Phase 0: Setup & Docs | May 13 | All members have docs, dev environments, shared repo |
| Phase 1: Build | May 14–17 | Each member builds their component |
| Phase 2: Integration | May 18 | Everything connects, pipeline runs end-to-end |
| Phase 3: Polish & Submit | May 19–20 | Demo video, README, submission |

**Integration checkpoint: May 15 (Day 2–3)** — quick smoke test, all three connect to backend.

---

## Phase 0 — Today (May 13)

**Abdul Mannan**
- [ ] Share all documentation files with Member 2 and Member 3
- [ ] Set up GitHub repository with folder structure from `06_shared_integration_contract.md`
- [ ] Create `.env.example` with all required keys listed (no actual keys)
- [ ] Brief both members on their roles verbally or in writing
- [ ] Download and install Antigravity
- [ ] Create Google Cloud project, enable Maps API, add key to `.env`

**Tabeen Bokhat:**
- [ ] Read all documentation files (priority: `02_system_architecture.md`, `03_agentic_workflow_spec.md`, `06_shared_integration_contract.md`)
- [ ] Install Python 3.11, set up development environment
- [ ] Download and install Antigravity (will need it for Agent 1 + 2)
- [ ] Write `data/mock_social_media.json` — 10 posts in Urdu/English covering the G-10 flood scenario

**Abdul Hannan Ahmar:**
- [ ] Read all documentation files (priority: `04_backend_design.md`, `06_shared_integration_contract.md`, `07_integration_guide.md`)
- [ ] Install Docker, Python 3.11
- [ ] Start PostgreSQL + PostGIS Docker container
- [ ] Sign up for OpenRouteService API key
- [ ] Write `data/facilities_db.json` and `data/inventory.json` using coordinates from Section 2 of integration contract

---

## Role A: Abdul Mannan
### Antigravity Orchestration + Web Dashboard + Mobile App

---

### May 14 — Antigravity Setup Day

**Morning:**
- [ ] Open all 6 agent workspaces in Antigravity Agent Manager
- [ ] Create `.agy_rules` file for each agent workspace (copy templates from `03_agentic_workflow_spec.md`)
- [ ] Test Agent 1 prompt manually: paste prompt into Agent Manager, verify it reads `mock_social_media.json` and calls Open-Meteo
- [ ] Verify Antigravity's browser tool can hit `https://api.open-meteo.com` (test with a simple GET prompt)

**Afternoon:**
- [ ] Set up web dashboard React project skeleton
  ```bash
  npx create-react-app web-dashboard
  cd web-dashboard
  npm install leaflet react-leaflet react-query
  ```
- [ ] Create basic layout: left panel + map + bottom tabs (can be empty/placeholder)
- [ ] Connect to backend WebSocket at `/ws/command` — even if backend isn't ready, write the connection code

---

### May 15 — Agent 1 & 2 Working + Dashboard Map

**Morning:**
- [ ] Agent 1 runs fully: reads mock data, calls weather API, produces valid `signals.json`
- [ ] Agent 1 POSTs to `localhost:8000/api/signals/ingest` successfully (coordinate with Ahmar)
- [ ] **Integration Checkpoint**: confirm Ahmar's backend accepts the POST and returns 200

**Afternoon:**
- [ ] Agent 2 working: reads signals, produces `crisis.json`, POSTs to backend
- [ ] Web dashboard: Leaflet map renders Islamabad, hardcode one crisis zone polygon to verify map layer works
- [ ] Web dashboard: Crisis panel (left sidebar) shows hardcoded crisis card

---

### May 16 — Agent 6 + Dashboard Live Updates

**Morning:**
- [ ] Agent 6 prompt working: calls `/api/crisis/full/{id}`, generates SITREP via Gemini, POSTs complete state
- [ ] Agent trace log format finalized — decide on exact log structure (share with all members)
- [ ] Dashboard: WebSocket connection live — crisis card updates when Agent 2 POSTs

**Afternoon:**
- [ ] Mobile app React Native project setup:
  ```bash
  npx create-expo-app mobile-app
  cd mobile-app
  npm install react-native-maps @react-navigation/native
  ```
- [ ] Screens 2 and 3 (Home + Crisis Detail) wired to backend REST API
- [ ] Crisis zone displays on mobile map using demo coordinates

---

### May 17 — Mobile App Polish + Full Dashboard

**Morning:**
- [ ] Dashboard: Agent trace tab live (shows log lines from backend)
- [ ] Dashboard: Before/After traffic toggle working with hardcoded simulation data
- [ ] Dashboard: SITREP tab rendering markdown

**Afternoon:**
- [ ] Mobile: Safe Routes screen showing alternate route (hardcoded route from simulation data)
- [ ] Mobile: Alerts screen with simulated alerts
- [ ] Mobile: Polish — loading states, error handling, correct colors

---

### May 18 — Integration Day

- [ ] Full pipeline test: trigger Agent 1 → watch all agents run → verify dashboard + mobile both update
- [ ] Fix all integration bugs
- [ ] Record one complete pipeline run as backup (in case demo has issues on recording day)

---

### May 19 — Demo Video

- [ ] Record 3–5 min demo video:
  1. Open Antigravity Agent Manager — show 6 workspaces
  2. Trigger Agent 1 — show it calling Open-Meteo, normalizing posts
  3. Agent 2 — show confidence reasoning in trace
  4. Show dashboard updating in real time as each agent completes
  5. Show map: crisis zone → route animation → before/after traffic
  6. Show mobile: crisis alert → safe route
  7. Show SITREP tab (Gemini output)
- [ ] Record 2–3 min Antigravity usage video (required separately)
- [ ] Export all agent trace logs as `CIRO_agent_trace.log`

---

## Role B: Tabeen Bokhat
### Agent 1 (Signal Ingestion) + Agent 2 (Crisis Detection) + Gemini Prompt Engineering

---

### May 14 — Mock Data + Agent 1 Scaffold

**Morning:**
- [ ] Write `data/mock_social_media.json` — 10 realistic posts
  - 4 in Urdu about G-10 flooding
  - 3 in English about road blockage on Srinagar Highway
  - 2 ambiguous/noisy posts (for robustness evidence)
  - 1 unrelated post (false positive test)
- [ ] Write `agents/agent_1_signal_ingestion/ingest.py`:
  - Load `mock_social_media.json`
  - Define `SignalEvent` schema (copy from `06_shared_integration_contract.md`)
  - Write output to `output/signals.json`

**Afternoon:**
- [ ] Test Agent 1 prompt in Antigravity Agent Manager
- [ ] Verify Antigravity's browser tool can call Open-Meteo API
- [ ] Write `agent1_trace.log` format — each step logged with timestamp
- [ ] Gemini prompt for text normalization:
  ```
  Normalize this social media post into English. Extract:
  1. Location (district/area name)
  2. Crisis type (flood/accident/heatwave/road_blockage)
  3. Key details (vehicles stranded, roads blocked, etc.)
  
  Return JSON: {"normalized": "...", "location": "...", "crisis_type": "...", "details": "..."}
  
  Post: "{raw_text}"
  ```

---

### May 15 — Agent 1 Complete + Agent 2 Start

**Morning:**
- [ ] Agent 1 fully working: reads mock data + weather API → produces valid `signals.json`
- [ ] Agent 1 POSTs to backend (coordinate with Ahmar for backend to be ready)
- [ ] **Integration Checkpoint (10am):** verify POST to backend succeeds

**Afternoon:**
- [ ] Write `agents/agent_2_crisis_detection/classify.py`:
  - Load `signals.json`
  - Group signals by (lat/lng within 5km) + (same type) + (within 30 min)
  - Output clusters
- [ ] Write clustering logic (Python, no ML needed — simple distance + type matching):
  ```python
  from math import radians, cos, sin, asin, sqrt
  
  def haversine(lat1, lng1, lat2, lng2):
      R = 6371
      dlat = radians(lat2 - lat1)
      dlng = radians(lng2 - lng1)
      a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
      return 2 * R * asin(sqrt(a))
  ```

---

### May 16 — Agent 2 Complete + Gemini Integration

**Morning:**
- [ ] Agent 2 confidence reasoning prompt (Gemini):
  ```
  You are analyzing signals from multiple sources about a potential urban crisis.
  
  Signals:
  {signals_summary}
  
  Based on these signals, determine:
  1. Is this a confirmed crisis? (yes/no)
  2. Confidence score (0.0-1.0)
  3. 2-3 sentence explanation of your reasoning
  4. Crisis type: flood | heatwave | accident | road_blockage | infrastructure_failure
  5. Severity (1-5): 1=minor, 5=catastrophic
  
  Return JSON only.
  ```
- [ ] Agent 2 produces valid `crisis.json` following Schema B
- [ ] Agent 2 POSTs to `/api/crisis/detected`

**Afternoon:**
- [ ] Write Agent 3 Python helpers (situational awareness data scripts):
  - `agents/agent_3_situational_awareness/osm_query.py` — calls Overpass API, extracts roads in bbox
  - `agents/agent_3_situational_awareness/haversine.py` — distance calculations
- [ ] Write Overpass API query for G-10 bounding box (test it at https://overpass-turbo.eu)
- [ ] Agent 3 prompt tested end-to-end in Antigravity

---

### May 17 — Agent 3 Done + Robustness Evidence

**Morning:**
- [ ] Agent 3 complete: queries Overpass, reads `facilities_db.json`, produces `ops_pic.json`
- [ ] Verify Schema C output matches contract exactly

**Afternoon:**
- [ ] **Robustness evidence**: test Agent 2 with edge cases:
  - Only 1 signal (should not confirm crisis — good false negative test)
  - Conflicting signals (social says flood, weather says clear)
  - Signal with missing location field
  - Document how Agent 2 handles each case
- [ ] Write `docs/baseline_comparison.md`:
  - Without agents: operator reads reports manually, makes decisions in 45+ min
  - With CIRO: signals ingested in <60s, crisis confirmed in <2min, dispatch in <5min
  - Quantify the difference clearly

---

### May 18 — Integration Support

- [ ] Be available for integration day — fix any schema mismatches in Agent 1/2/3 outputs
- [ ] Ensure all agent trace logs are clean and readable
- [ ] Test Agent 1 + 2 + 3 chain multiple times until stable

---

## Role C: Abdul Hannan Ahmar
### FastAPI Backend + Database + Agent 4 (Dispatch) + Agent 5 (Simulation) + Cloud Run

---

### May 14 — Backend Foundation

**Morning:**
- [ ] Create FastAPI project structure (see `04_backend_design.md` Section 2)
- [ ] Create all SQLAlchemy ORM models (all 5 tables from Section 3)
- [ ] Create Pydantic schemas matching the canonical schemas in `06_shared_integration_contract.md`
- [ ] Initialize database and run `scripts/seed_db.py`

**Afternoon:**
- [ ] Implement POST `/api/signals/ingest`
- [ ] Implement GET `/api/signals/latest`
- [ ] Implement POST `/api/crisis/detected`
- [ ] Implement GET `/api/crisis/latest`
- [ ] Test all 4 endpoints with curl or Postman
- [ ] Implement basic WebSocket `/ws/command` (just echo back for now)

---

### May 15 — Remaining Endpoints + Seed Data

**Morning:**
- [ ] Implement remaining endpoints:
  - POST `/api/crisis/operational`
  - POST `/api/crisis/dispatch`
  - POST `/api/crisis/simulation`
  - POST `/api/crisis/complete`
  - GET `/api/crisis/active`
  - GET `/api/crisis/{id}`
  - GET `/api/crisis/full/{id}`
  - GET `/api/resources/available`
  - PATCH `/api/resources/{id}/status`
- [ ] **Integration Checkpoint (10am):** POST `/api/signals/ingest` from Tabeen's Agent 1

**Afternoon:**
- [ ] Write `data/facilities_db.json` — use exact coordinates from Section 2 of integration contract
- [ ] Write `data/inventory.json` — F-8 Rescue Unit, 2 ambulances, supply depots
- [ ] Write `data/population_density.json` — district-level estimates for Islamabad (find from Wikipedia or NDMA reports)
- [ ] WebSocket: implement `ConnectionManager` and integrate into crisis update flow
  - When any stage POST arrives → `broadcast()` to all connected clients

---

### May 16 — Agent 4 (Dispatch Logic)

**Morning:**
- [ ] Write `agents/agent_4_resource_dispatch/dispatch.py`:
  - Load `ops_pic.json` + `inventory.json`
  - OCHA consumption rate calculation
  - Gap calculation per resource type
  - Priority ranking formula: `severity × (1/distance_km) × log(population_at_risk)`
  - Unit assignment: for each required type, pick nearest available
- [ ] Test dispatch script independently with mock data
- [ ] Write Agent 4 prompt for Antigravity (uses browser tool to GET /api/crisis/operational + /api/resources/available, runs Python script via terminal)

**Afternoon:**
- [ ] Write dispatch reasoning strings — each dispatch order needs a 2-3 sentence `reason` field explaining the decision
- [ ] Agent 4 produces valid `dispatch.json` following Schema D
- [ ] Agent 4 POSTs to `/api/crisis/dispatch` successfully

---

### May 17 — Agent 5 (Routing + Simulation)

**Morning:**
- [ ] Write `agents/agent_5_simulation/route_engine.py`:
  - Calls OpenRouteService API with unit origin + crisis destination
  - Avoid parameter: blocked road coordinates from `ops_pic.json`
  - Returns: waypoints list, distance_km, duration_min
  - Handles API failure gracefully (falls back to straight-line estimate)
- [ ] Write `scripts/generate_ticket.py`:
  - Generates emergency ticket JSON with auto-incremented ID
  - Saves to `output/tickets/EMT_{id}.json`
- [ ] Write traffic state simulation:
  - Before: `{"Srinagar Highway": "severe_congestion"}`
  - After: `{"Srinagar Highway": "diverted", "Margalla Road": "moderate"}`
  - Calculate `congestion_reduction_pct` = (before_score - after_score) / before_score × 100

**Afternoon:**
- [ ] Agent 5 fully working: routing + simulation + ticket + alerts
- [ ] Test against demo scenario end-to-end
- [ ] Begin Cloud Run deployment:
  - Write `Dockerfile`
  - `docker build -t ciro-backend .` — verify it builds
  - Set up Cloud SQL PostgreSQL (or keep local for demo)

---

### May 18 — Integration + Deployment

**Morning:**
- [ ] Full pipeline test with all agents: Agent 1 → … → Agent 6
- [ ] Fix any backend bugs that surface
- [ ] Final Cloud Run deployment:
  ```bash
  gcloud builds submit --tag gcr.io/PROJECT_ID/ciro-backend
  gcloud run deploy ciro-backend --image gcr.io/PROJECT_ID/ciro-backend \
    --platform managed --region asia-south1 --allow-unauthenticated
  ```
- [ ] Verify public Cloud Run URL works

**Afternoon:**
- [ ] Cost/scalability note (for README):
  - Cost per demo run: ~$0.002 (OpenRouteService + Open-Meteo free, Gemini via Antigravity free)
  - 10x scaling: Cloud Run auto-scales, PostgreSQL needs connection pooling
  - Latency: ~8-12s per agent, ~50s end-to-end pipeline
- [ ] Robustness evidence: test one failure scenario:
  - OpenRouteService returns error → Agent 5 falls back to straight-line route and notes it in log
  - Document this in README

---

### May 19

- [ ] Support demo recording (be available for backend issues)
- [ ] Write README sections: backend architecture, API list, deployment steps, cost note
- [ ] Final database state check: demo scenario data loaded and clean

---

## May 20 — Submission Day

**All members:**
- [ ] Final review of README
- [ ] Upload demo video
- [ ] Export agent trace logs from Antigravity
- [ ] Submit via hackathon form before deadline

**What goes in the submission:**
1. GitHub repo link (all code)
2. Demo video link (3–5 min)
3. Antigravity usage video (2–3 min)
4. Agent trace log file (`CIRO_agent_trace.log`)
5. README.md

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Antigravity rate limit during demo | Medium | Pre-cache Gemini outputs; have a recording of a successful run |
| OpenRouteService API limit | Low | 2,000 free calls/day is more than enough |
| Schema mismatch at integration | High | Run Checkpoint 1 on Day 2; don't skip it |
| Cloud Run deployment issues | Medium | Keep local backend as fallback for demo |
| Mobile app not building in time | Medium | Use Expo Go on physical device instead of a standalone build |
| Agent 5 routing API slow | Low | Pre-compute route and cache result; replay for demo |
| Member becomes unavailable | Low | Architecture is documented; any member can pick up another's task from the docs |
