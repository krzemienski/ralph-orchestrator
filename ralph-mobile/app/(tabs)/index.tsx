import { View, Text, ScrollView, RefreshControl, StyleSheet } from 'react-native';
import { useState, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';

const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  info: '#3b82f6',
  white: '#ffffff',
  gray400: '#9ca3af',
};

export default function DashboardScreen() {
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  }, []);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.info}
          />
        }
      >
        <View style={styles.headerSection}>
          <Text style={styles.title}>Dashboard</Text>
          <Text style={styles.subtitle}>
            Pull to refresh • Orchestrator list will appear here
          </Text>
        </View>

        {/* Placeholder card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Test Orchestrator</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>Running</Text>
            </View>
          </View>
          <Text style={styles.cardMetrics}>
            Iterations: 5/10 • Tokens: 12.5K
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  headerSection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.white,
    marginBottom: 8,
  },
  subtitle: {
    color: colors.gray400,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  cardTitle: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 16,
  },
  badge: {
    backgroundColor: colors.info,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '500',
  },
  cardMetrics: {
    color: colors.gray400,
    fontSize: 14,
  },
});
