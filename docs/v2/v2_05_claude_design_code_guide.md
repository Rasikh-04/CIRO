# CIRO v2 — Using Claude Design + Claude Code for UI Development
## The Exact Workflow for Building the Mobile App and Dashboard

---

## 1. Overview: Two-Phase Approach

**Phase 1 — Design (Claude.ai web, using Projects)**
Use Claude's design understanding to generate complete component code from design specs. Do this iteratively, screen by screen.

**Phase 2 — Implementation (Claude Code in terminal)**
Use Claude Code to implement, test, debug, and iterate on the generated code in the actual project. It has access to your full codebase.

These two phases hand off at a clear point: Phase 1 produces component code files. Phase 2 integrates them, fixes package issues, runs tests, and builds.

---

## 2. Phase 1: Claude Web (Design) — Setup

### Create a Project
In Claude.ai → Projects → Create "CIRO Mobile App" and "CIRO Dashboard".

Add these as Project Instructions:

```
You are building the CIRO crisis management app for Pakistan.

Tech stack:
- Mobile: React Native 0.81.5, Expo SDK 54, TypeScript
- Web: React 18, Vite, Tailwind CSS, TypeScript, Leaflet.js
- State: React Query + Zustand
- Navigation (mobile): React Navigation v6

Design system (use these exactly):
- Primary bg: #0A1628
- Surface bg: #132743
- Elevated bg: #1B3558
- Accent primary (CTA, critical actions): #FF6B35
- Accent secondary (info, links): #3D9EFF
- Critical: #FF3B3B | High: #FF6B35 | Medium: #FFB830 | Low: #3ECF8E
- Text primary: #F0F4F8 | Secondary: #8BA0B5 | Muted: #4A6580
- Border: #1E3A56
- Font sizes: 11/13/15/17/20/24/32/40px
- Base spacing: 4px grid (4/8/12/16/20/24/32/48px)
- Border radius: 6/12/16/100px
- Touch targets: minimum 48×48pt
- Use Lucide React (web) or @expo/vector-icons Feather (mobile) for icons

Rules:
- TypeScript only — every component has proper types
- No inline styles on mobile — use StyleSheet.create()
- Tailwind only on web — no inline style objects
- Every component handles: loading, error, empty, offline states
- Every text element that shows to users must have an Urdu translation prop
- Use react-native-maps for maps (already installed)
- Don't install new packages without listing them first
```

---

## 3. Phase 1: How to Prompt Claude for Each Component

### Strategy: Give Code Context + Spec Section + Ask for One Component

The key insight: Claude produces best UI code when given (1) the relevant spec section, (2) a code snippet showing what's already wired up, and (3) one focused task.

**Template prompt:**

```
Here is the relevant spec for what I need:
[paste the relevant section from v2_04_uiux_spec.md]

Here is my existing code context:
[paste the relevant existing file or the screen's current scaffold]

Here is the data shape this component receives:
[paste the relevant TypeScript interface from your types file]

Build [COMPONENT NAME] that:
- Exactly matches the spec
- Is fully typed (TypeScript)
- Handles loading, error, and empty states
- Includes the Urdu text variant for all user-visible strings
- Uses the design system tokens from Project Instructions

Output only the component file. No explanations.
```

### What to Provide (Code Context Snippets)

**For mobile components:**
```
// Provide these snippets each time:
// 1. Your types/crisis.ts (the data interfaces)
// 2. The screen file that will import the component
// 3. Any existing hook or API call the component will use
```

**For dashboard components:**
```
// Provide these snippets:
// 1. Your types/index.ts
// 2. The relevant Zustand store slice
// 3. The WebSocket hook
```

---

## 4. Component Build Order (Mobile)

Build in this exact order — each component builds on the previous:

### Week 1: Foundation
1. `src/theme/colors.ts` — all color tokens as TypeScript constants
2. `src/theme/typography.ts` — type scale and font stack  
3. `src/theme/spacing.ts` — spacing system
4. `src/components/ui/Badge.tsx` — severity badge (used everywhere)
5. `src/components/ui/StatusPill.tsx` — "LIVE" / "OFFLINE" pill
6. `src/components/ui/BilingualText.tsx` — renders English + Urdu in one component
7. `src/hooks/useCrisisData.ts` — React Query hook for all crisis fetching
8. `src/hooks/useVoiceAlert.ts` — play/stop/cache voice alerts

**Prompt example for colors.ts:**
```
Build src/theme/colors.ts with the Naval Command color system from my Project Instructions.
Export a Colors object and a useColors() hook that returns the theme.
Also export a getSeverityColor(severity: 1|2|3|4|5) function.
TypeScript. No comments, just clean code.
```

### Week 2: Core Screens
9. `src/components/crisis/CrisisCard.tsx`
10. `src/screens/HomeScreen.tsx` — map + bottom sheet
11. `src/screens/CrisisDetailScreen.tsx`
12. `src/screens/AlertsScreen.tsx`

**Prompt example for CrisisCard:**
```
Here is the spec for CrisisCard (from §7.1 of the UI spec):
[paste §7.1]

Here is my CrisisEvent type:
[paste types/crisis.ts]

Here is the screen where it will be used:
[paste current HomeScreen.tsx]

Build CrisisCard.tsx. It receives a CrisisEvent and an optional onPress handler.
The 4px left border must use getSeverityColor(crisis.severity).
Use React Native StyleSheet, not inline styles.
Include a CrisisCardSkeleton loading variant.
```

### Week 3: Advanced Screens
13. `src/screens/SafeRoutesScreen.tsx`
14. `src/screens/ReportIncidentScreen.tsx`
15. `src/screens/ProfileScreen.tsx`
16. `src/services/voiceAlert.ts` — download, cache, play logic
17. `src/services/offlineCache.ts` — AsyncStorage crisis state caching

---

## 5. Component Build Order (Dashboard)

### Foundation
1. `src/theme/index.ts` — CSS variables as JS constants (mirrors mobile theme)
2. `src/components/ui/` — Badge, StatusPill, Button, Card (Tailwind versions)
3. `src/hooks/useCrisisWebSocket.ts`
4. `src/hooks/useCrisisData.ts`

### Core Layout
5. `src/components/layout/Header.tsx`
6. `src/components/layout/LeftPanel.tsx` — crisis list
7. `src/components/layout/BottomPanel.tsx` — tabs
8. `src/components/layout/RightPanel.tsx` — Track 2

### Map
9. `src/components/map/CrisisMap.tsx` — main Leaflet map
10. `src/components/map/CrisisZoneLayer.tsx`
11. `src/components/map/RouteLayer.tsx`
12. `src/components/map/TrafficToggle.tsx`

### Bottom Panel Tabs
13. `src/components/tabs/AgentTraceTab.tsx`
14. `src/components/tabs/DispatchOrdersTab.tsx`
15. `src/components/tabs/ResourceStatusTab.tsx`
16. `src/components/tabs/SITREPTab.tsx`
17. `src/components/tabs/Track2OpsTab.tsx`

---

## 6. Phase 2: Claude Code — Integration & Testing

### Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
cd ciro/mobile-app
claude  # starts Claude Code in the project
```

### Initial Context Setup

When you start Claude Code in the mobile app, give this context:

```
I'm working on CIRO, a crisis management React Native app (Expo SDK 54, RN 0.81.5, TypeScript).
The project is in /mobile-app.
We're using @expo/vector-icons for icons, react-native-maps for maps, React Navigation v6 for navigation.

Rules for this session:
1. Never install packages with known vulnerabilities (check npm audit)
2. Always use Expo SDK 54 compatible package versions
3. Run `npx expo install` instead of `npm install` for packages that need Expo compatibility
4. After any package install, run: npx expo-doctor to verify compatibility
5. For gradle/Android issues, check android/app/build.gradle for conflicts
6. Run TypeScript check after every significant change: npx tsc --noEmit
7. Test that the app builds before saying something is done: npx expo start --no-dev and confirm no Metro errors
```

### Claude Code Tasks to Give

**Task type 1: Fix existing broken screens**
```
The HomeScreen is showing a blank map. 
I have react-native-maps installed.
My Google Maps API key is in AndroidManifest.xml as GOOGLE_MAPS_KEY.
The component code is in src/screens/HomeScreen.tsx.
Diagnose and fix the map rendering issue.
Check: Is the key loaded correctly? Is the MapView import correct for Expo?
Don't change the visual design — only fix the broken map.
```

**Task type 2: Integrate component from Claude Design**
```
I just created src/components/crisis/CrisisCard.tsx from design work.
Integrate it into HomeScreen.tsx to replace the existing placeholder list.
The data comes from the useCrisisData() hook.
After integration, run tsc --noEmit to verify types are correct.
```

**Task type 3: Fix package issues**
```
Run: npm audit
For any HIGH or CRITICAL vulnerabilities:
1. Check if there's a patched version compatible with Expo SDK 54
2. Use `npx expo install [package]@[compatible-version]` to update
3. After updates: run npx expo-doctor and confirm 0 issues
4. Run: npx tsc --noEmit to confirm no type errors introduced
5. Show me the final npm audit output
```

**Task type 4: Build verification**
```
Verify the Android build is working:
1. cd android && ./gradlew clean
2. cd android && ./gradlew assembleDebug
3. If it fails, diagnose the build.gradle issue
4. Do not change the app logic — only fix build configuration
5. Show me the final build output
```

**Task type 5: Automated testing**
```
Write Vitest unit tests for src/services/voiceAlert.ts.
Tests should cover:
- downloadAndCacheAudio() caches correctly
- playAlert() plays cached audio
- playAlert() downloads if not cached
- handles network failure gracefully (shows error, doesn't crash)
Use mock for expo-av and expo-file-system.
Run the tests after writing them.
```

---

## 7. Package Management Rules (Claude Code must follow these)

Always give Claude Code these rules at the start of a package-touching session:

```
Package management rules:
1. For Expo projects: use `npx expo install` NOT `npm install` for anything touch Expo
2. Check Expo SDK 54 compatibility at: https://docs.expo.dev/versions/v54.0.0/
3. Never install these vulnerable packages: node-fetch <3, axios <1.6.0, tough-cookie <4.1.3
4. For react-native-maps: use the version specified at docs.expo.dev, don't upgrade without checking
5. After any install: run `npx expo-doctor` and fix ALL issues it reports
6. If expo-doctor reports incompatible packages: downgrade to compatible versions
7. Lock file: always commit package-lock.json changes, never delete it
8. Security: run `npm audit --audit-level=high` — NO high/critical vulnerabilities in production build
```

---

## 8. Voice Alert Implementation Guide

This is complex enough to walk through step by step.

### Step 1: Generate audio files (once, store in Cloud Storage)

```python
# scripts/generate_voice_alerts.py
# Run this script to generate all static voice alert audio files
# These are pre-recorded versions for common crisis types

ALERT_TEMPLATES = {
    "flood_warning_urdu": "خبردار: {علاقے} میں شدید سیلاب آ رہا ہے۔ فوری طور پر محفوظ مقام پر جائیں۔",
    "flood_warning_english": "WARNING: Severe flooding occurring in {area}. Move to higher ground immediately.",
    "road_blocked_urdu": "{سڑک} بند ہے۔ {متبادل راستہ} استعمال کریں۔",
    "road_blocked_english": "{road} is blocked. Use {alternate} instead.",
    "all_clear_urdu": "صورتحال معمول پر آ گئی ہے۔ احتیاط جاری رکھیں۔",
    "all_clear_english": "Situation has normalized. Continue to exercise caution.",
}
```

### Step 2: Mobile — play cached alert

```typescript
// src/services/voiceAlert.ts
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

const CACHE_DIR = FileSystem.cacheDirectory + 'voice_alerts/';

export async function playVoiceAlert(alertUrl: string, crisisId: string): Promise<void> {
  const filename = CACHE_DIR + crisisId + '.mp3';
  
  // Check cache
  const cached = await FileSystem.getInfoAsync(filename);
  if (!cached.exists) {
    // Download
    await FileSystem.makeDirectoryAsync(CACHE_DIR, { intermediates: true });
    await FileSystem.downloadAsync(alertUrl, filename);
  }
  
  // Play
  const { sound } = await Audio.Sound.createAsync({ uri: filename });
  await sound.playAsync();
}

export async function preCacheAlert(alertUrl: string, crisisId: string): Promise<void> {
  // Called when user enters affected zone — pre-caches for offline use
  const filename = CACHE_DIR + crisisId + '.mp3';
  const cached = await FileSystem.getInfoAsync(filename);
  if (!cached.exists) {
    await FileSystem.makeDirectoryAsync(CACHE_DIR, { intermediates: true });
    await FileSystem.downloadAsync(alertUrl, filename);
  }
}
```

### Step 3: Trigger based on location

```typescript
// src/hooks/useLocationAlerts.ts
import * as Location from 'expo-location';
import { useEffect } from 'react';
import { useCrisisData } from './useCrisisData';
import { preCacheAlert, playVoiceAlert } from '../services/voiceAlert';
import { isPointInCircle } from '../utils/geo';

export function useLocationAlerts() {
  const { data: crises } = useCrisisData();
  
  useEffect(() => {
    let subscription: Location.LocationSubscription;
    
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') return;
      
      subscription = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.Balanced, timeInterval: 30000 },
        (location) => {
          crises?.forEach(async (crisis) => {
            if (isPointInCircle(
              location.coords.latitude,
              location.coords.longitude,
              crisis.lat,
              crisis.lng,
              crisis.affected_radius_km * 1.5  // Alert radius is larger than crisis zone
            )) {
              // Pre-cache the audio
              if (crisis.alert_audio_url) {
                await preCacheAlert(crisis.alert_audio_url, crisis.id);
              }
              // Auto-play if severity ≥ 4
              if (crisis.severity >= 4 && crisis.alert_audio_url) {
                await playVoiceAlert(crisis.alert_audio_url, crisis.id);
              }
            }
          });
        }
      );
    })();
    
    return () => subscription?.remove();
  }, [crises]);
}
```

---

## 9. When to Use Which Tool

| Task | Tool | Notes |
|---|---|---|
| Design a new screen from spec | Claude.ai web (Project) | Paste spec + existing code context |
| Fix broken map/navigation | Claude Code | Has access to full project |
| Package vulnerabilities | Claude Code | Runs npm audit, fixes with expo install |
| Gradle build failures | Claude Code | Reads build.gradle, fixes config |
| Write tests | Claude Code | Has access to the actual function signatures |
| Refactor for performance | Claude Code | Can run tsc and lint after changes |
| Iterate design (colors, spacing) | Claude.ai web | Faster iteration on visual code |
| Debug API integration | Claude Code | Can read actual error logs and types |
| Generate SITREP prompt | Claude.ai web | Creative/reasoning task |
| Supabase schema migration | Claude Code | Can test against actual DB schema |
