import { View, Text, ScrollView } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function OrchestratorDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <SafeAreaView className="flex-1 bg-background" edges={['bottom']}>
      <ScrollView className="flex-1" contentContainerClassName="p-4">
        <View className="items-center justify-center py-10">
          <Text className="text-2xl font-bold text-white mb-2">
            Orchestrator Details
          </Text>
          <Text className="text-gray-400 text-center">ID: {id}</Text>
        </View>

        {/* Placeholder content */}
        <View className="bg-surface rounded-xl p-4 border border-border">
          <Text className="text-white font-semibold mb-2">
            Details will be implemented in Phase 5
          </Text>
          <Text className="text-gray-400 text-sm">
            This view will show metrics, tasks, and configuration
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
