import { View, Text } from 'react-native';

export default function DashboardScreen() {
  return (
    <View className="flex-1 bg-background p-4">
      <Text className="text-2xl font-bold text-textPrimary mb-4">
        Dashboard
      </Text>
      <View className="bg-surface rounded-lg p-4">
        <Text className="text-textSecondary">
          Agent status and quick actions will appear here.
        </Text>
      </View>
    </View>
  );
}
