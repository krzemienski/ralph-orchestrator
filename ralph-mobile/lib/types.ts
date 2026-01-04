/**
 * @fileoverview TypeScript type definitions for Ralph Mobile App
 * Defines orchestrator and related data structures
 */

/**
 * Orchestrator status values
 */
export type OrchestratorStatus = 'running' | 'completed' | 'failed' | 'paused' | 'pending';

/**
 * Metrics for an orchestrator run
 */
export interface OrchestratorMetrics {
  total_iterations: number;
  successful_iterations: number;
  failed_iterations: number;
  current_iteration: number;
  start_time: number;
  elapsed_time: number;
}

/**
 * Orchestrator instance data
 */
export interface Orchestrator {
  id: string;
  status: OrchestratorStatus;
  prompt_file: string;
  metrics: OrchestratorMetrics;
  created_at: string;
  port?: number;
}

/**
 * API response for listing orchestrators
 */
export interface OrchestratorsResponse {
  orchestrators: Orchestrator[];
  total: number;
}

/**
 * Task status values
 */
export type TaskStatus = 'completed' | 'running' | 'pending' | 'failed' | 'queued';

/**
 * Log level values
 */
export type LogLevel = 'error' | 'warning' | 'info' | 'debug';

/**
 * Task structure for orchestrator detail
 */
export interface Task {
  id: string;
  name: string;
  status: TaskStatus;
  started_at?: string;
  completed_at?: string;
}

/**
 * Log entry structure
 */
export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
}

/**
 * Extended orchestrator detail with tasks and logs
 */
export interface OrchestratorDetail extends Orchestrator {
  tasks: Task[];
  logs: LogEntry[];
}
