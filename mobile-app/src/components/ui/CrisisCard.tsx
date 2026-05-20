import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import type { CrisisEvent } from '../../types';
import { useTheme } from '../../theme/ThemeContext';
import { getSeverityColorFromPalette } from '../../theme/colors';
import SeverityBadge from './SeverityBadge';

function formatCrisisType(type: string): string {
  return type.replace(/_/g, ' ').toUpperCase();
}

function formatDetectedAt(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return new Date(iso).toLocaleDateString('en-PK', { day: 'numeric', month: 'short' });
}

interface CrisisCardProps {
  crisis: CrisisEvent;
  onPress: () => void;
  style?: ViewStyle;
}

export default function CrisisCard({ crisis, onPress, style }: CrisisCardProps) {
  const { colors } = useTheme();
  const severityColor = getSeverityColorFromPalette(crisis.severity, colors);

  return (
    <TouchableOpacity
      activeOpacity={0.72}
      onPress={onPress}
      style={[
        styles.card,
        {
          backgroundColor: colors.bgSurface,
          borderColor: colors.border,
          borderLeftColor: severityColor,
        },
        style,
      ]}
    >
      <View style={styles.topRow}>
        <Text style={[styles.crisisType, { color: colors.textPrimary }]} numberOfLines={1}>
          {formatCrisisType(crisis.type)}
        </Text>
        <SeverityBadge severity={crisis.severity} size="sm" />
      </View>

      <Text style={[styles.locationName, { color: colors.textPrimary }]} numberOfLines={1}>
        {crisis.location_name}
      </Text>

      <Text style={[styles.detectedAt, { color: colors.textSecondary }]} numberOfLines={1}>
        {formatDetectedAt(crisis.detected_at)}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 80,
    borderWidth: 1,
    borderLeftWidth: 4,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    justifyContent: 'center',
    gap: 3,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  crisisType: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.4,
    flexShrink: 1,
    marginRight: 8,
  },
  locationName: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 20,
  },
  detectedAt: {
    fontSize: 11,
    fontWeight: '400',
    lineHeight: 16,
    marginTop: 1,
  },
});
