import Foundation

/// Represents a skill from the Ralph orchestrator.
/// Matches the JSON response from GET /api/skills
public struct Skill: Identifiable, Codable, Equatable, Hashable {
    public let name: String
    public let description: String
    public let tags: [String]
    public let hats: [String]
    public let backends: [String]
    public let autoInject: Bool
    public let source: String  // "built-in" | "file"

    public var id: String { name }

    public enum CodingKeys: String, CodingKey {
        case name
        case description
        case tags
        case hats
        case backends
        case autoInject = "auto_inject"
        case source
    }

    /// Whether this is a built-in skill
    public var isBuiltIn: Bool {
        source == "built-in"
    }

    /// Icon for the skill source type
    public var sourceIcon: String {
        isBuiltIn ? "cube.fill" : "doc.text"
    }

    public init(
        name: String,
        description: String,
        tags: [String],
        hats: [String],
        backends: [String],
        autoInject: Bool,
        source: String
    ) {
        self.name = name
        self.description = description
        self.tags = tags
        self.hats = hats
        self.backends = backends
        self.autoInject = autoInject
        self.source = source
    }
}

/// Response for GET /api/skills
public struct SkillsListResponse: Decodable {
    public let skills: [Skill]
    public let count: Int

    public init(skills: [Skill], count: Int) {
        self.skills = skills
        self.count = count
    }
}

/// Response for GET /api/skills/{name}
public struct SkillMetadataResponse: Decodable {
    public let name: String
    public let description: String
    public let tags: [String]
    public let hats: [String]
    public let backends: [String]
    public let autoInject: Bool
    public let source: String

    public enum CodingKeys: String, CodingKey {
        case name
        case description
        case tags
        case hats
        case backends
        case autoInject = "auto_inject"
        case source
    }

    public init(
        name: String,
        description: String,
        tags: [String],
        hats: [String],
        backends: [String],
        autoInject: Bool,
        source: String
    ) {
        self.name = name
        self.description = description
        self.tags = tags
        self.hats = hats
        self.backends = backends
        self.autoInject = autoInject
        self.source = source
    }
}

/// Response for POST /api/skills/{name}/load
public struct SkillContentResponse: Decodable {
    public let name: String
    public let content: String  // XML-wrapped content

    public init(name: String, content: String) {
        self.name = name
        self.content = content
    }
}
