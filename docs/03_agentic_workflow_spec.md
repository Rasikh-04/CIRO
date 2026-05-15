# CIRO — Agentic Workflow Architecture, Design & Specification
## Google Antigravity Integration Guide

---

## 1. What Google Antigravity Is (For This Project)

Antigravity is an **agent-first IDE** with two surfaces:

- **Editor View**: Standard AI-powered coding interface (VS Code base). Used for writing code, editing files, running tests.
- **Agent Manager (Mission Control)**: Dedicated interface for spawning, orchestrating, and observing multiple agents running asynchronously in parallel workspaces.

For CIRO, **Agent Manager is the core**. Each of our 6 agents runs as an independent agent instance in Agent Manager, with its own workspace, task plan, and artifact trail.

### Key Antigravity Concepts Used in CIRO

| Concept | How CIRO Uses It |
|---|---|
| **Agent Manager** | Spawns and monitors all 6 CIRO agents |
| **Workspaces** | Each agent has its own workspace folder with relevant code/data |
| **Artifacts** | Each agent produces Task Plan → Implementation Plan → Output JSON → Log |
| **Parallel Execution** | Agents 1 & 2 can run simultaneously; Agents 3, 4, 5, 6 chain sequentially |
| **Review Policy** | Set to "Agent Decides" for demo flow; switch to "Request Review" for judge walkthroughs |
| **Knowledge Base** | Store reusable prompt templates, API schemas, and crisis type definitions |
| **Browser Tool** | Agent 1 uses it to hit weather + traffic APIs; Agent 3 queries Overpass API |
| **Terminal Tool** | Agents call Python scripts / curl commands for API integrations |

---

## 2. Agent Manager Setup

### Workspace Structure (on your local machine)
```
CIRO/
├── agent_1_signal_ingestion/
│   ├── mock_social_media.json
│   ├── ingest.py
│   └── .agy_rules          ← Antigravity agent rules file
├── agent_2_crisis_detection/
│   ├── classify.py
│   ├── thresholds.json
│   └── .agy_rules
├── agent_3_situational_awareness/
│   ├── osm_query.py
│   ├── facilities_db.json
│   └── .agy_rules
├── agent_4_resource_dispatch/
│   ├── inventory.json
│   ├── dispatch.py
│   └── .agy_rules
├── agent_5_simulation/
│   ├── simulate.py
│   ├── route_engine.py
│   └── .agy_rules
└── agent_6_dashboard/
    ├── sitrep_generator.py
    ├── push_to_backend.py
    └── .agy_rules
```

Each workspace is imported into Antigravity's Agent Manager as a separate workspace.

### Antigravity `.agy_rules` File (per agent)
This file defines the agent's behavior constraints. Example for Agent 1:
```
# Agent 1 — Signal Ingestion Rules
- Always output results to output/signals.json
- Use Gemini 3.1 Pro for text normalization
- Do not call external APIs without confirming URL in allowed list
- Log every signal processed with timestamp
- On completion, call: POST http://localhost:8000/api/signals/ingest
```

---

## 3. Agent Pipeline Flow

```
[TRIGGER: Manual or scheduled]
          │
          ▼
┌─────────────────────┐
│  Agent 1            │  → Reads mock_social_media.json
│  Signal Ingestion   │  → Calls Open-Meteo API (browser tool)
│                     │  → Calls Google Maps Traffic API
│  OUTPUT: signals.json│
└──────────┬──────────┘
           │ (POST to /api/signals → triggers Agent 2)
           ▼
┌─────────────────────┐
│  Agent 2            │  → Reads signals.json
│  Crisis Detection   │  → Clusters signals by location + type
│                     │  → Gemini 3.1 Pro: generate confidence reasoning
│  OUTPUT: crisis.json│
└──────────┬──────────┘
           │ (POST to /api/crisis/detected → triggers Agent 3)
           ▼
┌─────────────────────┐
│  Agent 3            │  → Queries Overpass API (browser tool)
│  Situational        │  → Reads facilities_db.json
│  Awareness          │  → Builds operational picture
│  OUTPUT: ops_pic.json│
└──────────┬──────────┘
           │ (POST to /api/crisis/operational → triggers Agent 4)
           ▼
┌─────────────────────┐
│  Agent 4            │  → Reads inventory.json + ops_pic.json
│  Resource Gap &     │  → Gap calculation (Python script)
│  Dispatch           │  → Priority ranking
│  OUTPUT: dispatch.json│
└──────────┬──────────┘
           │ (POST to /api/crisis/dispatch → triggers Agent 5)
           ▼
┌─────────────────────┐
│  Agent 5            │  → Calls OpenRouteService API
│  Route & Action     │  → Simulates traffic state change
│  Simulation         │  → Generates emergency ticket
│                     │  → Generates public alerts
│  OUTPUT: simulation.json│
└──────────┬──────────┘
           │ (POST to /api/crisis/simulation → triggers Agent 6)
           ▼
┌─────────────────────┐
│  Agent 6            │  → Aggregates all outputs
│  Command &          │  → Gemini 3.1 Pro: generate SITREP
│  Dashboard          │  → POST to /api/crisis/complete
│                     │  → Dashboard + mobile updated via WebSocket
│  OUTPUT: sitrep.md  │
│          dashboard_state.json│
└─────────────────────┘
```

---

## 4. Agent Prompts (Antigravity Mission Prompts)

These are the exact prompts to give each agent in Antigravity's Agent Manager.

### Agent 1 Prompt
```
You are the Signal Ingestion Agent for CIRO (Crisis Intelligence & Response Orchestrator).

Your task:
1. Read the file mock_social_media.json — these are simulated social media posts
2. Use the browser tool to call: https://api.open-meteo.com/v1/forecast?latitude=33.6844&longitude=73.0479&current=precipitation,weathercode&timezone=Asia/Karachi
3. Use the browser tool to call the Google Maps traffic simulation endpoint (see traffic_mock.json if real API unavailable)
4. For each social media post, normalize the text into English using Gemini — extract location, crisis type, and severity keywords
5. Combine all signals into the SignalEvent schema (see schema.json)
6. Write the output to output/signals.json
7. Log every step to output/agent1_trace.log
8. When done, POST the output to http://localhost:8000/api/signals/ingest
```

### Agent 2 Prompt
```
You are the Crisis Detection & Classification Agent for CIRO.

Your task:
1. Read output/signals.json from Agent 1's workspace (or from the backend GET /api/signals/latest)
2. Cluster signals: group those within 5km radius and same crisis type within a 30-minute window
3. Cross-reference: if ≥2 signals from different sources (social + weather, or social + traffic) confirm same event, mark as corroborated
4. For each cluster with ≥2 signals, use Gemini to generate a confidence score (0-1) and a 2-3 sentence reasoning explanation
5. Classify crisis type: flood | heatwave | accident | road_blockage | infrastructure_failure
6. Assign severity 1-5 based on: number of signals, signal intensity, population density
7. Write output to output/crisis.json using CrisisEvent schema (see schema.json)
8. Log every step to output/agent2_trace.log
9. If confidence_score > 0.7, POST to http://localhost:8000/api/crisis/detected
```

### Agent 3 Prompt
```
You are the Situational Awareness Agent for CIRO.

Your task:
1. Read crisis.json from Agent 2 (or GET /api/crisis/latest)
2. Use the browser tool to query Overpass API for road network in affected zone:
   https://overpass-api.de/api/interpreter?data=[bbox:{lat-0.05},{lng-0.05},{lat+0.05},{lng+0.05}][highway]
3. Read facilities_db.json — this contains emergency units, hospitals, rescue stations with coordinates
4. For each facility, calculate distance from crisis center using the Haversine formula (run via terminal: python haversine.py)
5. Identify road closures based on traffic data from Agent 1 + crisis location overlap
6. Estimate population at risk using population_density.json (district-level estimates)
7. Write output to output/ops_pic.json using OperationalPicture schema
8. Log to output/agent3_trace.log
9. POST to http://localhost:8000/api/crisis/operational
```

### Agent 4 Prompt
```
You are the Resource Gap & Dispatch Agent for CIRO.

Your task:
1. Read ops_pic.json from Agent 3 (or GET /api/crisis/operational)
2. Read inventory.json — current resource availability across all depots
3. Calculate resource requirements using OCHA standard rates:
   - Tents: 1 per 5 people
   - Food packs: 3 per person per day
   - Medical kits: 1 per 50 people
   - Water rescue units: 1 per 500 people at risk
4. Compare requirements vs. inventory — identify gaps
5. Rank response priorities: severity_score × (1/distance_km) × population_at_risk
6. Select and assign units: for each required resource type, pick the nearest available unit
7. Generate dispatch orders with written reasoning for each decision (2-3 sentences)
8. Write output to output/dispatch.json
9. Log to output/agent4_trace.log
10. POST to http://localhost:8000/api/crisis/dispatch
```

### Agent 5 Prompt
```
You are the Route & Action Simulation Agent for CIRO.

Your task:
1. Read dispatch.json from Agent 4 (or GET /api/crisis/dispatch)
2. For each dispatch order, use the browser tool to call OpenRouteService:
   https://api.openrouteservice.org/v2/directions/driving-car
   - Origin: unit current location
   - Destination: crisis zone center
   - Avoid: blocked roads from ops_pic.json
3. Record route waypoints, distance, and estimated duration
4. Simulate traffic state change: mark blocked roads as "diverted", calculate congestion reduction %
5. Generate an emergency ticket (use terminal: python generate_ticket.py)
6. Generate public alert messages for SMS and app notification
7. Record before/after traffic state
8. Write output to output/simulation.json
9. Log to output/agent5_trace.log
10. POST to http://localhost:8000/api/crisis/simulation
```

### Agent 6 Prompt
```
You are the Command & Dashboard Agent for CIRO.

Your task:
1. GET /api/crisis/full/{crisis_id} — retrieve all agent outputs for this crisis
2. Use Gemini to generate a SITREP in the following format:
   ---
   SITUATION REPORT — [datetime]
   Crisis ID: [id]
   Type: [type] | Location: [location] | Severity: [X/5]
   
   SITUATION: [2-3 sentence summary]
   ACTIONS TAKEN: [bulleted dispatch orders]
   RESOURCES DEPLOYED: [list]
   CURRENT STATUS: [outcome summary]
   NEXT UPDATE: [30 min from now]
   ---
3. Write SITREP to output/sitrep.md
4. Build dashboard_state.json — unified object for web + mobile
5. POST dashboard_state to http://localhost:8000/api/crisis/complete
6. Log all agent reasoning chain to output/agent6_trace.log (include agent 1-5 summaries)
7. The final trace log is a submission deliverable — make it readable and well-structured
```

---

## 5. Trace Log Format (Submission Deliverable)

Each agent must produce a structured log. This is what judges read.

```
[2026-05-13T14:32:00Z] AGENT_1 | START | Signal Ingestion initiated
[2026-05-13T14:32:01Z] AGENT_1 | TOOL_CALL | browser → Open-Meteo API
[2026-05-13T14:32:03Z] AGENT_1 | RESULT | weather: precipitation=12mm/hr, code=95 (thunderstorm)
[2026-05-13T14:32:04Z] AGENT_1 | PROCESS | Normalizing 8 social media posts via Gemini
[2026-05-13T14:32:08Z] AGENT_1 | DECISION | 3 signals classified as flood-type in G-10 area
[2026-05-13T14:32:09Z] AGENT_1 | OUTPUT | Written to output/signals.json (8 signals)
[2026-05-13T14:32:10Z] AGENT_1 | ACTION | POST /api/signals/ingest → 200 OK
[2026-05-13T14:32:10Z] AGENT_1 | END | Duration: 10s
```

The full consolidated trace (all 6 agents) is exported as `CIRO_agent_trace.log` for submission.

---

## 6. Antigravity-Specific Tips for This Project

- **Use "Review-driven development" mode** during development. Switch to "Agent-driven" for the final demo recording so the flow is uninterrupted.
- **Save prompt templates to Knowledge Base** in Antigravity — this makes re-running agents faster.
- **Use Artifacts** — after each agent run, save the output JSON as an Artifact. This creates a clean paper trail for judges.
- **Browser tool for APIs** — Agent 1, 3, and 5 heavily use Antigravity's built-in browser tool to hit external APIs. Test these API calls manually first before giving to the agent.
- **Context window management** — if an agent session gets long, start a fresh conversation with a summary of prior state rather than continuing in the same window.
- **Parallel agents** — Agent 1 and Agent 6's SITREP generation can run in parallel with other agents during the demo. Use this in the demo video to show Antigravity's parallel capability.
