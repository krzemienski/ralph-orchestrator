/**
 * useOrchestrator Hook
 *
 * React Query hook for fetching a single orchestrator by ID.
 * Supports real-time updates via polling or manual refresh.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getOrchestrator, getOrchestratorTasks } from '../api/client';
import type { Orchestrator, Task } from '../types';

/**
 * Get query key for a single orchestrator
 */
export const orchestratorQueryKey = (id: string) => ['orchestrator', id] as const;

/**
 * Get query key for orchestrator tasks
 */
export const orchestratorTasksQueryKey = (id: string) => ['orchestrator', id, 'tasks'] as const;

/**
 * Hook to fetch a single orchestrator by ID
 *
 * @param id - Orchestrator ID
 * @param refetchInterval - Polling interval in ms (default: 5000 for active, 0 for inactive)
 * @returns Query result with orchestrator data
 */
export function useOrchestrator(id: string, refetchInterval: number = 5000) {
  return useQuery<Orchestrator, Error>({
    queryKey: orchestratorQueryKey(id),
    queryFn: () => getOrchestrator(id),
    enabled: !!id,
    refetchInterval,
    staleTime: 2000,
  });
}

/**
 * Hook to fetch tasks for an orchestrator
 *
 * @param id - Orchestrator ID
 * @param enabled - Whether to enable the query
 * @returns Query result with tasks data
 */
export function useOrchestratorTasks(id: string, enabled: boolean = true) {
  return useQuery<Task[], Error>({
    queryKey: orchestratorTasksQueryKey(id),
    queryFn: () => getOrchestratorTasks(id),
    enabled: !!id && enabled,
    refetchInterval: 5000,
    staleTime: 2000,
  });
}

/**
 * Hook to invalidate orchestrator cache
 */
export function useInvalidateOrchestrator() {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.invalidateQueries({ queryKey: orchestratorQueryKey(id) });
    queryClient.invalidateQueries({ queryKey: orchestratorTasksQueryKey(id) });
  };
}

/**
 * Hook to update orchestrator in cache optimistically
 */
export function useUpdateOrchestratorCache() {
  const queryClient = useQueryClient();

  return (id: string, updater: (old: Orchestrator | undefined) => Orchestrator | undefined) => {
    queryClient.setQueryData<Orchestrator>(orchestratorQueryKey(id), updater);
  };
}
