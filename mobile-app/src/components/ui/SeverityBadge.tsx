import React from 'react';
import { Text, StyleSheet, View } from 'react-native';
import { getSeverityColor, getSeverityBgColor, getSeverityLabel } from '../../theme/colors';
import { FontSizes, FontWeights } from '../../theme/typography';
import { Radii, Space } from '../../theme/spacing';

interface Props {
  severity: 1 | 2 | 3 | 4 | 5;
  size?: 'sm' | 'md';
}

export default function SeverityBadge({ severity, size = 'md' }: Props) {
  const color = getSeverityColor(severity);
  const bg = getSeverityBgColor(severity);
  const label = getSeverityLabel(severity);
  const fontSize = size === 'sm' ? FontSizes.xs : FontSizes.sm;

  return (
    <View style={[styles.badge, { backgroundColor: bg, borderColor: color }]}>
      <Text style={[styles.label, { color, fontSize }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: Space[2],
    paddingVertical: 2,
    borderRadius: Radii.pill,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  label: {
    fontWeight: FontWeights.bold,
    letterSpacing: 0.8,
  },
});
