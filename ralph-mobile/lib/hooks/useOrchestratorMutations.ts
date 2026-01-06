/**
 * useOrchestratorMutations Hook
 *
 * React Query mutation hooks for orchestrator actions:
 * start, stop, pause, resume.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  startOrchestrator,
  stopOrchestrator,
  pauseOrchestrator,
  resumeOrchestrator,
} from '../api/client';
import type {
  StartOrchestratorRequest,
  StartOrchestratorResponse,
  Orchestrator,
} from '../types';
import { orchestratorsQueryKey } from './useOrchestrators';
import { orchestratorQueryKey } from './useOrchestrator';

/**
 * Hook for starting a new orchestration
 *
 * @returns Mutation for starting orchestrator
 */
export function useStartOrchestrator() {
  const queryClient = useQueryClient();

  return useMutation<StartOrchestratorResponse, Error, StartOrchestratorRequest>({
    mutationFn: startOrchestrator,
    onSuccess: (data) => {
      // Add the new orchestrator to the cache
      queryClient.setQueryData<Orchestrator[]>(
        orchestratorsQueryKey,
        (old) => old ? [...old, data.orchestrator] : [data.orchestrator]
      );
      // Also set it as a single orchestrator query
      queryClient.setQueryData(
        orchestratorQueryKey(data.orchestrator.id),
        data.orchestrator
      );
      // Invalidate to refetch fresh data
      queryClient.invalidateQueries({ queryKey: orchestratorsQueryKey });
    },
  });
}

/**
 * Mutation context type for rollback support
 */
interface MutationContext {
  previousOrchestrator: Orchestrator | undefined;
}

/**
 * Hook for stopping an orchestration
 *
 * @returns Mutation for stopping orchestrator
 */
export function useStopOrchestrator() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string, MutationContext>({
    mutationFn: stopOrchestrator,
    onMutate: async (id) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: orchestratorQueryKey(id) });
      await queryClient.cancelQueries({ queryKey: orchestratorsQueryKey });

      // Snapshot previous value
      const previousOrchestrator = queryClient.getQueryData<Orchestrator>(
        orchestratorQueryKey(id)
      );

      // Optimistically update status
      if (previousOrchestrator) {
        queryClient.setQueryData<Orchestrator>(orchestratorQueryKey(id), {
          ...previousOrchestrator,
          status: 'completed',
        });
      }

      return { previousOrchestrator };
    },
    onError: (_err, id, context) => {
      // Rollback on error
      if (context?.previousOrchestrator) {
        queryClient.setQueryData(
          orchestratorQueryKey(id),
          context.previousOrchestrator
        );
      }
    },
    onSettled: (_data, _error, id) => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey: orchestratorQueryKey(id) });
      queryClient.invalidateQueries({ queryKey: orchestratorsQueryKey });
    },
  });
}

/**
 * Hook for pausing an orchestration
 *
 * @returns Mutation for pausing orchestrator
 */
export function usePauseOrchestrator() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string, MutationContext>({
    mutationFn: pauseOrchestrator,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: orchestratorQueryKey(id) });

      const previousOrchestrator = queryClient.getQueryData<Orchestrator>(
        orchestratorQueryKey(id)
      );

      // Optimistically update status to paused
      if (previousOrchestrator) {
        queryClient.setQueryData<Orchestrator>(orchestratorQueryKey(id), {
          ...previousOrchestrator,
          status: 'paused',
        });
      }

      return { previousOrchestrator };
    },
    onError: (_err, id, context) => {
      if (context?.previousOrchestrator) {
        queryClient.setQueryData(
          orchestratorQueryKey(id),
          context.previousOrchestrator
        );
      }
    },
    onSettled: (_data, _error, id) => {
      queryClient.invalidateQueries({ queryKey: orchestratorQueryKey(id) });
      queryClient.invalidateQueries({ queryKey: orchestratorsQueryKey });
    },
  });
}

/**
 * Hook for resuming a paused orchestration
 *
 * @returns Mutation for resuming orchestrator
 */
export function useResumeOrchestrator() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string, MutationContext>({
    mutationFn: resumeOrchestrator,
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: orchestratorQueryKey(id) });

      const previousOrchestrator = queryClient.getQueryData<Orchestrator>(
        orchestratorQueryKey(id)
      );

      // Optimistically update status to running
      if (previousOrchestrator) {
        queryClient.setQueryData<Orchestrator>(orchestratorQueryKey(id), {
          ...previousOrchestrator,
          status: 'running',
        });
      }

      return { previousOrchestrator };
    },
    onError: (_err, id, context) => {
      if (context?.previousOrchestrator) {
        queryClient.setQueryData(
          orchestratorQueryKey(id),
          context.previousOrchestrator
        );
      }
    },
    onSettled: (_data, _error, id) => {
      queryClient.invalidateQueries({ queryKey: orchestratorQueryKey(id) });
      queryClient.invalidateQueries({ queryKey: orchestratorsQueryKey });
    },
  });
}

/**
 * Combined hook returning all mutation hooks
 *
 * @returns Object with all orchestrator mutations
 */
export function useOrchestratorMutations() {
  const start = useStartOrchestrator();
  const stop = useStopOrchestrator();
  const pause = usePauseOrchestrator();
  const resume = useResumeOrchestrator();

  return {
    start,
    stop,
    pause,
    resume,
    isAnyLoading: start.isPending || stop.isPending || pause.isPending || resume.isPending,
  };
}
