/**
 * ControlButtons Component
 *
 * Action button group for orchestrator control:
 * Start, Pause, Resume, Stop
 *
 * Features:
 * - Context-aware button visibility based on current orchestrator state
 * - Haptic feedback on button press
 * - Loading states during API calls
 * - Confirmation dialogs for destructive actions
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import type { OrchestratorStatus } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  success: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  black: '#000000',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  gray600: '#4b5563',
  gray700: '#374151',
};

interface ControlButtonsProps {
  /** Current orchestrator status (or undefined if none selected) */
  currentStatus?: OrchestratorStatus;
  /** ID of the currently selected orchestrator */
  orchestratorId?: string;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
  /** Callback when start is triggered */
  onStart: () => void;
  /** Callback when pause is triggered */
  onPause: (id: string) => void;
  /** Callback when resume is triggered */
  onResume: (id: string) => void;
  /** Callback when stop is triggered */
  onStop: (id: string) => void;
  /** Whether any action is in progress */
  isLoading?: boolean;
}

/**
 * ControlButtons - Action button group for orchestrator control
 *
 * Displays contextually appropriate buttons based on orchestrator state:
 * - No orchestrator: Start only
 * - Running: Pause, Stop
 * - Paused: Resume, Stop
 * - Completed/Failed: Start new
 * - Pending: Stop
 */
export function ControlButtons({
  currentStatus,
  orchestratorId,
  hapticEnabled = true,
  onStart,
  onPause,
  onResume,
  onStop,
  isLoading = false,
}: ControlButtonsProps): React.ReactElement {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  /**
   * Trigger haptic feedback
   */
  const triggerHaptic = useCallback(
    async (type: 'success' | 'warning' | 'error') => {
      if (!hapticEnabled) return;

      try {
        switch (type) {
          case 'success':
            await Haptics.notificationAsync(
              Haptics.NotificationFeedbackType.Success
            );
            break;
          case 'warning':
            await Haptics.notificationAsync(
              Haptics.NotificationFeedbackType.Warning
            );
            break;
          case 'error':
            await Haptics.notificationAsync(
              Haptics.NotificationFeedbackType.Error
            );
            break;
        }
      } catch {
        // Haptics not available on this device
      }
    },
    [hapticEnabled]
  );

  /**
   * Handle Start action
   */
  const handleStart = useCallback(() => {
    triggerHaptic('success');
    setLoadingAction('start');
    onStart();
    // Loading state will be cleared by parent component
  }, [onStart, triggerHaptic]);

  /**
   * Handle Pause action
   */
  const handlePause = useCallback(() => {
    if (!orchestratorId) return;
    triggerHaptic('warning');
    setLoadingAction('pause');
    onPause(orchestratorId);
  }, [orchestratorId, onPause, triggerHaptic]);

  /**
   * Handle Resume action
   */
  const handleResume = useCallback(() => {
    if (!orchestratorId) return;
    triggerHaptic('success');
    setLoadingAction('resume');
    onResume(orchestratorId);
  }, [orchestratorId, onResume, triggerHaptic]);

  /**
   * Handle Stop action with confirmation
   */
  const handleStop = useCallback(() => {
    if (!orchestratorId) return;

    Alert.alert(
      'Stop Orchestration',
      'Are you sure you want to stop this orchestration? This action cannot be undone.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Stop',
          style: 'destructive',
          onPress: () => {
            triggerHaptic('error');
            setLoadingAction('stop');
            onStop(orchestratorId);
          },
        },
      ]
    );
  }, [orchestratorId, onStop, triggerHaptic]);

  // Clear loading state when isLoading prop changes to false
  React.useEffect(() => {
    if (!isLoading) {
      setLoadingAction(null);
    }
  }, [isLoading]);

  /**
   * Determine which buttons to show based on current status
   */
  const showStart = !currentStatus || currentStatus === 'completed' || currentStatus === 'failed';
  const showPause = currentStatus === 'running';
  const showResume = currentStatus === 'paused';
  const showStop = currentStatus === 'running' || currentStatus === 'paused' || currentStatus === 'pending';

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Quick Actions</Text>

      {/* Primary actions row */}
      <View style={styles.buttonRow}>
        {showStart && (
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.startButton,
              pressed && styles.buttonPressed,
              isLoading && styles.buttonDisabled,
            ]}
            onPress={handleStart}
            disabled={isLoading}
            accessibilityLabel="Start new orchestration"
            accessibilityRole="button"
          >
            {loadingAction === 'start' ? (
              <ActivityIndicator size="small" color={colors.white} />
            ) : (
              <Text style={styles.buttonText}>Start New</Text>
            )}
          </Pressable>
        )}

        {showPause && (
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.pauseButton,
              pressed && styles.buttonPressed,
              isLoading && styles.buttonDisabled,
            ]}
            onPress={handlePause}
            disabled={isLoading}
            accessibilityLabel="Pause orchestration"
            accessibilityRole="button"
          >
            {loadingAction === 'pause' ? (
              <ActivityIndicator size="small" color={colors.black} />
            ) : (
              <Text style={[styles.buttonText, styles.darkText]}>Pause</Text>
            )}
          </Pressable>
        )}

        {showResume && (
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.resumeButton,
              pressed && styles.buttonPressed,
              isLoading && styles.buttonDisabled,
            ]}
            onPress={handleResume}
            disabled={isLoading}
            accessibilityLabel="Resume orchestration"
            accessibilityRole="button"
          >
            {loadingAction === 'resume' ? (
              <ActivityIndicator size="small" color={colors.white} />
            ) : (
              <Text style={styles.buttonText}>Resume</Text>
            )}
          </Pressable>
        )}
      </View>

      {/* Stop button row (when applicable) */}
      {showStop && (
        <View style={styles.buttonRow}>
          <Pressable
            style={({ pressed }) => [
              styles.button,
              styles.stopButton,
              styles.fullWidth,
              pressed && styles.buttonPressed,
              isLoading && styles.buttonDisabled,
            ]}
            onPress={handleStop}
            disabled={isLoading}
            accessibilityLabel="Stop orchestration"
            accessibilityRole="button"
          >
            {loadingAction === 'stop' ? (
              <ActivityIndicator size="small" color={colors.white} />
            ) : (
              <Text style={styles.buttonText}>Stop Orchestration</Text>
            )}
          </Pressable>
        </View>
      )}

      {/* No actions available message */}
      {!showStart && !showPause && !showResume && !showStop && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No actions available</Text>
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
  buttonRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  button: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  fullWidth: {
    flex: 1,
  },
  startButton: {
    backgroundColor: colors.success,
  },
  pauseButton: {
    backgroundColor: colors.warning,
  },
  resumeButton: {
    backgroundColor: colors.info,
  },
  stopButton: {
    backgroundColor: colors.error,
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 15,
  },
  darkText: {
    color: colors.black,
  },
  emptyState: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  emptyText: {
    color: colors.gray500,
    fontSize: 14,
  },
});

export default ControlButtons;
