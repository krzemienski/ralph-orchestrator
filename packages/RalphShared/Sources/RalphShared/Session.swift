import Foundation

/// Represents a Ralph orchestrator session being monitored.
/// Matches the JSON response from GET /api/sessions and GET /api/sessions/{id}/status
public struct Session: Identifiable, Codable, Equatable, Hashable {
    public let id: String
    public var iteration: Int
    public var total: Int?
    public var hat: String?
    public var elapsedSeconds: Int?  // Only present in status endpoint
    public var mode: String?         // Only present in status endpoint
    public var startedAt: String?    // Only present in list endpoint
    public var status: String?       // "running", "paused", "stopped", "idle"
    public var triggerEvent: String? // Event that triggered current hat
    public var availablePublishes: [String]? // Events this hat can publish

    public enum CodingKeys: String, CodingKey {
        case id
        case iteration
        case total
        case hat
        case elapsedSeconds = "elapsed_secs"
        case mode
        case startedAt = "started_at"
        case status
        case triggerEvent = "trigger_event"
        case availablePublishes = "publishes"
    }

    /// Computed property to get start time as Date
    public var startTime: Date? {
        guard let startedAt = startedAt else { return nil }
        return Formatters.iso8601Formatter.date(from: startedAt)
    }

    public init(
        id: String,
        iteration: Int,
        total: Int? = nil,
        hat: String? = nil,
        elapsedSeconds: Int? = nil,
        mode: String? = nil,
        startedAt: String? = nil,
        status: String? = nil,
        triggerEvent: String? = nil,
        availablePublishes: [String]? = nil
    ) {
        self.id = id
        self.iteration = iteration
        self.total = total
        self.hat = hat
        self.elapsedSeconds = elapsedSeconds
        self.mode = mode
        self.startedAt = startedAt
        self.status = status
        self.triggerEvent = triggerEvent
        self.availablePublishes = availablePublishes
    }
}

/// Backpressure check results
public struct BackpressureStatus: Codable, Equatable {
    public var testsPass: Bool
    public var lintPass: Bool
    public var typecheckPass: Bool

    public enum CodingKeys: String, CodingKey {
        case testsPass = "tests"
        case lintPass = "lint"
        case typecheckPass = "typecheck"
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        // Handle both bool and string values
        if let tests = try? container.decode(Bool.self, forKey: .testsPass) {
            testsPass = tests
        } else if let tests = try? container.decode(String.self, forKey: .testsPass) {
            testsPass = tests.lowercased() == "pass"
        } else {
            testsPass = false
        }

        if let lint = try? container.decode(Bool.self, forKey: .lintPass) {
            lintPass = lint
        } else if let lint = try? container.decode(String.self, forKey: .lintPass) {
            lintPass = lint.lowercased() == "pass"
        } else {
            lintPass = false
        }

        if let typecheck = try? container.decode(Bool.self, forKey: .typecheckPass) {
            typecheckPass = typecheck
        } else if let typecheck = try? container.decode(String.self, forKey: .typecheckPass) {
            typecheckPass = typecheck.lowercased() == "pass"
        } else {
            typecheckPass = false
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(testsPass, forKey: .testsPass)
        try container.encode(lintPass, forKey: .lintPass)
        try container.encode(typecheckPass, forKey: .typecheckPass)
    }

    public init(testsPass: Bool = false, lintPass: Bool = false, typecheckPass: Bool = false) {
        self.testsPass = testsPass
        self.lintPass = lintPass
        self.typecheckPass = typecheckPass
    }
}
