# CIRO v2 — Testing Strategy
## Automated Testing for Every Component

---

## 1. Testing Philosophy

**Test from the outside in.** The most valuable tests are:
1. End-to-end: inject a signal, verify a public alert is generated
2. Integration: agent receives Pub/Sub event, produces correct output schema
3. Unit: business logic (confidence scoring, dispatch priority, deduplication)

Don't test frameworks or libraries. Don't test that FastAPI routes exist. Test that CIRO's logic is correct.

---

## 2. Backend Tests (pytest)

```bash
cd backend
pip install pytest pytest-asyncio pytest-httpx
pytest tests/ -v --tb=short
```

### Test Files Structure
```
backend/tests/
├── test_state_machine.py
├── test_agent_webhooks.py
├── test_crisis_api.py
├── test_deduplication.py
├── test_dispatch_logic.py
└── fixtures/
    ├── sample_signals.json
    ├── sample_crisis.json
    └── sample_ndma_report.pdf
```

### `test_state_machine.py`
```python
import pytest
from app.core.state_machine import transition, InvalidTransitionError

@pytest.mark.asyncio
async def test_valid_transition_detected():
    """Crisis in monitoring state can transition to detected."""
    result = await transition("CRS_TEST", "detected", source="agent_2_test")
    assert result.new_status == "detected"

@pytest.mark.asyncio
async def test_cannot_skip_states():
    """Cannot jump from detected to simulated."""
    with pytest.raises(InvalidTransitionError):
        await transition("CRS_TEST", "simulated", source="test")

@pytest.mark.asyncio
async def test_resolved_is_terminal():
    """Resolved crisis cannot transition back to active states."""
    with pytest.raises(InvalidTransitionError):
        await transition("CRS_RESOLVED", "detected", source="test")

@pytest.mark.asyncio
async def test_audit_log_entry_created():
    """Every transition creates an audit log entry."""
    await transition("CRS_AUDIT_TEST", "detected", source="agent_2", reasoning="test")
    logs = await db.get_audit_log("CRS_AUDIT_TEST")
    assert len(logs) == 1
    assert logs[0].event_type == "state_change"
    assert logs[0].reasoning == "test"
```

### `test_deduplication.py`
```python
@pytest.mark.asyncio
async def test_semantic_duplicate_detected():
    """Two posts about the same flood are marked as duplicates."""
    signal_1 = SignalEvent(
        normalized="G-10 flooding, vehicles stranded on Srinagar Highway",
        location={"lat": 33.6844, "lng": 73.0479},
        signal_type="flood",
        timestamp=now()
    )
    signal_2 = SignalEvent(
        normalized="Srinagar Highway completely flooded near G-10, cars stuck",
        location={"lat": 33.6850, "lng": 73.0485},
        signal_type="flood",
        timestamp=now() + timedelta(minutes=5)
    )
    result = await is_duplicate(signal_2, window_minutes=30)
    assert result == True

@pytest.mark.asyncio
async def test_different_location_not_duplicate():
    """Two floods in different districts are NOT duplicates."""
    # G-10 flood
    # I-8 flood (5km away)
    result = await is_duplicate(signal_i8, window_minutes=30)
    assert result == False
```

### `test_dispatch_logic.py`
```python
def test_priority_score_increases_with_severity():
    low_sev = DispatchZone(severity=2, distance_km=3, population=5000)
    high_sev = DispatchZone(severity=4, distance_km=3, population=5000)
    assert priority_score(high_sev) > priority_score(low_sev)

def test_ocha_gap_calculation():
    """10,000 people at risk should require correct number of tents."""
    gaps = calculate_gap(population=10_000, deployed={"tents": 500})
    assert gaps["gaps"]["tents"] == 1500  # 10000/5 - 500 = 1500

def test_dispatch_selects_nearest_available_unit():
    crisis_location = (33.6844, 73.0479)
    units = [
        Unit(name="Unit A", lat=33.7080, lng=73.0479, status="available"),
        Unit(name="Unit B", lat=33.6200, lng=73.0200, status="available"),  # farther
    ]
    selected = select_unit(units, crisis_location, "water_rescue")
    assert selected.name == "Unit A"
```

---

## 3. Agent Tests (pytest for each agent service)

Each agent has its own test file. Run within the agent's directory.

### `agents/agent_2_crisis_detection/tests/test_classify.py`
```python
@pytest.mark.asyncio
async def test_three_corroborating_signals_confirm_crisis():
    """3 signals from different sources → crisis confirmed."""
    signals = [
        make_signal(source="social_media", signal_type="flood", lat=33.6844, lng=73.0479),
        make_signal(source="weather_api", signal_type="flood", lat=33.6844, lng=73.0479),
        make_signal(source="traffic_api", signal_type="flood", lat=33.6844, lng=73.0479),
    ]
    result = await classify_signals(signals)
    assert result.status == "confirmed"
    assert result.confidence_score > 0.7

@pytest.mark.asyncio
async def test_single_signal_does_not_confirm():
    """1 social media signal → not enough to confirm."""
    signals = [make_signal(source="social_media", signal_type="flood")]
    result = await classify_signals(signals)
    assert result.status == "monitoring"  # Not confirmed

@pytest.mark.asyncio
async def test_sarcasm_filtered_by_normalization():
    """The sarcastic post from mock data should be filtered at A1, not reach A2."""
    # This is tested in Agent 1 tests — A2 should never receive it
    pass

def test_severity_assignment_flood():
    """Flood with weather corroboration + 3 signals → severity 4."""
    cluster = SignalCluster(
        signals=[...3 signals...],
        has_weather_corroboration=True,
        signal_count=3
    )
    assert estimate_severity("urban_flooding", cluster) == 4
```

### `agents/agent_5_simulation/tests/test_routing.py`
```python
@pytest.mark.asyncio
async def test_ors_failure_falls_back_to_haversine():
    """When OpenRouteService returns 500, fallback to straight-line."""
    with mock.patch("httpx.AsyncClient.post", side_effect=httpx.HTTPError("timeout")):
        route = await compute_route(order, closures=[])
    
    assert route.fallback == True
    assert route.fallback_reason is not None
    assert route.distance_km > 0  # Haversine gives a result

@pytest.mark.asyncio
async def test_route_avoids_blocked_roads():
    """Route must not pass through blocked Srinagar Highway."""
    closure = RoadClosure(
        road="Srinagar Highway",
        bbox=[(33.685, 73.050), (33.690, 73.060)]
    )
    route = await compute_route(f8_to_g10_order, closures=[closure])
    # Verify route waypoints don't intersect the closure bbox
    for wp in route.waypoints:
        assert not point_in_bbox(wp, closure.bbox)
```

---

## 4. Mobile App Tests (Vitest + React Native Testing Library)

```bash
cd mobile-app
npm install --save-dev vitest @testing-library/react-native
npx vitest run
```

### `src/services/__tests__/voiceAlert.test.ts`
```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest';
import * as FileSystem from 'expo-file-system';
import { Audio } from 'expo-av';
import { playVoiceAlert, preCacheAlert } from '../voiceAlert';

vi.mock('expo-file-system');
vi.mock('expo-av');

describe('Voice Alert Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('downloads audio if not cached', async () => {
    vi.mocked(FileSystem.getInfoAsync).mockResolvedValue({ exists: false } as any);
    vi.mocked(FileSystem.downloadAsync).mockResolvedValue({} as any);
    vi.mocked(Audio.Sound.createAsync).mockResolvedValue({
      sound: { playAsync: vi.fn() }
    } as any);

    await playVoiceAlert('https://example.com/alert.mp3', 'CRS_001');

    expect(FileSystem.downloadAsync).toHaveBeenCalledOnce();
  });

  it('uses cached file if available', async () => {
    vi.mocked(FileSystem.getInfoAsync).mockResolvedValue({ exists: true } as any);

    await playVoiceAlert('https://example.com/alert.mp3', 'CRS_001');

    expect(FileSystem.downloadAsync).not.toHaveBeenCalled();
  });

  it('handles network failure gracefully', async () => {
    vi.mocked(FileSystem.getInfoAsync).mockResolvedValue({ exists: false } as any);
    vi.mocked(FileSystem.downloadAsync).mockRejectedValue(new Error('Network error'));

    // Should not throw — should handle gracefully
    await expect(playVoiceAlert('...', 'CRS_001')).resolves.not.toThrow();
  });
});
```

### `src/hooks/__tests__/useCrisisData.test.ts`
```typescript
import { renderHook, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCrisisData } from '../useCrisisData';

const mockCrises = [{ id: 'CRS_001', type: 'urban_flooding', severity: 4 }];

global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve(mockCrises)
});

it('fetches and returns crisis data', async () => {
  const { result } = renderHook(() => useCrisisData(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={new QueryClient()}>
        {children}
      </QueryClientProvider>
    )
  });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data).toEqual(mockCrises);
});

it('handles offline gracefully', async () => {
  global.fetch = vi.fn().mockRejectedValue(new Error('Network Error'));
  // ... test that cached data is returned and isOffline is true
});
```

---

## 5. Dashboard Tests (Vitest + React Testing Library)

```bash
cd web-dashboard
npx vitest run
```

```typescript
// src/components/crisis/__tests__/CrisisCard.test.tsx
import { render, screen } from '@testing-library/react';
import { CrisisCard } from '../CrisisCard';

const mockCrisis = {
  id: 'CRS_001',
  type: 'urban_flooding',
  location_name: 'G-10, Islamabad',
  severity: 4,
  status: 'dispatched',
  detected_at: new Date().toISOString()
};

it('displays severity badge with correct color', () => {
  render(<CrisisCard crisis={mockCrisis} />);
  const badge = screen.getByText('HIGH');
  expect(badge).toHaveStyle({ color: '#FF6B35' });
});

it('shows left severity border', () => {
  const { container } = render(<CrisisCard crisis={mockCrisis} />);
  expect(container.firstChild).toHaveStyle({ borderLeftColor: '#FF6B35' });
});

it('renders skeleton when loading', () => {
  render(<CrisisCard loading />);
  expect(screen.getByTestId('crisis-card-skeleton')).toBeInTheDocument();
});
```

---

## 6. Running All Tests (CI script)

```bash
#!/bin/bash
# scripts/run_all_tests.sh
set -e  # Exit on first failure

echo "=== Backend Tests ==="
cd backend
python -m pytest tests/ -v --tb=short --no-header
cd ..

echo "=== Agent Tests ==="
for agent_dir in agents/agent_*/; do
  if [ -d "$agent_dir/tests" ]; then
    echo "--- Testing $agent_dir ---"
    cd "$agent_dir"
    python -m pytest tests/ -v --tb=short
    cd ../..
  fi
done

echo "=== Mobile App Tests ==="
cd mobile-app
npx tsc --noEmit
npx vitest run --reporter=verbose
npx expo-doctor
cd ..

echo "=== Web Dashboard Tests ==="
cd web-dashboard
npx tsc --noEmit
npx vitest run --reporter=verbose
cd ..

echo "=== Security Audit ==="
cd mobile-app && npm audit --audit-level=high
cd ../web-dashboard && npm audit --audit-level=high
cd ..

echo "=== All tests passed ==="
```

---

## 7. GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CIRO CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest tests/ -v

  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd mobile-app && npm ci
      - run: cd mobile-app && npx tsc --noEmit
      - run: cd mobile-app && npx vitest run
      - run: cd mobile-app && npm audit --audit-level=high

  dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd web-dashboard && npm ci
      - run: cd web-dashboard && npx tsc --noEmit
      - run: cd web-dashboard && npx vitest run
      - run: cd web-dashboard && npm audit --audit-level=high

  android-build:
    runs-on: ubuntu-latest
    needs: mobile
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { java-version: '17' }
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd mobile-app && npm ci
      - run: |
          cd mobile-app/android
          chmod +x gradlew
          ./gradlew assembleDebug
      - uses: actions/upload-artifact@v4
        with:
          name: debug-apk
          path: mobile-app/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 8. Android Build Verification (Claude Code Task)

Give Claude Code this exact task when the Gradle build breaks:

```
The Android build is failing. Here is the error output:
[paste full ./gradlew assembleDebug output]

Diagnose and fix the issue. Rules:
1. Only modify android/app/build.gradle, android/build.gradle, or android/settings.gradle
2. Do NOT modify any JavaScript/TypeScript source files
3. After fixing: run ./gradlew assembleDebug and show me the final output
4. If the fix requires a package version change: use `npx expo install [package]@[version]` 
   and then re-run the build
5. Show me the diff of what you changed
```

Common Android build issues and fixes:
- `Duplicate class kotlin.collections` → add `resolutionStrategy` to `build.gradle`
- `minSdkVersion` mismatch → align in `app/build.gradle`
- Missing `google-services.json` → add Firebase config
- Gradle JDK incompatibility → ensure JDK 17 in project
- `compileSdkVersion` too old for a dependency → bump to 34
