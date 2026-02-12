import Foundation

/// Aggregated token usage and cost metrics for a session.
public struct TokenMetrics: Equatable {
    public var inputTokens: Int = 0
    public var outputTokens: Int = 0
    public var estimatedCost: Double = 0.0
    public var durationMs: Int?
    public var maxTokens: Int = 100_000  // Default context window (100K)

    /// Total tokens (input + output).
    public var totalTokens: Int {
        inputTokens + outputTokens
    }

    /// Reset all metrics to initial state.
    public mutating func reset() {
        inputTokens = 0
        outputTokens = 0
        estimatedCost = 0.0
        durationMs = nil
    }

    /// Add token usage from an event payload.
    public mutating func addUsage(input: Int, output: Int) {
        inputTokens += input
        outputTokens += output
    }

    public init(
        inputTokens: Int = 0,
        outputTokens: Int = 0,
        estimatedCost: Double = 0.0,
        durationMs: Int? = nil,
        maxTokens: Int = 100_000
    ) {
        self.inputTokens = inputTokens
        self.outputTokens = outputTokens
        self.estimatedCost = estimatedCost
        self.durationMs = durationMs
        self.maxTokens = maxTokens
    }
}

/// Parsed usage data from an Assistant event payload.
public struct UsageData: Decodable {
    public let inputTokens: Int
    public let outputTokens: Int

    public enum CodingKeys: String, CodingKey {
        case inputTokens = "input_tokens"
        case outputTokens = "output_tokens"
    }

    public init(inputTokens: Int, outputTokens: Int) {
        self.inputTokens = inputTokens
        self.outputTokens = outputTokens
    }
}

/// Parsed result data from a Result event payload.
public struct ResultData: Decodable {
    public let totalCostUsd: Double?
    public let durationMs: Int?

    public enum CodingKeys: String, CodingKey {
        case totalCostUsd = "total_cost_usd"
        case durationMs = "duration_ms"
    }

    public init(totalCostUsd: Double? = nil, durationMs: Int? = nil) {
        self.totalCostUsd = totalCostUsd
        self.durationMs = durationMs
    }
}

/// Helper to parse event payloads for token metrics.
public enum TokenMetricsParser {
    /// Extract usage data from an Assistant event payload.
    /// Expected format: {"type": "assistant", "usage": {"input_tokens": 100, "output_tokens": 50}}
    public static func parseUsage(from payload: String?) -> UsageData? {
        guard let payload = payload,
              let data = payload.data(using: .utf8) else {
            return nil
        }

        struct AssistantPayload: Decodable {
            let usage: UsageData?
        }

        do {
            let decoded = try JSONDecoder().decode(AssistantPayload.self, from: data)
            return decoded.usage
        } catch {
            return nil
        }
    }

    /// Extract result data from a Result event payload.
    /// Expected format: {"total_cost_usd": 0.05, "duration_ms": 12345}
    public static func parseResult(from payload: String?) -> ResultData? {
        guard let payload = payload,
              let data = payload.data(using: .utf8) else {
            return nil
        }

        do {
            return try JSONDecoder().decode(ResultData.self, from: data)
        } catch {
            return nil
        }
    }
}
