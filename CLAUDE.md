# CIRO — Claude Code Rules
## Anti-Hallucination & Development Guidelines

---

## Who You Are Working With

**Abdul Mannan** — Team Lead. His scope:
- Google Antigravity Agent Manager (6 workspaces, all `.agy_rules` files, Agent 6 prompt + code)
- Web Dashboard (`web-dashboard/` — React 18 + Leaflet.js + Tailwind)
- Mobile App (`mobile-app/` — React Native 0.74 + Expo)

Claude Code does all the coding. Abdul Mannan handles manual tasks (Antigravity UI, Google Cloud Console, demo recording).

---

## Immutable Constraints — Never Deviate

### 1. The Demo Scenario Is Frozen
```
Crisis:   Urban Flooding, G-10, Islamabad
Lat/Lng:  33.6844, 73.0479
Severity: 4/5  |  Confidence: High (0.89)
Trigger:  3 social posts + heavy rainfall + traffic spike
Dispatch: F-8 Rescue Unit Alpha → G-10 via Margalla Road
Outcome:  61% congestion reduction
Ticket:   EMT_2841
```
Do not add multi-scenario support. Build for this one scenario, flawlessly.

### 2. Fixed Coordinates — Use These Exactly
| Entity | Lat | Lng |
|---|---|---|
| Crisis center (G-10) | 33.6844 | 73.0479 |
| F-8 Rescue Station | 33.7080 | 73.0479 |
| PIMS Hospital | 33.7161 | 73.0738 |
| Srinagar Highway blockage | 33.6880 | 73.0550 |
| Margalla Road (alternate) | 33.7200 | 73.0450 |

### 3. Canonical Schemas — Do Not Alter Field Names
Schemas A–F are defined in `docs/06_shared_integration_contract.md`.
- Copy field names **exactly** into Pydantic models, TypeScript types, and JSON files
- Any schema change must be discussed with the team before implementation
- Never add fields that aren't in the contract

### 4. API Endpoints — Use These Exactly
Base URL dev: `http://localhost:8000`

| Endpoint | Purpose |
|---|---|
| POST `/api/signals/ingest` | Agent 1 pushes signals |
| POST `/api/crisis/detected` | Agent 2 confirms crisis |
| POST `/api/crisis/operational` | Agent 3 posts ops picture |
| POST `/api/crisis/dispatch` | Agent 4 posts dispatch plan |
| POST `/api/crisis/simulation` | Agent 5 posts simulation |
| GET `/api/crisis/full/{id}` | Agent 6 aggregates all |
| POST `/api/crisis/complete` | Agent 6 posts dashboard state |
| GET `/api/crisis/active` | Mobile app polls |
| GET `/api/crisis/{id}` | Web dashboard |
| WS `/ws/crisis/{crisis_id}` | Real-time updates |
| WS `/ws/command` | All crisis feed |

---

## Tech Stack — No Substitutions

| Layer | Technology |
|---|---|
| Agent Orchestration | Google Antigravity (mandatory) |
| Primary LLM | Gemini 3.1 Pro (via Antigravity) |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL + PostGIS |
| Routing | OpenRouteService API |
| OSM roads | Overpass API |
| Web map | **Leaflet.js** (NOT Google Maps JS — avoid double quota) |
| Mobile map | react-native-maps (Google Maps SDK) |
| Mobile framework | React Native 0.74 + Expo |
| CSS | Tailwind CSS |

---

## Role Boundaries

| Component | Owner | Do NOT touch unless asked |
|---|---|---|
| `backend/` | Ahmar | Yes |
| `agents/agent_1*/`, `agent_2*/`, `agent_3*/` | Tabeen | Yes |
| `agents/agent_4*/`, `agent_5*/` | Ahmar | Yes |
| `web-dashboard/` | Abdul Mannan | This is our work |
| `mobile-app/` | Abdul Mannan | This is our work |
| `agents/agent_6*/` | Abdul Mannan | This is our work |
| All `.agy_rules` files | Abdul Mannan | This is our work |

---

## Code Standards

- **No comments** unless the WHY is non-obvious
- **No premature abstractions** — three similar lines > an unneeded helper
- **No extra features** beyond what the demo requires
- **All simulated data** must include `"source": "simulated"` field
- **No `.env` files committed** — use `.env.example` with keys listed but no values
- React components: functional + hooks only, no class components
- TypeScript where possible on frontend

---

## What Judges Evaluate (Prioritize These)

1. **Antigravity integration (25%)** — all 6 agents visible in Agent Manager, reasoning traces exported
2. **Agentic reasoning (20%)** — observe → reason → decide → act → evaluate loop visible in traces
3. **Problem understanding (20%)** — two-layer architecture, coordinated dispatch, not just detection
4. **Action simulation (15%)** — map updates, before/after traffic, emergency ticket, public alerts
5. **Technical (10%)** — backend works, DB holds data, WebSocket updates dashboard
6. **UX/Innovation (10%)** — dual-audience design, Urdu/English, realistic Pakistan scenario

---

## When Uncertain

1. Check `docs/` first — especially `02_system_architecture.md` and `06_shared_integration_contract.md`
2. If still unclear, ask Abdul Mannan — do not guess or invent
3. Never invent API endpoints, schema fields, or coordinates not in the docs

---

## Project Structure
```
ciro/
├── CLAUDE.md               ← This file
├── docs/                   ← All design documents (read-only reference)
├── backend/                ← Ahmar's — FastAPI + DB
├── agents/
│   ├── agent_1_signal_ingestion/     ← Tabeen
│   ├── agent_2_crisis_detection/     ← Tabeen
│   ├── agent_3_situational_awareness/← Tabeen
│   ├── agent_4_resource_dispatch/    ← Ahmar
│   ├── agent_5_simulation/           ← Ahmar
│   └── agent_6_dashboard/            ← Abdul Mannan (us)
├── web-dashboard/          ← Abdul Mannan (us)
├── mobile-app/             ← Abdul Mannan (us)
└── README.md
```
