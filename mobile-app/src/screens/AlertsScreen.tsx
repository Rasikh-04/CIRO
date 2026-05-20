import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { fetchActiveCrises, fetchSafeRoutes } from "../lib/api";
import { CrisisAlert, SafeRoute } from "../types";

export default function AlertsScreen({ navigation }: { navigation: any }) {
  const { colors } = useTheme();
  const [crises, setCrises] = useState<CrisisEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const styles = useMemo(() => StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bgPrimary },
    header: {
      paddingHorizontal: Space[4],
      paddingTop: Space[4],
      paddingBottom: Space[4],
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: FontSizes.xl,
      fontWeight: FontWeights.bold,
      color: colors.textPrimary,
    },
    headerSubtitle: {
      fontSize: FontSizes.sm,
      color: colors.textSecondary,
      marginTop: Space[1],
    },
    centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    emptyTitle: {
      fontSize: FontSizes.lg,
      fontWeight: FontWeights.semibold,
      color: colors.textPrimary,
      marginBottom: Space[2],
    },
    emptySubtitle: { fontSize: FontSizes.sm, color: colors.textSecondary, textAlign: 'center' },
    listContent: { paddingHorizontal: Space[3], paddingVertical: Space[3] },
    alertCard: {
      backgroundColor: colors.bgSurface,
      borderRadius: Radii.md,
      borderLeftWidth: 4,
      paddingHorizontal: Space[4],
      paddingVertical: Space[3],
      marginBottom: Space[3],
    },
    alertHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: Space[1],
    },
    alertType: {
      fontSize: FontSizes.md,
      fontWeight: FontWeights.bold,
      color: colors.textPrimary,
      flex: 1,
      marginRight: Space[2],
    },
    alertDesc: {
      fontSize: FontSizes.sm,
      color: colors.textSecondary,
      marginBottom: 2,
      textTransform: 'capitalize',
    },
    alertTime: { fontSize: FontSizes.xs, color: colors.textMuted, marginBottom: Space[3] },
    routeButton: { alignSelf: 'flex-start', paddingVertical: Space[1] },
    routeButtonText: {
      fontSize: FontSizes.sm,
      color: colors.accentSecondary,
      fontWeight: FontWeights.medium,
    },
  }), [colors]);

  const loadCrises = useCallback(async () => {
    setLoading(true);
    const data = await fetchActiveCrises();
    setCrises(data.sort((a, b) => b.severity - a.severity));
    setLoading(false);
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadCrises();
    setRefreshing(false);
  }, [loadCrises]);

  useFocusEffect(useCallback(() => { loadCrises(); }, [loadCrises]));

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Alerts</Text>
        <Text style={styles.headerSubtitle}>
          {crises.length > 0 ? `${crises.length} active` : 'No active alerts'} · Islamabad
        </Text>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.accentPrimary} />
        </View>
      ) : crises.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyTitle}>No Active Crises</Text>
          <Text style={styles.emptySubtitle}>All clear. Check back for updates.</Text>
        </View>
      ) : (
        <FlatList
          data={crises}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.accentPrimary}
            />
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.alertCard, { borderLeftColor: getSeverityColor(item.severity) }]}
              onPress={() => navigation.navigate('CrisisDetail', { crisisId: item.id })}
            >
              <View style={styles.alertHeader}>
                <Text style={styles.alertType} numberOfLines={1}>{item.location_name}</Text>
                <SeverityBadge severity={item.severity} size="sm" />
              </View>

              <View style={styles.alertDetails}>
                <Text style={styles.location}>
                  📍 {item.location_name}
                </Text>
                <Text style={styles.timestamp}>
                  ⏰ {new Date(item.detected_at).toLocaleString()}
                </Text>
              </View>

              <TouchableOpacity
                style={styles.actionButton}
                onPress={async () => {
                  const routes = await fetchSafeRoutes(item.crisis_id);
                  if (routes.length === 0) {
                    Alert.alert("No Routes", "No safe routes available for this crisis.");
                  } else {
                    Alert.alert(
                      "Safe Routes",
                      routes.map((r) => `${r.name} — ${r.distance_km}km (~${r.eta_minutes}min)`).join("\n")
                    );
                  }
                }}
              >
                <Text style={styles.actionButtonText}>Get Safe Routes</Text>
              </TouchableOpacity>
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: "700",
    color: "#F8FAFC",
  },
  headerSubtitle: {
    fontSize: 14,
    color: "#94A3B8",
    marginTop: 4,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: "600",
    color: "#F8FAFC",
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: "#94A3B8",
    textAlign: "center",
  },
  listContent: {
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  alertCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderLeftWidth: 4,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: 12,
  },
  alertHeader: {
    marginBottom: 12,
  },
  titleContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  alertType: {
    fontSize: 18,
    fontWeight: "700",
    color: "#F8FAFC",
    flex: 1,
  },
  severityBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginLeft: 8,
  },
  severityLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#FFF",
  },
  alertDetails: {
    marginBottom: 12,
    gap: 6,
  },
  location: {
    fontSize: 13,
    color: "#CBD5E1",
  },
  timestamp: {
    fontSize: 12,
    color: "#94A3B8",
  },
  actionButton: {
    backgroundColor: "#2563EB",
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FFF",
  },
});
