/**
 * LogFilter - Filter controls for log levels
 *
 * Toggle buttons for each log level, clear logs button,
 * and pause/resume streaming toggle.
 */

import React from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import type { LogLevel } from '../../lib/types';

/** All available log levels */
const LOG_LEVELS: LogLevel[] = ['debug', 'info', 'warn', 'error'];

interface LogFilterProps {
  /** Currently enabled log levels */
  enabledLevels: Set<LogLevel>;
  /** Callback when level is toggled */
  onToggleLevel: (level: LogLevel) => void;
  /** Whether streaming is paused */
  isPaused: boolean;
  /** Callback to toggle pause state */
  onTogglePause: () => void;
  /** Callback to clear all logs */
  onClearLogs: () => void;
  /** Number of logs currently displayed */
  logCount: number;
}

/**
 * Get level button colors
 */
function getLevelColors(
  level: LogLevel,
  enabled: boolean
): { bg: string; text: string; border: string } {
  if (!enabled) {
    return {
      bg: 'bg-transparent',
      text: 'text-textSecondary',
      border: 'border-border',
    };
  }

  const colorMap: Record<LogLevel, { bg: string; text: string; border: string }> = {
    debug: { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500' },
    info: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500' },
    warn: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500' },
    error: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500' },
  };
  return colorMap[level];
}

/**
 * LogFilter component
 */
export function LogFilter({
  enabledLevels,
  onToggleLevel,
  isPaused,
  onTogglePause,
  onClearLogs,
  logCount,
}: LogFilterProps): React.JSX.Element {
  return (
    <View className="bg-surface border-b border-border">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 12, paddingVertical: 8 }}
      >
        {/* Log level toggles */}
        {LOG_LEVELS.map((level) => {
          const isEnabled = enabledLevels.has(level);
          const colors = getLevelColors(level, isEnabled);
          return (
            <Pressable
              key={level}
              onPress={() => onToggleLevel(level)}
              className={`px-3 py-1.5 rounded-full border mr-2 ${colors.bg} ${colors.border} active:opacity-70`}
            >
              <Text className={`text-xs font-medium uppercase ${colors.text}`}>
                {level}
              </Text>
            </Pressable>
          );
        })}

        {/* Separator */}
        <View className="w-px h-6 bg-border mx-2 self-center" />

        {/* Pause/Resume toggle */}
        <Pressable
          onPress={onTogglePause}
          className={`px-3 py-1.5 rounded-full border mr-2 active:opacity-70 ${
            isPaused
              ? 'bg-yellow-500/20 border-yellow-500'
              : 'bg-green-500/20 border-green-500'
          }`}
        >
          <Text
            className={`text-xs font-medium ${
              isPaused ? 'text-yellow-400' : 'text-green-400'
            }`}
          >
            {isPaused ? '▶ Resume' : '⏸ Pause'}
          </Text>
        </Pressable>

        {/* Clear logs button */}
        <Pressable
          onPress={onClearLogs}
          className="px-3 py-1.5 rounded-full border border-border bg-transparent active:opacity-70"
        >
          <Text className="text-xs font-medium text-textSecondary">
            Clear ({logCount})
          </Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

export default LogFilter;
