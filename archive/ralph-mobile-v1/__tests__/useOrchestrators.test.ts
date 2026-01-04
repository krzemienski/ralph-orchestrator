/**
 * @fileoverview TDD tests for orchestrator API functions
 * Plan 05-01: Orchestrator List View
 * Plan 05-02: Orchestrator Detail View
 */

import { fetchOrchestrators, fetchOrchestratorDetail, fetchOrchestratorLogs } from '../lib/orchestratorApi';
import type { Orchestrator, OrchestratorDetail, Task, LogEntry } from '../lib/types';

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

// Plan 05-02: Orchestrator Detail View Tests
const mockTasks: Task[] = [
  {
    id: 'task-1',
    name: 'Generate code',
    status: 'completed',
    started_at: '2024-01-15T10:30:00Z',
    completed_at: '2024-01-15T10:31:00Z',
  },
  {
    id: 'task-2',
    name: 'Run tests',
    status: 'running',
    started_at: '2024-01-15T10:31:00Z',
  },
  {
    id: 'task-3',
    name: 'Deploy',
    status: 'pending',
  },
];

const mockLogs: LogEntry[] = [
  { timestamp: '2024-01-15T10:30:00Z', level: 'info', message: 'Starting iteration 1' },
  { timestamp: '2024-01-15T10:30:30Z', level: 'info', message: 'Code generated successfully' },
  { timestamp: '2024-01-15T10:31:00Z', level: 'warning', message: 'Test taking longer than expected' },
];

const mockOrchestratorDetail: OrchestratorDetail = {
  ...mockOrchestrators[0],
  tasks: mockTasks,
  logs: mockLogs,
};

describe('fetchOrchestratorDetail', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('fetches orchestrator detail with tasks and logs', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrchestratorDetail,
    });

    const result = await fetchOrchestratorDetail('abc12345');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/orchestrators/abc12345'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
    expect(result.tasks).toHaveLength(3);
    expect(result.logs).toHaveLength(3);
  });

  it('throws error when orchestrator not found', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Orchestrator not found' }),
    });

    await expect(fetchOrchestratorDetail('nonexistent')).rejects.toThrow('Orchestrator not found');
  });

  it('includes authorization header', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrchestratorDetail,
    });

    await fetchOrchestratorDetail('abc12345');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: expect.stringContaining('Bearer'),
        }),
      })
    );
  });
});

describe('fetchOrchestratorLogs', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  it('fetches logs for an orchestrator', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ logs: mockLogs }),
    });

    const result = await fetchOrchestratorLogs('abc12345');

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/orchestrators/abc12345/logs'),
      expect.any(Object)
    );
    expect(result.logs).toHaveLength(3);
  });

  it('supports limit parameter', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ logs: mockLogs.slice(0, 2) }),
    });

    const result = await fetchOrchestratorLogs('abc12345', { limit: 2 });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('limit=2'),
      expect.any(Object)
    );
    expect(result.logs).toHaveLength(2);
  });

  it('throws error on API failure', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal server error' }),
    });

    await expect(fetchOrchestratorLogs('abc12345')).rejects.toThrow('Internal server error');
  });
});
