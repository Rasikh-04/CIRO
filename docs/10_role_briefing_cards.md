# CIRO — Role Briefing Cards
## Quick-Start Guide Per Member

---

# 🟦 ROLE A: Abdul Mannan
### Antigravity Orchestration + Web Dashboard + Mobile App

**Your deliverable:** The system works. Every part connects. The demo video is recorded.

---

**Read first:** `02_system_architecture.md`, `03_agentic_workflow_spec.md`, `06_shared_integration_contract.md`

**Today (May 13):**
1. Share all docs with both members
2. Create GitHub repo with folder structure
3. Download and install Antigravity (antigravity.google/download)
4. Create Google Cloud project → enable Maps JavaScript API, Maps SDK for Android/iOS
5. Create `.env.example` file — list all required keys (no values)

**Your build scope:**
- Antigravity Agent Manager: set up all 6 workspaces, write `.agy_rules` files, test Agent 1 and Agent 2 prompts, run Agent 6 (SITREP + push to backend)
- Web dashboard (React + Leaflet): map, crisis panel, agent trace tab, dispatch tab, SITREP tab, before/after toggle
- Mobile app (React Native + Expo): Home screen, Crisis Detail screen, Safe Routes screen, Alerts screen

**Key files you write:**
- All `.agy_rules` files in each agent workspace
- `web-dashboard/` — full React project
- `mobile-app/` — full React Native project
- Agent 6 workspace code + prompt
- `CIRO_agent_trace.log` — export from Antigravity, combine all 6 agents

**Your integration dependency:**
- You need Ahmar's backend running at localhost:8000 on Day 2
- You need Tabeen's Agent 1 producing signals.json by Day 2
- You own the final integration day (May 18)

**Demo video is your responsibility.** Plan 3–5 min showing: Antigravity Agent Manager with 6 workspaces → pipeline running → dashboard updating → mobile app.

---

# 🟩 ROLE B: Tabeen Bokhat
### Agent 1 (Signal Ingestion) + Agent 2 (Crisis Detection) + Gemini Prompt Engineering

**Your deliverable:** Reliable signal ingestion and crisis classification, with clean trace logs.

---

**Read first:** `02_system_architecture.md` (Agents 1–3), `03_agentic_workflow_spec.md` (Agent 1 + 2 prompts), `06_shared_integration_contract.md` (Schemas A and B)

**Today (May 13):**
1. Read all documentation
2. Install Python 3.11 + Antigravity
3. Write `data/mock_social_media.json` — 10 posts (7 real signals, 2 noisy/ambiguous, 1 unrelated) about G-10 flooding in Urdu/English

**Your build scope:**
- `agents/agent_1_signal_ingestion/ingest.py` — load JSON, call Open-Meteo API, normalize text via Gemini, output `signals.json` (Schema A)
- `agents/agent_2_crisis_detection/classify.py` — cluster signals by location + type, run Gemini confidence reasoning, output `crisis.json` (Schema B)
- `agents/agent_3_situational_awareness/osm_query.py` — Overpass API query, `haversine.py` — distance calculator
- All Gemini prompts for: text normalization (Agent 1), confidence reasoning (Agent 2)
- Agent 3 prompt + workspace (Antigravity)

**Key schemas you produce:**
- `SignalEvent[]` → POST to `/api/signals/ingest`
- `CrisisEvent` → POST to `/api/crisis/detected`
- `OperationalPicture` → POST to `/api/crisis/operational`

**Critical: Integration Checkpoint Day 2 (May 15, morning)**
Your Agent 1 must be able to POST to Ahmar's backend and get a 200 response. Do not skip this.

**Robustness you must document:**
- What happens when Agent 2 receives only 1 signal (no crisis confirmation)
- What happens with a sarcastic/noisy post (post #9 in your mock data)
- These are your "edge cases" for the submission

**Tip:** Test your Gemini prompts in a plain chat window first. Once they produce clean JSON, paste them into Antigravity agent prompts.

---

# 🟥 ROLE C: Ahmar
### FastAPI Backend + Database + Agent 4 (Dispatch) + Agent 5 (Simulation) + Cloud Run

**Your deliverable:** The backend is the backbone. If the backend is down, nothing works. Treat it as the most critical component.

---

**Read first:** `04_backend_design.md` (entire document), `06_shared_integration_contract.md` (all schemas, especially D and E), `07_integration_guide.md` (External APIs, Deployment)

**Today (May 13):**
1. Read all documentation
2. Install Docker, Python 3.11
3. Start PostgreSQL + PostGIS: `docker run -d --name ciro-db -e POSTGRES_PASSWORD=ciro_pass -e POSTGRES_DB=ciro -p 5432:5432 postgis/postgis:15-3.3`
4. Sign up for OpenRouteService API key: https://openrouteservice.org/dev/#/signup
5. Write `data/facilities_db.json` and `data/inventory.json` (use coordinates from Section 2 of `06_shared_integration_contract.md` exactly)

**Your build scope:**
- `backend/` — complete FastAPI project: all models, schemas, endpoints, WebSocket manager
- `agents/agent_4_resource_dispatch/dispatch.py` — gap calculation, priority ranking, dispatch logic
- `agents/agent_5_simulation/route_engine.py` — OpenRouteService integration + fallback
- `scripts/generate_ticket.py` — emergency ticket generator
- `Dockerfile` + Cloud Run deployment
- Database seeding script

**Key schemas you consume and produce:**
- Consume: `OperationalPicture` (Schema C) → Produce: `DispatchPlan` (Schema D)
- Consume: `DispatchPlan` (Schema D) → Produce: `SimulationResult` (Schema E)

**Critical: Integration Checkpoint Day 2 (May 15, morning)**
Your backend must be accepting POST `/api/signals/ingest` from Tabeen's Agent 1. This is your primary goal for Day 1.

**Robustness you must build:**
- OpenRouteService failure fallback (haversine straight-line estimate)
- If a dispatch POST comes in before `crisis/detected` is set, return 400 with clear error
- If `quantity` in inventory drops to 0, mark unit unavailable

**README sections you write:**
- Cost estimate per demo run
- Scalability discussion (10x / 100x)
- Backend architecture section
- API list with descriptions

**Day 6 (May 18) is your most important day** — you own the Cloud Run deployment. Start the Dockerfile on Day 3 so it's not last-minute.
