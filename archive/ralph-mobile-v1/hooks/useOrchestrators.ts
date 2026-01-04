/**
 * @fileoverview Hook for fetching and managing orchestrator data
 * Plan 05-01: Orchestrator List View
 */

import { useState, useEffect, useCallback } from 'react';
import type { Orchestrator } from '../lib/types';
import { fetchOrchestrators } from '../lib/orchestratorApi';

interface UseOrchestratorsResult {
  orchestrators: Orchestrator[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage orchestrator list
 * Auto-refreshes every 5 seconds when active
 */
export function useOrchestrators(): UseOrchestratorsResult {
  const [orchestrators, setOrchestrators] = useState<Orchestrator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      setError(null);
      const response = await fetchOrchestrators();
      setOrchestrators(response.orchestrators);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch orchestrators');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();

    // Auto-refresh every 5 seconds
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { orchestrators, loading, error, refetch };
}

export default useOrchestrators;
