# CIRO API Status — Endpoint Contract Verification

**Base URL:** `http://localhost:8000` (dev) | `https://ciro-backend-[hash]-uc.a.run.app` (prod)

## All Endpoints & Status

| # | Method | Endpoint | Owner | Request Schema | Response | Status | Notes |
|---|---|---|---|---|---|---|---|
| 1 | POST | `/api/signals/ingest` | Agent 1 | `SignalEvent[]` | `{"accepted": n}` | Pending | Awaiting Agent 1 integration |
| 2 | GET | `/api/signals/latest` | Agent 2 | — | `SignalEvent[]` | Pending | Agent 2 reads latest signals |
| 3 | POST | `/api/crisis/detected` | Agent 2 | `CrisisEvent` | `{"crisis_id": "..."}` | Pending | Crisis detected → stored |
| 4 | GET | `/api/crisis/latest` | Agent 3 | — | `CrisisEvent` | Pending | Agent 3 reads latest crisis |
| 5 | POST | `/api/crisis/operational` | Agent 3 | `OperationalPicture` | `{"ok": true}` | Pending | Ops picture updated |
| 6 | GET | `/api/resources/available` | Agent 4 | — | `Resource[]` | Pending | Agent 4 fetches inventory |
| 7 | POST | `/api/crisis/dispatch` | Agent 4 | `DispatchPlan` | `{"ok": true}` | Pending | Dispatch orders stored |
| 8 | POST | `/api/crisis/simulation` | Agent 5 | `SimulationResult` | `{"ok": true}` | Pending | Route simulation saved |
| 9 | GET | `/api/crisis/full/{id}` | Agent 6 | — | All schemas merged | Pending | Agent 6 aggregates full state |
| 10 | POST | `/api/crisis/complete` | Agent 6 | `DashboardState` | `{"ok": true}` | Pending | Dashboard state finalized |
| 11 | WS | `/ws/crisis/{id}` | Web Dashboard | — | Live `DashboardState` | Pending | Real-time WebSocket updates |
| 12 | GET | `/api/crisis/active` | Mobile App | — | Summary list | Pending | Mobile fetches active crises |

---

## Integration Checkpoint Status

### Checkpoint 1: May 15 Smoke Test (Skipped Today)
- [ ] Backend running at localhost:8000
- [ ] Agent 1 can POST to `/api/signals/ingest` (returns 200)
- [ ] Dashboard can fetch from `/api/crisis/active` (graceful offline fallback implemented)

**Status:** Deferred to May 16

### Checkpoint 2: May 18 Schema Audit (Tabeen — completed 2026-05-17)

Full cross-check of Agent 1/2/3 outputs against backend Pydantic schemas and DB models.
Results below — **5 backend fixes needed before end-to-end test can pass.**

#### Fixed (Agent side — Tabeen, merged)
- [x] **ingest.py `post_to_backend()`** was sending a raw `list` to `/api/signals/ingest`.
      Backend `SignalIngestRequest` expects `{"signals": [...], "ingest_timestamp": "..."}`.
      **Fixed in `tabeen/may18-integration` branch.**

#### Needs Fix — Backend (Ahmar)

| # | File | Issue | Impact |
|---|---|---|---|
| B1 | `backend/app/api/crisis.py` | `/api/crisis/operational` endpoint **does not exist** and is not registered in `main.py` | Agent 3 POST will get 404 — ops picture never stored |
| B2 | `backend/app/models/crisis.py` | `Crisis` DB model has no `contributing_signals` column | Signal IDs sent by Agent 2 are silently dropped — audit trail broken |
| B3 | `backend/app/models/operational_picture.py` | `OperationalPicture` DB model has no `affected_zone` column | Dashboard/Agent 6 can't render the crisis zone boundary |
| B4 | `backend/app/api/signals.py` | `GET /api/signals/latest` returns raw SQLAlchemy objects — `location` is a GeoAlchemy2 `Geography` type, not JSON-serializable | Agent 2 live-fetch will crash; fallback to local file kicks in |
| B5 | `backend/app/api/crisis.py` | `GET /api/crisis/latest` same issue — returns raw `Crisis` ORM object with non-serializable `location` field | Agent 3 live-fetch will crash; fallback to local file kicks in |

**Suggested fixes for Ahmar:**
- B1: Add `@router.post("/crisis/operational")` handler in `crisis.py`, register in `main.py`
- B2: Add `contributing_signals = Column(JSONB)` to `Crisis` model; store in `crisis_detected()`
- B3: Add `affected_zone = Column(JSONB)` to `OperationalPicture` model; store in the new B1 handler
- B4 & B5: Add Pydantic `response_model` to both GET routes, serializing `location` via `geoalchemy2.shape.to_shape()` → dict

**Workaround in place:** Agent 2 (`classify.py`) and Agent 3 (`situational.py`) both have try/except fallbacks that read from local `output/*.json` files when the backend GET endpoints fail. The pipeline will function in demo mode without a live backend.

### Checkpoint 3: May 19 End-to-End Test
- [ ] Backend running with B1–B5 fixes applied
- [ ] Agent 1 POSTs to `/api/signals/ingest` → 200 OK, `{"accepted": 12}`
- [ ] Agent 2 GETs from `/api/signals/latest` → parses correctly
- [ ] Agent 2 POSTs to `/api/crisis/detected` → 200 OK, `{"crisis_id": "CRS_20260513_001"}`
- [ ] Agent 3 GETs from `/api/crisis/latest` → parses correctly
- [ ] Agent 3 POSTs to `/api/crisis/operational` → 200 OK
- [ ] Dashboard updates via WebSocket
- [ ] Mobile app shows active crisis with correct location

**Status:** Blocked on B1–B5

---

## Schema Validation Checklist

✅ **Schema A (SignalEvent)** — Mobile types and Agent 1 generator
✅ **Schema B (CrisisEvent)** — Mobile types and Agent 2 detector
✅ **Schema C (OperationalPicture)** — Web dashboard MapView + types
✅ **Schema D (DispatchPlan)** — Web dashboard DispatchTab + types
✅ **Schema E (SimulationResult)** — Web dashboard route visualization + types
✅ **Schema F (DashboardState)** — Agent 6 aggregation + types

All schemas defined in `/agents/agent_6_dashboard/`, `/web-dashboard/src/types/`, and `/mobile-app/src/types/`.

**Rule:** Any schema field rename/type change must be announced before merging.

---

## Key Notes for Team

1. **No endpoint URL changes allowed** — these are locked in CLAUDE.md
2. **Response format must match exactly** — consumers depend on field names
3. **WebSocket at `/ws/command`** — broadcasts all crisis changes to all clients (web + mobile)
4. **Backend offline graceful** — Web dashboard shows banner, mobile app queues intents locally
5. **Mock data location** — `/backend/data/*.json` (read by all agents during testing)
