/**
 * @fileoverview API functions for controlling orchestrators
 * Plan 06-01: Start Orchestration UI
 * Plan 06-02: Stop/Pause/Resume Controls
 *
 * Provides functions to start, stop, pause, and resume orchestrations
 */

import { apiClient, getAuthHeaders } from './api';

/**
 * Request to start a new orchestrator
 */
export interface StartOrchestratorRequest {
  prompt_file: string;
  max_iterations?: number;
  max_runtime?: number;
  auto_commit?: boolean;
}

/**
 * Response from starting an orchestrator
 */
export interface StartOrchestratorResponse {
  instance_id: string;
  status: string;
  port?: number;
}

/**
 * Start a new orchestrator
 */
export async function startOrchestrator(
  request: StartOrchestratorRequest
): Promise<StartOrchestratorResponse> {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${apiClient.baseURL}/api/orchestrators`, {
    method: 'POST',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start orchestrator');
  }

  return response.json();
}

/**
 * Response from control operations (stop/pause/resume)
 */
export interface ControlResponse {
  instance_id: string;
  status: string;
  message?: string;
}

/**
 * Stop a running or paused orchestrator
 */
export async function stopOrchestrator(instanceId: string): Promise<ControlResponse> {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${apiClient.baseURL}/api/orchestrators/${instanceId}/stop`, {
    method: 'POST',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stop orchestrator');
  }

  return response.json();
}

/**
 * Pause a running orchestrator
 */
export async function pauseOrchestrator(instanceId: string): Promise<ControlResponse> {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${apiClient.baseURL}/api/orchestrators/${instanceId}/pause`, {
    method: 'POST',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to pause orchestrator');
  }

  return response.json();
}

/**
 * Resume a paused orchestrator
 */
export async function resumeOrchestrator(instanceId: string): Promise<ControlResponse> {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${apiClient.baseURL}/api/orchestrators/${instanceId}/resume`, {
    method: 'POST',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to resume orchestrator');
  }

  return response.json();
}
