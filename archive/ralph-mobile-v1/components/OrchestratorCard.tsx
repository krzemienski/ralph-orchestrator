/**
 * @fileoverview OrchestratorCard component for displaying orchestrator status
 * Plan 05-01: Orchestrator List View
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { colors, spacing, typography } from '../lib/theme';
import type { Orchestrator } from '../lib/types';
import { getStatusColor, formatElapsedTime, getSuccessRatio } from '../lib/orchestratorHelpers';

interface OrchestratorCardProps {
  orchestrator: Orchestrator;
  onPress?: (orchestrator: Orchestrator) => void;
}

/**
 * Card component displaying orchestrator status and metrics
 */
export default function OrchestratorCard({ orchestrator, onPress }: OrchestratorCardProps) {
  const statusColor = getStatusColor(orchestrator.status);

  return (
    <Pressable
      testID="orchestrator-card"
      style={styles.card}
      onPress={() => onPress?.(orchestrator)}
    >
      <View style={styles.header}>
        <Text style={styles.id}>{orchestrator.id}</Text>
        <View
          testID="status-badge"
          style={[styles.statusBadge, { backgroundColor: statusColor }]}
        >
          <Text style={styles.statusText}>{orchestrator.status}</Text>
        </View>
      </View>

      <Text style={styles.promptFile}>{orchestrator.prompt_file}</Text>

      <View style={styles.metricsRow}>
        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Iteration</Text>
          <Text style={styles.metricValue}>
            {orchestrator.metrics.current_iteration}
          </Text>
        </View>

        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Success</Text>
          <Text style={styles.metricValue}>
            {getSuccessRatio(orchestrator.metrics)}
          </Text>
        </View>

        <View style={styles.metric}>
          <Text style={styles.metricLabel}>Time</Text>
          <Text style={styles.metricValue}>
            {formatElapsedTime(orchestrator.metrics.elapsed_time)}
          </Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  id: {
    fontSize: typography.sizes.lg,
    fontWeight: typography.weights.bold,
    color: colors.text,
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 6,
  },
  statusText: {
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.medium,
    color: colors.text,
  },
  promptFile: {
    fontSize: typography.sizes.md,
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: typography.sizes.sm,
    color: colors.textMuted,
    marginBottom: spacing.xs,
  },
  metricValue: {
    fontSize: typography.sizes.lg,
    fontWeight: typography.weights.medium,
    color: colors.primary,
  },
});
