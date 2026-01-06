/**
 * MetricsGrid Component
 *
 * Key performance indicators for an orchestrator:
 * - Iterations: completed / total
 * - Tokens Used: formatted with K/M suffix
 * - Duration: elapsed time
 * - Success Rate: percentage
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { OrchestratorMetrics } from '../../lib/types';

// Theme colors
const colors = {
  surface: '#1a1a1a',
  surfaceLight: '#262626',
  border: '#333333',
  success: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

interface MetricsGridProps {
  /** Orchestrator metrics */
  metrics: OrchestratorMetrics;
}

/**
 * Format duration in seconds to human-readable string
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

/**
 * Format large numbers with K/M suffix
 */
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toLocaleString();
}

/**
 * Get color for success rate
 */
function getSuccessRateColor(rate: number): string {
  if (rate >= 0.9) return colors.success;
  if (rate >= 0.7) return colors.warning;
  return colors.error;
}

/**
 * MetricsGrid - Key performance indicators
 *
 * Displays a 2x2 grid of metrics:
 * - Iterations with progress
 * - Token usage with formatted number
 * - Duration with human-readable time
 * - Success rate with color coding
 */
export function MetricsGrid({ metrics }: MetricsGridProps): React.ReactElement {
  const {
    iterations_completed,
    iterations_total,
    tokens_used,
    duration_seconds,
    success_rate,
  } = metrics;

  const iterationProgress =
    iterations_total > 0
      ? Math.round((iterations_completed / iterations_total) * 100)
      : 0;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Metrics</Text>

      <View style={styles.grid}>
        {/* Iterations */}
        <View
          style={styles.metricCard}
          accessibilityLabel={`Iterations: ${iterations_completed} of ${iterations_total} completed, ${iterationProgress}% progress`}
          accessibilityRole="text"
        >
          <Text style={styles.metricValue}>
            {iterations_completed}
            <Text style={styles.metricTotal}>/{iterations_total}</Text>
          </Text>
          <Text style={styles.metricLabel}>Iterations</Text>
          <View style={styles.progressBarContainer}>
            <View
              style={[
                styles.progressBar,
                {
                  width: `${iterationProgress}%`,
                  backgroundColor: colors.info,
                },
              ]}
            />
          </View>
        </View>

        {/* Tokens */}
        <View
          style={styles.metricCard}
          accessibilityLabel={`Tokens used: ${tokens_used.toLocaleString()}`}
          accessibilityRole="text"
        >
          <Text style={styles.metricValue}>{formatNumber(tokens_used)}</Text>
          <Text style={styles.metricLabel}>Tokens Used</Text>
          <Text style={styles.metricSubtext}>
            {tokens_used.toLocaleString()} total
          </Text>
        </View>

        {/* Duration */}
        <View
          style={styles.metricCard}
          accessibilityLabel={`Duration: ${formatDuration(duration_seconds)}, ${Math.round(duration_seconds)} seconds elapsed`}
          accessibilityRole="text"
        >
          <Text style={styles.metricValue}>
            {formatDuration(duration_seconds)}
          </Text>
          <Text style={styles.metricLabel}>Duration</Text>
          <Text style={styles.metricSubtext}>
            {Math.round(duration_seconds)}s elapsed
          </Text>
        </View>

        {/* Success Rate */}
        <View
          style={styles.metricCard}
          accessibilityLabel={`Success rate: ${Math.round(success_rate * 100)} percent`}
          accessibilityRole="text"
        >
          <Text
            style={[
              styles.metricValue,
              { color: getSuccessRateColor(success_rate) },
            ]}
          >
            {Math.round(success_rate * 100)}%
          </Text>
          <Text style={styles.metricLabel}>Success Rate</Text>
          <View style={styles.progressBarContainer}>
            <View
              style={[
                styles.progressBar,
                {
                  width: `${success_rate * 100}%`,
                  backgroundColor: getSuccessRateColor(success_rate),
                },
              ]}
            />
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -6,
  },
  metricCard: {
    width: '50%',
    paddingHorizontal: 6,
    marginBottom: 16,
  },
  metricValue: {
    color: colors.white,
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 2,
  },
  metricTotal: {
    color: colors.gray500,
    fontSize: 16,
    fontWeight: '500',
  },
  metricLabel: {
    color: colors.gray400,
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 6,
  },
  metricSubtext: {
    color: colors.gray500,
    fontSize: 11,
  },
  progressBarContainer: {
    height: 4,
    backgroundColor: colors.surfaceLight,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 2,
  },
});

export default MetricsGrid;
