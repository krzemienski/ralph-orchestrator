import { View, Text, Pressable } from 'react-native';

export default function ControlsScreen() {
  return (
    <View className="flex-1 bg-background p-4">
      <Text className="text-2xl font-bold text-textPrimary mb-4">
        Controls
      </Text>
      <View className="bg-surface rounded-lg p-4 gap-3">
        <Pressable className="bg-primary rounded-lg p-4 active:opacity-80">
          <Text className="text-textPrimary font-semibold text-center">
            Start Agent
          </Text>
        </Pressable>
        <Pressable className="bg-surfaceLight rounded-lg p-4 active:opacity-80">
          <Text className="text-textSecondary font-semibold text-center">
            Stop Agent
          </Text>
        </Pressable>
      </View>
    </View>
  );
}
