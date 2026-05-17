import { StyleSheet, TextStyle } from 'react-native';
import { Colors } from './colors';

export const FontFamilies = {
  primary: 'Inter',
  urdu:    'NotoNastaliqUrdu',
  mono:    'JetBrainsMono',
} as const;

export const FontSizes = {
  xs:   11,
  sm:   13,
  base: 15,
  md:   17,
  lg:   20,
  xl:   24,
  '2xl': 32,
  '3xl': 40,
} as const;

export const FontWeights = {
  regular:  '400' as TextStyle['fontWeight'],
  medium:   '500' as TextStyle['fontWeight'],
  semibold: '600' as TextStyle['fontWeight'],
  bold:     '700' as TextStyle['fontWeight'],
};

export const LineHeights = {
  tight:   1.1,
  snug:    1.2,
  normal:  1.4,
  relaxed: 1.5,
  loose:   1.6,
  urdu:    1.8,
};

export const TypeScale: Record<keyof typeof FontSizes, { fontSize: number; lineHeight: number }> = {
  xs:    { fontSize: 11, lineHeight: 15 },
  sm:    { fontSize: 13, lineHeight: 18 },
  base:  { fontSize: 15, lineHeight: 23 },
  md:    { fontSize: 17, lineHeight: 24 },
  lg:    { fontSize: 20, lineHeight: 26 },
  xl:    { fontSize: 24, lineHeight: 29 },
  '2xl': { fontSize: 32, lineHeight: 35 },
  '3xl': { fontSize: 40, lineHeight: 40 },
};

export const urduStyle = StyleSheet.create({
  base: {
    writingDirection: 'rtl',
    textAlign: 'right',
    lineHeight: FontSizes.base * LineHeights.urdu,
    color: Colors.textPrimary,
  },
  secondary: {
    writingDirection: 'rtl',
    textAlign: 'right',
    lineHeight: FontSizes.base * LineHeights.urdu,
    color: Colors.textSecondary,
  },
  muted: {
    writingDirection: 'rtl',
    textAlign: 'right',
    lineHeight: FontSizes.base * LineHeights.urdu,
    color: Colors.textMuted,
  },
});
