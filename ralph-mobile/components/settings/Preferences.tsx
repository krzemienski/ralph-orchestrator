/**
 * Preferences Component
 *
 * App behavior settings with:
 * - Auto-refresh interval selector
 * - Log buffer size selector
 * - Haptic feedback toggle
 * - Dark mode toggle (always on for now)
 */

import React from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Switch,
} from 'react-native';
import type { RefreshInterval, LogBufferSize } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceSecondary: '#262626',
  border: '#333333',
  info: '#3b82f6',
  white: '#ffffff',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

interface PreferencesProps {
  /** Current refresh interval */
  refreshInterval: RefreshInterval;
  /** Callback when refresh interval changes */
  onRefreshIntervalChange: (interval: RefreshInterval) => void;
  /** Current log buffer size */
  logBufferSize: LogBufferSize;
  /** Callback when log buffer size changes */
  onLogBufferSizeChange: (size: LogBufferSize) => void;
  /** Whether haptic feedback is enabled */
  hapticFeedbackEnabled: boolean;
  /** Callback when haptic feedback changes */
  onHapticFeedbackChange: (enabled: boolean) => void;
  /** Whether dark mode is enabled */
  darkMode: boolean;
  /** Callback when dark mode changes */
  onDarkModeChange: (enabled: boolean) => void;
}

const REFRESH_INTERVALS: { value: RefreshInterval; label: string }[] = [
  { value: 5, label: '5s' },
  { value: 10, label: '10s' },
  { value: 30, label: '30s' },
  { value: 60, label: '1m' },
];

const LOG_BUFFER_SIZES: { value: LogBufferSize; label: string }[] = [
  { value: 100, label: '100' },
  { value: 500, label: '500' },
  { value: 1000, label: '1K' },
  { value: -1, label: '∞' },
];

/**
 * Preferences - App behavior settings component
 *
 * Allows users to configure:
 * - Auto-refresh interval for data updates
 * - Log buffer size for memory management
 * - Haptic feedback for touch interactions
 * - Dark mode (currently always on)
 */
export function Preferences({
  refreshInterval,
  onRefreshIntervalChange,
  logBufferSize,
  onLogBufferSizeChange,
  hapticFeedbackEnabled,
  onHapticFeedbackChange,
  darkMode,
  onDarkModeChange,
}: PreferencesProps): React.ReactElement {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Preferences</Text>

      {/* Auto-refresh Interval */}
      <View style={styles.settingRow}>
        <View style={styles.settingLabelContainer}>
          <Text style={styles.settingLabel}>Auto-refresh</Text>
          <Text style={styles.settingDescription}>
            How often to fetch updates
          </Text>
        </View>
        <View style={styles.segmentedControl}>
          {REFRESH_INTERVALS.map((option) => (
            <Pressable
              key={option.value}
              style={[
                styles.segmentOption,
                refreshInterval === option.value && styles.segmentOptionActive,
              ]}
              onPress={() => onRefreshIntervalChange(option.value)}
              accessibilityLabel={`Set refresh interval to ${option.label}`}
              accessibilityRole="button"
              accessibilityState={{ selected: refreshInterval === option.value }}
            >
              <Text
                style={[
                  styles.segmentText,
                  refreshInterval === option.value && styles.segmentTextActive,
                ]}
              >
                {option.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Log Buffer Size */}
      <View style={styles.settingRow}>
        <View style={styles.settingLabelContainer}>
          <Text style={styles.settingLabel}>Log buffer</Text>
          <Text style={styles.settingDescription}>
            Max logs to keep in memory
          </Text>
        </View>
        <View style={styles.segmentedControl}>
          {LOG_BUFFER_SIZES.map((option) => (
            <Pressable
              key={option.value}
              style={[
                styles.segmentOption,
                logBufferSize === option.value && styles.segmentOptionActive,
              ]}
              onPress={() => onLogBufferSizeChange(option.value)}
              accessibilityLabel={`Set log buffer to ${option.value === -1 ? 'unlimited' : option.label}`}
              accessibilityRole="button"
              accessibilityState={{ selected: logBufferSize === option.value }}
            >
              <Text
                style={[
                  styles.segmentText,
                  logBufferSize === option.value && styles.segmentTextActive,
                ]}
              >
                {option.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Haptic Feedback Toggle */}
      <View style={styles.toggleRow}>
        <View style={styles.settingLabelContainer}>
          <Text style={styles.settingLabel}>Haptic feedback</Text>
          <Text style={styles.settingDescription}>
            Vibration on touch interactions
          </Text>
        </View>
        <Switch
          value={hapticFeedbackEnabled}
          onValueChange={onHapticFeedbackChange}
          trackColor={{ false: colors.surfaceSecondary, true: colors.info }}
          thumbColor={colors.white}
          accessibilityLabel="Toggle haptic feedback"
          accessibilityRole="switch"
          accessibilityState={{ checked: hapticFeedbackEnabled }}
        />
      </View>

      {/* Dark Mode Toggle */}
      <View style={styles.toggleRow}>
        <View style={styles.settingLabelContainer}>
          <Text style={styles.settingLabel}>Dark mode</Text>
          <Text style={styles.settingDescription}>
            Use dark theme (always on)
          </Text>
        </View>
        <Switch
          value={darkMode}
          onValueChange={onDarkModeChange}
          trackColor={{ false: colors.surfaceSecondary, true: colors.info }}
          thumbColor={colors.white}
          disabled // Always dark mode for now
          accessibilityLabel="Toggle dark mode"
          accessibilityRole="switch"
          accessibilityState={{ checked: darkMode, disabled: true }}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 16,
    marginBottom: 16,
  },
  settingRow: {
    marginBottom: 20,
  },
  settingLabelContainer: {
    marginBottom: 10,
  },
  settingLabel: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  settingDescription: {
    color: colors.gray500,
    fontSize: 12,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 8,
    padding: 4,
  },
  segmentOption: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  segmentOptionActive: {
    backgroundColor: colors.info,
  },
  segmentText: {
    color: colors.gray400,
    fontSize: 13,
    fontWeight: '500',
  },
  segmentTextActive: {
    color: colors.white,
  },
  toggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});

export default Preferences;
