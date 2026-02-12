import Foundation

/// Response wrapper for the tasks list endpoint.
public struct TasksResponse: Decodable {
    public let tasks: [TaskItem]
    public let total: Int

    public init(tasks: [TaskItem], total: Int) {
        self.tasks = tasks
        self.total = total
    }
}

/// Represents a work item tracked by the orchestrator.
/// Matches the JSON response from GET /api/tasks
public struct TaskItem: Decodable, Identifiable {
    public let id: String
    public let title: String
    public let description: String?
    public let status: String          // "open" | "in_progress" | "closed" | "failed"
    public let priority: UInt8         // 1-5
    public let blockedBy: [String]
    public let loopId: String?
    public let createdAt: String
    public let updatedAt: String?

    public enum CodingKeys: String, CodingKey {
        case id, title, description, status, priority
        case blockedBy = "blocked_by"
        case loopId = "loop_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    public init(
        id: String,
        title: String,
        description: String?,
        status: String,
        priority: UInt8,
        blockedBy: [String],
        loopId: String?,
        createdAt: String,
        updatedAt: String?
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.blockedBy = blockedBy
        self.loopId = loopId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

/// Request body for creating a new task.
public struct CreateTaskRequest: Encodable {
    public let title: String
    public let description: String?
    public let priority: UInt8
    public let blockedBy: [String]

    public enum CodingKeys: String, CodingKey {
        case title, description, priority
        case blockedBy = "blocked_by"
    }

    public init(title: String, description: String?, priority: UInt8, blockedBy: [String]) {
        self.title = title
        self.description = description
        self.priority = priority
        self.blockedBy = blockedBy
    }
}

/// Request body for updating a task's status.
public struct UpdateTaskRequest: Encodable {
    public let status: String

    public init(status: String) {
        self.status = status
    }
}
