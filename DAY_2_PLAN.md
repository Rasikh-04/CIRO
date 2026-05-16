# CIRO — Day 2 Plan (May 15)

## MANUAL TASKS FOR ABDUL MANNAN

### A. Git & Repo Sync
- [x] Git becomes available
- [x] Integrate Tabeen's Agent 1/2 code into `/agents/` (zip → extract)
- [x] Integrate Ahmar's Backend code into `/backend/` (zip → extract)
- [x] Verify no conflicts, directory structure clean
- [x] `git add .` and commit: "Integrate team code from local work"
- [x] `git push origin main`
- [x] Message team: "Central repo ready — clone and continue work from branches"

### B. Web Dashboard — Test Locally
- [x] `cd web-dashboard && npm install` (fix any peer dependency issues)
- [x] `npm start` — verify loads at `localhost:3000`
- [x] Test: Map renders, Islamabad coordinates correct (33.6844, 73.0479), dark theme applied
- [x] Note: Backend offline is expected — dashboard should show "OFFLINE" banner gracefully

### C. Antigravity Setup (Prepare, Don't Run Yet)
- [x] Antigravity desktop app installed & signed in
- [x] Create 6 agent workspaces in Agent Manager:
  - [x] agent_1_signal_ingestion
  - [x] agent_2_crisis_detection
  - [x] agent_3_situational_awareness
  - [x] agent_4_resource_dispatch
  - [x] agent_5_simulation
  - [x] agent_6_dashboard
- [x] Each workspace points to `/home/rasikh/Projects/CIRO/agents/agent_N_*/` folder
- [x] `.agy_rules` files visible in each workspace

### D. Coordinate with Tabeen & Ahmar
- [ ] Message Tabeen: "Agent 1/2 are merged into central repo. Clone and continue from branch `tabeen/*`. May 16 morning we'll test Agent 1 → Backend posting."
- [ ] Message Ahmar: "Backend merged into central repo. Clone and continue from branch `ahmar/*`. May 16 we'll test full dispatch pipeline."

### E. Google Cloud — Double-Check
- [x] Verify project "ciro-hackathon" exists in Google Cloud Console
- [x] Verify Maps JavaScript API enabled
- [ ] Verify API keys created for:
  - [x] Web dashboard — N/A (Leaflet uses OSM tiles, no API key needed)
  - [ ] Mobile app (Android + iOS bundle restrictions) — create key restricted to package `com.aiseekho.ciro`, add to `mobile-app/.env.local`
- [x] Keys stored securely (not in repo) — `.gitignore` covers all `.env` / `.env.local` files

---

## CODING TASKS FOR CLAUDE CODE

### Task 1: Mobile App Scaffold (React Native + Expo)
**Deliverables:**
- [x] `mobile-app/package.json` (Expo + React Native 0.74, TypeScript, react-navigation, react-native-maps)
- [x] `mobile-app/app.json` (Expo config, app name "CIRO", splash screen)
- [x] `mobile-app/src/types/index.ts` (TypeScript interfaces matching schemas A–F)
- [x] `mobile-app/src/screens/HomeScreen.tsx` (Bottom nav: Home, Alerts, Safe Routes, Profile)
- [x] `mobile-app/src/screens/CrisisDetailScreen.tsx` (Map + crisis info card)
- [x] `mobile-app/src/navigation/BottomTabNavigator.tsx` (Tab navigation)
- [x] `mobile-app/src/App.tsx` (Root navigation setup)
- [x] `mobile-app/.env.local` (REACT_APP_BACKEND_URL, REACT_APP_API_KEY)
- [x] `mobile-app/eas.json` (Expo build config for Android/iOS)

**Status:** Complete (not tested yet — Expo Go test pending)

### Task 2: Agent 6 Dashboard — Add Trace Log Output
**Deliverables:**
- [x] `agents/agent_6_dashboard/push_to_backend.py` — complete ✓
- [x] `agents/agent_6_dashboard/sitrep_generator.py` — complete ✓
- [x] Verify both write to `output/agent6_trace.log` with correct format
- [x] Test locally: `python sitrep_generator.py` produces placeholder SITREP
- [x] Test locally: `python push_to_backend.py` consolidates all agent logs

**Status:** Verified complete

### Task 3: Web Dashboard — Route Simulation Visualization
**Deliverables:**
- [x] `src/components/MapView.tsx` displays green polyline routes from `simulation.routes[].route.waypoints`
- [x] Route legend: "Unit Routes" with unit name and green line icon (bottom-right overlay)
- [x] Handles empty simulation data gracefully (legend hidden when no routes)

**Status:** Complete

### Task 4: Mobile App — Safe Routes Screen
**Deliverables:**
- [x] `src/screens/SafeRoutesScreen.tsx` — list alternate routes fetched from backend
- [x] Display: Route name, distance, ETA, risk level badge, "Use This Route" button (logs intent)
- [x] Fetch from `/api/crisis/{id}/safe-routes` (stub endpoint for now)

**Status:** Complete

### Task 5: Documentation — API Contract Verification
**Deliverables:**
- [x] Audited all API endpoints against `docs/06_shared_integration_contract.md`
- [x] Schemas A–F match across TypeScript types and integration contract
- [x] Endpoint table (Endpoint | Method | Owner | Schema | Status) added to `README.md`

**Status:** Complete — see README.md "API Endpoints" section

---

## Definition of Done (Daily Checklist)

**For each task:**
- [x] Code matches TypeScript strictness
- [x] File ownership respected (no touching other team's folders)
- [x] Simulated data has `"source": "simulated"` where applicable
- [ ] Committed to branch (do at end of day)

**At end of day:**
- [ ] All commits pushed to branch
- [ ] Abdul reviews & merges
- [ ] CLAUDE.md & MEMORY updated if needed

---

## Priority Order

1. **Mobile app scaffold** (Task 1) — ✅ Done
2. **Web dashboard route visualization** (Task 3) — ✅ Done
3. **Safe routes screen** (Task 4) — ✅ Done
4. **Agent 6 verification** (Task 2) — ✅ Done
5. **API contract doc** (Task 5) — ✅ Done

---

## Notes

- **No smoke test today** — Tabeen/Ahmar still integrating locally
- **May 16 morning:** Coordination call with Tabeen/Ahmar to plan Agent 1→Backend testing
- **May 18:** Full pipeline testing (all 6 agents in Antigravity)
- **May 19-20:** Polish, demo video, submit
