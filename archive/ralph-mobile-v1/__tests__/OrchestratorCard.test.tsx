/**
 * @fileoverview TDD tests for OrchestratorCard component
 * Plan 05-01: Orchestrator List View
 * Tests component logic and data transformation
 */

import type { Orchestrator, OrchestratorStatus } from '../lib/types';
import {
  getStatusColor,
  formatElapsedTime,
  getSuccessRatio,
} from '../lib/orchestratorHelpers';

// Mock orchestrator data for tests
const mockOrchestrator: Orchestrator = {
  id: 'abc12345',
  status: 'running',
  prompt_file: 'test-prompt.md',
  metrics: {
    total_iterations: 5,
    successful_iterations: 4,
    failed_iterations: 1,
    current_iteration: 5,
    start_time: Date.now() - 60000, // 1 minute ago
    elapsed_time: 60,
  },
  created_at: new Date().toISOString(),
};

describe('OrchestratorCard Helpers', () => {
  describe('getStatusColor', () => {
    it('returns success color for completed status', () => {
      expect(getStatusColor('completed')).toBe('#22c55e');
    });

    it('returns error color for failed status', () => {
      expect(getStatusColor('failed')).toBe('#ef4444');
    });

    it('returns primary color for running status', () => {
      expect(getStatusColor('running')).toBe('#3b82f6');
    });

    it('returns muted color for paused status', () => {
      expect(getStatusColor('paused')).toBe('#a1a1aa');
    });

    it('returns muted color for pending status', () => {
      expect(getStatusColor('pending')).toBe('#a1a1aa');
    });
  });

  describe('formatElapsedTime', () => {
    it('formats seconds correctly', () => {
      expect(formatElapsedTime(45)).toBe('45s');
    });

    it('formats minutes correctly', () => {
      expect(formatElapsedTime(90)).toBe('1m 30s');
    });

    it('formats hours correctly', () => {
      expect(formatElapsedTime(3665)).toBe('1h 1m');
    });

    it('handles zero', () => {
      expect(formatElapsedTime(0)).toBe('0s');
    });
  });

  describe('getSuccessRatio', () => {
    it('returns correct ratio string', () => {
      expect(getSuccessRatio(mockOrchestrator.metrics)).toBe('4/5');
    });

    it('handles all successes', () => {
      const metrics = { ...mockOrchestrator.metrics, failed_iterations: 0, successful_iterations: 5 };
      expect(getSuccessRatio(metrics)).toBe('5/5');
    });

    it('handles all failures', () => {
      const metrics = { ...mockOrchestrator.metrics, failed_iterations: 5, successful_iterations: 0 };
      expect(getSuccessRatio(metrics)).toBe('0/5');
    });

    it('handles zero iterations', () => {
      const metrics = { ...mockOrchestrator.metrics, total_iterations: 0, successful_iterations: 0, failed_iterations: 0 };
      expect(getSuccessRatio(metrics)).toBe('0/0');
    });
  });
});

describe('Orchestrator Types', () => {
  it('has required fields', () => {
    expect(mockOrchestrator.id).toBeDefined();
    expect(mockOrchestrator.status).toBeDefined();
    expect(mockOrchestrator.prompt_file).toBeDefined();
    expect(mockOrchestrator.metrics).toBeDefined();
    expect(mockOrchestrator.created_at).toBeDefined();
  });

  it('has correct status type', () => {
    const validStatuses: OrchestratorStatus[] = ['running', 'completed', 'failed', 'paused', 'pending'];
    expect(validStatuses).toContain(mockOrchestrator.status);
  });

  it('has metrics with required fields', () => {
    expect(mockOrchestrator.metrics.total_iterations).toBeDefined();
    expect(mockOrchestrator.metrics.successful_iterations).toBeDefined();
    expect(mockOrchestrator.metrics.failed_iterations).toBeDefined();
    expect(mockOrchestrator.metrics.current_iteration).toBeDefined();
    expect(mockOrchestrator.metrics.elapsed_time).toBeDefined();
  });
});
