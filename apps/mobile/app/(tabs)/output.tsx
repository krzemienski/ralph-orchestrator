import { View, Text, ScrollView } from 'react-native';

export default function OutputScreen() {
  return (
    <View className="flex-1 bg-background">
      <ScrollView className="flex-1 p-4">
        <Text className="text-2xl font-bold text-textPrimary mb-4">
          Output
        </Text>
        <View className="bg-surface rounded-lg p-4">
          <Text className="text-textSecondary font-mono text-sm">
            Agent output stream will appear here.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}
