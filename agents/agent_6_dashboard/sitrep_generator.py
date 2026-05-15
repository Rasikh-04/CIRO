"""
Agent 6 — SITREP Generator
Reads the full crisis record from the backend, calls Gemini via a prompt,
and writes the SITREP to output/sitrep.md.

In Antigravity: the agent runs this via terminal tool.
Outside Antigravity: run directly for testing.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SITREP_PROMPT_TEMPLATE = """Generate a professional situation report (SITREP) in the exact format below.
Use ONLY the data provided. Be concise and factual. No added commentary.

Crisis Data:
{crisis_json}

Dispatch Data:
{dispatch_json}

Simulation Data:
{simulation_json}

---
SITUATION REPORT
Date/Time: {datetime}
Crisis ID: {crisis_id}
Prepared by: CIRO Automated System

1. SITUATION
   Type: {type} | Location: {location} | Severity: {severity}/5
   [2-3 sentences describing the confirmed situation based on signal data]

2. AFFECTED AREA
   [1-2 sentences on geographic scope and estimated population at risk]

3. ACTIONS TAKEN
   [Bulleted list of dispatch orders with unit name, destination, and ETA]

4. RESOURCES DEPLOYED
   [List of all units and supplies dispatched]

5. SIMULATED OUTCOME
   Congestion reduction: {congestion_pct}%
   Units en route: {units_count}
   Emergency ticket: {ticket_id}

6. PUBLIC GUIDANCE
   [2-3 actionable sentences for residents in affected area]

7. NEXT UPDATE
   Scheduled: +30 minutes
---
Return this as formatted markdown. Do not add any text outside the report template."""


def load_dashboard_state(state_path: str | None = None) -> dict:
    if state_path:
        with open(state_path) as f:
            return json.load(f)
    raise FileNotFoundError("No dashboard state provided. Run push_to_backend.py first.")


def build_sitrep_prompt(state: dict) -> str:
    crisis = state.get("crisis", {})
    dispatch = state.get("dispatch_plan", {}).get("dispatch_plan", {})
    simulation = state.get("simulation", {}).get("simulation", {})

    orders = dispatch.get("dispatch_orders", [])
    units_count = len(orders)
    ticket_id = simulation.get("emergency_ticket", {}).get("ticket_id", "N/A")
    congestion_pct = simulation.get("traffic_state", {}).get("congestion_reduction_pct", 0)

    return SITREP_PROMPT_TEMPLATE.format(
        crisis_json=json.dumps(crisis, indent=2),
        dispatch_json=json.dumps(dispatch, indent=2),
        simulation_json=json.dumps(simulation, indent=2),
        datetime=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        crisis_id=crisis.get("crisis_id", "N/A"),
        type=crisis.get("type", "N/A").replace("_", " ").title(),
        location=crisis.get("location", {}).get("primary", "N/A"),
        severity=crisis.get("severity", "N/A"),
        congestion_pct=congestion_pct,
        units_count=units_count,
        ticket_id=ticket_id,
    )


def write_sitrep(sitrep_text: str) -> Path:
    out = OUTPUT_DIR / "sitrep.md"
    out.write_text(sitrep_text, encoding="utf-8")
    print(f"[SITREP] Written to {out}")
    return out


def log(message: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] AGENT_6 | SITREP | {message}"
    print(line)
    with open(OUTPUT_DIR / "agent6_trace.log", "a") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    log("START | SITREP generation initiated")

    state_path = sys.argv[1] if len(sys.argv) > 1 else str(OUTPUT_DIR / "dashboard_state.json")

    if not Path(state_path).exists():
        log(f"ERROR | dashboard_state.json not found at {state_path}")
        print("Usage: python sitrep_generator.py [path/to/dashboard_state.json]")
        sys.exit(1)

    log(f"LOAD | Reading dashboard state from {state_path}")
    state = load_dashboard_state(state_path)

    prompt = build_sitrep_prompt(state)
    log("PROCESS | SITREP prompt built — pass to Gemini in Antigravity")

    # In Antigravity: the agent uses Gemini to fill this prompt.
    # For local testing: write the prompt as a placeholder SITREP.
    placeholder = f"""# SITREP — PLACEHOLDER (Run via Antigravity for Gemini output)

**Gemini Prompt to use:**

```
{prompt}
```

Replace this file content with Gemini's output.
"""
    write_sitrep(placeholder)
    log("OUTPUT | sitrep.md written (placeholder — replace with Gemini output)")
    log("END | Duration: <1s")
