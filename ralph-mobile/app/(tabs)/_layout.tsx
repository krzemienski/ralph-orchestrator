/**
 * @fileoverview Tab navigation layout using Expo Router
 * Implements bottom tab navigation with Dashboard, History, and Settings
 */

import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { tabs, getTabIcon, getTabTitle } from '../../lib/navigation';
import { colors } from '../../lib/theme';

/**
 * Tab bar icon component
 */
function TabBarIcon({ name, color }: { name: keyof typeof Ionicons.glyphMap; color: string }) {
  return <Ionicons name={name} size={24} color={color} />;
}

/**
 * Tab layout component with bottom navigation
 */
export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.background,
        },
        headerStyle: {
          backgroundColor: colors.surface,
        },
        headerTintColor: colors.text,
      }}
    >
      {tabs.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.title,
            tabBarIcon: ({ color }) => (
              <TabBarIcon name={getTabIcon(tab.name) as keyof typeof Ionicons.glyphMap} color={color} />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}
