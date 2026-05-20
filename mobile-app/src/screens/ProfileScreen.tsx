import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Switch,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import type { UserPreferences } from '../types';
import { Themes, THEME_LABELS, type ThemeKey } from '../theme/colors';
import { useTheme } from '../theme/ThemeContext';
import { FontSizes, FontWeights } from '../theme/typography';
import { Space, Radii } from '../theme/spacing';

const DEFAULT_PREFS: UserPreferences = {
  alert_radius_km: 10,
  notification_sound: 'sound',
  language: 'both',
  voice_language: 'urdu',
  auto_play_voice: true,
  pre_download_alerts: true,
};

const RADIUS_OPTIONS: UserPreferences['alert_radius_km'][] = [2, 5, 10, 100];
const RADIUS_LABELS: Record<number, string> = { 2: '2 km', 5: '5 km', 10: '10 km', 100: 'City-wide' };

export default function ProfileScreen() {
  const { colors, themeKey: activeTheme, setTheme } = useTheme();
  const [prefs, setPrefs] = useState<UserPreferences>(DEFAULT_PREFS);

  function setPref<K extends keyof UserPreferences>(key: K, value: UserPreferences[K]) {
    setPrefs((p) => ({ ...p, [key]: value }));
  }

  const styles = useMemo(() => StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bgPrimary },
    content: { paddingHorizontal: Space[4], paddingVertical: Space[5] },
    pageTitle: {
      fontSize: FontSizes.xl,
      fontWeight: FontWeights.bold,
      color: colors.textPrimary,
      marginBottom: Space[6],
    },
    section: { marginBottom: Space[6] },
    sectionTitle: {
      fontSize: FontSizes.xs,
      fontWeight: FontWeights.bold,
      color: colors.textMuted,
      letterSpacing: 1,
      marginBottom: Space[3],
    },
    segmented: {
      flexDirection: 'row',
      backgroundColor: colors.bgSurface,
      borderRadius: Radii.md,
      borderWidth: 1,
      borderColor: colors.border,
      overflow: 'hidden',
    },
    segment: {
      flex: 1,
      paddingVertical: Space[2],
      alignItems: 'center',
      borderRightWidth: 1,
      borderRightColor: colors.border,
    },
    segmentActive: { backgroundColor: colors.accentPrimary + '33' },
    segmentText: { fontSize: FontSizes.sm, color: colors.textSecondary },
    segmentTextActive: { color: colors.accentPrimary, fontWeight: FontWeights.semibold },
    row: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: Space[3],
      paddingHorizontal: Space[3],
      backgroundColor: colors.bgSurface,
      borderRadius: Radii.md,
      marginBottom: Space[2],
      borderWidth: 1,
      borderColor: colors.border,
    },
    rowInfo: { flex: 1, marginRight: Space[3] },
    rowLabel: { fontSize: FontSizes.base, fontWeight: FontWeights.medium, color: colors.textPrimary },
    rowDesc: { fontSize: FontSizes.xs, color: colors.textMuted, marginTop: 2 },
    themeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Space[3] },
    themeCard: {
      width: '47%',
      backgroundColor: colors.bgSurface,
      borderRadius: Radii.md,
      borderWidth: 1,
      borderColor: colors.border,
      padding: Space[3],
      gap: Space[2],
    },
    themeCardActive: { borderColor: colors.accentPrimary, borderWidth: 2 },
    themeCardLabel: {
      fontSize: FontSizes.sm,
      fontWeight: FontWeights.medium,
      color: colors.textSecondary,
    },
    themeCardLabelActive: { color: colors.textPrimary, fontWeight: FontWeights.semibold },
    themeDotsRow: { flexDirection: 'row', gap: Space[1], marginTop: Space[1] },
    themeDot: { width: 12, height: 12, borderRadius: 6, borderWidth: 1, borderColor: colors.border },
    footer: {
      fontSize: FontSizes.xs,
      color: colors.textMuted,
      textAlign: 'center',
      marginTop: Space[4],
    },
  }), [colors]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.pageTitle}>Preferences</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ALERT RADIUS</Text>
        <View style={styles.segmented}>
          {RADIUS_OPTIONS.map((r) => (
            <View
              key={r}
              style={[styles.segment, prefs.alert_radius_km === r && styles.segmentActive]}
            >
              <Text
                style={[styles.segmentText, prefs.alert_radius_km === r && styles.segmentTextActive]}
                onPress={() => setPref('alert_radius_km', r)}
              >
                {RADIUS_LABELS[r]}
              </Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>VOICE ALERTS</Text>
        <View style={styles.row}>
          <View style={styles.rowInfo}>
            <Text style={styles.rowLabel}>Auto-play in affected area</Text>
            <Text style={styles.rowDesc}>Plays when you enter crisis zone (severity 4+)</Text>
          </View>
          <Switch
            value={prefs.auto_play_voice}
            onValueChange={(v) => setPref('auto_play_voice', v)}
            trackColor={{ false: colors.border, true: colors.accentPrimary }}
            thumbColor="#fff"
          />
        </View>
        <View style={styles.row}>
          <View style={styles.rowInfo}>
            <Text style={styles.rowLabel}>Pre-download for offline</Text>
            <Text style={styles.rowDesc}>Cache alerts for use without internet</Text>
          </View>
          <Switch
            value={prefs.pre_download_alerts}
            onValueChange={(v) => setPref('pre_download_alerts', v)}
            trackColor={{ false: colors.border, true: colors.accentPrimary }}
            thumbColor="#fff"
          />
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>THEME</Text>
        <View style={styles.themeGrid}>
          {(Object.keys(Themes) as ThemeKey[]).map((key) => {
            const palette = Themes[key];
            const isActive = activeTheme === key;
            return (
              <TouchableOpacity
                key={key}
                style={[
                  styles.themeCard,
                  isActive && styles.themeCardActive,
                  isActive && { backgroundColor: palette.accentPrimary + '22' },
                ]}
                onPress={() => setTheme(key)}
                activeOpacity={0.75}
              >
                <Text style={[styles.themeCardLabel, isActive && styles.themeCardLabelActive]}>
                  {THEME_LABELS[key]}
                </Text>
                <View style={styles.themeDotsRow}>
                  {([palette.bgPrimary, palette.accentPrimary, palette.accentSecondary] as string[]).map(
                    (dotColor, i) => (
                      <View key={i} style={[styles.themeDot, { backgroundColor: dotColor }]} />
                    ),
                  )}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <Text style={styles.footer}>CIRO v2 · Crisis Intelligence &amp; Response Operations</Text>
    </ScrollView>
  );
}
