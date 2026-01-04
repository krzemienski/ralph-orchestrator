/**
 * @fileoverview API functions for orchestrator data
 * Plan 05-01: Orchestrator List View
 */

import { apiClient, getAuthHeaders } from './api';
import type { Orchestrator, OrchestratorsResponse, OrchestratorDetail, LogEntry } from './types';

/**
 * Response for log fetching
 */
export interface LogsResponse {
  logs: LogEntry[];
}

/**
 * Options for fetching logs
 */
export interface FetchLogsOptions {
  limit?: number;
  offset?: number;
}

/**
 * Fetch all orchestrators from the API
 */
export async function fetchOrchestrators(): Promise<OrchestratorsResponse> {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${apiClient.baseURL}/api/orchestrators`, {
    method: 'GET',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch orchestrators');
  }

  return response.json();
}

/**
 * Fetch a single orchestrator by ID
 */
export async function fetchOrchestrator(id: string): Promise<Orchestrator> {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${apiClient.baseURL}/api/orchestrators/${id}`, {
    method: 'GET',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch orchestrator');
  }

  return response.json();
}

/**
 * Fetch orchestrator detail with tasks and logs
 * Plan 05-02: Orchestrator Detail View
 */
export async function fetchOrchestratorDetail(id: string): Promise<OrchestratorDetail> {
  const authHeaders = await getAuthHeaders();
  const response = await fetch(`${apiClient.baseURL}/api/orchestrators/${id}`, {
    method: 'GET',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch orchestrator detail');
  }

  return response.json();
}

/**
 * Fetch logs for an orchestrator
 * Plan 05-02: Orchestrator Detail View
 */
export async function fetchOrchestratorLogs(
  id: string,
  options: FetchLogsOptions = {}
): Promise<LogsResponse> {
  const authHeaders = await getAuthHeaders();

  // Build query string
  const params = new URLSearchParams();
  if (options.limit !== undefined) {
    params.append('limit', options.limit.toString());
  }
  if (options.offset !== undefined) {
    params.append('offset', options.offset.toString());
  }

  const queryString = params.toString();
  const url = `${apiClient.baseURL}/api/orchestrators/${id}/logs${queryString ? `?${queryString}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      ...apiClient.defaultHeaders,
      ...authHeaders,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch orchestrator logs');
  }

  return response.json();
}
