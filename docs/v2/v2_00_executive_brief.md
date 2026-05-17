# CIRO v2 — Executive Brief
## What Changed, What Was Missing, and What We're Building Now

---

## 1. Honest Assessment of v1

The v1 build produced a working scaffold. Every component exists. But several fundamental issues prevent it from being anything more than a demo that runs once on one machine:

**Agent pipeline is a script queue, not an agentic system.**
Running `run_pipeline.sh` calls Python scripts in order. That is a batch job. Agents in a real system observe state, react to events, make decisions with incomplete information, and run concurrently. The current pipeline cannot handle two simultaneous crises. It cannot react to a crisis escalating mid-pipeline. It cannot have Agent 3 and Agent 4 work in parallel once Agent 2 confirms a crisis.

**Only one of two tracks was built.**
The system was designed from the start as two-track: (1) urban signal intelligence for the public and emergency dispatch, and (2) multi-agency coordination for NDMA, military, NGOs during large-scale crises. Track 2 does not exist in v1. Not even a scaffold. This is the more differentiated, more defensible, and harder-to-replicate part of the system.

**No real data ingestion.**
Agents read from `mock_social_media.json`. That is the only "live" input. The original architecture planned: Pakistan Met Department weather, UNOSAT flood maps, NDMA PDF reports, Overpass API road network, ReliefWeb/OCHA crisis updates, HealthSites.io facility data. None of these are integrated.

**Mobile app does not function.**
Maps don't render, icon imports are broken, API calls error out. It is a layout exercise with navigation wired up.

**Not deployed anywhere.**
Backend runs locally. If the laptop closes, the system stops.

---

## 2. The Two-Track System (Full Vision)

```
TRACK 1 — Urban Crisis Intelligence (civilian + dispatch)
┌──────────────────────────────────────────────────────────┐
│  Signals: social media (Urdu/English), weather, traffic  │
│  Detects: flooding, accidents, heatwaves, blockages       │
│  Outputs: public alerts, traffic rerouting, dispatch      │
│  Audience: civilians (mobile app) + dispatch teams        │
└──────────────────────────────────────────────────────────┘

TRACK 2 — Multi-Agency Response Coordination (ops room)
┌──────────────────────────────────────────────────────────┐
│  Signals: NDMA PDFs, UNOSAT maps, OCHA updates, field     │
│  Manages: NDMA, PDMAs, military, NGOs, INGOs              │
│  Outputs: resource allocation, SITREPs, de-confliction    │
│  Audience: NDMA commanders, military ops, NGO field leads │
└──────────────────────────────────────────────────────────┘
```

These two tracks share the same backend, the same database, and the same map infrastructure. Track 1 events can escalate into Track 2 when a crisis exceeds a severity threshold (e.g., flooding moves from "urban incident" to "district-level disaster").

---

## 3. What "Production-Ready" Means Here

The term is not used loosely. This system needs to:

- Handle multiple simultaneous crises in different cities
- Ingest live data from real APIs (not mock files)
- Not crash when OpenRouteService is slow, or when a PDF is malformed
- Be testable by actual emergency coordinators before real deployment
- Run 24/7 on cloud infrastructure within a $5/month + free tier budget
- Generate outputs that a real NDMA officer could read and act on

"Battle-tested" in this context means: a pilot with Pakistan's 1122 rescue services or a regional PDMA could run a tabletop exercise using this system and the outputs would be credible.

---

## 4. What We Reuse from v1

| Component | Reuse Decision |
|---|---|
| FastAPI backend structure | Reuse, extend significantly |
| PostgreSQL + PostGIS schema | Reuse, add Track 2 tables |
| WebSocket manager | Reuse |
| Agent scripts (Python logic) | Refactor into event-driven services, not scripts |
| Leaflet.js map component | Reuse, extend |
| Mobile app screens | Discard structure, keep screen names and navigation concept |
| run_pipeline.sh | Replace with Pub/Sub event system |
| Mock data JSON files | Supplement with real API connectors |
| Agent prompts | Refactor for both tracks |

---

## 5. Technology Decisions for v2

| Decision | Choice | Reason |
|---|---|---|
| Agent communication | Google Cloud Pub/Sub | Event-driven, free tier 10GB/month, native Cloud Run integration |
| Database | Supabase (PostgreSQL + PostGIS) | Free tier, real-time subscriptions, PostGIS included, no Cloud SQL cost |
| Agent deployment | Google Cloud Run | Free tier: 2M req/month + 360K GB-sec compute |
| File/map storage | Google Cloud Storage | Free 5GB for UNOSAT GeoTIFFs, NDMA PDFs |
| Mobile build | Expo EAS (free tier) | Managed builds, OTA updates |
| Web hosting | Firebase Hosting | Free tier, CDN |
| Urdu NLP | Gemini Flash (multilingual) | No model training needed; handles Urdu natively |
| Crisis text classification | Vertex AI + Gemini Flash | $5 credit covers thousands of calls |
| Routing | OpenRouteService | Free 2K req/day |
| Weather | Pakistan Met Dept + Open-Meteo | Both free |
| Flood maps | UNOSAT | Free, REST API |
| NDMA/OCHA data | ReliefWeb API | Free |

**Total estimated monthly cost in steady state:** $0–$3 (within free tiers for a testing deployment)

---

## 6. The Gaps Nobody Described

These were missing from all prior documents and need explicit attention in v2:

**Gap 1: No escalation logic.** When does a Track 1 urban crisis become a Track 2 multi-agency event? The system needs a defined severity/duration threshold that automatically activates Track 2 coordination.

**Gap 2: No state persistence across agent runs.** If the backend restarts mid-pipeline, the crisis state is partially lost. The Supabase realtime subscription and a proper state machine solves this.

**Gap 3: No data deduplication.** Social media will produce dozens of posts about the same flood. Without deduplication, Agent 2 will over-count confidence. Need location-time clustering with dedup before classification.

**Gap 4: No human-in-the-loop interface.** A real NDMA operator needs to confirm, override, or escalate agent decisions. The dashboard needs an action panel, not just a read-only view.

**Gap 5: No offline-capable mobile.** If a civilian is in a flood zone, their connection may be degraded. The mobile app must cache the last alert state locally and use voice to convey critical information.

**Gap 6: No audit trail.** Every agent decision that leads to a dispatch order or public alert must be logged immutably for post-incident review. This is a legal and operational requirement for emergency services.
