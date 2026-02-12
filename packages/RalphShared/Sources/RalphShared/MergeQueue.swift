import Foundation

/// Response from the merge queue endpoint containing pending and completed items.
public struct MergeQueueResponse: Decodable {
    public let pending: [MergeQueueItem]
    public let completed: [MergeQueueItem]

    public init(pending: [MergeQueueItem], completed: [MergeQueueItem]) {
        self.pending = pending
        self.completed = completed
    }
}

/// Represents a worktree loop queued for merge into the main branch.
/// Matches the JSON response from GET /api/merge-queue
public struct MergeQueueItem: Decodable, Identifiable {
    public let id: String
    public let status: String
    public let prompt: String
    public let worktreePath: String?
    public let queuedAt: String
    public let mergedAt: String?

    public enum CodingKeys: String, CodingKey {
        case id, status, prompt
        case worktreePath = "worktree_path"
        case queuedAt = "queued_at"
        case mergedAt = "merged_at"
    }

    public init(
        id: String,
        status: String,
        prompt: String,
        worktreePath: String?,
        queuedAt: String,
        mergedAt: String?
    ) {
        self.id = id
        self.status = status
        self.prompt = prompt
        self.worktreePath = worktreePath
        self.queuedAt = queuedAt
        self.mergedAt = mergedAt
    }
}
