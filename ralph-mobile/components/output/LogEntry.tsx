/**
 * LogEntry Component
 *
 * Individual log item displaying timestamp, level badge, and message.
 * Supports expandable metadata section on tap.
 */

import React, { useState, useCallback, memo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { LogEntry as LogEntryType, LogLevel } from '../../lib/types';
import { LOG_LEVEL_COLORS } from '../../lib/types';

interface LogEntryProps {
  /** Log entry data */
  log: LogEntryType;
  /** Whether to show the full timestamp or just time */
  showFullTimestamp?: boolean;
}

/**
 * Format timestamp to HH:MM:SS.mmm format
 */
function formatTimestamp(timestamp: string, full: boolean = false): string {
  try {
    const date = new Date(timestamp);
    if (full) {
      return date.toLocaleString();
    }
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');
    const ms = date.getMilliseconds().toString().padStart(3, '0');
    return `${hours}:${minutes}:${seconds}.${ms}`;
  } catch {
    return timestamp;
  }
}

/**
 * Get display text for log level
 */
function getLevelText(level: LogLevel): string {
  return level.toUpperCase();
}

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
};

/**
 * LogEntry - Displays a single log item with expandable metadata
 *
 * Features:
 * - Color-coded level badge (debug=gray, info=blue, warn=yellow, error=red)
 * - Timestamp in HH:MM:SS.mmm format
 * - Word-wrapped message text
 * - Expandable metadata section when tapped
 * - Memoized for FlatList performance
 */
function LogEntryComponent({
  log,
  showFullTimestamp = false,
}: LogEntryProps): React.ReactElement {
  const [expanded, setExpanded] = useState(false);

  const hasMetadata = log.metadata && Object.keys(log.metadata).length > 0;

  const handlePress = useCallback(() => {
    if (hasMetadata) {
      setExpanded((prev) => !prev);
    }
  }, [hasMetadata]);

  const levelColor = LOG_LEVEL_COLORS[log.level];

  return (
    <Pressable
      onPress={handlePress}
      style={({ pressed }) => [
        styles.container,
        hasMetadata && pressed && styles.containerPressed,
      ]}
      disabled={!hasMetadata}
      accessibilityRole={hasMetadata ? 'button' : 'text'}
      accessibilityLabel={`${log.level} log: ${log.message}`}
      accessibilityHint={hasMetadata ? 'Double tap to expand metadata' : undefined}
    >
      {/* Header Row: Level Badge + Timestamp */}
      <View style={styles.header}>
        <View style={[styles.levelBadge, { backgroundColor: levelColor }]}>
          <Text style={styles.levelText}>{getLevelText(log.level)}</Text>
        </View>
        <Text style={styles.timestamp}>
          {formatTimestamp(log.timestamp, showFullTimestamp)}
        </Text>
        {hasMetadata && (
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={16}
            color={colors.gray500}
            style={styles.expandIcon}
          />
        )}
      </View>

      {/* Message */}
      <Text style={styles.message} selectable>
        {log.message}
      </Text>

      {/* Expandable Metadata Section */}
      {expanded && hasMetadata && (
        <View style={styles.metadataContainer}>
          <Text style={styles.metadataLabel}>Metadata:</Text>
          <View style={styles.metadataContent}>
            {Object.entries(log.metadata!).map(([key, value]) => (
              <View key={key} style={styles.metadataRow}>
                <Text style={styles.metadataKey}>{key}:</Text>
                <Text style={styles.metadataValue} selectable>
                  {typeof value === 'object'
                    ? JSON.stringify(value, null, 2)
                    : String(value)}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </Pressable>
  );
}

/**
 * Memoized LogEntry for FlatList performance
 * Only re-renders when log ID changes
 */
export const LogEntry = memo(LogEntryComponent, (prevProps, nextProps) => {
  return prevProps.log.id === nextProps.log.id;
});

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: 12,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  containerPressed: {
    backgroundColor: colors.surfaceHover,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  levelBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 8,
  },
  levelText: {
    color: colors.white,
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  timestamp: {
    color: colors.gray500,
    fontSize: 12,
    fontFamily: 'monospace',
    flex: 1,
  },
  expandIcon: {
    marginLeft: 4,
  },
  message: {
    color: colors.gray300,
    fontSize: 13,
    lineHeight: 18,
  },
  metadataContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  metadataLabel: {
    color: colors.gray500,
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  metadataContent: {
    backgroundColor: colors.background,
    borderRadius: 6,
    padding: 10,
  },
  metadataRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  metadataKey: {
    color: colors.gray400,
    fontSize: 12,
    fontFamily: 'monospace',
    marginRight: 8,
  },
  metadataValue: {
    color: colors.gray300,
    fontSize: 12,
    fontFamily: 'monospace',
    flex: 1,
  },
});

export default LogEntry;
