import React, { useEffect, useState } from "react";
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

export default function AlertsScreen() {
  const [crises, setCrises] = useState<CrisisAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadCrises = async () => {
    setLoading(true);
    const data = await fetchActiveCrises();
    setCrises(data.sort((a, b) => b.severity - a.severity));
    setLoading(false);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadCrises();
    setRefreshing(false);
  };

  useFocusEffect(
    React.useCallback(() => {
      loadCrises();
    }, [])
  );

  const getSeverityColor = (severity: number) => {
    if (severity >= 4) return "#DC2626";
    if (severity >= 3) return "#EA580C";
    if (severity >= 2) return "#D97706";
    return "#16A34A";
  };

  const getSeverityLabel = (severity: number) => {
    if (severity >= 4) return "CRITICAL";
    if (severity >= 3) return "HIGH";
    if (severity >= 2) return "MEDIUM";
    return "LOW";
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Crisis Alerts</Text>
        <Text style={styles.headerSubtitle}>
          {crises.length} active crisis{crises.length !== 1 ? "es" : ""}
        </Text>
      </View>

      {loading && !refreshing ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#2563EB" />
        </View>
      ) : crises.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Active Crises</Text>
          <Text style={styles.emptySubtitle}>
            Everything is safe. Check back for updates.
          </Text>
        </View>
      ) : (
        <FlatList
          data={crises}
          keyExtractor={(item) => item.crisis_id}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          renderItem={({ item }) => (
            <View
              style={[
                styles.alertCard,
                { borderLeftColor: getSeverityColor(item.severity) },
              ]}
            >
              <View style={styles.alertHeader}>
                <View style={styles.titleContainer}>
                  <Text style={styles.alertType}>{item.type}</Text>
                  <View
                    style={[
                      styles.severityBadge,
                      { backgroundColor: getSeverityColor(item.severity) },
                    ]}
                  >
                    <Text style={styles.severityLabel}>
                      {getSeverityLabel(item.severity)}
                    </Text>
                  </View>
                </View>
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
