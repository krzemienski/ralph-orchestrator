/**
 * Ralph Mobile - TypeScript Type Definitions
 *
 * All data models and API types for the Ralph orchestrator mobile app.
 */

// =============================================================================
// ORCHESTRATOR TYPES
// =============================================================================

/**
 * Orchestrator lifecycle status
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
 * Main orchestrator entity
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

// =============================================================================
// LOG TYPES
// =============================================================================

/**
 * Log severity level
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * Single log entry from an orchestrator
 */
export interface LogEntry {
  id: string;
  orchestrator_id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  metadata?: Record<string, unknown>;
}

// =============================================================================
// TASK TYPES
// =============================================================================

/**
 * Task execution status
 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

/**
 * Individual task within an orchestration
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

// =============================================================================
// API REQUEST/RESPONSE TYPES
// =============================================================================

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
 * Standard API error response
 */
export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, unknown>;
}

/**
 * Health check response from server
 */
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  version?: string;
  uptime?: number;
}

// =============================================================================
// WEBSOCKET MESSAGE TYPES
// =============================================================================

/**
 * WebSocket message types for real-time updates
 */
export type WebSocketMessageType =
  | 'log'
  | 'status_change'
  | 'metrics_update'
  | 'task_update'
  | 'error'
  | 'connected'
  | 'disconnected';

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
 * Log message payload
 */
export interface LogMessagePayload {
  log: LogEntry;
}

/**
 * Status change payload
 */
export interface StatusChangePayload {
  previous_status: OrchestratorStatus;
  new_status: OrchestratorStatus;
}

/**
 * Metrics update payload
 */
export interface MetricsUpdatePayload {
  metrics: OrchestratorMetrics;
}

/**
 * Task update payload
 */
export interface TaskUpdatePayload {
  task: Task;
}

// =============================================================================
// APP SETTINGS TYPES
// =============================================================================

/**
 * Auto-refresh interval options (in seconds)
 */
export type RefreshInterval = 5 | 10 | 30 | 60;

/**
 * Log buffer size options
 */
export type LogBufferSize = 100 | 500 | 1000 | -1; // -1 = unlimited

/**
 * Application settings stored in AsyncStorage
 */
export interface AppSettings {
  apiUrl: string;
  wsUrl: string;
  refreshInterval: RefreshInterval;
  logBufferSize: LogBufferSize;
  hapticFeedbackEnabled: boolean;
  darkMode: boolean;
}

/**
 * Default app settings
 */
export const DEFAULT_SETTINGS: AppSettings = {
  apiUrl: 'http://localhost:8420',
  wsUrl: 'ws://localhost:8420',
  refreshInterval: 10,
  logBufferSize: 500,
  hapticFeedbackEnabled: true,
  darkMode: true,
};

// =============================================================================
// UI HELPER TYPES
// =============================================================================

/**
 * Status badge color mapping
 */
export const STATUS_COLORS: Record<OrchestratorStatus, string> = {
  pending: '#6b7280',   // gray
  running: '#3b82f6',   // blue
  paused: '#eab308',    // yellow
  completed: '#22c55e', // green
  failed: '#ef4444',    // red
};

/**
 * Log level color mapping
 */
export const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  debug: '#6b7280', // gray
  info: '#3b82f6',  // blue
  warn: '#eab308',  // yellow
  error: '#ef4444', // red
};

/**
 * Connection state for UI display
 */
export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'error';

/**
 * Action result for control panel history
 */
export interface ActionResult {
  id: string;
  timestamp: string;
  action: 'start' | 'stop' | 'pause' | 'resume';
  orchestrator_id?: string;
  success: boolean;
  message?: string;
}
