import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Platform,
  StatusBar,
} from 'react-native';
import MapView, { Circle } from 'react-native-maps';
import { Feather } from '@expo/vector-icons';
import type { CrisisDetail } from '../types';
import { fetchCrisisDetail } from '../lib/api';
import { getSeverityColor } from '../theme/colors';
import { useTheme } from '../theme/ThemeContext';
import type { ColorPalette } from '../theme/colors';
import SeverityBadge from '../components/ui/SeverityBadge';
import BilingualText from '../components/ui/BilingualText';

interface CrisisDetailScreenProps {
  route: { params: { crisisId: string } };
  navigation: { goBack: () => void };
}

const STATUS_BAR_HEIGHT =
  Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) : 44;

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-PK', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatCrisisType(type: string): string {
  return type.replace(/_/g, ' ').toUpperCase();
}

function getStatusColor(status: string, colors: ColorPalette): string {
  const map: Record<string, string> = {
    DETECTED:   colors.statusMedium,
    ANALYZED:   colors.accentSecondary,
    DISPATCHED: colors.statusHigh,
    SIMULATED:  colors.accentPrimary,
    RESOLVED:   colors.statusResolved,
  };
  return map[status.toUpperCase()] ?? colors.textSecondary;
}

function getDispatchStatusColor(status: string, colors: ColorPalette): string {
  const map: Record<string, string> = {
    PENDING:   colors.statusMedium,
    EN_ROUTE:  colors.accentSecondary,
    ON_SCENE:  colors.statusHigh,
    COMPLETED: colors.statusResolved,
  };
  return map[status.toUpperCase()] ?? colors.textSecondary;
}

function SectionLabel({ label, colors }: { label: string; colors: ColorPalette }) {
  return (
    <Text style={{ fontSize: 11, fontWeight: '700', letterSpacing: 0.8, color: colors.textSecondary, marginBottom: 4 }}>
      {label}
    </Text>
  );
}

function StatusPill({ status, colors }: { status: string; colors: ColorPalette }) {
  const color = getStatusColor(status, colors);
  return (
    <View style={[pillLayout.statusPill, { borderColor: color }]}>
      <View style={[pillLayout.statusDot, { backgroundColor: color }]} />
      <Text style={{ fontSize: 11, fontWeight: '700', letterSpacing: 0.5, color }}>{status.toUpperCase()}</Text>
    </View>
  );
}

function DispatchStatusPill({ status, colors }: { status: string; colors: ColorPalette }) {
  const color = getDispatchStatusColor(status, colors);
  return (
    <View style={[pillLayout.dispatchPill, { backgroundColor: color + '22', borderColor: color }]}>
      <Text style={{ fontSize: 10, fontWeight: '700', letterSpacing: 0.4, color }}>{status.toUpperCase()}</Text>
    </View>
  );
}

// Layout-only styles for pills — no colors
const pillLayout = StyleSheet.create({
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderWidth: 1,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  statusDot: { width: 6, height: 6, borderRadius: 3 },
  dispatchPill: { borderWidth: 1, borderRadius: 100, paddingHorizontal: 8, paddingVertical: 2 },
});

export default function CrisisDetailScreen({ route, navigation }: CrisisDetailScreenProps) {
  const { crisisId } = route.params;
  const { colors } = useTheme();

  const [detail, setDetail] = useState<CrisisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const styles = useMemo(() => StyleSheet.create({
    root: { flex: 1, backgroundColor: colors.bgPrimary },
    scroll: { flex: 1 },
    scrollContent: {
      paddingTop: STATUS_BAR_HEIGHT + 64,
      paddingHorizontal: 16,
      paddingBottom: 32,
      gap: 12,
    },
    centered: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.bgPrimary,
      padding: 24,
      gap: 12,
    },
    backButton: {
      position: 'absolute',
      top: STATUS_BAR_HEIGHT + 8,
      left: 16,
      zIndex: 10,
      width: 40,
      height: 40,
      borderRadius: 20,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.bgElevated,
      borderWidth: 1,
      borderColor: colors.border,
    },
    card: {
      backgroundColor: colors.bgSurface,
      borderRadius: 12,
      padding: 16,
      borderWidth: 1,
      borderColor: colors.border,
      gap: 10,
    },
    headerCard: { gap: 8 },
    mapCard: { padding: 0, overflow: 'hidden' },
    alertCard: { borderLeftWidth: 4, borderLeftColor: colors.accentSecondary },
    locationName: {
      fontSize: 20,
      fontWeight: '700',
      color: colors.textPrimary,
      lineHeight: 26,
    },
    detectedAtText: { fontSize: 11, fontWeight: '400', color: colors.textSecondary },
    map: { width: '100%', height: 180 },
    dispatchRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingVertical: 10,
    },
    dispatchRowBorder: { borderBottomWidth: 1, borderBottomColor: colors.border },
    dispatchInfo: { flex: 1, gap: 2 },
    dispatchUnit: { fontSize: 15, fontWeight: '600', color: colors.textPrimary },
    dispatchDestination: { fontSize: 13, fontWeight: '400', color: colors.textSecondary },
    dispatchRight: { alignItems: 'flex-end', gap: 4, marginLeft: 12 },
    etaText: { fontSize: 12, fontWeight: '500', color: colors.accentSecondary },
    simTicketRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
    simTicketId: { fontSize: 13, fontWeight: '500', color: colors.accentSecondary },
    simMetrics: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 4 },
    simMetricItem: { alignItems: 'center', gap: 2 },
    simMetricValue: { fontSize: 24, fontWeight: '700', color: colors.textPrimary, lineHeight: 28 },
    simMetricLabel: { fontSize: 11, fontWeight: '400', color: colors.textSecondary },
    simArrow: { marginHorizontal: 4 },
    simReductionPill: {
      marginLeft: 'auto',
      alignItems: 'center',
      backgroundColor: colors.statusResolved + '22',
      borderRadius: 12,
      paddingHorizontal: 14,
      paddingVertical: 8,
      borderWidth: 1,
      borderColor: colors.statusResolved,
    },
    simReductionText: { fontSize: 20, fontWeight: '700', color: colors.statusResolved, lineHeight: 24 },
    simReductionSub: { fontSize: 10, fontWeight: '500', color: colors.statusResolved, opacity: 0.8 },
    alertEnglishText: { fontSize: 15, fontWeight: '400', color: colors.textPrimary, lineHeight: 24 },
    errorText: {
      fontSize: 15,
      fontWeight: '400',
      color: colors.textSecondary,
      textAlign: 'center',
      lineHeight: 22,
    },
    retryButton: {
      marginTop: 8,
      paddingHorizontal: 24,
      paddingVertical: 12,
      borderRadius: 12,
      backgroundColor: colors.accentPrimary,
      minWidth: 120,
      alignItems: 'center',
    },
    retryButtonText: { fontSize: 15, fontWeight: '600', color: colors.textPrimary },
    headerTopRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    typePill: { borderWidth: 1, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
    typePillText: { fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
    headerMetaRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginTop: 2,
    },
    bottomSpacer: { height: 16 },
  }), [colors]);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const data = await fetchCrisisDetail(crisisId);
      if (data === null) {
        setError('Failed to load crisis details. Please try again.');
      } else {
        setDetail(data);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [crisisId]);

  useEffect(() => { void load(); }, [load]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.accentPrimary} />
      </View>
    );
  }

  if (error || !detail) {
    return (
      <View style={styles.centered}>
        <Feather name="alert-circle" size={32} color={colors.statusCritical} />
        <Text style={styles.errorText}>{error ?? 'No data available.'}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => void load()}>
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const { crisis, dispatch_orders, simulation, public_alerts } = detail;
  const severityColor = getSeverityColor(crisis.severity);
  const alert = public_alerts[0] ?? null;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" />

      <TouchableOpacity
        style={styles.backButton}
        onPress={navigation.goBack}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        accessibilityLabel="Go back"
      >
        <Feather name="arrow-left" size={20} color={colors.textPrimary} />
      </TouchableOpacity>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => void load(true)}
            tintColor={colors.accentPrimary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* ─── Section 1: Crisis header ─────────────────────────────────── */}
        <View style={[styles.card, styles.headerCard]}>
          <View style={styles.headerTopRow}>
            <View style={[styles.typePill, { borderColor: severityColor }]}>
              <Text style={[styles.typePillText, { color: severityColor }]}>
                {formatCrisisType(crisis.type)}
              </Text>
            </View>
            <SeverityBadge severity={crisis.severity} size="md" />
          </View>

          <Text style={styles.locationName}>{crisis.location_name}</Text>

          <View style={styles.headerMetaRow}>
            <StatusPill status={crisis.status} colors={colors} />
            <Text style={styles.detectedAtText}>{formatDateTime(crisis.detected_at)}</Text>
          </View>
        </View>

        {/* ─── Section 2: Map preview ───────────────────────────────────── */}
        <View style={[styles.card, styles.mapCard]}>
          <MapView
            style={styles.map}
            initialRegion={{
              latitude: crisis.location.lat,
              longitude: crisis.location.lng,
              latitudeDelta: 0.05,
              longitudeDelta: 0.05,
            }}
            scrollEnabled={false}
            zoomEnabled={false}
            rotateEnabled={false}
            pitchEnabled={false}
            mapType="standard"
          >
            <Circle
              center={{ latitude: crisis.location.lat, longitude: crisis.location.lng }}
              radius={crisis.affected_radius_km * 1000}
              fillColor={severityColor + '33'}
              strokeColor={severityColor + '99'}
              strokeWidth={2}
            />
          </MapView>
        </View>

        {/* ─── Section 3: Dispatch orders ───────────────────────────────── */}
        {dispatch_orders.length > 0 && (
          <View style={styles.card}>
            <SectionLabel label="DISPATCH ORDERS" colors={colors} />
            {dispatch_orders.map((order, idx) => (
              <View
                key={order.id}
                style={[
                  styles.dispatchRow,
                  idx < dispatch_orders.length - 1 && styles.dispatchRowBorder,
                ]}
              >
                <View style={styles.dispatchInfo}>
                  <Text style={styles.dispatchUnit}>{order.unit_name}</Text>
                  <Text style={styles.dispatchDestination}>→ {order.destination_name}</Text>
                </View>
                <View style={styles.dispatchRight}>
                  <DispatchStatusPill status={order.status} colors={colors} />
                  <Text style={styles.etaText}>{order.eta_minutes} min</Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* ─── Section 4: Simulation results ───────────────────────────── */}
        {simulation && (
          <View style={styles.card}>
            <SectionLabel label="SIMULATION RESULTS" colors={colors} />

            <View style={styles.simTicketRow}>
              <Feather name="activity" size={14} color={colors.accentSecondary} />
              <Text style={styles.simTicketId}>Ticket {simulation.emergency_ticket_id}</Text>
            </View>

            <View style={styles.simMetrics}>
              <View style={styles.simMetricItem}>
                <Text style={styles.simMetricValue}>
                  {simulation.traffic_before.congestion_index}
                </Text>
                <Text style={styles.simMetricLabel}>Before</Text>
              </View>

              <View style={styles.simArrow}>
                <Feather name="arrow-right" size={16} color={colors.textMuted} />
              </View>

              <View style={styles.simMetricItem}>
                <Text style={styles.simMetricValue}>
                  {simulation.traffic_after.congestion_index}
                </Text>
                <Text style={styles.simMetricLabel}>After</Text>
              </View>

              <View style={styles.simReductionPill}>
                <Text style={styles.simReductionText}>
                  ↓ {simulation.congestion_reduction_pct}%
                </Text>
                <Text style={styles.simReductionSub}>congestion</Text>
              </View>
            </View>
          </View>
        )}

        {/* ─── Section 5: Public guidance ───────────────────────────────── */}
        {alert && (
          <View style={[styles.card, styles.alertCard]}>
            <SectionLabel label="PUBLIC GUIDANCE" colors={colors} />
            <BilingualText
              english={alert.text_english}
              urdu={alert.text_urdu}
              showUrdu
              englishStyle={styles.alertEnglishText}
            />
          </View>
        )}

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </View>
  );
}
