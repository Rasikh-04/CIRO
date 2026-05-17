# CIRO v2 — Data Ingestion & Real APIs
## Every Data Source, How to Access It, and How to Integrate It

---

## 1. Data Sources Overview

| Source | Track | Data Type | Cost | Update Frequency |
|---|---|---|---|---|
| Pakistan Meteorological Department | 1 + 2 | Weather, rainfall, flood warnings | Free | Hourly |
| Open-Meteo | 1 + 2 | Weather (backup, more reliable API) | Free | Hourly |
| UNOSAT (UN Satellite Centre) | 2 | Flood inundation maps (GeoTIFF) | Free | Event-based |
| OpenStreetMap (Overpass API) | 1 + 2 | Road network, facilities | Free | Near-real-time |
| Google Maps Platform | 1 | Traffic, directions, geocoding | Free tier | Near-real-time |
| ReliefWeb API (OCHA) | 2 | Crisis reports, agency updates | Free | Daily/event |
| HealthSites.io | 2 | Hospital, clinic locations | Free | Monthly |
| Pakistan 1122 | 1 | Rescue service dispatch (manual) | Contact required | Real-time |
| Twitter/X (Nitter) | 1 | Social media signals | Free (Nitter) | Real-time |
| Pakistan social media (scrape) | 1 | Urdu/English crisis posts | Free | Real-time |
| NDMA Situation Reports | 2 | Official disaster assessments | Free (public PDFs) | Daily during crisis |
| Google Cloud Text-to-Speech | 1 | Voice alerts (Urdu + English) | Free 1M chars/mo | On-demand |

---

## 2. Ingestion Services (Separate from Agents)

These run as **scheduled Cloud Run Jobs** or **continuous Cloud Run services**. They push to `signals.raw` Pub/Sub topic. Agents never call external APIs directly — ingestion services do.

```
ciro/
└── ingestion/
    ├── weather_ingestor/         ← runs every 15 min (Cloud Scheduler)
    ├── unosat_ingestor/          ← runs every 6 hr (Cloud Scheduler)
    ├── overpass_ingestor/        ← runs every 30 min
    ├── reliefweb_ingestor/       ← runs every 1 hr
    ├── social_monitor/           ← continuous (Cloud Run service)
    ├── ndma_pdf_ingestor/        ← runs every 2 hr
    └── citizen_report_relay/     ← via backend webhook
```

---

## 3. Weather — Pakistan Meteorological Department (PMD)

**URL:** https://www.pmd.gov.pk  
**API:** PMD does not have a public REST API — use web scraping for bulletins  
**Better alternative: Open-Meteo (backup + primary)**

### Open-Meteo Integration (Primary)
```
https://api.open-meteo.com/v1/forecast
  ?latitude=33.6844
  &longitude=73.0479
  &current=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m
  &hourly=precipitation,rain,precipitation_probability
  &daily=precipitation_sum,rain_sum,precipitation_hours
  &timezone=Asia/Karachi
  &forecast_days=3
```
**No API key needed. Free. Unlimited.**

### Crisis-Relevant Weather Codes
```python
CRISIS_WEATHER_CODES = {
    51: ("drizzle_moderate", 0),  # Not a crisis
    61: ("rain_moderate", 1),
    63: ("rain_heavy", 2),
    65: ("rain_very_heavy", 3),
    80: ("showers_moderate", 2),
    81: ("showers_heavy", 3),
    82: ("showers_violent", 4),    # Flood risk
    95: ("thunderstorm", 3),
    96: ("thunderstorm_hail", 4),
    99: ("thunderstorm_heavy_hail", 5),
}

FLOOD_PRECIPITATION_THRESHOLD_MM = 25  # >25mm/hr = flood risk
HEATWAVE_TEMP_THRESHOLD_C = 44
```

### PMD RSS Scraper (for official warnings)
```python
import feedparser

PMD_FEEDS = [
    "https://www.pmd.gov.pk/en/feed/",  # RSS feed
]

async def fetch_pmd_warnings():
    for feed_url in PMD_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if any(kw in entry.title.lower() for kw in ["flood", "warning", "alert", "rainfall"]):
                yield {
                    "source": "pmd_official",
                    "text": entry.summary,
                    "title": entry.title,
                    "url": entry.link,
                    "published": entry.published,
                    "reliability": "official"
                }
```

---

## 4. UNOSAT Flood Maps

**Access:** https://unosat.org/products/  
**API:** https://unosat.org/api/v2/ (REST, free, registration required)  
**Data format:** GeoTIFF raster + GeoJSON vector  
**Registration:** https://unosat.org/user/register (free, no review needed)

### UNOSAT API Integration
```python
UNOSAT_API_KEY = os.environ["UNOSAT_API_KEY"]
UNOSAT_BASE = "https://unosat.org/api/v2"

async def fetch_flood_extent(lat: float, lng: float, radius_km: float = 50) -> Optional[dict]:
    """
    Searches UNOSAT for recent flood activations near the given coordinates.
    Returns GeoJSON polygon of flood extent if found.
    """
    # Search for recent activations
    bbox = bbox_from_center(lat, lng, radius_km)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{UNOSAT_BASE}/activations/",
            headers={"Authorization": f"Token {UNOSAT_API_KEY}"},
            params={
                "bbox": f"{bbox.west},{bbox.south},{bbox.east},{bbox.north}",
                "event_type": "FL",  # Flood
                "date_from": (datetime.now() - timedelta(days=30)).isoformat()
            }
        )
    
    if response.status_code != 200 or not response.json()["results"]:
        return None
    
    # Get the most recent activation
    activation = response.json()["results"][0]
    
    # Download GeoJSON flood extent
    geojson_response = await client.get(
        activation["download_links"]["geojson"],
        headers={"Authorization": f"Token {UNOSAT_API_KEY}"}
    )
    
    return geojson_response.json()
```

**Also download archived Pakistan data:**
- 2022 Pakistan Flood: https://unosat.org/products/3674
- GeoTIFF for Supabase/PostGIS import
- Store in Cloud Storage: `gs://ciro-assets/unosat/pakistan_2022_flood.tif`

---

## 5. OpenStreetMap — Overpass API

**URL:** https://overpass-api.de/api/interpreter  
**No API key. Free. Rate limit: 1 req/5 sec.**  
**Mirror for reliability:** https://overpass.kumi.systems/api/interpreter

### Road Network Query (around crisis zone)
```python
def build_overpass_query(lat: float, lng: float, radius_m: int = 5000) -> str:
    return f"""
    [out:json][timeout:30];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary|residential"]
        (around:{radius_m},{lat},{lng});
      node["highway"="traffic_signals"](around:{radius_m},{lat},{lng});
      node["barrier"](around:{radius_m},{lat},{lng});
    );
    out geom;
    """

async def fetch_road_network(lat: float, lng: float, radius_km: float) -> OSMRoadNetwork:
    query = build_overpass_query(lat, lng, int(radius_km * 1000))
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30
        )
    return parse_overpass_response(r.json())
```

### Facility Query
```python
def build_facility_query(lat: float, lng: float, radius_m: int = 10000) -> str:
    return f"""
    [out:json][timeout:30];
    (
      node["amenity"~"hospital|clinic|fire_station|police"](around:{radius_m},{lat},{lng});
      node["emergency"="yes"](around:{radius_m},{lat},{lng});
      node["healthcare"](around:{radius_m},{lat},{lng});
    );
    out body;
    """
```

**Pre-cache Islamabad facilities to Supabase on startup** — don't query Overpass for every crisis.

---

## 6. ReliefWeb API (OCHA)

**URL:** https://api.reliefweb.int/v1/  
**No API key needed. Free.**

### Fetch Pakistan Crisis Reports
```python
RELIEFWEB_BASE = "https://api.reliefweb.int/v1"

async def fetch_crisis_reports(country: str = "Pakistan", days_back: int = 7) -> List[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RELIEFWEB_BASE}/reports",
            json={
                "filter": {
                    "operator": "AND",
                    "conditions": [
                        {"field": "primary_country.iso3", "value": "PAK"},
                        {"field": "date.created", "value": {
                            "from": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00+00:00")
                        }},
                        {"field": "theme.name", "value": ["Disaster Management", "Flood", "Natural Disaster"]}
                    ]
                },
                "fields": {"include": ["title", "body", "date", "source", "url", "format"]},
                "sort": ["date.created:desc"],
                "limit": 20
            }
        )
    return response.json().get("data", [])
```

### Fetch Agency Capacity Data
```python
async def fetch_organization_data(country: str = "Pakistan") -> List[dict]:
    """Fetches registered humanitarian organizations operating in Pakistan."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RELIEFWEB_BASE}/sources",
            params={"filter[field][primary_country.iso3]": "PAK", "limit": 50}
        )
    return response.json().get("data", [])
```

---

## 7. HealthSites.io

**URL:** https://healthsites.io/api/v2/  
**API key required (free): Register at https://healthsites.io/accounts/register/**

```python
async def fetch_health_facilities(lat: float, lng: float, radius_km: float = 20):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://healthsites.io/api/v2/facilities/",
            params={
                "api-key": os.environ["HEALTHSITES_API_KEY"],
                "bbox": build_bbox_string(lat, lng, radius_km),
                "format": "json",
                "limit": 50
            }
        )
    return response.json()
```

**One-time download:** Pre-cache all Pakistan health facilities to Supabase `facilities` table. Update weekly via Cloud Scheduler.

```python
# scripts/seed_pakistan_facilities.py
# Run once: downloads all Pakistan hospitals/clinics from HealthSites
# Stores in Supabase facilities table with PostGIS POINT geometry
```

---

## 8. Social Media Monitoring

**Note on Twitter/X API:** The paid tier starts at $100/month. Not feasible. Use these alternatives:

### Option A: Nitter (Self-hosted or public instances)
Nitter is an open-source Twitter frontend that exposes RSS feeds. No API key needed.

```python
import feedparser
import httpx

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org"
]

CRISIS_SEARCH_TERMS = [
    "flood islamabad", "pani islamabad", "road band islamabad",
    "G-10 flood", "G-10 pani", "Lahore flood", "karachi flood",
    "accident motorway", "heatwave pakistan", "bijli gul",
]

async def monitor_nitter(search_term: str) -> List[dict]:
    for instance in NITTER_INSTANCES:
        try:
            feed_url = f"{instance}/search/rss?q={quote(search_term)}&f=tweets"
            feed = feedparser.parse(feed_url)
            return [
                {
                    "text": entry.title,
                    "url": entry.link,
                    "timestamp": entry.published,
                    "source": "social_nitter",
                    "search_term": search_term
                }
                for entry in feed.entries[:20]
            ]
        except Exception:
            continue
    return []
```

### Option B: Pakistan-Specific News Aggregation
```python
PAKISTAN_NEWS_FEEDS = {
    "geo": "https://www.geo.tv/rss/1/breaking-news",
    "dawn": "https://www.dawn.com/feeds/home",
    "ard_news": "https://arynews.tv/feed/",
    "samaa": "https://www.samaa.tv/feed/",
    "express_urdu": "https://www.express.pk/feed/",
}

CRISIS_KEYWORDS = [
    # Urdu (roman)
    "سیلاب", "بارش", "حادثہ", "بجلی", "پانی",
    # Roman Urdu
    "sailab", "barish", "hadsa", "bijli", "pani", "band rasta",
    # English
    "flood", "accident", "road closed", "power outage", "rainfall", "heatwave"
]
```

### Option C: Citizen Report App (Primary for Production)
The mobile app's "Report" feature (Screen 6) is the most reliable long-term social signal. Each submission goes directly to the ingestion pipeline as a citizen report.

---

## 9. NDMA PDF Ingestion

**Source:** https://ndma.gov.pk/situation-reports/  
**Format:** PDF situation reports published during active crises  
**Access:** Free, public

```python
async def monitor_ndma_reports():
    """
    Checks NDMA website for new situation reports.
    Downloads, parses, and ingests new ones.
    Runs every 2 hours via Cloud Scheduler.
    """
    import fitz  # PyMuPDF: pip install pymupdf

    # Scrape the NDMA situation reports page
    async with httpx.AsyncClient() as client:
        page = await client.get("https://ndma.gov.pk/situation-reports/")
    
    # Parse PDF links
    pdf_links = extract_pdf_links(page.text)
    
    for link in pdf_links:
        # Check if already processed
        if await is_processed(link):
            continue
        
        # Download and parse
        pdf_content = await download_pdf(link)
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        
        # Gemini structures the report
        structured = await gemini_structure_ndma_report(text)
        
        # Store in Supabase
        await store_ndma_report(link, structured)
        
        # Push to ingestion pipeline if active crisis detected
        if structured.get("active_crisis"):
            await publish_to_signals(structured)
```

**PyMuPDF (fitz) installation:** `pip install pymupdf`  
**GitHub:** https://github.com/pymupdf/PyMuPDF

---

## 10. Google Cloud Text-to-Speech (Voice Alerts)

**Free tier:** 1 million characters/month (standard voices), 1M chars/month WaveNet  
**Urdu voice:** `ur-PK-Standard-A` (female) or `ur-PK-Wavenet-A`

```python
# Available Urdu voices
URDU_VOICES = {
    "female_standard": "ur-PK-Standard-A",
    "male_standard": "ur-PK-Standard-B",
    "female_wavenet": "ur-PK-Wavenet-A",
    "male_wavenet": "ur-PK-Wavenet-B"
}

# English Pakistan voice
ENGLISH_PAKISTAN_VOICE = "en-IN-Wavenet-A"  # Closest to Pakistani English
```

**Documentation:** https://cloud.google.com/text-to-speech/docs/voices  
**Console:** https://console.cloud.google.com/apis/library/texttospeech.googleapis.com

---

## 11. All Required Environment Variables

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=ciro-production
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Vertex AI / Gemini
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL=gemini-1.5-flash-002

# External APIs
UNOSAT_API_KEY=your-unosat-key
HEALTHSITES_API_KEY=your-healthsites-key
OPENROUTESERVICE_API_KEY=your-ors-key
GOOGLE_MAPS_API_KEY=your-maps-key

# Pub/Sub Topics
PUBSUB_SIGNALS_RAW=signals-raw
PUBSUB_SIGNALS_PROCESSED=signals-processed
PUBSUB_CRISIS_DETECTED=crisis-detected
PUBSUB_CRISIS_MAJOR=crisis-major
PUBSUB_OPS_READY=ops-picture-ready
PUBSUB_DISPATCH_PLANNED=dispatch-planned
PUBSUB_SIMULATION_DONE=simulation-complete
PUBSUB_ALERT_BROADCAST=alert-broadcast
PUBSUB_TRACK2_UPDATE=track2-update

# Backend
BACKEND_URL=https://ciro-backend-xxx-uc.a.run.app
ENVIRONMENT=production
```

---

## 12. API Registration Checklist

Before starting development:

| API | Registration URL | Free? | Time to Activate |
|---|---|---|---|
| Google Cloud Project | console.cloud.google.com | $5 credit | Instant |
| Google Maps Platform | console.cloud.google.com/apis | Free tier | Instant |
| Google Cloud Text-to-Speech | Enable in Cloud Console | Free tier | Instant |
| Vertex AI | Enable in Cloud Console | $5 credit | Instant |
| Google Cloud Pub/Sub | Enable in Cloud Console | Free tier | Instant |
| Supabase | supabase.com | Free | Instant |
| Firebase | firebase.google.com | Free | Instant |
| OpenRouteService | openrouteservice.org/dev | Free | Instant |
| UNOSAT | unosat.org/user/register | Free | 1-2 days |
| HealthSites.io | healthsites.io/accounts/register | Free | Instant |
| Open-Meteo | No registration | Free | None |
| Overpass API | No registration | Free | None |
| ReliefWeb | No registration | Free | None |
