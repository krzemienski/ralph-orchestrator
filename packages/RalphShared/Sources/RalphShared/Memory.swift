import Foundation

/// Represents the memories file content and metadata.
/// Matches the JSON response from GET /api/memories and PUT /api/memories
public struct MemoriesContent: Codable {
    public let content: String
    public let lastModified: String?

    public enum CodingKeys: String, CodingKey {
        case content
        case lastModified = "last_modified"
    }

    public init(content: String, lastModified: String?) {
        self.content = content
        self.lastModified = lastModified
    }
}

/// Request body for updating memories content.
public struct UpdateMemoriesRequest: Encodable {
    public let content: String

    public init(content: String) {
        self.content = content
    }
}

/// Response from exporting memories as a downloadable file.
public struct MemoriesExport: Decodable {
    public let content: String
    public let exportedAt: String
    public let filename: String

    public enum CodingKeys: String, CodingKey {
        case content, filename
        case exportedAt = "exported_at"
    }

    public init(content: String, exportedAt: String, filename: String) {
        self.content = content
        self.exportedAt = exportedAt
        self.filename = filename
    }
}
