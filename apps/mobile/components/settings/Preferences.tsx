/**
 * Preferences - App preferences configuration component
 *
 * Displays:
 * - Auto-refresh interval selector
 * - Log buffer size selector
 * - Haptic feedback toggle
 */

import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, Pressable, Switch } from 'react-native';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { DEFAULT_SETTINGS, type AppSettings } from '../../lib/types';

const STORAGE_KEY = 'ralph_app_settings';

/** Auto-refresh interval options in seconds */
const REFRESH_INTERVALS = [
  { value: 5, label: '5 seconds' },
  { value: 10, label: '10 seconds' },
  { value: 30, label: '30 seconds' },
  { value: 60, label: '1 minute' },
];

/** Log buffer size options */
const BUFFER_SIZES = [
  { value: 100, label: '100 entries' },
  { value: 500, label: '500 entries' },
  { value: 1000, label: '1,000 entries' },
  { value: -1, label: 'Unlimited' },
];

interface PreferencesProps {
  /** Callback when haptic setting changes */
  onHapticChange?: (enabled: boolean) => void;
  /** Callback when any setting changes */
  onSettingsChange?: (settings: Partial<AppSettings>) => void;
}

/** Option selector component */
function OptionSelector({
  label,
  options,
  value,
  onChange,
  hapticEnabled,
}: {
  label: string;
  options: { value: number; label: string }[];
  value: number;
  onChange: (value: number) => void;
  hapticEnabled: boolean;
}): React.JSX.Element {
  const handleSelect = useCallback(
    async (newValue: number) => {
      if (hapticEnabled) {
        await Haptics.selectionAsync();
      }
      onChange(newValue);
    },
    [hapticEnabled, onChange]
  );

  return (
    <View className="mb-4">
      <Text className="text-xs text-textSecondary mb-2">{label}</Text>
      <View className="flex-row flex-wrap gap-2">
        {options.map((option) => (
          <Pressable
            key={option.value}
            className={`rounded-lg px-4 py-2 ${
              value === option.value ? 'bg-primary' : 'bg-surfaceLight'
            }`}
            onPress={() => handleSelect(option.value)}
          >
            <Text
              className={`text-sm ${
                value === option.value ? 'text-white font-medium' : 'text-textSecondary'
              }`}
            >
              {option.label}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

/**
 * Preferences component
 */
export function Preferences({
  onHapticChange,
  onSettingsChange,
}: PreferencesProps): React.JSX.Element {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const stored = await AsyncStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored) as Partial<AppSettings>;
          setSettings({ ...DEFAULT_SETTINGS, ...parsed });
        }
      } catch {
        // Use defaults on error
      } finally {
        setIsLoading(false);
      }
    };
    loadSettings();
  }, []);

  /** Save settings to AsyncStorage */
  const saveSettings = useCallback(async (newSettings: AppSettings) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
    } catch {
      // Silently fail
    }
  }, []);

  /** Update a setting */
  const updateSetting = useCallback(
    async <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
      const newSettings = { ...settings, [key]: value };
      setSettings(newSettings);
      await saveSettings(newSettings);
      onSettingsChange?.({ [key]: value });
    },
    [settings, saveSettings, onSettingsChange]
  );

  /** Handle refresh interval change */
  const handleRefreshChange = useCallback(
    (value: number) => {
      updateSetting('autoRefreshInterval', value);
    },
    [updateSetting]
  );

  /** Handle buffer size change */
  const handleBufferChange = useCallback(
    (value: number) => {
      updateSetting('logBufferSize', value);
    },
    [updateSetting]
  );

  /** Handle haptic toggle */
  const handleHapticToggle = useCallback(
    async (enabled: boolean) => {
      if (enabled) {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
      await updateSetting('hapticFeedbackEnabled', enabled);
      onHapticChange?.(enabled);
    },
    [updateSetting, onHapticChange]
  );

  /** Reset to defaults */
  const handleReset = useCallback(async () => {
    if (settings.hapticFeedbackEnabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    setSettings(DEFAULT_SETTINGS);
    await saveSettings(DEFAULT_SETTINGS);
    onSettingsChange?.(DEFAULT_SETTINGS);
    onHapticChange?.(DEFAULT_SETTINGS.hapticFeedbackEnabled);
  }, [settings.hapticFeedbackEnabled, saveSettings, onSettingsChange, onHapticChange]);

  if (isLoading) {
    return (
      <View className="bg-surface rounded-2xl p-4">
        <Text className="text-sm font-medium text-textSecondary mb-4">Preferences</Text>
        <View className="items-center py-8">
          <Text className="text-sm text-textSecondary">Loading...</Text>
        </View>
      </View>
    );
  }

  return (
    <View className="bg-surface rounded-2xl p-4">
      <View className="flex-row items-center justify-between mb-4">
        <Text className="text-sm font-medium text-textSecondary">Preferences</Text>
        <Pressable onPress={handleReset}>
          <Text className="text-xs text-primary">Reset All</Text>
        </Pressable>
      </View>

      {/* Auto-refresh Interval */}
      <OptionSelector
        label="Auto-refresh Interval"
        options={REFRESH_INTERVALS}
        value={settings.autoRefreshInterval}
        onChange={handleRefreshChange}
        hapticEnabled={settings.hapticFeedbackEnabled}
      />

      {/* Log Buffer Size */}
      <OptionSelector
        label="Log Buffer Size"
        options={BUFFER_SIZES}
        value={settings.logBufferSize}
        onChange={handleBufferChange}
        hapticEnabled={settings.hapticFeedbackEnabled}
      />

      {/* Haptic Feedback Toggle */}
      <View className="flex-row items-center justify-between py-2">
        <View>
          <Text className="text-sm text-textPrimary">Haptic Feedback</Text>
          <Text className="text-xs text-textSecondary">
            Vibration on button presses
          </Text>
        </View>
        <Switch
          value={settings.hapticFeedbackEnabled}
          onValueChange={handleHapticToggle}
          trackColor={{ false: '#374151', true: '#3b82f6' }}
          thumbColor={settings.hapticFeedbackEnabled ? '#fff' : '#9ca3af'}
        />
      </View>
    </View>
  );
}

export default Preferences;
