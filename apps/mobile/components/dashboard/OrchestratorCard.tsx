/**
 * OrchestratorCard - Card showing orchestrator summary
 *
 * Displays name, status badge, progress bar, and key metrics.
 * Tap to navigate to detail view.
 */

import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import type { Orchestrator } from '../../lib/types';
import { StatusBadge } from '../ui/StatusBadge';
import { MetricsSummary } from './MetricsSummary';

interface OrchestratorCardProps {
  /** Orchestrator data to display */
  orchestrator: Orchestrator;
}

/**
 * Calculate progress percentage
 */
function getProgressPercent(metrics: Orchestrator['metrics']): number {
  if (metrics.iterations_total === 0) return 0;
  return Math.round((metrics.iterations_completed / metrics.iterations_total) * 100);
}

/**
 * Get progress bar color based on status
 */
function getProgressColor(status: Orchestrator['status']): string {
  const colorMap: Record<Orchestrator['status'], string> = {
    pending: 'bg-gray-500',
    running: 'bg-blue-500',
    paused: 'bg-yellow-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
  };
  return colorMap[status];
}

/**
 * Format relative time
 */
function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  return `${diffDay}d ago`;
}

/**
 * OrchestratorCard component
 */
export function OrchestratorCard({ orchestrator }: OrchestratorCardProps): React.JSX.Element {
  const router = useRouter();
  const progressPercent = getProgressPercent(orchestrator.metrics);
  const progressColor = getProgressColor(orchestrator.status);

  const handlePress = (): void => {
    router.push({
      pathname: '/orchestrator/[id]',
      params: { id: orchestrator.id },
    });
  };

  return (
    <Pressable
      onPress={handlePress}
      className="bg-surface rounded-xl mb-3 overflow-hidden active:opacity-80"
    >
      {/* Header */}
      <View className="p-4">
        <View className="flex-row justify-between items-start mb-2">
          <View className="flex-1 mr-3">
            <Text className="text-lg font-semibold text-textPrimary" numberOfLines={1}>
              {orchestrator.name}
            </Text>
            <Text className="text-xs text-textSecondary mt-0.5">
              Updated {formatRelativeTime(orchestrator.updated_at)}
            </Text>
          </View>
          <StatusBadge status={orchestrator.status} size="small" />
        </View>

        {/* Progress Bar */}
        <View className="h-1.5 bg-border rounded-full overflow-hidden mt-2">
          <View
            className={`h-full ${progressColor} rounded-full`}
            style={{ width: `${progressPercent}%` }}
          />
        </View>
        <Text className="text-xs text-textSecondary mt-1">{progressPercent}% complete</Text>

        {/* Error message if failed */}
        {orchestrator.error && (
          <View className="mt-2 p-2 bg-red-500/10 rounded-lg">
            <Text className="text-xs text-red-400" numberOfLines={2}>
              {orchestrator.error}
            </Text>
          </View>
        )}
      </View>

      {/* Metrics Section */}
      <View className="border-t border-border">
        <MetricsSummary metrics={orchestrator.metrics} />
      </View>
    </Pressable>
  );
}

export default OrchestratorCard;
