import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Linking,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { fetchActiveCrises, fetchSafeRoutes } from '../lib/api';
import type { SafeRoute } from '../types';
import { FontSizes, FontWeights } from '../theme/typography';
import { Space, Radii } from '../theme/spacing';
import { useTheme } from '../theme/ThemeContext';

export default function SafeRoutesScreen() {
  const { colors } = useTheme();

  const riskColors: Record<string, string> = {
    clear:   colors.statusLow,
    monitor: colors.statusMedium,
    avoid:   colors.statusCritical,
  };

  const [routes, setRoutes] = useState<SafeRoute[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadRoutes = useCallback(async () => {
    setLoading(true);
    const crises = await fetchActiveCrises();
    if (crises.length > 0) {
      const data = await fetchSafeRoutes(crises[0].id);
      setRoutes(data);
    }
    setLoading(false);
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadRoutes();
    setRefreshing(false);
  }, [loadRoutes]);

  useFocusEffect(useCallback(() => { loadRoutes(); }, [loadRoutes]));

  return (
    <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <Text style={[styles.headerTitle, { color: colors.textPrimary }]}>Safe Routes</Text>
        <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
          {routes.length > 0 ? `${routes.length} alternate routes available` : 'No routes available'}
        </Text>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.accentPrimary} />
        </View>
      ) : routes.length === 0 ? (
        <View style={styles.centered}>
          <Text style={[styles.emptyTitle, { color: colors.textPrimary }]}>No Active Routes</Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            Check back when there are active crises nearby.
          </Text>
        </View>
      ) : (
        <FlatList
          data={routes}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.accentPrimary} />
          }
          renderItem={({ item }) => {
            const riskColor = riskColors[item.risk_level];
            return (
              <View style={[styles.routeCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
                <View style={styles.routeHeader}>
                  <Text style={[styles.routeName, { color: colors.textPrimary }]}>{item.name}</Text>
                  <View style={[styles.riskBadge, { backgroundColor: riskColor + '33', borderColor: riskColor }]}>
                    <Text style={[styles.riskLabel, { color: riskColor }]}>
                      {item.risk_level.toUpperCase()}
                    </Text>
                  </View>
                </View>

                {item.via ? (
                  <Text style={[styles.via, { color: colors.textSecondary }]}>via {item.via}</Text>
                ) : null}

                <View style={[styles.stats, { borderColor: colors.border }]}>
                  <View style={styles.stat}>
                    <Text style={[styles.statLabel, { color: colors.textMuted }]}>Distance</Text>
                    <Text style={[styles.statValue, { color: colors.textPrimary }]}>
                      {item.distance_km.toFixed(1)} km
                    </Text>
                  </View>
                  <View style={styles.stat}>
                    <Text style={[styles.statLabel, { color: colors.textMuted }]}>ETA</Text>
                    <Text style={[styles.statValue, { color: colors.textPrimary }]}>
                      {item.eta_minutes} min
                    </Text>
                  </View>
                  {item.extra_minutes > 0 && (
                    <View style={styles.stat}>
                      <Text style={[styles.statLabel, { color: colors.textMuted }]}>Extra</Text>
                      <Text style={[styles.statValue, { color: colors.statusMedium }]}>
                        +{item.extra_minutes} min
                      </Text>
                    </View>
                  )}
                </View>

                {item.maps_deep_link ? (
                  <TouchableOpacity
                    style={styles.mapsButton}
                    onPress={() => item.maps_deep_link && Linking.openURL(item.maps_deep_link)}
                  >
                    <Text style={[styles.mapsButtonText, { color: colors.accentSecondary }]}>
                      Open in Google Maps →
                    </Text>
                  </TouchableOpacity>
                ) : null}
              </View>
            );
          }}
        />
      )}
    </View>
  );
}

// Layout, spacing, and typography only — no color values.
const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    paddingHorizontal: Space[4],
    paddingTop: Space[4],
    paddingBottom: Space[4],
    borderBottomWidth: 1,
  },
  headerTitle: { fontSize: FontSizes.xl, fontWeight: FontWeights.bold },
  headerSubtitle: { fontSize: FontSizes.sm, marginTop: Space[1] },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyTitle: { fontSize: FontSizes.lg, fontWeight: FontWeights.semibold, marginBottom: Space[2] },
  emptySubtitle: { fontSize: FontSizes.sm, textAlign: 'center' },
  listContent: { paddingHorizontal: Space[3], paddingVertical: Space[3] },
  routeCard: {
    borderRadius: Radii.md,
    borderWidth: 1,
    paddingHorizontal: Space[4],
    paddingVertical: Space[3],
    marginBottom: Space[3],
  },
  routeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Space[1],
  },
  routeName: { fontSize: FontSizes.md, fontWeight: FontWeights.bold, flex: 1 },
  riskBadge: {
    paddingHorizontal: Space[2],
    paddingVertical: 2,
    borderRadius: Radii.pill,
    borderWidth: 1,
  },
  riskLabel: { fontSize: FontSizes.xs, fontWeight: FontWeights.bold, letterSpacing: 0.5 },
  via: { fontSize: FontSizes.sm, marginBottom: Space[2] },
  stats: {
    flexDirection: 'row',
    gap: Space[6],
    paddingVertical: Space[3],
    borderTopWidth: 1,
    borderBottomWidth: 1,
    marginBottom: Space[3],
  },
  stat: { alignItems: 'center' },
  statLabel: { fontSize: FontSizes.xs, marginBottom: 2 },
  statValue: { fontSize: FontSizes.md, fontWeight: FontWeights.semibold },
  mapsButton: { alignSelf: 'flex-start' },
  mapsButtonText: { fontSize: FontSizes.sm, fontWeight: FontWeights.medium },
});
