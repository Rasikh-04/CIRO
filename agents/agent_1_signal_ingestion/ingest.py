import argparse
import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR    = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

TRACE_LOG      = OUTPUT_DIR / "agent1_trace.log"
SIGNALS_OUTPUT = OUTPUT_DIR / "signals.json"
BACKEND_URL    = os.getenv("CIRO_BACKEND_URL", "http://localhost:8000")

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=33.6844&longitude=73.0479"
    "&current=precipitation,weathercode"
    "&timezone=Asia%2FKarachi"
)

open(TRACE_LOG, "w").close()


def load_scenario(name: str) -> dict:
    path = (BASE_DIR / ".." / "scenarios" / f"{name}.json").resolve()
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def log(level: str, message: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] AGENT_1 | {level} | {message}"
    print(line)
    with open(TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _local_extract(text: str, location: dict) -> dict:
    t = text.lower()

    flood_kw = ["pani", "flood", "baarish", "doob", "paani", "bhar gaya", "flooded", "naali toot"]
    road_kw  = ["road", "highway", "band", "blocked", "jam", "divert", "traffic"]
    heat_kw  = ["garmi", "heat", "heatwave", "garam", "temperature", "behosh", "collapsed", "heat stroke"]

    if any(k in t for k in heat_kw):
        crisis_type = "heatwave"
    elif any(k in t for k in flood_kw):
        crisis_type = "flood"
    elif any(k in t for k in road_kw):
        crisis_type = "road_blockage"
    else:
        crisis_type = "flood"

    sarcasm   = any(k in t for k in ["lol", "as usual", "nothing new", "so '", "dramatic"])
    unrelated = any(k in t for k in ["cricket", "match", "jeet", "acha tha"])
    confidence = 0.25 if unrelated else 0.30 if sarcasm else 0.82

    district   = location["district"]
    loc_lower  = district.lower().replace("-", "")
    if loc_lower in t or district.lower() in t:
        detected_location = district
    else:
        detected_location = district  # default to scenario location

    normalized = f"{detected_location}: {crisis_type} reported — {text[:80].strip()}"
    return {
        "normalized":  normalized,
        "location":    detected_location,
        "crisis_type": crisis_type,
        "confidence":  confidence,
    }


def normalize_post(post: dict, location: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-pro")
            prompt = (
                "Normalize this social media post into English. Extract:\n"
                "1. Location (district/area name in Islamabad)\n"
                "2. Crisis type: flood | heatwave | accident | road_blockage | infrastructure_failure\n"
                "3. Key details\n\n"
                'Return ONLY valid JSON: {"normalized":"...","location":"...","crisis_type":"...","confidence":0.0}\n\n'
                f'Post: "{post["text"]}"'
            )
            resp = model.generate_content(prompt)
            raw = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(raw)
        except Exception as e:
            log("WARNING", f"Gemini call failed ({e}) — using local extraction")
    return _local_extract(post["text"], location)


def fetch_weather() -> dict:
    log("TOOL_CALL", "browser -> Open-Meteo API")
    try:
        resp = requests.get(OPEN_METEO_URL, timeout=10)
        resp.raise_for_status()
        current = resp.json().get("current", {})
        result = {
            "precipitation_mm": current.get("precipitation", 0),
            "weather_code":     current.get("weathercode", 0),
            "source":           "real",
        }
        log("RESULT", f"weather: precipitation={result['precipitation_mm']}mm, code={result['weather_code']}")
        return result
    except Exception as e:
        log("WARNING", f"Open-Meteo failed ({e}) — using simulated weather")
        return {"precipitation_mm": 12.0, "weather_code": 95, "source": "simulated"}


def weather_to_signal(w: dict, location: dict):
    if w["weather_code"] >= 80 or w["precipitation_mm"] > 5:
        signal_type = "flood" if w["precipitation_mm"] > 8 else "road_blockage"
        return {
            "id":     "sig_weather_001",
            "source": "weather",
            "raw_text": f"precipitation={w['precipitation_mm']}mm, weathercode={w['weather_code']}",
            "normalized": (
                f"Heavy rainfall alert: {w['precipitation_mm']}mm precipitation, "
                f"weather code {w['weather_code']} (storm/heavy rain)"
            ),
            "location": {
                "district": location["district"],
                "city":     "Islamabad",
                "lat":      location["lat"],
                "lng":      location["lng"],
            },
            "signal_type": signal_type,
            "timestamp":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "confidence":  0.95,
            "source_label": w["source"],
        }
    return None


def traffic_to_signals(traffic_data: dict, location: dict) -> list:
    signals = []
    for i, road in enumerate(traffic_data.get("traffic_data", [])):
        if road["congestion_level"] not in ("severe", "moderate"):
            continue
        signals.append({
            "id":     f"sig_traffic_{i+1:03d}",
            "source": "traffic",
            "raw_text": f"{road['road']}: speed {road['speed_kmh']}km/h (normal {road['normal_speed_kmh']}km/h)",
            "normalized": (
                f"Traffic congestion on {road['road']}: {road['congestion_level']} "
                f"({road.get('incident_type', 'congestion')})"
            ),
            "location": {
                "district": location["district"],
                "city":     "Islamabad",
                "lat":      road["lat"],
                "lng":      road["lng"],
            },
            "signal_type": "flood" if road.get("incident_type") == "flooding" else "road_blockage",
            "timestamp":   traffic_data["timestamp"],
            "confidence":  0.88 if road["congestion_level"] == "severe" else 0.65,
            "source_label": "simulated",
        })
    return signals


def process_social_posts(posts: list, location: dict) -> list:
    signals = []
    log("PROCESS", f"Normalizing {len(posts)} social media posts")
    for post in posts:
        result = normalize_post(post, location)
        if result["confidence"] < 0.4:
            log("DECISION", f"Skipped {post['id']}: low confidence ({result['confidence']}) — unrelated or sarcastic")
            continue
        signal = {
            "id":     f"sig_{post['id']}",
            "source": "social_media",
            "raw_text":   post["text"],
            "normalized": result["normalized"],
            "location": {
                "district": result.get("location", location["district"]),
                "city":     "Islamabad",
                "lat":      location["lat"],
                "lng":      location["lng"],
            },
            "signal_type": result.get("crisis_type", location.get("crisis_type", "flood")),
            "timestamp":   post["timestamp"],
            "confidence":  result["confidence"],
            "source_label": "simulated",
        }
        signals.append(signal)
        log("DECISION", f"Accepted {post['id']}: type={signal['signal_type']}, confidence={signal['confidence']}")
    return signals


def post_to_backend(signals: list):
    url = f"{BACKEND_URL}/api/signals/ingest"
    payload = {
        "signals":          signals,
        "ingest_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    log("ACTION", f"POST {url} ({len(signals)} signals)")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        log("ACTION", f"POST {url} -> {resp.status_code} OK")
    except Exception as e:
        log("WARNING", f"Backend not available ({e}) — output saved locally")


def main():
    parser = argparse.ArgumentParser(description="CIRO Agent 1 — Signal Ingestion")
    parser.add_argument("--scenario", default="g10_flood", help="Scenario name (e.g. g10_flood, f8_heatwave)")
    args = parser.parse_args()

    start = datetime.now(timezone.utc)
    log("START", f"Signal Ingestion initiated | scenario={args.scenario}")

    scenario = load_scenario(args.scenario)
    location = scenario["location"]
    log("PROCESS", f"Loaded scenario '{args.scenario}' — location={location['name']}, type={scenario['crisis_type']}")

    posts = scenario["social_posts"]
    log("RESULT", f"Loaded {len(posts)} social media posts from scenario")

    weather = fetch_weather()

    traffic_data = scenario["traffic"]
    log("RESULT", f"Loaded {len(traffic_data.get('traffic_data', []))} traffic road segments from scenario")

    social_signals  = process_social_posts(posts, location)
    weather_signal  = weather_to_signal(weather, location)
    traffic_signals = traffic_to_signals(traffic_data, location)

    if weather_signal:
        log("DECISION", f"Weather signal added: type={weather_signal['signal_type']}, confidence={weather_signal['confidence']}")
    log("DECISION", f"{len(traffic_signals)} traffic signals added")

    all_signals = social_signals[:]
    if weather_signal:
        all_signals.append(weather_signal)
    all_signals.extend(traffic_signals)

    output = {
        "signals":          all_signals,
        "ingest_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(SIGNALS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    log("OUTPUT", f"Written to output/signals.json ({len(all_signals)} signals)")

    post_to_backend(all_signals)

    duration      = (datetime.now(timezone.utc) - start).seconds
    weather_count = 1 if weather_signal else 0
    log("END", (
        f"Duration: {duration}s | {len(social_signals)} social + {weather_count} weather + "
        f"{len(traffic_signals)} traffic = {len(all_signals)} total signals"
    ))


if __name__ == "__main__":
    main()
