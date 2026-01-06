/**
 * OrchestratorCard Component
 *
 * Card displaying orchestrator summary with status badge,
 * progress indicator, and key metrics. Tappable to navigate
 * to detail view.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  AccessibilityInfo,
} from 'react-native';
import { useRouter } from 'expo-router';
import type { Orchestrator } from '../../lib/types';
import { StatusBadge } from '../ui/StatusBadge';

interface OrchestratorCardProps {
  /** Orchestrator data to display */
  orchestrator: Orchestrator;
  /** Optional callback when card is pressed (overrides default navigation) */
  onPress?: (orchestrator: Orchestrator) => void;
}

/**
 * Format token count with K/M suffix
 */
function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(1)}K`;
  }
  return tokens.toString();
}

/**
 * Format duration in human-readable form
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m ${seconds % 60}s`;
  }
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

/**
 * Calculate progress percentage (0-100)
 */
function calculateProgress(completed: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}

/**
 * Theme colors for dark mode
 */
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceHover: '#252525',
  border: '#333333',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  info: '#3b82f6',
  infoDim: '#3b82f620',
};

/**
 * OrchestratorCard - Displays orchestrator summary in a tappable card
 *
 * Features:
 * - Status badge with color-coded indicator
 * - Progress bar showing iteration completion
 * - Key metrics: iterations, tokens, duration
 * - Press feedback with color change
 * - Navigates to detail view on tap
 */
export function OrchestratorCard({
  orchestrator,
  onPress,
}: OrchestratorCardProps): React.ReactElement {
  const router = useRouter();

  const progress = calculateProgress(
    orchestrator.metrics.iterations_completed,
    orchestrator.metrics.iterations_total
  );

  const handlePress = () => {
    if (onPress) {
      onPress(orchestrator);
    } else {
      // Navigate to detail view
      router.push(`/orchestrator/${orchestrator.id}`);
    }
  };

  // Accessibility label for screen readers
  const accessibilityLabel = `${orchestrator.name}, ${orchestrator.status}, ${progress}% complete, ${formatTokens(orchestrator.metrics.tokens_used)} tokens used`;

  return (
    <Pressable
      onPress={handlePress}
      style={({ pressed }) => [
        styles.card,
        pressed && styles.cardPressed,
      ]}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint="Double tap to view details"
    >
      {/* Header: Name and Status Badge */}
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text
            style={styles.name}
            numberOfLines={1}
            ellipsizeMode="tail"
          >
            {orchestrator.name}
          </Text>
          <Text style={styles.id}>#{orchestrator.id.slice(0, 8)}</Text>
        </View>
        <StatusBadge status={orchestrator.status} size="small" />
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressTrack}>
          <View
            style={[
              styles.progressFill,
              { width: `${progress}%` },
            ]}
          />
        </View>
        <Text style={styles.progressText}>{progress}%</Text>
      </View>

      {/* Metrics Row */}
      <View style={styles.metricsRow}>
        <MetricItem
          label="Iterations"
          value={`${orchestrator.metrics.iterations_completed}/${orchestrator.metrics.iterations_total}`}
        />
        <MetricItem
          label="Tokens"
          value={formatTokens(orchestrator.metrics.tokens_used)}
        />
        <MetricItem
          label="Duration"
          value={formatDuration(orchestrator.metrics.duration_seconds)}
        />
      </View>

      {/* Error Message (if failed) */}
      {orchestrator.error && orchestrator.status === 'failed' && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText} numberOfLines={2}>
            {orchestrator.error}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

/**
 * MetricItem - Single metric display helper
 */
interface MetricItemProps {
  label: string;
  value: string;
}

function MetricItem({ label, value }: MetricItemProps): React.ReactElement {
  return (
    <View style={styles.metricItem}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardPressed: {
    backgroundColor: colors.surfaceHover,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  titleContainer: {
    flex: 1,
    marginRight: 12,
  },
  name: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  id: {
    color: colors.gray500,
    fontSize: 12,
    fontFamily: 'monospace',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  progressTrack: {
    flex: 1,
    height: 6,
    backgroundColor: colors.infoDim,
    borderRadius: 3,
    overflow: 'hidden',
    marginRight: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.info,
    borderRadius: 3,
  },
  progressText: {
    color: colors.gray400,
    fontSize: 12,
    fontWeight: '500',
    minWidth: 35,
    textAlign: 'right',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricItem: {
    alignItems: 'center',
    flex: 1,
  },
  metricValue: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  metricLabel: {
    color: colors.gray500,
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  errorContainer: {
    marginTop: 12,
    padding: 8,
    backgroundColor: '#ef444420',
    borderRadius: 8,
  },
  errorText: {
    color: '#ef4444',
    fontSize: 12,
  },
});

export default OrchestratorCard;
