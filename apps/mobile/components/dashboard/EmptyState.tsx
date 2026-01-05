/**
 * EmptyState - Display when no orchestrators exist
 *
 * Shows illustration/icon, message, and action button.
 */

import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';

interface EmptyStateProps {
  /** Optional custom message */
  message?: string;
  /** Whether to show the start button */
  showStartButton?: boolean;
}

/**
 * EmptyState component
 */
export function EmptyState({
  message = 'No orchestrators running',
  showStartButton = true,
}: EmptyStateProps): React.JSX.Element {
  const router = useRouter();

  const handleStartNew = (): void => {
    router.push('/controls');
  };

  return (
    <View className="flex-1 items-center justify-center p-8">
      {/* Icon representation using text/emoji */}
      <View className="w-20 h-20 rounded-full bg-surface items-center justify-center mb-4">
        <Text className="text-4xl">🤖</Text>
      </View>

      {/* Message */}
      <Text className="text-lg font-medium text-textPrimary text-center mb-2">
        {message}
      </Text>
      <Text className="text-sm text-textSecondary text-center mb-6">
        Start a new orchestration to see it appear here
      </Text>

      {/* Start New Button */}
      {showStartButton && (
        <Pressable
          onPress={handleStartNew}
          className="bg-blue-500 px-6 py-3 rounded-lg active:opacity-80"
        >
          <Text className="text-white font-semibold">Start New</Text>
        </Pressable>
      )}
    </View>
  );
}

export default EmptyState;
