/**
 * useOrchestratorLogs Hook
 *
 * React Query hook for fetching orchestrator logs with pagination.
 * For real-time log streaming, use WebSocket (lib/api/websocket.ts).
 */

import { useQuery, useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { getOrchestratorLogs } from '../api/client';
import type { LogEntry } from '../types';

/**
 * Get query key for orchestrator logs
 */
export const orchestratorLogsQueryKey = (id: string) => ['orchestrator', id, 'logs'] as const;

/**
 * Default log fetch limit
 */
const DEFAULT_LOG_LIMIT = 100;

/**
 * Hook to fetch logs for an orchestrator
 *
 * @param id - Orchestrator ID
 * @param limit - Max number of logs to fetch
 * @param enabled - Whether to enable the query
 * @returns Query result with log entries
 */
export function useOrchestratorLogs(
  id: string,
  limit: number = DEFAULT_LOG_LIMIT,
  enabled: boolean = true
) {
  return useQuery<LogEntry[], Error>({
    queryKey: [...orchestratorLogsQueryKey(id), limit],
    queryFn: () => getOrchestratorLogs(id, limit),
    enabled: !!id && enabled,
    refetchInterval: 5000, // Poll for new logs
    staleTime: 1000,
  });
}

/**
 * Hook to fetch logs with infinite scrolling
 *
 * @param id - Orchestrator ID
 * @param pageSize - Number of logs per page
 * @returns Infinite query result
 */
export function useInfiniteOrchestratorLogs(id: string, pageSize: number = 50) {
  return useInfiniteQuery<LogEntry[], Error>({
    queryKey: [...orchestratorLogsQueryKey(id), 'infinite'],
    queryFn: ({ pageParam }) => getOrchestratorLogs(id, pageSize),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      // If we got a full page, there might be more
      return lastPage.length === pageSize ? allPages.length : undefined;
    },
    enabled: !!id,
    staleTime: 1000,
  });
}

/**
 * Hook to add a new log entry to the cache (for WebSocket updates)
 */
export function useAddLogToCache() {
  const queryClient = useQueryClient();

  return (orchestratorId: string, log: LogEntry) => {
    queryClient.setQueryData<LogEntry[]>(
      [...orchestratorLogsQueryKey(orchestratorId), DEFAULT_LOG_LIMIT],
      (old) => {
        if (!old) return [log];
        // Add new log and keep within limit
        const updated = [log, ...old];
        if (updated.length > DEFAULT_LOG_LIMIT) {
          updated.pop();
        }
        return updated;
      }
    );
  };
}

/**
 * Hook to invalidate logs cache
 */
export function useInvalidateLogs() {
  const queryClient = useQueryClient();

  return (orchestratorId: string) => {
    queryClient.invalidateQueries({
      queryKey: orchestratorLogsQueryKey(orchestratorId)
    });
  };
}

/**
 * Hook to clear logs from cache
 */
export function useClearLogsCache() {
  const queryClient = useQueryClient();

  return (orchestratorId: string) => {
    queryClient.removeQueries({
      queryKey: orchestratorLogsQueryKey(orchestratorId)
    });
  };
}
