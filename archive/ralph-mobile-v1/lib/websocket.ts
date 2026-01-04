/**
 * @fileoverview WebSocket manager for real-time updates
 * Plan 05-03: Real-Time Updates
 *
 * Provides WebSocket connection management with:
 * - Automatic authentication via JWT token
 * - Message parsing and validation
 * - Subscriber pattern for message dispatch
 * - Connection state management
 */

import * as SecureStore from 'expo-secure-store';

/**
 * WebSocket connection states
 */
export type WebSocketConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'error';

/**
 * WebSocket message types
 */
export type WebSocketMessageType =
  | 'orchestrator_update'
  | 'log_entry'
  | 'task_update'
  | 'connection_status';

/**
 * Generic WebSocket message structure
 */
export interface WebSocketMessage {
  type: WebSocketMessageType | string;
  data: Record<string, any>;
}

/**
 * WebSocket manager configuration
 */
export interface WebSocketManagerConfig {
  baseURL?: string;
}

/**
 * Subscriber callback type
 */
export type WebSocketSubscriber = (message: WebSocketMessage) => void;

/**
 * WebSocket manager interface
 */
export interface WebSocketManager {
  connect: () => Promise<void>;
  disconnect: () => void;
  reconnect: () => Promise<void>;
  subscribe: (callback: WebSocketSubscriber) => () => void;
  getState: () => WebSocketConnectionState;
}

/**
 * Parse a raw WebSocket message string into a typed message object
 * Returns null if the message is invalid
 */
export function parseWebSocketMessage(rawMessage: string): WebSocketMessage | null {
  try {
    const parsed = JSON.parse(rawMessage);

    // Validate required fields
    if (typeof parsed.type !== 'string' || !parsed.data) {
      return null;
    }

    return {
      type: parsed.type,
      data: parsed.data,
    };
  } catch {
    return null;
  }
}

/**
 * Create a WebSocket manager for real-time updates
 */
export function createWebSocketManager(
  config: WebSocketManagerConfig = {}
): WebSocketManager {
  const baseURL = config.baseURL || 'ws://localhost:8080';

  let state: WebSocketConnectionState = 'disconnected';
  let ws: WebSocket | null = null;
  const subscribers: Set<WebSocketSubscriber> = new Set();

  /**
   * Get current connection state
   */
  function getState(): WebSocketConnectionState {
    return state;
  }

  /**
   * Notify all subscribers of a message
   */
  function notifySubscribers(message: WebSocketMessage): void {
    subscribers.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        console.error('WebSocket subscriber error:', error);
      }
    });
  }

  /**
   * Connect to WebSocket server
   */
  async function connect(): Promise<void> {
    state = 'connecting';

    // Get token for authentication
    const token = await SecureStore.getItemAsync('token');

    // Build WebSocket URL with token
    const wsURL = `${baseURL}/ws?token=${token}`;

    ws = new WebSocket(wsURL);

    ws.onopen = () => {
      state = 'connected';
    };

    ws.onclose = () => {
      state = 'disconnected';
    };

    ws.onerror = () => {
      state = 'error';
    };

    ws.onmessage = (event) => {
      const message = parseWebSocketMessage(event.data);
      if (message) {
        notifySubscribers(message);
      }
    };
  }

  /**
   * Disconnect from WebSocket server
   */
  function disconnect(): void {
    if (ws) {
      ws.close();
      ws = null;
    }
    state = 'disconnected';
  }

  /**
   * Reconnect to WebSocket server
   */
  async function reconnect(): Promise<void> {
    disconnect();
    await connect();
  }

  /**
   * Subscribe to WebSocket messages
   * Returns an unsubscribe function
   */
  function subscribe(callback: WebSocketSubscriber): () => void {
    subscribers.add(callback);

    return () => {
      subscribers.delete(callback);
    };
  }

  return {
    connect,
    disconnect,
    reconnect,
    subscribe,
    getState,
  };
}
