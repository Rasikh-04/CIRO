# CIRO v2 — Complete UI/UX Specification
## From Spacing to System: Everything Needed to Build Production-Grade Interfaces

---

## 1. Design Philosophy

CIRO serves two audiences in high-stress conditions:
- **Civilians** during an active emergency (mobile) — need instant clarity, minimum friction, one-hand operation, offline tolerance
- **Emergency coordinators** (dashboard) — need information density, decision support, and action capability

Design principles:
1. **Function precedes form** — no decoration that doesn't carry information
2. **Every Vstate is visible** — loading, error, offline, stale data are always communicated
3. **Urgency is color** — the color system is semantic, not aesthetic
4. **Bilingual always** — Urdu and English must coexist gracefully in every text element
5. **Touch targets are generous** — minimum 48×48pt, 56pt preferred for emergency actions

---

## 2. Color System — Four Options

### Option A: Naval Command (RECOMMENDED)
**Best for:** Emergency operations — the orange creates urgency contrast against navy

| Token | Value | Usage |
|---|---|---|
| `--color-bg-primary` | `#0A1628` | App background, screen base |
| `--color-bg-surface` | `#132743` | Cards, panels, sidebars |
| `--color-bg-elevated` | `#1B3558` | Modal surfaces, tooltips |
| `--color-accent-primary` | `#FF6B35` | CTAs, severity 4–5 alerts, critical actions |
| `--color-accent-secondary` | `#3D9EFF` | Links, info, map overlays |
| `--color-status-critical` | `#FF3B3B` | Severity 5, immediate danger |
| `--color-status-high` | `#FF6B35` | Severity 4, dispatch active |
| `--color-status-medium` | `#FFB830` | Severity 3, monitoring |
| `--color-status-low` | `#3ECF8E` | Severity 1–2, informational |
| `--color-status-resolved` | `#2ECC71` | Crisis resolved |
| `--color-text-primary` | `#F0F4F8` | Body text, labels |
| `--color-text-secondary` | `#8BA0B5` | Timestamps, captions |
| `--color-text-muted` | `#4A6580` | Disabled, placeholder |
| `--color-border` | `#1E3A56` | Card borders, dividers |
| `--color-border-strong` | `#2D5072` | Focus rings, active states |

### Option B: Arctic Ops
**Best for:** Clean, clinical feel — better for prolonged use in ops room

| Token | Value | Usage |
|---|---|---|
| `--color-bg-primary` | `#0D1B2A` | Background |
| `--color-bg-surface` | `#162032` | Cards |
| `--color-accent-primary` | `#00B4D8` | CTAs, info |
| `--color-accent-secondary` | `#0077B6` | Secondary actions |
| `--color-status-critical` | `#EF233C` | Critical |
| `--color-status-high` | `#F77F00` | High |
| `--color-status-medium` | `#FCBF49` | Medium |
| `--color-status-low` | `#EAE2B7` | Low |
| `--color-text-primary` | `#EDF2F4` | Text |
| `--color-text-secondary` | `#8D99AE` | Secondary |

### Option C: Deep Navy Professional
**Best for:** Most conservative — suitable for government/NDMA presentation

| Token | Value | Usage |
|---|---|---|
| `--color-bg-primary` | `#06111F` | Background |
| `--color-bg-surface` | `#0F2137` | Cards |
| `--color-accent-primary` | `#2B7FFF` | CTAs |
| `--color-accent-secondary` | `#1BCDFE` | Secondary |
| `--color-status-critical` | `#FF4444` | Critical |
| `--color-status-high` | `#FF8800` | High |
| `--color-status-medium` | `#FFD700` | Medium |

### Option D: Night Ops (High Contrast)
**Best for:** Outdoor use, field officers, bright conditions

| Token | Value | Usage |
|---|---|---|
| `--color-bg-primary` | `#000000` | Background |
| `--color-bg-surface` | `#111827` | Cards |
| `--color-accent-primary` | `#F59E0B` | CTAs (amber — high visibility) |
| `--color-accent-secondary` | `#3B82F6` | Info |
| `--color-status-critical` | `#FF0000` | Critical |

**Recommendation: Option A (Naval Command)**. The orange accent creates unambiguous urgency signaling in a maritime/ops aesthetic.

---

## 3. Typography

```css
/* Font Stack */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-urdu: 'Noto Nastaliq Urdu', 'Noto Naskh Arabic', serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Type Scale (base: 16px) */
--text-xs:   11px / 1.4  /* Timestamps, badges */
--text-sm:   13px / 1.4  /* Captions, helper text */
--text-base: 15px / 1.5  /* Body text */
--text-md:   17px / 1.4  /* Card titles, labels */
--text-lg:   20px / 1.3  /* Section headers */
--text-xl:   24px / 1.2  /* Page titles */
--text-2xl:  32px / 1.1  /* Hero numbers, severity */
--text-3xl:  40px / 1.0  /* Crisis counter, status hero */

/* Font Weights */
--font-regular:   400
--font-medium:    500
--font-semibold:  600
--font-bold:      700

/* Urdu text: always right-to-left */
.urdu { 
  font-family: var(--font-urdu); 
  direction: rtl; 
  text-align: right; 
  line-height: 1.8;  /* Urdu needs more line height */
}
```

---

## 4. Spacing System (4pt base grid)

```css
/* All spacing is a multiple of 4px */
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px

/* Component spacing rules */
--padding-card:         16px 20px      /* Card inner padding */
--padding-screen:       0 16px         /* Mobile screen edge padding */
--padding-screen-top:   16px           /* Status bar clearance */
--gap-list-item:        12px           /* Between list items */
--gap-section:          24px           /* Between sections */
--gap-inline:           8px            /* Between inline elements */
--border-radius-sm:     6px
--border-radius-md:     12px
--border-radius-lg:     16px
--border-radius-pill:   100px
```

---

## 5. Motion & Transitions

```css
/* Duration tokens */
--duration-instant:   50ms    /* Micro-interactions */
--duration-fast:      100ms   /* Button press, toggle */
--duration-normal:    200ms   /* Most transitions */
--duration-slow:      350ms   /* Panel slides, modal */
--duration-xslow:     500ms   /* Page transitions */

/* Easing */
--ease-standard:  cubic-bezier(0.4, 0.0, 0.2, 1)  /* Default motion */
--ease-enter:     cubic-bezier(0.0, 0.0, 0.2, 1)  /* Elements entering */
--ease-exit:      cubic-bezier(0.4, 0.0, 1, 1)    /* Elements leaving */
--ease-spring:    cubic-bezier(0.175, 0.885, 0.32, 1.275) /* Bouncy feedback */

/* Rules */
/* 1. Never animate layout properties (height, width) - use transform/opacity only */
/* 2. Crisis alerts animate in with scale(0.95) → scale(1) + opacity: 0 → 1 */
/* 3. Map overlays fade in over 350ms */
/* 4. Severity number change: count-up animation 500ms */
/* 5. Loading skeletons pulse with 1.5s ease-in-out infinite */
```

---

## 6. Iconography

Use **Lucide React** (web) and **@expo/vector-icons Feather + MaterialIcons** (mobile).  
No custom icons unless absolutely necessary.

```
Crisis types:         Droplets (flood), Thermometer (heatwave), 
                      AlertTriangle (accident), ZapOff (infrastructure)
Navigation:           Map, Bell, Navigation2, User
Status:               CheckCircle, XCircle, AlertCircle, Clock, Loader2
Actions:              Send, Phone, ExternalLink, Download, RefreshCw
Map:                  MapPin, Route, Building2, Truck, Shield
Track 2:              Users, Package, FileText, Radio
Voice:                Volume2, VolumeX, Mic
```

**Icon sizing:**
- `16px` — inline with text, badges
- `20px` — list items, nav labels
- `24px` — primary nav icons
- `32px` — hero/empty state icons
- `48px` — splash, onboarding

---

## 7. Component Specifications

### 7.1 Crisis Card (used in both mobile + dashboard)

```
┌─────────────────────────────────────────┐
│ [icon] CRISIS TYPE         [severity █] │  ← 48px height header
│ Location name                     time  │  ← text-sm, secondary color
├─────────────────────────────────────────┤  ← 1px border, --color-border
│ Status: DISPATCHED → SIMULATED          │  ← progress step indicator
│ [■■■■□] 4 units en route                │  ← mini progress bar
└─────────────────────────────────────────┘

Height: auto min 80px
Border: 1px solid --color-border
Border-left: 4px solid [severity color]  ← key visual: severity stripe
Border-radius: --border-radius-md
Background: --color-bg-surface
Active state: border-left-color + subtle glow (box-shadow: 0 0 0 1px [severity-color]33)
Hover: background lightens 5% (--color-bg-elevated)
Transition: all 200ms --ease-standard
```

### 7.2 Severity Badge

```
Severity 1: background #3ECF8E22, color #3ECF8E, text "LOW"
Severity 2: background #3ECF8E22, color #3ECF8E, text "MINOR"
Severity 3: background #FFB83022, color #FFB830, text "MODERATE"
Severity 4: background #FF6B3522, color #FF6B35, text "HIGH"
Severity 5: background #FF3B3B22, color #FF3B3B, text "CRITICAL"

Width: fit-content
Padding: 2px 8px
Border-radius: --border-radius-pill
Font: --text-xs, --font-bold, letter-spacing: 0.05em
```

### 7.3 Map Overlays

```
Crisis zone circle:
  color: severity-color at 20% opacity fill, 2px solid at 60% opacity
  animation: pulse — scale 1→1.02, opacity 100%→80%, 2s infinite (critical only)

Road closure line:
  color: #FF3B3B
  width: 3px
  dash-array: 8 4
  opacity: 0.9

Dispatch route polyline:
  color: #3D9EFF
  width: 3px
  opacity: 0.8
  end-cap: arrow (arrowhead at destination)

Unit marker:
  circle, 12px diameter
  color: unit type color
  border: 2px white
  shadow: 0 2px 8px rgba(0,0,0,0.4)
  animation: bounce-once on arrival

Flood extent polygon (UNOSAT):
  fill: #00B4D8 at 25% opacity
  stroke: #00B4D8 at 70%, 1px
```

### 7.4 Agent Trace Row

```
[timestamp]  [AGENT N]  [▸ LEVEL]   message text
14:32:01     Agent 1    ▸ TOOL      Called Open-Meteo API
14:32:08     Agent 1    ▸ DECISION  3 flood signals clustered in G-10
14:35:00     Agent 2    ▸ OUTPUT    Crisis confirmed: 0.89 confidence

Level colors:
  TOOL:     --color-text-secondary
  RESULT:   --color-text-primary
  DECISION: #FFB830 (amber)
  ACTION:   #FF6B35 (orange)
  OUTPUT:   #3ECF8E (green)
  ERROR:    #FF3B3B (red)
  WARNING:  #FFB830 (amber)

Font: --font-mono, --text-sm
Background: alternating rows — transparent / rgba(255,255,255,0.02)
Row height: 32px
```

---

## 8. Mobile App — Screen-by-Screen Specification

### Screen 1: Splash / Boot

```
Background: full-screen map (blurred 4px, dark overlay 70%)
Center:
  - CIRO logo (40px text, --font-bold, --color-text-primary)
  - Tagline: "Real-time crisis intelligence" (--text-sm, --color-text-secondary)
  - Loading indicator: 3-dot pulse animation, --color-accent-primary

Duration: 1.2s or until API responds (whichever is longer)
Offline fallback: show "Offline — using cached data" after 3s
```

### Screen 2: Home (Main)

```
Layout: Full-screen map underneath, bottom sheet overlay

MAP LAYER (full screen):
  react-native-maps, initial region: user's city
  Show: active crisis circles, user location pin
  Crisis circle taps → navigate to Crisis Detail

BOTTOM SHEET (default peek: 240px from bottom):
  States: peek (240px) → half (50% screen) → full
  Drag handle: 32px wide, 4px tall, centered, --color-text-muted, margin-top: 8px

  [peek state content]:
    Crisis count header:
      "● N ACTIVE CRISIS" (--text-sm, --font-semibold, --color-status-critical if N>0)
      "Islamabad • Updated 2 min ago"

    Crisis cards (horizontally scrollable, peek=1.5 cards visible):
      Card: 280px wide, 96px tall, see §7.1
      Snap scrolling

  [half state content]:
    Full list of active crises (vertical scroll)
    Nearby alerts section (road closures near user)

  [full state content]:
    All crises, sort options (severity / time / distance)

HEADER (floating, top):
  Left: CIRO logo (compact, 24px)
  Right: [Bell icon] notification count, [Mic icon] voice alert status
  Background: rgba(10,22,40,0.85) + blur
  Height: 52px + status bar padding (SafeAreaView)
```

### Screen 3: Crisis Detail

```
Layout: Full-screen map + sliding bottom sheet (starts at 40% from bottom)

MAP:
  Centered on crisis zone
  Shows: crisis circle, all unit markers, route polylines, road closure overlays
  Tap road closure → tooltip with closure info and alternate
  Animated: units move along routes if simulation running

BOTTOM SHEET:

  HEADER (always visible at any sheet height):
    [Crisis type icon]  Crisis Type Title          Severity badge
    "G-10, Islamabad • Detected 14 min ago"
    Stage progress bar: DETECTED → ANALYZED → DISPATCHED → SIMULATED → RESOLVED
    (Each stage: 20% width, filled = accent color, current = pulse animation)

  BODY (scrolls inside sheet):

    CONFIDENCE BLOCK (if recently detected):
      "Confidence: High (89%)"
      "Based on 3 corroborating signals..."
      [Expand toggle] → shows signal list

    REASONING (collapsible):
      Agent 2's confidence explanation text
      --text-sm, line-height 1.6

    ACTIONS SECTION:
      Section label: "RESPONSE ACTIONS" (--text-xs, --font-semibold, letter-spacing 0.1em)
      Each action row: [unit icon] [Unit Name] → [Destination] [ETA badge]
      ETA badge: "12 min" pill, --color-accent-secondary background

    PUBLIC GUIDANCE:
      Section label: "WHAT YOU SHOULD DO"
      Numbered list of 2-3 clear instructions
      --text-base, line-height 1.6
      Urdu translation toggle below (tap → expands Urdu text)

    VOICE ALERT BUTTON (if user is in affected zone):
      Large button (full width), height 56px
      [Volume2 icon] "Play Voice Alert" | [VolumeX] "Stop"
      Background: --color-status-critical at 15% + border 1px --color-status-critical
      Plays cached .mp3 from Cloud Storage

STATUS BAR CHIP (floating, bottom of map):
  "● RESCUE EN ROUTE" — amber, with breathing animation
  Auto-dismisses when status changes
```

### Screen 4: Alerts Feed

```
Layout: Standard list screen with header

HEADER:
  Title: "Alerts" (--text-xl, --font-bold)
  Subtitle: "Islamabad • Last updated 2 min ago"
  Filter pills (horizontal scroll): ALL | CRITICAL | FLOODING | TRAFFIC | HEATWAVE

ALERT LIST:
  Each item:
    [Left accent bar: 4px, severity color]
    [Icon: crisis type, 20px]  [Title: --text-md]
    [Location + time: --text-sm, --color-text-secondary]
    [Short description: 2 lines max, --text-sm]
    [Action button: "Get Safe Routes →" if has routes | "View on Map"]

    Tap → Crisis Detail screen (modal presentation)

  Sections:
    "ACTIVE (N)" — sorted by severity desc
    "RESOLVED TODAY (N)" — greyed out, collapsed by default

EMPTY STATE:
  [CheckCircle icon, 48px, --color-status-resolved]
  "No active alerts in your area"
  "Last checked: 2 min ago"
```

### Screen 5: Safe Routes

```
Layout: Full-screen map + bottom info panel (fixed 260px)

MAP:
  Shows: blocked roads (red dashed), safe routes (green), user location
  Multiple alternate routes (different green shades)

BOTTOM PANEL:
  Title: "Safe Routes from your location"
  Subtitle: "Srinagar Highway closed — use alternates"

  ROUTE CARDS (horizontal scroll):
    Each card (260px wide):
      [Route name]: "Via Margalla Road"
      [Time]: "+8 min" (vs normal)
      [Distance]: "3.2 km"
      [Risk badge]: CLEAR / MONITOR / AVOID
      [Open in Google Maps] → deep link

  "Share location" button (bottom, full width)
  "Voice directions" button (if in affected area)
```

### Screen 6: Report Incident

```
Layout: Form screen

FORM:
  Header: "Report an Incident"
  Subtext: "Your report goes directly to emergency services"

  WHAT HAPPENED:
    Chip selection (multi-select, horizontal scroll):
    [🌊 Flooding] [🚗 Accident] [🔥 Fire] [⚡ Power Cut] [🚧 Road Blocked] [Other]
    Tap chips → selected state (accent background)

  DESCRIBE (optional):
    TextInput, placeholder "Add details... (Urdu or English)"
    4 lines visible, expandable
    Character limit: 280, shown as "N/280"

  WHERE:
    [📍 Use my current location] — primary, auto-selected
    [Type location] — secondary, text input with autocomplete

  PHOTO (optional):
    [Camera icon] button
    Thumbnail preview after selection

  SUBMIT:
    Full-width button, 56px height
    "Send Report to Emergency Services"
    --color-accent-primary background
    Loading state: spinner + "Sending..."
    Success: checkmark + "Report received. Thank you."

PRIVACY NOTE (--text-xs, --color-text-muted):
  "Your name is not shared. Location is used for emergency response only."
```

### Screen 7: Profile / Preferences

```
ALERT PREFERENCES:
  "Alert me for crises within:" → segmented control [2km | 5km | 10km | City-wide]
  "Alert types:" → toggles for each type
  "Notification sound:" → dropdown [Silent | Vibrate | Sound | Voice Alert]
  "Language preference:" → [English | اردو | Both]

VOICE ALERT SETTINGS:
  "Auto-play voice alerts when in affected area" → toggle (default: ON)
  "Voice language:" → [Urdu | English | Both (Urdu first)]
  "Pre-download alerts for offline use" → toggle (default: ON)

ABOUT:
  Version, licenses, data sources attribution
```

---

## 9. Web Dashboard — Screen Specification

### Main Dashboard (Command View)

**Layout (1440px+ optimized, responsive down to 1024px):**

```
┌──────────────────────────────────────────────────────────────────────┐
│ HEADER (56px)                                                        │
│  [CIRO]  [Track 1] [Track 2]   [● 1 Active]  [●LIVE]  [⚙][👤]      │
├──────────────────────────────────────────────────────────────────────┤
│          │                                              │             │
│  LEFT    │        MAP PANEL (flex, fills center)       │  RIGHT      │
│  PANEL   │        Leaflet.js full height               │  PANEL      │
│  320px   │                                             │  320px      │
│          │  [Layer controls: floating top-right]       │  (Track 2)  │
│  Crisis  │  [Traffic toggle: floating top-center]      │             │
│  List    │  [Zoom to crisis: floating bottom-right]    │  Agency     │
│          │                                             │  Status     │
│  Active  │                                             │  Panel      │
│  (N)     │                                             │  (T2 only)  │
│          │                                             │             │
│  [+Trig] │                                             │             │
├──────────┴─────────────────────────────────────────────┴─────────────┤
│ BOTTOM PANEL (320px, resizable)                                       │
│  [Agent Trace] [Dispatch Orders] [Resource Status] [SITREP] [T2 Ops] │
│                                                                       │
│  Tab content area                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Header Detail

```
Background: --color-bg-surface + 1px bottom border
Left: "CIRO" logo text (--text-lg, --font-bold) + version pill
Center: Tab nav — [Track 1] [Track 2] — pill style, active has accent bg
Right cluster: 
  Active crisis count badge (red if >0)
  Connection status pill: "● LIVE" (green pulse) | "● CONNECTING" (amber) | "○ OFFLINE" (muted)
  Settings icon, User icon
```

### Left Panel — Crisis List

```
Background: --color-bg-surface
Border-right: 1px --color-border
Padding: 16px 12px

Search/filter bar (32px height, full width):
  [Search icon] "Filter crises..." placeholder
  Type filter pills below: ALL | FLOOD | ACCIDENT | HEATWAVE

Crisis cards (see §7.1):
  Stacked vertically, 8px gap
  Active/selected: left-border + elevated background
  Click: loads crisis on map + populates bottom panel

Footer:
  "Trigger Demo" button (for hackathon) → 40px, full width, outlined style
  "Add Manual Crisis" button
```

### Bottom Panel Detail

```
Tab bar: 48px height
  [Agent Trace][Dispatch Orders][Resource Status][SITREP][T2 Operations]
  Active tab: 3px bottom border, accent color
  Tab has unread badge (for new events)

Agent Trace tab:
  Virtual scrolling list (performance — can be thousands of rows)
  Auto-scroll to bottom when new events arrive
  "Pause scroll" button (appears when user scrolls up)
  Filter: ALL | DECISION | ACTION | ERROR | by agent number
  Search: full-text search across all trace entries

Dispatch Orders tab:
  Table: Unit | Type | Destination | Status | ETA | Route
  Status badge: PENDING | EN_ROUTE | ON_SCENE | COMPLETED
  Row click → highlights route on map

Resource Status tab:
  Two sections: Available | Deployed
  Each row: [icon] resource name | quantity | depot/location | status
  Low inventory: amber row highlight

SITREP tab:
  Rendered markdown (react-markdown)
  "Download PDF" button (top right)
  "Regenerate" button (calls Agent 6 again)
  Timestamp + "Generated by CIRO AI" attribution

T2 Operations tab (only visible when Track 2 active):
  Agency grid: each agency card showing deployed/available/gap
  De-confliction map (small inline map showing coverage overlaps)
  Coordination messages log
```

### Track 2 Right Panel (when active)

```
"MULTI-AGENCY COORDINATION" header
[Active since 2 hr 14 min]

AGENCY STATUS (scrollable):
  Per agency card:
    [Agency name + logo placeholder]
    Deployed: N units
    Coverage: [area name]
    Last update: 14 min ago
  Expand → shows detailed inventory

RESOURCE GAPS:
  Quick summary table
  Item | Required | Available | Gap
  Color code gaps: red if gap > 0

"Generate SITREP" primary button
"Broadcast to Agencies" button
```

---

## 10. Design Checklist (must pass before production)

### Accessibility
- [ ] All color combinations pass WCAG AA contrast (4.5:1 text, 3:1 UI components)
- [ ] Focus rings visible on all interactive elements (keyboard nav)
- [ ] Touch targets minimum 48×48pt on mobile
- [ ] Screen reader labels on all icons and icon-only buttons
- [ ] Loading states have `aria-live` announcements
- [ ] Urdu text has correct `lang="ur"` + `dir="rtl"` attributes

### Responsiveness (Dashboard)
- [ ] 1024px: right panel collapses into a tab
- [ ] 1280px: bottom panel reduced height
- [ ] 1440px+: full layout

### Performance
- [ ] Map tiles load within 2s on 4G
- [ ] First meaningful paint < 1.5s
- [ ] Crisis list renders 100+ items without jank (virtualized)
- [ ] Agent trace handles 10K+ log lines (windowed rendering)
- [ ] Voice alert audio is pre-cached when user enters affected zone

### Offline (Mobile)
- [ ] Last crisis state cached in AsyncStorage
- [ ] Voice alert audio cached locally
- [ ] App launches and shows cached data without internet
- [ ] Offline banner displayed: "Last updated X min ago — No connection"
- [ ] Citizen report queued locally if offline, sent when connection restored

### States (every screen must handle these)
- [ ] Loading (skeleton screens, not spinners except for actions)
- [ ] Empty (meaningful message + suggested action)
- [ ] Error (specific error, retry button)
- [ ] Offline (cached data + "offline" badge)
- [ ] No crises active ("All clear")

### Language
- [ ] Every user-facing string has Urdu translation
- [ ] RTL layout tested (flip icon positions, text alignment)
- [ ] Long Urdu strings don't break layouts
- [ ] Bilingual alert text readable at glance
