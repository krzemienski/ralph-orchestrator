/**
 * About - App information and version display
 *
 * Displays:
 * - App version and build number
 * - Ralph server version (when connected)
 * - Debug options (dev mode only)
 */

import React, { useState, useCallback } from 'react';
import { View, Text, Pressable, Linking, Alert } from 'react-native';
import Constants from 'expo-constants';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useConnection } from '../../lib/hooks/useConnection';

interface AboutProps {
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
  /** Callback when cache is cleared */
  onCacheClear?: () => void;
  /** Callback when settings are reset */
  onSettingsReset?: () => void;
}

/** Info row component */
function InfoRow({
  label,
  value,
  isLink,
  onPress,
}: {
  label: string;
  value: string;
  isLink?: boolean;
  onPress?: () => void;
}): React.JSX.Element {
  const content = (
    <View className="flex-row items-center justify-between py-2">
      <Text className="text-sm text-textSecondary">{label}</Text>
      <Text className={`text-sm ${isLink ? 'text-primary' : 'text-textPrimary'}`}>
        {value}
      </Text>
    </View>
  );

  if (onPress) {
    return (
      <Pressable onPress={onPress} className="active:opacity-70">
        {content}
      </Pressable>
    );
  }

  return content;
}

/**
 * About component
 */
export function About({
  hapticEnabled = true,
  onCacheClear,
  onSettingsReset,
}: AboutProps): React.JSX.Element {
  const { health, isConnected } = useConnection();
  const [showDebug, setShowDebug] = useState(__DEV__);

  // App version info
  const appVersion = Constants.expoConfig?.version || '1.0.0';
  const buildNumber = Constants.expoConfig?.ios?.buildNumber ||
    Constants.expoConfig?.android?.versionCode?.toString() ||
    '1';
  const expoSdkVersion = Constants.expoConfig?.sdkVersion || 'Unknown';

  /** Open Ralph documentation */
  const handleDocsPress = useCallback(async () => {
    if (hapticEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    try {
      await Linking.openURL('https://github.com/ralph-orchestrator/ralph');
    } catch {
      // Silently fail
    }
  }, [hapticEnabled]);

  /** Clear app cache */
  const handleClearCache = useCallback(async () => {
    if (hapticEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }

    Alert.alert(
      'Clear Cache',
      'This will clear all cached data. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              // Clear specific cache keys, not all storage
              const cacheKeys = [
                'ralph_orchestrators_cache',
                'ralph_logs_cache',
              ];
              await Promise.all(
                cacheKeys.map((key) => AsyncStorage.removeItem(key))
              );
              onCacheClear?.();
              Alert.alert('Success', 'Cache cleared successfully');
            } catch {
              Alert.alert('Error', 'Failed to clear cache');
            }
          },
        },
      ]
    );
  }, [hapticEnabled, onCacheClear]);

  /** Reset all settings */
  const handleResetSettings = useCallback(async () => {
    if (hapticEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }

    Alert.alert(
      'Reset Settings',
      'This will reset all settings to defaults. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.removeItem('ralph_app_settings');
              await AsyncStorage.removeItem('ralph_server_url');
              onSettingsReset?.();
              Alert.alert('Success', 'Settings reset to defaults');
            } catch {
              Alert.alert('Error', 'Failed to reset settings');
            }
          },
        },
      ]
    );
  }, [hapticEnabled, onSettingsReset]);

  /** Toggle debug section (tap 5 times on version) */
  const [tapCount, setTapCount] = useState(0);
  const handleVersionTap = useCallback(() => {
    const newCount = tapCount + 1;
    setTapCount(newCount);
    if (newCount >= 5 && !showDebug) {
      setShowDebug(true);
      setTapCount(0);
      if (hapticEnabled) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    }
    // Reset tap count after 2 seconds
    setTimeout(() => setTapCount(0), 2000);
  }, [tapCount, showDebug, hapticEnabled]);

  return (
    <View className="bg-surface rounded-2xl p-4">
      <Text className="text-sm font-medium text-textSecondary mb-4">About</Text>

      {/* App Info */}
      <View className="border-b border-surfaceLight pb-3 mb-3">
        <Pressable onPress={handleVersionTap}>
          <InfoRow label="App Version" value={`v${appVersion}`} />
        </Pressable>
        <InfoRow label="Build Number" value={buildNumber} />
        <InfoRow label="Expo SDK" value={expoSdkVersion} />
      </View>

      {/* Server Info */}
      <View className="border-b border-surfaceLight pb-3 mb-3">
        <Text className="text-xs text-textSecondary mb-2">Server</Text>
        {isConnected && health ? (
          <>
            <InfoRow label="Status" value={health.status || 'Unknown'} />
            <InfoRow label="Version" value={health.version || 'Unknown'} />
          </>
        ) : (
          <View className="py-2">
            <Text className="text-sm text-red-400">Not connected</Text>
            <Text className="text-xs text-textSecondary mt-1">
              Configure server in Server Connection above
            </Text>
          </View>
        )}
      </View>

      {/* Links */}
      <View className="border-b border-surfaceLight pb-3 mb-3">
        <InfoRow
          label="Documentation"
          value="View Docs →"
          isLink
          onPress={handleDocsPress}
        />
      </View>

      {/* Debug Section (dev mode or after 5 taps) */}
      {showDebug && (
        <View>
          <Text className="text-xs text-textSecondary mb-2">Debug</Text>
          <View className="flex-row gap-3">
            <Pressable
              className="flex-1 bg-surfaceLight rounded-lg py-3 items-center active:opacity-70"
              onPress={handleClearCache}
            >
              <Text className="text-sm text-textSecondary">Clear Cache</Text>
            </Pressable>
            <Pressable
              className="flex-1 bg-red-500/20 rounded-lg py-3 items-center active:opacity-70"
              onPress={handleResetSettings}
            >
              <Text className="text-sm text-red-400">Reset All</Text>
            </Pressable>
          </View>
        </View>
      )}

      {/* Footer */}
      <View className="mt-4 items-center">
        <Text className="text-xs text-textSecondary">
          Ralph Mobile • Made with ❤️
        </Text>
      </View>
    </View>
  );
}

export default About;
