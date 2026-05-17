import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { fetchActiveCrises } from '../lib/api';
import type { CrisisEvent } from '../types';
import { getSeverityColor } from '../theme/colors';
import { useTheme } from '../theme/ThemeContext';
import { FontSizes, FontWeights } from '../theme/typography';
import { Space, Radii } from '../theme/spacing';
import SeverityBadge from '../components/ui/SeverityBadge';

export default function AlertsScreen({ navigation }: { navigation: any }) {
  const { colors } = useTheme();
  const [crises, setCrises] = useState<CrisisEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const styles = useMemo(() => StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.bgPrimary },
    header: {
      paddingHorizontal: Space[4],
      paddingTop: Space[4],
      paddingBottom: Space[4],
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: FontSizes.xl,
      fontWeight: FontWeights.bold,
      color: colors.textPrimary,
    },
    headerSubtitle: {
      fontSize: FontSizes.sm,
      color: colors.textSecondary,
      marginTop: Space[1],
    },
    centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    emptyTitle: {
      fontSize: FontSizes.lg,
      fontWeight: FontWeights.semibold,
      color: colors.textPrimary,
      marginBottom: Space[2],
    },
    emptySubtitle: { fontSize: FontSizes.sm, color: colors.textSecondary, textAlign: 'center' },
    listContent: { paddingHorizontal: Space[3], paddingVertical: Space[3] },
    alertCard: {
      backgroundColor: colors.bgSurface,
      borderRadius: Radii.md,
      borderLeftWidth: 4,
      paddingHorizontal: Space[4],
      paddingVertical: Space[3],
      marginBottom: Space[3],
    },
    alertHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: Space[1],
    },
    alertType: {
      fontSize: FontSizes.md,
      fontWeight: FontWeights.bold,
      color: colors.textPrimary,
      flex: 1,
      marginRight: Space[2],
    },
    alertDesc: {
      fontSize: FontSizes.sm,
      color: colors.textSecondary,
      marginBottom: 2,
      textTransform: 'capitalize',
    },
    alertTime: { fontSize: FontSizes.xs, color: colors.textMuted, marginBottom: Space[3] },
    routeButton: { alignSelf: 'flex-start', paddingVertical: Space[1] },
    routeButtonText: {
      fontSize: FontSizes.sm,
      color: colors.accentSecondary,
      fontWeight: FontWeights.medium,
    },
  }), [colors]);

  const loadCrises = useCallback(async () => {
    setLoading(true);
    const data = await fetchActiveCrises();
    setCrises(data.sort((a, b) => b.severity - a.severity));
    setLoading(false);
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadCrises();
    setRefreshing(false);
  }, [loadCrises]);

  useFocusEffect(useCallback(() => { loadCrises(); }, [loadCrises]));

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Alerts</Text>
        <Text style={styles.headerSubtitle}>
          {crises.length > 0 ? `${crises.length} active` : 'No active alerts'} · Islamabad
        </Text>
      </View>

      {loading && !refreshing ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.accentPrimary} />
        </View>
      ) : crises.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyTitle}>No Active Crises</Text>
          <Text style={styles.emptySubtitle}>All clear. Check back for updates.</Text>
        </View>
      ) : (
        <FlatList
          data={crises}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.accentPrimary}
            />
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.alertCard, { borderLeftColor: getSeverityColor(item.severity) }]}
              onPress={() => navigation.navigate('CrisisDetail', { crisisId: item.id })}
            >
              <View style={styles.alertHeader}>
                <Text style={styles.alertType} numberOfLines={1}>{item.location_name}</Text>
                <SeverityBadge severity={item.severity} size="sm" />
              </View>
              <Text style={styles.alertDesc}>
                {item.type.replace(/_/g, ' ')} · {item.status}
              </Text>
              <Text style={styles.alertTime}>
                {new Date(item.detected_at).toLocaleString()}
              </Text>
              <TouchableOpacity
                style={styles.routeButton}
                onPress={() => navigation.navigate('Routes', { crisisId: item.id })}
              >
                <Text style={styles.routeButtonText}>Get Safe Routes →</Text>
              </TouchableOpacity>
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}
