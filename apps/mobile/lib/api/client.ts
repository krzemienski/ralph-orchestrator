/**
 * Ralph Mobile - REST API Client
 *
 * Provides typed functions for communicating with the Ralph backend API.
 * All functions return ApiResult<T> for consistent error handling.
 */

import type {
  ApiError,
  ApiResult,
  LogEntry,
  Orchestrator,
  StartOrchestratorRequest,
  StartOrchestratorResponse,
  Task,
} from '../types';

// === Configuration ===

let baseUrl = 'http://localhost:8420';

/**
 * Get the current API base URL
 */
export function getBaseUrl(): string {
  return baseUrl;
}

/**
 * Set the API base URL (for settings screen)
 */
export function setBaseUrl(url: string): void {
  // Remove trailing slash if present
  baseUrl = url.replace(/\/$/, '');
}

// === Internal Helpers ===

/**
 * Standard headers for all API requests
 */
function getHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
}

/**
 * Parse error response from API
 */
async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const data = await response.json();
    return {
      error: data.error || `HTTP ${response.status}`,
      code: data.code || `HTTP_${response.status}`,
      details: data.details,
    };
  } catch {
    return {
      error: `HTTP ${response.status}: ${response.statusText}`,
      code: `HTTP_${response.status}`,
    };
  }
}

/**
 * Create network error response
 */
function createNetworkError(error: unknown): ApiError {
  const message = error instanceof Error ? error.message : 'Unknown network error';
  return {
    error: message,
    code: 'NETWORK_ERROR',
  };
}

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResult<T>> {
  const url = `${baseUrl}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...getHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await parseErrorResponse(response);
      return { success: false, error };
    }

    const data = await response.json();
    return { success: true, data: data as T };
  } catch (error) {
    return { success: false, error: createNetworkError(error) };
  }
}

// === Orchestrator API Functions ===

/**
 * Fetch all orchestrators
 * GET /api/orchestrators
 */
export async function getOrchestrators(): Promise<ApiResult<Orchestrator[]>> {
  return apiFetch<Orchestrator[]>('/api/orchestrators', { method: 'GET' });
}

/**
 * Fetch a single orchestrator by ID
 * GET /api/orchestrators/:id
 */
export async function getOrchestrator(id: string): Promise<ApiResult<Orchestrator>> {
  return apiFetch<Orchestrator>(`/api/orchestrators/${id}`, { method: 'GET' });
}

/**
 * Start a new orchestration
 * POST /api/orchestrators
 */
export async function startOrchestrator(
  request: StartOrchestratorRequest
): Promise<ApiResult<StartOrchestratorResponse>> {
  return apiFetch<StartOrchestratorResponse>('/api/orchestrators', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Stop an orchestration
 * DELETE /api/orchestrators/:id
 */
export async function stopOrchestrator(id: string): Promise<ApiResult<void>> {
  return apiFetch<void>(`/api/orchestrators/${id}`, { method: 'DELETE' });
}

/**
 * Pause a running orchestration
 * POST /api/orchestrators/:id/pause
 */
export async function pauseOrchestrator(id: string): Promise<ApiResult<void>> {
  return apiFetch<void>(`/api/orchestrators/${id}/pause`, { method: 'POST' });
}

/**
 * Resume a paused orchestration
 * POST /api/orchestrators/:id/resume
 */
export async function resumeOrchestrator(id: string): Promise<ApiResult<void>> {
  return apiFetch<void>(`/api/orchestrators/${id}/resume`, { method: 'POST' });
}

/**
 * Fetch logs for an orchestrator
 * GET /api/orchestrators/:id/logs
 */
export async function getOrchestratorLogs(
  id: string,
  limit?: number
): Promise<ApiResult<LogEntry[]>> {
  const query = limit ? `?limit=${limit}` : '';
  return apiFetch<LogEntry[]>(`/api/orchestrators/${id}/logs${query}`, {
    method: 'GET',
  });
}

/**
 * Fetch tasks for an orchestrator
 * GET /api/orchestrators/:id/tasks
 */
export async function getOrchestratorTasks(id: string): Promise<ApiResult<Task[]>> {
  return apiFetch<Task[]>(`/api/orchestrators/${id}/tasks`, { method: 'GET' });
}

// === Health & Connection ===

/**
 * Health check response type
 */
export interface HealthCheckResponse {
  status: string;
  version?: string;
}

/**
 * Test connection to the API server
 * GET /api/health
 */
export async function testConnection(): Promise<ApiResult<HealthCheckResponse>> {
  return apiFetch<HealthCheckResponse>('/api/health', { method: 'GET' });
}
