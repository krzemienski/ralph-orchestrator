/**
 * Header Component
 *
 * Orchestrator detail header with:
 * - Name and ID display
 * - Large status badge
 * - Created timestamp
 * - Quick action buttons (stop/pause/resume)
 */

import React, { useCallback } from 'react';
import { View, Text, Pressable, StyleSheet, Alert } from 'react-native';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
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
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

interface HeaderProps {
  /** Orchestrator data */
  orchestrator: Orchestrator;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
  /** Callback when pause is pressed */
  onPause?: (id: string) => void;
  /** Callback when resume is pressed */
  onResume?: (id: string) => void;
  /** Callback when stop is pressed */
  onStop?: (id: string) => void;
  /** Whether any action is loading */
  isLoading?: boolean;
}

/**
 * Format date to human-readable string
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) {
    return 'Just now';
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

/**
 * Header - Orchestrator detail header
 *
 * Shows:
 * - Back navigation
 * - Orchestrator name and ID
 * - Large status badge
 * - Created timestamp
 * - Quick action buttons
 */
export function Header({
  orchestrator,
  hapticEnabled = true,
  onPause,
  onResume,
  onStop,
  isLoading = false,
}: HeaderProps): React.ReactElement {
  const { id, name, status, created_at } = orchestrator;

  /**
   * Trigger haptic feedback
   */
  const triggerHaptic = useCallback(async () => {
    if (hapticEnabled) {
      try {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      } catch {
        // Haptics not available
      }
    }
  }, [hapticEnabled]);

  /**
   * Handle back navigation
   */
  const handleBack = useCallback(async () => {
    await triggerHaptic();
    router.back();
  }, [triggerHaptic]);

  /**
   * Handle pause action
   */
  const handlePause = useCallback(async () => {
    await triggerHaptic();
    onPause?.(id);
  }, [id, onPause, triggerHaptic]);

  /**
   * Handle resume action
   */
  const handleResume = useCallback(async () => {
    await triggerHaptic();
    onResume?.(id);
  }, [id, onResume, triggerHaptic]);

  /**
   * Handle stop action with confirmation
   */
  const handleStop = useCallback(async () => {
    await triggerHaptic();
    Alert.alert(
      'Stop Orchestration',
      'Are you sure you want to stop this orchestration? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stop',
          style: 'destructive',
          onPress: () => onStop?.(id),
        },
      ]
    );
  }, [id, onStop, triggerHaptic]);

  /**
   * Check if an action is available based on status
   */
  const canPause = status === 'running';
  const canResume = status === 'paused';
  const canStop = status === 'running' || status === 'paused';

  return (
    <View style={styles.container}>
      {/* Back button row */}
      <Pressable
        style={({ pressed }) => [
          styles.backButton,
          pressed && styles.backButtonPressed,
        ]}
        onPress={handleBack}
        accessibilityLabel="Go back"
        accessibilityRole="button"
      >
        <Text style={styles.backIcon}>←</Text>
        <Text style={styles.backText}>Back</Text>
      </Pressable>

      {/* Main header content */}
      <View style={styles.content}>
        {/* Name and status */}
        <View style={styles.titleRow}>
          <Text style={styles.name} numberOfLines={2}>
            {name}
          </Text>
          <StatusBadge status={status} size="large" />
        </View>

        {/* ID and timestamp */}
        <View style={styles.metaRow}>
          <Text style={styles.idText} numberOfLines={1}>
            ID: {id.slice(0, 8)}...
          </Text>
          <Text style={styles.timestamp}>Created {formatDate(created_at)}</Text>
        </View>

        {/* Quick action buttons */}
        {canStop && (
          <View style={styles.actions}>
            {canPause && (
              <Pressable
                style={({ pressed }) => [
                  styles.actionButton,
                  styles.pauseButton,
                  pressed && styles.actionButtonPressed,
                  isLoading && styles.actionButtonDisabled,
                ]}
                onPress={handlePause}
                disabled={isLoading}
                accessibilityLabel="Pause orchestration"
                accessibilityRole="button"
              >
                <Text style={styles.actionButtonText}>Pause</Text>
              </Pressable>
            )}

            {canResume && (
              <Pressable
                style={({ pressed }) => [
                  styles.actionButton,
                  styles.resumeButton,
                  pressed && styles.actionButtonPressed,
                  isLoading && styles.actionButtonDisabled,
                ]}
                onPress={handleResume}
                disabled={isLoading}
                accessibilityLabel="Resume orchestration"
                accessibilityRole="button"
              >
                <Text style={styles.actionButtonText}>Resume</Text>
              </Pressable>
            )}

            <Pressable
              style={({ pressed }) => [
                styles.actionButton,
                styles.stopButton,
                pressed && styles.actionButtonPressed,
                isLoading && styles.actionButtonDisabled,
              ]}
              onPress={handleStop}
              disabled={isLoading}
              accessibilityLabel="Stop orchestration"
              accessibilityRole="button"
            >
              <Text style={styles.actionButtonText}>Stop</Text>
            </Pressable>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButtonPressed: {
    backgroundColor: colors.surfaceLight,
  },
  backIcon: {
    color: colors.info,
    fontSize: 18,
    marginRight: 6,
  },
  backText: {
    color: colors.info,
    fontSize: 15,
    fontWeight: '500',
  },
  content: {
    padding: 16,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
    gap: 12,
  },
  name: {
    flex: 1,
    color: colors.white,
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 26,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  idText: {
    color: colors.gray500,
    fontSize: 12,
    fontFamily: 'monospace',
  },
  timestamp: {
    color: colors.gray400,
    fontSize: 12,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  actionButtonDisabled: {
    opacity: 0.5,
  },
  pauseButton: {
    backgroundColor: colors.warning,
  },
  resumeButton: {
    backgroundColor: colors.success,
  },
  stopButton: {
    backgroundColor: colors.error,
  },
  actionButtonText: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
});

export default Header;
