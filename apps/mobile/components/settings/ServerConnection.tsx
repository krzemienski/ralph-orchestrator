/**
 * ServerConnection - Server URL configuration component
 *
 * Displays:
 * - API URL input field
 * - WebSocket URL input field
 * - Test connection button with status indicator
 * - Save/reset buttons
 */

import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, TextInput, Pressable, ActivityIndicator } from 'react-native';
import * as Haptics from 'expo-haptics';
import { useConnection } from '../../lib/hooks/useConnection';
import { DEFAULT_SETTINGS } from '../../lib/types';

interface ServerConnectionProps {
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
}

/**
 * ServerConnection component
 */
export function ServerConnection({
  hapticEnabled = true,
}: ServerConnectionProps): React.JSX.Element {
  const {
    serverUrl,
    isConnected,
    isTesting,
    error,
    health,
    testConnection,
    updateServerUrl,
  } = useConnection();

  // Local state for editing
  const [apiUrl, setApiUrl] = useState(serverUrl);
  const [wsUrl, setWsUrl] = useState(serverUrl.replace(/^http/, 'ws'));
  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Sync local state when serverUrl changes externally
  useEffect(() => {
    setApiUrl(serverUrl);
    setWsUrl(serverUrl.replace(/^http/, 'ws'));
  }, [serverUrl]);

  // Track changes
  useEffect(() => {
    const apiChanged = apiUrl !== serverUrl;
    const wsChanged = wsUrl !== serverUrl.replace(/^http/, 'ws');
    setHasChanges(apiChanged || wsChanged);
  }, [apiUrl, wsUrl, serverUrl]);

  /** Handle API URL change */
  const handleApiUrlChange = useCallback((text: string) => {
    setApiUrl(text);
    // Auto-update WebSocket URL if it follows the pattern
    if (wsUrl === serverUrl.replace(/^http/, 'ws')) {
      setWsUrl(text.replace(/^http/, 'ws'));
    }
  }, [wsUrl, serverUrl]);

  /** Handle test connection */
  const handleTestConnection = useCallback(async () => {
    if (hapticEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    await testConnection();
  }, [hapticEnabled, testConnection]);

  /** Handle save */
  const handleSave = useCallback(async () => {
    if (hapticEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }

    setSaveStatus('saving');
    try {
      await updateServerUrl(apiUrl);
      setSaveStatus('saved');
      setHasChanges(false);

      // Reset status after delay
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  }, [hapticEnabled, apiUrl, updateServerUrl]);

  /** Handle reset to defaults */
  const handleReset = useCallback(async () => {
    if (hapticEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    setApiUrl(DEFAULT_SETTINGS.serverUrl);
    setWsUrl(DEFAULT_SETTINGS.websocketUrl);
  }, [hapticEnabled]);

  /** Get connection status display */
  const getConnectionStatus = (): { text: string; color: string; bgColor: string } => {
    if (isTesting) {
      return { text: 'Testing...', color: 'text-blue-400', bgColor: 'bg-blue-500/20' };
    }
    if (error) {
      return { text: 'Disconnected', color: 'text-red-400', bgColor: 'bg-red-500/20' };
    }
    if (isConnected && health) {
      return { text: 'Connected', color: 'text-green-400', bgColor: 'bg-green-500/20' };
    }
    return { text: 'Unknown', color: 'text-gray-400', bgColor: 'bg-gray-500/20' };
  };

  const status = getConnectionStatus();

  return (
    <View className="bg-surface rounded-2xl p-4">
      <Text className="text-sm font-medium text-textSecondary mb-4">Server Connection</Text>

      {/* Connection Status */}
      <View className="flex-row items-center justify-between mb-4">
        <View className="flex-row items-center">
          <View className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
          <Text className="text-sm text-textPrimary">Status</Text>
        </View>
        <View className={`rounded-lg px-3 py-1 ${status.bgColor}`}>
          {isTesting ? (
            <View className="flex-row items-center">
              <ActivityIndicator size="small" color="#60a5fa" />
              <Text className={`text-xs font-medium ml-2 ${status.color}`}>{status.text}</Text>
            </View>
          ) : (
            <Text className={`text-xs font-medium ${status.color}`}>{status.text}</Text>
          )}
        </View>
      </View>

      {/* Server info when connected */}
      {isConnected && health && (
        <View className="bg-surfaceLight rounded-lg p-3 mb-4">
          <View className="flex-row justify-between mb-1">
            <Text className="text-xs text-textSecondary">Status</Text>
            <Text className="text-xs text-textPrimary">{health.status || 'Unknown'}</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-xs text-textSecondary">Version</Text>
            <Text className="text-xs text-textPrimary">{health.version || 'Unknown'}</Text>
          </View>
        </View>
      )}

      {/* Error message */}
      {error && (
        <View className="bg-red-500/10 rounded-lg p-3 mb-4">
          <Text className="text-xs text-red-400">{error.error}</Text>
        </View>
      )}

      {/* API URL Input */}
      <View className="mb-4">
        <Text className="text-xs text-textSecondary mb-2">API URL</Text>
        <TextInput
          className="bg-surfaceLight rounded-lg px-4 py-3 text-textPrimary text-sm"
          value={apiUrl}
          onChangeText={handleApiUrlChange}
          placeholder="http://localhost:8420"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
      </View>

      {/* WebSocket URL Input */}
      <View className="mb-4">
        <Text className="text-xs text-textSecondary mb-2">WebSocket URL</Text>
        <TextInput
          className="bg-surfaceLight rounded-lg px-4 py-3 text-textPrimary text-sm"
          value={wsUrl}
          onChangeText={setWsUrl}
          placeholder="ws://localhost:8420"
          placeholderTextColor="#6b7280"
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
      </View>

      {/* Action Buttons */}
      <View className="flex-row gap-3">
        {/* Test Connection Button */}
        <Pressable
          className={`flex-1 rounded-lg py-3 items-center ${
            isTesting ? 'bg-blue-500/50' : 'bg-blue-500'
          }`}
          onPress={handleTestConnection}
          disabled={isTesting}
        >
          {isTesting ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text className="text-sm font-medium text-white">Test</Text>
          )}
        </Pressable>

        {/* Save Button */}
        <Pressable
          className={`flex-1 rounded-lg py-3 items-center ${
            hasChanges
              ? saveStatus === 'saving'
                ? 'bg-green-500/50'
                : 'bg-green-500'
              : 'bg-gray-600'
          }`}
          onPress={handleSave}
          disabled={!hasChanges || saveStatus === 'saving'}
        >
          {saveStatus === 'saving' ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : saveStatus === 'saved' ? (
            <Text className="text-sm font-medium text-white">Saved ✓</Text>
          ) : (
            <Text className="text-sm font-medium text-white">Save</Text>
          )}
        </Pressable>

        {/* Reset Button */}
        <Pressable
          className="rounded-lg py-3 px-4 items-center bg-gray-700"
          onPress={handleReset}
        >
          <Text className="text-sm font-medium text-textSecondary">Reset</Text>
        </Pressable>
      </View>
    </View>
  );
}

export default ServerConnection;
