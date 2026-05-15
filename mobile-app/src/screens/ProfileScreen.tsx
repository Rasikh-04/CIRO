import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Switch,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { UserProfile } from "../types";

export default function ProfileScreen() {
  const [profile, setProfile] = useState<UserProfile>({
    user_id: "user_001",
    name: "You",
    alert_preferences: {
      severity_threshold: 2,
      push_enabled: true,
      sms_enabled: false,
    },
  });

  const togglePushNotifications = () => {
    setProfile((prev) => ({
      ...prev,
      alert_preferences: {
        ...prev.alert_preferences,
        push_enabled: !prev.alert_preferences.push_enabled,
      },
    }));
  };

  const toggleSmsNotifications = () => {
    setProfile((prev) => ({
      ...prev,
      alert_preferences: {
        ...prev.alert_preferences,
        sms_enabled: !prev.alert_preferences.sms_enabled,
      },
    }));
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <Ionicons name="person-circle" size={80} color="#2563EB" />
        </View>
        <Text style={styles.userName}>{profile.name}</Text>
        <Text style={styles.userId}>ID: {profile.user_id}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Alert Preferences</Text>

        <View style={styles.preferenceItem}>
          <View>
            <Text style={styles.preferenceName}>Push Notifications</Text>
            <Text style={styles.preferenceDesc}>Get instant crisis alerts</Text>
          </View>
          <Switch
            value={profile.alert_preferences.push_enabled}
            onValueChange={togglePushNotifications}
            trackColor={{ false: "#334155", true: "#2563EB" }}
            thumbColor={profile.alert_preferences.push_enabled ? "#2563EB" : "#94A3B8"}
          />
        </View>

        <View style={styles.preferenceItem}>
          <View>
            <Text style={styles.preferenceName}>SMS Notifications</Text>
            <Text style={styles.preferenceDesc}>Receive alerts via SMS</Text>
          </View>
          <Switch
            value={profile.alert_preferences.sms_enabled}
            onValueChange={toggleSmsNotifications}
            trackColor={{ false: "#334155", true: "#2563EB" }}
            thumbColor={profile.alert_preferences.sms_enabled ? "#2563EB" : "#94A3B8"}
          />
        </View>

        <View style={styles.preferenceItem}>
          <View>
            <Text style={styles.preferenceName}>Alert Severity Threshold</Text>
            <Text style={styles.preferenceDesc}>
              Show alerts severity {profile.alert_preferences.severity_threshold}/5 and above
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About CIRO</Text>
        <TouchableOpacity style={styles.linkItem}>
          <Text style={styles.linkText}>Privacy Policy</Text>
          <Ionicons name="chevron-forward" size={20} color="#2563EB" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.linkItem}>
          <Text style={styles.linkText}>Terms of Service</Text>
          <Ionicons name="chevron-forward" size={20} color="#2563EB" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.linkItem}>
          <Text style={styles.linkText}>App Version</Text>
          <Text style={styles.versionText}>1.0.0</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.logoutButton}>
        <Text style={styles.logoutButtonText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  content: {
    paddingHorizontal: 16,
    paddingVertical: 20,
  },
  header: {
    alignItems: "center",
    marginBottom: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  avatarContainer: {
    marginBottom: 16,
  },
  userName: {
    fontSize: 24,
    fontWeight: "700",
    color: "#F8FAFC",
    marginBottom: 4,
  },
  userId: {
    fontSize: 12,
    color: "#94A3B8",
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#F8FAFC",
    marginBottom: 12,
  },
  preferenceItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: "#1E293B",
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  preferenceName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#F8FAFC",
    marginBottom: 4,
  },
  preferenceDesc: {
    fontSize: 12,
    color: "#94A3B8",
  },
  linkItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: "#1E293B",
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  linkText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#F8FAFC",
  },
  versionText: {
    fontSize: 14,
    color: "#94A3B8",
  },
  logoutButton: {
    backgroundColor: "#DC2626",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 16,
  },
  logoutButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FFF",
  },
});
