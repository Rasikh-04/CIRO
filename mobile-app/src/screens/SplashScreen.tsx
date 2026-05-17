import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Colors } from '../theme/colors';
import { FontSizes, FontWeights } from '../theme/typography';
import { Space } from '../theme/spacing';

interface SplashScreenProps {
  onReady: () => void;
}

const MIN_DISPLAY_MS = 1200;
const OFFLINE_TIMEOUT_MS = 3000;
const DOT_COUNT = 3;
const DOT_ANIMATION_DURATION = 400;
const DOT_STAGGER_MS = 160;

export default function SplashScreen({ onReady }: SplashScreenProps): React.JSX.Element {
  const minElapsed = useRef(false);
  const callerReady = useRef(false);
  const firedReady = useRef(false);

  const [showOffline, setShowOffline] = useState(false);

  const dotAnims = useRef<Animated.Value[]>(
    Array.from({ length: DOT_COUNT }, () => new Animated.Value(0)),
  ).current;

  const logoOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const dotsOpacity = useRef(new Animated.Value(0)).current;

  function attemptFireReady(): void {
    if (firedReady.current) return;
    if (minElapsed.current && callerReady.current) {
      firedReady.current = true;
      onReady();
    }
  }

  useEffect(() => {
    Animated.stagger(120, [
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.timing(taglineOpacity, {
        toValue: 1,
        duration: 350,
        useNativeDriver: true,
      }),
      Animated.timing(dotsOpacity, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, [dotsOpacity, logoOpacity, taglineOpacity]);

  useEffect(() => {
    function buildDotSequence(anim: Animated.Value): Animated.CompositeAnimation {
      return Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: 1,
            duration: DOT_ANIMATION_DURATION,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: DOT_ANIMATION_DURATION,
            useNativeDriver: true,
          }),
        ]),
      );
    }

    const animations = dotAnims.map((anim, i) => {
      const staggered = Animated.sequence([
        Animated.delay(i * DOT_STAGGER_MS),
        buildDotSequence(anim),
      ]);
      return staggered;
    });

    animations.forEach((a) => a.start());

    return () => {
      animations.forEach((a) => a.stop());
      dotAnims.forEach((a) => a.setValue(0));
    };
  }, [dotAnims]);

  useEffect(() => {
    const timer = setTimeout(() => {
      minElapsed.current = true;
      attemptFireReady();
    }, MIN_DISPLAY_MS);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!firedReady.current) {
        setShowOffline(true);
        callerReady.current = true;
        attemptFireReady();
      }
    }, OFFLINE_TIMEOUT_MS);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Signal caller readiness on mount — parent should only mount this after data resolves
  useEffect(() => {
    callerReady.current = true;
    attemptFireReady();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <View style={styles.root}>
      <View style={styles.glow} />

      <Animated.View style={[styles.content, { opacity: logoOpacity }]}>
        <Text style={styles.logo}>CIRO</Text>

        <Animated.Text style={[styles.tagline, { opacity: taglineOpacity }]}>
          Real-time crisis intelligence
        </Animated.Text>

        <Animated.View style={[styles.dotsRow, { opacity: dotsOpacity }]}>
          {dotAnims.map((anim, i) => {
            const scale = anim.interpolate({
              inputRange: [0, 1],
              outputRange: [0.7, 1.15],
            });
            const opacity = anim.interpolate({
              inputRange: [0, 1],
              outputRange: [0.35, 1],
            });
            return (
              <Animated.View
                key={i}
                style={[styles.dot, { transform: [{ scale }], opacity }]}
              />
            );
          })}
        </Animated.View>

        {showOffline && (
          <Text style={styles.offlineText}>Offline — using cached data</Text>
        )}
      </Animated.View>

      <Text style={styles.attribution}>Pakistan Emergency Management</Text>
    </View>
  );
}

const DOT_SIZE = 8;

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.bgPrimary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  glow: {
    position: 'absolute',
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: Colors.accentPrimary,
    opacity: 0.04,
  },
  content: {
    alignItems: 'center',
    gap: Space[4],
  },
  logo: {
    fontSize: FontSizes['3xl'],
    fontWeight: FontWeights.bold,
    color: Colors.textPrimary,
    letterSpacing: 4,
  },
  tagline: {
    fontSize: FontSizes.sm,
    fontWeight: FontWeights.regular,
    color: Colors.textSecondary,
    letterSpacing: 0.4,
  },
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Space[2],
    marginTop: Space[2],
  },
  dot: {
    width: DOT_SIZE,
    height: DOT_SIZE,
    borderRadius: DOT_SIZE / 2,
    backgroundColor: Colors.accentPrimary,
  },
  offlineText: {
    marginTop: Space[3],
    fontSize: FontSizes.xs,
    fontWeight: FontWeights.regular,
    color: Colors.textMuted,
    letterSpacing: 0.2,
  },
  attribution: {
    position: 'absolute',
    bottom: Space[8],
    fontSize: FontSizes.xs,
    fontWeight: FontWeights.regular,
    color: Colors.textMuted,
    letterSpacing: 0.5,
    opacity: 0.6,
  },
});
