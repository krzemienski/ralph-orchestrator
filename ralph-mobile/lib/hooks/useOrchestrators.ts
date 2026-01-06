/**
 * useOrchestrators Hook
 *
 * React Query hook for fetching the list of all orchestrators.
 * Supports polling/refetch and caching.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getOrchestrators } from '../api/client';
import type { Orchestrator } from '../types';

/**
 * Query key for orchestrators list
 */
export const orchestratorsQueryKey = ['orchestrators'] as const;

/**
 * Hook to fetch all orchestrators with automatic polling
 *
 * @param refetchInterval - Polling interval in ms (default: 10000)
 * @returns Query result with orchestrators data
 */
export function useOrchestrators(refetchInterval: number = 10000) {
  return useQuery<Orchestrator[], Error>({
    queryKey: orchestratorsQueryKey,
    queryFn: getOrchestrators,
    refetchInterval,
    staleTime: 5000,
  });
}

/**
 * Hook to manually invalidate orchestrators cache
 */
export function useInvalidateOrchestrators() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: orchestratorsQueryKey });
  };
}

/**
 * Hook to prefetch orchestrators (useful before navigation)
 */
export function usePrefetchOrchestrators() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.prefetchQuery({
      queryKey: orchestratorsQueryKey,
      queryFn: getOrchestrators,
      staleTime: 5000,
    });
  };
}
