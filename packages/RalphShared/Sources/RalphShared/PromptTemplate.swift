import Foundation

/// A reusable prompt template for Ralph workflows.
/// Templates can be bundled (read-only) or custom (user-created, editable).
public struct PromptTemplate: Codable, Identifiable, Hashable {
    public let id: UUID
    public var name: String
    public var content: String
    public var description: String
    public var isBundled: Bool
    public var createdAt: Date
    public var updatedAt: Date

    public enum CodingKeys: String, CodingKey {
        case id
        case name
        case content
        case description
        case isBundled
        case createdAt
        case updatedAt
    }

    public init(
        id: UUID,
        name: String,
        content: String,
        description: String,
        isBundled: Bool,
        createdAt: Date,
        updatedAt: Date
    ) {
        self.id = id
        self.name = name
        self.content = content
        self.description = description
        self.isBundled = isBundled
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    /// The 4 bundled prompt templates (read-only).
    public static let bundled: [PromptTemplate] = [
        PromptTemplate(
            id: UUID(uuidString: "00000000-0000-0000-0001-000000000001")!,
            name: "Design Start",
            content: """
            # Design Task

            ## Objective
            [Describe what you want to design]

            ## Requirements
            - Functional requirement 1
            - Non-functional requirement 1

            ## Constraints
            - Time constraint
            - Technology constraint

            ## Success Criteria
            - Criterion 1
            - Criterion 2
            """,
            description: "Start a new design workflow",
            isBundled: true,
            createdAt: Date(timeIntervalSince1970: 0),
            updatedAt: Date(timeIntervalSince1970: 0)
        ),
        PromptTemplate(
            id: UUID(uuidString: "00000000-0000-0000-0001-000000000002")!,
            name: "Task Start",
            content: """
            # Implementation Task

            ## Goal
            [What should be implemented]

            ## Context
            [Relevant background information]

            ## Acceptance Criteria
            - [ ] Criterion 1
            - [ ] Criterion 2

            ## Notes
            [Any additional considerations]
            """,
            description: "Begin implementation task",
            isBundled: true,
            createdAt: Date(timeIntervalSince1970: 0),
            updatedAt: Date(timeIntervalSince1970: 0)
        ),
        PromptTemplate(
            id: UUID(uuidString: "00000000-0000-0000-0001-000000000003")!,
            name: "Code Review",
            content: """
            # Code Review Request

            ## Files to Review
            - `path/to/file.swift`

            ## Focus Areas
            - [ ] Code quality
            - [ ] Performance
            - [ ] Security

            ## Context
            [What does this code do]
            """,
            description: "Review code for quality",
            isBundled: true,
            createdAt: Date(timeIntervalSince1970: 0),
            updatedAt: Date(timeIntervalSince1970: 0)
        ),
        PromptTemplate(
            id: UUID(uuidString: "00000000-0000-0000-0001-000000000004")!,
            name: "Debug Issue",
            content: """
            # Debug Request

            ## Issue
            [Describe the bug]

            ## Expected Behavior
            [What should happen]

            ## Actual Behavior
            [What actually happens]

            ## Steps to Reproduce
            1. Step 1
            2. Step 2
            3. Step 3

            ## Relevant Logs
            ```
            [Paste logs here]
            ```
            """,
            description: "Debug and fix a problem",
            isBundled: true,
            createdAt: Date(timeIntervalSince1970: 0),
            updatedAt: Date(timeIntervalSince1970: 0)
        )
    ]
}
