/**
 * Ralph Mobile - WebSocket Client
 *
 * Handles real-time WebSocket communication with the Ralph orchestrator backend.
 * Provides event-based callbacks for logs, status changes, and metrics updates.
 */

import {
  type LogEntry,
  type OrchestratorStatus,
  type OrchestratorMetrics,
  type Task,
  type WebSocketMessage,
  type WebSocketMessageType,
  type LogMessagePayload,
  type StatusChangePayload,
  type MetricsUpdatePayload,
  type TaskUpdatePayload,
  type ConnectionState,
  DEFAULT_SETTINGS,
} from '../types';

// =============================================================================
// TYPES
// =============================================================================

/**
 * Callback types for WebSocket events
 */
type LogCallback = (log: LogEntry) => void;
type StatusCallback = (status: OrchestratorStatus, previousStatus?: OrchestratorStatus) => void;
type MetricsCallback = (metrics: OrchestratorMetrics) => void;
type TaskCallback = (task: Task) => void;
type ConnectionCallback = (state: ConnectionState) => void;
type ErrorCallback = (error: Error) => void;

/**
 * WebSocket options
 */
export interface WebSocketOptions {
  /** Base WebSocket URL (defaults to DEFAULT_SETTINGS.wsUrl) */
  wsUrl?: string;
  /** Auto-reconnect on disconnect (default: true) */
  autoReconnect?: boolean;
  /** Reconnect delay in ms (default: 3000) */
  reconnectDelay?: number;
  /** Maximum reconnect attempts (default: 5) */
  maxReconnectAttempts?: number;
}

// =============================================================================
// WEBSOCKET CLASS
// =============================================================================

/**
 * WebSocket client for real-time orchestrator updates
 *
 * Usage:
 * ```typescript
 * const ws = new OrchestratorWebSocket();
 * ws.onLog((log) => console.log(log.message));
 * ws.onStatusChange((status) => console.log('New status:', status));
 * ws.connect('orchestrator-123');
 * ```
 */
export class OrchestratorWebSocket {
  private socket: WebSocket | null = null;
  private orchestratorId: string | null = null;
  private connectionState: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  // Options
  private readonly wsUrl: string;
  private readonly autoReconnect: boolean;
  private readonly reconnectDelay: number;
  private readonly maxReconnectAttempts: number;

  // Callbacks
  private logCallbacks: LogCallback[] = [];
  private statusCallbacks: StatusCallback[] = [];
  private metricsCallbacks: MetricsCallback[] = [];
  private taskCallbacks: TaskCallback[] = [];
  private connectionCallbacks: ConnectionCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];

  constructor(options: WebSocketOptions = {}) {
    this.wsUrl = options.wsUrl || DEFAULT_SETTINGS.wsUrl;
    this.autoReconnect = options.autoReconnect ?? true;
    this.reconnectDelay = options.reconnectDelay ?? 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
  }

  // ===========================================================================
  // CONNECTION MANAGEMENT
  // ===========================================================================

  /**
   * Connect to WebSocket for a specific orchestrator
   */
  connect(orchestratorId: string): void {
    // Disconnect existing connection if any
    if (this.socket) {
      this.disconnect();
    }

    this.orchestratorId = orchestratorId;
    this.reconnectAttempts = 0;
    this.establishConnection();
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    // Clear reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close socket
    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      this.socket.close();
      this.socket = null;
    }

    this.orchestratorId = null;
    this.setConnectionState('disconnected');
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Get currently connected orchestrator ID
   */
  getOrchestratorId(): string | null {
    return this.orchestratorId;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState === 'connected' && this.socket?.readyState === WebSocket.OPEN;
  }

  // ===========================================================================
  // EVENT SUBSCRIPTIONS
  // ===========================================================================

  /**
   * Subscribe to log events
   */
  onLog(callback: LogCallback): () => void {
    this.logCallbacks.push(callback);
    return () => {
      this.logCallbacks = this.logCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Subscribe to status change events
   */
  onStatusChange(callback: StatusCallback): () => void {
    this.statusCallbacks.push(callback);
    return () => {
      this.statusCallbacks = this.statusCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Subscribe to metrics update events
   */
  onMetricsUpdate(callback: MetricsCallback): () => void {
    this.metricsCallbacks.push(callback);
    return () => {
      this.metricsCallbacks = this.metricsCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Subscribe to task update events
   */
  onTaskUpdate(callback: TaskCallback): () => void {
    this.taskCallbacks.push(callback);
    return () => {
      this.taskCallbacks = this.taskCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionChange(callback: ConnectionCallback): () => void {
    this.connectionCallbacks.push(callback);
    return () => {
      this.connectionCallbacks = this.connectionCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Subscribe to error events
   */
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(): void {
    this.logCallbacks = [];
    this.statusCallbacks = [];
    this.metricsCallbacks = [];
    this.taskCallbacks = [];
    this.connectionCallbacks = [];
    this.errorCallbacks = [];
  }

  // ===========================================================================
  // PRIVATE METHODS
  // ===========================================================================

  /**
   * Establish WebSocket connection
   */
  private establishConnection(): void {
    if (!this.orchestratorId) {
      return;
    }

    this.setConnectionState('connecting');

    const url = `${this.wsUrl}/ws/orchestrators/${this.orchestratorId}/logs`;

    try {
      this.socket = new WebSocket(url);
      this.setupSocketHandlers();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error('Failed to create WebSocket'));
      this.scheduleReconnect();
    }
  }

  /**
   * Set up WebSocket event handlers
   */
  private setupSocketHandlers(): void {
    if (!this.socket) {
      return;
    }

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.setConnectionState('connected');
    };

    this.socket.onclose = (event) => {
      const wasConnected = this.connectionState === 'connected';
      this.setConnectionState('disconnected');

      // Only attempt reconnect if we were connected or connecting
      if (wasConnected && this.autoReconnect && this.orchestratorId) {
        this.scheduleReconnect();
      }
    };

    this.socket.onerror = (event) => {
      this.setConnectionState('error');
      this.handleError(new Error('WebSocket error'));
    };

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data);
    };
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data) as WebSocketMessage;
      this.dispatchMessage(message);
    } catch (error) {
      this.handleError(new Error(`Failed to parse WebSocket message: ${data}`));
    }
  }

  /**
   * Dispatch message to appropriate callbacks
   */
  private dispatchMessage(message: WebSocketMessage): void {
    const { type, payload } = message;

    switch (type) {
      case 'log': {
        const logPayload = payload as LogMessagePayload;
        this.logCallbacks.forEach((cb) => cb(logPayload.log));
        break;
      }

      case 'status_change': {
        const statusPayload = payload as StatusChangePayload;
        this.statusCallbacks.forEach((cb) =>
          cb(statusPayload.new_status, statusPayload.previous_status)
        );
        break;
      }

      case 'metrics_update': {
        const metricsPayload = payload as MetricsUpdatePayload;
        this.metricsCallbacks.forEach((cb) => cb(metricsPayload.metrics));
        break;
      }

      case 'task_update': {
        const taskPayload = payload as TaskUpdatePayload;
        this.taskCallbacks.forEach((cb) => cb(taskPayload.task));
        break;
      }

      case 'connected':
        // Server acknowledged connection
        break;

      case 'disconnected':
        // Server initiated disconnect
        this.setConnectionState('disconnected');
        break;

      case 'error': {
        const errorMessage = (payload as { message?: string })?.message || 'Unknown error';
        this.handleError(new Error(errorMessage));
        break;
      }

      default:
        // Unknown message type - ignore
        break;
    }
  }

  /**
   * Set connection state and notify listeners
   */
  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      this.connectionCallbacks.forEach((cb) => cb(state));
    }
  }

  /**
   * Handle error and notify listeners
   */
  private handleError(error: Error): void {
    this.errorCallbacks.forEach((cb) => cb(error));
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.handleError(new Error('Max reconnection attempts reached'));
      return;
    }

    // Clear any existing timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts; // Exponential backoff

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      if (this.orchestratorId) {
        this.establishConnection();
      }
    }, delay);
  }
}

// =============================================================================
// SINGLETON INSTANCE
// =============================================================================

/**
 * Default WebSocket instance for app-wide use
 */
let defaultWebSocket: OrchestratorWebSocket | null = null;

/**
 * Get the default WebSocket instance
 */
export function getWebSocket(): OrchestratorWebSocket {
  if (!defaultWebSocket) {
    defaultWebSocket = new OrchestratorWebSocket();
  }
  return defaultWebSocket;
}

/**
 * Reset the default WebSocket instance (useful for testing or settings changes)
 */
export function resetWebSocket(options?: WebSocketOptions): OrchestratorWebSocket {
  if (defaultWebSocket) {
    defaultWebSocket.disconnect();
    defaultWebSocket.removeAllListeners();
  }
  defaultWebSocket = new OrchestratorWebSocket(options);
  return defaultWebSocket;
}
