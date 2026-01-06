/**
 * ProgressSection Component
 *
 * Visual progress indicator for orchestrator:
 * - Circular progress ring showing completion
 * - Current phase/iteration label
 * - ETA calculation based on average iteration time
 */

import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { OrchestratorMetrics, OrchestratorStatus } from '../../lib/types';

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

interface ProgressSectionProps {
  /** Orchestrator metrics */
  metrics: OrchestratorMetrics;
  /** Current status */
  status: OrchestratorStatus;
}

/**
 * Get progress ring color based on status
 */
function getProgressColor(status: OrchestratorStatus): string {
  switch (status) {
    case 'running':
      return colors.info;
    case 'completed':
      return colors.success;
    case 'failed':
      return colors.error;
    case 'paused':
      return colors.warning;
    default:
      return colors.gray500;
  }
}

/**
 * Calculate ETA based on current progress
 */
function calculateETA(
  iterationsCompleted: number,
  iterationsTotal: number,
  durationSeconds: number
): string | null {
  if (iterationsCompleted === 0 || iterationsTotal === 0) {
    return null;
  }

  if (iterationsCompleted >= iterationsTotal) {
    return 'Complete';
  }

  const avgTimePerIteration = durationSeconds / iterationsCompleted;
  const remainingIterations = iterationsTotal - iterationsCompleted;
  const remainingSeconds = avgTimePerIteration * remainingIterations;

  if (remainingSeconds < 60) {
    return `~${Math.round(remainingSeconds)}s remaining`;
  }

  const remainingMinutes = Math.floor(remainingSeconds / 60);
  if (remainingMinutes < 60) {
    return `~${remainingMinutes}m remaining`;
  }

  const remainingHours = Math.floor(remainingMinutes / 60);
  const mins = remainingMinutes % 60;
  return `~${remainingHours}h ${mins}m remaining`;
}

/**
 * Get status message based on current state
 */
function getStatusMessage(status: OrchestratorStatus): string {
  switch (status) {
    case 'pending':
      return 'Waiting to start';
    case 'running':
      return 'Processing...';
    case 'paused':
      return 'Paused';
    case 'completed':
      return 'All iterations complete';
    case 'failed':
      return 'Orchestration failed';
    default:
      return '';
  }
}

/**
 * ProgressSection - Visual progress indicator
 *
 * Displays:
 * - Large circular progress indicator
 * - Percentage complete in center
 * - Current iteration / total
 * - Status message
 * - ETA calculation
 */
export function ProgressSection({ metrics, status }: ProgressSectionProps): React.ReactElement {
  const {
    iterations_completed,
    iterations_total,
    duration_seconds,
  } = metrics;

  const progress = useMemo(() => {
    if (iterations_total === 0) return 0;
    return Math.min(iterations_completed / iterations_total, 1);
  }, [iterations_completed, iterations_total]);

  const percentage = Math.round(progress * 100);
  const progressColor = getProgressColor(status);
  const eta = calculateETA(iterations_completed, iterations_total, duration_seconds);
  const statusMessage = getStatusMessage(status);

  // Calculate stroke dasharray for progress ring
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Progress</Text>

      <View style={styles.content}>
        {/* Progress Ring */}
        <View style={styles.progressRingContainer}>
          {/* Background circle */}
          <View style={styles.progressRingBackground} />

          {/* Progress indicator (simplified without SVG) */}
          <View
            style={[
              styles.progressRingFill,
              {
                borderTopColor: progressColor,
                borderRightColor: progress > 0.25 ? progressColor : colors.surfaceLight,
                borderBottomColor: progress > 0.5 ? progressColor : colors.surfaceLight,
                borderLeftColor: progress > 0.75 ? progressColor : colors.surfaceLight,
                transform: [{ rotate: `${progress * 360}deg` }],
              },
            ]}
          />

          {/* Center content */}
          <View style={styles.progressCenter}>
            <Text style={[styles.percentageText, { color: progressColor }]}>
              {percentage}%
            </Text>
            <Text style={styles.iterationText}>
              {iterations_completed}/{iterations_total}
            </Text>
          </View>
        </View>

        {/* Status and ETA */}
        <View style={styles.statusContainer}>
          <Text style={styles.statusMessage}>{statusMessage}</Text>
          {eta && status === 'running' && (
            <Text style={styles.etaText}>{eta}</Text>
          )}
          {status === 'completed' && (
            <Text style={[styles.etaText, { color: colors.success }]}>
              ✓ Completed successfully
            </Text>
          )}
          {status === 'failed' && (
            <Text style={[styles.etaText, { color: colors.error }]}>
              ✗ Check logs for details
            </Text>
          )}
        </View>
      </View>

      {/* Progress bar (linear alternative) */}
      <View style={styles.linearProgressContainer}>
        <View style={styles.linearProgressBackground}>
          <View
            style={[
              styles.linearProgressFill,
              {
                width: `${percentage}%`,
                backgroundColor: progressColor,
              },
            ]}
          />
        </View>
        <Text style={styles.linearProgressLabel}>
          Iteration {iterations_completed} of {iterations_total}
        </Text>
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
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  progressRingContainer: {
    width: 100,
    height: 100,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 20,
  },
  progressRingBackground: {
    position: 'absolute',
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 8,
    borderColor: colors.surfaceLight,
  },
  progressRingFill: {
    position: 'absolute',
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 8,
  },
  progressCenter: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
  },
  percentageText: {
    fontSize: 24,
    fontWeight: '700',
  },
  iterationText: {
    color: colors.gray400,
    fontSize: 12,
    marginTop: 2,
  },
  statusContainer: {
    flex: 1,
  },
  statusMessage: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  etaText: {
    color: colors.gray400,
    fontSize: 14,
  },
  linearProgressContainer: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  linearProgressBackground: {
    height: 8,
    backgroundColor: colors.surfaceLight,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  linearProgressFill: {
    height: '100%',
    borderRadius: 4,
  },
  linearProgressLabel: {
    color: colors.gray500,
    fontSize: 12,
    textAlign: 'center',
  },
});

export default ProgressSection;
