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

### Checkpoint 2: May 18 End-to-End Test
- [ ] All 6 agents complete pipeline sequentially
- [ ] Dashboard updates via WebSocket
- [ ] Mobile app shows active crisis with correct location
- [ ] CIRO_agent_trace.log consolidated from all agents

**Status:** In planning

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
