"""
CIRO — Minimal Mock Backend
Stdlib-only (no FastAPI/SQLAlchemy/PostGIS required).
Handles all endpoints the agents and web/mobile frontends call.
Run: py -3.11 backend/mock_server.py [--port 8000]

Storage: SQLite in backend/mock_ciro.db (auto-created).
Note: WebSocket is not supported in this mock — the dashboard falls back to
30-second HTTP polling. Use the FastAPI backend for real-time WebSocket updates.
"""
import json
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

DB_PATH = Path(__file__).parent / "mock_ciro.db"
PORT = 8000


# ── Pre-baked scenario data (mirrors demo.py) ─────────────────────────────────

_TS = "2026-05-13T14:30:00Z"

_SCENARIOS: dict = {
    "g10_flood": {
        "crisis_id": "CRS_20260513_001", "type": "urban_flooding",
        "location_name": "G-10, Islamabad", "affected_radius": 2.5,
        "lat": 33.6844, "lng": 73.0479,
        "severity": 4, "confidence_label": "high", "confidence_score": 0.89,
        "reasoning": (
            "Multi-source confirmation: 8 social media posts report active flooding in G-10, "
            "heavy rainfall (12 mm) from Open-Meteo, and severe congestion on Srinagar Highway."
        ),
        "signals": [
            {"id": "sig_demo_g10_01", "source": "social_media",
             "raw_text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
             "normalized": "G-10: flood — vehicles trapped, water rising",
             "signal_type": "flood", "district": "G-10", "city": "Islamabad",
             "lat": 33.6844, "lng": 73.0479, "confidence": 0.82},
            {"id": "sig_demo_g10_02", "source": "social_media",
             "raw_text": "Flash flood at G-10, roads completely blocked",
             "normalized": "G-10: flood — roads blocked",
             "signal_type": "flood", "district": "G-10", "city": "Islamabad",
             "lat": 33.6844, "lng": 73.0479, "confidence": 0.85},
            {"id": "sig_demo_g10_03", "source": "weather",
             "raw_text": "precipitation=12.0mm, weathercode=95",
             "normalized": "Heavy rainfall: 12 mm precipitation, thunderstorm",
             "signal_type": "flood", "district": "G-10", "city": "Islamabad",
             "lat": 33.6844, "lng": 73.0479, "confidence": 0.95},
            {"id": "sig_demo_g10_04", "source": "traffic",
             "raw_text": "Srinagar Highway: 10 km/h (normal 70 km/h)",
             "normalized": "Srinagar Highway: severe congestion (flooding)",
             "signal_type": "flood", "district": "G-10", "city": "Islamabad",
             "lat": 33.6880, "lng": 73.0550, "confidence": 0.88},
        ],
        "road_closures": [
            {"road": "Srinagar Highway", "status": "blocked",
             "lat": 33.6880, "lng": 73.0550, "source": "traffic_api"},
            {"road": "Khayaban-e-Iqbal", "status": "partial",
             "lat": 33.6830, "lng": 73.0460, "source": "simulated"},
        ],
        "nearby_facilities": [
            {"type": "rescue_unit", "name": "F-8 Rescue Unit Alpha",
             "lat": 33.7080, "lng": 73.0479, "distance_km": 2.62, "status": "available"},
            {"type": "hospital", "name": "PIMS Hospital",
             "lat": 33.7161, "lng": 73.0738, "distance_km": 4.97, "status": "available"},
            {"type": "fire_station", "name": "Sector F-7 Fire Station",
             "lat": 33.7200, "lng": 73.0500, "distance_km": 3.91, "status": "available"},
        ],
        "population_at_risk": 12000,
    },
    "i8_heat": {
        "crisis_id": "CRS_20260513_002", "type": "heatwave",
        "location_name": "I-8, Islamabad", "affected_radius": 3.0,
        "lat": 33.6560, "lng": 73.0717,
        "severity": 3, "confidence_label": "medium", "confidence_score": 0.76,
        "reasoning": (
            "5 corroborating signals: social media reports of heat exhaustion, "
            "Met Office red alert 48 °C, PIMS emergency ward at capacity."
        ),
        "signals": [
            {"id": "sig_demo_heat_01", "source": "social_media",
             "raw_text": "I-8 mein garmi se 3 log behosh ho gaye, PIMS emergency bhar gaya",
             "normalized": "I-8: heatwave — 3 unconscious, PIMS full",
             "signal_type": "heatwave", "district": "I-8", "city": "Islamabad",
             "lat": 33.6560, "lng": 73.0717, "confidence": 0.85},
            {"id": "sig_demo_heat_02", "source": "social_media",
             "raw_text": "Temperature in I-8 hit 48°C. Multiple heat stroke cases.",
             "normalized": "I-8: heatwave — 48°C, heat stroke cases",
             "signal_type": "heatwave", "district": "I-8", "city": "Islamabad",
             "lat": 33.6560, "lng": 73.0717, "confidence": 0.82},
            {"id": "sig_demo_heat_03", "source": "weather",
             "raw_text": "Met Office: Islamabad 48°C red alert, I-8 extreme heat",
             "normalized": "Met Office: 48°C red alert for I-8",
             "signal_type": "heatwave", "district": "I-8", "city": "Islamabad",
             "lat": 33.6560, "lng": 73.0717, "confidence": 0.95},
        ],
        "road_closures": [],
        "nearby_facilities": [
            {"type": "hospital", "name": "PIMS Hospital",
             "lat": 33.7161, "lng": 73.0738, "distance_km": 6.62, "status": "unavailable"},
            {"type": "rescue_unit", "name": "I-8 Rescue Station",
             "lat": 33.6580, "lng": 73.0680, "distance_km": 0.42, "status": "available"},
            {"type": "depot", "name": "NDMA Water Point I-8",
             "lat": 33.6540, "lng": 73.0720, "distance_km": 0.22, "status": "deployed"},
        ],
        "population_at_risk": 18500,
    },
    "f10_accident": {
        "crisis_id": "CRS_20260513_003", "type": "road_blockage",
        "location_name": "F-10 / Kashmir Highway, Islamabad", "affected_radius": 1.5,
        "lat": 33.6938, "lng": 72.9827,
        "severity": 3, "confidence_label": "high", "confidence_score": 0.84,
        "reasoning": (
            "4 corroborating reports of a multi-vehicle pile-up on Kashmir Highway near F-10. "
            "Islamabad Traffic Police confirmed closure in both directions."
        ),
        "signals": [
            {"id": "sig_demo_acc_01", "source": "social_media",
             "raw_text": "Kashmir Highway F-10 interchange par badi accident, 6 gaadiyaan takra gayi",
             "normalized": "F-10/Kashmir Highway: 6-vehicle pile-up",
             "signal_type": "road_blockage", "district": "F-10", "city": "Islamabad",
             "lat": 33.6938, "lng": 72.9827, "confidence": 0.86},
            {"id": "sig_demo_acc_02", "source": "social_media",
             "raw_text": "Major pile-up on Kashmir Highway near F-10, avoid area, 5km backup",
             "normalized": "F-10/Kashmir Highway: road blocked, 5 km backup",
             "signal_type": "road_blockage", "district": "F-10", "city": "Islamabad",
             "lat": 33.6938, "lng": 72.9827, "confidence": 0.88},
            {"id": "sig_demo_acc_03", "source": "traffic",
             "raw_text": "Kashmir Highway F-10: 0 km/h — accident closure",
             "normalized": "Kashmir Highway standstill: accident closure F-10",
             "signal_type": "road_blockage", "district": "F-10", "city": "Islamabad",
             "lat": 33.6938, "lng": 72.9827, "confidence": 0.92},
        ],
        "road_closures": [
            {"road": "Kashmir Highway (F-10 Interchange)", "status": "blocked",
             "lat": 33.6938, "lng": 72.9827, "source": "traffic_api"},
            {"road": "Kashmir Highway Westbound Approach", "status": "partial",
             "lat": 33.6960, "lng": 72.9780, "source": "simulated"},
        ],
        "nearby_facilities": [
            {"type": "hospital", "name": "F-10 Civil Hospital",
             "lat": 33.6940, "lng": 72.9760, "distance_km": 0.54, "status": "available"},
            {"type": "rescue_unit", "name": "Rescue 1122 F-10",
             "lat": 33.6900, "lng": 72.9850, "distance_km": 0.48, "status": "deployed"},
        ],
        "population_at_risk": 4800,
    },
}


# ── Database ──────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS signals (
                id          TEXT PRIMARY KEY,
                source      TEXT,
                raw_text    TEXT,
                normalized  TEXT,
                signal_type TEXT,
                district    TEXT,
                city        TEXT,
                lat         REAL,
                lng         REAL,
                confidence  REAL,
                source_label TEXT,
                timestamp   TEXT,
                ingested_at TEXT
            );
            CREATE TABLE IF NOT EXISTS crises (
                crisis_id            TEXT PRIMARY KEY,
                type                 TEXT,
                location_name        TEXT,
                affected_radius      REAL,
                lat                  REAL,
                lng                  REAL,
                severity             INTEGER,
                confidence           TEXT,
                confidence_score     REAL,
                reasoning            TEXT,
                contributing_signals TEXT,
                status               TEXT,
                detected_at          TEXT
            );
            CREATE TABLE IF NOT EXISTS ops_pics (
                crisis_id    TEXT PRIMARY KEY,
                payload      TEXT,
                generated_at TEXT
            );
        """)


# ── Handler ───────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] {self.address_string()} {fmt % args}")

    def _send_json(self, code: int, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _path(self):
        return urlparse(self.path).path.rstrip("/")

    # ── GET ──────────────────────────────────────────────────────────────────

    def do_GET(self):
        p = self._path()

        if p == "/api/signals/latest":
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 50"
                ).fetchall()
            self._send_json(200, {"signals": [
                {
                    "id": r["id"], "source": r["source"],
                    "raw_text": r["raw_text"], "normalized": r["normalized"],
                    "location": {
                        "district": r["district"], "city": r["city"],
                        "lat": r["lat"], "lng": r["lng"],
                    },
                    "signal_type": r["signal_type"],
                    "timestamp": r["timestamp"],
                    "confidence": r["confidence"],
                    "source_label": r["source_label"] or "simulated",
                }
                for r in rows
            ]})

        elif p == "/api/crisis/latest":
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM crises ORDER BY detected_at DESC LIMIT 1"
                ).fetchone()
            if not row:
                self._send_json(404, {"detail": "No crisis found"})
                return
            self._send_json(200, self._format_crisis(row))

        elif p == "/api/crisis/active":
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM crises WHERE status != 'resolved' ORDER BY detected_at DESC"
                ).fetchall()
            self._send_json(200, [
                {
                    "crisis_id":     r["crisis_id"],
                    "type":          r["type"],
                    "location_name": r["location_name"],
                    "severity":      r["severity"],
                    "stage":         r["status"],
                    "detected_at":   r["detected_at"],
                }
                for r in rows
            ])

        elif p.startswith("/api/crisis/") and p.endswith("/safe-routes"):
            crisis_id = p[len("/api/crisis/"):-len("/safe-routes")]
            self._send_json(200, {"routes": [
                {
                    "route_id": f"{crisis_id}_r1",
                    "name": "Margalla Road (Alternate)",
                    "distance_km": 4.8,
                    "eta_minutes": 12,
                    "risk_level": "low",
                    "waypoints": [
                        {"lat": 33.6844, "lng": 73.0479},
                        {"lat": 33.7000, "lng": 73.0465},
                        {"lat": 33.7200, "lng": 73.0450},
                    ],
                },
                {
                    "route_id": f"{crisis_id}_r2",
                    "name": "Karakoram Highway Detour",
                    "distance_km": 7.2,
                    "eta_minutes": 18,
                    "risk_level": "low",
                    "waypoints": [
                        {"lat": 33.6844, "lng": 73.0479},
                        {"lat": 33.6900, "lng": 73.0300},
                        {"lat": 33.7100, "lng": 73.0200},
                    ],
                },
            ]})

        elif p.startswith("/api/crisis/full/"):
            crisis_id = p[len("/api/crisis/full/"):]
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM crises WHERE crisis_id = ?", (crisis_id,)
                ).fetchone()
                ops_row = conn.execute(
                    "SELECT * FROM ops_pics WHERE crisis_id = ?", (crisis_id,)
                ).fetchone()
            if not row:
                self._send_json(404, {"detail": "Crisis not found"})
                return
            crisis_data = self._format_crisis(row)
            ops_data = None
            if ops_row:
                payload = json.loads(ops_row["payload"])
                ops_data = {
                    "crisis_id": crisis_id,
                    "operational_picture": payload.get("operational_picture", {}),
                    "generated_at": ops_row["generated_at"],
                }
            stage = row["status"]
            if stage == "detected" and ops_row:
                stage = "analyzed"
            self._send_json(200, {
                "crisis_id":           crisis_id,
                "stage":               stage,
                "crisis":              crisis_data,
                "operational_picture": ops_data,
                "dispatch_plan":       None,
                "simulation":          None,
                "sitrep_text":         "",
                "agent_trace_summary": [],
                "last_updated":        row["detected_at"],
            })

        elif p in ("/", ""):
            self._send_json(200, {"status": "CIRO mock backend running"})

        else:
            self._send_json(404, {"detail": f"Not found: {p}"})

    # ── POST ─────────────────────────────────────────────────────────────────

    def do_POST(self):
        p = self._path()
        body = self._read_body()

        if p == "/api/signals/ingest":
            signals = body.get("signals", [])
            count = 0
            with get_conn() as conn:
                for sig in signals:
                    loc = sig.get("location", {})
                    try:
                        conn.execute(
                            """INSERT OR IGNORE INTO signals
                               (id, source, raw_text, normalized, signal_type,
                                district, city, lat, lng, confidence, timestamp,
                                source_label, ingested_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (
                                sig["id"], sig["source"],
                                sig.get("raw_text", ""), sig.get("normalized", ""),
                                sig.get("signal_type", ""),
                                loc.get("district", ""), loc.get("city", ""),
                                loc.get("lat", 0.0), loc.get("lng", 0.0),
                                sig.get("confidence", 0.0),
                                str(sig.get("timestamp", "")),
                                sig.get("source_label", "simulated"),
                                datetime.now(timezone.utc).isoformat(),
                            )
                        )
                        count += 1
                    except Exception as e:
                        print(f"  skip {sig.get('id')}: {e}")
            self._send_json(200, {"accepted": count})

        elif p == "/api/crisis/detected":
            loc = body.get("location", {})
            with get_conn() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO crises
                       (crisis_id, type, location_name, affected_radius, lat, lng,
                        severity, confidence, confidence_score, reasoning,
                        contributing_signals, status, detected_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        body["crisis_id"], body["type"],
                        loc.get("primary", ""), loc.get("affected_radius_km", 0),
                        loc.get("lat", 0.0), loc.get("lng", 0.0),
                        body.get("severity", 0), body.get("confidence", "low"),
                        body.get("confidence_score", 0.0), body.get("reasoning", ""),
                        json.dumps(body.get("contributing_signals", [])),
                        "detected",
                        str(body.get("detected_at", "")),
                    )
                )
            self._send_json(200, {"crisis_id": body["crisis_id"]})

        elif p == "/api/crisis/operational":
            crisis_id = body.get("crisis_id", "")
            now = datetime.now(timezone.utc).isoformat()
            with get_conn() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO ops_pics (crisis_id, payload, generated_at)
                       VALUES (?,?,?)""",
                    (crisis_id, json.dumps(body), str(body.get("generated_at", now)))
                )
                # Advance status
                conn.execute(
                    "UPDATE crises SET status='analyzed' WHERE crisis_id=? AND status='detected'",
                    (crisis_id,)
                )
            self._send_json(200, {"crisis_id": crisis_id, "status": "ok"})

        elif p.startswith("/api/crisis/") and p.endswith("/user-intent"):
            self._send_json(200, {"status": "ok"})

        elif p == "/api/demo/trigger":
            scenario_name = body.get("scenario", "g10_flood")
            s = _SCENARIOS.get(scenario_name)
            if not s:
                self._send_json(400, {
                    "error": f"Unknown scenario '{scenario_name}'. Valid: {list(_SCENARIOS)}"
                })
                return
            now = datetime.now(timezone.utc).isoformat()
            crisis_id = s["crisis_id"]
            with get_conn() as conn:
                # signals
                for sig in s["signals"]:
                    try:
                        conn.execute(
                            """INSERT OR IGNORE INTO signals
                               (id, source, raw_text, normalized, signal_type,
                                district, city, lat, lng, confidence, timestamp,
                                source_label, ingested_at)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (
                                sig["id"], sig["source"], sig["raw_text"],
                                sig["normalized"], sig["signal_type"],
                                sig["district"], sig["city"],
                                sig["lat"], sig["lng"], sig["confidence"],
                                _TS, "simulated", now,
                            )
                        )
                    except Exception as e:
                        print(f"  demo signal skip {sig['id']}: {e}")
                # crisis
                conn.execute(
                    """INSERT OR IGNORE INTO crises
                       (crisis_id, type, location_name, affected_radius, lat, lng,
                        severity, confidence, confidence_score, reasoning,
                        contributing_signals, status, detected_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        crisis_id, s["type"], s["location_name"], s["affected_radius"],
                        s["lat"], s["lng"], s["severity"],
                        s["confidence_label"], s["confidence_score"], s["reasoning"],
                        json.dumps([sig["id"] for sig in s["signals"]]),
                        "analyzed", now,
                    )
                )
                # ops_pic
                ops_payload = {
                    "crisis_id": crisis_id,
                    "operational_picture": {
                        "affected_zone": {"center": [s["lat"], s["lng"]], "radius_km": s["affected_radius"]},
                        "road_closures":     s["road_closures"],
                        "nearby_facilities": s["nearby_facilities"],
                        "data_gaps":         [],
                        "population_at_risk": s["population_at_risk"],
                    },
                    "generated_at": now,
                }
                conn.execute(
                    """INSERT OR IGNORE INTO ops_pics (crisis_id, payload, generated_at)
                       VALUES (?,?,?)""",
                    (crisis_id, json.dumps(ops_payload), now)
                )
            self._send_json(200, {
                "crisis_id": crisis_id,
                "scenario": scenario_name,
                "status": "ok",
            })

        else:
            self._send_json(404, {"detail": f"Not found: {p}"})

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _format_crisis(self, row) -> dict:
        return {
            "crisis_id": row["crisis_id"],
            "type": row["type"],
            "location": {
                "primary": row["location_name"],
                "affected_radius_km": row["affected_radius"],
                "lat": row["lat"], "lng": row["lng"],
            },
            "severity": row["severity"],
            "confidence": row["confidence"],
            "confidence_score": row["confidence_score"],
            "reasoning": row["reasoning"],
            "contributing_signals": json.loads(row["contributing_signals"] or "[]"),
            "status": row["status"],
            "detected_at": row["detected_at"],
        }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    port = PORT
    for i, arg in enumerate(sys.argv[1:]):
        if arg in ("--port", "-p") and i + 1 < len(sys.argv) - 1:
            port = int(sys.argv[i + 2])

    init_db()
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[CIRO Mock Backend] Listening on http://localhost:{port}")
    print(f"[CIRO Mock Backend] DB: {DB_PATH}")
    print(f"[CIRO Mock Backend] Scenarios: {list(_SCENARIOS)}")
    print("[CIRO Mock Backend] Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CIRO Mock Backend] Stopped.")


if __name__ == "__main__":
    main()
