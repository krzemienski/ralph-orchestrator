/**
 * LogList Component
 *
 * Virtualized list of log entries with auto-scroll behavior.
 * Integrates LogEntry and LogFilter components.
 */

import React, { useRef, useCallback, useState, useEffect, memo } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  Text,
  NativeSyntheticEvent,
  NativeScrollEvent,
} from 'react-native';
import type { LogEntry as LogEntryType, LogLevel } from '../../lib/types';
import { LogEntry } from './LogEntry';
import { LogFilter } from './LogFilter';

interface LogListProps {
  /** Array of log entries to display */
  logs: LogEntryType[];
  /** Whether WebSocket streaming is paused */
  isPaused: boolean;
  /** Callback when pause/resume is toggled */
  onTogglePause: () => void;
  /** Callback when clear logs is pressed */
  onClearLogs: () => void;
  /** Whether to show empty state */
  showEmptyState?: boolean;
}

/**
 * Threshold in pixels from bottom to consider "at bottom"
 * Used for auto-scroll behavior
 */
const SCROLL_THRESHOLD = 100;

/**
 * Theme colors for dark mode
 */
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

/**
 * LogList - Virtualized list with filtering and auto-scroll
 *
 * Features:
 * - FlatList for efficient rendering of large log lists
 * - Log level filtering (debug, info, warn, error)
 * - Auto-scroll to bottom when new logs arrive (if at bottom)
 * - Scroll-lock when user scrolls up
 * - Filter controls header
 * - Empty state when no logs match filter
 */
function LogListComponent({
  logs,
  isPaused,
  onTogglePause,
  onClearLogs,
  showEmptyState = true,
}: LogListProps): React.ReactElement {
  const flatListRef = useRef<FlatList<LogEntryType>>(null);
  const [enabledLevels, setEnabledLevels] = useState<Set<LogLevel>>(
    new Set(['debug', 'info', 'warn', 'error'])
  );
  const [isAtBottom, setIsAtBottom] = useState(true);
  const previousLogCountRef = useRef(logs.length);

  /**
   * Filter logs based on enabled levels
   */
  const filteredLogs = logs.filter((log) => enabledLevels.has(log.level));

  /**
   * Toggle a log level filter
   */
  const handleToggleLevel = useCallback((level: LogLevel) => {
    setEnabledLevels((prev) => {
      const next = new Set(prev);
      if (next.has(level)) {
        // Don't allow disabling all levels
        if (next.size > 1) {
          next.delete(level);
        }
      } else {
        next.add(level);
      }
      return next;
    });
  }, []);

  /**
   * Track scroll position to enable/disable auto-scroll
   */
  const handleScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;
      const distanceFromBottom =
        contentSize.height - layoutMeasurement.height - contentOffset.y;
      setIsAtBottom(distanceFromBottom < SCROLL_THRESHOLD);
    },
    []
  );

  /**
   * Auto-scroll to bottom when new logs arrive (if at bottom)
   */
  useEffect(() => {
    if (
      isAtBottom &&
      filteredLogs.length > previousLogCountRef.current &&
      flatListRef.current
    ) {
      // Small delay to ensure content is rendered
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
    previousLogCountRef.current = filteredLogs.length;
  }, [filteredLogs.length, isAtBottom]);

  /**
   * Render individual log entry
   */
  const renderItem = useCallback(
    ({ item }: { item: LogEntryType }) => <LogEntry log={item} />,
    []
  );

  /**
   * Extract unique key for each item
   */
  const keyExtractor = useCallback((item: LogEntryType) => item.id, []);

  /**
   * Empty state component
   */
  const ListEmpty = useCallback(
    () =>
      showEmptyState ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Logs</Text>
          <Text style={styles.emptySubtitle}>
            {logs.length > 0
              ? 'No logs match the current filter'
              : 'Logs will appear here when available'}
          </Text>
        </View>
      ) : null,
    [logs.length, showEmptyState]
  );

  /**
   * Footer spacer for better UX
   */
  const ListFooter = useCallback(
    () => <View style={styles.footerSpacer} />,
    []
  );

  return (
    <View style={styles.container}>
      {/* Filter Controls */}
      <LogFilter
        enabledLevels={enabledLevels}
        onToggleLevel={handleToggleLevel}
        isPaused={isPaused}
        onTogglePause={onTogglePause}
        onClearLogs={onClearLogs}
        logCount={filteredLogs.length}
      />

      {/* Log List */}
      <FlatList
        ref={flatListRef}
        data={filteredLogs}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        ListEmptyComponent={ListEmpty}
        ListFooterComponent={ListFooter}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={true}
        onScroll={handleScroll}
        scrollEventThrottle={100}
        // Performance optimizations
        removeClippedSubviews={true}
        maxToRenderPerBatch={15}
        windowSize={10}
        initialNumToRender={20}
        // Accessibility
        accessibilityLabel="Log entries list"
        accessibilityHint="Scroll to view log entries. New logs appear at the bottom."
      />

      {/* Scroll indicator when not at bottom */}
      {!isAtBottom && filteredLogs.length > 0 && (
        <View style={styles.scrollIndicator}>
          <Text style={styles.scrollIndicatorText}>
            ↓ New logs below
          </Text>
        </View>
      )}
    </View>
  );
}

export const LogList = memo(LogListComponent);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  listContent: {
    padding: 12,
    flexGrow: 1,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    color: colors.gray400,
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtitle: {
    color: colors.gray500,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  footerSpacer: {
    height: 20,
  },
  scrollIndicator: {
    position: 'absolute',
    bottom: 16,
    alignSelf: 'center',
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.border,
  },
  scrollIndicatorText: {
    color: colors.gray400,
    fontSize: 12,
    fontWeight: '500',
  },
});

export default LogList;
