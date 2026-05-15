# CIRO — UI/UX Specifications
## Web Dashboard (Command View) + Mobile App (Public View)

**Owner:** Team Lead  
**Stack:** React + Leaflet.js (web), React Native (mobile)

---

## 1. Design Principles

- **Information density over aesthetics** — this is an emergency ops tool; clarity beats beauty
- **Real-time first** — every screen should feel live; stale data is worse than no data
- **Two audiences, one source** — the same backend feeds both; the difference is what is shown and how
- **Color language is consistent**: Red = critical/active crisis, Amber = warning/pending, Green = resolved/safe, Blue = informational

---

## 2. Web Dashboard — Command View

### 2.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CIRO | Crisis Command Dashboard           [Active: 1] [●LIVE]  │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                   │
│  CRISIS      │                 MAP VIEW                         │
│  PANEL       │         (Leaflet.js full-screen map)             │
│              │                                                   │
│  [Crisis 1]  │  [Crisis zone polygon]                           │
│  Urban Flood │  [Unit pins moving]                              │
│  G-10, ISB   │  [Road closure overlays]                         │
│  Severity: 4 │  [Facility icons]                                │
│  ● Active    │                                                   │
│              │                                                   │
│  [+ New]     │                                                   │
├──────────────┴──────────────────────────────────────────────────┤
│                      BOTTOM PANEL (tabs)                        │
│  [Agent Trace] [Dispatch Orders] [Resource Status] [SITREP]    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Crisis Panel (Left Sidebar)

Each crisis card shows:
- Crisis type icon + label
- Location name
- Severity badge (1–5, color-coded)
- Time since detection
- Status dot (Detected / Analyzed / Dispatched / Simulated / Resolved)
- Click to expand → selects crisis on map + loads bottom panel

### 2.3 Map View (Center, main real estate)

**Layers (toggle-able):**
- Crisis zone: semi-transparent red polygon with radius
- Road closures: red dashed lines on affected roads
- Dispatched units: vehicle icons moving along routes (animated, pulled from simulation waypoints)
- Facilities: color-coded icons (hospital = blue cross, rescue = orange star, depot = brown box)
- Traffic congestion: heatmap overlay (before = red, after = amber/green)
- Public alert zones: dashed amber boundary

**Controls:**
- Layer toggles (top right)
- Before/After toggle for traffic state (shows simulation outcome)
- Zoom to crisis button

### 2.4 Bottom Panel (Tabs)

**Tab 1 — Agent Trace:**
Live-scrolling log of agent reasoning steps. Formatted like:
```
14:32:01  Agent 1 ▸ TOOL_CALL  → Open-Meteo API: precipitation=12mm/hr
14:32:08  Agent 1 ▸ DECISION   → 3 flood signals detected in G-10 cluster
14:35:00  Agent 2 ▸ OUTPUT     → Crisis confirmed: Urban Flooding, Confidence: High (0.89)
14:37:00  Agent 3 ▸ ACTION     → Queried Overpass API — 1 road closure identified
14:39:00  Agent 4 ▸ DECISION   → F-8 Rescue Unit Alpha dispatched (nearest available, 3.1km)
```

**Tab 2 — Dispatch Orders:**
Table view:
| Unit | Type | Destination | ETA | Status |
| F-8 Rescue Alpha | Water Rescue | G-10 Sector | 12 min | En Route |

**Tab 3 — Resource Status:**
Current inventory table — Available / Deployed / Unavailable counts per resource type.

**Tab 4 — SITREP:**
Rendered markdown of the Gemini-generated situation report. Download button (PDF export).

### 2.5 Tech Notes (Web)
- **React 18** functional components, hooks
- **Leaflet.js** for map — do not use Google Maps JS on the dashboard (avoid double API quota)
- **WebSocket** connection to `/ws/command` — auto-reconnect on disconnect
- **React Query** for REST data fetching
- Tailwind CSS for layout and utility classes
- No external UI component library needed — keep it minimal and fast

---

## 3. Mobile App — Public View

**Platform:** React Native (runs on iOS + Android)  
**Mandatory for submission.**

### 3.1 Screen List

```
1. Splash / Loading
2. Home — Active Crisis List
3. Crisis Detail — Map + Status
4. Safe Routes — Map with alternate paths
5. Alerts — Notification feed
6. (Optional) Report Screen — Submit a crisis signal
```

### 3.2 Screen 1: Splash

- CIRO logo + tagline: "Real-time crisis intelligence for Islamabad"
- Loads active crises in background
- Transitions to Home after 1.5s

### 3.3 Screen 2: Home — Active Crisis List

```
┌─────────────────────────────┐
│  CIRO                  🔔   │
│  Islamabad              ●   │
├─────────────────────────────┤
│  ● ACTIVE CRISIS            │
│  ┌─────────────────────┐   │
│  │ 🌊 Urban Flooding    │   │
│  │ G-10, Islamabad      │   │
│  │ Severity ████░ 4/5   │   │
│  │ Detected 14 min ago  │   │
│  │ Rescue en route →    │   │
│  └─────────────────────┘   │
│                             │
│  ⚠ NEARBY ALERTS           │
│  Road closed: Srinagar Hwy  │
│  Use Margalla Road instead  │
│                             │
│  ✓ All clear: G-9, I-10    │
└─────────────────────────────┘
```

### 3.4 Screen 3: Crisis Detail

Full-screen map (Google Maps or Leaflet via WebView) with:
- Red zone boundary (affected area)
- My location pin (if location permission granted)
- Rescue unit pins (animated if simulation running)
- Road closure overlays

Below the map (card that slides up):
- Crisis type + confidence
- Reasoning summary (2-3 sentences from Agent 2)
- Actions taken (bullets from Agent 4 dispatch)
- What public should do (extracted from SITREP)
- Last updated timestamp (live)

### 3.5 Screen 4: Safe Routes

```
┌─────────────────────────────┐
│  ← Safe Routes              │
│                             │
│  [Map with green route]     │
│                             │
│  Srinagar Highway ✗ CLOSED  │
│  Margalla Road    ✓ CLEAR   │
│                             │
│  Alternate Route:           │
│  Via Margalla Road          │
│  +8 min | All clear         │
│                             │
│  [Open in Google Maps]      │
└─────────────────────────────┘
```

Data source: Agent 5's route simulation output (alternate roads)

### 3.6 Screen 5: Alerts

Push notification feed:
- Each alert shows: timestamp, affected area, message text, action recommended
- Color-coded by severity

### 3.7 (Optional) Screen 6: Report

Simple form:
- What happened? (text input, auto-detected language)
- Where? (current location button or manual text)
- Attach photo (optional)
- Submit → POST to `/api/signals/ingest` as source: "citizen_report"

This feeds Agent 1 directly and demonstrates the full citizen → agent → response loop.

### 3.8 Tech Notes (Mobile)

- **React Native 0.74** with Expo (faster setup, easier demo build)
- **React Navigation** for screen routing
- **Expo Location** for GPS access
- **Expo Notifications** for push alerts
- **react-native-maps** for map component
- API calls via `fetch()` to backend REST endpoints
- WebSocket for live crisis detail updates
- Use `.env` for backend URL (swap dev/prod easily)

### 3.9 Mobile API Calls

| Screen | API Call | Frequency |
|---|---|---|
| Home | GET `/api/crisis/active` | Every 30s or WebSocket |
| Crisis Detail | GET `/api/crisis/{id}` + WS `/ws/crisis/{id}` | Real-time |
| Safe Routes | GET `/api/crisis/{id}/routes` | On screen load |
| Alerts | GET `/api/alerts/recent` | On screen load |
| Report | POST `/api/signals/ingest` | On submit |

---

## 4. Color System

| Meaning | Hex | Usage |
|---|---|---|
| Critical / Active | `#DC2626` | Active crisis badge, road closure, severity 5 |
| High severity | `#EA580C` | Severity 4, urgent alerts |
| Warning | `#D97706` | Severity 3, amber zones |
| Safe / Resolved | `#16A34A` | Clear roads, resolved status |
| Informational | `#2563EB` | Facilities, neutral info |
| Background | `#0F172A` | Dark mode dashboard |
| Surface | `#1E293B` | Cards, panels |
| Text primary | `#F8FAFC` | Main text |
| Text secondary | `#94A3B8` | Timestamps, labels |

---

## 5. Demo Flow (What Judges See)

### Web Dashboard Demo (3 min of the video)
1. Dashboard loads — map of Islamabad visible, no active crises
2. "Trigger Demo" button clicked (or manual: social media post submitted)
3. Agent Trace panel starts scrolling — Agent 1 working
4. Crisis card appears in left panel: "Urban Flooding — G-10 — Detected"
5. Red zone polygon appears on map
6. Status updates: Analyzed → Dispatched
7. Unit pin appears on map, moves along route toward crisis zone
8. Traffic heatmap shifts from red → amber (congestion reduction)
9. SITREP tab shows generated situation report
10. Before/After toggle demonstrates outcome

### Mobile App Demo (1 min of the video)
1. App opens — crisis visible on home screen
2. Tap crisis → detail map with affected zone
3. Safe Routes tab — alternate route highlighted
4. Alerts screen — public alert message visible

---

## 6. Demo Data Requirements (Coordinate to Hardcode)

These exact coordinates must be consistent across backend seed data, agent mock data, and frontend:

| Entity | Name | Lat | Lng |
|---|---|---|---|
| Crisis center | G-10, Islamabad | 33.6844 | 73.0479 |
| F-8 Rescue Station | F-8 Rescue Unit Alpha | 33.7080 | 73.0479 |
| PIMS Hospital | Emergency facility | 33.7161 | 73.0738 |
| Blocked road | Srinagar Highway G-10 | 33.6880 | 73.0550 |
| Alternate route start | Margalla Road | 33.7200 | 73.0450 |
