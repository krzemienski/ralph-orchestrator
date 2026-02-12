import Foundation

/// Response wrapper for the iterations endpoint.
public struct IterationsResponse: Decodable {
    public let iterations: [IterationItem]
    public let total: Int

    public init(iterations: [IterationItem], total: Int) {
        self.iterations = iterations
        self.total = total
    }
}

/// Represents a single iteration within a session's execution history.
/// Matches the JSON response from GET /api/sessions/{id}/iterations
public struct IterationItem: Decodable, Identifiable {
    public let number: UInt32
    public let hat: String?
    public let startedAt: String
    public let durationSecs: UInt64?

    public var id: UInt32 { number }

    public enum CodingKeys: String, CodingKey {
        case number, hat
        case startedAt = "started_at"
        case durationSecs = "duration_secs"
    }

    public init(number: UInt32, hat: String?, startedAt: String, durationSecs: UInt64?) {
        self.number = number
        self.hat = hat
        self.startedAt = startedAt
        self.durationSecs = durationSecs
    }
}
