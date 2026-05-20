# CIRO v2 — System Architecture
## Dual-Track, Event-Driven, Cloud-Deployed

---

## 1. High-Level Architecture

```
╔══════════════════════════════════════════════════════════════════════╗
║                    DATA INGESTION LAYER                              ║
║  PMD Weather │ Open-Meteo │ UNOSAT │ OSM │ ReliefWeb │ Social NLP    ║
║  Pakistan 1122 │ NDMA PDFs │ HealthSites.io │ Google Maps Traffic    ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
                              ▼ events
╔══════════════════════════════════════════════════════════════════════╗
║                  GOOGLE CLOUD PUB/SUB (Event Bus)                    ║
║  Topics: signals.raw │ crisis.detected │ crisis.major                ║
║          ops.updated │ dispatch.ready │ simulation.done              ║
║          track2.activated │ sitrep.generated │ alert.broadcast       ║
╚══════════════════════════════════════════════════════════════════════╝
         │                                          │
         ▼ TRACK 1                                  ▼ TRACK 2
╔═════════════════════╗                  ╔═════════════════════════════╗
║  URBAN CRISIS       ║                  ║  MULTI-AGENCY COORDINATION  ║
║  INTELLIGENCE       ║                  ║                             ║
║                     ║                  ║  T2-A1: Agency Status Agent ║
║  A1: Signal Ingest  ║                  ║  T2-A2: Resource Gap Agent  ║
║  A2: Crisis Detect  ║                  ║  T2-A3: Field Coord Agent   ║
║  A3: Situational    ║◄────escalate────►║  T2-A4: Command Intel Agent ║
║  A4: Dispatch       ║                  ║                             ║
║  A5: Simulation     ║                  ║  NDMA │ PDMA │ Military     ║
║  A6: Alert Gen      ║                  ║  NGOs │ UN Agencies         ║
╚═════════════════════╝                  ╚═════════════════════════════╝
         │                                          │
         └──────────────────┬───────────────────────┘
                            ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    FASTAPI BACKEND (Cloud Run)                       ║
║   REST API │ WebSocket │ Agent Webhook Receivers │ State Machine     ║
╚══════════════════════════════════════════════════════════════════════╝
         │                    │                    │
         ▼                    ▼                    ▼
╔══════════════╗    ╔══════════════════╗  ╔═══════════════════╗
║  Supabase    ║    ║  Cloud Storage   ║  ║  Firebase Hosting ║
║  PostgreSQL  ║    ║  GeoTIFFs │ PDFs ║  ║  Web Dashboard    ║
║  + PostGIS   ║    ║  Audio Alerts    ║  ║                   ║
║  + Realtime  ║    ╚══════════════════╝  ╚═══════════════════╝
╚══════════════╝
         │
         ▼
╔══════════════════════════════════════════════════════════════════════╗
║                        CLIENT LAYER                                  ║
║   Mobile App (Expo/RN)  │  Web Dashboard (React + Leaflet)           ║
║   Voice Alerts (offline-capable) │ Ops Room Dashboard (Track 2)      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 2. Event Bus Architecture

Every agent interaction flows through Pub/Sub topics. Agents are Cloud Run services that subscribe to topics and publish to topics. Nothing calls anything else directly except the frontend → backend REST.

### Topics and Their Subscribers

| Topic | Published By | Subscribed By | Trigger |
|---|---|---|---|
| `signals.raw` | Ingestion services | A1 Signal Ingest | New raw signal arrives |
| `signals.processed` | A1 | A2 Crisis Detect | Processed signal batch ready |
| `crisis.detected` | A2 | A3 Situational, A6 Alert | Crisis confidence > 0.7 |
| `crisis.major` | A2 or operator | T2-A1 Agency Status, T2-A2 Resource Gap | Severity ≥ 4 OR duration > 2hr |
| `ops.picture.ready` | A3 | A4 Dispatch | Operational picture built |
| `dispatch.planned` | A4 | A5 Simulation | Dispatch orders generated |
| `simulation.complete` | A5 | A6 Alert, backend | Route simulation done |
| `alert.broadcast` | A6 | Backend (WebSocket + push) | Public alert ready |
| `sitrep.generated` | T2-A4 | Backend (dashboard) | SITREP document ready |
| `track2.update` | Any T2 agent | Backend, Ops dashboard | Multi-agency state changed |
| `crisis.resolved` | Operator or A2 | All agents | Crisis over, deallocate |

### Event Schema (all Pub/Sub messages follow this wrapper)

```json
{
  "event_id": "evt_20260517_001",
  "topic": "crisis.detected",
  "crisis_id": "CRS_20260513_001",
  "track": 1,
  "timestamp": "ISO8601",
  "source_agent": "agent_2_crisis_detection",
  "payload": { ... },
  "schema_version": "2.0"
}
```

---

## 3. Track 1 — Urban Crisis Intelligence

**Trigger:** Any raw signal arriving from ingestion services.  
**Outputs:** Public alerts, traffic rerouting recommendations, emergency dispatch orders.  
**Audience:** Civilians via mobile app; local emergency dispatch.

### Agent Flow (parallel after A2)

```
[Ingestion Services] → signals.raw topic
         │
    [A1: Normalizer]  ← runs continuously
         │ signals.processed
    [A2: Classifier]  ← confidence scoring + clustering
         │
    ┌────┴──────────────────────┐
    │ crisis.detected           │ crisis.major
    ▼                           ▼
[A3: Situational]          [Escalate to Track 2]
[A4: Dispatch]  ← parallel after A3
[A5: Simulation]
    │
[A6: Alert Generator]
    │
[alert.broadcast → backend → WebSocket + push]
```

A3, A4, and A5 run in sequence but A4 and A5 can begin as soon as A3 finishes a partial picture (road closures don't need to wait for all facility data). This is the key improvement over v1's fully sequential pipeline.

---

## 4. Track 2 — Multi-Agency Coordination

**Trigger:** `crisis.major` event (severity ≥ 4 OR operator activation OR duration threshold).  
**Outputs:** Resource allocation across agencies, SITREP documents, de-confliction maps, field coordination messages.  
**Audience:** NDMA commanders, PDMA officers, military liaison, NGO coordinators.

### Track 2 Agent Set

**T2-A1: Agency Status Agent**
- Monitors: NDMA daily reports (Supabase storage), ReliefWeb API, manual operator inputs
- Maintains: per-agency capacity table (what each agency has deployed, available, and requested)
- Publishes: `track2.agency_status` events on any capacity change

**T2-A2: Resource Gap Agent**
- Input: affected population from A3, OCHA consumption standards, agency capacity from T2-A1
- Process: gap calculation per district, priority ranking (severity × accessibility × unmet need)
- Output: deployment recommendation list, auto-refreshed every 30 min during active crisis

**T2-A3: Field Coordination Agent**
- Input: all agency deployments, coverage maps from T2-A2
- Process: de-confliction (flags overlapping coverage), coordination messaging drafts
- Output: de-conflicted coverage map, WhatsApp/SMS drafts per agency, task assignment log

**T2-A4: Command Intelligence Agent**
- Input: all T2 agent outputs + Track 1 crisis data
- Process: Gemini Flash generates SITREP in NDMA format; strategic decision support
- Output: SITREP document (PDF via WeasyPrint), command dashboard state, briefing cards

### Track 2 Escalation Logic

```python
def should_escalate_to_track2(crisis: CrisisEvent) -> bool:
    return any([
        crisis.severity >= 4,
        crisis.affected_population_estimate >= 10_000,
        crisis.duration_hours >= 2,
        crisis.type in ["major_flood", "earthquake", "mass_casualty"],
        crisis.multi_district == True
    ])
```

When escalation triggers:
1. Backend publishes `crisis.major` to Pub/Sub
2. T2-A1 immediately fetches all agency statuses
3. Ops dashboard gains a "Track 2 Active" banner
4. Track 2 panel appears alongside Track 1 view

---

## 5. Antigravity's Role in v2

Antigravity is no longer just a way to run scripts. In v2, Antigravity is the **development and reasoning environment** for all agents. The actual deployed agents are Cloud Run services that wrap Antigravity-designed prompts and logic.

**Development workflow:**
1. Design agent logic in Antigravity (iterate prompts, test reasoning)
2. Export the finalized prompt + Python wrapper as a Cloud Run service
3. The deployed Cloud Run service uses Gemini Flash API directly (not through Antigravity at runtime)
4. Antigravity continues to be used for monitoring and debugging during testing

**Why this matters:** Antigravity's free tier Gemini access is for development. Production agent calls use Vertex AI Gemini Flash (covered by the $5 credit + free tier). This keeps the system deployable 24/7 without Antigravity being online.

---

## 6. Database — Supabase Schema Overview

Using Supabase (free tier: 500MB, PostGIS, realtime) instead of Cloud SQL to stay within budget.

### Core Tables

```sql
-- Track 1
signals, crises, operational_pictures, dispatch_orders, simulations, public_alerts

-- Track 2 (new)
agencies, agency_deployments, resource_gaps, coordination_messages, sitreps

-- Shared
audit_log, crisis_escalations, user_operators

-- Spatial (PostGIS)
crisis_zones (GEOGRAPHY), road_closures (GEOMETRY), flood_extents (RASTER via PostGIS)
```

Supabase Realtime: the dashboard and mobile app subscribe directly to Supabase realtime channels for instant updates — no custom WebSocket needed for simple state reads.

Custom WebSocket (FastAPI) is kept for: complex agent trace streaming and command dashboard event feed.

---

## 7. Infrastructure Map (Cloud Services)

| Service | Provider | Tier | Monthly Cost | Purpose |
|---|---|---|---|---|
| Backend API | Google Cloud Run | Free (2M req) | $0 | FastAPI + agent webhooks |
| Agent workers | Google Cloud Run Jobs | Free (180K vCPU-sec) | $0 | Agent microservices |
| Event bus | Google Cloud Pub/Sub | Free (10GB) | $0 | Agent communication |
| Database | Supabase | Free (500MB) | $0 | All data + PostGIS + realtime |
| File storage | Google Cloud Storage | Free (5GB) | $0 | GeoTIFFs, PDFs, audio |
| Web hosting | Firebase Hosting | Free (10GB) | $0 | Web dashboard |
| LLM | Vertex AI Gemini Flash | $5 credit + free | ~$1–3 | All AI reasoning |
| Maps (mobile) | Google Maps SDK | Free (28K loads/mo) | $0 | Mobile map |
| Routing | OpenRouteService | Free (2K/day) | $0 | Route calculation |
| Mobile build | Expo EAS | Free tier | $0 | APK/IPA builds |
| **Total** | | | **$0–3/mo** | |

---

## 8. Deployment Topology

```
Local dev (Antigravity IDE)
    │
    │ git push
    ▼
GitHub Actions CI
    │ tests pass
    ▼
Google Cloud Build
    ├── builds backend Docker image → Cloud Run (backend)
    ├── builds agent images → Cloud Run Jobs (each agent)
    └── builds web dashboard → Firebase Hosting

Supabase (external, free)
    └── PostgreSQL + PostGIS + Realtime

Google Cloud Storage
    └── UNOSAT GeoTIFFs, NDMA PDFs, audio alert files

Mobile (Expo EAS)
    └── APK distributed via direct link for testing
```

---

## 9. Crisis Lifecycle State Machine (v2)

```
NEW
 │
 ├─ signals received
 ▼
MONITORING     ← Track 1 active, low signal count
 │
 ├─ confidence > 0.7
 ▼
DETECTED       ← Crisis confirmed, public alert issued
 │
 ├─ severity ≥ 4 OR duration > 2hr
 ├─────────────────────────────────────► TRACK_2_ACTIVE
 │                                              │
 ▼                                              ▼
DISPATCHED     ← Units en route           COORDINATING  ← Agencies aligned
 │                                              │
 ▼                                              ▼
SIMULATED      ← Outcomes projected       FIELD_OPS     ← Active multi-agency
 │                                              │
 ├─ operator confirms                           │
 ▼                                              ▼
RESOLVED ◄──────────────────────────────── STAND_DOWN
 │
 ▼
ARCHIVED       ← Immutable audit log, post-incident review
```

All transitions are logged to `audit_log` with: timestamp, agent or operator trigger, reasoning summary.
