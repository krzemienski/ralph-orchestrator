/**
 * CurrentStatus Component
 *
 * Displays the current orchestrator status with:
 * - Large status indicator
 * - Progress ring/bar
 * - ETA calculation based on iteration rate
 * - Key metrics summary
 */

import React, { useMemo } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { StatusBadge } from '../ui/StatusBadge';
import type { Orchestrator, OrchestratorStatus } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
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
  gray600: '#4b5563',
};

interface CurrentStatusProps {
  /** Current orchestrator (or undefined if none) */
  orchestrator?: Orchestrator;
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
  return num.toString();
}

/**
 * Calculate ETA based on iteration rate
 */
function calculateETA(
  completed: number,
  total: number,
  durationSeconds: number
): string {
  if (completed === 0 || total === 0 || completed >= total) {
    return '--';
  }

  const iterationRate = durationSeconds / completed;
  const remainingIterations = total - completed;
  const estimatedSeconds = remainingIterations * iterationRate;

  return formatDuration(estimatedSeconds);
}

/**
 * Get status-specific message
 */
function getStatusMessage(status: OrchestratorStatus): string {
  switch (status) {
    case 'pending':
      return 'Preparing to start...';
    case 'running':
      return 'Processing iterations';
    case 'paused':
      return 'Orchestration paused';
    case 'completed':
      return 'Successfully completed';
    case 'failed':
      return 'Orchestration failed';
    default:
      return 'Unknown status';
  }
}

/**
 * CurrentStatus - Active orchestrator display
 *
 * Shows:
 * - Large status indicator with pulse for running
 * - Progress bar with percentage
 * - ETA calculation
 * - Key metrics (iterations, tokens, duration)
 */
export function CurrentStatus({
  orchestrator,
}: CurrentStatusProps): React.ReactElement {
  // Animation for pulse effect
  const pulseAnim = React.useRef(new Animated.Value(1)).current;

  React.useEffect(() => {
    if (orchestrator?.status === 'running') {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      return () => {
        pulse.stop();
        pulseAnim.setValue(1);
      };
    } else {
      pulseAnim.setValue(1);
    }
  }, [orchestrator?.status, pulseAnim]);

  // Calculate progress percentage
  const progress = useMemo(() => {
    if (!orchestrator?.metrics) return 0;
    const { iterations_completed, iterations_total } = orchestrator.metrics;
    if (iterations_total === 0) return 0;
    return Math.round((iterations_completed / iterations_total) * 100);
  }, [orchestrator?.metrics]);

  // Calculate ETA
  const eta = useMemo(() => {
    if (!orchestrator?.metrics) return '--';
    const { iterations_completed, iterations_total, duration_seconds } =
      orchestrator.metrics;
    return calculateETA(iterations_completed, iterations_total, duration_seconds);
  }, [orchestrator?.metrics]);

  // No orchestrator selected
  if (!orchestrator) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Current Status</Text>
        <View style={styles.emptyState}>
          <View style={styles.emptyDot} />
          <Text style={styles.emptyText}>No active orchestration</Text>
          <Text style={styles.emptySubtext}>
            Start a new orchestration to see status here
          </Text>
        </View>
      </View>
    );
  }

  const { metrics, status, name, error } = orchestrator;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Current Status</Text>

      {/* Status header with badge */}
      <View style={styles.statusHeader}>
        <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
          <StatusBadge status={status} size="large" />
        </Animated.View>
        <Text style={styles.statusMessage}>{getStatusMessage(status)}</Text>
      </View>

      {/* Orchestrator name */}
      <Text style={styles.orchestratorName} numberOfLines={1}>
        {name}
      </Text>

      {/* Progress bar */}
      <View style={styles.progressSection}>
        <View style={styles.progressHeader}>
          <Text style={styles.progressLabel}>Progress</Text>
          <Text style={styles.progressPercent}>{progress}%</Text>
        </View>
        <View style={styles.progressBarContainer}>
          <View
            style={[
              styles.progressBar,
              {
                width: `${progress}%`,
                backgroundColor:
                  status === 'failed' ? colors.error : colors.info,
              },
            ]}
          />
        </View>
        <View style={styles.progressFooter}>
          <Text style={styles.iterationsText}>
            {metrics.iterations_completed} / {metrics.iterations_total} iterations
          </Text>
          {status === 'running' && (
            <Text style={styles.etaText}>ETA: {eta}</Text>
          )}
        </View>
      </View>

      {/* Metrics grid */}
      <View style={styles.metricsGrid}>
        <View style={styles.metricItem}>
          <Text style={styles.metricValue}>
            {formatNumber(metrics.tokens_used)}
          </Text>
          <Text style={styles.metricLabel}>Tokens</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricValue}>
            {formatDuration(metrics.duration_seconds)}
          </Text>
          <Text style={styles.metricLabel}>Duration</Text>
        </View>
        <View style={styles.metricItem}>
          <Text style={styles.metricValue}>
            {Math.round(metrics.success_rate * 100)}%
          </Text>
          <Text style={styles.metricLabel}>Success</Text>
        </View>
      </View>

      {/* Error message if failed */}
      {status === 'failed' && error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Error</Text>
          <Text style={styles.errorText} numberOfLines={3}>
            {error}
          </Text>
        </View>
      )}
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
    fontWeight: '600',
    fontSize: 16,
    marginBottom: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  emptyDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: colors.gray500,
    marginBottom: 12,
  },
  emptyText: {
    color: colors.gray400,
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 4,
  },
  emptySubtext: {
    color: colors.gray500,
    fontSize: 13,
  },
  statusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  statusMessage: {
    color: colors.gray400,
    fontSize: 14,
    flex: 1,
  },
  orchestratorName: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  progressSection: {
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressLabel: {
    color: colors.gray400,
    fontSize: 13,
  },
  progressPercent: {
    color: colors.white,
    fontSize: 13,
    fontWeight: '600',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: colors.surfaceLight,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 4,
  },
  progressFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  iterationsText: {
    color: colors.gray500,
    fontSize: 12,
  },
  etaText: {
    color: colors.info,
    fontSize: 12,
    fontWeight: '500',
  },
  metricsGrid: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 16,
  },
  metricItem: {
    flex: 1,
    alignItems: 'center',
  },
  metricValue: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  metricLabel: {
    color: colors.gray500,
    fontSize: 12,
  },
  errorContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: colors.error + '15',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.error + '30',
  },
  errorTitle: {
    color: colors.error,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  errorText: {
    color: colors.gray400,
    fontSize: 12,
    lineHeight: 18,
  },
});

export default CurrentStatus;
