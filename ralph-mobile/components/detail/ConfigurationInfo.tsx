/**
 * ConfigurationInfo Component
 *
 * Display orchestrator configuration:
 * - Model selection
 * - Max iterations
 * - Timeout settings
 * - Prompt/task description
 * - Created/Updated timestamps
 */

import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import * as Haptics from 'expo-haptics';
import type { OrchestratorConfig } from '../../lib/types';

// Theme colors
const colors = {
  surface: '#1a1a1a',
  surfaceLight: '#262626',
  border: '#333333',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  info: '#3b82f6',
};

interface ConfigurationInfoProps {
  /** Orchestrator configuration */
  config: OrchestratorConfig;
  /** Created timestamp */
  createdAt: string;
  /** Updated timestamp */
  updatedAt: string;
  /** Enable haptic feedback */
  hapticEnabled?: boolean;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format timeout duration
 */
function formatTimeout(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} seconds`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

/**
 * Configuration row item
 */
interface ConfigRowProps {
  label: string;
  value: string | number;
}

function ConfigRow({ label, value }: ConfigRowProps): React.ReactElement {
  return (
    <View style={styles.configRow}>
      <Text style={styles.configLabel}>{label}</Text>
      <Text style={styles.configValue}>{value}</Text>
    </View>
  );
}

/**
 * ConfigurationInfo - Orchestrator configuration display
 *
 * Shows all configuration settings in a collapsible format:
 * - Model, iterations, timeout in summary
 * - Prompt text (truncated with expand)
 * - Timestamps at bottom
 */
export function ConfigurationInfo({
  config,
  createdAt,
  updatedAt,
  hapticEnabled = true,
}: ConfigurationInfoProps): React.ReactElement {
  const [isPromptExpanded, setIsPromptExpanded] = useState(false);

  const handleTogglePrompt = useCallback(() => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    setIsPromptExpanded((prev) => !prev);
  }, [hapticEnabled]);

  const promptPreview = config.prompt.length > 100
    ? config.prompt.substring(0, 100) + '...'
    : config.prompt;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Configuration</Text>

      {/* Main configuration */}
      <View style={styles.configGrid}>
        <ConfigRow label="Model" value={config.model} />
        <ConfigRow label="Max Iterations" value={config.max_iterations.toString()} />
        <ConfigRow label="Timeout" value={formatTimeout(config.timeout_seconds)} />
      </View>

      {/* Prompt/Task */}
      <View style={styles.promptSection}>
        <Text style={styles.promptLabel}>Prompt / Task</Text>
        <Pressable
          onPress={handleTogglePrompt}
          style={({ pressed }) => [
            styles.promptContainer,
            pressed && styles.promptContainerPressed,
          ]}
          accessibilityLabel="Orchestration prompt"
          accessibilityHint="Tap to expand or collapse"
        >
          <Text style={styles.promptText} numberOfLines={isPromptExpanded ? undefined : 3}>
            {isPromptExpanded ? config.prompt : promptPreview}
          </Text>
          {config.prompt.length > 100 && (
            <Text style={styles.expandToggle}>
              {isPromptExpanded ? 'Show less' : 'Show more'}
            </Text>
          )}
        </Pressable>
      </View>

      {/* Timestamps */}
      <View style={styles.timestampSection}>
        <View style={styles.timestampRow}>
          <Text style={styles.timestampLabel}>Created</Text>
          <Text style={styles.timestampValue}>{formatTimestamp(createdAt)}</Text>
        </View>
        <View style={styles.timestampRow}>
          <Text style={styles.timestampLabel}>Last Updated</Text>
          <Text style={styles.timestampValue}>{formatTimestamp(updatedAt)}</Text>
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
  configGrid: {
    marginBottom: 16,
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  configLabel: {
    color: colors.gray400,
    fontSize: 14,
  },
  configValue: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '500',
  },
  promptSection: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  promptLabel: {
    color: colors.gray400,
    fontSize: 14,
    marginBottom: 8,
  },
  promptContainer: {
    backgroundColor: colors.surfaceLight,
    padding: 12,
    borderRadius: 8,
  },
  promptContainerPressed: {
    opacity: 0.8,
  },
  promptText: {
    color: colors.white,
    fontSize: 13,
    lineHeight: 20,
  },
  expandToggle: {
    color: colors.info,
    fontSize: 12,
    fontWeight: '500',
    marginTop: 8,
  },
  timestampSection: {
    gap: 8,
  },
  timestampRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timestampLabel: {
    color: colors.gray500,
    fontSize: 12,
  },
  timestampValue: {
    color: colors.gray400,
    fontSize: 12,
  },
});

export default ConfigurationInfo;
