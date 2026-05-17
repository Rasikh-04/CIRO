export interface ColorPalette {
  bgPrimary:       string;
  bgSurface:       string;
  bgElevated:      string;
  accentPrimary:   string;
  accentSecondary: string;
  statusCritical:  string;
  statusHigh:      string;
  statusMedium:    string;
  statusLow:       string;
  statusResolved:  string;
  textPrimary:     string;
  textSecondary:   string;
  textMuted:       string;
  border:          string;
  borderStrong:    string;
}

export type ThemeKey = 'navalCommand' | 'arcticOps' | 'deepNavy' | 'nightOps';

// ─── A: Naval Command ─────────────────────────────────────────────────────────
// Source of truth — matches web dashboard CSS variables exactly.

const navalCommand: ColorPalette = {
  bgPrimary:       '#0A1628',
  bgSurface:       '#132743',
  bgElevated:      '#1B3558',
  accentPrimary:   '#FF6B35',
  accentSecondary: '#3D9EFF',
  statusCritical:  '#FF3B3B',
  statusHigh:      '#FF6B35',
  statusMedium:    '#FFB830',
  statusLow:       '#3ECF8E',
  statusResolved:  '#2ECC71',
  textPrimary:     '#F0F4F8',
  textSecondary:   '#8BA0B5',
  textMuted:       '#4A6580',
  border:          '#1E3A56',
  borderStrong:    '#2D5072',
};

// ─── B: Arctic Ops ────────────────────────────────────────────────────────────
// Spec defines 10 keys; remaining 5 derived from palette's bg range.

const arcticOps: ColorPalette = {
  bgPrimary:       '#0D1B2A',
  bgSurface:       '#162032',
  bgElevated:      '#1E2D3F',
  accentPrimary:   '#00B4D8',
  accentSecondary: '#0077B6',
  statusCritical:  '#EF233C',
  statusHigh:      '#F77F00',
  statusMedium:    '#FCBF49',
  statusLow:       '#EAE2B7',
  statusResolved:  '#06D6A0',
  textPrimary:     '#EDF2F4',
  textSecondary:   '#8D99AE',
  textMuted:       '#4A5568',
  border:          '#1A2C3E',
  borderStrong:    '#2A4257',
};

// ─── C: Deep Navy Professional ────────────────────────────────────────────────
// Spec defines 7 keys; remaining 8 derived for formal/government aesthetic.

const deepNavy: ColorPalette = {
  bgPrimary:       '#06111F',
  bgSurface:       '#0F2137',
  bgElevated:      '#172E4A',
  accentPrimary:   '#2B7FFF',
  accentSecondary: '#1BCDFE',
  statusCritical:  '#FF4444',
  statusHigh:      '#FF8800',
  statusMedium:    '#FFD700',
  statusLow:       '#36B37E',
  statusResolved:  '#2D9E6B',
  textPrimary:     '#E8EEF5',
  textSecondary:   '#7A94B0',
  textMuted:       '#3D5670',
  border:          '#142840',
  borderStrong:    '#1F3D5C',
};

// ─── D: Night Ops (High Contrast) ────────────────────────────────────────────
// Spec defines 5 keys; remaining 10 derived for maximum field legibility.

const nightOps: ColorPalette = {
  bgPrimary:       '#000000',
  bgSurface:       '#111827',
  bgElevated:      '#1F2937',
  accentPrimary:   '#F59E0B',
  accentSecondary: '#3B82F6',
  statusCritical:  '#FF0000',
  statusHigh:      '#FF6600',
  statusMedium:    '#FACC15',
  statusLow:       '#4ADE80',
  statusResolved:  '#22C55E',
  textPrimary:     '#FFFFFF',
  textSecondary:   '#9CA3AF',
  textMuted:       '#4B5563',
  border:          '#1F2937',
  borderStrong:    '#374151',
};

// ─── Registry ─────────────────────────────────────────────────────────────────

export const Themes: Record<ThemeKey, ColorPalette> = {
  navalCommand,
  arcticOps,
  deepNavy,
  nightOps,
};

export const THEME_LABELS: Record<ThemeKey, string> = {
  navalCommand: 'Naval Command',
  arcticOps:    'Arctic Ops',
  deepNavy:     'Deep Navy',
  nightOps:     'Night Ops',
};

// Backward-compatible default — all existing `Colors.*` imports continue to work.
export const Colors = Themes.navalCommand;

// ─── Severity helpers ─────────────────────────────────────────────────────────

const SEVERITY_COLOR_KEYS: Record<1 | 2 | 3 | 4 | 5, keyof ColorPalette> = {
  1: 'statusLow',
  2: 'statusLow',
  3: 'statusMedium',
  4: 'statusHigh',
  5: 'statusCritical',
};

const SEVERITY_LABELS: Record<1 | 2 | 3 | 4 | 5, string> = {
  1: 'LOW',
  2: 'MINOR',
  3: 'MODERATE',
  4: 'HIGH',
  5: 'CRITICAL',
};

/** For themed components — returns severity color from the active palette. */
export function getSeverityColorFromPalette(
  severity: 1 | 2 | 3 | 4 | 5,
  palette: ColorPalette,
): string {
  return palette[SEVERITY_COLOR_KEYS[severity]];
}

/** Legacy: Naval Command reference palette. Safe in StyleSheet.create() contexts. */
export function getSeverityColor(severity: 1 | 2 | 3 | 4 | 5): string {
  return getSeverityColorFromPalette(severity, navalCommand);
}

export function getSeverityLabel(severity: 1 | 2 | 3 | 4 | 5): string {
  return SEVERITY_LABELS[severity];
}

/** Legacy: hex alpha bg from Naval Command. In themed components: getSeverityColorFromPalette(...) + '22' */
export function getSeverityBgColor(severity: 1 | 2 | 3 | 4 | 5): string {
  return getSeverityColor(severity) + '22'; // hex alpha: 0x22 ≈ 13%
}

// ─── Agent trace colors ───────────────────────────────────────────────────────
// Semantic, not theme-specific — fixed across all themes for trace log consistency.

export const AgentTraceColors = {
  tool:     Colors.textSecondary,
  result:   Colors.textPrimary,
  decision: '#FFB830',
  action:   '#FF6B35',
  output:   '#3ECF8E',
  error:    '#FF3B3B',
  warning:  '#FFB830',
} as const;
