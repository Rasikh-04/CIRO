// 4pt base grid

export const Space = {
  1:  4,
  2:  8,
  3:  12,
  4:  16,
  5:  20,
  6:  24,
  8:  32,
  10: 40,
  12: 48,
  16: 64,
} as const;

export const Radii = {
  sm:   6,
  md:   12,
  lg:   16,
  pill: 100,
} as const;

export const TouchTargetMin = 48;
export const TouchTargetPreferred = 56; // emergency action buttons

export const Layout = {
  paddingCard:      { paddingHorizontal: 20, paddingVertical: 16 },
  paddingScreen:    { paddingHorizontal: 16 },
  paddingScreenTop: 16,
  gapListItem:      12,
  gapSection:       24,
  gapInline:        8,
} as const;
