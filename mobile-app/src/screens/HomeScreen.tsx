import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import MapView, { Marker, Circle } from "react-native-maps";
import { useFocusEffect } from "@react-navigation/native";
import { fetchActiveCrises, fetchCrisisDetail } from "../lib/api";
import { CrisisAlert, DashboardState } from "../types";

const DARK_MAP_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
];

const ISLAMABAD_REGION = {
  latitude: 33.6844,
  longitude: 73.0479,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};

export default function HomeScreen({ navigation }: any) {
  const [crises, setCrises] = useState<CrisisAlert[]>([]);
  const [selectedCrisis, setSelectedCrisis] = useState<DashboardState | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadCrises = async () => {
    setLoading(true);
    const data = await fetchActiveCrises();
    setCrises(data);
    if (data.length > 0) {
      const full = await fetchCrisisDetail(data[0].crisis_id);
      setSelectedCrisis(full);
    }
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
    if (severity >= 4) return "#DC2626"; // critical
    if (severity >= 3) return "#EA580C"; // high
    if (severity >= 2) return "#D97706"; // warning
    return "#16A34A"; // safe
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>CIRO Crisis Map</Text>
        <Text style={styles.headerSubtitle}>Islamabad Real-Time Alerts</Text>
      </View>

      {selectedCrisis && (
        <MapView
          style={styles.map}
          initialRegion={ISLAMABAD_REGION}
          customMapStyle={DARK_MAP_STYLE}
        >
          <Circle
            center={{
              latitude: selectedCrisis.crisis.location.latitude,
              longitude: selectedCrisis.crisis.location.longitude,
            }}
            radius={(selectedCrisis.crisis.location.affected_radius_km || 2) * 1000}
            fillColor="rgba(220, 38, 38, 0.2)"
            strokeColor="#DC2626"
            strokeWidth={2}
          />
          <Marker
            coordinate={{
              latitude: selectedCrisis.crisis.location.latitude,
              longitude: selectedCrisis.crisis.location.longitude,
            }}
            title={selectedCrisis.crisis.type}
            description={`Severity: ${selectedCrisis.crisis.severity}/5`}
          />
        </MapView>
      )}

      {!selectedCrisis && (
        <View style={styles.noMapPlaceholder}>
          <Text style={styles.noMapText}>No active crises</Text>
        </View>
      )}

      <View style={styles.crisisListContainer}>
        <Text style={styles.listTitle}>Active Crises</Text>
        {loading && !refreshing ? (
          <ActivityIndicator size="large" color="#2563EB" style={styles.loader} />
        ) : crises.length === 0 ? (
          <Text style={styles.emptyText}>No active crises at this time</Text>
        ) : (
          <FlatList
            data={crises}
            keyExtractor={(item) => item.crisis_id}
            scrollEnabled={true}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={[
                  styles.crisisCard,
                  selectedCrisis?.crisis_id === item.crisis_id && styles.crisisCardActive,
                ]}
                onPress={async () => {
                  const full = await fetchCrisisDetail(item.crisis_id);
                  setSelectedCrisis(full);
                }}
              >
                <View
                  style={[
                    styles.severityBadge,
                    { backgroundColor: getSeverityColor(item.severity) },
                  ]}
                >
                  <Text style={styles.severityText}>{item.severity}/5</Text>
                </View>
                <View style={styles.crisisInfo}>
                  <Text style={styles.crisisType}>{item.type}</Text>
                  <Text style={styles.crisisLocation}>{item.location.primary}</Text>
                  <Text style={styles.crisisTime}>
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </Text>
                </View>
              </TouchableOpacity>
            )}
          />
        )}
      </View>
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
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "700",
    color: "#F8FAFC",
  },
  headerSubtitle: {
    fontSize: 12,
    color: "#94A3B8",
    marginTop: 4,
  },
  map: {
    flex: 1,
    minHeight: 250,
  },
  noMapPlaceholder: {
    height: 250,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#1E293B",
  },
  noMapText: {
    color: "#94A3B8",
    fontSize: 16,
  },
  crisisListContainer: {
    maxHeight: 240,
    backgroundColor: "#1E293B",
    borderTopWidth: 1,
    borderTopColor: "#334155",
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  listTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#F8FAFC",
    marginBottom: 8,
  },
  loader: {
    marginVertical: 16,
  },
  emptyText: {
    textAlign: "center",
    color: "#94A3B8",
    marginVertical: 16,
  },
  crisisCard: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 8,
    marginBottom: 8,
    backgroundColor: "#0F172A",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  crisisCardActive: {
    borderColor: "#2563EB",
    backgroundColor: "rgba(37, 99, 235, 0.1)",
  },
  severityBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  severityText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#FFF",
  },
  crisisInfo: {
    flex: 1,
  },
  crisisType: {
    fontSize: 14,
    fontWeight: "600",
    color: "#F8FAFC",
  },
  crisisLocation: {
    fontSize: 12,
    color: "#94A3B8",
    marginTop: 2,
  },
  crisisTime: {
    fontSize: 10,
    color: "#64748B",
    marginTop: 2,
  },
});
