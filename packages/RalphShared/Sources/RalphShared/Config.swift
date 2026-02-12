import Foundation

/// Represents a Ralph configuration preset.
/// Matches the JSON response from GET /api/configs
public struct Config: Identifiable, Codable, Equatable, Hashable {
    /// Path to the config file relative to project root.
    public let path: String
    /// Name derived from filename without extension.
    public let name: String
    /// Description extracted from first comment line, empty if none.
    public let description: String

    /// Use path as the unique identifier for SwiftUI lists.
    public var id: String { path }

    public init(path: String, name: String, description: String) {
        self.path = path
        self.name = name
        self.description = description
    }
}

/// Response wrapper for GET /api/configs.
public struct ConfigsResponse: Codable {
    public let configs: [Config]

    public init(configs: [Config]) {
        self.configs = configs
    }
}
