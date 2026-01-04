/**
 * @fileoverview TDD tests for useOrchestrators hook
 * Plan 05-01: Orchestrator List View
 */

import { fetchOrchestrators } from '../lib/orchestratorApi';
import type { Orchestrator } from '../lib/types';

// Mock fetch
global.fetch = jest.fn();

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn().mockResolvedValue('test-token'),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const mockOrchestrators: Orchestrator[] = [
  {
    id: 'abc12345',
    status: 'running',
    prompt_file: 'test-prompt.md',
    metrics: {
      total_iterations: 5,
      successful_iterations: 4,
      failed_iterations: 1,
      current_iteration: 5,
      start_time: Date.now(),
      elapsed_time: 60,
    },
    created_at: new Date().toISOString(),
  },
  {
    id: 'def67890',
    status: 'completed',
    prompt_file: 'another-prompt.md',
    metrics: {
      total_iterations: 10,
      successful_iterations: 10,
      failed_iterations: 0,
      current_iteration: 10,
      start_time: Date.now() - 300000,
      elapsed_time: 300,
    },
    created_at: new Date().toISOString(),
  },
];

describe('fetchOrchestrators', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('fetches orchestrators from API', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ orchestrators: mockOrchestrators, total: 2 }),
    });

    const result = await fetchOrchestrators();

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/orchestrators'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
    expect(result.orchestrators).toHaveLength(2);
  });

  it('includes authorization header', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ orchestrators: [], total: 0 }),
    });

    await fetchOrchestrators();

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: expect.stringContaining('Bearer'),
        }),
      })
    );
  });

  it('throws error on API failure', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Unauthorized' }),
    });

    await expect(fetchOrchestrators()).rejects.toThrow('Unauthorized');
  });

  it('returns empty array when no orchestrators', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ orchestrators: [], total: 0 }),
    });

    const result = await fetchOrchestrators();

    expect(result.orchestrators).toEqual([]);
    expect(result.total).toBe(0);
  });
});
