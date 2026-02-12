import Foundation

/// Response wrapper for the loops list endpoint.
public struct LoopsResponse: Decodable {
    public let loops: [LoopInfo]

    public init(loops: [LoopInfo]) {
        self.loops = loops
    }
}

/// Represents a running orchestration loop (primary or worktree).
/// Matches the JSON response from GET /api/loops and GET /api/loops/{id}
public struct LoopInfo: Decodable, Identifiable {
    public let id: String
    public let status: String        // "primary" | "worktree"
    public let prompt: String
    public let pid: UInt32
    public let startedAt: String
    public let worktreePath: String?
    public let workspace: String

    public enum CodingKeys: String, CodingKey {
        case id, status, prompt, pid, workspace
        case startedAt = "started_at"
        case worktreePath = "worktree_path"
    }

    public init(
        id: String,
        status: String,
        prompt: String,
        pid: UInt32,
        startedAt: String,
        worktreePath: String?,
        workspace: String
    ) {
        self.id = id
        self.status = status
        self.prompt = prompt
        self.pid = pid
        self.startedAt = startedAt
        self.worktreePath = worktreePath
        self.workspace = workspace
    }
}

/// Request body for spawning a new worktree loop.
public struct SpawnLoopRequest: Encodable {
    public let prompt: String
    public let configPath: String?
    public let baseBranch: String

    public enum CodingKeys: String, CodingKey {
        case prompt
        case configPath = "config_path"
        case baseBranch = "base_branch"
    }

    public init(prompt: String, configPath: String?, baseBranch: String) {
        self.prompt = prompt
        self.configPath = configPath
        self.baseBranch = baseBranch
    }
}

/// Response after successfully spawning a loop.
public struct SpawnLoopResponse: Decodable {
    public let id: String
    public let worktreePath: String
    public let status: String

    public enum CodingKeys: String, CodingKey {
        case id, status
        case worktreePath = "worktree_path"
    }

    public init(id: String, worktreePath: String, status: String) {
        self.id = id
        self.worktreePath = worktreePath
        self.status = status
    }
}

/// Generic operation result for merge/discard actions.
public struct OperationResponse: Decodable {
    public let success: Bool
    public let message: String

    public init(success: Bool, message: String) {
        self.success = success
        self.message = message
    }
}
