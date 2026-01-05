/**
 * ControlButtons - Action button group for orchestrator control
 *
 * Displays context-aware buttons based on orchestrator status:
 * - Start: when stopped/none
 * - Pause: when running
 * - Resume: when paused
 * - Stop: when running/paused
 *
 * All destructive actions require confirmation dialogs.
 * Haptic feedback on button press.
 */

import React, { useCallback } from 'react';
import { View, Text, Pressable, Alert, ActivityIndicator } from 'react-native';
import * as Haptics from 'expo-haptics';
import type { OrchestratorStatus } from '../../lib/types';

interface ControlButtonsProps {
  /** Current orchestrator status, or null if none selected */
  status: OrchestratorStatus | null;
  /** Whether any action is currently in progress */
  isLoading: boolean;
  /** Called when start action triggered */
  onStart: () => void;
  /** Called when stop action confirmed */
  onStop: () => void;
  /** Called when pause action triggered */
  onPause: () => void;
  /** Called when resume action triggered */
  onResume: () => void;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
}

/** Button configuration type */
interface ButtonConfig {
  label: string;
  icon: string;
  bgColor: string;
  textColor: string;
  onPress: () => void;
  requiresConfirmation: boolean;
  confirmTitle?: string;
  confirmMessage?: string;
}

/**
 * ControlButtons component
 */
export function ControlButtons({
  status,
  isLoading,
  onStart,
  onStop,
  onPause,
  onResume,
  hapticEnabled = true,
}: ControlButtonsProps): React.JSX.Element {
  /** Trigger haptic feedback */
  const triggerHaptic = useCallback(
    (type: 'light' | 'medium' | 'heavy' = 'medium') => {
      if (!hapticEnabled) return;
      switch (type) {
        case 'light':
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'medium':
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'heavy':
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          break;
      }
    },
    [hapticEnabled]
  );

  /** Handle button press with optional confirmation */
  const handlePress = useCallback(
    (config: ButtonConfig) => {
      triggerHaptic('light');

      if (config.requiresConfirmation) {
        Alert.alert(
          config.confirmTitle ?? 'Confirm Action',
          config.confirmMessage ?? 'Are you sure you want to proceed?',
          [
            {
              text: 'Cancel',
              style: 'cancel',
            },
            {
              text: 'Confirm',
              style: 'destructive',
              onPress: () => {
                triggerHaptic('heavy');
                config.onPress();
              },
            },
          ]
        );
      } else {
        config.onPress();
      }
    },
    [triggerHaptic]
  );

  /** Get available buttons based on current status */
  const getButtons = (): ButtonConfig[] => {
    const buttons: ButtonConfig[] = [];

    // No orchestrator or completed/failed: show Start only
    if (!status || status === 'completed' || status === 'failed') {
      buttons.push({
        label: 'Start New',
        icon: '▶',
        bgColor: 'bg-green-600',
        textColor: 'text-white',
        onPress: onStart,
        requiresConfirmation: false,
      });
      return buttons;
    }

    // Pending: show Start
    if (status === 'pending') {
      buttons.push({
        label: 'Start',
        icon: '▶',
        bgColor: 'bg-green-600',
        textColor: 'text-white',
        onPress: onStart,
        requiresConfirmation: false,
      });
    }

    // Running: show Pause and Stop
    if (status === 'running') {
      buttons.push({
        label: 'Pause',
        icon: '⏸',
        bgColor: 'bg-yellow-600',
        textColor: 'text-white',
        onPress: onPause,
        requiresConfirmation: false,
      });
      buttons.push({
        label: 'Stop',
        icon: '⏹',
        bgColor: 'bg-red-600',
        textColor: 'text-white',
        onPress: onStop,
        requiresConfirmation: true,
        confirmTitle: 'Stop Orchestration?',
        confirmMessage:
          'This will stop the current orchestration. Any in-progress work will be lost.',
      });
    }

    // Paused: show Resume and Stop
    if (status === 'paused') {
      buttons.push({
        label: 'Resume',
        icon: '▶',
        bgColor: 'bg-green-600',
        textColor: 'text-white',
        onPress: onResume,
        requiresConfirmation: false,
      });
      buttons.push({
        label: 'Stop',
        icon: '⏹',
        bgColor: 'bg-red-600',
        textColor: 'text-white',
        onPress: onStop,
        requiresConfirmation: true,
        confirmTitle: 'Stop Orchestration?',
        confirmMessage:
          'This will stop the paused orchestration. Any completed work will be preserved.',
      });
    }

    return buttons;
  };

  const buttons = getButtons();

  return (
    <View className="flex-row gap-3">
      {buttons.map((button, index) => (
        <Pressable
          key={button.label}
          className={`flex-1 flex-row items-center justify-center py-4 px-6 rounded-xl ${button.bgColor} ${
            isLoading ? 'opacity-50' : 'active:opacity-80'
          }`}
          onPress={() => handlePress(button)}
          disabled={isLoading}
          style={{
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.15,
            shadowRadius: 4,
            elevation: 3,
          }}
        >
          {isLoading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <>
              <Text className={`text-lg mr-2 ${button.textColor}`}>{button.icon}</Text>
              <Text className={`font-semibold text-base ${button.textColor}`}>
                {button.label}
              </Text>
            </>
          )}
        </Pressable>
      ))}

      {buttons.length === 0 && (
        <View className="flex-1 py-4 px-6 rounded-xl bg-surfaceLight items-center justify-center">
          <Text className="text-textSecondary text-base">No actions available</Text>
        </View>
      )}
    </View>
  );
}

export default ControlButtons;
