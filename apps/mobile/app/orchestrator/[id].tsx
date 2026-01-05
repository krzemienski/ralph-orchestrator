/**
 * Orchestrator Detail Screen
 *
 * Full detail view for a single orchestrator showing:
 * - Header with name, status, quick actions
 * - Progress visualization
 * - Metrics grid
 * - Task list
 * - Configuration info
 */

import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl, Pressable, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useOrchestrator, useOrchestratorMutations } from '../../lib/hooks';
import {
  Header,
  MetricsGrid,
  ProgressSection,
  TaskList,
  ConfigurationInfo,
} from '../../components/detail';
import type { Task, ApiError } from '../../lib/types';

/**
 * Mock tasks for demonstration (will be replaced with real API data)
 */
function generateMockTasks(orchestratorId: string, iterationsCompleted: number): Task[] {
  const tasks: Task[] = [];
  const taskNames = [
    'Initialize context',
    'Load prompt file',
    'Parse configuration',
    'Execute iteration',
    'Validate output',
    'Save checkpoint',
  ];

  for (let i = 0; i < Math.min(iterationsCompleted + 2, taskNames.length); i++) {
    const isCompleted = i < iterationsCompleted;
    const isRunning = i === iterationsCompleted;
    const isFailed = i === iterationsCompleted - 1 && Math.random() > 0.8;

    tasks.push({
      id: `task-${i}`,
      orchestrator_id: orchestratorId,
      name: taskNames[i],
      status: isFailed ? 'failed' : isRunning ? 'running' : isCompleted ? 'completed' : 'pending',
      started_at: isCompleted || isRunning ? new Date(Date.now() - (iterationsCompleted - i) * 60000).toISOString() : undefined,
      completed_at: isCompleted ? new Date(Date.now() - (iterationsCompleted - i - 1) * 60000).toISOString() : undefined,
      output: isCompleted ? `Task ${taskNames[i]} completed successfully.` : undefined,
      error: isFailed ? 'Validation failed: unexpected output format' : undefined,
    });
  }

  return tasks;
}

/**
 * Error state component
 */
function ErrorState({
  error,
  onRetry,
}: {
  error: ApiError;
  onRetry: () => void;
}): React.JSX.Element {
  return (
    <View className="flex-1 bg-background items-center justify-center p-8">
      <View className="w-16 h-16 rounded-full bg-red-500/20 items-center justify-center mb-4">
        <Text className="text-3xl">⚠️</Text>
      </View>
      <Text className="text-lg font-medium text-textPrimary text-center mb-2">
        Failed to Load
      </Text>
      <Text className="text-sm text-textSecondary text-center mb-4">
        {error.error}
      </Text>
      <Pressable
        className="bg-blue-600 rounded-xl px-6 py-3 active:opacity-80"
        onPress={onRetry}
      >
        <Text className="text-white font-semibold">Retry</Text>
      </Pressable>
    </View>
  );
}

/**
 * Loading state component
 */
function LoadingState(): React.JSX.Element {
  return (
    <View className="flex-1 bg-background items-center justify-center">
      <ActivityIndicator size="large" color="#3b82f6" />
      <Text className="text-sm text-textSecondary mt-4">Loading orchestrator...</Text>
    </View>
  );
}

/**
 * Orchestrator Detail Screen Component
 */
export default function OrchestratorDetailScreen(): React.JSX.Element {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  // Fetch orchestrator data with auto-refresh for active orchestrations
  const { orchestrator, isLoading, error, refetch } = useOrchestrator(id ?? '', {
    enabled: !!id,
  });

  // Get mutations
  const { stop, pause, resume } = useOrchestratorMutations();

  // Track mutation state
  const [isMutating, setIsMutating] = useState(false);

  // Pull-to-refresh
  const [isRefreshing, setIsRefreshing] = useState(false);

  /** Handle refresh */
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  }, [refetch]);

  /** Handle stop action */
  const handleStop = useCallback(async () => {
    if (!id) return;
    setIsMutating(true);
    try {
      await stop.mutateAsync(id);
    } finally {
      setIsMutating(false);
    }
  }, [id, stop]);

  /** Handle pause action */
  const handlePause = useCallback(async () => {
    if (!id) return;
    setIsMutating(true);
    try {
      await pause.mutateAsync(id);
    } finally {
      setIsMutating(false);
    }
  }, [id, pause]);

  /** Handle resume action */
  const handleResume = useCallback(async () => {
    if (!id) return;
    setIsMutating(true);
    try {
      await resume.mutateAsync(id);
    } finally {
      setIsMutating(false);
    }
  }, [id, resume]);

  // Loading state
  if (isLoading && !orchestrator) {
    return <LoadingState />;
  }

  // Error state
  if (error && !orchestrator) {
    return <ErrorState error={error} onRetry={handleRefresh} />;
  }

  // No orchestrator found
  if (!orchestrator) {
    return (
      <View className="flex-1 bg-background items-center justify-center p-8">
        <View className="w-16 h-16 rounded-full bg-gray-500/20 items-center justify-center mb-4">
          <Text className="text-3xl">🔍</Text>
        </View>
        <Text className="text-lg font-medium text-textPrimary text-center mb-2">
          Not Found
        </Text>
        <Text className="text-sm text-textSecondary text-center mb-4">
          Orchestrator &quot;{id}&quot; could not be found
        </Text>
        <Pressable
          className="bg-blue-600 rounded-xl px-6 py-3 active:opacity-80"
          onPress={() => router.back()}
        >
          <Text className="text-white font-semibold">Go Back</Text>
        </Pressable>
      </View>
    );
  }

  // Generate mock tasks based on current progress
  const mockTasks = generateMockTasks(orchestrator.id, orchestrator.metrics.iterations_completed);

  return (
    <View className="flex-1 bg-background">
      {/* Back button header */}
      <View className="flex-row items-center px-4 pt-4 pb-2">
        <Pressable
          className="flex-row items-center active:opacity-70"
          onPress={() => router.back()}
        >
          <Text className="text-2xl text-blue-500 mr-2">‹</Text>
          <Text className="text-base text-blue-500">Back</Text>
        </Pressable>
      </View>

      {/* Scrollable content */}
      <ScrollView
        className="flex-1"
        contentContainerClassName="p-4 gap-4 pb-8"
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#3b82f6"
          />
        }
      >
        {/* Header section */}
        <Header
          orchestrator={orchestrator}
          isLoading={isMutating}
          onStop={handleStop}
          onPause={handlePause}
          onResume={handleResume}
        />

        {/* Progress section */}
        <ProgressSection orchestrator={orchestrator} />

        {/* Metrics grid */}
        <MetricsGrid metrics={orchestrator.metrics} />

        {/* Task list */}
        <TaskList tasks={mockTasks} />

        {/* Configuration info */}
        <ConfigurationInfo orchestrator={orchestrator} />
      </ScrollView>
    </View>
  );
}
