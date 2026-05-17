# CIRO v2 — Agent Architecture & Orchestration
## Production-Grade, Event-Driven, Both Tracks

---

## 1. Agent Deployment Model

Every agent is a **Cloud Run service** — a containerized Python service that:
- Subscribes to one or more Pub/Sub topics (via push subscription → HTTP endpoint)
- Has its own stateless logic
- Calls Vertex AI Gemini Flash for reasoning tasks
- Publishes results back to Pub/Sub
- POSTs state updates to the FastAPI backend

This replaces the script queue. The backend no longer triggers agents — Pub/Sub events do.

### Agent Service Template

```python
# agents/base/agent_base.py
from fastapi import FastAPI, Request
from google.cloud import pubsub_v1
import json, logging, os

app = FastAPI()
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]

def publish_event(topic: str, payload: dict, crisis_id: str, agent_name: str):
    topic_path = publisher.topic_path(PROJECT_ID, topic)
    message = {
        "event_id": generate_id(),
        "topic": topic,
        "crisis_id": crisis_id,
        "source_agent": agent_name,
        "timestamp": now_iso(),
        "payload": payload,
        "schema_version": "2.0"
    }
    publisher.publish(topic_path, json.dumps(message).encode())

@app.post("/pubsub/push")
async def handle_pubsub_push(request: Request):
    """Receives Pub/Sub push messages."""
    envelope = await request.json()
    message_data = json.loads(
        base64.b64decode(envelope["message"]["data"]).decode()
    )
    await process_message(message_data)
    return {"status": "ok"}
```

---

## 2. Track 1 Agents — Detailed Specification

### Agent 1 — Signal Normalization Service

**Purpose:** Continuously ingests raw signals from all sources, normalizes to standard schema.  
**Trigger:** `signals.raw` Pub/Sub topic  
**Runs:** Continuously (Cloud Run with min_instances=1 during active crisis)

**Inputs consumed:**
- Social media monitor service (Pub/Sub push)
- Weather ingestion service (scheduled every 15 min)
- Traffic data service (scheduled every 5 min)
- Citizen reports (mobile app → backend → Pub/Sub)

**Logic:**
```python
async def normalize_signal(raw_signal: dict) -> SignalEvent:
    if raw_signal["source"] == "social_media":
        # Urdu/English NLP via Gemini Flash
        normalized = await gemini_normalize_text(raw_signal["text"])
    elif raw_signal["source"] == "weather":
        normalized = parse_weather_signal(raw_signal)
    elif raw_signal["source"] == "traffic":
        normalized = parse_traffic_signal(raw_signal)
    elif raw_signal["source"] == "citizen_report":
        normalized = await gemini_normalize_text(raw_signal["text"])
    
    # Location extraction
    if not normalized.get("location"):
        normalized["location"] = await gemini_extract_location(raw_signal["text"])
    
    # Deduplication check
    if await is_duplicate(normalized, window_minutes=30):
        return None  # Discard
    
    await publish_event("signals.processed", normalized, ...)
    return normalized
```

**Gemini prompt for text normalization:**
```
You are normalizing Pakistani emergency reports. The text may be in Urdu, English, or mixed (Roman Urdu).

Input text: "{text}"

Extract and return JSON only:
{
  "normalized_text": "English translation/summary",
  "location": {"area": "district/sector", "city": "city name", "confidence": 0.0-1.0},
  "crisis_indicators": ["flooding", "road_blocked", "stranded_vehicles", etc.],
  "severity_keywords": ["severe", "minor", "worsening", etc.],
  "is_firsthand": true/false (is the person reporting direct observation?),
  "timestamp_mentioned": "if a time was mentioned",
  "source_reliability": "eyewitness | secondhand | unknown"
}

Return null if the text contains no crisis-relevant information.
```

---

### Agent 2 — Crisis Detection & Classification Service

**Purpose:** Clusters related signals, detects crisis events with confidence scoring.  
**Trigger:** `signals.processed` Pub/Sub topic  
**Logic:** Spatial-temporal clustering + Gemini reasoning

**Clustering algorithm:**
```python
def cluster_signals(signals: List[SignalEvent]) -> List[SignalCluster]:
    """
    Groups signals that are:
    - Within 5km radius of each other
    - Of the same crisis type (or compatible types)
    - Within 45-minute window
    """
    clusters = []
    for signal in signals:
        placed = False
        for cluster in clusters:
            if (
                haversine(signal.lat, signal.lng, cluster.center_lat, cluster.center_lng) <= 5.0
                and signal_types_compatible(signal.signal_type, cluster.dominant_type)
                and abs((signal.timestamp - cluster.latest_timestamp).seconds) <= 2700
            ):
                cluster.add(signal)
                placed = True
                break
        if not placed:
            clusters.append(SignalCluster(seed=signal))
    return clusters
```

**Confidence scoring:**
```python
def calculate_confidence(cluster: SignalCluster) -> float:
    score = 0.0
    
    # Source diversity (0.0 - 0.4)
    sources = set(s.source for s in cluster.signals)
    score += min(len(sources) * 0.13, 0.4)
    
    # Corroboration count (0.0 - 0.3)
    score += min(len(cluster.signals) * 0.06, 0.3)
    
    # High-reliability sources (0.0 - 0.2)
    if any(s.source in ["weather_api", "traffic_api", "official_report"] for s in cluster.signals):
        score += 0.2
    
    # Firsthand reports (0.0 - 0.1)
    firsthand = sum(1 for s in cluster.signals if s.is_firsthand)
    score += min(firsthand * 0.05, 0.1)
    
    return round(score, 3)
```

**Severity estimation:**
```python
SEVERITY_RULES = {
    "urban_flooding": lambda c: min(5, 1 + c.signal_count//2 + (2 if c.has_weather_corroboration else 0)),
    "road_blockage": lambda c: min(5, 1 + (2 if c.affects_highway else 0) + c.signal_count//3),
    "accident": lambda c: min(5, 2 + (1 if c.has_injury_keywords else 0) + (1 if c.affects_multiple_vehicles else 0)),
    "heatwave": lambda c: min(5, 1 + (2 if c.temp_above_45 else 0) + (1 if c.duration_days > 2 else 0)),
}
```

**Escalation check (Track 2):**
After confirming a crisis, Agent 2 checks escalation criteria and publishes to `crisis.major` if met.

---

### Agent 3 — Situational Awareness Service

**Purpose:** Builds operational picture for confirmed crisis zone.  
**Trigger:** `crisis.detected` Pub/Sub topic  
**Parallelism:** Runs 3 sub-tasks concurrently

```python
async def build_operational_picture(crisis: CrisisEvent):
    # Run all three concurrently
    road_data, facility_data, population_data = await asyncio.gather(
        fetch_road_network(crisis.lat, crisis.lng, crisis.radius_km),
        fetch_nearby_facilities(crisis.lat, crisis.lng, radius_km=10),
        estimate_population_at_risk(crisis.lat, crisis.lng, crisis.radius_km)
    )
    
    # Identify road closures from traffic + crisis location overlap
    road_closures = identify_closures(road_data, crisis)
    
    # Check for UNOSAT flood extent if flood type
    flood_extent = None
    if crisis.type in ["urban_flooding", "flash_flood", "riverine_flood"]:
        flood_extent = await fetch_unosat_extent(crisis.lat, crisis.lng)
    
    ops_picture = OperationalPicture(
        crisis_id=crisis.id,
        road_closures=road_closures,
        nearby_facilities=facility_data,
        population_at_risk=population_data,
        flood_extent=flood_extent,
        data_gaps=identify_gaps(road_data, facility_data)
    )
    
    await publish_event("ops.picture.ready", ops_picture.dict(), crisis.id, "agent_3")
```

---

### Agent 4 — Resource Dispatch Service

**Purpose:** Calculates resource needs and generates dispatch orders.  
**Trigger:** `ops.picture.ready`

**Priority ranking formula:**
```python
def priority_score(zone: AffectedZone, ops: OperationalPicture) -> float:
    severity_weight = zone.severity / 5.0
    access_weight = 1.0 / (1.0 + ops.nearest_road_closure_km)
    population_weight = math.log10(max(ops.population_at_risk, 10)) / 5.0
    time_weight = 1.0 + (zone.duration_minutes / 120)  # Increases urgency over time
    
    return severity_weight * access_weight * population_weight * time_weight
```

**Dispatch reasoning (Gemini):**
```
Generate a dispatch order reasoning explanation for this assignment:

Unit: {unit_name} ({unit_type}) at {distance_km}km
Crisis: {crisis_type} severity {severity}/5, {population_at_risk} at risk
Decision: Dispatch via {route_via}

Write 2-3 sentences explaining:
1. Why this unit was selected (nearest + correct type)
2. Why this route was chosen (alternatives and why rejected)
3. Any constraints or caveats the dispatch team should know

Be direct and factual. This will be read by an emergency coordinator.
```

---

### Agent 5 — Route & Simulation Service

**Purpose:** Computes optimal routes, simulates outcomes.  
**Trigger:** `dispatch.planned`

**Routing with fallback chain:**
```python
async def compute_route(order: DispatchOrder, closures: List[RoadClosure]) -> Route:
    # Attempt 1: OpenRouteService with avoidance
    try:
        route = await ors_route(order.origin, order.destination, avoid=closures)
        if route: return route
    except Exception as e:
        log_warning(f"ORS failed: {e}, trying fallback")
    
    # Attempt 2: Google Directions API
    try:
        route = await google_directions(order.origin, order.destination)
        if route: return route
    except Exception as e:
        log_warning(f"Google Directions failed: {e}, using straight-line")
    
    # Attempt 3: Straight-line with estimated time
    return Route(
        waypoints=[order.origin, order.destination],
        distance_km=haversine(*order.origin, *order.destination),
        duration_min=haversine(*order.origin, *order.destination) / 0.5,
        fallback=True,
        fallback_reason="All routing APIs unavailable"
    )
```

**Traffic simulation:**
```python
def simulate_traffic_impact(routes: List[Route], crisis: CrisisEvent) -> TrafficSimulation:
    before_state = get_current_traffic_state(crisis.affected_area)
    
    # Simulate: remove blocked roads, add diverted flow
    after_state = before_state.copy()
    for route in routes:
        after_state.add_flow(route.waypoints, route.vehicle_type)
    
    for closure in crisis.road_closures:
        after_state.block(closure.road_segment)
        after_state.divert_to(closure.alternate_route)
    
    congestion_before = calculate_congestion_index(before_state)
    congestion_after = calculate_congestion_index(after_state)
    
    return TrafficSimulation(
        before=before_state,
        after=after_state,
        reduction_pct=round((congestion_before - congestion_after) / congestion_before * 100),
        civilian_alert_routes=identify_safe_alternatives(after_state)
    )
```

---

### Agent 6 — Alert Generation Service

**Purpose:** Generates public alerts, push notifications, and civilian guidance.  
**Trigger:** `simulation.complete`

**Alert generation:**
```python
async def generate_public_alert(crisis: CrisisEvent, simulation: TrafficSimulation) -> PublicAlert:
    # Gemini generates alert text in Urdu + English
    alert_text = await gemini_generate_alert(crisis, simulation)
    
    # Identify affected civilian zones (expand crisis radius by 1.5x for alert)
    alert_zone = crisis.affected_zone.buffer(crisis.affected_radius_km * 1.5)
    
    # Generate voice alert audio file
    audio_url = await generate_voice_alert(alert_text.urdu, alert_text.english)
    
    alert = PublicAlert(
        crisis_id=crisis.id,
        severity=crisis.severity,
        affected_zone=alert_zone,
        text_urdu=alert_text.urdu,
        text_english=alert_text.english,
        audio_url=audio_url,
        safe_routes=simulation.civilian_alert_routes,
        do_not_use=crisis.blocked_roads,
        generated_at=now_iso()
    )
    
    await publish_event("alert.broadcast", alert.dict(), crisis.id, "agent_6")
    return alert
```

**Voice alert generation:**
```python
async def generate_voice_alert(urdu_text: str, english_text: str) -> str:
    """
    Uses Google Cloud Text-to-Speech to generate voice alert.
    Stores in Cloud Storage. Returns public URL.
    Free tier: 1M characters/month for standard voices.
    """
    from google.cloud import texttospeech, storage
    
    client = texttospeech.TextToSpeechClient()
    
    # Urdu voice (WaveNet ur-PK)
    synthesis_input = texttospeech.SynthesisInput(text=urdu_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ur-PK",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    # Upload to Cloud Storage
    filename = f"alerts/{crisis_id}_{timestamp}.mp3"
    blob = storage_bucket.blob(filename)
    blob.upload_from_string(response.audio_content, content_type="audio/mpeg")
    blob.make_public()
    
    return blob.public_url
```

---

## 3. Track 2 Agents — Detailed Specification

### T2-A1: Agency Status Agent

**Purpose:** Maintains real-time picture of all agency capacities.  
**Data sources:** Supabase `agencies` table (operator-updated) + ReliefWeb API + NDMA PDF parsing

**NDMA PDF parsing:**
```python
async def parse_ndma_sitrep(pdf_url: str) -> NDMAReport:
    """
    Downloads and parses NDMA situation reports.
    Uses PyMuPDF for extraction + Gemini for structuring.
    """
    import fitz  # PyMuPDF
    
    doc = fitz.open(stream=await download_pdf(pdf_url), filetype="pdf")
    full_text = "\n".join(page.get_text() for page in doc)
    
    # Gemini structures the unstructured PDF text
    structured = await gemini_structure_ndma_report(full_text)
    
    return NDMAReport(
        date=structured["date"],
        districts_affected=structured["districts"],
        resources_deployed=structured["resources"],
        population_affected=structured["population"],
        source_url=pdf_url
    )
```

### T2-A2: Resource Gap Agent

**OCHA standard consumption rates (hardcoded, OCHA Sphere Standards):**
```python
OCHA_RATES = {
    "tents": 1 / 5,           # 1 tent per 5 people
    "food_packs": 3,           # 3 packs per person per day
    "water_liters": 15,        # 15L per person per day
    "medical_kits": 1 / 50,   # 1 kit per 50 people
    "water_rescue_units": 1 / 500,  # 1 unit per 500 at risk
    "latrines": 1 / 20,       # 1 per 20 people
}

def calculate_gap(population: int, deployed: dict, days: float = 1) -> dict:
    required = {
        item: round(population * rate * days)
        for item, rate in OCHA_RATES.items()
    }
    gaps = {
        item: max(0, required[item] - deployed.get(item, 0))
        for item in required
    }
    return {"required": required, "deployed": deployed, "gaps": gaps}
```

### T2-A3: Field Coordination Agent

**De-confliction logic:**
```python
def deconflict_coverage(agency_deployments: List[AgencyDeployment]) -> DeconflictMap:
    """
    Identifies: overlapping coverage areas (wasteful) and uncovered gaps (dangerous).
    """
    coverage_polygons = {
        dep.agency_id: dep.coverage_polygon 
        for dep in agency_deployments
    }
    
    overlaps = []
    for a, b in combinations(coverage_polygons.keys(), 2):
        intersection = coverage_polygons[a].intersection(coverage_polygons[b])
        if not intersection.is_empty:
            overlaps.append(CoverageOverlap(agency_a=a, agency_b=b, area=intersection))
    
    union = unary_union(list(coverage_polygons.values()))
    crisis_zone = get_crisis_zone()
    uncovered = crisis_zone.difference(union)
    
    return DeconflictMap(overlaps=overlaps, uncovered_areas=uncovered)
```

### T2-A4: Command Intelligence Agent

**SITREP generation (Gemini Flash):**
```python
SITREP_PROMPT = """
You are generating an official Situation Report (SITREP) for the National Disaster Management Authority of Pakistan.

Crisis Data:
{crisis_summary}

Agency Status:
{agency_summary}

Resource Gaps:
{gap_summary}

Actions Taken:
{actions_summary}

Generate a formal SITREP in this exact structure. Be precise, use numbers, avoid vague language.
Use active voice. This will be read by NDMA commissioners and military commanders.

SITUATION REPORT — NDMA
Date/Time: {datetime}
Crisis Reference: {crisis_id}
Prepared by: CIRO Automated Intelligence System
Verified by: [OPERATOR TO COMPLETE]

1. EXECUTIVE SUMMARY (3 sentences max)
2. AFFECTED AREA AND POPULATION
3. CURRENT SITUATION (factual, sourced)
4. RESPONSE OPERATIONS
   a. Government agencies
   b. Military assets
   c. NGO/INGO presence
5. RESOURCE STATUS (table format)
6. CRITICAL GAPS AND REQUIREMENTS
7. RECOMMENDED ACTIONS (prioritized)
8. NEXT UPDATE: [30/60/120 min — choose based on severity]
9. CONTACT: [operator fields]

Return as structured markdown. No preamble. No commentary outside the SITREP.
"""
```

---

## 4. Models and Data Sources

### No Custom Model Training Required

All AI tasks are handled by Gemini Flash (multilingual, handles Urdu natively). No fine-tuning needed. This saves compute cost and training time.

**Where Gemini Flash is used:**
- Text normalization (Urdu → structured JSON)
- Location extraction from text
- Confidence reasoning explanation
- Dispatch order reasoning
- Alert text generation (bilingual)
- NDMA PDF structuring
- SITREP generation

### HuggingFace Models (download once, run as Cloud Run service)

These are used for non-LLM classification tasks where Gemini calls would be expensive at scale:

| Model | Purpose | Download |
|---|---|---|
| `bert-base-multilingual-cased` | Crisis text classification (fast pre-filter before Gemini) | https://huggingface.co/bert-base-multilingual-cased |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Signal deduplication (semantic similarity) | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |

**Usage:** These run locally in the Cloud Run container, not via API. Downloaded at container build time.

```dockerfile
# In agents/agent_1_signal_ingestion/Dockerfile
RUN pip install sentence-transformers transformers torch --no-cache-dir
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

The deduplication model prevents flooding the pipeline with 50 posts about the same event:
```python
from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

async def is_duplicate(new_signal: SignalEvent, window_minutes=30) -> bool:
    recent = await get_recent_signals(new_signal.location, window_minutes)
    if not recent:
        return False
    
    new_embedding = model.encode(new_signal.normalized_text)
    recent_embeddings = model.encode([s.normalized_text for s in recent])
    
    similarities = util.cos_sim(new_embedding, recent_embeddings)[0]
    return float(similarities.max()) > 0.85  # 85% semantic similarity = duplicate
```

---

## 5. Agent Health Monitoring

Each agent exposes a `/health` endpoint for Cloud Run health checks:

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": AGENT_NAME,
        "last_processed": last_processed_timestamp,
        "queue_depth": await get_subscription_backlog(),
        "gemini_available": await check_gemini_api()
    }
```

Backend aggregates health checks every 60 seconds and surfaces in the command dashboard.

---

## 6. Antigravity Workspaces (v2 Role)

In v2, Antigravity is used for:
1. **Development**: Designing and iterating agent prompts and logic
2. **Testing**: Running agents manually against test datasets before deployment
3. **Monitoring during demo**: All 6 Track 1 + 4 Track 2 agent workspaces visible in Agent Manager

The deployed Cloud Run services run the finalized code independently. Antigravity is not a runtime dependency in production.
