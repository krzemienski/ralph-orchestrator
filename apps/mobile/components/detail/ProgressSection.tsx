/**
 * ProgressSection - Visual progress indicator for orchestrator detail
 *
 * Displays:
 * - Circular or linear progress indicator
 * - Current phase/iteration label
 * - ETA calculation based on rate
 */

import React, { useMemo } from 'react';
import { View, Text } from 'react-native';
import type { Orchestrator, OrchestratorStatus } from '../../lib/types';

interface ProgressSectionProps {
  /** Orchestrator data */
  orchestrator: Orchestrator;
}

/** Format duration for ETA display */
function formatETA(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    return `${mins}m`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

/** Calculate ETA based on progress */
function calculateETA(
  completed: number,
  total: number,
  elapsed: number
): string | null {
  if (completed === 0 || total === 0) return null;
  const remaining = total - completed;
  const rate = completed / elapsed;
  if (rate === 0) return null;
  const etaSeconds = remaining / rate;
  return formatETA(etaSeconds);
}

/** Get status-based ring color */
function getStatusColor(status: OrchestratorStatus): string {
  const colors: Record<OrchestratorStatus, string> = {
    pending: '#9ca3af', // gray
    running: '#3b82f6', // blue
    paused: '#f59e0b', // amber
    completed: '#22c55e', // green
    failed: '#ef4444', // red
  };
  return colors[status];
}

/** Simple circular progress indicator */
function CircularProgress({
  progress,
  color,
  size = 120,
}: {
  progress: number;
  color: string;
  size?: number;
}): React.JSX.Element {
  // Clamp progress between 0-100
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        borderWidth: 8,
        borderColor: '#374151', // gray-700
        backgroundColor: 'transparent',
        position: 'relative',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* Progress arc overlay */}
      <View
        style={{
          position: 'absolute',
          top: -8,
          left: -8,
          width: size,
          height: size,
          borderRadius: size / 2,
          borderWidth: 8,
          borderColor: color,
          borderTopColor: clampedProgress > 75 ? color : 'transparent',
          borderRightColor: clampedProgress > 50 ? color : 'transparent',
          borderBottomColor: clampedProgress > 25 ? color : 'transparent',
          borderLeftColor: clampedProgress > 0 ? color : 'transparent',
          transform: [{ rotate: `${(clampedProgress / 100) * 360 - 90}deg` }],
        }}
      />
    </View>
  );
}

/** Linear progress bar */
function LinearProgress({
  progress,
  color,
}: {
  progress: number;
  color: string;
}): React.JSX.Element {
  // Clamp progress between 0-100
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <View className="h-3 bg-gray-700 rounded-full overflow-hidden">
      <View
        className="h-full rounded-full"
        style={{
          width: `${clampedProgress}%`,
          backgroundColor: color,
        }}
      />
    </View>
  );
}

/**
 * ProgressSection component
 */
export function ProgressSection({ orchestrator }: ProgressSectionProps): React.JSX.Element {
  const { status, metrics } = orchestrator;
  const { iterations_completed, iterations_total, duration_seconds } = metrics;

  // Calculate progress percentage
  const progress = useMemo(() => {
    if (iterations_total === 0) return 0;
    return Math.round((iterations_completed / iterations_total) * 100);
  }, [iterations_completed, iterations_total]);

  // Calculate ETA for running orchestrations
  const eta = useMemo(() => {
    if (status !== 'running') return null;
    return calculateETA(iterations_completed, iterations_total, duration_seconds);
  }, [status, iterations_completed, iterations_total, duration_seconds]);

  // Get status color
  const statusColor = getStatusColor(status);

  // Get status label
  const getStatusLabel = (): string => {
    switch (status) {
      case 'pending':
        return 'Waiting to start...';
      case 'running':
        return `Iteration ${iterations_completed + 1} of ${iterations_total}`;
      case 'paused':
        return 'Paused';
      case 'completed':
        return 'Completed successfully';
      case 'failed':
        return 'Failed';
    }
  };

  return (
    <View className="bg-surface rounded-2xl p-4">
      <Text className="text-sm font-medium text-textSecondary mb-4">Progress</Text>

      <View className="items-center">
        {/* Circular progress with percentage */}
        <View className="relative mb-4">
          <CircularProgress progress={progress} color={statusColor} size={120} />
          <View className="absolute inset-0 items-center justify-center">
            <Text className="text-3xl font-bold text-textPrimary">{progress}%</Text>
          </View>
        </View>

        {/* Linear progress bar */}
        <View className="w-full mb-3">
          <LinearProgress progress={progress} color={statusColor} />
        </View>

        {/* Status label */}
        <Text className="text-sm text-textSecondary text-center">{getStatusLabel()}</Text>

        {/* ETA display for running orchestrations */}
        {eta && status === 'running' && (
          <View className="flex-row items-center mt-2 bg-surfaceLight rounded-lg px-3 py-1.5">
            <Text className="text-xs text-textSecondary mr-1">⏱ ETA:</Text>
            <Text className="text-sm font-medium text-textPrimary">{eta}</Text>
          </View>
        )}

        {/* Completed message */}
        {status === 'completed' && (
          <View className="flex-row items-center mt-2 bg-green-500/20 rounded-lg px-3 py-1.5">
            <Text className="text-sm text-green-400">✓ All iterations complete</Text>
          </View>
        )}

        {/* Failed message with error */}
        {status === 'failed' && orchestrator.error && (
          <View className="mt-3 bg-red-500/10 rounded-lg p-3 w-full">
            <Text className="text-xs text-red-400 font-medium mb-1">Error</Text>
            <Text className="text-sm text-red-300" numberOfLines={3}>
              {orchestrator.error}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

export default ProgressSection;
