/**
 * Output Viewer Screen - Real-time log streaming
 *
 * Streams logs from orchestrators via WebSocket with filtering,
 * auto-scroll, and orchestrator selection.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { View, Text } from 'react-native';
import { useOrchestrators, useOrchestratorLogs } from '../../lib/hooks';
import {
  LogList,
  LogFilter,
  OrchestratorSelector,
  ConnectionStatus,
} from '../../components/output';
import { orchestratorWs as orchestratorWebSocket } from '../../lib/api/websocket';
import type { LogEntry, LogLevel } from '../../lib/types';

/** All log levels for initial filter state */
const ALL_LOG_LEVELS: LogLevel[] = ['debug', 'info', 'warn', 'error'];

/**
 * Output Viewer Screen Component
 */
export default function OutputScreen(): React.JSX.Element {
  // Orchestrator selection
  const { orchestrators, isLoading: isLoadingOrchestrators } = useOrchestrators({
    refetchInterval: 10_000,
  });
  const [selectedOrchestratorId, setSelectedOrchestratorId] = useState<string | null>(null);

  // Log state
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [enabledLevels, setEnabledLevels] = useState<Set<LogLevel>>(
    new Set(ALL_LOG_LEVELS)
  );
  const [isPaused, setIsPaused] = useState(false);

  // Connection state
  const [connectionState, setConnectionState] = useState<
    'connected' | 'connecting' | 'disconnected' | 'error'
  >('disconnected');
  const [connectionError, setConnectionError] = useState<string | undefined>();

  // WebSocket buffer for paused state
  const pausedLogsBuffer = useRef<LogEntry[]>([]);

  // Fetch initial logs when orchestrator selected
  const { logs: initialLogs, isLoading: isLoadingLogs } = useOrchestratorLogs(
    selectedOrchestratorId ?? '',
    { limit: 100, enabled: !!selectedOrchestratorId }
  );

  // Set initial logs when they load
  useEffect(() => {
    if (initialLogs.length > 0) {
      setLogs(initialLogs);
    }
  }, [initialLogs]);

  // Auto-select first running orchestrator if none selected
  useEffect(() => {
    if (!selectedOrchestratorId && orchestrators.length > 0) {
      const running = orchestrators.find((o) => o.status === 'running');
      setSelectedOrchestratorId(running?.id ?? orchestrators[0].id);
    }
  }, [orchestrators, selectedOrchestratorId]);

  // WebSocket connection management
  useEffect(() => {
    if (!selectedOrchestratorId) {
      setConnectionState('disconnected');
      return;
    }

    setConnectionState('connecting');
    setConnectionError(undefined);

    // Connect to WebSocket
    orchestratorWebSocket.connect(selectedOrchestratorId);

    // Set up callbacks
    orchestratorWebSocket.onLog((log: LogEntry) => {
      if (isPaused) {
        pausedLogsBuffer.current.push(log);
      } else {
        setLogs((prev) => [...prev, log]);
      }
    });

    orchestratorWebSocket.onConnectionStateChange((state) => {
      switch (state) {
        case 'connected':
          setConnectionState('connected');
          setConnectionError(undefined);
          break;
        case 'connecting':
          setConnectionState('connecting');
          break;
        case 'disconnected':
          setConnectionState('disconnected');
          break;
        case 'error':
          setConnectionState('error');
          setConnectionError('Connection failed');
          break;
      }
    });

    return () => {
      orchestratorWebSocket.disconnect();
      setConnectionState('disconnected');
    };
  }, [selectedOrchestratorId, isPaused]);

  // Flush buffered logs when resuming
  useEffect(() => {
    if (!isPaused && pausedLogsBuffer.current.length > 0) {
      setLogs((prev) => [...prev, ...pausedLogsBuffer.current]);
      pausedLogsBuffer.current = [];
    }
  }, [isPaused]);

  // Handlers
  const handleSelectOrchestrator = useCallback((id: string) => {
    setSelectedOrchestratorId(id);
    setLogs([]); // Clear logs when switching
  }, []);

  const handleToggleLevel = useCallback((level: LogLevel) => {
    setEnabledLevels((prev) => {
      const next = new Set(prev);
      if (next.has(level)) {
        next.delete(level);
      } else {
        next.add(level);
      }
      return next;
    });
  }, []);

  const handleTogglePause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  const handleClearLogs = useCallback(() => {
    setLogs([]);
    pausedLogsBuffer.current = [];
  }, []);

  return (
    <View className="flex-1 bg-background">
      {/* Header */}
      <View className="px-4 pt-4 pb-2 flex-row items-center justify-between">
        <Text className="text-2xl font-bold text-textPrimary">Output</Text>
        <ConnectionStatus state={connectionState} error={connectionError} />
      </View>

      {/* Orchestrator Selector */}
      <OrchestratorSelector
        orchestrators={orchestrators}
        selectedId={selectedOrchestratorId}
        onSelect={handleSelectOrchestrator}
        isLoading={isLoadingOrchestrators}
      />

      {/* Log Filter */}
      <LogFilter
        enabledLevels={enabledLevels}
        onToggleLevel={handleToggleLevel}
        isPaused={isPaused}
        onTogglePause={handleTogglePause}
        onClearLogs={handleClearLogs}
        logCount={logs.length}
      />

      {/* Log List */}
      <LogList
        logs={logs}
        enabledLevels={enabledLevels}
        isPaused={isPaused}
        isLoading={isLoadingLogs}
      />
    </View>
  );
}
