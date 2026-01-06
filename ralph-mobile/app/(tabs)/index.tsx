/**
 * Dashboard Screen
 *
 * Main screen displaying list of orchestrators with real-time status updates.
 * Features:
 * - FlatList for efficient rendering of orchestrator cards
 * - Pull-to-refresh for manual data reload
 * - Loading, empty, and error states
 * - Navigation to detail view on card tap
 */

import React, { useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  RefreshControl,
  StyleSheet,
  ActivityIndicator,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useOrchestrators } from '../../lib/hooks/useOrchestrators';
import { OrchestratorCard } from '../../components/dashboard/OrchestratorCard';
import { EmptyState } from '../../components/dashboard/EmptyState';
import type { Orchestrator } from '../../lib/types';

/**
 * Theme colors for dark mode
 */
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  info: '#3b82f6',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  error: '#ef4444',
  errorDim: '#ef444420',
};

/**
 * DashboardScreen - Main screen showing all orchestrators
 *
 * Uses FlatList for performance with large lists:
 * - Pull-to-refresh triggers data reload
 * - Automatic polling every 10 seconds
 * - Loading spinner during initial fetch
 * - Empty state when no orchestrators exist
 * - Error state with retry button on API failure
 */
export default function DashboardScreen() {
  const router = useRouter();
  const {
    data: orchestrators,
    isLoading,
    isError,
    error,
    refetch,
    isRefetching,
  } = useOrchestrators(10000); // Poll every 10 seconds

  /**
   * Handle pull-to-refresh action
   */
  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  /**
   * Navigate to controls tab to start new orchestration
   */
  const handleStartNew = useCallback(() => {
    router.push('/(tabs)/controls');
  }, [router]);

  /**
   * Render individual orchestrator card
   */
  const renderItem = useCallback(
    ({ item }: { item: Orchestrator }) => (
      <OrchestratorCard orchestrator={item} />
    ),
    []
  );

  /**
   * Extract unique key for each item
   */
  const keyExtractor = useCallback(
    (item: Orchestrator) => item.id,
    []
  );

  /**
   * List header component with title
   */
  const ListHeader = useCallback(
    () => (
      <View style={styles.headerSection}>
        <Text style={styles.title}>Dashboard</Text>
        <Text style={styles.subtitle}>
          {orchestrators && orchestrators.length > 0
            ? `${orchestrators.length} orchestrator${orchestrators.length === 1 ? '' : 's'}`
            : 'Pull to refresh'}
        </Text>
      </View>
    ),
    [orchestrators]
  );

  /**
   * Empty state component
   */
  const ListEmpty = useCallback(
    () => (
      <EmptyState
        title="No Orchestrators"
        subtitle="Start a new orchestration to monitor your workflows"
        actionText="Start New"
        onAction={handleStartNew}
      />
    ),
    [handleStartNew]
  );

  // Loading state - initial load
  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.info} />
          <Text style={styles.loadingText}>Loading orchestrators...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Error state with retry
  if (isError) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.errorContainer}>
          <View style={styles.errorContent}>
            <Text style={styles.errorTitle}>Connection Error</Text>
            <Text style={styles.errorMessage}>
              {error?.message || 'Unable to fetch orchestrators'}
            </Text>
            <Pressable
              onPress={() => refetch()}
              style={({ pressed }) => [
                styles.retryButton,
                pressed && styles.retryButtonPressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Retry loading orchestrators"
            >
              <Text style={styles.retryButtonText}>Retry</Text>
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <FlatList
        data={orchestrators || []}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        ListHeaderComponent={ListHeader}
        ListEmptyComponent={ListEmpty}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={handleRefresh}
            tintColor={colors.info}
            colors={[colors.info]}
          />
        }
        // Performance optimizations
        removeClippedSubviews={true}
        maxToRenderPerBatch={10}
        windowSize={5}
        initialNumToRender={10}
        getItemLayout={(_, index) => ({
          length: CARD_HEIGHT,
          offset: HEADER_HEIGHT + index * CARD_HEIGHT,
          index,
        })}
        accessibilityLabel="Orchestrators list"
        accessibilityHint="Pull down to refresh. Tap a card to view details."
      />
    </SafeAreaView>
  );
}

/**
 * Estimated heights for getItemLayout optimization
 */
const CARD_HEIGHT = 156; // Estimated card height including margin
const HEADER_HEIGHT = 80; // Estimated header height

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  listContent: {
    padding: 16,
    flexGrow: 1,
  },
  headerSection: {
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.white,
    marginBottom: 4,
  },
  subtitle: {
    color: colors.gray400,
    fontSize: 14,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  loadingText: {
    color: colors.gray400,
    marginTop: 16,
    fontSize: 15,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  errorContent: {
    backgroundColor: colors.errorDim,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    maxWidth: 300,
  },
  errorTitle: {
    color: colors.error,
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  errorMessage: {
    color: colors.gray400,
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  retryButton: {
    backgroundColor: colors.error,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  retryButtonPressed: {
    opacity: 0.8,
  },
  retryButtonText: {
    color: colors.white,
    fontSize: 15,
    fontWeight: '600',
  },
});
