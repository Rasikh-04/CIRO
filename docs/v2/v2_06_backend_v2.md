# CIRO v2 — Backend Design
## Production FastAPI + Supabase + Pub/Sub

---

## 1. What the Backend Does in v2

The backend in v2 is smaller but more important than in v1. It no longer runs agents. It:

1. **Receives agent outputs** via Pub/Sub push subscriptions (webhook endpoints)
2. **Manages crisis state machine** (enforces valid transitions, logs to audit table)
3. **Serves REST API** to frontend (dashboard, mobile app)
4. **Relays real-time updates** via WebSocket and Supabase realtime
5. **Validates and authenticates** operator actions (human-in-the-loop)
6. **Serves as the ingestion relay** for citizen reports (mobile → Pub/Sub)

---

## 2. Directory Structure v2

```
backend/
├── main.py
├── requirements.txt
├── Dockerfile
├── .env
├── app/
│   ├── api/
│   │   ├── agent_webhooks.py    ← Pub/Sub push endpoints (all agent outputs)
│   │   ├── crisis.py            ← Crisis REST API
│   │   ├── resources.py         ← Resource/inventory API
│   │   ├── alerts.py            ← Public alert API
│   │   ├── reports.py           ← Citizen reports → Pub/Sub relay
│   │   ├── operators.py         ← Human-in-the-loop actions
│   │   └── track2.py            ← Multi-agency coordination API
│   ├── core/
│   │   ├── state_machine.py     ← Crisis lifecycle transitions
│   │   ├── audit.py             ← Immutable audit log
│   │   ├── pubsub.py            ← Pub/Sub publisher client
│   │   └── auth.py              ← JWT for operator dashboard
│   ├── models/                  ← Pydantic schemas (all canonical)
│   │   ├── signals.py
│   │   ├── crisis.py
│   │   ├── track2.py
│   │   └── events.py
│   ├── db/
│   │   ├── supabase.py          ← Supabase client init
│   │   └── queries.py           ← All DB queries (no raw SQL in endpoints)
│   └── ws/
│       └── manager.py           ← WebSocket connection manager
└── tests/
    ├── test_state_machine.py
    ├── test_agent_webhooks.py
    └── test_crisis_api.py
```

---

## 3. Supabase Schema (Complete v2)

```sql
-- ============================================================
-- TRACK 1: URBAN CRISIS INTELLIGENCE
-- ============================================================

CREATE TABLE signals (
    id              VARCHAR(60) PRIMARY KEY,
    source          VARCHAR(30) NOT NULL,
    raw_text        TEXT,
    normalized      TEXT,
    signal_type     VARCHAR(50),
    location        GEOGRAPHY(POINT, 4326),
    district        VARCHAR(100),
    city            VARCHAR(100),
    confidence      FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    is_firsthand    BOOLEAN DEFAULT false,
    source_label    VARCHAR(20) DEFAULT 'unknown',
    is_duplicate    BOOLEAN DEFAULT false,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    crisis_id       VARCHAR(60) REFERENCES crises(id)
);

CREATE TABLE crises (
    id                  VARCHAR(60) PRIMARY KEY,
    type                VARCHAR(50) NOT NULL,
    location            GEOGRAPHY(POINT, 4326),
    location_name       VARCHAR(200),
    affected_radius_km  FLOAT NOT NULL DEFAULT 2.5,
    severity            INTEGER CHECK (severity BETWEEN 1 AND 5),
    confidence_score    FLOAT,
    confidence_label    VARCHAR(10),
    reasoning           TEXT,
    status              VARCHAR(30) NOT NULL DEFAULT 'monitoring',
    track               INTEGER DEFAULT 1,
    track2_activated    BOOLEAN DEFAULT false,
    detected_at         TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

CREATE TABLE operational_pictures (
    id                  SERIAL PRIMARY KEY,
    crisis_id           VARCHAR(60) REFERENCES crises(id),
    road_closures       JSONB,
    nearby_facilities   JSONB,
    flood_extent        GEOMETRY(POLYGON, 4326),
    population_at_risk  INTEGER,
    data_gaps           JSONB,
    generated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE dispatch_orders (
    id                  VARCHAR(60) PRIMARY KEY,
    crisis_id           VARCHAR(60) REFERENCES crises(id),
    unit_id             VARCHAR(60),
    unit_name           VARCHAR(100),
    unit_type           VARCHAR(50),
    origin              GEOGRAPHY(POINT, 4326),
    destination         GEOGRAPHY(POINT, 4326),
    destination_name    VARCHAR(200),
    reason              TEXT,
    eta_minutes         INTEGER,
    status              VARCHAR(30) DEFAULT 'pending',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE simulations (
    id                          SERIAL PRIMARY KEY,
    crisis_id                   VARCHAR(60) REFERENCES crises(id),
    routes                      JSONB,
    traffic_before              JSONB,
    traffic_after               JSONB,
    congestion_reduction_pct    FLOAT,
    emergency_ticket_id         VARCHAR(60),
    public_alerts               JSONB,
    civilian_safe_routes        JSONB,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public_alerts (
    id              VARCHAR(60) PRIMARY KEY,
    crisis_id       VARCHAR(60) REFERENCES crises(id),
    severity        INTEGER,
    affected_zone   GEOGRAPHY(POLYGON, 4326),
    text_english    TEXT,
    text_urdu       TEXT,
    audio_url_urdu  TEXT,
    audio_url_en    TEXT,
    safe_routes     JSONB,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

-- ============================================================
-- TRACK 2: MULTI-AGENCY COORDINATION
-- ============================================================

CREATE TABLE agencies (
    id              VARCHAR(60) PRIMARY KEY,
    name            VARCHAR(200),
    type            VARCHAR(50),  -- ndma | pdma | military | ngo | ingo | un
    country         VARCHAR(10) DEFAULT 'PAK',
    contact_name    VARCHAR(100),
    contact_phone   VARCHAR(30),
    whatsapp_number VARCHAR(30),
    is_active       BOOLEAN DEFAULT true
);

CREATE TABLE agency_deployments (
    id              SERIAL PRIMARY KEY,
    agency_id       VARCHAR(60) REFERENCES agencies(id),
    crisis_id       VARCHAR(60) REFERENCES crises(id),
    coverage_area   GEOMETRY(POLYGON, 4326),
    units_deployed  INTEGER,
    resources_list  JSONB,
    status          VARCHAR(30) DEFAULT 'active',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE resource_gaps (
    id              SERIAL PRIMARY KEY,
    crisis_id       VARCHAR(60) REFERENCES crises(id),
    item_type       VARCHAR(50),
    required        INTEGER,
    available       INTEGER,
    gap             INTEGER GENERATED ALWAYS AS (GREATEST(0, required - available)) STORED,
    priority        VARCHAR(10),  -- critical | high | medium | low
    mitigation      TEXT,
    calculated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sitreps (
    id              VARCHAR(60) PRIMARY KEY,
    crisis_id       VARCHAR(60) REFERENCES crises(id),
    content_md      TEXT,
    content_pdf_url TEXT,
    generated_by    VARCHAR(50) DEFAULT 'ciro_ai',
    verified_by     VARCHAR(100),
    version         INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SHARED: AUDIT & OPERATORS
-- ============================================================

CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    crisis_id       VARCHAR(60),
    event_type      VARCHAR(50),  -- state_change | dispatch | operator_action | agent_decision
    source          VARCHAR(50),  -- agent name or 'operator:user_id'
    details         JSONB,
    reasoning       TEXT,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
    -- Immutable: no UPDATE or DELETE allowed on this table
);

CREATE TABLE operator_actions (
    id              SERIAL PRIMARY KEY,
    operator_id     VARCHAR(60),
    crisis_id       VARCHAR(60) REFERENCES crises(id),
    action_type     VARCHAR(50),  -- confirm | override | escalate | resolve | add_note
    payload         JSONB,
    note            TEXT,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE resources (
    id              VARCHAR(60) PRIMARY KEY,
    name            VARCHAR(100),
    type            VARCHAR(50),
    subtype         VARCHAR(50),
    depot_name      VARCHAR(100),
    location        GEOGRAPHY(POINT, 4326),
    status          VARCHAR(30) DEFAULT 'available',
    quantity        INTEGER DEFAULT 1,
    source_label    VARCHAR(20) DEFAULT 'real'
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_crises_status ON crises(status);
CREATE INDEX idx_crises_location ON crises USING GIST(location);
CREATE INDEX idx_signals_location ON signals USING GIST(location);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_audit_log_crisis ON audit_log(crisis_id, timestamp);
CREATE INDEX idx_public_alerts_zone ON public_alerts USING GIST(affected_zone);
```

---

## 4. Complete API Specification v2

### Agent Webhooks (Pub/Sub push → backend)

All Pub/Sub agents push to these backend endpoints. The backend validates, transitions state, and broadcasts.

```python
# app/api/agent_webhooks.py

POST /webhooks/pubsub/signals-processed
  → validates SignalEvent schema
  → deduplication check against Supabase
  → inserts to signals table
  → checks if clustering threshold met → publishes crisis.detected if so

POST /webhooks/pubsub/crisis-detected
  → validates CrisisEvent schema
  → state_machine.transition(crisis_id, "detected")
  → inserts/updates crises table
  → checks escalation criteria → publishes crisis.major if met
  → broadcasts via WebSocket to dashboard
  → inserts audit_log entry

POST /webhooks/pubsub/ops-picture-ready
  → validates OperationalPicture
  → state_machine.transition(crisis_id, "analyzed")
  → inserts operational_pictures
  → broadcasts update

POST /webhooks/pubsub/dispatch-planned
  → validates DispatchPlan
  → state_machine.transition(crisis_id, "dispatched")
  → inserts dispatch_orders (bulk)
  → updates resource status to 'deployed'
  → broadcasts update

POST /webhooks/pubsub/simulation-complete
  → validates SimulationResult
  → state_machine.transition(crisis_id, "simulated")
  → inserts simulations + public_alerts
  → broadcasts alert to all mobile clients in affected zone

POST /webhooks/pubsub/alert-broadcast
  → validates PublicAlert
  → inserts public_alerts
  → broadcasts to all /ws/crisis/{id} subscribers
  → logs to audit_log

POST /webhooks/pubsub/sitrep-generated
  → validates SITREPDocument
  → inserts sitreps
  → uploads PDF to Cloud Storage
  → broadcasts to dashboard

POST /webhooks/pubsub/track2-update
  → routes to appropriate handler based on event type
```

### Crisis REST API

```
GET  /api/v2/crisis                         List all (filterable: status, type, severity, city)
GET  /api/v2/crisis/active                  Active crises only (public-safe, for mobile)
GET  /api/v2/crisis/{id}                    Full crisis + all sub-schemas
GET  /api/v2/crisis/{id}/timeline           Ordered event log for this crisis
POST /api/v2/crisis/{id}/escalate           Operator: escalate to Track 2
POST /api/v2/crisis/{id}/resolve            Operator: mark resolved
POST /api/v2/crisis/{id}/note               Operator: add note to audit log

GET  /api/v2/crisis/{id}/alerts             Public alerts for this crisis
GET  /api/v2/crisis/{id}/dispatch           Dispatch orders for this crisis
GET  /api/v2/crisis/{id}/simulation         Simulation results
GET  /api/v2/crisis/{id}/sitrep             Latest SITREP for this crisis
```

### Citizen Reports

```
POST /api/v2/reports                        Submit citizen report (mobile)
  Body: { text, location, type_guess, photo_base64? }
  → validates and sanitizes
  → publishes to signals.raw Pub/Sub topic
  → returns { report_id, status: "received" }
```

### Track 2 API

```
GET  /api/v2/track2/{crisis_id}/overview    Multi-agency overview
GET  /api/v2/track2/{crisis_id}/agencies    Agency deployment status
GET  /api/v2/track2/{crisis_id}/gaps        Resource gap analysis
POST /api/v2/track2/{crisis_id}/agencies    Operator: update agency deployment
GET  /api/v2/track2/{crisis_id}/deconflict  Coverage de-confliction map
```

### WebSocket

```
WS /ws/command                              Full command feed (auth required)
WS /ws/crisis/{id}                          Crisis-specific feed (public)
WS /ws/alerts/{city}                        City-wide alert feed (public)
```

### Mobile App

```
GET  /api/v2/mobile/alerts?lat=&lng=&radius=   Alerts near location
GET  /api/v2/mobile/routes/{crisis_id}          Safe routes for crisis
POST /api/v2/mobile/reports                     Citizen report (alias)
GET  /api/v2/mobile/crisis/{id}/audio           Voice alert URL for crisis
```

---

## 5. State Machine (Complete)

```python
# app/core/state_machine.py

VALID_TRANSITIONS = {
    "monitoring":   ["detected"],
    "detected":     ["analyzed", "resolved"],
    "analyzed":     ["dispatched", "resolved"],
    "dispatched":   ["simulated", "resolved"],
    "simulated":    ["resolved"],
    "resolved":     ["archived"],
    "archived":     []
}

TRACK2_ACTIVATION_TRANSITIONS = {
    "detected":   "coordinating",
    "analyzed":   "coordinating",
    "dispatched": "field_ops",
    "simulated":  "field_ops",
}

async def transition(crisis_id: str, new_status: str, source: str, reasoning: str = ""):
    crisis = await db.get_crisis(crisis_id)
    
    if new_status not in VALID_TRANSITIONS.get(crisis.status, []):
        raise InvalidTransitionError(
            f"Cannot transition {crisis.status} → {new_status}"
        )
    
    await db.update_crisis_status(crisis_id, new_status)
    
    # Immutable audit log
    await db.insert_audit(
        crisis_id=crisis_id,
        event_type="state_change",
        source=source,
        details={"from": crisis.status, "to": new_status},
        reasoning=reasoning
    )
    
    # Broadcast
    await ws_manager.broadcast({
        "type": "crisis_state_change",
        "crisis_id": crisis_id,
        "from": crisis.status,
        "to": new_status,
        "timestamp": now_iso()
    }, channels=[f"crisis_{crisis_id}", "command"])
```

---

## 6. Human-in-the-Loop Actions

Operators can override agent decisions via the dashboard. These are the action endpoints:

```python
# POST /api/v2/crisis/{id}/override-dispatch
# Operator disagrees with a dispatch order and creates a manual override

{
  "order_id": "DO_001",
  "action": "cancel | replace | add",
  "replacement_unit": "...",  # if action == "replace"
  "reason": "required text — must explain override"
}

# All overrides logged to audit_log with operator_id
# System sends updated dispatch to affected agents via Pub/Sub
```

---

## 7. Testing

```python
# tests/test_state_machine.py

import pytest
from app.core.state_machine import transition, InvalidTransitionError

async def test_valid_transition():
    await transition("CRS_001", "detected", "agent_2")
    # Asserts: crisis status updated, audit log entry created

async def test_invalid_transition():
    with pytest.raises(InvalidTransitionError):
        await transition("CRS_001", "simulated", "agent_5")  # skipping steps

async def test_track2_escalation():
    crisis = create_test_crisis(severity=4)
    result = await check_escalation(crisis)
    assert result.should_escalate == True
```

---

## 8. Dockerfile v2

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc libgeos-dev libproj-dev gdal-bin \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

## 9. requirements.txt (Pinned)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
supabase==2.4.6
httpx==0.27.0
google-cloud-pubsub==2.21.4
google-cloud-texttospeech==2.16.3
google-cloud-storage==2.17.0
google-generativeai==0.7.2
python-jose[cryptography]==3.3.0
PyMuPDF==1.24.4
feedparser==6.0.11
shapely==2.0.4
geopy==2.4.1
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.6
```
