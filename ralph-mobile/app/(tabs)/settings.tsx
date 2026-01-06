/**
 * Settings Screen
 *
 * Full settings implementation with:
 * - Server connection configuration
 * - App preferences
 * - About information
 * - AsyncStorage persistence
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ScrollView, StyleSheet, ActivityIndicator, View, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { ServerConnection, Preferences, About } from '../../components/settings';
import { testConnection, setApiBaseUrl } from '../../lib/api/client';
import type { AppSettings, RefreshInterval, LogBufferSize } from '../../lib/types';
import { DEFAULT_SETTINGS } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  white: '#ffffff',
  gray400: '#9ca3af',
};

// Storage key for settings
const SETTINGS_STORAGE_KEY = '@ralph_mobile_settings';

/**
 * Load settings from AsyncStorage
 */
async function loadSettings(): Promise<AppSettings> {
  try {
    const stored = await AsyncStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
  return DEFAULT_SETTINGS;
}

/**
 * Save settings to AsyncStorage
 */
async function saveSettings(settings: AppSettings): Promise<void> {
  try {
    await AsyncStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error('Failed to save settings:', error);
  }
}

/**
 * Settings Screen Component
 *
 * Manages app settings with persistence via AsyncStorage.
 * Uses modular components for each settings section.
 */
export default function SettingsScreen(): React.ReactElement {
  // Loading state
  const [isLoading, setIsLoading] = useState(true);

  // Settings state
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);

  // Draft state for unsaved changes
  const [draftApiUrl, setDraftApiUrl] = useState(DEFAULT_SETTINGS.apiUrl);
  const [draftWsUrl, setDraftWsUrl] = useState(DEFAULT_SETTINGS.wsUrl);
  const [isDirty, setIsDirty] = useState(false);

  // Load settings on mount
  useEffect(() => {
    loadSettings().then((loaded) => {
      setSettings(loaded);
      setDraftApiUrl(loaded.apiUrl);
      setDraftWsUrl(loaded.wsUrl);
      // Apply saved API URL to client
      setApiBaseUrl(loaded.apiUrl);
      setIsLoading(false);
    });
  }, []);

  // Track dirty state for server URLs
  useEffect(() => {
    setIsDirty(
      draftApiUrl !== settings.apiUrl || draftWsUrl !== settings.wsUrl
    );
  }, [draftApiUrl, draftWsUrl, settings.apiUrl, settings.wsUrl]);

  // Server connection handlers
  const handleApiUrlChange = useCallback((url: string) => {
    setDraftApiUrl(url);
  }, []);

  const handleWsUrlChange = useCallback((url: string) => {
    setDraftWsUrl(url);
  }, []);

  const handleTestConnection = useCallback(async (): Promise<boolean> => {
    // Temporarily set URL for testing
    setApiBaseUrl(draftApiUrl);
    const success = await testConnection();
    // Restore original if test fails and we haven't saved
    if (!success) {
      setApiBaseUrl(settings.apiUrl);
    }
    return success;
  }, [draftApiUrl, settings.apiUrl]);

  const handleSaveServer = useCallback(async () => {
    const newSettings = {
      ...settings,
      apiUrl: draftApiUrl,
      wsUrl: draftWsUrl,
    };
    setSettings(newSettings);
    await saveSettings(newSettings);
    // Apply saved API URL to client
    setApiBaseUrl(draftApiUrl);
  }, [settings, draftApiUrl, draftWsUrl]);

  const handleResetServer = useCallback(() => {
    setDraftApiUrl(DEFAULT_SETTINGS.apiUrl);
    setDraftWsUrl(DEFAULT_SETTINGS.wsUrl);
  }, []);

  // Preferences handlers
  const handleRefreshIntervalChange = useCallback(
    async (interval: RefreshInterval) => {
      const newSettings = { ...settings, refreshInterval: interval };
      setSettings(newSettings);
      await saveSettings(newSettings);
    },
    [settings]
  );

  const handleLogBufferSizeChange = useCallback(
    async (size: LogBufferSize) => {
      const newSettings = { ...settings, logBufferSize: size };
      setSettings(newSettings);
      await saveSettings(newSettings);
    },
    [settings]
  );

  const handleHapticFeedbackChange = useCallback(
    async (enabled: boolean) => {
      const newSettings = { ...settings, hapticFeedbackEnabled: enabled };
      setSettings(newSettings);
      await saveSettings(newSettings);
    },
    [settings]
  );

  const handleDarkModeChange = useCallback(
    async (enabled: boolean) => {
      const newSettings = { ...settings, darkMode: enabled };
      setSettings(newSettings);
      await saveSettings(newSettings);
    },
    [settings]
  );

  // Loading state
  if (isLoading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.white} />
          <Text style={styles.loadingText}>Loading settings...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Server Connection Section */}
        <ServerConnection
          apiUrl={draftApiUrl}
          onApiUrlChange={handleApiUrlChange}
          wsUrl={draftWsUrl}
          onWsUrlChange={handleWsUrlChange}
          onTestConnection={handleTestConnection}
          onSave={handleSaveServer}
          onReset={handleResetServer}
          isDirty={isDirty}
        />

        {/* Preferences Section */}
        <View style={styles.sectionGap} />
        <Preferences
          refreshInterval={settings.refreshInterval}
          onRefreshIntervalChange={handleRefreshIntervalChange}
          logBufferSize={settings.logBufferSize}
          onLogBufferSizeChange={handleLogBufferSizeChange}
          hapticFeedbackEnabled={settings.hapticFeedbackEnabled}
          onHapticFeedbackChange={handleHapticFeedbackChange}
          darkMode={settings.darkMode}
          onDarkModeChange={handleDarkModeChange}
        />

        {/* About Section */}
        <View style={styles.sectionGap} />
        <About />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  sectionGap: {
    height: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    color: colors.gray400,
    fontSize: 14,
  },
});
