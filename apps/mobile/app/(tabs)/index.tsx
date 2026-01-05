/**
 * Dashboard Screen - List of orchestrators with status and metrics
 *
 * Shows all orchestrators with pull-to-refresh and navigation to details.
 */

import React, { useCallback } from 'react';
import { View, Text, FlatList, RefreshControl, ActivityIndicator, Pressable } from 'react-native';
import type { ListRenderItem } from 'react-native';
import { useOrchestrators } from '../../lib/hooks';
import { OrchestratorCard, EmptyState } from '../../components/dashboard';
import type { Orchestrator } from '../../lib/types';

/**
 * Dashboard Screen Component
 */
export default function DashboardScreen(): React.JSX.Element {
  const { orchestrators, isLoading, isRefetching, error, refetch } = useOrchestrators({
    refetchInterval: 10_000, // Poll every 10 seconds
  });

  const handleRefresh = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const renderItem: ListRenderItem<Orchestrator> = useCallback(
    ({ item }) => <OrchestratorCard orchestrator={item} />,
    []
  );

  const keyExtractor = useCallback((item: Orchestrator) => item.id, []);

  // Loading state
  if (isLoading && orchestrators.length === 0) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text className="text-textSecondary mt-4">Loading orchestrators...</Text>
      </View>
    );
  }

  // Error state
  if (error && orchestrators.length === 0) {
    return (
      <View className="flex-1 bg-background items-center justify-center p-8">
        <View className="w-16 h-16 rounded-full bg-red-500/20 items-center justify-center mb-4">
          <Text className="text-3xl">⚠️</Text>
        </View>
        <Text className="text-lg font-medium text-textPrimary text-center mb-2">
          Connection Error
        </Text>
        <Text className="text-sm text-textSecondary text-center mb-6">
          {error.error || 'Unable to connect to server'}
        </Text>
        <Pressable
          onPress={handleRefresh}
          className="bg-blue-500 px-6 py-3 rounded-lg active:opacity-80"
        >
          <Text className="text-white font-semibold">Retry</Text>
        </Pressable>
      </View>
    );
  }

  // Empty state
  if (orchestrators.length === 0) {
    return (
      <View className="flex-1 bg-background">
        <EmptyState />
      </View>
    );
  }

  // List view
  return (
    <View className="flex-1 bg-background">
      {/* Header */}
      <View className="px-4 pt-4 pb-2">
        <Text className="text-2xl font-bold text-textPrimary">Dashboard</Text>
        <Text className="text-sm text-textSecondary mt-1">
          {orchestrators.length} orchestrator{orchestrators.length !== 1 ? 's' : ''}
        </Text>
      </View>

      {/* List */}
      <FlatList
        data={orchestrators}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 16 }}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={handleRefresh}
            tintColor="#3b82f6"
            colors={['#3b82f6']}
          />
        }
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}
