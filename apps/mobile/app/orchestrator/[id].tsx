/**
 * Orchestrator Detail Screen - Placeholder for Phase 3
 *
 * This is a placeholder route to enable navigation from the dashboard.
 * Full implementation will be done in Phase 3.
 */

import React from 'react';
import { View, Text } from 'react-native';
import { useLocalSearchParams } from 'expo-router';

/**
 * Orchestrator Detail Screen Component
 */
export default function OrchestratorDetailScreen(): React.JSX.Element {
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <View className="flex-1 bg-background items-center justify-center p-8">
      <View className="w-16 h-16 rounded-full bg-blue-500/20 items-center justify-center mb-4">
        <Text className="text-3xl">🔧</Text>
      </View>
      <Text className="text-lg font-medium text-textPrimary text-center mb-2">
        Orchestrator Details
      </Text>
      <Text className="text-sm text-textSecondary text-center">
        ID: {id}
      </Text>
      <Text className="text-xs text-textSecondary text-center mt-4">
        Full implementation coming in Phase 3
      </Text>
    </View>
  );
}
