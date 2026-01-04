/**
 * @fileoverview TDD tests for Plan 06-02: Stop/Pause/Resume Controls
 * Tests control helper functions and API functions for orchestrator control
 */

import {
  validateControlAction,
  getConfirmationMessage,
  isActionAllowed,
  getNextStatus,
  ControlAction,
} from '../lib/orchestratorControlHelpers';

import {
  stopOrchestrator,
  pauseOrchestrator,
  resumeOrchestrator,
  ControlResponse,
} from '../lib/orchestratorControlApi';

import { OrchestratorStatus } from '../lib/types';

// Mock the api module
jest.mock('../lib/api', () => ({
  apiClient: {
    baseURL: 'http://localhost:8080',
    defaultHeaders: { 'Content-Type': 'application/json' },
  },
  getAuthHeaders: jest.fn().mockResolvedValue({ Authorization: 'Bearer test-token' }),
}));

// Mock fetch
global.fetch = jest.fn();

describe('Plan 06-02: OrchestratorControlHelpers', () => {
  describe('validateControlAction', () => {
    it('returns true for valid action types', () => {
      expect(validateControlAction('stop')).toBe(true);
      expect(validateControlAction('pause')).toBe(true);
      expect(validateControlAction('resume')).toBe(true);
    });

    it('returns false for invalid action types', () => {
      expect(validateControlAction('restart')).toBe(false);
      expect(validateControlAction('')).toBe(false);
      expect(validateControlAction('STOP')).toBe(false);
    });
  });

  describe('getConfirmationMessage', () => {
    it('returns stop confirmation message', () => {
      const message = getConfirmationMessage('stop', 'abc123');
      expect(message).toBe('Are you sure you want to stop orchestrator abc123? This action cannot be undone.');
    });

    it('returns pause confirmation message', () => {
      const message = getConfirmationMessage('pause', 'xyz789');
      expect(message).toBe('Pause orchestrator xyz789? You can resume it later.');
    });

    it('returns resume confirmation message', () => {
      const message = getConfirmationMessage('resume', 'def456');
      expect(message).toBe('Resume orchestrator def456?');
    });

    it('returns default message for unknown action', () => {
      const message = getConfirmationMessage('unknown' as ControlAction, 'id');
      expect(message).toBe('Perform action on orchestrator id?');
    });
  });

  describe('isActionAllowed', () => {
    // Stop is allowed from running or paused
    it('allows stop from running state', () => {
      expect(isActionAllowed('stop', 'running')).toBe(true);
    });

    it('allows stop from paused state', () => {
      expect(isActionAllowed('stop', 'paused')).toBe(true);
    });

    it('disallows stop from completed state', () => {
      expect(isActionAllowed('stop', 'completed')).toBe(false);
    });

    it('disallows stop from failed state', () => {
      expect(isActionAllowed('stop', 'failed')).toBe(false);
    });

    // Pause is only allowed from running
    it('allows pause from running state', () => {
      expect(isActionAllowed('pause', 'running')).toBe(true);
    });

    it('disallows pause from paused state', () => {
      expect(isActionAllowed('pause', 'paused')).toBe(false);
    });

    it('disallows pause from completed state', () => {
      expect(isActionAllowed('pause', 'completed')).toBe(false);
    });

    // Resume is only allowed from paused
    it('allows resume from paused state', () => {
      expect(isActionAllowed('resume', 'paused')).toBe(true);
    });

    it('disallows resume from running state', () => {
      expect(isActionAllowed('resume', 'running')).toBe(false);
    });

    it('disallows resume from completed state', () => {
      expect(isActionAllowed('resume', 'completed')).toBe(false);
    });
  });

  describe('getNextStatus', () => {
    it('returns stopped status after stop action', () => {
      expect(getNextStatus('stop')).toBe('stopped');
    });

    it('returns paused status after pause action', () => {
      expect(getNextStatus('pause')).toBe('paused');
    });

    it('returns running status after resume action', () => {
      expect(getNextStatus('resume')).toBe('running');
    });

    it('returns null for unknown action', () => {
      expect(getNextStatus('unknown' as ControlAction)).toBeNull();
    });
  });
});

describe('Plan 06-02: OrchestratorControlApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('stopOrchestrator', () => {
    it('sends POST request to stop endpoint', async () => {
      const mockResponse: ControlResponse = {
        instance_id: 'abc123',
        status: 'stopped',
        message: 'Orchestrator stopped successfully',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await stopOrchestrator('abc123');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8080/api/orchestrators/abc123/stop',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            Authorization: 'Bearer test-token',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('throws error on failed stop request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Orchestrator not found' }),
      });

      await expect(stopOrchestrator('invalid')).rejects.toThrow('Orchestrator not found');
    });
  });

  describe('pauseOrchestrator', () => {
    it('sends POST request to pause endpoint', async () => {
      const mockResponse: ControlResponse = {
        instance_id: 'xyz789',
        status: 'paused',
        message: 'Orchestrator paused successfully',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await pauseOrchestrator('xyz789');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8080/api/orchestrators/xyz789/pause',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('throws error when pause is not allowed', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Cannot pause: orchestrator not running' }),
      });

      await expect(pauseOrchestrator('paused-id')).rejects.toThrow(
        'Cannot pause: orchestrator not running'
      );
    });
  });

  describe('resumeOrchestrator', () => {
    it('sends POST request to resume endpoint', async () => {
      const mockResponse: ControlResponse = {
        instance_id: 'def456',
        status: 'running',
        message: 'Orchestrator resumed successfully',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await resumeOrchestrator('def456');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8080/api/orchestrators/def456/resume',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('throws error when resume is not allowed', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Cannot resume: orchestrator not paused' }),
      });

      await expect(resumeOrchestrator('running-id')).rejects.toThrow(
        'Cannot resume: orchestrator not paused'
      );
    });
  });
});
