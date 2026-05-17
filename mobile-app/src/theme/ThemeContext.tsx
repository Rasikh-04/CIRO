import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { type ColorPalette, type ThemeKey, Themes } from './colors';

const STORAGE_KEY = 'ciro_theme';
const DEFAULT_THEME: ThemeKey = 'navalCommand';

interface ThemeContextValue {
  colors: ColorPalette;
  themeKey: ThemeKey;
  setTheme: (key: ThemeKey) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function isThemeKey(value: unknown): value is ThemeKey {
  return typeof value === 'string' && Object.prototype.hasOwnProperty.call(Themes, value);
}

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps): React.JSX.Element {
  const [themeKey, setThemeKey] = useState<ThemeKey>(DEFAULT_THEME);

  // Single AsyncStorage read on mount
  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((stored: string | null) => { if (isThemeKey(stored)) setThemeKey(stored); })
      .catch(() => undefined);
  }, []);

  // useCallback-stable so consumers of only setTheme don't re-render on theme change
  const setTheme = useCallback((key: ThemeKey) => {
    setThemeKey(key);
    AsyncStorage.setItem(STORAGE_KEY, key).catch(() => undefined);
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({ colors: Themes[themeKey], themeKey, setTheme }),
    [themeKey, setTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (ctx === null) {
    throw new Error('useTheme() must be called inside <ThemeProvider>');
  }
  return ctx;
}
