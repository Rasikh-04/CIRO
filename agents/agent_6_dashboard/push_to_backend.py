"""
Agent 6 — Push to Backend
Aggregates all agent outputs into DashboardState (Schema F) and POSTs to backend.

In Antigravity: the agent runs this via terminal tool after sitrep_generator.py.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OUTPUT_DIR = Path(__file__).parent / "output"


def log(message: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] AGENT_6 | PUSH | {message}"
    print(line)
    with open(OUTPUT_DIR / "agent6_trace.log", "a") as f:
        f.write(line + "\n")


def fetch_full_state(crisis_id: str) -> dict:
    url = f"{BACKEND_URL}/api/crisis/full/{crisis_id}"
    log(f"TOOL_CALL | GET {url}")
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    log(f"RESULT | Full crisis state retrieved ({len(resp.content)} bytes)")
    return resp.json()


def load_sitrep() -> str:
    sitrep_path = OUTPUT_DIR / "sitrep.md"
    if sitrep_path.exists():
        return sitrep_path.read_text(encoding="utf-8")
    return ""


_LOG_RE = re.compile(r"^\[([^\]]+)\]\s+[^|]+\|\s*([A-Z_]+)\s*\|\s*(.+)$")
_SHOW_LEVELS = {"DECISION", "ACTION", "RESULT", "OUTPUT", "END"}

_AGENT_LOGS = [
    ("agent_1_signal_ingestion",      "Agent 1", ["agent1_trace.log"]),
    ("agent_2_crisis_detection",      "Agent 2", ["agent2_trace.log"]),
    ("agent_3_situational_awareness", "Agent 3", ["agent3_trace.log"]),
    ("agent_4_resource_dispatch",     "Agent 4", ["agent4_trace.log"]),
    ("agent_5_simulation",            "Agent 5", ["agent5_trace.log"]),
    ("agent_6_dashboard",             "Agent 6", ["agent6_trace.log"]),
]


def build_trace_summaries() -> list:
    summaries = []
    base = Path(__file__).parent.parent

    for agent_dir, short_name, log_names in _AGENT_LOGS:
        out_dir = OUTPUT_DIR if agent_dir == "agent_6_dashboard" else base / agent_dir / "output"
        content = ""
        for name in log_names:
            p = out_dir / name
            if p.exists():
                content = p.read_text(encoding="utf-8")
                break
        if not content:
            continue

        for line in content.splitlines():
            m = _LOG_RE.match(line)
            if not m:
                continue
            timestamp, level, message = m.group(1), m.group(2), m.group(3).strip()

            # Agent 6 wraps all lines under "PUSH" — extract real level from message body
            if level == "PUSH":
                inner = re.match(r"^([A-Z_]+)\s*\|\s*(.+)$", message)
                if inner:
                    level, message = inner.group(1), inner.group(2).strip()

            if level not in _SHOW_LEVELS:
                continue

            summaries.append({
                "agent": short_name,
                "key_decision": f"{short_name} | {level} | {message}",
                "timestamp": timestamp,
            })

    log(f"RESULT | Built {len(summaries)} trace summary entries from agent logs")
    return summaries


def build_dashboard_state(full_state: dict, sitrep_text: str) -> dict:
    crisis = full_state.get("crisis", {})
    trace_summaries = build_trace_summaries()

    dashboard_state = {
        "crisis_id": crisis.get("crisis_id", "CRS_20260513_001"),
        "stage": full_state.get("stage", "simulated"),
        "crisis": crisis,
        "operational_picture": full_state.get("operational_picture", {}),
        "dispatch_plan": full_state.get("dispatch_plan", {}),
        "simulation": full_state.get("simulation", {}),
        "sitrep_text": sitrep_text,
        "agent_trace_summary": trace_summaries,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return dashboard_state


def write_dashboard_state(state: dict) -> Path:
    out = OUTPUT_DIR / "dashboard_state.json"
    out.write_text(json.dumps(state, indent=2), encoding="utf-8")
    log(f"OUTPUT | dashboard_state.json written ({out})")
    return out


def post_to_backend(state: dict) -> bool:
    url = f"{BACKEND_URL}/api/crisis/complete"
    log(f"ACTION | POST {url}")
    try:
        resp = httpx.post(url, json=state, timeout=15)
        resp.raise_for_status()
        log(f"RESULT | Backend accepted — 200 OK")
        return True
    except httpx.HTTPStatusError as e:
        log(f"ERROR | Backend returned {e.response.status_code}: {e.response.text}")
        return False
    except httpx.ConnectError:
        log("ERROR | Cannot connect to backend — is it running at localhost:8000?")
        return False


def consolidate_trace_log():
    """Combine all individual agent trace logs into one submission file."""
    agents = [
        "agent_1_signal_ingestion",
        "agent_2_crisis_detection",
        "agent_3_situational_awareness",
        "agent_4_resource_dispatch",
        "agent_5_simulation",
        "agent_6_dashboard",
    ]
    combined = []
    base = Path(__file__).parent.parent

    for agent in agents:
        log_path = base / agent / "output" / f"{agent.split('_')[1]}_trace.log"
        # Try numbered format too
        for candidate in [
            log_path,
            base / agent / "output" / "agent1_trace.log",
            base / agent / "output" / "agent2_trace.log",
            base / agent / "output" / "agent3_trace.log",
            base / agent / "output" / "agent4_trace.log",
            base / agent / "output" / "agent5_trace.log",
            base / agent / "output" / "agent6_trace.log",
        ]:
            if candidate.exists():
                combined.append(f"\n# === {agent.upper()} ===\n")
                combined.append(candidate.read_text(encoding="utf-8"))
                break

    if combined:
        out = OUTPUT_DIR / "CIRO_agent_trace.log"
        out.write_text("".join(combined), encoding="utf-8")
        log(f"OUTPUT | Consolidated trace log written: {out}")


if __name__ == "__main__":
    log("START | Dashboard push initiated")

    crisis_id = sys.argv[1] if len(sys.argv) > 1 else "CRS_20260513_001"
    log(f"PROCESS | Crisis ID: {crisis_id}")

    log("TOOL_CALL | Fetching full crisis state from backend")
    try:
        full_state = fetch_full_state(crisis_id)
    except Exception as e:
        log(f"ERROR | Could not fetch full state: {e}")
        log("FALLBACK | Using empty state structure")
        full_state = {"crisis": {"crisis_id": crisis_id}, "stage": "simulated"}

    sitrep = load_sitrep()
    log(f"LOAD | SITREP loaded ({len(sitrep)} chars)")

    dashboard_state = build_dashboard_state(full_state, sitrep)
    write_dashboard_state(dashboard_state)

    success = post_to_backend(dashboard_state)
    if success:
        log("ACTION | Dashboard state pushed to backend — WebSocket broadcast triggered")
    else:
        log("WARN | Backend push failed — dashboard_state.json saved locally")

    consolidate_trace_log()
    log("END | Agent 6 complete")
