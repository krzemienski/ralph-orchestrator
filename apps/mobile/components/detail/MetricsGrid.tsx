/**
 * MetricsGrid - Key metrics display for orchestrator detail
 *
 * Displays:
 * - Iterations completed/total
 * - Tokens used (with K/M suffix formatting)
 * - Duration (elapsed time)
 * - Success rate (percentage)
 */

import React from 'react';
import { View, Text } from 'react-native';
import type { OrchestratorMetrics } from '../../lib/types';

interface MetricsGridProps {
  /** Orchestrator metrics data */
  metrics: OrchestratorMetrics;
}

/** Format large numbers with K/M suffix */
function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(1)}K`;
  }
  return tokens.toLocaleString();
}

/** Format duration in seconds to human-readable string */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

/** Format success rate as percentage */
function formatSuccessRate(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

/** Individual metric card */
function MetricCard({
  label,
  value,
  subValue,
  icon,
  color = 'text-textPrimary',
}: {
  label: string;
  value: string;
  subValue?: string;
  icon: string;
  color?: string;
}): React.JSX.Element {
  return (
    <View className="flex-1 min-w-[45%] bg-surfaceLight rounded-xl p-3">
      <View className="flex-row items-center mb-1">
        <Text className="text-base mr-1.5">{icon}</Text>
        <Text className="text-xs text-textSecondary">{label}</Text>
      </View>
      <Text className={`text-xl font-bold ${color}`}>
        {value}
        {subValue && (
          <Text className="text-sm font-normal text-textSecondary"> {subValue}</Text>
        )}
      </Text>
    </View>
  );
}

/**
 * MetricsGrid component
 */
export function MetricsGrid({ metrics }: MetricsGridProps): React.JSX.Element {
  const { iterations_completed, iterations_total, tokens_used, duration_seconds, success_rate } =
    metrics;

  // Calculate progress percentage for color coding
  const progressPercent =
    iterations_total > 0 ? (iterations_completed / iterations_total) * 100 : 0;

  // Determine success rate color
  const getSuccessRateColor = (): string => {
    if (success_rate >= 0.9) return 'text-green-400';
    if (success_rate >= 0.7) return 'text-yellow-400';
    if (success_rate >= 0.5) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <View className="bg-surface rounded-2xl p-4">
      <Text className="text-sm font-medium text-textSecondary mb-3">Metrics</Text>
      <View className="flex-row flex-wrap gap-3">
        {/* Iterations */}
        <MetricCard
          label="Iterations"
          value={iterations_completed.toString()}
          subValue={`/ ${iterations_total}`}
          icon="🔄"
        />

        {/* Tokens Used */}
        <MetricCard
          label="Tokens Used"
          value={formatTokens(tokens_used)}
          icon="🎯"
        />

        {/* Duration */}
        <MetricCard
          label="Duration"
          value={formatDuration(duration_seconds)}
          icon="⏱"
        />

        {/* Success Rate */}
        <MetricCard
          label="Success Rate"
          value={formatSuccessRate(success_rate)}
          icon="✓"
          color={getSuccessRateColor()}
        />
      </View>
    </View>
  );
}

export default MetricsGrid;
