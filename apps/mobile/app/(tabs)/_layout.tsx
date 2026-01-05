/**
 * Tab Layout - Main navigation structure
 *
 * Includes accessibility labels for screen readers
 */

import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: true,
        headerStyle: {
          backgroundColor: '#1a1a1a',
        },
        headerTintColor: '#ffffff',
        headerTitleStyle: {
          fontWeight: '600',
        },
        tabBarStyle: {
          backgroundColor: '#1a1a1a',
          borderTopColor: '#2a2a2a',
          borderTopWidth: 1,
        },
        tabBarActiveTintColor: '#3b82f6',
        tabBarInactiveTintColor: '#71717a',
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarAccessibilityLabel: 'Dashboard tab, view orchestrators',
          tabBarIcon: ({ color, size }) => (
            <Ionicons
              name="grid-outline"
              size={size}
              color={color}
              accessibilityLabel="Dashboard"
            />
          ),
        }}
      />
      <Tabs.Screen
        name="output"
        options={{
          title: 'Output',
          tabBarAccessibilityLabel: 'Output tab, view logs',
          tabBarIcon: ({ color, size }) => (
            <Ionicons
              name="terminal-outline"
              size={size}
              color={color}
              accessibilityLabel="Output logs"
            />
          ),
        }}
      />
      <Tabs.Screen
        name="controls"
        options={{
          title: 'Controls',
          tabBarAccessibilityLabel: 'Controls tab, manage orchestrations',
          tabBarIcon: ({ color, size }) => (
            <Ionicons
              name="game-controller-outline"
              size={size}
              color={color}
              accessibilityLabel="Controls"
            />
          ),
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
          tabBarAccessibilityLabel: 'Settings tab, app preferences',
          tabBarIcon: ({ color, size }) => (
            <Ionicons
              name="settings-outline"
              size={size}
              color={color}
              accessibilityLabel="Settings"
            />
          ),
        }}
      />
    </Tabs>
  );
}
