import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  Animated,
  Dimensions,
  FlatList,
  PanResponder,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import MapView, { Circle, Marker } from 'react-native-maps';
import { useFocusEffect } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { fetchActiveCrises } from '../lib/api';
import type { CrisisEvent } from '../types';
import { getSeverityColorFromPalette } from '../theme/colors';
import { useTheme } from '../theme/ThemeContext';
import { FontSizes, FontWeights } from '../theme/typography';
import { Space, Radii, TouchTargetMin } from '../theme/spacing';
import CrisisCard from '../components/ui/CrisisCard';

interface HomeScreenProps {
  navigation: { navigate: (screen: string, params?: Record<string, unknown>) => void };
}

const { height: SCREEN_HEIGHT } = Dimensions.get('window');
const POLL_INTERVAL_MS = 30_000;

const ISLAMABAD_REGION = {
  latitude: 33.6844,
  longitude: 73.0479,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
} as const;

const SNAP_PEEK = 240;
const SNAP_HALF = Math.round(SCREEN_HEIGHT * 0.5);
const SNAP_FULL = SCREEN_HEIGHT - 80;

const SNAP_POINTS = [SNAP_PEEK, SNAP_HALF, SNAP_FULL] as const;
type SnapPoint = (typeof SNAP_POINTS)[number];

const DRAG_THRESHOLD = 20;
const CRISIS_CARD_WIDTH = 280;
const CRISIS_CARD_HEIGHT = 96;

function nearestSnap(value: number): SnapPoint {
  return SNAP_POINTS.reduce<SnapPoint>((closest, snap) =>
    Math.abs(snap - value) < Math.abs(closest - value) ? snap : closest,
  SNAP_PEEK);
}

function snapAbove(current: SnapPoint): SnapPoint {
  const idx = SNAP_POINTS.indexOf(current);
  return idx < SNAP_POINTS.length - 1 ? SNAP_POINTS[idx + 1] : SNAP_FULL;
}

function snapBelow(current: SnapPoint): SnapPoint {
  const idx = SNAP_POINTS.indexOf(current);
  return idx > 0 ? SNAP_POINTS[idx - 1] : SNAP_PEEK;
}

function formatUpdated(iso: string | undefined): string {
  if (!iso) return 'just now';
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 1) return 'just now';
  if (mins === 1) return '1 min ago';
  return `${mins} min ago`;
}

function SkeletonCard(): React.JSX.Element {
  const { colors } = useTheme();
  const pulse = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 750, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.4, duration: 750, useNativeDriver: true }),
      ]),
    ).start();
  }, [pulse]);

  return (
    <Animated.View
      style={[
        skeletonLayout.card,
        {
          opacity: pulse,
          backgroundColor: colors.bgElevated,
          borderColor: colors.border,
          borderLeftColor: colors.border,
        },
      ]}
    >
      <View style={[skeletonLayout.line, { backgroundColor: colors.border }]} />
      <View style={[skeletonLayout.line, skeletonLayout.lineMid, { backgroundColor: colors.border }]} />
      <View style={[skeletonLayout.line, skeletonLayout.lineShort, { backgroundColor: colors.border }]} />
    </Animated.View>
  );
}

// Layout-only styles for SkeletonCard — no colors
const skeletonLayout = StyleSheet.create({
  card: {
    width: CRISIS_CARD_WIDTH,
    height: CRISIS_CARD_HEIGHT,
    borderRadius: Radii.md,
    borderWidth: 1,
    borderLeftWidth: 4,
    marginRight: Space[3],
    overflow: 'hidden',
    justifyContent: 'space-evenly',
    paddingHorizontal: Space[3],
  },
  line: { height: 12, borderRadius: Radii.sm, width: '80%' },
  lineMid: { width: '60%' },
  lineShort: { width: '40%' },
});

const SORT_OPTIONS = ['SEVERITY', 'TIME', 'DISTANCE'] as const;
type SortOption = (typeof SORT_OPTIONS)[number];

export default function HomeScreen({ navigation }: HomeScreenProps): React.JSX.Element {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const [crises, setCrises] = useState<CrisisEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string | undefined>(undefined);
  const [sort, setSort] = useState<SortOption>('SEVERITY');

  const styles = useMemo(() => StyleSheet.create({
    root: { flex: 1, backgroundColor: colors.bgPrimary },
    header: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 10,
      backgroundColor: colors.bgPrimary + 'D9', // ~85% opacity
      flexDirection: 'row',
      alignItems: 'flex-end',
      justifyContent: 'space-between',
      paddingHorizontal: Space[4],
      paddingBottom: Space[3],
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerLogo: {
      fontSize: FontSizes.lg,
      fontWeight: FontWeights.bold,
      color: colors.textPrimary,
      letterSpacing: 2,
    },
    headerRight: { flexDirection: 'row', alignItems: 'center', gap: Space[3] },
    headerBadge: {
      backgroundColor: colors.statusCritical,
      borderRadius: Radii.pill,
      minWidth: 20,
      height: 20,
      paddingHorizontal: Space[1],
      alignItems: 'center',
      justifyContent: 'center',
    },
    headerBadgeText: { fontSize: FontSizes.xs, fontWeight: FontWeights.bold, color: colors.textPrimary },
    headerIcon: { width: TouchTargetMin, height: TouchTargetMin, alignItems: 'center', justifyContent: 'center' },
    sheet: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: colors.bgSurface,
      borderTopLeftRadius: Radii.lg,
      borderTopRightRadius: Radii.lg,
      borderWidth: 1,
      borderBottomWidth: 0,
      borderColor: colors.border,
      elevation: 12,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: -4 },
      shadowOpacity: 0.35,
      shadowRadius: 12,
    },
    dragArea: { width: '100%', height: 28, alignItems: 'center', justifyContent: 'center' },
    dragHandle: {
      width: 32,
      height: 4,
      borderRadius: 2,
      backgroundColor: colors.textMuted,
      marginTop: Space[2],
    },
    sheetContent: { flex: 1, overflow: 'hidden' },
    countHeader: { paddingHorizontal: Space[4], paddingBottom: Space[3] },
    countLabel: { fontSize: FontSizes.sm, fontWeight: FontWeights.semibold, letterSpacing: 0.5 },
    countSubtitle: { fontSize: FontSizes.xs, color: colors.textSecondary, marginTop: 2 },
    cardListContent: { paddingHorizontal: Space[4], paddingBottom: Space[2] },
    verticalListContent: { paddingHorizontal: Space[4], paddingBottom: Space[4], gap: Space[3] },
    crisisCardHorizontal: {
      width: CRISIS_CARD_WIDTH,
      height: CRISIS_CARD_HEIGHT,
      marginRight: Space[3],
    },
    sectionLabel: {
      fontSize: FontSizes.xs,
      fontWeight: FontWeights.semibold,
      color: colors.textSecondary,
      letterSpacing: 0.8,
      paddingHorizontal: Space[4],
      paddingBottom: Space[3],
    },
    sortRow: { flexDirection: 'row', gap: Space[2], paddingHorizontal: Space[4], paddingBottom: Space[3] },
    sortPill: {
      paddingHorizontal: Space[3],
      paddingVertical: Space[1],
      borderRadius: Radii.pill,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: 'transparent',
    },
    sortPillActive: { backgroundColor: colors.accentPrimary + '22', borderColor: colors.accentPrimary },
    sortPillText: { fontSize: FontSizes.xs, fontWeight: FontWeights.semibold, color: colors.textMuted, letterSpacing: 0.5 },
    sortPillTextActive: { color: colors.accentPrimary },
    emptyPeek: { flexDirection: 'row', alignItems: 'center', gap: Space[3], paddingHorizontal: Space[4], paddingTop: Space[2] },
    emptyPeekText: { fontSize: FontSizes.sm, color: colors.textSecondary },
    emptyFull: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: Space[2], paddingBottom: Space[8] },
    emptyFullText: { fontSize: FontSizes.base, fontWeight: FontWeights.medium, color: colors.textPrimary },
    emptyFullSub: { fontSize: FontSizes.sm, color: colors.textMuted },
  }), [colors]);

  const loadCrises = useCallback(async () => {
    const data = await fetchActiveCrises();
    setCrises(data);
    setLastUpdated(new Date().toISOString());
    setLoading(false);
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      void loadCrises();
    }, [loadCrises]),
  );

  useEffect(() => {
    const id = setInterval(() => void loadCrises(), POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [loadCrises]);

  const sortedCrises = useMemo(() => {
    const copy = [...crises];
    if (sort === 'SEVERITY') return copy.sort((a, b) => b.severity - a.severity);
    if (sort === 'TIME')
      return copy.sort(
        (a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime(),
      );
    return copy;
  }, [crises, sort]);

  const sheetHeight = useRef(new Animated.Value(SNAP_PEEK)).current;
  const currentSnap = useRef<SnapPoint>(SNAP_PEEK);
  const dragStart = useRef(0);

  function animateTo(snap: SnapPoint): void {
    currentSnap.current = snap;
    Animated.spring(sheetHeight, {
      toValue: snap,
      useNativeDriver: false,
      bounciness: 4,
    }).start();
  }

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dy) > 4,
      onPanResponderGrant: () => {
        sheetHeight.stopAnimation((v) => {
          dragStart.current = v;
        });
      },
      onPanResponderMove: (_, g) => {
        const next = Math.min(SNAP_FULL, Math.max(SNAP_PEEK, dragStart.current - g.dy));
        sheetHeight.setValue(next);
      },
      onPanResponderRelease: (_, g) => {
        const current = currentSnap.current;
        if (g.dy < -DRAG_THRESHOLD) {
          animateTo(snapAbove(current));
        } else if (g.dy > DRAG_THRESHOLD) {
          animateTo(snapBelow(current));
        } else {
          animateTo(nearestSnap(dragStart.current - g.dy));
        }
      },
    }),
  ).current;

  const [visibleSnap, setVisibleSnap] = useState<SnapPoint>(SNAP_PEEK);
  useEffect(() => {
    const id = sheetHeight.addListener(({ value }) => {
      setVisibleSnap(nearestSnap(value));
    });
    return () => sheetHeight.removeListener(id);
  }, [sheetHeight]);

  const goToDetail = useCallback(
    (crisisId: string) => navigation.navigate('CrisisDetail', { crisisId }),
    [navigation],
  );

  const headerHeight = 52 + insets.top;
  const activeCrises = crises.filter((c) => c.status !== 'resolved');
  const countLabel = activeCrises.length > 0 ? `● ${activeCrises.length} ACTIVE CRISIS` : '● ALL CLEAR';
  const countColor = activeCrises.length > 0 ? colors.statusCritical : colors.statusLow;

  return (
    <View style={styles.root}>
      <MapView
        style={StyleSheet.absoluteFillObject}
        initialRegion={ISLAMABAD_REGION}
        showsUserLocation
        showsMyLocationButton={false}
        mapType="standard"
      >
        {crises.map((crisis) => {
          const color = getSeverityColorFromPalette(crisis.severity, colors);
          return (
            <React.Fragment key={crisis.id}>
              <Circle
                center={{ latitude: crisis.location.lat, longitude: crisis.location.lng }}
                radius={Math.max(100, (crisis.affected_radius_km || 2.5) * 1000)}
                fillColor={color + '55'}
                strokeColor={color + '99'}
                strokeWidth={2}
              />
              {/* react-native-maps doesn't fire onPress on Circle — invisible Marker is the workaround */}
              <Marker
                coordinate={{ latitude: crisis.location.lat, longitude: crisis.location.lng }}
                onPress={() => goToDetail(crisis.id)}
                opacity={0}
              />
            </React.Fragment>
          );
        })}
      </MapView>

      <View style={[styles.header, { paddingTop: insets.top, height: headerHeight }]}>
        <Text style={styles.headerLogo}>CIRO</Text>
        <View style={styles.headerRight}>
          {activeCrises.length > 0 && (
            <View style={styles.headerBadge}>
              <Text style={styles.headerBadgeText}>{activeCrises.length}</Text>
            </View>
          )}
          <TouchableOpacity style={styles.headerIcon} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Feather name="bell" size={20} color={colors.textPrimary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerIcon} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Feather name="mic" size={20} color={colors.textMuted} />
          </TouchableOpacity>
        </View>
      </View>

      <Animated.View style={[styles.sheet, { height: sheetHeight }]}>
        <View {...panResponder.panHandlers} style={styles.dragArea}>
          <View style={styles.dragHandle} />
        </View>

        {visibleSnap === SNAP_PEEK && (
          <View style={styles.sheetContent}>
            <View style={styles.countHeader}>
              <Text style={[styles.countLabel, { color: countColor }]}>{countLabel}</Text>
              <Text style={styles.countSubtitle}>
                Islamabad{'  '}·{'  '}Updated {formatUpdated(lastUpdated)}
              </Text>
            </View>

            {loading ? (
              <FlatList
                horizontal
                data={[1, 2, 3]}
                keyExtractor={(i) => String(i)}
                renderItem={() => <SkeletonCard />}
                contentContainerStyle={styles.cardListContent}
                showsHorizontalScrollIndicator={false}
              />
            ) : crises.length === 0 ? (
              <View style={styles.emptyPeek}>
                <Feather name="check-circle" size={24} color={colors.statusResolved} />
                <Text style={styles.emptyPeekText}>No active crises in your area</Text>
              </View>
            ) : (
              <FlatList
                horizontal
                data={crises}
                keyExtractor={(c) => c.id}
                renderItem={({ item }) => (
                  <CrisisCard
                    crisis={item}
                    onPress={() => goToDetail(item.id)}
                    style={styles.crisisCardHorizontal}
                  />
                )}
                contentContainerStyle={styles.cardListContent}
                showsHorizontalScrollIndicator={false}
                snapToInterval={CRISIS_CARD_WIDTH + Space[3]}
                decelerationRate="fast"
                snapToAlignment="start"
              />
            )}
          </View>
        )}

        {visibleSnap === SNAP_HALF && (
          <View style={styles.sheetContent}>
            <Text style={styles.sectionLabel}>ACTIVE CRISES</Text>
            {loading ? (
              [1, 2, 3].map((k) => <SkeletonCard key={k} />)
            ) : crises.length === 0 ? (
              <View style={styles.emptyFull}>
                <Feather name="check-circle" size={32} color={colors.statusResolved} />
                <Text style={styles.emptyFullText}>No active crises</Text>
                <Text style={styles.emptyFullSub}>Last checked {formatUpdated(lastUpdated)}</Text>
              </View>
            ) : (
              <FlatList
                data={sortedCrises}
                keyExtractor={(c) => c.id}
                renderItem={({ item }) => (
                  <CrisisCard crisis={item} onPress={() => goToDetail(item.id)} />
                )}
                contentContainerStyle={styles.verticalListContent}
                showsVerticalScrollIndicator={false}
              />
            )}
          </View>
        )}

        {visibleSnap === SNAP_FULL && (
          <View style={styles.sheetContent}>
            <View style={styles.sortRow}>
              {SORT_OPTIONS.map((opt) => (
                <TouchableOpacity
                  key={opt}
                  style={[styles.sortPill, sort === opt && styles.sortPillActive]}
                  onPress={() => setSort(opt)}
                >
                  <Text style={[styles.sortPillText, sort === opt && styles.sortPillTextActive]}>
                    {opt}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {loading ? (
              [1, 2, 3].map((k) => <SkeletonCard key={k} />)
            ) : crises.length === 0 ? (
              <View style={styles.emptyFull}>
                <Feather name="check-circle" size={32} color={colors.statusResolved} />
                <Text style={styles.emptyFullText}>No active crises</Text>
                <Text style={styles.emptyFullSub}>Last checked {formatUpdated(lastUpdated)}</Text>
              </View>
            ) : (
              <FlatList
                data={sortedCrises}
                keyExtractor={(c) => c.id}
                renderItem={({ item }) => (
                  <CrisisCard crisis={item} onPress={() => goToDetail(item.id)} />
                )}
                contentContainerStyle={styles.verticalListContent}
                showsVerticalScrollIndicator={false}
              />
            )}
          </View>
        )}
      </Animated.View>
    </View>
  );
}
