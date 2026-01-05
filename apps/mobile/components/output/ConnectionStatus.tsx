/**
 * ConnectionStatus - Shows WebSocket connection status
 *
 * Displays online/offline indicator for real-time log streaming.
 */

import React from 'react';
import { View, Text } from 'react-native';

type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error';

interface ConnectionStatusProps {
  /** Current connection state */
  state: ConnectionState;
  /** Optional error message */
  error?: string;
}

/**
 * Get status display properties
 */
function getStatusDisplay(state: ConnectionState): {
  color: string;
  bgColor: string;
  label: string;
  icon: string;
} {
  switch (state) {
    case 'connected':
      return {
        color: 'text-green-400',
        bgColor: 'bg-green-500/20',
        label: 'Connected',
        icon: '●',
      };
    case 'connecting':
      return {
        color: 'text-yellow-400',
        bgColor: 'bg-yellow-500/20',
        label: 'Connecting...',
        icon: '○',
      };
    case 'disconnected':
      return {
        color: 'text-gray-400',
        bgColor: 'bg-gray-500/20',
        label: 'Disconnected',
        icon: '○',
      };
    case 'error':
      return {
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        label: 'Error',
        icon: '✕',
      };
  }
}

/**
 * ConnectionStatus component
 */
export function ConnectionStatus({
  state,
  error,
}: ConnectionStatusProps): React.JSX.Element {
  const display = getStatusDisplay(state);

  return (
    <View className="flex-row items-center">
      <View className={`flex-row items-center px-2 py-1 rounded-full ${display.bgColor}`}>
        <Text className={`text-xs mr-1 ${display.color}`}>{display.icon}</Text>
        <Text className={`text-xs font-medium ${display.color}`}>
          {display.label}
        </Text>
      </View>
      {error && state === 'error' && (
        <Text className="text-xs text-red-400 ml-2" numberOfLines={1}>
          {error}
        </Text>
      )}
    </View>
  );
}

export default ConnectionStatus;
