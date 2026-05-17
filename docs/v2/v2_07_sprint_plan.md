# CIRO v2 — Sprint Plan
## Complete Development Roadmap (No Role Split — Task-First)

---

## Sprint 0: Environment & Foundation
**Goal:** Everything runs locally. No broken imports. No package errors. Database connected.

### Tasks

**Backend foundation:**
- [ ] Migrate from local PostgreSQL to Supabase — create project at supabase.com
- [ ] Run Supabase schema migration (all tables from v2_06_backend_v2.md §3)
- [ ] Update backend Supabase client: `pip install supabase==2.4.6`
- [ ] Replace all SQLAlchemy queries with Supabase client calls
- [ ] Verify all existing v1 endpoints still work with Supabase
- [ ] Create Google Cloud project, enable Pub/Sub API, create all topics from architecture doc
- [ ] Add `app/core/pubsub.py` — Pub/Sub publisher client
- [ ] Create service account, download JSON key to `backend/service-account.json`

**Environment:**
- [ ] Create `.env.production` template with all vars from v2_03_data_ingestion.md §11
- [ ] Register for all APIs (checklist in v2_03_data_ingestion.md §12)
- [ ] Confirm Google Cloud free tier limits are not exceeded

**Mobile app cleanup:**
- [ ] In Claude Code: run `npm audit --audit-level=high`
- [ ] Fix all HIGH/CRITICAL vulnerabilities: `npx expo install [affected-package]@[safe-version]`
- [ ] Run `npx expo-doctor` → resolve ALL issues
- [ ] Run `npx tsc --noEmit` → fix all TypeScript errors
- [ ] Verify Android build: `cd android && ./gradlew clean assembleDebug`
- [ ] Fix `react-native-maps` rendering (Google Maps API key correctly loaded in AndroidManifest.xml)
- [ ] Fix icon imports (use `@expo/vector-icons` Feather, not custom SVGs)

**Definition of done:** Backend connects to Supabase, mobile app builds clean APK, no type errors, no audit vulnerabilities.

---

## Sprint 1: Real Data Ingestion
**Goal:** System ingests live data from at least 3 real APIs. No mock JSON files as primary sources.

### Tasks

**Ingestion services (new `ciro/ingestion/` directory):**
- [ ] `ingestion/weather_ingestor/main.py`
  - Calls Open-Meteo every 15 min for Islamabad, Lahore, Karachi, Rawalpindi
  - Parses `CRISIS_WEATHER_CODES` (from v2_02_agent_architecture.md)
  - Publishes to `signals.raw` Pub/Sub topic if crisis threshold exceeded
  - Deploy as Cloud Run Job, trigger via Cloud Scheduler

- [ ] `ingestion/social_monitor/main.py`
  - Nitter RSS scraper for CRISIS_SEARCH_TERMS list
  - Runs continuously (Cloud Run service)
  - Filters: last 1 hour, Pakistan-geolocated or Pakistan-keywords
  - Publishes to `signals.raw`

- [ ] `ingestion/news_ingestor/main.py`
  - RSS feeds: Geo.tv, Dawn, ARY, Samaa, Express Urdu
  - Keyword filter before publishing
  - Publishes to `signals.raw`

- [ ] `ingestion/ndma_pdf_ingestor/main.py`
  - Scrapes ndma.gov.pk/situation-reports/ every 2 hours
  - Downloads new PDFs, parses with PyMuPDF
  - Gemini Flash structures the text
  - Stores in Supabase `ndma_reports` table + publishes signal

- [ ] `ingestion/overpass_cache/main.py`
  - Pre-caches road network for 5 major Pakistani cities
  - Runs daily, stores in Supabase `road_network` table
  - On-demand queries still available for new crisis zones

**Backend webhook receivers:**
- [ ] `POST /webhooks/pubsub/signals-raw` — receives all raw signals, stores in Supabase
- [ ] Deduplication: semantic similarity check using sentence-transformers model
- [ ] After dedup: publishes clean signals to `signals.processed`

**Tests:**
- [ ] Test weather ingestor parses all 10 weather code scenarios correctly
- [ ] Test NDMA PDF parser against a real 2022 flood report (download from ndma.gov.pk)
- [ ] Test deduplication: 10 posts about same flood → only 2-3 unique signals

**Definition of done:** Running `./ingest_demo.sh` populates Supabase `signals` table with real data from at least weather + one news source within 60 seconds.

---

## Sprint 2: Track 1 Agents — Production Grade
**Goal:** Agents run as Cloud Run services subscribed to Pub/Sub. No manual script execution.

### Tasks

**Refactor agent structure:**
- [ ] Create `agents/base/agent_base.py` (from v2_02_agent_architecture.md §1)
- [ ] Each agent becomes a FastAPI app with `/pubsub/push` endpoint + `/health`
- [ ] Create `Dockerfile` for each agent (agents share base image)

**Agent 1 — Signal Normalization Service:**
- [ ] Install sentence-transformers in Docker image (downloads model at build time)
- [ ] Implement semantic deduplication (v2_02 §2)
- [ ] Implement clustering algorithm (5km radius, 45-min window)
- [ ] Implement Gemini Flash text normalization with Urdu support
- [ ] Test: 10 Urdu social posts → normalized correctly to SignalEvent schema
- [ ] Deploy to Cloud Run, subscribe to `signals.processed` Pub/Sub push

**Agent 2 — Crisis Detection:**
- [ ] Implement confidence scoring formula (v2_02 §2)
- [ ] Implement severity estimation rules by crisis type
- [ ] Implement escalation check → publish to `crisis.major` if criteria met
- [ ] Test: input cluster of 3 corroborating signals → crisis.json with confidence > 0.7
- [ ] Test: single unrelated signal → no crisis published
- [ ] Deploy to Cloud Run

**Agent 3 — Situational Awareness:**
- [ ] Implement parallel async fetching (asyncio.gather)
- [ ] Overpass API road network query
- [ ] UNOSAT flood extent fetch (if flood type)
- [ ] Facility data from Supabase cache
- [ ] Test: given G-10 crisis coords → operational picture with road closures
- [ ] Deploy to Cloud Run

**Agent 4 — Resource Dispatch:**
- [ ] Implement priority_score formula (v2_02 §2)
- [ ] Implement OCHA consumption rate calculator
- [ ] Gemini dispatch reasoning generation
- [ ] Test: operational picture + inventory → 2 dispatch orders with reasoning
- [ ] Deploy to Cloud Run

**Agent 5 — Route & Simulation:**
- [ ] OpenRouteService integration + 3-level fallback chain (v2_02 §2)
- [ ] Traffic simulation (before/after state calculation)
- [ ] Google Cloud TTS voice alert generation → upload to Cloud Storage
- [ ] Test: dispatch order → route JSON + simulated traffic state
- [ ] Test: ORS API down → graceful fallback to straight-line
- [ ] Deploy to Cloud Run

**Agent 6 — Alert Generation:**
- [ ] Gemini bilingual alert text generation (Urdu + English)
- [ ] Location-based alert zone calculation (1.5x crisis radius)
- [ ] PublicAlert record creation + publish to `alert.broadcast`
- [ ] Test: simulation output → public alert with both languages
- [ ] Deploy to Cloud Run

**Backend webhook receivers:**
- [ ] All 6 webhook endpoints complete (v2_06_backend_v2.md §4)
- [ ] State machine enforcing all transitions
- [ ] All state changes broadcast via WebSocket
- [ ] All decisions logged to audit_log

**End-to-end test:**
- [ ] Trigger: inject a G-10 flood scenario via `POST /api/v2/debug/inject-scenario`
- [ ] Watch: all 6 agents process in sequence via Pub/Sub
- [ ] Verify: Supabase has complete crisis record after ~90 seconds
- [ ] Verify: public_alerts table has Urdu + English alert
- [ ] Verify: audio file in Cloud Storage

**Definition of done:** Full pipeline runs cloud-to-cloud without any local script execution.

---

## Sprint 3: Track 2 — Multi-Agency Coordination
**Goal:** The second track is functional end-to-end.

### Tasks

**Data foundation:**
- [ ] Seed `agencies` table: NDMA, PDMA Punjab, PDMA Sindh, 1122 Rescue, Red Crescent Pakistan, UN OCHA, IOM Pakistan
- [ ] Seed `resources` table: realistic Pakistan rescue/relief inventory
- [ ] ReliefWeb ingestor: `ingestion/reliefweb_ingestor/main.py`
- [ ] HealthSites.io: seed `facilities` table (one-time script for Pakistan)

**T2 Agents:**
- [ ] `T2-A1: Agency Status Agent`
  - Monitor Supabase `agencies` table for updates
  - Parse NDMA PDFs → update agency deployments
  - Publish `track2.agency_status` events
  - Deploy to Cloud Run

- [ ] `T2-A2: Resource Gap Agent`
  - OCHA consumption rate calculation (v2_02 §3)
  - Priority ranking: severity × accessibility × unmet need
  - Auto-refresh every 30 min during active crisis
  - Deploy to Cloud Run

- [ ] `T2-A3: Field Coordination Agent`
  - De-confliction algorithm (Shapely polygon operations)
  - Coverage gap detection
  - Coordination message drafting (Gemini)
  - Deploy to Cloud Run

- [ ] `T2-A4: Command Intelligence Agent`
  - SITREP generation (full prompt from v2_02 §3)
  - PDF generation via WeasyPrint: `pip install weasyprint`
  - Upload PDF to Cloud Storage
  - Deploy to Cloud Run

**Backend Track 2:**
- [ ] All Track 2 API endpoints (`/api/v2/track2/*`)
- [ ] Escalation handler: when `crisis.major` → activate Track 2, notify T2 agents
- [ ] SITREP PDF serving via Cloud Storage signed URL

**Tests:**
- [ ] Escalation: severity=4 crisis → T2 activates automatically
- [ ] Gap calculation: 10,000 people × OCHA rates → correct gap numbers
- [ ] De-confliction: 2 overlapping agency coverages → overlap detected and flagged
- [ ] SITREP: complete Track 2 state → SITREP document generated (readable, correct format)

---

## Sprint 4: Mobile App — Complete Build
**Goal:** The mobile app is fully functional, visually complete, and production-ready.

### Claude Design Phase (web)
For each screen, use the workflow from v2_05_claude_design_code_guide.md §4.

- [ ] `src/theme/` — complete color, typography, spacing tokens
- [ ] `src/components/ui/` — Badge, StatusPill, BilingualText, Button, Card, Skeleton
- [ ] `src/hooks/useCrisisData.ts` — React Query, handles loading/error/offline
- [ ] `src/hooks/useVoiceAlert.ts` — download, cache, play
- [ ] `src/hooks/useLocationAlerts.ts` — location-based auto-play
- [ ] `src/services/offlineCache.ts` — AsyncStorage with expiry

### Screens (Claude Code integration)
- [ ] `HomeScreen.tsx` — map renders correctly, crisis zone circle, bottom sheet
- [ ] `CrisisDetailScreen.tsx` — full spec from v2_04 §8.3
- [ ] `AlertsScreen.tsx` — filter pills, severity sections, navigation to routes
- [ ] `SafeRoutesScreen.tsx` — map + route cards with ETA
- [ ] `ReportIncidentScreen.tsx` — form with location, chip select, submit
- [ ] `ProfileScreen.tsx` — alert preferences, voice settings, language

### Voice alerts:
- [ ] `expo-av` for audio playback
- [ ] `expo-file-system` for caching
- [ ] Pre-cache on entering affected zone
- [ ] Auto-play if severity ≥ 4 and user in zone
- [ ] Manual play button always available on CrisisDetail

### Offline support:
- [ ] App launches with cached data if offline
- [ ] "Offline" banner shown
- [ ] Citizen reports queued and sent when reconnected
- [ ] Voice alerts playable without internet (cached)

### Testing (Claude Code):
- [ ] All hooks: Vitest unit tests
- [ ] Voice alert service: tested with mocked expo-av
- [ ] Offline cache: tested with mocked FileSystem
- [ ] `npx tsc --noEmit` — 0 errors
- [ ] `npm audit --audit-level=high` — 0 vulnerabilities
- [ ] Android build: `./gradlew assembleDebug` — clean build
- [ ] Test on physical Android device via USB

---

## Sprint 5: Web Dashboard — Complete Build
**Goal:** Dashboard is production-grade, all tabs functional, Track 2 panel working.

### Claude Design Phase (web)
- [ ] `src/theme/index.ts` — CSS variables matching Naval Command palette
- [ ] All base components (`/components/ui/`)
- [ ] Map components (Leaflet layers, route overlay, traffic toggle)
- [ ] Layout components (Header, LeftPanel, BottomPanel, RightPanel)
- [ ] All 5 bottom panel tabs
- [ ] Track 2 right panel

### Features:
- [ ] WebSocket: auto-reconnect on disconnect, offline banner
- [ ] Agent trace: virtual scrolling (handles 10K+ lines), filter, search
- [ ] Map: all overlay types (crisis zone, road closure, routes, unit markers)
- [ ] Map: Before/After traffic toggle (animated transition)
- [ ] Map: unit markers animate along route waypoints
- [ ] SITREP tab: renders markdown, PDF download button
- [ ] Operator actions: confirm/override/resolve buttons with confirmation modal
- [ ] Human-in-the-loop: override dispatch order panel
- [ ] Track 2: agency grid, gap table, de-confliction mini-map

### Testing:
- [ ] Vitest: all hooks and utility functions
- [ ] `npx tsc --noEmit` — 0 errors
- [ ] Lighthouse: Performance > 80, Accessibility > 90
- [ ] Test with 100 mock crises in the list (no jank)
- [ ] Test WebSocket reconnection (disable backend briefly)

---

## Sprint 6: Deployment
**Goal:** Everything is deployed and accessible via public URLs.

### Tasks:

**Backend:**
- [ ] `Dockerfile` builds clean: `docker build -t ciro-backend .`
- [ ] Google Cloud Build trigger on `main` branch push
- [ ] `gcloud run deploy ciro-backend --region asia-south1`
- [ ] Cloud Run connects to Supabase via `DATABASE_URL` env var
- [ ] All Pub/Sub push subscriptions point to Cloud Run backend URL
- [ ] Verify: `curl https://ciro-backend-xxx.a.run.app/health` returns 200

**Agents:**
- [ ] Each agent has its own Dockerfile
- [ ] Each agent deployed as Cloud Run service
- [ ] Pub/Sub push subscriptions configured for each agent
- [ ] Health check endpoints verified

**Ingestion services:**
- [ ] Weather ingestor: Cloud Run Job + Cloud Scheduler (every 15 min)
- [ ] Social monitor: Cloud Run service (always-on, min 1 instance during active crisis)
- [ ] NDMA PDF ingestor: Cloud Scheduler every 2 hours

**Web dashboard:**
- [ ] `npm run build` → `dist/`
- [ ] `firebase deploy --only hosting`
- [ ] Update CORS settings in backend to allow Firebase Hosting domain

**Mobile app:**
- [ ] Update `EXPO_PUBLIC_BACKEND_URL` to production Cloud Run URL
- [ ] `npx eas build --profile production --platform android` (Expo EAS free tier)
- [ ] Download APK, install on test device
- [ ] Verify all features work against production backend

**Environment:**
- [ ] All secrets in Google Cloud Secret Manager (not env vars directly)
- [ ] Cloud Run reads secrets via Secret Manager bindings
- [ ] No secrets in Git history

---

## Sprint 7: Hardening & Pilot Readiness
**Goal:** System handles failure, edge cases, and real-world usage.

### Tasks:

**Robustness:**
- [ ] All external API calls have timeout + retry logic (httpx: `timeout=10, max_retries=3`)
- [ ] Agent failures don't crash the pipeline — Pub/Sub retries on 5xx
- [ ] Malformed PDFs handled gracefully (try/except in NDMA parser)
- [ ] Gemini Flash rate limit handled: exponential backoff + fallback text
- [ ] Duplicate crisis prevention: same location/type within 1 hour → updates existing

**Load testing:**
- [ ] Simulate 5 simultaneous crises → all pipelines run independently
- [ ] 100 concurrent WebSocket connections → no dropped messages
- [ ] 500 citizen reports in 1 minute → deduplication works, no DB overflow

**Monitoring:**
- [ ] Cloud Run logs stream to Cloud Logging
- [ ] Set up Cloud Monitoring alert: error rate > 5% for any agent
- [ ] Supabase dashboard: monitor row counts, free tier limits (500MB)

**Documentation for testers:**
- [ ] `README.md` — complete setup, API list, known issues
- [ ] `TESTING_GUIDE.md` — how to run a tabletop exercise with the system
- [ ] `OPERATOR_GUIDE.md` — dashboard usage, how to override, how to resolve

---

## Technical Debt Log (Address in Sprint 7)

| Issue | Location | Fix |
|---|---|---|
| run_pipeline.sh | root | Delete — replaced by Pub/Sub |
| mock JSON files as primary source | agents/data/ | Keep as test fixtures only, not production input |
| SQLAlchemy ORM models | backend/app/models/ | Replace with Supabase client calls + Pydantic only |
| Hardcoded demo scenario | multiple files | Generalize to parameter-driven |
| Agent 6 on same machine as others | agents/ | Deploy as independent Cloud Run service |
