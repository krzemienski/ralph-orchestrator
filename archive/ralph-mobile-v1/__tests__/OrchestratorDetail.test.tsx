/**
 * @fileoverview TDD tests for Orchestrator Detail View
 * Plan 05-02: Orchestrator Detail View
 *
 * Tests helper functions for:
 * - Task list formatting
 * - Log entry formatting
 * - Progress calculation
 */

import {
  formatTaskStatus,
  getTaskStatusColor,
  formatLogEntry,
  getLogLevelColor,
  calculateProgress,
  formatTimestamp,
} from '../lib/orchestratorDetailHelpers';
import { colors } from '../lib/theme';

describe('OrchestratorDetail Helpers', () => {
  describe('formatTaskStatus', () => {
    it('returns "Completed" for completed status', () => {
      expect(formatTaskStatus('completed')).toBe('Completed');
    });

    it('returns "In Progress" for running status', () => {
      expect(formatTaskStatus('running')).toBe('In Progress');
    });

    it('returns "Pending" for pending status', () => {
      expect(formatTaskStatus('pending')).toBe('Pending');
    });

    it('returns "Failed" for failed status', () => {
      expect(formatTaskStatus('failed')).toBe('Failed');
    });

    it('returns "Queued" for queued status', () => {
      expect(formatTaskStatus('queued')).toBe('Queued');
    });
  });

  describe('getTaskStatusColor', () => {
    it('returns success color for completed', () => {
      expect(getTaskStatusColor('completed')).toBe(colors.success);
    });

    it('returns primary color for running', () => {
      expect(getTaskStatusColor('running')).toBe(colors.primary);
    });

    it('returns error color for failed', () => {
      expect(getTaskStatusColor('failed')).toBe(colors.error);
    });

    it('returns muted color for pending', () => {
      expect(getTaskStatusColor('pending')).toBe(colors.textMuted);
    });

    it('returns muted color for queued', () => {
      expect(getTaskStatusColor('queued')).toBe(colors.textMuted);
    });
  });

  describe('formatLogEntry', () => {
    it('formats log entry with timestamp and message', () => {
      const log = {
        timestamp: '2024-01-15T10:30:45.123Z',
        level: 'info' as const,
        message: 'Starting iteration 5',
      };
      const formatted = formatLogEntry(log);
      // Check for time format (HH:MM:SS) - timezone may vary
      expect(formatted).toMatch(/^\d{2}:\d{2}:\d{2} \[INFO\] Starting iteration 5$/);
    });

    it('formats error level correctly', () => {
      const log = {
        timestamp: '2024-01-15T10:30:45.123Z',
        level: 'error' as const,
        message: 'Connection failed',
      };
      const formatted = formatLogEntry(log);
      expect(formatted).toContain('[ERROR]');
    });

    it('formats warning level correctly', () => {
      const log = {
        timestamp: '2024-01-15T10:30:45.123Z',
        level: 'warning' as const,
        message: 'Retrying request',
      };
      const formatted = formatLogEntry(log);
      expect(formatted).toContain('[WARN]');
    });
  });

  describe('getLogLevelColor', () => {
    it('returns error color for error level', () => {
      expect(getLogLevelColor('error')).toBe(colors.error);
    });

    it('returns warning color for warning level', () => {
      expect(getLogLevelColor('warning')).toBe(colors.warning);
    });

    it('returns text color for info level', () => {
      expect(getLogLevelColor('info')).toBe(colors.text);
    });

    it('returns muted color for debug level', () => {
      expect(getLogLevelColor('debug')).toBe(colors.textMuted);
    });
  });

  describe('calculateProgress', () => {
    it('returns 0 for zero total iterations', () => {
      expect(calculateProgress(0, 0)).toBe(0);
    });

    it('calculates percentage correctly', () => {
      expect(calculateProgress(5, 10)).toBe(50);
    });

    it('returns 100 for completed', () => {
      expect(calculateProgress(10, 10)).toBe(100);
    });

    it('rounds to nearest integer', () => {
      expect(calculateProgress(1, 3)).toBe(33);
    });
  });

  describe('formatTimestamp', () => {
    it('formats ISO timestamp to time only', () => {
      const timestamp = '2024-01-15T10:30:45.123Z';
      // Should return local time format HH:MM:SS
      const formatted = formatTimestamp(timestamp);
      expect(formatted).toMatch(/^\d{2}:\d{2}:\d{2}$/);
    });

    it('returns empty string for invalid timestamp', () => {
      expect(formatTimestamp('')).toBe('');
      expect(formatTimestamp('invalid')).toBe('');
    });
  });
});

describe('OrchestratorDetail API Types', () => {
  describe('OrchestratorDetailResponse', () => {
    it('should have required task fields', () => {
      const task = {
        id: 'task-1',
        name: 'Generate code',
        status: 'completed' as const,
        started_at: '2024-01-15T10:30:00Z',
        completed_at: '2024-01-15T10:31:00Z',
      };
      expect(task.id).toBeDefined();
      expect(task.name).toBeDefined();
      expect(task.status).toBeDefined();
    });

    it('should have required log fields', () => {
      const log = {
        timestamp: '2024-01-15T10:30:45Z',
        level: 'info' as const,
        message: 'Test message',
      };
      expect(log.timestamp).toBeDefined();
      expect(log.level).toBeDefined();
      expect(log.message).toBeDefined();
    });
  });
});
