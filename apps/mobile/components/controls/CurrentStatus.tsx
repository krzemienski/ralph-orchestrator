/**
 * CurrentStatus - Large status indicator for active orchestrator
 *
 * Displays:
 * - Large status badge with icon
 * - Progress indicator showing iteration completion
 * - ETA/elapsed time
 * - Current iteration details
 */

import React, { useMemo } from 'react';
import { View, Text } from 'react-native';
import type { Orchestrator, OrchestratorStatus } from '../../lib/types';

interface CurrentStatusProps {
  /** Active orchestrator data, or null if none */
  orchestrator: Orchestrator | null;
}

/** Status display configuration */
interface StatusConfig {
  icon: string;
  label: string;
  color: string;
  bgColor: string;
  ringColor: string;
}

/** Get status display configuration */
function getStatusConfig(status: OrchestratorStatus): StatusConfig {
  switch (status) {
    case 'pending':
      return {
        icon: '⏳',
        label: 'Pending',
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/20',
        ringColor: '#facc15',
      };
    case 'running':
      return {
        icon: '▶',
        label: 'Running',
        color: 'text-green-400',
        bgColor: 'bg-green-500/20',
        ringColor: '#22c55e',
      };
    case 'paused':
      return {
        icon: '⏸',
        label: 'Paused',
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/20',
        ringColor: '#fb923c',
      };
    case 'completed':
      return {
        icon: '✓',
        label: 'Completed',
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/20',
        ringColor: '#3b82f6',
      };
    case 'failed':
      return {
        icon: '✕',
        label: 'Failed',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        ringColor: '#ef4444',
      };
  }
}

/** Format duration to human-readable string */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
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
  const eta = remaining / rate;
  return formatDuration(eta);
}

/**
 * Simple Progress Circle Component (no SVG dependency)
 * Uses View-based approach with border styling
 */
function ProgressCircle({
  progress,
  color,
  size = 140,
}: {
  progress: number;
  color: string;
  size?: number;
}): React.JSX.Element {
  // Simple circular progress using nested views
  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        borderWidth: 8,
        borderColor: '#374151',
        backgroundColor: 'transparent',
        position: 'relative',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* Progress arc overlay using conic gradient simulation */}
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
          borderTopColor: progress > 75 ? color : 'transparent',
          borderRightColor: progress > 50 ? color : 'transparent',
          borderBottomColor: progress > 25 ? color : 'transparent',
          borderLeftColor: progress > 0 ? color : 'transparent',
          transform: [{ rotate: `${(progress / 100) * 360 - 90}deg` }],
        }}
      />
    </View>
  );
}

/**
 * CurrentStatus component
 */
export function CurrentStatus({
  orchestrator,
}: CurrentStatusProps): React.JSX.Element {
  // Calculate progress percentage
  const progress = useMemo(() => {
    if (!orchestrator) return 0;
    const { iterations_completed, iterations_total } = orchestrator.metrics;
    if (iterations_total === 0) return 0;
    return Math.round((iterations_completed / iterations_total) * 100);
  }, [orchestrator]);

  // Calculate ETA
  const eta = useMemo(() => {
    if (!orchestrator || orchestrator.status !== 'running') return null;
    const { iterations_completed, iterations_total, duration_seconds } =
      orchestrator.metrics;
    return calculateETA(iterations_completed, iterations_total, duration_seconds);
  }, [orchestrator]);

  // No orchestrator selected
  if (!orchestrator) {
    return (
      <View className="bg-surface rounded-2xl p-6 items-center">
        <View className="w-28 h-28 rounded-full bg-surfaceLight items-center justify-center mb-4">
          <Text className="text-4xl">🚀</Text>
        </View>
        <Text className="text-xl font-semibold text-textPrimary mb-1">
          No Active Orchestration
        </Text>
        <Text className="text-sm text-textSecondary text-center">
          Start a new orchestration or select an existing one from the dashboard
        </Text>
      </View>
    );
  }

  const config = getStatusConfig(orchestrator.status);
  const { iterations_completed, iterations_total, duration_seconds, tokens_used } =
    orchestrator.metrics;

  return (
    <View className="bg-surface rounded-2xl p-6">
      {/* Status Header */}
      <View className="flex-row items-center justify-between mb-6">
        <View>
          <Text className="text-sm text-textSecondary">Current Status</Text>
          <Text className="text-lg font-semibold text-textPrimary" numberOfLines={1}>
            {orchestrator.name}
          </Text>
        </View>
        <View className={`px-3 py-1 rounded-full ${config.bgColor}`}>
          <Text className={`text-sm font-medium ${config.color}`}>
            {config.icon} {config.label}
          </Text>
        </View>
      </View>

      {/* Progress Circle with Stats */}
      <View className="items-center mb-6">
        <View className="relative">
          <ProgressCircle progress={progress} color={config.ringColor} size={140} />
          <View className="absolute inset-0 items-center justify-center">
            <Text className="text-3xl font-bold text-textPrimary">{progress}%</Text>
            <Text className="text-xs text-textSecondary">Complete</Text>
          </View>
        </View>
      </View>

      {/* Metrics Grid */}
      <View className="flex-row flex-wrap gap-3">
        {/* Iterations */}
        <View className="flex-1 min-w-[45%] bg-surfaceLight rounded-xl p-3">
          <Text className="text-xs text-textSecondary mb-1">Iterations</Text>
          <Text className="text-lg font-semibold text-textPrimary">
            {iterations_completed}
            <Text className="text-textSecondary font-normal">
              {' '}
              / {iterations_total}
            </Text>
          </Text>
        </View>

        {/* Duration */}
        <View className="flex-1 min-w-[45%] bg-surfaceLight rounded-xl p-3">
          <Text className="text-xs text-textSecondary mb-1">Duration</Text>
          <Text className="text-lg font-semibold text-textPrimary">
            {formatDuration(duration_seconds)}
          </Text>
        </View>

        {/* Tokens */}
        <View className="flex-1 min-w-[45%] bg-surfaceLight rounded-xl p-3">
          <Text className="text-xs text-textSecondary mb-1">Tokens Used</Text>
          <Text className="text-lg font-semibold text-textPrimary">
            {tokens_used.toLocaleString()}
          </Text>
        </View>

        {/* ETA */}
        <View className="flex-1 min-w-[45%] bg-surfaceLight rounded-xl p-3">
          <Text className="text-xs text-textSecondary mb-1">
            {orchestrator.status === 'running' ? 'ETA' : 'Status'}
          </Text>
          <Text className="text-lg font-semibold text-textPrimary">
            {orchestrator.status === 'running' && eta
              ? eta
              : orchestrator.status === 'completed'
              ? '✓ Done'
              : orchestrator.status === 'failed'
              ? '✕ Error'
              : orchestrator.status === 'paused'
              ? '⏸ Paused'
              : '...'}
          </Text>
        </View>
      </View>

      {/* Error message if failed */}
      {orchestrator.status === 'failed' && orchestrator.error && (
        <View className="mt-4 bg-red-500/10 rounded-xl p-3">
          <Text className="text-xs text-red-400 font-medium mb-1">Error</Text>
          <Text className="text-sm text-red-300" numberOfLines={3}>
            {orchestrator.error}
          </Text>
        </View>
      )}
    </View>
  );
}

export default CurrentStatus;
