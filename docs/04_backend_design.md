# CIRO — Backend Design Document
## FastAPI + PostgreSQL + PostGIS

**Owner:** Member 3  
**Stack:** Python 3.11, FastAPI, SQLAlchemy, PostGIS, WebSocket, Docker, Google Cloud Run

---

## 1. Role of the Backend

The backend is the **central state store and relay layer** between:
- Antigravity agents (write state via REST)
- Web dashboard (reads state via WebSocket + REST)
- Mobile app (reads state via REST polling)

The backend does **not** contain agent logic. All reasoning, classification, routing, and dispatch decisions happen in Antigravity agents. The backend stores, serves, and relays their outputs.

---

## 2. Project Structure

```
ciro-backend/
├── main.py                    # FastAPI app entry point
├── requirements.txt
├── Dockerfile
├── .env                       # API keys, DB URL (never commit)
├── app/
│   ├── api/
│   │   ├── signals.py         # /api/signals/*
│   │   ├── crisis.py          # /api/crisis/*
│   │   ├── resources.py       # /api/resources/* (inventory)
│   │   └── websocket.py       # /ws/*
│   ├── models/
│   │   ├── signal.py          # SQLAlchemy ORM models
│   │   ├── crisis.py
│   │   ├── dispatch.py
│   │   └── simulation.py
│   ├── schemas/
│   │   ├── signal.py          # Pydantic schemas (input validation)
│   │   ├── crisis.py
│   │   └── simulation.py
│   ├── db/
│   │   ├── session.py         # DB session setup
│   │   └── init_db.py         # Table creation + seed data
│   ├── services/
│   │   ├── crisis_service.py  # Business logic (state transitions)
│   │   └── alert_service.py   # Simulated alert generation
│   └── ws/
│       └── manager.py         # WebSocket connection manager
├── data/
│   ├── mock_social_media.json
│   ├── facilities_db.json
│   ├── inventory.json
│   └── population_density.json
└── scripts/
    ├── generate_ticket.py
    ├── haversine.py
    └── seed_db.py
```

---

## 3. Database Schema

### Table: `signals`
```sql
CREATE TABLE signals (
    id              VARCHAR(50) PRIMARY KEY,
    source          VARCHAR(30),        -- social_media | weather | traffic
    raw_text        TEXT,
    normalized      TEXT,
    signal_type     VARCHAR(30),        -- flood | accident | heatwave etc.
    location        GEOGRAPHY(POINT),
    district        VARCHAR(100),
    city            VARCHAR(100),
    confidence      FLOAT,
    timestamp       TIMESTAMPTZ,
    crisis_id       VARCHAR(50) REFERENCES crises(id)
);
```

### Table: `crises`
```sql
CREATE TABLE crises (
    id              VARCHAR(50) PRIMARY KEY,
    type            VARCHAR(50),
    location        GEOGRAPHY(POINT),
    location_name   VARCHAR(200),
    affected_radius FLOAT,              -- km
    severity        INTEGER,            -- 1-5
    confidence      FLOAT,
    confidence_label VARCHAR(10),       -- low | medium | high
    reasoning       TEXT,
    status          VARCHAR(30),        -- detected | analyzed | dispatched | simulated | resolved
    detected_at     TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ
);
```

### Table: `operational_pictures`
```sql
CREATE TABLE operational_pictures (
    id              SERIAL PRIMARY KEY,
    crisis_id       VARCHAR(50) REFERENCES crises(id),
    road_closures   JSONB,
    nearby_facilities JSONB,
    population_at_risk INTEGER,
    data_gaps       JSONB,
    generated_at    TIMESTAMPTZ
);
```

### Table: `dispatch_orders`
```sql
CREATE TABLE dispatch_orders (
    id              VARCHAR(50) PRIMARY KEY,
    crisis_id       VARCHAR(50) REFERENCES crises(id),
    unit_name       VARCHAR(100),
    unit_type       VARCHAR(50),
    destination     VARCHAR(200),
    destination_geo GEOGRAPHY(POINT),
    reason          TEXT,
    eta_minutes     INTEGER,
    status          VARCHAR(30),        -- pending | en_route | on_scene
    created_at      TIMESTAMPTZ
);
```

### Table: `simulations`
```sql
CREATE TABLE simulations (
    id              SERIAL PRIMARY KEY,
    crisis_id       VARCHAR(50) REFERENCES crises(id),
    routes          JSONB,              -- route data per unit
    traffic_before  JSONB,
    traffic_after   JSONB,
    congestion_reduction_pct FLOAT,
    emergency_ticket_id VARCHAR(50),
    public_alerts   JSONB,
    created_at      TIMESTAMPTZ
);
```

### Table: `resources` (Simulated Inventory)
```sql
CREATE TABLE resources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100),
    type            VARCHAR(50),        -- rescue_unit | supplies | vehicle
    depot_name      VARCHAR(100),
    location        GEOGRAPHY(POINT),
    status          VARCHAR(30),        -- available | deployed | unavailable
    quantity        INTEGER
);
```

---

## 4. API Endpoints

### Signals

| Method | Endpoint | Description | Called By |
|---|---|---|---|
| POST | `/api/signals/ingest` | Agent 1 pushes normalized signals | Agent 1 |
| GET | `/api/signals/latest` | Get most recent signal batch | Agent 2, Dashboard |

### Crisis Lifecycle

| Method | Endpoint | Description | Called By |
|---|---|---|---|
| POST | `/api/crisis/detected` | Agent 2 confirms a crisis | Agent 2 |
| POST | `/api/crisis/operational` | Agent 3 posts operational picture | Agent 3 |
| POST | `/api/crisis/dispatch` | Agent 4 posts dispatch plan | Agent 4 |
| POST | `/api/crisis/simulation` | Agent 5 posts simulation results | Agent 5 |
| POST | `/api/crisis/complete` | Agent 6 posts final state + SITREP | Agent 6 |
| GET | `/api/crisis/active` | List all active crises (public-safe) | Mobile app |
| GET | `/api/crisis/{id}` | Full crisis record (command view) | Web dashboard |
| GET | `/api/crisis/full/{id}` | All agent outputs aggregated | Agent 6 |

### Resources

| Method | Endpoint | Description | Called By |
|---|---|---|---|
| GET | `/api/resources/available` | Inventory of available units | Agent 4 |
| PATCH | `/api/resources/{id}/status` | Update unit status after dispatch | Agent 4, 5 |

### WebSocket

| Endpoint | Description | Consumers |
|---|---|---|
| `/ws/crisis/{crisis_id}` | Real-time updates for a specific crisis | Web dashboard, Mobile |
| `/ws/command` | All crisis updates (command room feed) | Web dashboard |

---

## 5. WebSocket Manager

```python
# app/ws/manager.py
from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, crisis_id: str):
        await websocket.accept()
        if crisis_id not in self.active_connections:
            self.active_connections[crisis_id] = []
        self.active_connections[crisis_id].append(websocket)

    def disconnect(self, websocket: WebSocket, crisis_id: str):
        self.active_connections[crisis_id].remove(websocket)

    async def broadcast(self, message: dict, crisis_id: str):
        if crisis_id in self.active_connections:
            for connection in self.active_connections[crisis_id]:
                await connection.send_json(message)

manager = ConnectionManager()
```

Every time an agent POSTs a new stage update, the crisis service calls `manager.broadcast()` to push the update to all connected clients.

---

## 6. Crisis State Machine

```
INITIATED → DETECTED → ANALYZED → DISPATCHED → SIMULATED → RESOLVED
```

State transitions are triggered by agent POST calls. Invalid transitions are rejected (e.g., cannot go from DETECTED to SIMULATED, skipping ANALYZED).

```python
VALID_TRANSITIONS = {
    "initiated":   ["detected"],
    "detected":    ["analyzed"],
    "analyzed":    ["dispatched"],
    "dispatched":  ["simulated"],
    "simulated":   ["resolved"],
}
```

---

## 7. Simulated Data Files

### `data/mock_social_media.json`
```json
[
  {
    "id": "sm_001",
    "platform": "Twitter/X",
    "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
    "timestamp": "2026-05-13T14:30:00Z",
    "user_location": "Islamabad",
    "source": "simulated"
  },
  {
    "id": "sm_002",
    "text": "Flash flood happening at G10 for past 30 mins, roads completely blocked",
    "timestamp": "2026-05-13T14:31:00Z",
    "source": "simulated"
  }
]
```

### `data/inventory.json`
```json
[
  {
    "id": "res_001",
    "name": "F-8 Rescue Unit Alpha",
    "type": "water_rescue",
    "depot": "F-8 Rescue Station",
    "lat": 33.7080, "lng": 73.0479,
    "status": "available",
    "quantity": 1,
    "source": "simulated"
  }
]
```

---

## 8. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. Environment Variables (`.env`)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ciro
OPENROUTESERVICE_API_KEY=your_key_here
GOOGLE_MAPS_API_KEY=your_key_here
ENVIRONMENT=development
```

---

## 10. Deployment to Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ciro-backend

# Deploy to Cloud Run
gcloud run deploy ciro-backend \
  --image gcr.io/YOUR_PROJECT_ID/ciro-backend \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=...,OPENROUTESERVICE_API_KEY=...
```

Use Cloud SQL for PostgreSQL + PostGIS in production, or a local Docker PostgreSQL for development.

---

## 11. Development Setup

```bash
# Clone repo and set up environment
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary geoalchemy2 websockets python-dotenv

# Start local PostgreSQL with PostGIS
docker run -d \
  --name ciro-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=ciro \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Initialize database
python scripts/seed_db.py

# Run backend
uvicorn main:app --reload --port 8000
```

---

## 12. Key Libraries

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
geoalchemy2==0.14.7
psycopg2-binary==2.9.9
python-dotenv==1.0.1
httpx==0.27.0       # For calling external APIs from backend
websockets==12.0
pymupdf==1.24.0     # Optional: NDMA PDF parsing
```
