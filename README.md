# CIRO — Crisis Intelligence & Response Orchestrator

> AISeekho 2026 Hackathon — Challenge 3

## What It Does

CIRO is a two-layer agentic system for real-time urban crisis detection and coordinated emergency response. It ingests multi-source signals (social media, weather, traffic), confirms crises through corroboration, and orchestrates field response — dispatching units, optimizing routes, generating SITREPs, and alerting the public — with every decision visibly reasoned through a 6-agent pipeline running in Google Antigravity.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CIRO SYSTEM                              │
│  ┌─────────────┐    ┌──────────────────────────────────────┐   │
│  │  LAYER 1    │    │              LAYER 2                  │   │
│  │  Crisis     │───▶│       Response Orchestration          │   │
│  │Intelligence │    └──────────────────────────────────────┘   │
│  └─────────────┘                    │                           │
│                                     ▼                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ANTIGRAVITY AGENT MANAGER (6 Agents)       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  FastAPI Backend ← → PostgreSQL/PostGIS ← → Google Cloud Run   │
│  Web Dashboard (React + Leaflet)  Mobile App (React Native)    │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Pipeline

| Agent | Role | Output |
|---|---|---|
| Agent 1 | Signal Ingestion | Normalized `SignalEvent[]` from social/weather/traffic |
| Agent 2 | Crisis Detection | `CrisisEvent` with confidence score + reasoning |
| Agent 3 | Situational Awareness | `OperationalPicture` — roads, facilities, population |
| Agent 4 | Resource Gap & Dispatch | `DispatchPlan` with priority ranking + reasoning |
| Agent 5 | Route & Action Simulation | `SimulationResult` — routes, traffic before/after, ticket, alerts |
| Agent 6 | Command & Dashboard | `DashboardState` + SITREP via Gemini |

## Google Antigravity Usage

All 6 agents run as separate workspaces in Antigravity's Agent Manager. Antigravity's browser tool enables agents to call external APIs (Open-Meteo, Overpass, OpenRouteService). Gemini 3.1 Pro handles: Urdu/English normalization (Agent 1), confidence reasoning (Agent 2), and SITREP generation (Agent 6). All AI workloads run through Antigravity's built-in Gemini access.

## Tools & APIs Used

| Tool | Purpose | Real/Simulated |
|---|---|---|
| Open-Meteo | Weather data | Real |
| Overpass API | OSM road network | Real |
| OpenRouteService | Route optimization | Real |
| Google Maps SDK | Mobile map display | Real |
| Gemini 3.1 Pro | Text tasks via Antigravity | Real |
| Social media posts | Signal inputs | **Simulated** |
| Emergency inventory | Resource data | **Simulated** |
| Traffic state | Simulation output | **Simulated** |
| Facility locations | Hospitals, stations | **Simulated** |

## Demo Scenario

**Urban flooding in G-10, Islamabad** — 3 corroborating signals detected → crisis confirmed (confidence 0.89) → F-8 Rescue Unit Alpha dispatched via Margalla Road → 61% congestion reduction simulated → public alerts sent → SITREP generated.

## Setup

See [docs/07_integration_guide.md](docs/07_integration_guide.md) for full setup instructions.

**Quick start:**
```bash
# 1. Copy env file
cp .env.example .env
# Edit .env with your API keys

# 2. Start database
docker run -d --name ciro-db -e POSTGRES_PASSWORD=ciro_pass -e POSTGRES_DB=ciro \
  -p 5432:5432 postgis/postgis:15-3.3

# 3. Start backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# 4. Start web dashboard
cd web-dashboard && npm install && npm start

# 5. Mobile app
cd mobile-app && npm install && npx expo start
```

## Assumptions

- Crisis scenario is limited to G-10, Islamabad for the prototype
- Emergency resource inventory reflects a plausible but simulated dataset
- Population at risk estimates are district-level approximations
- Routing avoidance polygons are approximated from traffic reports, not real-time sensors

## Privacy Note

No real personal data is used. All social media posts are synthetically generated. No real user location data is collected or stored.

## Cost Estimate

- Open-Meteo: Free ($0)
- Overpass API: Free ($0)
- OpenRouteService: Free tier, ~6 calls per demo run (~$0)
- Google Maps: Free tier covers 1,000+ demo runs
- Gemini via Antigravity: Covered by Antigravity's free preview quota
- Google Cloud Run: ~$0.002 per demo run
- **Total cost per demo run: ~$0.002**

## Scalability

- Cloud Run auto-scales to handle 10x concurrent crises
- Agent pipeline is stateless — each crisis runs independently
- At 100x scale: database needs connection pooling (PgBouncer); agents need a queue (Cloud Tasks)
- Latency: ~50s end-to-end pipeline for a single crisis event

## Baseline Comparison

| Metric | Without CIRO | With CIRO |
|---|---|---|
| Time to crisis detection | 20–45 min (manual) | <2 min (automated) |
| Dispatch decision | Committee process | <5 min (agent-ranked) |
| Coordination | Phone calls, fragmented | Unified dashboard, auto-SITREP |
| Public alerts | Delayed, manually drafted | Automated within pipeline |

## Limitations

- Simulated inventory does not reflect real NDMA resource data
- Agent pipeline requires manual trigger (automation possible with Cloud Scheduler)
- Mobile app uses polling; production would use native push notifications
- SITREP format approximates NDMA structure; not formally validated

## Team

- **Abdul Mannan** — Antigravity orchestration, web dashboard, mobile app
- **Tabeen Bokhat** — Signal ingestion, crisis detection, Gemini prompts
- **Abdul Hannan Ahmar** — Backend, database, routing simulation, Cloud Run
