/**
 * ServerConnection Component
 *
 * Server connection settings with:
 * - API URL input
 * - WebSocket URL input (auto-derived from API URL)
 * - Test connection button with status indicator
 * - Save/Reset buttons
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import type { ConnectionState } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceSecondary: '#262626',
  border: '#333333',
  success: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  gray600: '#4b5563',
};

interface ServerConnectionProps {
  /** Current API URL */
  apiUrl: string;
  /** Callback when API URL changes */
  onApiUrlChange: (url: string) => void;
  /** Current WebSocket URL */
  wsUrl: string;
  /** Callback when WebSocket URL changes */
  onWsUrlChange: (url: string) => void;
  /** Test connection handler - returns true if successful */
  onTestConnection: () => Promise<boolean>;
  /** Save settings handler */
  onSave: () => void;
  /** Reset to defaults handler */
  onReset: () => void;
  /** Whether settings have been modified */
  isDirty: boolean;
}

/**
 * Derive WebSocket URL from API URL
 */
function deriveWsUrl(apiUrl: string): string {
  try {
    const url = new URL(apiUrl);
    const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${url.host}`;
  } catch {
    return apiUrl.replace(/^http/, 'ws');
  }
}

/**
 * Get connection state color
 */
function getConnectionColor(state: ConnectionState): string {
  switch (state) {
    case 'connected':
      return colors.success;
    case 'connecting':
      return colors.warning;
    case 'disconnected':
      return colors.gray500;
    case 'error':
      return colors.error;
  }
}

/**
 * Get connection state label
 */
function getConnectionLabel(state: ConnectionState): string {
  switch (state) {
    case 'connected':
      return 'Connected';
    case 'connecting':
      return 'Testing...';
    case 'disconnected':
      return 'Not tested';
    case 'error':
      return 'Connection failed';
  }
}

/**
 * ServerConnection - Server configuration component
 *
 * Allows users to configure the API and WebSocket URLs,
 * test the connection, and save/reset settings.
 */
export function ServerConnection({
  apiUrl,
  onApiUrlChange,
  wsUrl,
  onWsUrlChange,
  onTestConnection,
  onSave,
  onReset,
  isDirty,
}: ServerConnectionProps): React.ReactElement {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [autoWs, setAutoWs] = useState(true);

  // Handle API URL change with auto-derive WebSocket URL
  const handleApiUrlChange = useCallback(
    (url: string) => {
      onApiUrlChange(url);
      if (autoWs) {
        onWsUrlChange(deriveWsUrl(url));
      }
    },
    [onApiUrlChange, onWsUrlChange, autoWs]
  );

  // Handle WebSocket URL change (disables auto-derive)
  const handleWsUrlChange = useCallback(
    (url: string) => {
      setAutoWs(false);
      onWsUrlChange(url);
    },
    [onWsUrlChange]
  );

  // Test connection handler
  const handleTestConnection = useCallback(async () => {
    setConnectionState('connecting');
    try {
      const success = await onTestConnection();
      setConnectionState(success ? 'connected' : 'error');
    } catch {
      setConnectionState('error');
    }
  }, [onTestConnection]);

  // Reset handler (also resets connection state)
  const handleReset = useCallback(() => {
    setConnectionState('disconnected');
    setAutoWs(true);
    onReset();
  }, [onReset]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Server Connection</Text>

      {/* API URL Input */}
      <Text style={styles.label}>API URL</Text>
      <TextInput
        value={apiUrl}
        onChangeText={handleApiUrlChange}
        style={styles.input}
        placeholder="http://localhost:8420"
        placeholderTextColor={colors.gray500}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
        accessibilityLabel="API URL input"
        accessibilityHint="Enter the Ralph orchestrator API URL"
      />

      {/* WebSocket URL Input */}
      <View style={styles.labelRow}>
        <Text style={styles.label}>WebSocket URL</Text>
        {autoWs && (
          <Text style={styles.autoLabel}>(auto)</Text>
        )}
      </View>
      <TextInput
        value={wsUrl}
        onChangeText={handleWsUrlChange}
        style={[styles.input, autoWs && styles.inputAuto]}
        placeholder="ws://localhost:8420"
        placeholderTextColor={colors.gray500}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
        accessibilityLabel="WebSocket URL input"
        accessibilityHint="Enter the Ralph orchestrator WebSocket URL"
      />

      {/* Connection Status */}
      <View style={styles.statusRow}>
        <View
          style={[
            styles.statusDot,
            { backgroundColor: getConnectionColor(connectionState) },
          ]}
        />
        <Text
          style={[
            styles.statusText,
            { color: getConnectionColor(connectionState) },
          ]}
        >
          {getConnectionLabel(connectionState)}
        </Text>
      </View>

      {/* Test Connection Button */}
      <Pressable
        style={({ pressed }) => [
          styles.testButton,
          pressed && styles.buttonPressed,
          connectionState === 'connecting' && styles.buttonDisabled,
        ]}
        onPress={handleTestConnection}
        disabled={connectionState === 'connecting'}
        accessibilityLabel="Test connection"
        accessibilityHint="Test the connection to the Ralph orchestrator server"
        accessibilityRole="button"
      >
        {connectionState === 'connecting' ? (
          <ActivityIndicator size="small" color={colors.white} />
        ) : (
          <Text style={styles.testButtonText}>Test Connection</Text>
        )}
      </Pressable>

      {/* Save/Reset Buttons */}
      <View style={styles.buttonRow}>
        <Pressable
          style={({ pressed }) => [
            styles.secondaryButton,
            pressed && styles.buttonPressed,
          ]}
          onPress={handleReset}
          accessibilityLabel="Reset to defaults"
          accessibilityHint="Reset server URLs to default values"
          accessibilityRole="button"
        >
          <Text style={styles.secondaryButtonText}>Reset</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
            !isDirty && styles.buttonDisabled,
          ]}
          onPress={onSave}
          disabled={!isDirty}
          accessibilityLabel="Save settings"
          accessibilityHint="Save the server connection settings"
          accessibilityRole="button"
        >
          <Text style={styles.primaryButtonText}>Save</Text>
        </Pressable>
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
    fontWeight: '600',
    fontSize: 16,
    marginBottom: 16,
  },
  label: {
    color: colors.gray400,
    fontSize: 14,
    marginBottom: 8,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  autoLabel: {
    color: colors.gray500,
    fontSize: 12,
    fontStyle: 'italic',
  },
  input: {
    backgroundColor: colors.surfaceSecondary,
    color: colors.white,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 12,
    fontSize: 14,
  },
  inputAuto: {
    opacity: 0.7,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '500',
  },
  testButton: {
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
    minHeight: 44,
    justifyContent: 'center',
  },
  testButtonText: {
    color: colors.white,
    fontWeight: '500',
    fontSize: 14,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  primaryButton: {
    flex: 1,
    backgroundColor: colors.info,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 14,
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  secondaryButtonText: {
    color: colors.gray300,
    fontWeight: '500',
    fontSize: 14,
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
});

export default ServerConnection;
