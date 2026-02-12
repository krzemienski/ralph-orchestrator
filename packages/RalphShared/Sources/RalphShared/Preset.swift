import Foundation

/// Response wrapper for the presets endpoint.
public struct PresetsResponse: Decodable {
    public let presets: [PresetItem]

    public init(presets: [PresetItem]) {
        self.presets = presets
    }
}

/// Represents a configuration preset file available for orchestration.
/// Matches the JSON response from GET /api/presets
public struct PresetItem: Decodable, Identifiable {
    public let name: String
    public let path: String
    public let description: String

    public var id: String { path }

    public init(name: String, path: String, description: String) {
        self.name = name
        self.path = path
        self.description = description
    }
}
