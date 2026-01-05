/**
 * Ralph Mobile - Type Definitions
 * Core TypeScript interfaces for orchestrator management
 */

// === Orchestrator Types ===

/**
 * Possible states of an orchestrator
 */
export type OrchestratorStatus =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed';

/**
 * Performance metrics for an orchestrator run
 */
export interface OrchestratorMetrics {
  iterations_completed: number;
  iterations_total: number;
  tokens_used: number;
  duration_seconds: number;
  success_rate: number;
}

/**
 * Full orchestrator entity
 */
export interface Orchestrator {
  id: string;
  name: string;
  status: OrchestratorStatus;
  prompt_file: string;
  config_file: string;
  metrics: OrchestratorMetrics;
  created_at: string;
  updated_at: string;
  port?: number;
  error?: string;
}

// === Log Types ===

/**
 * Log severity levels
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Individual log entry from orchestrator
 */
export interface LogEntry {
  id: string;
  orchestrator_id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  metadata?: Record<string, unknown>;
}

// === Task Types ===

/**
 * Possible states of a task within an orchestrator
 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

/**
 * Task entity within an orchestrator run
 */
export interface Task {
  id: string;
  orchestrator_id: string;
  name: string;
  status: TaskStatus;
  started_at?: string;
  completed_at?: string;
  output?: string;
  error?: string;
}

// === API Request/Response Types ===

/**
 * Request body for starting a new orchestration
 */
export interface StartOrchestratorRequest {
  prompt_file: string;
  config_file?: string;
  max_iterations?: number;
  max_runtime_seconds?: number;
}

/**
 * Response from starting an orchestration
 */
export interface StartOrchestratorResponse {
  orchestrator: Orchestrator;
  message: string;
}

/**
 * Standard error response from API
 */
export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, unknown>;
}

// === WebSocket Event Types ===

/**
 * WebSocket message types
 */
export type WebSocketMessageType = 'log' | 'status_change' | 'metrics_update';

/**
 * Base WebSocket message structure
 */
export interface WebSocketMessage<T = unknown> {
  type: WebSocketMessageType;
  orchestrator_id: string;
  timestamp: string;
  payload: T;
}

/**
 * WebSocket log message payload
 */
export interface LogPayload {
  log: LogEntry;
}

/**
 * WebSocket status change payload
 */
export interface StatusChangePayload {
  previous_status: OrchestratorStatus;
  new_status: OrchestratorStatus;
}

/**
 * WebSocket metrics update payload
 */
export interface MetricsUpdatePayload {
  metrics: OrchestratorMetrics;
}

// === Settings Types ===

/**
 * App settings persisted to storage
 */
export interface AppSettings {
  serverUrl: string;
  websocketUrl: string;
  autoRefreshInterval: number; // seconds: 5, 10, 30, 60
  logBufferSize: number; // 100, 500, 1000, -1 for unlimited
  hapticFeedbackEnabled: boolean;
}

/**
 * Default settings values
 */
export const DEFAULT_SETTINGS: AppSettings = {
  serverUrl: 'http://localhost:8420',
  websocketUrl: 'ws://localhost:8420',
  autoRefreshInterval: 10,
  logBufferSize: 500,
  hapticFeedbackEnabled: true,
};

// === Utility Types ===

/**
 * API response wrapper for consistent error handling
 */
export type ApiResult<T> =
  | { success: true; data: T }
  | { success: false; error: ApiError };

/**
 * Connection state for WebSocket
 */
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';
