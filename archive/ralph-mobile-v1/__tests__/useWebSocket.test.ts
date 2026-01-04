/**
 * @fileoverview Tests for WebSocket real-time updates
 * Plan 05-03: Real-Time Updates
 *
 * TDD: Write tests first, then implement
 */

import {
  createWebSocketManager,
  parseWebSocketMessage,
  WebSocketMessage,
  WebSocketConnectionState,
} from '../lib/websocket';

// Mock SecureStore for token retrieval
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn().mockResolvedValue('test-jwt-token'),
}));

describe('WebSocket Message Parsing', () => {
  describe('parseWebSocketMessage', () => {
    it('should parse valid orchestrator update message', () => {
      const rawMessage = JSON.stringify({
        type: 'orchestrator_update',
        data: {
          id: 'abc123',
          status: 'running',
          metrics: {
            current_iteration: 5,
            total_iterations: 10,
          },
        },
      });

      const parsed = parseWebSocketMessage(rawMessage);

      expect(parsed).not.toBeNull();
      expect(parsed?.type).toBe('orchestrator_update');
      expect(parsed?.data.id).toBe('abc123');
      expect(parsed?.data.status).toBe('running');
    });

    it('should parse log entry message', () => {
      const rawMessage = JSON.stringify({
        type: 'log_entry',
        data: {
          orchestrator_id: 'abc123',
          timestamp: '2024-01-15T10:30:00Z',
          level: 'info',
          message: 'Task completed successfully',
        },
      });

      const parsed = parseWebSocketMessage(rawMessage);

      expect(parsed).not.toBeNull();
      expect(parsed?.type).toBe('log_entry');
      expect(parsed?.data.level).toBe('info');
    });

    it('should parse task update message', () => {
      const rawMessage = JSON.stringify({
        type: 'task_update',
        data: {
          orchestrator_id: 'abc123',
          task: {
            id: 'task-1',
            name: 'Build component',
            status: 'completed',
          },
        },
      });

      const parsed = parseWebSocketMessage(rawMessage);

      expect(parsed).not.toBeNull();
      expect(parsed?.type).toBe('task_update');
      expect(parsed?.data.task.status).toBe('completed');
    });

    it('should parse connection status message', () => {
      const rawMessage = JSON.stringify({
        type: 'connection_status',
        data: {
          status: 'connected',
          client_id: 'client-xyz',
        },
      });

      const parsed = parseWebSocketMessage(rawMessage);

      expect(parsed).not.toBeNull();
      expect(parsed?.type).toBe('connection_status');
    });

    it('should return null for invalid JSON', () => {
      const parsed = parseWebSocketMessage('not valid json{');
      expect(parsed).toBeNull();
    });

    it('should return null for message without type', () => {
      const rawMessage = JSON.stringify({ data: { foo: 'bar' } });
      const parsed = parseWebSocketMessage(rawMessage);
      expect(parsed).toBeNull();
    });

    it('should return null for message without data', () => {
      const rawMessage = JSON.stringify({ type: 'orchestrator_update' });
      const parsed = parseWebSocketMessage(rawMessage);
      expect(parsed).toBeNull();
    });
  });
});

describe('WebSocketManager', () => {
  let mockWebSocket: any;
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    // Store original WebSocket
    originalWebSocket = global.WebSocket;

    // Create mock WebSocket constructor
    mockWebSocket = {
      close: jest.fn(),
      send: jest.fn(),
      readyState: 1, // OPEN
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null,
      CONNECTING: 0,
      OPEN: 1,
      CLOSING: 2,
      CLOSED: 3,
    };

    (global as any).WebSocket = jest.fn(() => mockWebSocket);
  });

  afterEach(() => {
    // Restore original WebSocket
    global.WebSocket = originalWebSocket;
    jest.clearAllMocks();
  });

  describe('createWebSocketManager', () => {
    it('should create a manager with disconnected initial state', () => {
      const manager = createWebSocketManager();

      expect(manager.getState()).toBe('disconnected');
    });

    it('should provide connect method', () => {
      const manager = createWebSocketManager();

      expect(typeof manager.connect).toBe('function');
    });

    it('should provide disconnect method', () => {
      const manager = createWebSocketManager();

      expect(typeof manager.disconnect).toBe('function');
    });

    it('should provide subscribe method', () => {
      const manager = createWebSocketManager();

      expect(typeof manager.subscribe).toBe('function');
    });
  });

  describe('connection lifecycle', () => {
    it('should transition to connecting state when connect is called', async () => {
      const manager = createWebSocketManager();

      await manager.connect();

      expect(manager.getState()).toBe('connecting');
    });

    it('should create WebSocket with correct URL including token', async () => {
      const manager = createWebSocketManager({
        baseURL: 'ws://localhost:8080',
      });

      await manager.connect();

      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8080/ws')
      );
      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('token=test-jwt-token')
      );
    });

    it('should transition to connected state on WebSocket open', async () => {
      const manager = createWebSocketManager();

      await manager.connect();

      // Simulate WebSocket open event
      mockWebSocket.onopen?.();

      expect(manager.getState()).toBe('connected');
    });

    it('should transition to disconnected state on WebSocket close', async () => {
      const manager = createWebSocketManager();

      await manager.connect();
      mockWebSocket.onopen?.();

      // Simulate WebSocket close event
      mockWebSocket.onclose?.({ code: 1000, reason: 'Normal closure' });

      expect(manager.getState()).toBe('disconnected');
    });

    it('should transition to error state on WebSocket error', async () => {
      const manager = createWebSocketManager();

      await manager.connect();

      // Simulate WebSocket error event
      mockWebSocket.onerror?.({ message: 'Connection failed' });

      expect(manager.getState()).toBe('error');
    });

    it('should close WebSocket when disconnect is called', async () => {
      const manager = createWebSocketManager();

      await manager.connect();
      mockWebSocket.onopen?.();

      manager.disconnect();

      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });

  describe('message handling', () => {
    it('should notify subscribers when message is received', async () => {
      const manager = createWebSocketManager();
      const callback = jest.fn();

      manager.subscribe(callback);
      await manager.connect();
      mockWebSocket.onopen?.();

      // Simulate receiving a message
      const message = {
        type: 'orchestrator_update',
        data: { id: 'abc123', status: 'running' },
      };
      mockWebSocket.onmessage?.({ data: JSON.stringify(message) });

      expect(callback).toHaveBeenCalledWith(message);
    });

    it('should not notify unsubscribed callbacks', async () => {
      const manager = createWebSocketManager();
      const callback = jest.fn();

      const unsubscribe = manager.subscribe(callback);
      unsubscribe();

      await manager.connect();
      mockWebSocket.onopen?.();

      const message = {
        type: 'orchestrator_update',
        data: { id: 'abc123', status: 'running' },
      };
      mockWebSocket.onmessage?.({ data: JSON.stringify(message) });

      expect(callback).not.toHaveBeenCalled();
    });

    it('should support multiple subscribers', async () => {
      const manager = createWebSocketManager();
      const callback1 = jest.fn();
      const callback2 = jest.fn();

      manager.subscribe(callback1);
      manager.subscribe(callback2);

      await manager.connect();
      mockWebSocket.onopen?.();

      const message = {
        type: 'orchestrator_update',
        data: { id: 'abc123', status: 'running' },
      };
      mockWebSocket.onmessage?.({ data: JSON.stringify(message) });

      expect(callback1).toHaveBeenCalledWith(message);
      expect(callback2).toHaveBeenCalledWith(message);
    });

    it('should ignore invalid messages without crashing', async () => {
      const manager = createWebSocketManager();
      const callback = jest.fn();

      manager.subscribe(callback);
      await manager.connect();
      mockWebSocket.onopen?.();

      // Simulate receiving invalid JSON
      mockWebSocket.onmessage?.({ data: 'not valid json{' });

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('reconnection', () => {
    it('should provide reconnect method', () => {
      const manager = createWebSocketManager();

      expect(typeof manager.reconnect).toBe('function');
    });

    it('should close existing connection and create new one on reconnect', async () => {
      const manager = createWebSocketManager();

      await manager.connect();
      mockWebSocket.onopen?.();

      await manager.reconnect();

      expect(mockWebSocket.close).toHaveBeenCalled();
      expect(global.WebSocket).toHaveBeenCalledTimes(2);
    });
  });
});

describe('WebSocket Message Types', () => {
  it('should export WebSocketMessage type', () => {
    // This is a compile-time check - if types are wrong, this won't compile
    const message: WebSocketMessage = {
      type: 'orchestrator_update',
      data: { id: 'test', status: 'running' },
    };
    expect(message.type).toBe('orchestrator_update');
  });

  it('should export WebSocketConnectionState type', () => {
    const states: WebSocketConnectionState[] = [
      'disconnected',
      'connecting',
      'connected',
      'error',
    ];
    expect(states).toHaveLength(4);
  });
});
