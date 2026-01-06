/**
 * Output Screen
 *
 * Real-time log viewer with WebSocket streaming support.
 * Features:
 * - Orchestrator selection dropdown
 * - Real-time log streaming via WebSocket
 * - Log level filtering
 * - Auto-scroll with scroll-lock behavior
 * - Pause/resume streaming
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useOrchestrators } from '../../lib/hooks/useOrchestrators';
import {
  useOrchestratorLogs,
  useAddLogToCache,
} from '../../lib/hooks/useOrchestratorLogs';
import { getWebSocket } from '../../lib/api/websocket';
import { LogList, OrchestratorSelector } from '../../components/output';
import type { LogEntry } from '../../lib/types';

/**
 * Theme colors for dark mode
 */
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  info: '#3b82f6',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

/**
 * OutputScreen - Real-time log viewer
 *
 * Flow:
 * 1. Fetch orchestrators list
 * 2. Auto-select first running orchestrator (or first if none running)
 * 3. Fetch existing logs via REST API
 * 4. Subscribe to WebSocket for real-time updates
 * 5. Display in virtualized list with filtering
 */
export default function OutputScreen() {
  const [selectedOrchestratorId, setSelectedOrchestratorId] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [localLogs, setLocalLogs] = useState<LogEntry[]>([]);
  const wsUnsubscribeRef = useRef<(() => void) | null>(null);

  // Fetch orchestrators list
  const {
    data: orchestrators,
    isLoading: isLoadingOrchestrators,
  } = useOrchestrators(15000); // Refresh every 15 seconds

  // Fetch logs for selected orchestrator
  const {
    data: fetchedLogs,
    isLoading: isLoadingLogs,
    refetch: refetchLogs,
  } = useOrchestratorLogs(
    selectedOrchestratorId || '',
    5000, // Refresh every 5 seconds as fallback
    !selectedOrchestratorId // Disable if no selection
  );

  // Cache mutation for WebSocket logs
  const addLogToCache = useAddLogToCache();

  /**
   * Auto-select first orchestrator (prefer running)
   */
  useEffect(() => {
    if (orchestrators && orchestrators.length > 0 && !selectedOrchestratorId) {
      // Prefer running orchestrator
      const runningOrchestrator = orchestrators.find((o) => o.status === 'running');
      const toSelect = runningOrchestrator || orchestrators[0];
      setSelectedOrchestratorId(toSelect.id);
    }
  }, [orchestrators, selectedOrchestratorId]);

  /**
   * Sync fetched logs to local state
   */
  useEffect(() => {
    if (fetchedLogs) {
      setLocalLogs(fetchedLogs);
    }
  }, [fetchedLogs]);

  /**
   * WebSocket subscription for real-time logs
   */
  useEffect(() => {
    if (!selectedOrchestratorId || isPaused) {
      // Cleanup existing subscription
      if (wsUnsubscribeRef.current) {
        wsUnsubscribeRef.current();
        wsUnsubscribeRef.current = null;
      }
      return;
    }

    const ws = getWebSocket();

    // Subscribe to log events
    const unsubscribe = ws.onLog((log: LogEntry) => {
      // Only add logs for selected orchestrator
      if (log.orchestrator_id === selectedOrchestratorId) {
        setLocalLogs((prev) => {
          // Check for duplicate
          if (prev.some((l) => l.id === log.id)) {
            return prev;
          }
          // Add to cache for React Query
          addLogToCache(selectedOrchestratorId, log);
          // Add to local state
          return [...prev, log];
        });
      }
    });

    wsUnsubscribeRef.current = unsubscribe;

    // Connect WebSocket if not already connected
    ws.connect(selectedOrchestratorId);

    return () => {
      if (wsUnsubscribeRef.current) {
        wsUnsubscribeRef.current();
        wsUnsubscribeRef.current = null;
      }
    };
  }, [selectedOrchestratorId, isPaused, addLogToCache]);

  /**
   * Handle orchestrator selection change
   */
  const handleSelectOrchestrator = useCallback((id: string) => {
    setSelectedOrchestratorId(id);
    setLocalLogs([]); // Clear logs when switching
  }, []);

  /**
   * Toggle pause/resume streaming
   */
  const handleTogglePause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  /**
   * Clear all logs
   */
  const handleClearLogs = useCallback(() => {
    setLocalLogs([]);
  }, []);

  // Loading state
  if (isLoadingOrchestrators) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.info} />
          <Text style={styles.loadingText}>Loading orchestrators...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // No orchestrators available
  if (!orchestrators || orchestrators.length === 0) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Orchestrators</Text>
          <Text style={styles.emptySubtitle}>
            Start an orchestration to view logs
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {/* Header with title */}
      <View style={styles.header}>
        <Text style={styles.title}>Output</Text>
        {isLoadingLogs && (
          <ActivityIndicator size="small" color={colors.info} />
        )}
      </View>

      {/* Orchestrator Selector */}
      <OrchestratorSelector
        orchestrators={orchestrators}
        selectedId={selectedOrchestratorId}
        onSelect={handleSelectOrchestrator}
      />

      {/* Log List */}
      <LogList
        logs={localLogs}
        isPaused={isPaused}
        onTogglePause={handleTogglePause}
        onClearLogs={handleClearLogs}
      />

      {/* Connection Status */}
      {isPaused && (
        <View style={styles.pausedBanner}>
          <Text style={styles.pausedText}>Streaming paused</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.white,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  loadingText: {
    color: colors.gray400,
    marginTop: 16,
    fontSize: 15,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyTitle: {
    color: colors.white,
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtitle: {
    color: colors.gray500,
    fontSize: 14,
    textAlign: 'center',
  },
  pausedBanner: {
    position: 'absolute',
    bottom: 16,
    alignSelf: 'center',
    backgroundColor: colors.surface,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pausedText: {
    color: colors.gray400,
    fontSize: 13,
    fontWeight: '500',
  },
});
