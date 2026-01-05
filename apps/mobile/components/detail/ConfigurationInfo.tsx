/**
 * ConfigurationInfo - Configuration display for orchestrator detail
 *
 * Displays:
 * - Prompt file path
 * - Config file path
 * - Port (if running)
 * - Created/Updated timestamps
 */

import React, { useCallback } from 'react';
import { View, Text, Pressable, Alert } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import type { Orchestrator } from '../../lib/types';

interface ConfigurationInfoProps {
  /** Orchestrator data */
  orchestrator: Orchestrator;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
}

/** Format timestamp for display */
function formatTimestamp(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

/** Extract filename from path */
function extractFilename(path: string): string {
  const parts = path.split('/');
  return parts[parts.length - 1] || path;
}

/** Individual config row */
function ConfigRow({
  label,
  value,
  fullPath,
  onCopy,
  icon,
}: {
  label: string;
  value: string;
  fullPath?: string;
  onCopy?: () => void;
  icon: string;
}): React.JSX.Element {
  return (
    <Pressable
      className={`flex-row items-start py-3 ${onCopy ? 'active:opacity-70' : ''}`}
      onPress={onCopy}
      disabled={!onCopy}
    >
      <Text className="text-base mr-2">{icon}</Text>
      <View className="flex-1">
        <Text className="text-xs text-textSecondary mb-0.5">{label}</Text>
        <Text className="text-sm text-textPrimary" numberOfLines={1}>
          {value}
        </Text>
        {fullPath && fullPath !== value && (
          <Text className="text-xs text-textSecondary font-mono mt-0.5" numberOfLines={1}>
            {fullPath}
          </Text>
        )}
      </View>
      {onCopy && <Text className="text-xs text-textSecondary ml-2">📋</Text>}
    </Pressable>
  );
}

/**
 * ConfigurationInfo component
 */
export function ConfigurationInfo({
  orchestrator,
  hapticEnabled = true,
}: ConfigurationInfoProps): React.JSX.Element {
  const { prompt_file, config_file, port, created_at, updated_at } = orchestrator;

  /** Trigger haptic feedback */
  const triggerHaptic = useCallback(() => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  }, [hapticEnabled]);

  /** Copy path to clipboard */
  const handleCopyPath = useCallback(
    async (path: string, label: string) => {
      triggerHaptic();
      await Clipboard.setStringAsync(path);
      Alert.alert('Copied', `${label} copied to clipboard`);
    },
    [triggerHaptic]
  );

  return (
    <View className="bg-surface rounded-2xl p-4">
      <Text className="text-sm font-medium text-textSecondary mb-2">Configuration</Text>

      <View className="divide-y divide-gray-800">
        {/* Prompt file */}
        <ConfigRow
          label="Prompt File"
          value={extractFilename(prompt_file)}
          fullPath={prompt_file}
          onCopy={() => handleCopyPath(prompt_file, 'Prompt file path')}
          icon="📄"
        />

        {/* Config file */}
        <ConfigRow
          label="Config File"
          value={extractFilename(config_file)}
          fullPath={config_file}
          onCopy={() => handleCopyPath(config_file, 'Config file path')}
          icon="⚙️"
        />

        {/* Port (if running) */}
        {port && (
          <ConfigRow
            label="Port"
            value={port.toString()}
            onCopy={() => handleCopyPath(`http://localhost:${port}`, 'Server URL')}
            icon="🔌"
          />
        )}

        {/* Created timestamp */}
        <ConfigRow
          label="Created"
          value={formatTimestamp(created_at)}
          icon="🕐"
        />

        {/* Updated timestamp */}
        <ConfigRow
          label="Last Updated"
          value={formatTimestamp(updated_at)}
          icon="🔄"
        />
      </View>
    </View>
  );
}

export default ConfigurationInfo;
