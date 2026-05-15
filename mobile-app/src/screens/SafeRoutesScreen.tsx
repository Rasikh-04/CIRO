import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { fetchActiveCrises, fetchSafeRoutes, logUserIntent } from "../lib/api";
import { SafeRoute } from "../types";

export default function SafeRoutesScreen() {
  const [routes, setRoutes] = useState<SafeRoute[]>([]);
  const [selectedCrisisId, setSelectedCrisisId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadRoutes = async () => {
    setLoading(true);
    const crises = await fetchActiveCrises();
    if (crises.length > 0) {
      setSelectedCrisisId(crises[0].crisis_id);
      const data = await fetchSafeRoutes(crises[0].crisis_id);
      setRoutes(data);
    }
    setLoading(false);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRoutes();
    setRefreshing(false);
  };

  useFocusEffect(
    React.useCallback(() => {
      loadRoutes();
    }, [])
  );

  const getRiskColor = (riskLevel: string) => {
    if (riskLevel === "high") return "#DC2626";
    if (riskLevel === "medium") return "#D97706";
    return "#16A34A";
  };

  const handleTakeRoute = async (route: SafeRoute) => {
    if (selectedCrisisId) {
      await logUserIntent(selectedCrisisId, "route_taken", {
        route_id: route.route_id,
        route_name: route.name,
      });
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Safe Routes</Text>
        <Text style={styles.headerSubtitle}>
          {routes.length > 0
            ? `${routes.length} alternate route${routes.length !== 1 ? "s" : ""} available`
            : "No routes available"}
        </Text>
      </View>

      {loading && !refreshing ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#2563EB" />
        </View>
      ) : routes.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Active Routes</Text>
          <Text style={styles.emptySubtitle}>
            Check back when there are active crises in your area.
          </Text>
        </View>
      ) : (
        <FlatList
          data={routes}
          keyExtractor={(item) => item.route_id}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          renderItem={({ item }) => (
            <View style={styles.routeCard}>
              <View style={styles.routeHeader}>
                <Text style={styles.routeName}>{item.name}</Text>
                <View
                  style={[
                    styles.riskBadge,
                    { backgroundColor: getRiskColor(item.risk_level) },
                  ]}
                >
                  <Text style={styles.riskLabel}>{item.risk_level.toUpperCase()}</Text>
                </View>
              </View>

              <View style={styles.routeStats}>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Distance</Text>
                  <Text style={styles.statValue}>{item.distance_km.toFixed(1)} km</Text>
                </View>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>ETA</Text>
                  <Text style={styles.statValue}>{item.eta_minutes} min</Text>
                </View>
                <View style={styles.stat}>
                  <Text style={styles.statLabel}>Waypoints</Text>
                  <Text style={styles.statValue}>{item.waypoints.length}</Text>
                </View>
              </View>

              <TouchableOpacity
                style={styles.takeButton}
                onPress={() => handleTakeRoute(item)}
              >
                <Text style={styles.takeButtonText}>Use This Route</Text>
              </TouchableOpacity>
            </View>
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
  routeCard: {
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: 12,
  },
  routeHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  routeName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#F8FAFC",
    flex: 1,
  },
  riskBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
  },
  riskLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: "#FFF",
  },
  routeStats: {
    flexDirection: "row",
    justifyContent: "space-around",
    paddingVertical: 12,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: "#334155",
    marginBottom: 12,
  },
  stat: {
    alignItems: "center",
  },
  statLabel: {
    fontSize: 12,
    color: "#94A3B8",
    marginBottom: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: "600",
    color: "#F8FAFC",
  },
  takeButton: {
    backgroundColor: "#16A34A",
    paddingVertical: 11,
    borderRadius: 8,
    alignItems: "center",
  },
  takeButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FFF",
  },
});
