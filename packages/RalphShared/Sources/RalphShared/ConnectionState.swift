import Foundation

/// Represents the connection state to the Ralph Mobile server.
public enum ConnectionState: Equatable {
    case disconnected
    case connecting
    case connected
    case reconnecting(attempt: Int)
    case error(String)

    public var isConnected: Bool {
        if case .connected = self { return true }
        return false
    }

    public var isError: Bool {
        if case .error = self { return true }
        return false
    }

    public var displayText: String {
        switch self {
        case .disconnected:
            return "Disconnected"
        case .connecting:
            return "Connecting..."
        case .connected:
            return "Connected"
        case .reconnecting(let attempt):
            return "Reconnecting (\(attempt))..."
        case .error(let message):
            return "Error: \(message)"
        }
    }
}
