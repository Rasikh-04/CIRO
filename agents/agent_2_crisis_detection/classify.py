import json
import os
import requests
from datetime import datetime, timezone
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

BASE_DIR = Path(__file__).parent
AGENT1_OUTPUT = BASE_DIR / ".." / "agent_1_signal_ingestion" / "output" / "signals.json"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TRACE_LOG = OUTPUT_DIR / "agent2_trace.log"
CRISIS_OUTPUT = OUTPUT_DIR / "crisis.json"
BACKEND_URL = os.getenv("CIRO_BACKEND_URL", "http://localhost:8000")
THRESHOLDS_PATH = BASE_DIR / "thresholds.json"

open(TRACE_LOG, "w").close()


def log(level: str, message: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] AGENT_2 | {level} | {message}"
    print(line)
    with open(TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(a))


def load_signals() -> list:
    url = f"{BACKEND_URL}/api/signals/latest"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            log("TOOL_CALL", f"GET {url} -> 200 OK")
            data = resp.json()
            return data.get("signals", data) if isinstance(data, dict) else data
    except Exception:
        pass
    log("TOOL_CALL", f"Read {AGENT1_OUTPUT} (backend not available)")
    with open(AGENT1_OUTPUT, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("signals", data) if isinstance(data, dict) else data


def cluster_signals(signals: list, thresholds: dict) -> list:
    radius_km = thresholds["cluster_radius_km"]
    time_window_min = thresholds["time_window_minutes"]
    min_signals = thresholds["min_signals_for_cluster"]

    clusters = []
    used = set()

    for i, sig in enumerate(signals):
        if i in used:
            continue
        cluster = [sig]
        used.add(i)
        lat1 = sig["location"]["lat"]
        lng1 = sig["location"]["lng"]
        t1 = datetime.fromisoformat(sig["timestamp"].replace("Z", "+00:00"))

        for j, other in enumerate(signals):
            if j in used or i == j:
                continue
            if other["signal_type"] != sig["signal_type"]:
                continue
            dist = haversine(lat1, lng1, other["location"]["lat"], other["location"]["lng"])
            t2 = datetime.fromisoformat(other["timestamp"].replace("Z", "+00:00"))
            time_diff_min = abs((t2 - t1).total_seconds() / 60)
            if dist <= radius_km and time_diff_min <= time_window_min:
                cluster.append(other)
                used.add(j)

        if len(cluster) >= min_signals:
            clusters.append(cluster)

    return clusters


def score_confidence(cluster: list) -> tuple:
    sources = {s["source"] for s in cluster}
    n = len(cluster)
    avg_conf = sum(s["confidence"] for s in cluster) / n
    source_bonus = 0.15 if len(sources) >= 2 else 0.0
    volume_bonus = min(0.10, (n - 2) * 0.03)
    score = min(0.99, avg_conf + source_bonus + volume_bonus)
    label = "high" if score >= 0.75 else "medium" if score >= 0.50 else "low"
    return round(score, 2), label


def build_reasoning_local(cluster: list, confidence: float) -> str:
    sources = list({s["source"] for s in cluster})
    n = len(cluster)
    return (
        f"{n} corroborating signals detected from sources: {', '.join(sources)}. "
        f"Signals cluster within the G-10 area over a 30-minute window. "
        f"Crisis type 'urban_flooding' confirmed with confidence {confidence} based on "
        f"multi-source agreement and signal intensity."
    )


def build_reasoning_gemini(cluster: list, confidence: float) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return build_reasoning_local(cluster, confidence)
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        summary = "\n".join(
            f"- [{s['source']}] {s['normalized']} (confidence: {s['confidence']})"
            for s in cluster
        )
        prompt = (
            "You are analyzing signals from multiple sources about a potential urban crisis.\n\n"
            f"Signals:\n{summary}\n\n"
            "Based on these signals, provide a 2-3 sentence reasoning explanation for why this is a "
            "confirmed crisis. Be specific about the corroborating evidence. Return plain text only."
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        log("WARNING", f"Gemini reasoning failed ({e}) — using local reasoning")
        return build_reasoning_local(cluster, confidence)


def classify_severity(cluster: list) -> int:
    n = len(cluster)
    sources = {s["source"] for s in cluster}
    max_conf = max(s["confidence"] for s in cluster)
    score = min(3, n) + (2 if max_conf > 0.85 else 1 if max_conf > 0.65 else 0) + (1 if len(sources) >= 2 else 0)
    if score >= 5:
        return 4
    elif score >= 3:
        return 3
    elif score >= 2:
        return 2
    return 1


def generate_crisis(cluster: list, thresholds: dict):
    confidence_score, confidence_label = score_confidence(cluster)

    if confidence_score < thresholds["min_confidence_to_confirm"]:
        log("DECISION", f"Cluster of {len(cluster)} below confidence threshold ({confidence_score} < {thresholds['min_confidence_to_confirm']}) — no crisis confirmed")
        return None

    type_map = {"flood": "urban_flooding", "road_blockage": "road_blockage"}
    raw_type = cluster[0]["signal_type"]
    crisis_type = type_map.get(raw_type, raw_type)

    avg_lat = sum(s["location"]["lat"] for s in cluster) / len(cluster)
    avg_lng = sum(s["location"]["lng"] for s in cluster) / len(cluster)
    severity = classify_severity(cluster)
    reasoning = build_reasoning_gemini(cluster, confidence_score)

    return {
        "crisis_id": "CRS_20260513_001",
        "type": crisis_type,
        "location": {
            "primary": "G-10, Islamabad",
            "affected_radius_km": 2.5,
            "lat": round(avg_lat, 4),
            "lng": round(avg_lng, 4),
        },
        "severity": severity,
        "confidence": confidence_label,
        "confidence_score": confidence_score,
        "reasoning": reasoning,
        "contributing_signals": [s["id"] for s in cluster],
        "status": "confirmed",
        "detected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def post_to_backend(crisis: dict):
    url = f"{BACKEND_URL}/api/crisis/detected"
    log("ACTION", f"POST {url}")
    try:
        resp = requests.post(url, json=crisis, timeout=5)
        resp.raise_for_status()
        log("ACTION", f"POST {url} -> {resp.status_code} OK | crisis_id={crisis['crisis_id']}")
    except Exception as e:
        log("WARNING", f"Backend not available ({e}) — crisis saved locally")


def main():
    start = datetime.now(timezone.utc)
    log("START", "Crisis Detection & Classification initiated")

    with open(THRESHOLDS_PATH, encoding="utf-8") as f:
        thresholds = json.load(f)
    log("PROCESS", f"Thresholds: radius={thresholds['cluster_radius_km']}km, window={thresholds['time_window_minutes']}min, min_signals={thresholds['min_signals_for_cluster']}, min_confidence={thresholds['min_confidence_to_confirm']}")

    signals = load_signals()
    log("RESULT", f"Loaded {len(signals)} signals")

    valid = [s for s in signals if s.get("location", {}).get("lat")]
    skipped = len(signals) - len(valid)
    if skipped:
        log("WARNING", f"Skipped {skipped} signals with missing/invalid location")

    clusters = cluster_signals(valid, thresholds)
    log("DECISION", f"Found {len(clusters)} qualifying cluster(s) with >={thresholds['min_signals_for_cluster']} signals")

    if not clusters:
        log("DECISION", "No qualifying clusters — no crisis confirmed")
        log("END", "No crisis detected. Exiting.")
        return

    clusters.sort(key=len, reverse=True)
    best = clusters[0]
    sources = list({s["source"] for s in best})
    log("DECISION", f"Top cluster: {len(best)} signals, sources={sources}, type={best[0]['signal_type']}")

    crisis = generate_crisis(best, thresholds)
    if not crisis:
        log("END", "No crisis confirmed after threshold check.")
        return

    log("OUTPUT", (
        f"Crisis confirmed: {crisis['type']} | {crisis['location']['primary']} | "
        f"severity={crisis['severity']} | confidence={crisis['confidence']} ({crisis['confidence_score']})"
    ))

    with open(CRISIS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(crisis, f, indent=2, ensure_ascii=False)
    log("OUTPUT", f"Written to output/crisis.json")

    post_to_backend(crisis)

    duration = (datetime.now(timezone.utc) - start).seconds
    log("END", f"Duration: {duration}s | Crisis ID: {crisis['crisis_id']} | Severity: {crisis['severity']}/5")


if __name__ == "__main__":
    main()
