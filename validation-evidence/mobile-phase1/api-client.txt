/**
 * Ralph Mobile - REST API Client
 *
 * Handles all HTTP communication with the Ralph orchestrator backend.
 * Uses fetch API with proper error handling and typed responses.
 */

import {
  type Orchestrator,
  type StartOrchestratorRequest,
  type StartOrchestratorResponse,
  type LogEntry,
  type Task,
  type ApiError,
  type HealthCheckResponse,
  DEFAULT_SETTINGS,
} from '../types';

// =============================================================================
// CONFIGURATION
// =============================================================================

/**
 * Get the API base URL from environment or settings
 */
let apiBaseUrl = process.env.EXPO_PUBLIC_API_URL || DEFAULT_SETTINGS.apiUrl;

/**
 * Update the API base URL (used by settings screen)
 */
export function setApiBaseUrl(url: string): void {
  apiBaseUrl = url;
}

/**
 * Get current API base URL
 */
export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

// =============================================================================
// REQUEST HELPERS
// =============================================================================

/**
 * Custom error class for API errors
 */
export class ApiRequestError extends Error {
  public readonly code: string;
  public readonly details?: Record<string, unknown>;
  public readonly statusCode: number;

  constructor(error: ApiError, statusCode: number) {
    super(error.error);
    this.name = 'ApiRequestError';
    this.code = error.code;
    this.details = error.details;
    this.statusCode = statusCode;
  }
}

/**
 * Make an API request with proper error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${apiBaseUrl}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle non-JSON responses (like 204 No Content)
    if (response.status === 204) {
      return undefined as T;
    }

    const data = await response.json();

    if (!response.ok) {
      const apiError: ApiError = data as ApiError;
      throw new ApiRequestError(
        {
          error: apiError.error || 'Unknown error',
          code: apiError.code || 'UNKNOWN_ERROR',
          details: apiError.details,
        },
        response.status
      );
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error;
    }

    // Network error or other fetch error
    throw new ApiRequestError(
      {
        error: error instanceof Error ? error.message : 'Network error',
        code: 'NETWORK_ERROR',
      },
      0
    );
  }
}

// =============================================================================
// ORCHESTRATOR ENDPOINTS
// =============================================================================

/**
 * List all orchestrators
 */
export async function getOrchestrators(): Promise<Orchestrator[]> {
  return apiRequest<Orchestrator[]>('/api/orchestrators');
}

/**
 * Get a single orchestrator by ID
 */
export async function getOrchestrator(id: string): Promise<Orchestrator> {
  return apiRequest<Orchestrator>(`/api/orchestrators/${id}`);
}

/**
 * Start a new orchestration
 */
export async function startOrchestrator(
  request: StartOrchestratorRequest
): Promise<StartOrchestratorResponse> {
  return apiRequest<StartOrchestratorResponse>('/api/orchestrators', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Stop a running orchestration
 */
export async function stopOrchestrator(id: string): Promise<void> {
  return apiRequest<void>(`/api/orchestrators/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Pause a running orchestration
 */
export async function pauseOrchestrator(id: string): Promise<void> {
  return apiRequest<void>(`/api/orchestrators/${id}/pause`, {
    method: 'POST',
  });
}

/**
 * Resume a paused orchestration
 */
export async function resumeOrchestrator(id: string): Promise<void> {
  return apiRequest<void>(`/api/orchestrators/${id}/resume`, {
    method: 'POST',
  });
}

// =============================================================================
// LOG ENDPOINTS
// =============================================================================

/**
 * Get logs for an orchestrator
 */
export async function getOrchestratorLogs(
  id: string,
  limit?: number
): Promise<LogEntry[]> {
  const params = limit ? `?limit=${limit}` : '';
  return apiRequest<LogEntry[]>(`/api/orchestrators/${id}/logs${params}`);
}

// =============================================================================
// TASK ENDPOINTS
// =============================================================================

/**
 * Get tasks for an orchestrator
 */
export async function getOrchestratorTasks(id: string): Promise<Task[]> {
  return apiRequest<Task[]>(`/api/orchestrators/${id}/tasks`);
}

// =============================================================================
// HEALTH CHECK
// =============================================================================

/**
 * Check server health
 */
export async function checkHealth(): Promise<HealthCheckResponse> {
  return apiRequest<HealthCheckResponse>('/api/health');
}

/**
 * Test connection to server
 * Returns true if server is healthy, false otherwise
 */
export async function testConnection(): Promise<boolean> {
  try {
    const health = await checkHealth();
    return health.status === 'healthy';
  } catch {
    return false;
  }
}
