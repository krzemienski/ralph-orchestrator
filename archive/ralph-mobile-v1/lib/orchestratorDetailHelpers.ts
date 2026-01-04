/**
 * @fileoverview Helper functions for orchestrator detail view
 * Plan 05-02: Orchestrator Detail View
 */

import { colors } from './theme';

/**
 * Task status values
 */
export type TaskStatus = 'completed' | 'running' | 'pending' | 'failed' | 'queued';

/**
 * Log level values
 */
export type LogLevel = 'error' | 'warning' | 'info' | 'debug';

/**
 * Log entry structure
 */
export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
}

/**
 * Task structure
 */
export interface Task {
  id: string;
  name: string;
  status: TaskStatus;
  started_at?: string;
  completed_at?: string;
}

/**
 * Format task status for display
 */
export function formatTaskStatus(status: TaskStatus): string {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'running':
      return 'In Progress';
    case 'pending':
      return 'Pending';
    case 'failed':
      return 'Failed';
    case 'queued':
      return 'Queued';
    default:
      return 'Unknown';
  }
}

/**
 * Get display color for task status
 */
export function getTaskStatusColor(status: TaskStatus): string {
  switch (status) {
    case 'completed':
      return colors.success;
    case 'running':
      return colors.primary;
    case 'failed':
      return colors.error;
    case 'pending':
    case 'queued':
    default:
      return colors.textMuted;
  }
}

/**
 * Format log entry for display
 * Returns: "HH:MM:SS [LEVEL] message"
 */
export function formatLogEntry(log: LogEntry): string {
  const time = formatTimestamp(log.timestamp);
  const level = log.level === 'warning' ? 'WARN' : log.level.toUpperCase();
  return `${time} [${level}] ${log.message}`;
}

/**
 * Get display color for log level
 */
export function getLogLevelColor(level: LogLevel): string {
  switch (level) {
    case 'error':
      return colors.error;
    case 'warning':
      return colors.warning;
    case 'info':
      return colors.text;
    case 'debug':
    default:
      return colors.textMuted;
  }
}

/**
 * Calculate progress percentage
 * @param current - Current iteration
 * @param total - Total iterations
 * @returns Progress percentage (0-100)
 */
export function calculateProgress(current: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((current / total) * 100);
}

/**
 * Format ISO timestamp to time only (HH:MM:SS)
 */
export function formatTimestamp(timestamp: string): string {
  if (!timestamp) return '';

  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return '';

    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const seconds = date.getSeconds().toString().padStart(2, '0');

    return `${hours}:${minutes}:${seconds}`;
  } catch {
    return '';
  }
}
