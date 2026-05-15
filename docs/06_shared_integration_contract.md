# CIRO — Shared Integration Contract
## The Single Document All Three Members Must Work From

> **READ THIS FIRST. BEFORE WRITING ANY CODE.**  
> This document defines the exact interfaces between all three workstreams.  
> If your output doesn't match these schemas, integration breaks.  
> Any schema changes must be announced in the team chat before implementation.

---

## 0. Team Quick Reference

| Member | Role | Primary Responsibility |
|---|---|---|
| **Abdul Mannan** | Antigravity orchestration + UI | Antigravity Agent Manager setup, web dashboard, mobile app |
| **Tabeen Bokhat** | Signal & Detection | Agent 1 + Agent 2 code, Gemini prompt engineering |
| **Abdul Hannan Ahmar** | Backend & Simulation | FastAPI backend, database, Agent 4 + Agent 5 routing logic |

---

## 1. The Demo Scenario (Fixed — Do Not Change)

Everything is built around this one scenario. No exceptions.

```
Crisis Type:    Urban Flooding
Location:       G-10, Islamabad
Lat/Lng:        33.6844, 73.0479
Severity:       4/5
Confidence:     High (0.89)
Trigger:        3 social media posts + heavy rainfall alert + traffic spike
Dispatch:       F-8 Rescue Unit Alpha → G-10 via Margalla Road
Outcome:        61% congestion reduction simulated
```

All mock data, all coordinate references, all hardcoded values must match this scenario.

---

## 2. Fixed Coordinates (Use Everywhere)

| Entity | Lat | Lng | Used In |
|---|---|---|---|
| Crisis center (G-10) | 33.6844 | 73.0479 | All agents, map, mobile |
| F-8 Rescue Station | 33.7080 | 73.0479 | inventory.json, map |
| PIMS Hospital | 33.7161 | 73.0738 | facilities_db.json, map |
| Srinagar Highway blockage | 33.6880 | 73.0550 | ops_pic.json, map overlay |
| Margalla Road (alternate) | 33.7200 | 73.0450 | route simulation, map |

---

## 3. Canonical JSON Schemas

These schemas are the contracts. Members write to these schemas; consumers read from them.

### Schema A: `SignalEvent` (Agent 1 → Agent 2, Backend)
```json
{
  "id": "sig_001",
  "source": "social_media | weather | traffic",
  "raw_text": "string",
  "normalized": "string (English)",
  "location": {
    "district": "string",
    "city": "string",
    "lat": 0.0,
    "lng": 0.0
  },
  "signal_type": "flood | heatwave | accident | road_blockage | infrastructure_failure",
  "timestamp": "ISO8601",
  "confidence": 0.0,
  "source_label": "simulated | real"
}
```

### Schema B: `CrisisEvent` (Agent 2 → Agent 3, Backend)
```json
{
  "crisis_id": "CRS_20260513_001",
  "type": "urban_flooding | heatwave | accident | road_blockage | infrastructure_failure",
  "location": {
    "primary": "string",
    "affected_radius_km": 0.0,
    "lat": 0.0,
    "lng": 0.0
  },
  "severity": 4,
  "confidence": "low | medium | high",
  "confidence_score": 0.0,
  "reasoning": "string",
  "contributing_signals": ["sig_001", "sig_002"],
  "status": "confirmed",
  "detected_at": "ISO8601"
}
```

### Schema C: `OperationalPicture` (Agent 3 → Agent 4, Backend)
```json
{
  "crisis_id": "string",
  "operational_picture": {
    "affected_zone": {
      "center": [33.6844, 73.0479],
      "radius_km": 2.5
    },
    "road_closures": [
      {
        "road": "string",
        "status": "blocked | partial | clear",
        "lat": 0.0,
        "lng": 0.0,
        "source": "traffic_api | osm | simulated"
      }
    ],
    "nearby_facilities": [
      {
        "type": "rescue_unit | hospital | fire_station | depot",
        "name": "string",
        "lat": 0.0,
        "lng": 0.0,
        "distance_km": 0.0,
        "status": "available | deployed | unavailable"
      }
    ],
    "data_gaps": [],
    "population_at_risk": 0
  },
  "generated_at": "ISO8601"
}
```

### Schema D: `DispatchPlan` (Agent 4 → Agent 5, Backend)
```json
{
  "crisis_id": "string",
  "dispatch_plan": {
    "priority_ranking": [
      {
        "zone": "string",
        "priority_score": 0,
        "reason": "string"
      }
    ],
    "dispatch_orders": [
      {
        "order_id": "DO_001",
        "unit": "string",
        "unit_type": "water_rescue | ambulance | fire | police | supplies",
        "destination": "string",
        "destination_lat": 0.0,
        "destination_lng": 0.0,
        "origin_lat": 0.0,
        "origin_lng": 0.0,
        "reason": "string",
        "eta_minutes": 0
      }
    ],
    "resource_gaps": [
      {
        "item": "string",
        "required": 0,
        "available": 0,
        "gap": 0,
        "mitigation": "string"
      }
    ]
  },
  "generated_at": "ISO8601"
}
```

### Schema E: `SimulationResult` (Agent 5 → Agent 6, Backend)
```json
{
  "crisis_id": "string",
  "simulation": {
    "routes": [
      {
        "order_id": "DO_001",
        "unit": "string",
        "route": {
          "via": "string",
          "waypoints": [[33.7080, 73.0479], [33.6844, 73.0479]],
          "distance_km": 0.0,
          "duration_min": 0
        },
        "route_reasoning": "string"
      }
    ],
    "traffic_state": {
      "before": { "road_name": "congestion_level" },
      "after": { "road_name": "congestion_level" },
      "congestion_reduction_pct": 0.0
    },
    "emergency_ticket": {
      "ticket_id": "EMT_2841",
      "created_at": "ISO8601",
      "status": "dispatched",
      "units": ["string"]
    },
    "public_alerts": [
      {
        "channel": "SMS | app_push | dashboard",
        "target_area": "string",
        "message": "string"
      }
    ]
  },
  "created_at": "ISO8601"
}
```

### Schema F: `DashboardState` (Agent 6 → Backend → UI)
```json
{
  "crisis_id": "string",
  "stage": "detected | analyzed | dispatched | simulated | resolved",
  "crisis": { ...CrisisEvent },
  "operational_picture": { ...OperationalPicture },
  "dispatch_plan": { ...DispatchPlan },
  "simulation": { ...SimulationResult },
  "sitrep_text": "string (markdown)",
  "agent_trace_summary": [
    {
      "agent": "Agent_1",
      "key_decision": "string",
      "timestamp": "ISO8601"
    }
  ],
  "last_updated": "ISO8601"
}
```

---

## 4. Backend API Contract (All Members Must Know)

**Base URL (dev):** `http://localhost:8000`  
**Base URL (prod):** `https://ciro-backend-[hash]-uc.a.run.app`

### Endpoints Every Member Calls

| Who | Method | Endpoint | Sends | Gets Back |
|---|---|---|---|---|
| Member 2 (Agent 1) | POST | `/api/signals/ingest` | `SignalEvent[]` | `{"accepted": n}` |
| Member 2 (Agent 2) | GET | `/api/signals/latest` | — | `SignalEvent[]` |
| Member 2 (Agent 2) | POST | `/api/crisis/detected` | `CrisisEvent` | `{"crisis_id": "..."}` |
| Member 3 (Agent 3) | GET | `/api/crisis/latest` | — | `CrisisEvent` |
| Member 3 (Agent 3) | POST | `/api/crisis/operational` | `OperationalPicture` | `{"ok": true}` |
| Member 3 (Agent 4) | GET | `/api/resources/available` | — | `Resource[]` |
| Member 3 (Agent 4) | POST | `/api/crisis/dispatch` | `DispatchPlan` | `{"ok": true}` |
| Member 3 (Agent 5) | POST | `/api/crisis/simulation` | `SimulationResult` | `{"ok": true}` |
| Team Lead (Agent 6) | GET | `/api/crisis/full/{id}` | — | All schemas merged |
| Team Lead (Agent 6) | POST | `/api/crisis/complete` | `DashboardState` | `{"ok": true}` |
| Mobile App | GET | `/api/crisis/active` | — | Summary list |
| Web Dashboard | WS | `/ws/crisis/{id}` | — | Live `DashboardState` |

---

## 5. Integration Checkpoints

### Checkpoint 1 — Day 2 (May 14–15): Smoke Test
**Goal:** Backend is running locally; Agent 1 can POST to it; Dashboard can fetch from it.

What to verify:
- Member 3: Backend running at localhost:8000, `/api/signals/ingest` returns 200
- Member 2: Agent 1 prompt produces valid `SignalEvent[]` JSON
- Team Lead: Dashboard fetches from `/api/crisis/active` without errors (empty list is fine)

**Do this before deep-building anything.** Catching schema mismatches on day 2 is fine. Day 6 is catastrophic.

### Checkpoint 2 — Day 5 (May 17–18): End-to-End Dry Run
**Goal:** Full demo scenario runs end-to-end, even if ugly.

What to verify:
- Full 6-agent pipeline completes without manual intervention
- Dashboard updates via WebSocket at each stage
- Mobile app shows active crisis with correct location
- Agent trace log covers all 6 agents

---

## 6. File Locations (Shared Across Members)

Use a shared GitHub repo. Structure:

```
ciro/
├── backend/           ← Member 3 owns
│   ├── app/
│   ├── data/          ← shared mock data files (everyone reads these)
│   │   ├── mock_social_media.json   ← Member 2 writes
│   │   ├── facilities_db.json       ← Member 3 writes
│   │   ├── inventory.json           ← Member 3 writes
│   │   └── population_density.json  ← Member 3 writes
│   └── scripts/
├── agents/            ← Team Lead + Member 2 own
│   ├── agent_1_signal_ingestion/
│   ├── agent_2_crisis_detection/
│   ├── agent_3_situational_awareness/
│   ├── agent_4_resource_dispatch/
│   ├── agent_5_simulation/
│   └── agent_6_dashboard/
├── web-dashboard/     ← Team Lead owns
├── mobile-app/        ← Team Lead owns
├── docs/              ← All documentation files (this folder)
└── README.md
```

---

## 7. The One Rule

> **If you change a schema field name, type, or structure, you tell the team before merging.**

Everything else can be flexible. Schemas cannot drift silently.
