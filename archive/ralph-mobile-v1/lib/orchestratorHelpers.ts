/**
 * @fileoverview Helper functions for orchestrator data
 * Plan 05-01: Orchestrator List View
 */

import type { OrchestratorStatus, OrchestratorMetrics } from './types';
import { colors } from './theme';

/**
 * Get the display color for an orchestrator status
 */
export function getStatusColor(status: OrchestratorStatus): string {
  switch (status) {
    case 'completed':
      return colors.success;
    case 'failed':
      return colors.error;
    case 'running':
      return colors.primary;
    case 'paused':
    case 'pending':
    default:
      return colors.textMuted;
  }
}

/**
 * Format elapsed time in seconds to human-readable string
 * Examples: "45s", "1m 30s", "1h 1m"
 */
export function formatElapsedTime(seconds: number): string {
  if (seconds === 0) return '0s';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

/**
 * Get success ratio string for display
 * Example: "4/5" for 4 successful out of 5 total
 */
export function getSuccessRatio(metrics: OrchestratorMetrics): string {
  return `${metrics.successful_iterations}/${metrics.total_iterations}`;
}
