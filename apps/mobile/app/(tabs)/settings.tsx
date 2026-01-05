/**
 * Settings Screen - App configuration and preferences
 *
 * Displays:
 * - Server connection configuration
 * - App preferences (refresh interval, buffer size, haptics)
 * - About section with version info
 */

import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, RefreshControl } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ServerConnection, Preferences, About } from '../../components/settings';
import { useConnection } from '../../lib/hooks/useConnection';

export default function SettingsScreen(): React.JSX.Element {
  const insets = useSafeAreaInsets();
  const { testConnection } = useConnection();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hapticEnabled, setHapticEnabled] = useState(true);

  /** Handle pull-to-refresh */
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await testConnection();
    setIsRefreshing(false);
  }, [testConnection]);

  /** Handle haptic setting change */
  const handleHapticChange = useCallback((enabled: boolean) => {
    setHapticEnabled(enabled);
  }, []);

  /** Handle cache clear */
  const handleCacheClear = useCallback(() => {
    // Could trigger a re-fetch or state reset here
  }, []);

  /** Handle settings reset */
  const handleSettingsReset = useCallback(() => {
    setHapticEnabled(true);
  }, []);

  return (
    <View className="flex-1 bg-background">
      <ScrollView
        className="flex-1"
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingTop: 16,
          paddingBottom: insets.bottom + 16,
        }}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#3b82f6"
          />
        }
      >
        {/* Header */}
        <View className="mb-6">
          <Text className="text-2xl font-bold text-textPrimary">Settings</Text>
          <Text className="text-sm text-textSecondary mt-1">
            Configure your Ralph Mobile experience
          </Text>
        </View>

        {/* Server Connection Section */}
        <View className="mb-4">
          <ServerConnection hapticEnabled={hapticEnabled} />
        </View>

        {/* Preferences Section */}
        <View className="mb-4">
          <Preferences onHapticChange={handleHapticChange} />
        </View>

        {/* About Section */}
        <View className="mb-4">
          <About
            hapticEnabled={hapticEnabled}
            onCacheClear={handleCacheClear}
            onSettingsReset={handleSettingsReset}
          />
        </View>
      </ScrollView>
    </View>
  );
}
