import Foundation

/// Response wrapper for the hats endpoint.
public struct HatsResponse: Decodable {
    public let hats: [HatItem]

    public init(hats: [HatItem]) {
        self.hats = hats
    }
}

/// Represents an orchestration role (hat) that Ralph can wear.
/// Matches the JSON response from GET /api/hats
public struct HatItem: Decodable, Identifiable {
    public let name: String
    public let description: String
    public let emoji: String

    public var id: String { name }

    public init(name: String, description: String, emoji: String) {
        self.name = name
        self.description = description
        self.emoji = emoji
    }
}
