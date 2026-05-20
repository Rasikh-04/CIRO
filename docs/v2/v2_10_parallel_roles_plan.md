# CIRO v2 — Parallel Execution Plan
## 3 Roles, May 17–19 (48 hours to demo-ready)

> **Today is May 17. Demo recording is May 19.**  
> This document tells each person exactly what to do, in what order, using which tools.  
> Read your own section fully before starting. Read the handoff points. Don't skip ahead.

---

## Critical Path Overview

```
MAY 17 (TODAY)              MAY 18                      MAY 19
────────────────────────────────────────────────────────────────
AHMAR
  [Cloud setup]──────────►[API keys to team]──────────►[Deploy backend + agents]
  [Supabase schema]        [Monitor + assist]            [Build APK via EAS]
  [Pub/Sub topics]                                       [Help record demo]

TABEEN
  [Agents scaffold]──────►[Track 1 agents working]──►  [Track 2 agents]
  [Ingestion services]     [End-to-end pipeline test]    [Final test + traces]

ABDUL MANNAN
  [Fix mobile (Claude)]──►[Screens complete]──────────►[Dashboard complete]
  [Theme + components]     [API integration]             [Demo video recording]
                                                         [Submission docs]
```

**The only hard dependency:** Ahmar must give Tabeen and Abdul Mannan the `.env` file with credentials by **May 17, 2pm**. Everything else runs in parallel.

---

## Handoff Signals

Use a shared WhatsApp/Slack message for these — don't assume the other person is watching:

| Signal | From | To | Meaning |
|---|---|---|---|
| "✅ ENV FILE READY" | Ahmar | Both | `.env` with all credentials shared |
| "✅ SUPABASE LIVE" | Ahmar | Tabeen | Schema applied, Tabeen can write to DB |
| "✅ PUBSUB LIVE" | Ahmar | Tabeen | All topics created, agents can publish |
| "✅ BACKEND DEPLOYED" | Ahmar | Abdul Mannan | Production URL confirmed, mobile can hit it |
| "✅ PIPELINE WORKING" | Tabeen | Abdul Mannan | Full A1→A6 pipeline runs, real data flowing |
| "✅ MOBILE BUILD" | Abdul Mannan | All | APK installable, all screens functional |
| "✅ DASHBOARD LIVE" | Abdul Mannan | All | Firebase URL confirmed, Track 1 view working |

---

# ROLE A: AHMAR
## Infrastructure, Cloud Setup, APIs, Manual Tasks

**Your tools:** Browser, terminal (gcloud CLI, Supabase CLI), Google Cloud Console, Supabase dashboard  
**No Claude Pro needed — everything here is configuration, not code generation**  
**Your output:** A working `.env` file in the shared repo that everyone uses

---

### MAY 17 — MORNING BLOCK (9am–1pm)
#### Priority: Get credentials to the team before lunch

**Step 1: Google Cloud Project (30 min)**
```bash
# Install gcloud if not installed: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud projects create ciro-production --name="CIRO"
gcloud config set project ciro-production
gcloud billing projects link ciro-production --billing-account=YOUR_BILLING_ACCOUNT_ID
# Find billing account: gcloud billing accounts list

# Enable all APIs in one command
gcloud services enable \
  run.googleapis.com pubsub.googleapis.com cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com texttospeech.googleapis.com \
  storage.googleapis.com secretmanager.googleapis.com \
  aiplatform.googleapis.com logging.googleapis.com
```

**Step 2: Service Account (15 min)**
```bash
gcloud iam service-accounts create ciro-backend \
  --display-name="CIRO Backend"

# Grant all needed roles
for role in pubsub.publisher pubsub.subscriber storage.objectAdmin \
  aiplatform.user secretmanager.secretAccessor run.invoker; do
  gcloud projects add-iam-policy-binding ciro-production \
    --member="serviceAccount:ciro-backend@ciro-production.iam.gserviceaccount.com" \
    --role="roles/$role"
done

# Download key — add to repo as backend/service-account.json (gitignored)
gcloud iam service-accounts keys create service-account.json \
  --iam-account=ciro-backend@ciro-production.iam.gserviceaccount.com
```

**Step 3: Cloud Storage Bucket (10 min)**
```bash
gsutil mb -p ciro-production -l asia-south1 gs://ciro-assets
gsutil iam ch allUsers:objectViewer gs://ciro-assets
```

**Step 4: Pub/Sub Topics (10 min)**
```bash
for topic in signals-raw signals-processed crisis-detected crisis-major \
  ops-picture-ready dispatch-planned simulation-complete alert-broadcast \
  sitrep-generated track2-update crisis-resolved; do
  gcloud pubsub topics create $topic
  echo "Created: $topic"
done
```

**Step 5: Supabase (30 min)**
1. Go to https://supabase.com → New Project
2. Name: `ciro-production`, Region: **Southeast Asia (Singapore)**
3. Wait for project to spin up (~2 min)
4. Go to **SQL Editor** → paste the ENTIRE schema from `v2_06_backend_v2.md §3`
5. Run it. Fix any errors (usually ordering — run `crises` table before tables that reference it)
6. Go to **Settings → API** → copy:
   - Project URL
   - `anon` public key
   - `service_role` secret key

**Step 6: Build the .env file (15 min)**

Create `backend/.env` with these values:
```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=ciro-production
GOOGLE_APPLICATION_CREDENTIALS=service-account.json

# Supabase (from Step 5)
SUPABASE_URL=https://[your-project].supabase.co
SUPABASE_KEY=[anon key]
SUPABASE_SERVICE_KEY=[service_role key]

# Pub/Sub Topics
PUBSUB_SIGNALS_RAW=signals-raw
PUBSUB_SIGNALS_PROCESSED=signals-processed
PUBSUB_CRISIS_DETECTED=crisis-detected
PUBSUB_CRISIS_MAJOR=crisis-major
PUBSUB_OPS_READY=ops-picture-ready
PUBSUB_DISPATCH_PLANNED=dispatch-planned
PUBSUB_SIMULATION_DONE=simulation-complete
PUBSUB_ALERT_BROADCAST=alert-broadcast
PUBSUB_SITREP=sitrep-generated
PUBSUB_TRACK2=track2-update

# APIs (fill as you register below)
OPENROUTESERVICE_API_KEY=
UNOSAT_API_KEY=
HEALTHSITES_API_KEY=
GOOGLE_MAPS_API_KEY=
GEMINI_API_KEY=

# Backend
ENVIRONMENT=production
BACKEND_URL=  (fill after deployment)
```

**📣 SEND "✅ ENV FILE READY" to team — share the .env file in private chat (not Git)**  
**📣 SEND "✅ SUPABASE LIVE" to Tabeen**  
**📣 SEND "✅ PUBSUB LIVE" to Tabeen**

---

### MAY 17 — AFTERNOON BLOCK (1pm–6pm)
#### Priority: API registrations + seed data

**API Registrations (do all of these, they're fast):**

| API | URL | What to do |
|---|---|---|
| OpenRouteService | https://openrouteservice.org/dev/#/signup | Register → Dashboard → Create token → copy |
| HealthSites.io | https://healthsites.io/accounts/register/ | Register → profile → API key |
| UNOSAT | https://unosat.org/user/register | Register (may take up to 24hr to activate) |
| Google Maps | console.cloud.google.com → APIs & Services → Credentials → Create API Key | Enable: Maps SDK for Android, Directions API, Maps JavaScript API |
| Vertex AI / Gemini | Already enabled above. Get key: console.cloud.google.com → APIs → Credentials | Create API Key restricted to Vertex AI |

Add each key to `.env` as you get them. Push updates to the shared repo.

**Seed data for Supabase (run these SQL inserts in Supabase SQL Editor):**

```sql
-- Agencies (Track 2)
INSERT INTO agencies (id, name, type, country) VALUES
('ndma', 'National Disaster Management Authority', 'ndma', 'PAK'),
('pdma_punjab', 'PDMA Punjab', 'pdma', 'PAK'),
('pdma_sindh', 'PDMA Sindh', 'pdma', 'PAK'),
('rescue_1122', 'Punjab Emergency Service (1122)', 'emergency', 'PAK'),
('red_crescent', 'Pakistan Red Crescent Society', 'ngo', 'PAK'),
('un_ocha', 'OCHA Pakistan', 'un', 'PAK'),
('iom', 'IOM Pakistan', 'ingo', 'PAK');

-- Resources / Inventory
INSERT INTO resources (id, name, type, subtype, depot_name, status, quantity, source_label) VALUES
('res_001', 'F-8 Rescue Unit Alpha', 'rescue_unit', 'water_rescue', 'F-8 Rescue Station', 'available', 1, 'simulated'),
('res_002', 'F-8 Rescue Unit Beta', 'rescue_unit', 'water_rescue', 'F-8 Rescue Station', 'available', 1, 'simulated'),
('res_003', 'I-8 Fire Tender 1', 'fire', 'fire_engine', 'I-8 Fire Station', 'available', 1, 'simulated'),
('res_004', 'PIMS Ambulance 1', 'ambulance', 'icu', 'PIMS Hospital', 'available', 1, 'simulated'),
('res_005', 'Emergency Tent Pack A', 'supplies', 'tents', 'G-9 Depot', 'available', 50, 'simulated'),
('res_006', 'Food Relief Packs', 'supplies', 'food_packs', 'G-9 Depot', 'available', 300, 'simulated'),
('res_007', 'Medical Kits', 'supplies', 'medical_kits', 'G-9 Depot', 'available', 20, 'simulated'),
('res_008', 'Rubber Rescue Boats', 'equipment', 'rubber_boats', 'F-8 Rescue Station', 'available', 2, 'simulated');
```

**Download NDMA archived reports (2022 flood) for Tabeen:**
- Go to: https://ndma.gov.pk/situation-reports/
- Download 3-5 PDF situation reports from August 2022 (flood peak)
- Save to: `ingestion/ndma_pdf_ingestor/test_data/`
- Push to repo

---

### MAY 17 — EVENING BLOCK (6pm–10pm)
#### Priority: Backend deployment

```bash
# Install Docker if not installed: https://docs.docker.com/desktop/install/

cd backend

# Build image
docker build -t ciro-backend .

# Submit to Cloud Build and deploy
gcloud builds submit --tag gcr.io/ciro-production/ciro-backend --timeout=15m

gcloud run deploy ciro-backend \
  --image gcr.io/ciro-production/ciro-backend \
  --region asia-south1 \
  --service-account ciro-backend@ciro-production.iam.gserviceaccount.com \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=ciro-production,ENVIRONMENT=production,SUPABASE_URL=[url],SUPABASE_SERVICE_KEY=[key],GOOGLE_CLOUD_PROJECT=ciro-production" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi

# Get URL
BACKEND_URL=$(gcloud run services describe ciro-backend --region asia-south1 --format="value(status.url)")
echo "BACKEND_URL=$BACKEND_URL"

# Verify
curl $BACKEND_URL/health
# Should return {"status":"healthy",...}
```

Update `.env` with `BACKEND_URL`. Push to repo.  
**📣 SEND "✅ BACKEND DEPLOYED" with the URL to Abdul Mannan**

---

### MAY 18 — ALL DAY
#### Priority: Agent deployment + Pub/Sub subscriptions + assist Tabeen

Once Tabeen has agents working locally (she'll tell you), help deploy them:

```bash
# For each agent directory that's ready:
AGENT_NAME=$1
AGENT_DIR="agents/$AGENT_NAME"
cd $AGENT_DIR

gcloud builds submit --tag gcr.io/ciro-production/ciro-$AGENT_NAME --timeout=20m

gcloud run deploy ciro-$AGENT_NAME \
  --image gcr.io/ciro-production/ciro-$AGENT_NAME \
  --region asia-south1 \
  --service-account ciro-backend@ciro-production.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --min-instances=0 \
  --max-instances=2 \
  --memory=1Gi

# Get agent URL and create Pub/Sub subscription
AGENT_URL=$(gcloud run services describe ciro-$AGENT_NAME --region asia-south1 --format="value(status.url)")

gcloud pubsub subscriptions create ${AGENT_NAME}-sub \
  --topic=[TOPIC_NAME] \
  --push-endpoint="${AGENT_URL}/pubsub/push" \
  --push-auth-service-account=ciro-backend@ciro-production.iam.gserviceaccount.com \
  --ack-deadline=300

cd ../../
```

**Also on May 18:**
- Deploy Firebase Hosting for dashboard (Abdul Mannan will give you the `dist/` folder or you run `npm run build`)
- Deploy weather ingestor Cloud Run Job + Cloud Scheduler
- Monitor Cloud Run logs for any errors: `gcloud logging read "resource.type=cloud_run_revision" --limit 50`
- Set up EAS for APK build (Abdul Mannan will need this)

---

### MAY 19 — MORNING
#### Priority: Final checks + demo support

- Verify all Cloud Run services are healthy
- Run one complete end-to-end pipeline trigger via the dashboard "Trigger Demo" button
- Watch logs: `gcloud logging tail "resource.type=cloud_run_revision"`
- Fix any deployment errors
- Help record demo (operate the cloud console side if needed for the video)
- Export agent trace logs from Supabase `audit_log` table → CSV → format for submission

---

# ROLE B: TABEEN
## Data Ingestion + Track 1 Agents + Track 2 Agents

**Your tools:** Python, Claude Code (terminal), Antigravity for agent prompt iteration  
**Wait for:** Ahmar's "✅ ENV FILE READY" before writing any DB code  
**Your output:** All agents deployed to Cloud Run, pipeline running end-to-end

---

### MAY 17 — MORNING BLOCK (9am–1pm)
#### Priority: Scaffold all agents while waiting for credentials

You can start this immediately — the agent Python logic doesn't need real credentials until you test it.

**Set up your environment:**
```bash
cd ciro
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn httpx google-cloud-pubsub supabase \
  sentence-transformers transformers pymupdf feedparser \
  google-generativeai python-dotenv shapely geopy
```

**Build the agent base class first (`agents/base/agent_base.py`):**
```python
import base64, json, logging, os
from fastapi import FastAPI, Request
from google.cloud import pubsub_v1
from datetime import datetime, timezone

app_instance = FastAPI()
log = logging.getLogger(__name__)

class AgentBase:
    def __init__(self, agent_name: str):
        self.name = agent_name
        self.project = os.environ.get("GOOGLE_CLOUD_PROJECT", "ciro-production")
        self.publisher = pubsub_v1.PublisherClient()
    
    def publish(self, topic: str, payload: dict, crisis_id: str):
        topic_path = self.publisher.topic_path(self.project, topic)
        message = {
            "event_id": f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "topic": topic,
            "crisis_id": crisis_id,
            "source_agent": self.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
            "schema_version": "2.0"
        }
        future = self.publisher.publish(topic_path, json.dumps(message).encode())
        log.info(f"[{self.name}] Published to {topic}: {future.result()}")

def make_pubsub_app(agent: AgentBase):
    """Creates a FastAPI app that receives Pub/Sub push messages."""
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "agent": agent.name}
    
    @app.post("/pubsub/push")
    async def handle_push(request: Request):
        envelope = await request.json()
        data = json.loads(base64.b64decode(envelope["message"]["data"]).decode())
        await agent.process(data)
        return {"status": "ok"}
    
    return app
```

**Use Claude Code to build each agent.** In your terminal:
```bash
cd ciro
claude
```

Give Claude Code this context at the start:
```
I'm building CIRO, an emergency management system. 
I need to build Python agent services that run on FastAPI 
and communicate via Google Cloud Pub/Sub.

Rules:
1. Each agent is a FastAPI service with /health and /pubsub/push endpoints
2. All agents inherit from agents/base/agent_base.py
3. Use the EXACT schemas from docs/v2_06_backend_v2.md
4. Gemini is called via google-generativeai package, model="gemini-1.5-flash-002"
5. All Supabase writes use the supabase-py client
6. Agents must handle errors gracefully (never crash on bad input)
7. Write a Dockerfile for each agent
```

**Build agents in this order (fastest to slowest):**

**Agent 2 first** (classification logic — no external APIs needed, easiest to test):
```
Build agents/agent_2_crisis_detection/classify.py

It receives a list of SignalEvent objects.
Implement:
1. haversine distance function
2. cluster_signals() - groups signals within 5km + 45min + same type
3. calculate_confidence() - scoring formula from v2_02_agent_architecture.md §2
4. estimate_severity() - rules by crisis type from v2_02
5. should_escalate_to_track2() - check criteria from v2_01_system_architecture.md §4

On receiving signals.processed event: run clustering, if cluster size >= 2 and 
confidence > 0.7, publish to crisis.detected topic.

Include /pubsub/push endpoint using the AgentBase class.
Include test data: 3 flood signals in G-10 area that should trigger a crisis.
```

**Agent 1 second** (normalization — needs Gemini but can mock it):
```
Build agents/agent_1_signal_ingestion/ingest.py

It receives signals from signals.raw topic.
Implement:
1. gemini_normalize_text() - calls Gemini Flash with the prompt from v2_02 §2
2. is_duplicate() using sentence-transformers paraphrase-multilingual-MiniLM-L12-v2
3. extract_location() if location is missing
4. publish normalized signal to signals.processed

Handle: Urdu text, Roman Urdu, mixed language.
Mock Gemini call with a simple regex fallback if GEMINI_API_KEY is not set (for testing).
```

**Ingestion services (can build these in parallel while agents are running):**
```
Build ingestion/weather_ingestor/main.py

Calls Open-Meteo API for 4 cities: Islamabad (33.6844,73.0479), 
Lahore (31.5204,74.3587), Karachi (24.8607,67.0011), Rawalpindi (33.5973,73.0479)

Every 15 minutes:
- Check precipitation > 25mm/hr OR weathercode in CRISIS_WEATHER_CODES (from v2_03)
- If crisis threshold: publish to signals.raw Pub/Sub topic
- If not: just log (don't publish noise)

Include a main() that runs once (Cloud Run Job style, not infinite loop).
```

---

### MAY 17 — AFTERNOON BLOCK (1pm–6pm)
#### Wait for "✅ ENV FILE READY" then test against real services

Once you have the `.env` file from Ahmar:
```bash
export $(cat backend/.env | xargs)
# Now you can test against real Supabase and Pub/Sub
```

**Test Agent 2 (should be done by now):**
```bash
cd agents/agent_2_crisis_detection
python -m pytest tests/ -v
# Should show: test_three_signals_confirm_crisis PASSED
# Should show: test_single_signal_no_crisis PASSED
```

**Build Agent 3 (Situational Awareness):**
```
Build agents/agent_3_situational_awareness/situational.py

Receives crisis.detected event.
Implement asyncio.gather() to run in parallel:
1. fetch_road_network() - Overpass API query for roads in crisis bbox
2. fetch_nearby_facilities() - query Supabase facilities table by distance
3. estimate_population_at_risk() - use population_density lookup for district

If crisis type is flood: also call UNOSAT API for flood extent.
Identify road closures: roads that intersect the crisis zone circle.

Output: OperationalPicture schema from v2_06 §3.
Publish to ops-picture-ready topic.
POST to backend /webhooks/pubsub/ops-picture-ready
```

**Build Agent 4 (Resource Dispatch):**
```
Build agents/agent_4_resource_dispatch/dispatch.py

Receives ops.picture.ready event.
Implement:
1. calculate_gap() using OCHA_RATES dict from v2_02 §3
2. priority_score() formula from v2_02 §2
3. select_unit() - nearest available unit of required type from Supabase resources table
4. Generate dispatch reasoning text via Gemini (2-3 sentences per order)

Output: DispatchPlan schema. Publish to dispatch-planned. POST to backend.
```

---

### MAY 17 — EVENING BLOCK (6pm–10pm)
#### Build Agent 5 + Agent 6 + social monitor

**Agent 5 (Simulation):**
```
Build agents/agent_5_simulation/simulate.py

Receives dispatch.planned event.
Implement:
1. compute_route() with 3-level fallback: ORS → straight-line haversine
2. simulate_traffic_impact() - before/after state with congestion reduction %
3. generate_emergency_ticket() - auto-increment from Supabase
4. Google Cloud TTS: generate Urdu + English voice alert audio → upload to gs://ciro-assets/alerts/

Output: SimulationResult schema. Publish to simulation-complete.
```

**Agent 6 (Alert Generation):**
```
Build agents/agent_6_dashboard/alert_gen.py

Receives simulation.complete event.
Implement:
1. gemini_generate_alert_text() - bilingual Urdu + English alert
2. calculate_alert_zone() - crisis radius × 1.5
3. identify_safe_routes() - routes from simulation that civilians can use

Output: PublicAlert schema. Publish to alert.broadcast.
```

**Social media monitor:**
```
Build ingestion/social_monitor/main.py

Nitter RSS scraper for CRISIS_SEARCH_TERMS from v2_03 §8
Runs on a 5-minute loop.
Filters: posts from last 10 minutes only.
For each hit: publish to signals.raw Pub/Sub topic.
Source label: "social_nitter"
```

---

### MAY 18 — MORNING BLOCK (9am–1pm)
#### End-to-end test + Track 2 agents

**End-to-end test (do this as a priority):**
```bash
# Inject a test signal directly to Pub/Sub
gcloud pubsub topics publish signals-raw --message='{
  "id": "test_001",
  "source": "social_media",
  "raw_text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
  "location": {"lat": 33.6844, "lng": 73.0479, "district": "G-10", "city": "Islamabad"},
  "signal_type": "flood",
  "timestamp": "2026-05-18T09:00:00Z",
  "source_label": "simulated"
}'

# Watch Supabase signals table for new rows
# Watch backend logs for webhook calls
# Within 90s: Supabase should have crisis, dispatch_orders, public_alerts records
```

**📣 SEND "✅ PIPELINE WORKING" to Abdul Mannan once this works**

**Track 2 Agents:**

Build T2-A1, T2-A2, T2-A3, T2-A4 in this priority order:

```
T2-A2 first (Resource Gap) — pure calculation, no external APIs:
Build agents/track2/t2_a2_resource_gap/gap.py
Uses OCHA_RATES from v2_02. 
Input: population + agency_deployments.
Output: ResourceGap[] with priority rankings.
Test: 10000 people → correct tent/food/medical calculations.

T2-A4 second (Command Intelligence + SITREP):
Build agents/track2/t2_a4_command/command.py
SITREP_PROMPT from v2_02 §3.
Output: sitrep markdown → POST to backend → Ahmar deploys WeasyPrint for PDF.

T2-A1 (Agency Status):
Reads Supabase agencies + agency_deployments tables.
Parses NDMA PDFs from test_data/ using PyMuPDF + Gemini.
Publishes track2.agency_status events.

T2-A3 (Field Coordination):
De-confliction using Shapely geometry (from v2_02 §3).
Coordination message drafting via Gemini.
```

---

### MAY 18 — AFTERNOON + EVENING
#### Antigravity workspace setup + trace logs

While Ahmar deploys your agents:

**Set up Antigravity workspaces:**
1. Open Antigravity Agent Manager
2. Add workspace for each of the 10 agent directories
3. Create `.agy_rules` for each (see v2_03_agentic_workflow_spec.md §2)
4. Test each agent prompt manually against the test scenario
5. Run one complete pipeline with all Antigravity workspaces open (for the demo video)

**Generate trace logs:**
```bash
# After running the full pipeline:
python scripts/export_trace.py  # exports audit_log from Supabase to CIRO_agent_trace.log
```

---

### MAY 19 — MORNING
#### Final tests + demo support

- Run complete pipeline 3 times, verify it's stable
- Make sure all agent trace logs are clean and formatted
- Be available for Abdul Mannan's dashboard demo recording (you'll trigger the pipeline)
- Export all trace logs for submission

---

# ROLE C: ABDUL MANNAN (Team Lead)
## Mobile App + Dashboard + Deployment Oversight + Hardening + Demo

**Your tools:** Claude Code (primary), Claude.ai web Project for design, Expo EAS for builds  
**You start immediately — don't wait for anything except the backend URL for final integration**  
**Your output:** Fully functional mobile app + dashboard. Demo video recorded.**

---

### MAY 17 — MORNING BLOCK (9am–1pm)
#### Priority: Fix the broken app, establish foundation

**Start Claude Code immediately:**
```bash
cd ciro/mobile-app
claude
```

Give this opening context:
```
I'm working on CIRO, a crisis management React Native app.
Stack: Expo SDK 54, RN 0.81.5, TypeScript, React Navigation v6.

Current state: The app is a scaffold. Maps don't render, icons are broken, 
API calls give errors. I need to fix it to production quality.

SESSION RULES (enforce these automatically):
1. `npx expo install` for ANY Expo-related package (never plain npm install)
2. After any package change: run `npx expo-doctor` and fix ALL issues
3. After code changes: run `npx tsc --noEmit` — 0 errors required
4. Never install vulnerable packages (npm audit --audit-level=high must pass)
5. Fix ONE thing at a time, test, then proceed

Start by running: npm audit --audit-level=high
Show me all HIGH and CRITICAL issues.
```

**Fix session 1 (have Claude Code do all of this):**
```
Task 1: Run npm audit. Fix all HIGH/CRITICAL vulnerabilities using npx expo install.
After fixes: run expo-doctor. Show me the clean output.

Task 2: Fix react-native-maps.
The map is not rendering. Check:
- Is GOOGLE_MAPS_API_KEY in android/app/src/main/AndroidManifest.xml?
- Is the MapView import correct for Expo SDK 54?
- Is the initialRegion prop set?
Fix the map in HomeScreen.tsx. Don't change any other logic.

Task 3: Fix icon imports.
Find every broken icon import in the project.
Replace with @expo/vector-icons Feather or MaterialIcons equivalents.
Run tsc --noEmit after. 0 errors.

Task 4: Fix API calls.
The backend API calls are giving errors. Look at src/lib/api.ts.
The backend URL is in EXPO_PUBLIC_BACKEND_URL env var.
For now, set a fallback: if EXPO_PUBLIC_BACKEND_URL is undefined, use 'http://localhost:8000'
Test that GET /api/v2/crisis/active no longer throws.
```

---

### MAY 17 — AFTERNOON BLOCK (1pm–6pm)
#### Build the design foundation + core components

**Open Claude.ai web → your "CIRO Mobile App" Project**

Add the Naval Command color palette to your Project Instructions from `v2_04_uiux_spec.md §2 Option A`.

**Build theme files (prompt for each):**

```
Build src/theme/colors.ts

Naval Command palette (exact values from my Project Instructions).
Export: Colors object, getSeverityColor(severity: 1|2|3|4|5) function.
TypeScript. No default export — named exports only.
```

```
Build src/theme/typography.ts

Font scale from my Project Instructions.
Export: Typography object with all size/weight combinations.
Include urduStyle: StyleSheet object for Urdu text (rtl, noto nastaliq, lineHeight 1.8)
```

```
Build src/components/ui/SeverityBadge.tsx

Props: severity (1-5), size? ('sm' | 'md')
Uses getSeverityColor from theme.
Pill shape, uppercase text (LOW/MINOR/MODERATE/HIGH/CRITICAL).
StyleSheet only, no inline styles.
TypeScript.
```

```
Build src/components/ui/BilingualText.tsx

Props: english (string), urdu (string), showUrdu? (boolean, default false)
Renders English text normally.
If showUrdu: renders Urdu below in urduStyle from typography.
Has toggle chevron button to expand/collapse Urdu.
```

**Switch to Claude Code for component integration:**
```
I just generated these component files. Integrate them:
- src/theme/colors.ts
- src/theme/typography.ts  
- src/components/ui/SeverityBadge.tsx
- src/components/ui/BilingualText.tsx

1. Make sure the imports work correctly throughout the app
2. Run tsc --noEmit — fix any type errors
3. Don't change any screen logic yet
```

---

### MAY 17 — EVENING BLOCK (6pm–midnight)
#### Build CrisisCard + HomeScreen + CrisisDetail

**In Claude.ai web Project, build CrisisCard:**
```
Build src/components/crisis/CrisisCard.tsx

Spec (from my UI spec §7.1):
- Container: 4px left border colored by severity, border-radius 12px
- Background: surface color (#132743)
- Header row: [CrisisType icon 20px] [title text-md] [SeverityBadge]
- Second row: location text-sm secondary, time-ago text-xs muted
- Status row: stage progress (DETECTED→ANALYZED→DISPATCHED→SIMULATED→RESOLVED)
  Each stage: 20% width pill. Filled = active. Current = pulse animation.
- Active state: box-shadow glow using severity color at 20% opacity
- CrisisCardSkeleton variant: same dimensions, animated shimmer

CrisisEvent type:
{
  id: string
  type: 'urban_flooding' | 'heatwave' | 'accident' | 'road_blockage' | 'infrastructure_failure'
  type_label: string
  location_name: string
  severity: 1 | 2 | 3 | 4 | 5
  confidence_label: 'low' | 'medium' | 'high'
  status: 'monitoring' | 'detected' | 'analyzed' | 'dispatched' | 'simulated' | 'resolved'
  detected_at: string
  lat: number
  lng: number
  affected_radius_km: number
  alert_audio_url?: string
}

Props: crisis: CrisisEvent, onPress?: () => void, loading?: boolean
```

Paste the generated code into your project, then switch to Claude Code:
```
I added src/components/crisis/CrisisCard.tsx
Integrate it into HomeScreen.tsx:
1. Replace the existing placeholder list with CrisisCard components
2. Use the useCrisisData hook (or create it if it doesn't exist)
   - GET /api/v2/crisis/active
   - React Query, refetch every 30 seconds
   - Returns CrisisEvent[]
3. Show CrisisCardSkeleton while loading (show 3 skeletons)
4. Run tsc --noEmit after integration
```

**Build HomeScreen map:**
```
Fix the HomeScreen map to show:
1. Full-screen react-native-maps MapView, initial region: Islamabad
2. For each active crisis: Circle overlay (crisis.lat, crisis.lng, crisis.affected_radius_km * 1000 meters)
   Circle fill: crisis severity color at 20% opacity
   Circle stroke: severity color at 60%
3. User location pin (request permission with expo-location)
4. Tap on crisis circle → navigate to CrisisDetail screen with crisis.id

Bottom sheet (use @gorhom/bottom-sheet if installed, otherwise simple Animated.View):
- Default snap: 240px from bottom
- Contains horizontally scrolling CrisisCard list
```

---

### MAY 18 — MORNING BLOCK (9am–1pm)
#### CrisisDetail + AlertsScreen + SafeRoutes

**CrisisDetail screen (Claude.ai web → paste → Claude Code integrate):**

```
Build src/screens/CrisisDetailScreen.tsx

Full spec from v2_04_uiux_spec.md §8.3.
Key features:
1. Full-screen map showing: crisis zone, dispatch unit markers, route polylines, road closures
2. Sliding bottom sheet starting at 40% screen height
3. Stage progress bar (5 stages, animated)
4. Confidence block: score + reasoning text from Agent 2
5. BilingualText component for agent reasoning
6. Dispatch orders list: [unit icon] Unit Name → Destination [ETA pill]
7. Public guidance section (numbered list, bilingual)
8. Voice alert button (large, full-width, 56px) - shown only if crisis.alert_audio_url exists
   Uses playVoiceAlert() from src/services/voiceAlert.ts
9. Floating status chip: "● RESCUE EN ROUTE" with breathing animation

Route from params: { crisisId: string }
Fetches: GET /api/v2/crisis/{id}
WebSocket: ws://[backend]/ws/crisis/{id} for live updates
```

**Voice alert service (Claude Code):**
```
Build src/services/voiceAlert.ts

Uses expo-av and expo-file-system.
Functions:
- playVoiceAlert(audioUrl: string, crisisId: string): Promise<void>
  Downloads to cache if not cached. Plays via Audio.Sound.
- preCacheAlert(audioUrl: string, crisisId: string): Promise<void>
  Downloads silently for offline use.
- stopAlert(): Promise<void>

Handle all errors gracefully - never crash.
Write Vitest tests in __tests__/voiceAlert.test.ts
```

**Location-based alert triggering (Claude Code):**
```
Build src/hooks/useLocationAlerts.ts

Uses expo-location (already installed).
Every 30 seconds: check if user is within 1.5× radius of any active crisis.
If yes + crisis.severity >= 4 + crisis.alert_audio_url exists:
  Call preCacheAlert() immediately
  If user hasn't heard this alert in last 30 min: call playVoiceAlert()
Track played alerts in AsyncStorage to avoid replaying.
```

---

### MAY 18 — AFTERNOON BLOCK (1pm–6pm)
#### AlertsScreen + SafeRoutes + ReportIncident + offline

**AlertsScreen, SafeRoutes, ReportIncident** — build all three with Claude.ai web, integrate with Claude Code:

```
Alerts screen filter pills, severity sections, tap → CrisisDetail
Safe Routes: map + route cards with ETA, "Open in Google Maps" deep link
Report Incident: chip multi-select, text input (280 char), location, photo upload
  Submit: POST /api/v2/reports with FormData
  Queue in AsyncStorage if offline, send when reconnected
```

**Offline cache (Claude Code):**
```
Build src/services/offlineCache.ts

On every successful API response: cache to AsyncStorage with timestamp.
On API failure: return cached data if < 1 hour old.
Functions:
- getCachedCrises(): CrisisEvent[] | null
- setCachedCrises(crises: CrisisEvent[]): void
- isStale(timestamp: string, maxAgeMinutes: number): boolean

Update useCrisisData hook to use offlineCache as fallback.
Add isOffline state to the hook.
Show "● OFFLINE — cached N min ago" banner in HomeScreen when isOffline.
```

**ProfileScreen (quick, use Claude Code):**
```
Build ProfileScreen.tsx
Alert radius preference: segmented control (2km/5km/10km/City-wide)
Voice alert toggle with language selector (Urdu/English/Both)
Store preferences in AsyncStorage.
Read preferences in useLocationAlerts hook.
```

---

### MAY 18 — EVENING BLOCK (6pm–11pm)
#### Dashboard + Android build

**Switch to web-dashboard. Claude Code:**
```
cd ciro/web-dashboard
claude

Opening context:
I'm building a React 18 + Vite + Tailwind + TypeScript + Leaflet.js dashboard.
The Naval Command theme CSS variables are in src/theme/index.css.

Rules:
1. TypeScript strict mode — 0 type errors
2. Tailwind for layout, CSS variables for colors (not hardcoded hex)
3. React Query for data, Zustand for UI state
4. Every component handles loading/error/empty states
5. Virtual scroll for agent trace (can have 10K+ items)
```

**Dashboard tasks for Claude Code:**
```
Task 1: Fix/create Header component with:
- CIRO logo, Track 1/2 tab toggle
- Active crisis count badge
- WebSocket status pill: LIVE/CONNECTING/OFFLINE (with polling useWebSocket hook)
- Colors from CSS variables

Task 2: Left panel CrisisList:
- Uses GET /api/v2/crisis with React Query
- Renders CrisisCard components (web version matching mobile spec)
- Click → selects crisis, loads in bottom panel and centers map
- "Trigger Demo" button at bottom: POST /api/v2/debug/inject-scenario

Task 3: Leaflet map (MapView component):
- Leaflet.js, tiles: OpenStreetMap
- For each active crisis: Circle with severity color, 
  Tooltip showing location + severity
- Road closure: Polyline dashed red
- Dispatch routes: Polyline blue with arrowhead
- Unit markers: custom icon by unit type
- Before/After traffic toggle: switches between two map states

Task 4: Bottom panel tabs (each as separate component):
- AgentTraceTab: windowed list (react-window), color-coded rows (from v2_04 §7.4)
  Auto-scroll, pause on user scroll, filter buttons
- DispatchOrdersTab: table with status badges
- ResourceStatusTab: available vs deployed sections
- SITREPTab: react-markdown renderer + Download PDF button
```

**Once dashboard is built — Android build:**
```bash
# In Claude Code:
cd android
./gradlew clean
./gradlew assembleDebug
```

If build fails, give Claude Code the full error output with the rule:
```
Fix this Gradle build error. Only modify build configuration files. 
Don't touch JavaScript/TypeScript source. Run assembleDebug after fix.
```

---

### MAY 19 — ALL DAY
#### Demo recording + submission

**Morning (8am–12pm): Final integration**

When Ahmar sends "✅ BACKEND DEPLOYED":
```bash
# Update backend URL everywhere
echo "EXPO_PUBLIC_BACKEND_URL=https://ciro-backend-xxx.a.run.app" > mobile-app/.env.production
echo "VITE_BACKEND_URL=https://ciro-backend-xxx.a.run.app" > web-dashboard/.env.production

# Rebuild APK with production URL
cd mobile-app && eas build --profile production --platform android --non-interactive
```

When Tabeen sends "✅ PIPELINE WORKING":
- Test the full pipeline via the dashboard "Trigger Demo" button
- Verify: crisis appears on map, route animates, alert generated, mobile gets push

**Demo recording (12pm–5pm):**

Structure the demo video (3-5 min):
1. (30s) Open Antigravity Agent Manager — show 6+ workspaces with `.agy_rules`
2. (30s) Show the web dashboard: empty map of Islamabad, "All clear" state
3. (60s) Trigger demo from dashboard:
   - Show Agent 1 workspace processing social posts
   - Show Agent 2 confidence scoring in trace tab
   - Crisis zone appears on map
4. (60s) Track 1 in action:
   - Route animation on map
   - Before/After traffic toggle
   - SITREP tab populating
5. (30s) Mobile app:
   - Crisis alert card
   - Voice alert playing
   - Safe routes screen
6. (30s) Track 2 panel: agency grid, gap analysis, SITREP

**Submission docs (5pm–10pm):**

Use Claude.ai web to generate the README:
```
Generate the README.md for CIRO v2 crisis management system.
Use the structure from docs/v2_09_deployment_guide.md §8.
Fill in all sections based on what we actually built:
[paste relevant sections from v2_00, v2_01, v2_03]
```

Final checklist for submission:
- [ ] Demo video 3-5 min (uploaded to YouTube/Drive, link ready)
- [ ] Antigravity usage video 2-3 min
- [ ] `CIRO_agent_trace.log` (exported from Supabase audit_log)
- [ ] README.md (with all required sections)
- [ ] GitHub repo link (with all code)
- [ ] Mobile APK link (EAS build URL)
- [ ] Dashboard URL (Firebase Hosting)

---

## Dependency Map (When Each Person Can Start What)

```
MAY 17 9am:
  Ahmar starts:  Cloud setup → (no dependencies)
  Tabeen starts: Agent scaffolding + Python logic → (no DB needed yet)
  Abdul starts:  npm audit fix + map fix → (no backend needed)

MAY 17 ~1pm (Ahmar: "✅ ENV FILE READY"):
  Tabeen: tests agents against real Supabase
  Abdul: updates backend URL in local env

MAY 17 ~6pm:
  Ahmar: deploys backend
  Tabeen: builds simulation + alert agents
  Abdul: builds CrisisDetail + voice alerts

MAY 18 morning:
  Ahmar: deploys agents as Tabeen finishes them
  Tabeen: Track 2 agents + end-to-end test
  Abdul: remaining screens + dashboard

MAY 18 afternoon ("✅ PIPELINE WORKING" from Tabeen):
  Abdul: integration test against real pipeline
  Tabeen: Antigravity workspace setup + trace logs

MAY 19:
  Everyone: final integration → demo video → submission
```
