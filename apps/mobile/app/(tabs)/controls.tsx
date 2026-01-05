/**
 * Controls Screen - Orchestrator control panel
 *
 * Provides full control over orchestrators:
 * - Start new orchestrations
 * - Stop/Pause/Resume running orchestrations
 * - View current status with progress
 * - Review recent actions history
 */

import React, { useState, useCallback, useMemo } from 'react';
import { View, Text, ScrollView, Modal } from 'react-native';
import { useOrchestrators, useOrchestratorMutations } from '../../lib/hooks';
import {
  ControlButtons,
  CurrentStatus,
  NewOrchestrationForm,
  ActionHistory,
} from '../../components/controls';
import type { StartOrchestratorRequest } from '../../lib/types';
import type { ActionRecord } from '../../components/controls/ActionHistory';

/**
 * Controls Screen Component
 */
export default function ControlsScreen(): React.JSX.Element {
  // Fetch orchestrators with auto-refresh
  const { orchestrators, isLoading } = useOrchestrators({ refetchInterval: 5_000 });

  // Get mutations
  const { start, stop, pause, resume } = useOrchestratorMutations();

  // Local state
  const [showNewForm, setShowNewForm] = useState(false);
  const [actionHistory, setActionHistory] = useState<ActionRecord[]>([]);

  // Find active orchestrator (running or paused)
  const activeOrchestrator = useMemo(() => {
    return orchestrators.find(
      (o) => o.status === 'running' || o.status === 'paused'
    ) ?? null;
  }, [orchestrators]);

  // Check if any mutation is loading
  const isMutating =
    start.isPending || stop.isPending || pause.isPending || resume.isPending;

  /** Add action to history */
  const addAction = useCallback(
    (
      type: 'start' | 'stop' | 'pause' | 'resume',
      orchestratorId: string,
      orchestratorName: string,
      status: 'success' | 'pending' | 'failed',
      error?: string
    ) => {
      const action: ActionRecord = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type,
        orchestratorId,
        orchestratorName,
        timestamp: new Date(),
        status,
        error,
      };
      setActionHistory((prev) => [action, ...prev].slice(0, 20)); // Keep last 20
    },
    []
  );

  /** Handle start new orchestration */
  const handleStartNew = useCallback(
    async (request: StartOrchestratorRequest) => {
      const name = request.prompt_file.split('/').pop() ?? 'New Orchestration';
      addAction('start', 'new', name, 'pending');

      try {
        await start.mutateAsync(request);
        setActionHistory((prev) =>
          prev.map((a, i) => (i === 0 ? { ...a, status: 'success' as const } : a))
        );
        setShowNewForm(false);
      } catch (error) {
        setActionHistory((prev) =>
          prev.map((a, i) =>
            i === 0
              ? {
                  ...a,
                  status: 'failed' as const,
                  error: error instanceof Error ? error.message : 'Unknown error',
                }
              : a
          )
        );
      }
    },
    [start, addAction]
  );

  /** Handle stop orchestrator */
  const handleStop = useCallback(async () => {
    if (!activeOrchestrator) return;

    addAction('stop', activeOrchestrator.id, activeOrchestrator.name, 'pending');

    try {
      await stop.mutateAsync(activeOrchestrator.id);
      setActionHistory((prev) =>
        prev.map((a, i) => (i === 0 ? { ...a, status: 'success' as const } : a))
      );
    } catch (error) {
      setActionHistory((prev) =>
        prev.map((a, i) =>
          i === 0
            ? {
                ...a,
                status: 'failed' as const,
                error: error instanceof Error ? error.message : 'Unknown error',
              }
            : a
        )
      );
    }
  }, [activeOrchestrator, stop, addAction]);

  /** Handle pause orchestrator */
  const handlePause = useCallback(async () => {
    if (!activeOrchestrator) return;

    addAction('pause', activeOrchestrator.id, activeOrchestrator.name, 'pending');

    try {
      await pause.mutateAsync(activeOrchestrator.id);
      setActionHistory((prev) =>
        prev.map((a, i) => (i === 0 ? { ...a, status: 'success' as const } : a))
      );
    } catch (error) {
      setActionHistory((prev) =>
        prev.map((a, i) =>
          i === 0
            ? {
                ...a,
                status: 'failed' as const,
                error: error instanceof Error ? error.message : 'Unknown error',
              }
            : a
        )
      );
    }
  }, [activeOrchestrator, pause, addAction]);

  /** Handle resume orchestrator */
  const handleResume = useCallback(async () => {
    if (!activeOrchestrator) return;

    addAction('resume', activeOrchestrator.id, activeOrchestrator.name, 'pending');

    try {
      await resume.mutateAsync(activeOrchestrator.id);
      setActionHistory((prev) =>
        prev.map((a, i) => (i === 0 ? { ...a, status: 'success' as const } : a))
      );
    } catch (error) {
      setActionHistory((prev) =>
        prev.map((a, i) =>
          i === 0
            ? {
                ...a,
                status: 'failed' as const,
                error: error instanceof Error ? error.message : 'Unknown error',
              }
            : a
        )
      );
    }
  }, [activeOrchestrator, resume, addAction]);

  return (
    <View className="flex-1 bg-background">
      {/* Header */}
      <View className="px-4 pt-4 pb-2">
        <Text className="text-2xl font-bold text-textPrimary">Controls</Text>
        <Text className="text-sm text-textSecondary">
          Manage your orchestration runs
        </Text>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerClassName="p-4 gap-4"
        showsVerticalScrollIndicator={false}
      >
        {/* Current Status */}
        <CurrentStatus orchestrator={activeOrchestrator} />

        {/* Control Buttons */}
        <ControlButtons
          status={activeOrchestrator?.status ?? null}
          isLoading={isMutating || isLoading}
          onStart={() => setShowNewForm(true)}
          onStop={handleStop}
          onPause={handlePause}
          onResume={handleResume}
        />

        {/* Action History */}
        <ActionHistory actions={actionHistory} maxItems={10} />
      </ScrollView>

      {/* New Orchestration Modal */}
      <Modal
        visible={showNewForm}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowNewForm(false)}
      >
        <View className="flex-1 bg-background">
          <NewOrchestrationForm
            onSubmit={handleStartNew}
            isSubmitting={start.isPending}
            onCancel={() => setShowNewForm(false)}
          />
        </View>
      </Modal>
    </View>
  );
}
