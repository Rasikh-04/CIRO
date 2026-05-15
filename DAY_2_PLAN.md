# CIRO — Day 2 Plan (May 15)

## MANUAL TASKS FOR ABDUL MANNAN

### A. Git & Repo Sync
- [ ] Git becomes available
- [ ] Integrate Tabeen's Agent 1/2/3 code into `/agents/` (zip → extract)
- [ ] Integrate Ahmar's Backend + Agent 4/5 code into `/agents/` and `/backend/` (zip → extract)
- [ ] Verify no conflicts, directory structure clean
- [ ] `git add .` and commit: "Integrate team code from local work"
- [ ] `git push origin main`
- [ ] Message team: "Central repo ready — clone and continue work from branches"

### B. Web Dashboard — Test Locally
- [ ] `cd web-dashboard && npm install` (fix any peer dependency issues)
- [ ] `npm start` — verify loads at `localhost:3000`
- [ ] Test: Map renders, Islamabad coordinates correct (33.6844, 73.0479), dark theme applied
- [ ] Note: Backend offline is expected — dashboard should show "OFFLINE" banner gracefully

### C. Antigravity Setup (Prepare, Don't Run Yet)
- [ ] Antigravity desktop app installed & signed in
- [ ] Create 6 agent workspaces in Agent Manager:
  - [ ] agent_1_signal_ingestion
  - [ ] agent_2_crisis_detection
  - [ ] agent_3_situational_awareness
  - [ ] agent_4_resource_dispatch
  - [ ] agent_5_simulation
  - [ ] agent_6_dashboard
- [ ] Each workspace points to `/home/rasikh/Projects/CIRO/agents/agent_N_*/` folder
- [ ] `.agy_rules` files visible in each workspace

### D. Coordinate with Tabeen & Ahmar
- [ ] Message Tabeen: "Agent 1/2/3 are merged into central repo. Clone and continue from branch `tabeen/*`. May 16 morning we'll test Agent 1 → Backend posting."
- [ ] Message Ahmar: "Backend + Agent 4/5 merged into central repo. Clone and continue from branch `ahmar/*`. May 16 we'll test full dispatch pipeline."

### E. Google Cloud — Double-Check
- [ ] Verify project "ciro-hackathon" exists in Google Cloud Console
- [ ] Verify Maps JavaScript API enabled
- [ ] Verify API keys created for:
  - [ ] Web dashboard (JavaScript restriction)
  - [ ] Mobile app (Android + iOS bundle restrictions)
- [ ] Keys stored securely (not in repo)

---

## CODING TASKS FOR CLAUDE CODE

### Task 1: Mobile App Scaffold (React Native + Expo)
**Deliverables:**
- [ ] `mobile-app/package.json` (Expo + React Native 0.74, TypeScript, react-navigation, react-native-maps)
- [ ] `mobile-app/app.json` (Expo config, app name "CIRO", splash screen)
- [ ] `mobile-app/src/types/index.ts` (TypeScript interfaces matching schemas A–F)
- [ ] `mobile-app/src/screens/HomeScreen.tsx` (Bottom nav: Home, Alerts, Safe Routes, Profile)
- [ ] `mobile-app/src/screens/CrisisDetailScreen.tsx` (Map + crisis info card)
- [ ] `mobile-app/src/navigation/BottomTabNavigator.tsx` (Tab navigation)
- [ ] `mobile-app/src/App.tsx` (Root navigation setup)
- [ ] `mobile-app/.env.local` (REACT_APP_BACKEND_URL, REACT_APP_API_KEY)
- [ ] `mobile-app/eas.json` (Expo build config for Android/iOS)

**Status:** Not started

### Task 2: Agent 6 Dashboard — Add Trace Log Output
**Deliverables:**
- [ ] `agents/agent_6_dashboard/push_to_backend.py` — already complete ✓
- [ ] `agents/agent_6_dashboard/sitrep_generator.py` — already complete ✓
- [ ] Verify both write to `output/agent6_trace.log` with correct format
- [ ] Test locally: `python sitrep_generator.py` produces placeholder SITREP
- [ ] Test locally: `python push_to_backend.py` consolidates all agent logs

**Status:** Review & verify

### Task 3: Web Dashboard — Route Simulation Visualization
**Deliverables:**
- [ ] Update `src/components/MapView.tsx` to display green polyline routes from simulation.routes[].waypoints
- [ ] Add route legend: "Unit Routes: F-8 Rescue Unit Alpha"
- [ ] Handle case when simulation data is empty (no routes yet)

**Status:** Not started

### Task 4: Mobile App — Safe Routes Screen
**Deliverables:**
- [ ] `src/screens/SafeRoutesScreen.tsx` — list alternate routes fetched from backend
- [ ] Display: Route name, distance, ETA, "Avoid" button (logs intent)
- [ ] Fetch from `/api/crisis/{id}/safe-routes` (stub endpoint for now)

**Status:** Not started

### Task 5: Documentation — API Contract Verification
**Deliverables:**
- [ ] Audit all 11 API endpoints defined in `docs/06_shared_integration_contract.md`
- [ ] Verify requests/responses match schemas A–F exactly
- [ ] Create simple table: Endpoint | Method | Owner | Status (Mock/Ready/Pending)
- [ ] Add to `README.md` for clarity

**Status:** Not started

---

## Definition of Done (Daily Checklist)

**For each task:**
- [ ] Code matches TypeScript strictness
- [ ] No console.error or warnings
- [ ] File ownership respected (no touching other team's folders)
- [ ] Simulated data has `"source": "simulated"` where applicable
- [ ] Committed to local branch (when git available)

**At end of day:**
- [ ] All commits pushed to branch (when git available)
- [ ] Abdul reviews & merges
- [ ] CLAUDE.md & MEMORY updated if needed

---

## Priority Order

1. **Mobile app scaffold** (Task 1) — longest lead time, needed for submission
2. **Web dashboard route visualization** (Task 3) — pairs with backend dispatch data
3. **Safe routes screen** (Task 4) — extends mobile app
4. **Agent 6 verification** (Task 2) — short, quick validation
5. **API contract doc** (Task 5) — meta task, do last if time permits

---

## Notes

- **No smoke test today** — Tabeen/Ahmar still integrating locally
- **May 16 morning:** Coordination call with Tabeen/Ahmar to plan Agent 1→Backend testing
- **May 18:** Full pipeline testing (all 6 agents in Antigravity)
- **May 19-20:** Polish, demo video, submit
