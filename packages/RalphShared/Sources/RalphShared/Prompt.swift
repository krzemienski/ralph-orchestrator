import Foundation

/// Represents a Ralph prompt file.
/// Matches the JSON response from GET /api/prompts
public struct Prompt: Identifiable, Codable, Equatable, Hashable {
    /// Path to the prompt file relative to project root.
    public let path: String
    /// Name derived from filename without extension.
    public let name: String
    /// Preview extracted from first line, truncated to 50 characters.
    public let preview: String

    /// Use path as the unique identifier for SwiftUI lists.
    public var id: String { path }

    public init(path: String, name: String, preview: String) {
        self.path = path
        self.name = name
        self.preview = preview
    }
}

/// Response wrapper for GET /api/prompts.
public struct PromptsResponse: Codable {
    public let prompts: [Prompt]

    public init(prompts: [Prompt]) {
        self.prompts = prompts
    }
}
