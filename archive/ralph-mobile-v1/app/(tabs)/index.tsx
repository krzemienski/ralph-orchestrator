/**
 * @fileoverview Dashboard tab - shows active orchestrators
 * Plan 05-01: Orchestrator List View
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { colors, spacing, typography } from '../../lib/theme';
import { useOrchestrators } from '../../hooks/useOrchestrators';
import OrchestratorCard from '../../components/OrchestratorCard';
import type { Orchestrator } from '../../lib/types';

/**
 * Dashboard screen component
 * Shows active orchestrators with real-time updates
 */
export default function DashboardScreen() {
  const { orchestrators, loading, error, refetch } = useOrchestrators();
  const [refreshing, setRefreshing] = React.useState(false);

  const handleRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const handleCardPress = React.useCallback((orchestrator: Orchestrator) => {
    // TODO: Navigate to detail view (Plan 05-02)
    console.log('Pressed orchestrator:', orchestrator.id);
  }, []);

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Text style={styles.emptyTitle}>No Orchestrators</Text>
      <Text style={styles.emptySubtitle}>
        Start a new orchestration to see it here
      </Text>
    </View>
  );

  const renderError = () => (
    <View style={styles.errorState}>
      <Text style={styles.errorText}>{error}</Text>
      <Text style={styles.retryText} onPress={refetch}>
        Tap to retry
      </Text>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Loading orchestrators...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        {renderError()}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={orchestrators}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <OrchestratorCard orchestrator={item} onPress={handleCardPress} />
        )}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={renderEmptyState}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: typography.sizes.md,
    color: colors.textMuted,
    marginTop: spacing.md,
  },
  listContent: {
    padding: spacing.md,
    flexGrow: 1,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xl * 2,
  },
  emptyTitle: {
    fontSize: typography.sizes.xl,
    fontWeight: typography.weights.bold,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  emptySubtitle: {
    fontSize: typography.sizes.md,
    color: colors.textMuted,
    textAlign: 'center',
  },
  errorState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  errorText: {
    fontSize: typography.sizes.lg,
    color: colors.error,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  retryText: {
    fontSize: typography.sizes.md,
    color: colors.primary,
    textDecorationLine: 'underline',
  },
});
