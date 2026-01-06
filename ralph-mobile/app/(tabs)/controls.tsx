/**
 * Controls Screen
 *
 * Control panel for orchestrator actions:
 * - Start new orchestrations
 * - Pause/Resume/Stop existing orchestrations
 * - View current orchestrator status
 *
 * Features haptic feedback for all actions.
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ControlButtons, CurrentStatus, NewOrchestrationForm } from '../../components/controls';
import { useOrchestrators } from '../../lib/hooks/useOrchestrators';
import {
  useStartOrchestrator,
  useStopOrchestrator,
  usePauseOrchestrator,
  useResumeOrchestrator,
} from '../../lib/hooks/useOrchestratorMutations';
import type { StartOrchestratorRequest, Orchestrator } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  success: '#22c55e',
  error: '#ef4444',
};

/**
 * Get the most recent active orchestrator
 */
function getActiveOrchestrator(orchestrators: Orchestrator[] | undefined): Orchestrator | undefined {
  if (!orchestrators || orchestrators.length === 0) return undefined;

  // Priority: running > paused > pending > completed/failed (most recent)
  const running = orchestrators.find((o) => o.status === 'running');
  if (running) return running;

  const paused = orchestrators.find((o) => o.status === 'paused');
  if (paused) return paused;

  const pending = orchestrators.find((o) => o.status === 'pending');
  if (pending) return pending;

  // Return the most recently updated
  return orchestrators.sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  )[0];
}

/**
 * ControlsScreen - Main control panel
 */
export default function ControlsScreen(): React.ReactElement {
  // State for form visibility
  const [showForm, setShowForm] = useState(false);

  // Query orchestrators
  const {
    data: orchestrators,
    isLoading: isLoadingOrchestrators,
    refetch,
    isRefetching,
  } = useOrchestrators();

  // Mutations
  const startMutation = useStartOrchestrator();
  const stopMutation = useStopOrchestrator();
  const pauseMutation = usePauseOrchestrator();
  const resumeMutation = useResumeOrchestrator();

  // Get active orchestrator
  const activeOrchestrator = useMemo(
    () => getActiveOrchestrator(orchestrators),
    [orchestrators]
  );

  // Check if any mutation is in progress
  const isAnyMutationLoading =
    startMutation.isPending ||
    stopMutation.isPending ||
    pauseMutation.isPending ||
    resumeMutation.isPending;

  /**
   * Handle start action
   */
  const handleStart = useCallback(() => {
    setShowForm(true);
  }, []);

  /**
   * Handle form submission
   */
  const handleFormSubmit = useCallback(
    (request: StartOrchestratorRequest) => {
      startMutation.mutate(request, {
        onSuccess: () => {
          setShowForm(false);
          Alert.alert('Success', 'Orchestration started successfully');
        },
        onError: (error) => {
          Alert.alert('Error', error.message || 'Failed to start orchestration');
        },
      });
    },
    [startMutation]
  );

  /**
   * Handle pause action
   */
  const handlePause = useCallback(
    (id: string) => {
      pauseMutation.mutate(id, {
        onSuccess: () => {
          Alert.alert('Paused', 'Orchestration paused successfully');
        },
        onError: (error) => {
          Alert.alert('Error', error.message || 'Failed to pause orchestration');
        },
      });
    },
    [pauseMutation]
  );

  /**
   * Handle resume action
   */
  const handleResume = useCallback(
    (id: string) => {
      resumeMutation.mutate(id, {
        onSuccess: () => {
          Alert.alert('Resumed', 'Orchestration resumed successfully');
        },
        onError: (error) => {
          Alert.alert('Error', error.message || 'Failed to resume orchestration');
        },
      });
    },
    [resumeMutation]
  );

  /**
   * Handle stop action
   */
  const handleStop = useCallback(
    (id: string) => {
      stopMutation.mutate(id, {
        onSuccess: () => {
          Alert.alert('Stopped', 'Orchestration stopped successfully');
        },
        onError: (error) => {
          Alert.alert('Error', error.message || 'Failed to stop orchestration');
        },
      });
    },
    [stopMutation]
  );

  /**
   * Handle pull to refresh
   */
  const onRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

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
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Controls</Text>
          <Text style={styles.subtitle}>
            Start, stop, pause, and resume orchestrations
          </Text>
        </View>

        {/* Current Status */}
        <View style={styles.section}>
          <CurrentStatus orchestrator={activeOrchestrator} />
        </View>

        {/* Control Buttons */}
        <View style={styles.section}>
          <ControlButtons
            currentStatus={activeOrchestrator?.status}
            orchestratorId={activeOrchestrator?.id}
            hapticEnabled={true}
            onStart={handleStart}
            onPause={handlePause}
            onResume={handleResume}
            onStop={handleStop}
            isLoading={isAnyMutationLoading}
          />
        </View>

        {/* New Orchestration Form (shown when Start is clicked) */}
        {showForm && (
          <View style={styles.section}>
            <NewOrchestrationForm
              onSubmit={handleFormSubmit}
              isSubmitting={startMutation.isPending}
              hapticEnabled={true}
              errorMessage={startMutation.error?.message}
            />
          </View>
        )}

        {/* Loading indicator during initial load */}
        {isLoadingOrchestrators && (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading orchestrators...</Text>
          </View>
        )}

        {/* Orchestrator count */}
        {orchestrators && orchestrators.length > 0 && (
          <View style={styles.infoSection}>
            <Text style={styles.infoText}>
              {orchestrators.length} orchestrator{orchestrators.length !== 1 ? 's' : ''} total
            </Text>
            <Text style={styles.infoSubtext}>
              Pull down to refresh
            </Text>
          </View>
        )}
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
  header: {
    alignItems: 'center',
    paddingVertical: 24,
    marginBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.white,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: colors.gray400,
    textAlign: 'center',
  },
  section: {
    marginBottom: 16,
  },
  loadingContainer: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  loadingText: {
    color: colors.gray500,
    fontSize: 14,
  },
  infoSection: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  infoText: {
    color: colors.gray500,
    fontSize: 13,
    marginBottom: 4,
  },
  infoSubtext: {
    color: colors.gray500,
    fontSize: 11,
  },
});
