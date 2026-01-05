/**
 * LogEntry - Individual log item component
 *
 * Displays a single log entry with timestamp, level badge, message,
 * and expandable metadata section.
 */

import React, { useState, useCallback } from 'react';
import { View, Text, Pressable } from 'react-native';
import type { LogEntry as LogEntryType, LogLevel } from '../../lib/types';

interface LogEntryProps {
  /** Log entry data */
  log: LogEntryType;
}

/**
 * Get log level badge color
 */
function getLevelColor(level: LogLevel): {
  bg: string;
  text: string;
} {
  const colorMap: Record<LogLevel, { bg: string; text: string }> = {
    debug: { bg: 'bg-gray-500/20', text: 'text-gray-400' },
    info: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
    warn: { bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
    error: { bg: 'bg-red-500/20', text: 'text-red-400' },
  };
  return colorMap[level];
}

/**
 * Format timestamp to HH:MM:SS.mmm
 */
function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  const seconds = date.getSeconds().toString().padStart(2, '0');
  const ms = date.getMilliseconds().toString().padStart(3, '0');
  return `${hours}:${minutes}:${seconds}.${ms}`;
}

/**
 * Format metadata for display
 */
function formatMetadata(metadata: Record<string, unknown>): string {
  return JSON.stringify(metadata, null, 2);
}

/**
 * LogEntry component
 */
export function LogEntry({ log }: LogEntryProps): React.JSX.Element {
  const [expanded, setExpanded] = useState(false);
  const levelColors = getLevelColor(log.level);
  const hasMetadata = log.metadata && Object.keys(log.metadata).length > 0;

  const handlePress = useCallback(() => {
    if (hasMetadata) {
      setExpanded((prev) => !prev);
    }
  }, [hasMetadata]);

  return (
    <Pressable
      onPress={handlePress}
      disabled={!hasMetadata}
      className="py-2 px-3 border-b border-border active:bg-surface"
    >
      {/* Main row */}
      <View className="flex-row items-start">
        {/* Timestamp */}
        <Text className="text-xs text-textSecondary font-mono mr-2 mt-0.5">
          {formatTimestamp(log.timestamp)}
        </Text>

        {/* Level badge */}
        <View className={`px-1.5 py-0.5 rounded mr-2 ${levelColors.bg}`}>
          <Text className={`text-xs font-medium uppercase ${levelColors.text}`}>
            {log.level}
          </Text>
        </View>

        {/* Message */}
        <Text className="flex-1 text-sm text-textPrimary" selectable>
          {log.message}
        </Text>

        {/* Expand indicator */}
        {hasMetadata && (
          <Text className="text-textSecondary ml-2">
            {expanded ? '▼' : '▶'}
          </Text>
        )}
      </View>

      {/* Expanded metadata */}
      {expanded && log.metadata && (
        <View className="mt-2 p-2 bg-surface rounded-lg ml-16">
          <Text className="text-xs text-textSecondary font-mono" selectable>
            {formatMetadata(log.metadata)}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

export default LogEntry;
