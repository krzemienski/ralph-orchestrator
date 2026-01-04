/**
 * @fileoverview API functions for orchestrator data
 * Plan 05-01: Orchestrator List View
 */

import { apiClient, getAuthHeaders } from './api';
import type { Orchestrator, OrchestratorsResponse } from './types';

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
