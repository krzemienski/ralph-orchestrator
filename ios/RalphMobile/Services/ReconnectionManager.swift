import Foundation

/// Manages automatic reconnection with exponential backoff + jitter for SSE streams.
class ReconnectionManager {
    private var retryCount = 0
    private let maxRetries = 10
    private let baseDelay: TimeInterval = 1.0
    private let maxDelay: TimeInterval = 30.0

    /// Returns the next delay interval with jitter, or nil if max retries exceeded.
    /// Implements exponential backoff with jitter: base * 2^n + random(0..1s), capped at 30s.
    func nextDelay() -> TimeInterval? {
        guard retryCount < maxRetries else { return nil }
        let exponential = baseDelay * pow(2.0, Double(retryCount))
        let jitter = Double.random(in: 0...1.0)
        retryCount += 1
        return min(exponential + jitter, maxDelay)
    }

    /// Resets retry count after successful connection.
    func reset() {
        retryCount = 0
    }

    /// Returns the current retry attempt number (1-based for display).
    var currentAttempt: Int {
        retryCount
    }
}
