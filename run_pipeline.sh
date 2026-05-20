#!/bin/bash
# CIRO Local Pipeline Runner
#
# Usage:
#   ./run_pipeline.sh              — run all 6 agents in sequence
#   ./run_pipeline.sh --agent 3   — run only Agent 3
#   ./run_pipeline.sh --from 3    — run Agent 3 through 6
#   ./run_pipeline.sh --agent 3 --agent 5  — run agents 3 and 5
#   ./run_pipeline.sh --reset     — wipe all outputs + DB rows, then exit
#
# Prerequisites:
#   - Backend running: cd backend && uvicorn main:app --reload --port 8000
#   - Run from project root: /home/rasikh/Projects/CIRO/

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
AGENTS_DIR="$PROJECT_ROOT/agents"
PYTHON="$BACKEND_DIR/.venv/bin/python"
CRISIS_ID="CRS_20260513_001"

export CIRO_BACKEND_URL="http://localhost:8000"
export BACKEND_URL="http://localhost:8000"
export BACKEND_DIR="$BACKEND_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

step() { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }
ok()   { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
die()  { echo -e "${RED}✗ $1${NC}"; exit 1; }

# ── Argument parsing ──────────────────────────────────────────────────────────
SELECTED_AGENTS=()
FROM_AGENT=""
DO_RESET=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent|-a)
            SELECTED_AGENTS+=("$2"); shift 2 ;;
        --from|-f)
            FROM_AGENT="$2"; shift 2 ;;
        --reset|-r)
            DO_RESET=true; shift ;;
        --help|-h)
            sed -n '2,11p' "$0"; exit 0 ;;
        *)
            die "Unknown flag: $1  (use --help)" ;;
    esac
done

# ── Reset ─────────────────────────────────────────────────────────────────────
if $DO_RESET; then
    step "Reset — wiping outputs + DB"

    # Agent output files
    for dir in \
        "$AGENTS_DIR/agent_1_signal_ingestion/output" \
        "$AGENTS_DIR/agent_2_crisis_detection/output" \
        "$AGENTS_DIR/agent_3_situational_awareness/output" \
        "$AGENTS_DIR/agent_5_simulation/output" \
        "$AGENTS_DIR/agent_6_dashboard/output" \
        "$BACKEND_DIR/agents/agent_4_resource_dispatch/output" \
        "$BACKEND_DIR/agents/agent_3_situational_awareness/output"
    do
        if [[ -d "$dir" ]]; then
            rm -f "$dir"/*.json "$dir"/*.log "$dir"/*.md
            ok "Cleared $dir"
        fi
    done

    # DB rows — delete in FK order
    "$PYTHON" - <<'PYEOF'
import os, sys
sys.path.insert(0, os.environ["BACKEND_DIR"])
from dotenv import load_dotenv
load_dotenv(os.path.join(os.environ["BACKEND_DIR"], ".env"))
from app.db.session import SessionLocal
from app.models.simulation import Simulation
from app.models.dispatch import DispatchOrder
from app.models.operational_picture import OperationalPicture
from app.models.signal import Signal
from app.models.crisis import Crisis

db = SessionLocal()
counts = {}
for Model in [Simulation, DispatchOrder, OperationalPicture, Signal, Crisis]:
    n = db.query(Model).delete()
    counts[Model.__tablename__] = n
db.commit()
db.close()
for table, n in counts.items():
    print(f"  Deleted {n} rows from {table}")
PYEOF

    ok "Database cleared"
    echo -e "\n${GREEN}Reset complete — ready for a fresh run.${NC}\n"
    exit 0
fi

# Build the list of agents to run
if [[ ${#SELECTED_AGENTS[@]} -gt 0 ]]; then
    RUN_AGENTS=("${SELECTED_AGENTS[@]}")
elif [[ -n "$FROM_AGENT" ]]; then
    RUN_AGENTS=()
    for n in 1 2 3 4 5 6; do
        [[ $n -ge $FROM_AGENT ]] && RUN_AGENTS+=("$n")
    done
else
    RUN_AGENTS=(1 2 3 4 5 6)
fi

should_run() { [[ " ${RUN_AGENTS[*]} " == *" $1 "* ]]; }

# ── Preflight ─────────────────────────────────────────────────────────────────
step "Preflight"

[ -f "$PYTHON" ] || die "Backend venv not found — run: cd backend && python -m venv .venv && pip install -r requirements.txt"
curl -sf http://localhost:8000/ > /dev/null 2>&1 || die "Backend not running at localhost:8000 — start it first"
ok "Backend reachable"

"$PYTHON" -c "import requests" 2>/dev/null || {
    warn "requests not in venv — installing..."
    "$BACKEND_DIR/.venv/bin/pip" install requests -q
    ok "requests installed"
}

echo "  Running agents: ${RUN_AGENTS[*]}"

# ── Agent 1 ───────────────────────────────────────────────────────────────────
if should_run 1; then
    step "AGENT 1 — Signal Ingestion"
    cd "$AGENTS_DIR/agent_1_signal_ingestion"
    "$PYTHON" ingest.py
    ok "Agent 1 complete → output/signals.json"
fi

# ── Agent 2 ───────────────────────────────────────────────────────────────────
if should_run 2; then
    step "AGENT 2 — Crisis Detection"
    cd "$AGENTS_DIR/agent_2_crisis_detection"
    "$PYTHON" classify.py
    ok "Agent 2 complete → output/crisis.json"
fi

# ── Agent 3 ───────────────────────────────────────────────────────────────────
if should_run 3; then
    step "AGENT 3 — Situational Awareness"
    cd "$AGENTS_DIR/agent_3_situational_awareness"
    "$PYTHON" situational.py
    ok "Agent 3 complete → output/ops_pic.json"

    mkdir -p "$BACKEND_DIR/agents/agent_3_situational_awareness/output"
    cp "$AGENTS_DIR/agent_3_situational_awareness/output/ops_pic.json" \
       "$BACKEND_DIR/agents/agent_3_situational_awareness/output/ops_pic.json"
fi

# ── Agent 4 ───────────────────────────────────────────────────────────────────
if should_run 4; then
    step "AGENT 4 — Resource Dispatch"
    cd "$BACKEND_DIR/agents/agent_4_resource_dispatch"
    "$PYTHON" dispatch.py
    ok "Agent 4 complete → output/dispatch.json"
fi

# ── Agent 5 ───────────────────────────────────────────────────────────────────
if should_run 5; then
    step "AGENT 5 — Simulation & Routing"
    cd "$AGENTS_DIR/agent_5_simulation"
    "$PYTHON" simulate.py
    ok "Agent 5 complete → output/simulation.json"
fi

# ── Agent 6 ───────────────────────────────────────────────────────────────────
if should_run 6; then
    step "AGENT 6 — Dashboard Push"
    cd "$AGENTS_DIR/agent_6_dashboard"
    "$PYTHON" sitrep_generator.py
    "$PYTHON" push_to_backend.py "$CRISIS_ID"
    ok "Agent 6 complete → dashboard state pushed"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}━━━ Done (agents: ${RUN_AGENTS[*]}) ━━━${NC}"
echo "  Crisis ID : $CRISIS_ID"
echo "  Dashboard : http://localhost:5173"
echo "  API check : curl http://localhost:8000/api/crisis/full/$CRISIS_ID"
echo ""
