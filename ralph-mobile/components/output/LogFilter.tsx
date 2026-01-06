/**
 * LogFilter Component
 *
 * Filter controls for log viewer with level toggles,
 * clear logs button, and pause/resume streaming toggle.
 */

import React, { memo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { LogLevel } from '../../lib/types';
import { LOG_LEVEL_COLORS } from '../../lib/types';

interface LogFilterProps {
  /** Currently enabled log levels */
  enabledLevels: Set<LogLevel>;
  /** Callback when a level is toggled */
  onToggleLevel: (level: LogLevel) => void;
  /** Whether log streaming is paused */
  isPaused: boolean;
  /** Callback when pause/resume is toggled */
  onTogglePause: () => void;
  /** Callback when clear logs is pressed */
  onClearLogs: () => void;
  /** Total log count */
  logCount: number;
}

/**
 * All available log levels
 */
const LOG_LEVELS: LogLevel[] = ['debug', 'info', 'warn', 'error'];

/**
 * Theme colors for dark mode
 */
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceHover: '#252525',
  border: '#333333',
  white: '#ffffff',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  gray600: '#4b5563',
  info: '#3b82f6',
  error: '#ef4444',
  warning: '#eab308',
};

/**
 * LogFilter - Filter controls for log viewer
 *
 * Features:
 * - Toggle buttons for each log level
 * - Pause/resume streaming toggle
 * - Clear logs button
 * - Log count display
 */
function LogFilterComponent({
  enabledLevels,
  onToggleLevel,
  isPaused,
  onTogglePause,
  onClearLogs,
  logCount,
}: LogFilterProps): React.ReactElement {
  return (
    <View style={styles.container}>
      {/* Level Toggles Row */}
      <View style={styles.levelRow}>
        {LOG_LEVELS.map((level) => (
          <LevelToggle
            key={level}
            level={level}
            isEnabled={enabledLevels.has(level)}
            onToggle={() => onToggleLevel(level)}
          />
        ))}
      </View>

      {/* Actions Row */}
      <View style={styles.actionsRow}>
        {/* Log Count */}
        <Text style={styles.logCount}>
          {logCount} {logCount === 1 ? 'log' : 'logs'}
        </Text>

        {/* Spacer */}
        <View style={styles.spacer} />

        {/* Pause/Resume Button */}
        <Pressable
          onPress={onTogglePause}
          style={({ pressed }) => [
            styles.actionButton,
            isPaused && styles.actionButtonActive,
            pressed && styles.actionButtonPressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel={isPaused ? 'Resume streaming' : 'Pause streaming'}
          accessibilityState={{ selected: isPaused }}
        >
          <Ionicons
            name={isPaused ? 'play' : 'pause'}
            size={16}
            color={isPaused ? colors.info : colors.gray400}
          />
          <Text
            style={[
              styles.actionButtonText,
              isPaused && styles.actionButtonTextActive,
            ]}
          >
            {isPaused ? 'Resume' : 'Pause'}
          </Text>
        </Pressable>

        {/* Clear Logs Button */}
        <Pressable
          onPress={onClearLogs}
          style={({ pressed }) => [
            styles.actionButton,
            pressed && styles.actionButtonPressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel="Clear all logs"
        >
          <Ionicons
            name="trash-outline"
            size={16}
            color={colors.gray400}
          />
          <Text style={styles.actionButtonText}>Clear</Text>
        </Pressable>
      </View>
    </View>
  );
}

/**
 * Level Toggle - Individual toggle button for a log level
 */
interface LevelToggleProps {
  level: LogLevel;
  isEnabled: boolean;
  onToggle: () => void;
}

const LevelToggle = memo(function LevelToggle({
  level,
  isEnabled,
  onToggle,
}: LevelToggleProps): React.ReactElement {
  const levelColor = LOG_LEVEL_COLORS[level];

  return (
    <Pressable
      onPress={onToggle}
      style={({ pressed }) => [
        styles.levelToggle,
        isEnabled && { backgroundColor: `${levelColor}30`, borderColor: levelColor },
        pressed && styles.levelTogglePressed,
      ]}
      accessibilityRole="checkbox"
      accessibilityLabel={`${level} logs`}
      accessibilityState={{ checked: isEnabled }}
    >
      <View
        style={[
          styles.levelDot,
          { backgroundColor: isEnabled ? levelColor : colors.gray600 },
        ]}
      />
      <Text
        style={[
          styles.levelToggleText,
          isEnabled && { color: levelColor },
        ]}
      >
        {level.toUpperCase()}
      </Text>
    </Pressable>
  );
});

export const LogFilter = memo(LogFilterComponent);

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  levelRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  levelToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  levelTogglePressed: {
    opacity: 0.7,
  },
  levelDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  levelToggleText: {
    color: colors.gray500,
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logCount: {
    color: colors.gray500,
    fontSize: 12,
  },
  spacer: {
    flex: 1,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    marginLeft: 8,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
  },
  actionButtonPressed: {
    opacity: 0.7,
  },
  actionButtonActive: {
    borderColor: colors.info,
    backgroundColor: `${colors.info}20`,
  },
  actionButtonText: {
    color: colors.gray400,
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  actionButtonTextActive: {
    color: colors.info,
  },
});

export default LogFilter;
