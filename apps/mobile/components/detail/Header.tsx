/**
 * Header - Orchestrator detail view header
 *
 * Displays:
 * - Orchestrator name (large title)
 * - ID (truncated, copyable)
 * - Created timestamp (relative)
 * - Large status badge
 * - Quick action buttons (stop/pause/resume)
 */

import React, { useCallback } from 'react';
import { View, Text, Pressable, Alert, ActivityIndicator } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import { StatusBadge } from '../ui/StatusBadge';
import type { Orchestrator, OrchestratorStatus } from '../../lib/types';

interface HeaderProps {
  /** Orchestrator data */
  orchestrator: Orchestrator;
  /** Whether any action is in progress */
  isLoading: boolean;
  /** Called when stop action confirmed */
  onStop: () => void;
  /** Called when pause action triggered */
  onPause: () => void;
  /** Called when resume action triggered */
  onResume: () => void;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
}

/** Format relative time from ISO date string */
function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'just now';
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`;
  }
  return date.toLocaleDateString();
}

/** Truncate ID for display */
function truncateId(id: string): string {
  if (id.length <= 12) return id;
  return `${id.slice(0, 6)}...${id.slice(-4)}`;
}

/**
 * Header component
 */
export function Header({
  orchestrator,
  isLoading,
  onStop,
  onPause,
  onResume,
  hapticEnabled = true,
}: HeaderProps): React.JSX.Element {
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

  /** Copy ID to clipboard */
  const handleCopyId = useCallback(async () => {
    triggerHaptic('light');
    await Clipboard.setStringAsync(orchestrator.id);
    Alert.alert('Copied', 'Orchestrator ID copied to clipboard');
  }, [orchestrator.id, triggerHaptic]);

  /** Handle stop with confirmation */
  const handleStop = useCallback(() => {
    triggerHaptic('light');
    Alert.alert(
      'Stop Orchestration?',
      'This will stop the current orchestration. Any in-progress work will be lost.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Stop',
          style: 'destructive',
          onPress: () => {
            triggerHaptic('heavy');
            onStop();
          },
        },
      ]
    );
  }, [onStop, triggerHaptic]);

  /** Handle pause */
  const handlePause = useCallback(() => {
    triggerHaptic('medium');
    onPause();
  }, [onPause, triggerHaptic]);

  /** Handle resume */
  const handleResume = useCallback(() => {
    triggerHaptic('medium');
    onResume();
  }, [onResume, triggerHaptic]);

  /** Get available quick actions based on status */
  const renderQuickActions = (): React.JSX.Element | null => {
    const { status } = orchestrator;

    // No actions for completed/failed/pending states
    if (status === 'completed' || status === 'failed' || status === 'pending') {
      return null;
    }

    return (
      <View className="flex-row gap-2 mt-4">
        {status === 'running' && (
          <>
            <Pressable
              className={`flex-1 flex-row items-center justify-center py-3 px-4 rounded-xl bg-yellow-600 ${
                isLoading ? 'opacity-50' : 'active:opacity-80'
              }`}
              onPress={handlePause}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Text className="text-white text-base mr-2">⏸</Text>
                  <Text className="text-white font-semibold">Pause</Text>
                </>
              )}
            </Pressable>
            <Pressable
              className={`flex-1 flex-row items-center justify-center py-3 px-4 rounded-xl bg-red-600 ${
                isLoading ? 'opacity-50' : 'active:opacity-80'
              }`}
              onPress={handleStop}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Text className="text-white text-base mr-2">⏹</Text>
                  <Text className="text-white font-semibold">Stop</Text>
                </>
              )}
            </Pressable>
          </>
        )}

        {status === 'paused' && (
          <>
            <Pressable
              className={`flex-1 flex-row items-center justify-center py-3 px-4 rounded-xl bg-green-600 ${
                isLoading ? 'opacity-50' : 'active:opacity-80'
              }`}
              onPress={handleResume}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Text className="text-white text-base mr-2">▶</Text>
                  <Text className="text-white font-semibold">Resume</Text>
                </>
              )}
            </Pressable>
            <Pressable
              className={`flex-1 flex-row items-center justify-center py-3 px-4 rounded-xl bg-red-600 ${
                isLoading ? 'opacity-50' : 'active:opacity-80'
              }`}
              onPress={handleStop}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Text className="text-white text-base mr-2">⏹</Text>
                  <Text className="text-white font-semibold">Stop</Text>
                </>
              )}
            </Pressable>
          </>
        )}
      </View>
    );
  };

  return (
    <View className="bg-surface rounded-2xl p-4">
      {/* Top row: Name and Status Badge */}
      <View className="flex-row items-start justify-between">
        <View className="flex-1 mr-3">
          <Text className="text-xl font-bold text-textPrimary" numberOfLines={2}>
            {orchestrator.name}
          </Text>
        </View>
        <StatusBadge status={orchestrator.status} size="large" />
      </View>

      {/* ID row (tappable to copy) */}
      <Pressable
        className="flex-row items-center mt-2 active:opacity-70"
        onPress={handleCopyId}
      >
        <Text className="text-xs text-textSecondary mr-1">ID:</Text>
        <Text className="text-xs text-textSecondary font-mono">
          {truncateId(orchestrator.id)}
        </Text>
        <Text className="text-xs text-textSecondary ml-1">📋</Text>
      </Pressable>

      {/* Created timestamp */}
      <Text className="text-xs text-textSecondary mt-1">
        Created {formatRelativeTime(orchestrator.created_at)}
      </Text>

      {/* Quick action buttons */}
      {renderQuickActions()}
    </View>
  );
}

export default Header;
