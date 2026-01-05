/**
 * LogList - Virtualized list of log entries with auto-scroll
 *
 * Displays logs in a FlatList with auto-scroll to bottom for new logs.
 * Scroll-lock pauses auto-scroll when user scrolls up.
 */

import React, { useRef, useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, ActivityIndicator } from 'react-native';
import type { ListRenderItem, NativeSyntheticEvent, NativeScrollEvent } from 'react-native';
import type { LogEntry as LogEntryType, LogLevel } from '../../lib/types';
import { LogEntry } from './LogEntry';

interface LogListProps {
  /** Log entries to display */
  logs: LogEntryType[];
  /** Currently enabled log levels */
  enabledLevels: Set<LogLevel>;
  /** Whether streaming is paused */
  isPaused: boolean;
  /** Whether initial data is loading */
  isLoading?: boolean;
}

/**
 * LogList component
 */
export function LogList({
  logs,
  enabledLevels,
  isPaused,
  isLoading = false,
}: LogListProps): React.JSX.Element {
  const flatListRef = useRef<FlatList<LogEntryType>>(null);
  const [isScrolledUp, setIsScrolledUp] = useState(false);
  const lastLogCount = useRef(logs.length);

  // Filter logs by enabled levels
  const filteredLogs = logs.filter((log) => enabledLevels.has(log.level));

  // Auto-scroll to bottom when new logs arrive (if not scrolled up)
  useEffect(() => {
    if (
      filteredLogs.length > lastLogCount.current &&
      !isScrolledUp &&
      !isPaused &&
      flatListRef.current
    ) {
      // Use setTimeout to ensure list has updated
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
    lastLogCount.current = filteredLogs.length;
  }, [filteredLogs.length, isScrolledUp, isPaused]);

  const handleScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;
      const isAtBottom = layoutMeasurement.height + contentOffset.y >= contentSize.height - 100;
      setIsScrolledUp(!isAtBottom);
    },
    []
  );

  const handleScrollToEnd = useCallback(() => {
    flatListRef.current?.scrollToEnd({ animated: true });
    setIsScrolledUp(false);
  }, []);

  const renderItem: ListRenderItem<LogEntryType> = useCallback(
    ({ item }) => <LogEntry log={item} />,
    []
  );

  const keyExtractor = useCallback((item: LogEntryType) => item.id, []);

  // Loading state
  if (isLoading && logs.length === 0) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text className="text-textSecondary mt-4">Loading logs...</Text>
      </View>
    );
  }

  // Empty state
  if (filteredLogs.length === 0) {
    return (
      <View className="flex-1 bg-background items-center justify-center p-8">
        <Text className="text-4xl mb-3">📝</Text>
        <Text className="text-base text-textSecondary text-center">
          {logs.length === 0
            ? 'No logs yet'
            : 'No logs match the current filters'}
        </Text>
        <Text className="text-sm text-textSecondary text-center mt-2">
          {logs.length === 0
            ? 'Logs will appear here when the orchestrator runs'
            : 'Try enabling more log levels'}
        </Text>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-background relative">
      <FlatList
        ref={flatListRef}
        data={filteredLogs}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        onScroll={handleScroll}
        scrollEventThrottle={100}
        showsVerticalScrollIndicator={true}
        initialNumToRender={20}
        maxToRenderPerBatch={20}
        windowSize={10}
        removeClippedSubviews={true}
        maintainVisibleContentPosition={{
          minIndexForVisible: 0,
          autoscrollToTopThreshold: 10,
        }}
      />

      {/* Scroll-to-bottom button when scrolled up */}
      {isScrolledUp && (
        <View className="absolute bottom-4 right-4">
          <View
            className="bg-blue-500 rounded-full px-4 py-2 flex-row items-center shadow-lg"
            style={{
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.25,
              shadowRadius: 4,
              elevation: 5,
            }}
          >
            <Text
              className="text-white font-medium"
              onPress={handleScrollToEnd}
            >
              ↓ New logs
            </Text>
          </View>
        </View>
      )}

      {/* Paused indicator */}
      {isPaused && (
        <View className="absolute top-2 left-1/2 -translate-x-1/2">
          <View className="bg-yellow-500/90 rounded-full px-3 py-1">
            <Text className="text-black text-xs font-medium">⏸ Paused</Text>
          </View>
        </View>
      )}
    </View>
  );
}

export default LogList;
