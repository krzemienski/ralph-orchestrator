/**
 * Ralph Mobile - WebSocket Client
 *
 * Provides real-time log streaming from orchestrators via WebSocket.
 * Handles connection lifecycle, automatic reconnection, and typed event callbacks.
 */

import type {
  ConnectionState,
  LogEntry,
  LogPayload,
  MetricsUpdatePayload,
  OrchestratorMetrics,
  OrchestratorStatus,
  StatusChangePayload,
  WebSocketMessage,
  WebSocketMessageType,
} from '../types';

// === Configuration ===

/** Default WebSocket base URL */
let wsBaseUrl = 'ws://localhost:8420';

/**
 * Get the current WebSocket base URL
 */
export function getWsBaseUrl(): string {
  return wsBaseUrl;
}

/**
 * Set the WebSocket base URL (for settings screen)
 */
export function setWsBaseUrl(url: string): void {
  // Remove trailing slash if present
  wsBaseUrl = url.replace(/\/$/, '');
}

// === Event Callback Types ===

export type LogCallback = (log: LogEntry) => void;
export type StatusChangeCallback = (
  newStatus: OrchestratorStatus,
  previousStatus: OrchestratorStatus
) => void;
export type MetricsUpdateCallback = (metrics: OrchestratorMetrics) => void;
export type ConnectionStateCallback = (state: ConnectionState) => void;
export type ErrorCallback = (error: Error) => void;

// === WebSocket Class ===

/**
 * OrchestratorWebSocket
 *
 * WebSocket client for real-time orchestrator updates.
 * Supports automatic reconnection and typed event callbacks.
 */
export class OrchestratorWebSocket {
  private ws: WebSocket | null = null;
  private orchestratorId: string | null = null;
  private connectionState: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  // Configuration
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelayMs = 2000;

  // Event callbacks
  private logCallbacks: LogCallback[] = [];
  private statusChangeCallbacks: StatusChangeCallback[] = [];
  private metricsUpdateCallbacks: MetricsUpdateCallback[] = [];
  private connectionStateCallbacks: ConnectionStateCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];

  // === Connection Lifecycle ===

  /**
   * Connect to orchestrator log stream
   * @param orchestratorId The orchestrator ID to stream logs from
   */
  connect(orchestratorId: string): void {
    // Disconnect existing connection first
    if (this.ws) {
      this.disconnect();
    }

    this.orchestratorId = orchestratorId;
    this.reconnectAttempts = 0;
    this.attemptConnection();
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.clearReconnectTimer();

    if (this.ws) {
      // Remove event listeners before closing to prevent reconnect
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      this.ws.onopen = null;

      this.ws.close();
      this.ws = null;
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
   * Get connected orchestrator ID
   */
  getConnectedOrchestratorId(): string | null {
    return this.orchestratorId;
  }

  // === Event Registration ===

  /**
   * Register callback for log entries
   */
  onLog(callback: LogCallback): () => void {
    this.logCallbacks.push(callback);
    return () => {
      this.logCallbacks = this.logCallbacks.filter((cb) => cb !== callback);
    };
  }

  /**
   * Register callback for status changes
   */
  onStatusChange(callback: StatusChangeCallback): () => void {
    this.statusChangeCallbacks.push(callback);
    return () => {
      this.statusChangeCallbacks = this.statusChangeCallbacks.filter(
        (cb) => cb !== callback
      );
    };
  }

  /**
   * Register callback for metrics updates
   */
  onMetricsUpdate(callback: MetricsUpdateCallback): () => void {
    this.metricsUpdateCallbacks.push(callback);
    return () => {
      this.metricsUpdateCallbacks = this.metricsUpdateCallbacks.filter(
        (cb) => cb !== callback
      );
    };
  }

  /**
   * Register callback for connection state changes
   */
  onConnectionStateChange(callback: ConnectionStateCallback): () => void {
    this.connectionStateCallbacks.push(callback);
    return () => {
      this.connectionStateCallbacks = this.connectionStateCallbacks.filter(
        (cb) => cb !== callback
      );
    };
  }

  /**
   * Register callback for errors
   */
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      this.errorCallbacks = this.errorCallbacks.filter((cb) => cb !== callback);
    };
  }

  // === Internal Methods ===

  private attemptConnection(): void {
    if (!this.orchestratorId) {
      return;
    }

    this.setConnectionState('connecting');
    const url = `${wsBaseUrl}/ws/orchestrators/${this.orchestratorId}/logs`;

    try {
      this.ws = new WebSocket(url);
      this.setupEventHandlers();
    } catch (error) {
      this.handleConnectionError(
        error instanceof Error ? error : new Error('WebSocket creation failed')
      );
    }
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.setConnectionState('connected');
    };

    this.ws.onclose = () => {
      this.setConnectionState('disconnected');
      this.scheduleReconnect();
    };

    this.ws.onerror = (event) => {
      // WebSocket error events don't contain useful info, create generic error
      const error = new Error('WebSocket connection error');
      this.handleConnectionError(error);
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(event.data);
    };
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data) as WebSocketMessage;
      this.dispatchMessage(message);
    } catch (error) {
      // Log parse errors but don't crash
      console.warn('Failed to parse WebSocket message:', error);
    }
  }

  private dispatchMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'log':
        this.dispatchLogMessage(message as WebSocketMessage<LogPayload>);
        break;
      case 'status_change':
        this.dispatchStatusChange(
          message as WebSocketMessage<StatusChangePayload>
        );
        break;
      case 'metrics_update':
        this.dispatchMetricsUpdate(
          message as WebSocketMessage<MetricsUpdatePayload>
        );
        break;
      default:
        // Unknown message type - ignore
        console.warn('Unknown WebSocket message type:', (message as WebSocketMessage).type);
    }
  }

  private dispatchLogMessage(message: WebSocketMessage<LogPayload>): void {
    const log = message.payload.log;
    this.logCallbacks.forEach((cb) => cb(log));
  }

  private dispatchStatusChange(
    message: WebSocketMessage<StatusChangePayload>
  ): void {
    const { new_status, previous_status } = message.payload;
    this.statusChangeCallbacks.forEach((cb) => cb(new_status, previous_status));
  }

  private dispatchMetricsUpdate(
    message: WebSocketMessage<MetricsUpdatePayload>
  ): void {
    const { metrics } = message.payload;
    this.metricsUpdateCallbacks.forEach((cb) => cb(metrics));
  }

  private handleConnectionError(error: Error): void {
    this.setConnectionState('error');
    this.errorCallbacks.forEach((cb) => cb(error));
    this.scheduleReconnect();
  }

  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      this.connectionStateCallbacks.forEach((cb) => cb(state));
    }
  }

  private scheduleReconnect(): void {
    // Don't reconnect if manually disconnected (orchestratorId cleared)
    if (!this.orchestratorId) {
      return;
    }

    // Don't reconnect if max attempts reached
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('Max WebSocket reconnect attempts reached');
      this.setConnectionState('error');
      return;
    }

    this.clearReconnectTimer();
    this.reconnectAttempts++;

    // Exponential backoff: 2s, 4s, 8s, 16s, 32s
    const delay = this.reconnectDelayMs * Math.pow(2, this.reconnectAttempts - 1);

    this.reconnectTimer = setTimeout(() => {
      this.attemptConnection();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

// === Singleton Instance ===

/**
 * Default WebSocket instance for app-wide use
 */
export const orchestratorWs = new OrchestratorWebSocket();
