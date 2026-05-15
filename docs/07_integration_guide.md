# CIRO — Integration Guide
## How Everything Connects: Agents, Backend, APIs, and Apps

---

## 1. Integration Architecture at a Glance

```
ANTIGRAVITY (local)              BACKEND (Cloud Run / localhost)
    │                                        │
    │  Agent 1  ──POST /signals/ingest──▶   │
    │  Agent 2  ──POST /crisis/detected──▶  │
    │  Agent 3  ──POST /crisis/operational─▶│──WebSocket──▶  Web Dashboard
    │  Agent 4  ──POST /crisis/dispatch───▶ │                Mobile App
    │  Agent 5  ──POST /crisis/simulation──▶│
    │  Agent 6  ──POST /crisis/complete───▶ │
    │            ◀──GET /api/*──────────────│
    │                                        │
EXTERNAL APIs (called by agents via browser tool)
    ├── Open-Meteo (weather)
    ├── Overpass API (OSM roads)
    └── OpenRouteService (routing)
```

---

## 2. External APIs — Setup & Access

### API 1: Open-Meteo (Weather)
- **Free, no API key required**
- URL: `https://api.open-meteo.com/v1/forecast`
- Parameters for Islamabad:
```
https://api.open-meteo.com/v1/forecast?latitude=33.6844&longitude=73.0479&current=precipitation,weathercode,windspeed_10m&timezone=Asia/Karachi
```
- Response field to check: `current.precipitation` (>5mm/hr = heavy rain), `current.weathercode` (95 = thunderstorm)
- **Who calls this:** Agent 1 (via Antigravity browser tool)
- **No signup needed**

### API 2: Overpass API (OSM Road Network)
- **Free, no API key required**
- URL: `https://overpass-api.de/api/interpreter`
- Query for roads in G-10 bounding box:
```
https://overpass-api.de/api/interpreter?data=[out:json][bbox:33.6744,73.0379,33.6944,73.0579][highway];out;
```
- Returns road segments as GeoJSON-compatible features
- **Who calls this:** Agent 3 (via Antigravity browser tool)
- If Overpass is slow: use the cached OSM data in `data/islamabad_roads.geojson` (Member 3 generates this once)

### API 3: OpenRouteService (Routing)
- **Free tier: 2,000 requests/day**
- Sign up: https://openrouteservice.org/dev/#/signup
- **Member 3 creates this account and adds key to `.env`**
- Endpoint:
```
POST https://api.openrouteservice.org/v2/directions/driving-car
Headers: Authorization: YOUR_KEY
Body: {
  "coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]],
  "avoid_polygons": { ... }  // optional blocked area
}
```
- Returns: route geometry, waypoints, distance, duration
- **Who calls this:** Agent 5 (via terminal: `python route_engine.py`)

### API 4: Google Maps (Traffic + Mobile Map)
- **Free tier covers hackathon usage**
- **Team Lead creates Google Cloud project and enables APIs:**
  - Maps JavaScript API (web dashboard, optional)
  - Maps SDK for Android/iOS (mobile)
  - Directions API (optional, fallback for routing)
- Add key to `.env` as `GOOGLE_MAPS_API_KEY`
- For Agent 1 traffic simulation: use `data/mock_traffic.json` unless real API is available

### API 5: Gemini 3.1 Pro (via Antigravity)
- **No separate setup needed** — Antigravity provides this natively
- Used in: Agent 1 (text normalization), Agent 2 (confidence reasoning), Agent 6 (SITREP generation)
- Rate limits are generous in Antigravity's free preview
- If rate limited: cache Gemini outputs and re-use for demo

---

## 3. Development Environment Setup

### Step 1: Clone Repository (all members)
```bash
git clone https://github.com/YOUR_ORG/ciro.git
cd ciro
```

### Step 2: Backend Setup (Member 3, then share .env)
```bash
cd backend

# Start PostgreSQL with PostGIS
docker run -d \
  --name ciro-db \
  -e POSTGRES_PASSWORD=ciro_pass \
  -e POSTGRES_DB=ciro \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Install Python dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env: add DATABASE_URL, API keys

# Seed the database
python scripts/seed_db.py

# Start backend
uvicorn main:app --reload --port 8000
# Verify: http://localhost:8000/docs (FastAPI auto-docs)
```

### Step 3: Antigravity Setup (Team Lead)
1. Download Antigravity from https://antigravity.google/download
2. Sign in with personal Gmail
3. In Agent Manager: Add Workspace → select `ciro/agents/agent_1_signal_ingestion/`
4. Repeat for all 6 agent workspaces
5. Set Review Policy: "Agent Decides" for initial testing

### Step 4: Web Dashboard Setup (Team Lead)
```bash
cd web-dashboard
npm install
# Create .env.local
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env.local
npm start
```

### Step 5: Mobile App Setup (Team Lead)
```bash
cd mobile-app
npm install
npx expo start
# Scan QR code with Expo Go app (iOS or Android)
```

---

## 4. Running the Full System Locally

**Order matters. Start in this sequence:**

```
Terminal 1: PostgreSQL (Docker)          → already running from setup
Terminal 2: cd backend && uvicorn ...    → backend at localhost:8000
Terminal 3: cd web-dashboard && npm start → dashboard at localhost:3000
Terminal 4: cd mobile-app && npx expo   → mobile at Expo tunnel
Antigravity: Agent Manager open          → agents ready to run
```

**Triggering the demo pipeline:**
1. In Antigravity Agent Manager, open Agent 1's workspace
2. Start new conversation: paste Agent 1 prompt (from `03_agentic_workflow_spec.md`)
3. Watch agent run → signals appear in backend DB
4. Agent 1 auto-POSTs to backend → triggers manual Agent 2 run (or automate)
5. Continue chain: Agent 3 → 4 → 5 → 6
6. Watch dashboard update in real time via WebSocket

---

## 5. Agent-to-Agent Handoff (Detailed)

Each agent is a separate Antigravity session. The handoff mechanism is:

**Method A: Backend-mediated (recommended)**
- Agent N finishes → POSTs output to backend endpoint
- Backend stores it + broadcasts WebSocket event
- Agent N+1 started manually (during dev) or by a coordinator script

**Method B: File-based (simpler for demo)**
- Agent N writes `output/result.json`
- Agent N+1 workspace reads that file directly (if on same machine)
- Less clean but works for demo

**Use Method A for the final demo** — it shows proper system integration and real API calls, which judges see in the trace.

### Coordinator Script (Optional, for automated demo)
```python
# scripts/run_demo.py
# Runs agents sequentially via Antigravity CLI (if available)
# OR triggers them by calling backend endpoints that Antigravity
# agents poll on startup

import httpx, time

backend = "http://localhost:8000"

# Inject demo trigger
httpx.post(f"{backend}/api/demo/trigger", json={"scenario": "g10_flood"})

print("Demo scenario triggered. Watch Antigravity Agent Manager.")
print("Agents will run sequentially as each stage completes.")
```

---

## 6. Testing Integration

### Unit Test: Backend endpoints (Member 3)
```bash
cd backend
pytest tests/test_api.py -v
```

### Integration Test: Full pipeline dry run
```bash
# 1. Seed fresh data
python scripts/seed_db.py --reset

# 2. Run mock pipeline
python scripts/mock_pipeline.py
# This script POSTs each schema to backend in sequence
# without Antigravity — tests that backend handles all stages correctly

# 3. Verify dashboard state
curl http://localhost:8000/api/crisis/active
```

---

## 7. Deployment Checklist (Day 6)

### Backend → Cloud Run
- [ ] `Dockerfile` builds cleanly: `docker build -t ciro-backend .`
- [ ] `.env` variables set in Cloud Run environment
- [ ] Cloud SQL PostgreSQL with PostGIS extension created
- [ ] `DATABASE_URL` points to Cloud SQL
- [ ] `gcloud run deploy` succeeds
- [ ] Public URL returns 200 on `/api/crisis/active`

### Web Dashboard
- [ ] `REACT_APP_BACKEND_URL` set to Cloud Run URL
- [ ] `npm run build` produces clean build
- [ ] Deploy to Firebase Hosting or Cloud Run static
- [ ] WebSocket connection works to Cloud Run backend

### Mobile App
- [ ] Backend URL hardcoded to Cloud Run URL for demo build
- [ ] `npx expo build:android` or use Expo Go for demo
- [ ] Demo runs on physical device (record this for the video)

### Antigravity
- [ ] All 6 agent workspaces open in Agent Manager
- [ ] All agent prompts tested end-to-end
- [ ] Trace logs saved as files
- [ ] Full pipeline runs once without errors before recording

---

## 8. Submission Checklist

Per the hackathon requirements:

| Item | Who Prepares | Status |
|---|---|---|
| Working mobile app (mandatory) | Team Lead | |
| Working web dashboard (optional but we're doing it) | Team Lead | |
| Demo video 3–5 min | Team Lead (records) | |
| Antigravity trace/logs | Team Lead (exports from agents) | |
| README with architecture, APIs, assumptions | All | |
| Baseline comparison (agentic vs non-agentic) | Member 2 | |
| Robustness evidence (failure/edge case) | Member 3 | |
| Cost/scalability note | Member 3 | |

### README Must Include
- System architecture diagram
- Antigravity usage explanation
- Tools/APIs used (with real vs. simulated labels)
- Assumptions list
- Privacy note (no real personal data)
- Cost estimate (API calls per demo run)
- Scalability: how it handles 10x / 100x crisis volume
- Limitations (honest, judges appreciate this)

### Baseline Comparison
Write a short section showing: "Without agents, this system would be a static form that emails an operator. With agents: [measurable difference in response time, coverage, coordination]."
