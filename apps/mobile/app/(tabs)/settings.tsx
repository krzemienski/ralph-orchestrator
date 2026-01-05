import { View, Text, ScrollView } from 'react-native';

export default function SettingsScreen() {
  return (
    <View className="flex-1 bg-background">
      <ScrollView className="flex-1 p-4">
        <Text className="text-2xl font-bold text-textPrimary mb-4">
          Settings
        </Text>
        <View className="bg-surface rounded-lg p-4 gap-4">
          <View className="border-b border-surfaceLight pb-4">
            <Text className="text-textPrimary font-semibold">Server URL</Text>
            <Text className="text-textMuted text-sm">Configure backend connection</Text>
          </View>
          <View className="border-b border-surfaceLight pb-4">
            <Text className="text-textPrimary font-semibold">Authentication</Text>
            <Text className="text-textMuted text-sm">Manage API credentials</Text>
          </View>
          <View>
            <Text className="text-textPrimary font-semibold">About</Text>
            <Text className="text-textMuted text-sm">Ralph Mobile v1.0.0</Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}
