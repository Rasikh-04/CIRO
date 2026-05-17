"""
CIRO — Minimal Mock Backend
Stdlib-only (no FastAPI/SQLAlchemy/PostGIS required).
Handles exactly the 5 endpoints Tabeen's agents call.
Run: py -3.11 backend/mock_server.py [--port 8000]

Storage: SQLite in backend/mock_ciro.db (auto-created).
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


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

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
                timestamp   TEXT,
                source_label TEXT,
                ingested_at TEXT
            );
            CREATE TABLE IF NOT EXISTS crises (
                crisis_id       TEXT PRIMARY KEY,
                type            TEXT,
                location_name   TEXT,
                affected_radius REAL,
                lat             REAL,
                lng             REAL,
                severity        INTEGER,
                confidence      TEXT,
                confidence_score REAL,
                reasoning       TEXT,
                contributing_signals TEXT,
                status          TEXT,
                detected_at     TEXT
            );
            CREATE TABLE IF NOT EXISTS ops_pics (
                crisis_id    TEXT PRIMARY KEY,
                payload      TEXT,
                generated_at TEXT
            );
        """)


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] {self.address_string()} {fmt % args}")

    def _send_json(self, code: int, data: dict):
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

    # ---- GET ---------------------------------------------------------------

    def do_GET(self):
        p = self._path()

        if p == "/api/signals/latest":
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 50"
                ).fetchall()
            signals = []
            for r in rows:
                signals.append({
                    "id": r["id"], "source": r["source"],
                    "raw_text": r["raw_text"], "normalized": r["normalized"],
                    "location": {
                        "district": r["district"], "city": r["city"],
                        "lat": r["lat"], "lng": r["lng"],
                    },
                    "signal_type": r["signal_type"],
                    "timestamp": r["timestamp"],
                    "confidence": r["confidence"],
                    "source_label": r["source_label"],
                })
            self._send_json(200, {"signals": signals})

        elif p == "/api/crisis/latest":
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM crises ORDER BY detected_at DESC LIMIT 1"
                ).fetchone()
            if not row:
                self._send_json(404, {"detail": "No crisis found"})
                return
            self._send_json(200, {
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
            })

        elif p == "/api/crisis/active":
            with get_conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM crises WHERE status != 'resolved' ORDER BY detected_at DESC"
                ).fetchall()
            self._send_json(200, [
                {
                    "crisis_id": r["crisis_id"], "type": r["type"],
                    "location_name": r["location_name"],
                    "severity": r["severity"], "stage": r["status"],
                    "detected_at": r["detected_at"],
                }
                for r in rows
            ])

        elif p in ("/", ""):
            self._send_json(200, {"status": "CIRO mock backend running"})

        else:
            self._send_json(404, {"detail": f"Not found: {p}"})

    # ---- POST --------------------------------------------------------------

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
                    """INSERT OR REPLACE INTO crises
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
                        body.get("status", "detected"),
                        str(body.get("detected_at", "")),
                    )
                )
            self._send_json(200, {"crisis_id": body["crisis_id"]})

        elif p == "/api/crisis/operational":
            crisis_id = body.get("crisis_id", "")
            with get_conn() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO ops_pics (crisis_id, payload, generated_at)
                       VALUES (?,?,?)""",
                    (crisis_id, json.dumps(body),
                     str(body.get("generated_at", datetime.now(timezone.utc).isoformat())))
                )
            self._send_json(200, {"crisis_id": crisis_id, "status": "ok"})

        else:
            self._send_json(404, {"detail": f"Not found: {p}"})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    port = PORT
    for i, arg in enumerate(sys.argv[1:]):
        if arg in ("--port", "-p") and i + 1 < len(sys.argv) - 1:
            port = int(sys.argv[i + 2])

    init_db()
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[CIRO Mock Backend] Listening on http://localhost:{port}")
    print(f"[CIRO Mock Backend] DB: {DB_PATH}")
    print("[CIRO Mock Backend] Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CIRO Mock Backend] Stopped.")


if __name__ == "__main__":
    main()
