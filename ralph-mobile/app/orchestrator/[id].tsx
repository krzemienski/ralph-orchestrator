/**
 * Orchestrator Detail Screen
 *
 * Full detail view for a single orchestrator showing:
 * - Header with back navigation and quick actions
 * - Progress section with visual indicator and ETA
 * - Metrics grid (iterations, tokens, duration, success rate)
 * - Task list with status and errors
 * - Configuration information
 *
 * Features:
 * - Pull to refresh
 * - Auto-refresh every 5 seconds for active orchestrations
 * - Loading and error states
 * - Haptic feedback on actions
 */

import React, { useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Header,
  MetricsGrid,
  ProgressSection,
  TaskList,
  ConfigurationInfo,
} from '../../components/detail';
import { useOrchestrator, useOrchestratorTasks } from '../../lib/hooks/useOrchestrator';
import {
  useStopOrchestrator,
  usePauseOrchestrator,
  useResumeOrchestrator,
} from '../../lib/hooks/useOrchestratorMutations';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  error: '#ef4444',
};

/**
 * OrchestratorDetailScreen - Full detail view for single orchestrator
 */
export default function OrchestratorDetailScreen(): React.ReactElement {
  const { id } = useLocalSearchParams<{ id: string }>();

  // Fetch orchestrator data - refresh every 5s for active orchestrations
  const {
    data: orchestrator,
    isLoading,
    isError,
    error,
    refetch,
    isRefetching,
  } = useOrchestrator(id!, 5000);

  // Fetch tasks - enabled when orchestrator is loaded
  const { data: tasks = [] } = useOrchestratorTasks(id!, !!orchestrator);

  // Mutations for quick actions
  const stopMutation = useStopOrchestrator();
  const pauseMutation = usePauseOrchestrator();
  const resumeMutation = useResumeOrchestrator();

  /**
   * Handle pull to refresh
   */
  const onRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  /**
   * Handle stop action from header
   */
  const handleStop = useCallback(() => {
    if (id) {
      stopMutation.mutate(id);
    }
  }, [id, stopMutation]);

  /**
   * Handle pause action from header
   */
  const handlePause = useCallback(() => {
    if (id) {
      pauseMutation.mutate(id);
    }
  }, [id, pauseMutation]);

  /**
   * Handle resume action from header
   */
  const handleResume = useCallback(() => {
    if (id) {
      resumeMutation.mutate(id);
    }
  }, [id, resumeMutation]);

  // Loading state
  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={colors.gray400} />
          <Text style={styles.loadingText}>Loading orchestrator...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Error state
  if (isError || !orchestrator) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.centerContent}>
          <Text style={styles.errorTitle}>Failed to load orchestrator</Text>
          <Text style={styles.errorMessage}>
            {error?.message || 'Orchestrator not found'}
          </Text>
          <Text style={styles.errorHint}>Pull down to retry</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={onRefresh}
            tintColor={colors.gray400}
          />
        }
      >
        {/* Header with back navigation and quick actions */}
        <View style={styles.section}>
          <Header
            orchestrator={orchestrator}
            onStop={handleStop}
            onPause={handlePause}
            onResume={handleResume}
            isLoading={
              stopMutation.isPending ||
              pauseMutation.isPending ||
              resumeMutation.isPending
            }
            hapticEnabled={true}
          />
        </View>

        {/* Progress section */}
        <View style={styles.section}>
          <ProgressSection
            metrics={orchestrator.metrics}
            status={orchestrator.status}
          />
        </View>

        {/* Metrics grid */}
        <View style={styles.section}>
          <MetricsGrid metrics={orchestrator.metrics} />
        </View>

        {/* Task list */}
        <View style={styles.section}>
          <TaskList tasks={tasks} hapticEnabled={true} />
        </View>

        {/* Configuration info */}
        <View style={styles.section}>
          <ConfigurationInfo
            config={orchestrator.config}
            createdAt={orchestrator.created_at}
            updatedAt={orchestrator.updated_at}
            hapticEnabled={true}
          />
        </View>

        {/* Bottom padding */}
        <View style={styles.bottomPadding} />
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
  scrollContent: {
    padding: 16,
  },
  section: {
    marginBottom: 16,
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    color: colors.gray500,
    fontSize: 14,
    marginTop: 12,
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
    marginBottom: 16,
  },
  errorHint: {
    color: colors.gray500,
    fontSize: 12,
  },
  bottomPadding: {
    height: 40,
  },
});
