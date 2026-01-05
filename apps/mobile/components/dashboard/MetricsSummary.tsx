/**
 * MetricsSummary - Compact metrics display for orchestrator cards
 *
 * Shows key metrics: iterations, tokens used, and duration.
 */

import React from 'react';
import { View, Text } from 'react-native';
import type { OrchestratorMetrics } from '../../lib/types';

interface MetricsSummaryProps {
  /** Metrics data to display */
  metrics: OrchestratorMetrics;
}

/**
 * Format number with K/M suffix
 */
function formatNumber(num: number): string {
  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(1)}M`;
  }
  if (num >= 1_000) {
    return `${(num / 1_000).toFixed(1)}K`;
  }
  return num.toString();
}

/**
 * Format duration to human-readable string
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

/**
 * Individual metric item component
 */
function MetricItem({
  label,
  value,
}: {
  label: string;
  value: string;
}): React.JSX.Element {
  return (
    <View className="items-center">
      <Text className="text-xs text-textSecondary mb-0.5">{label}</Text>
      <Text className="text-sm font-semibold text-textPrimary">{value}</Text>
    </View>
  );
}

/**
 * MetricsSummary component
 */
export function MetricsSummary({ metrics }: MetricsSummaryProps): React.JSX.Element {
  const iterationText = `${metrics.iterations_completed}/${metrics.iterations_total}`;
  const tokenText = formatNumber(metrics.tokens_used);
  const durationText = formatDuration(metrics.duration_seconds);

  return (
    <View className="flex-row justify-around py-2">
      <MetricItem label="Iterations" value={iterationText} />
      <View className="w-px bg-border" />
      <MetricItem label="Tokens" value={tokenText} />
      <View className="w-px bg-border" />
      <MetricItem label="Duration" value={durationText} />
    </View>
  );
}

export default MetricsSummary;
