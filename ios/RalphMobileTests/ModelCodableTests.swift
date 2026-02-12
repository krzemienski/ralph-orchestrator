import XCTest
import RalphShared
@testable import RalphMobile

/// Tests for Model Codable conformance (Session, Event, Config, BackpressureStatus)
final class ModelCodableTests: XCTestCase {

    // MARK: - Session Tests

    func testSessionDecodesFromValidJSON() throws {
        // Given: Valid Ralph session JSON from API
        let json = """
        {
            "id": "session-123",
            "iteration": 5,
            "total": 10,
            "hat": "Builder",
            "elapsed_secs": 1425,
            "mode": "tdd",
            "started_at": "2026-01-21T15:30:00.000Z",
            "status": "running",
            "trigger_event": "task.start",
            "publishes": ["task.complete", "build.blocked"]
        }
        """.data(using: .utf8)!

        // When: Decoding with JSONDecoder
        let decoder = JSONDecoder()
        let session = try decoder.decode(Session.self, from: json)

        // Then: Session instance is created with correct properties
        XCTAssertEqual(session.id, "session-123")
        XCTAssertEqual(session.iteration, 5)
        XCTAssertEqual(session.total, 10)
        XCTAssertEqual(session.hat, "Builder")
        XCTAssertEqual(session.elapsedSeconds, 1425)
        XCTAssertEqual(session.mode, "tdd")
        XCTAssertEqual(session.status, "running")
        XCTAssertEqual(session.triggerEvent, "task.start")
        XCTAssertEqual(session.availablePublishes, ["task.complete", "build.blocked"])
    }

    func testSessionHandlesISO8601Dates() throws {
        // Given: Session JSON with ISO8601 timestamp
        let json = """
        {
            "id": "session-456",
            "iteration": 1,
            "started_at": "2026-01-21T10:30:45.123Z"
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        let session = try decoder.decode(Session.self, from: json)

        // Then: startTime parses correctly
        XCTAssertNotNil(session.startTime)
        let calendar = Calendar(identifier: .gregorian)
        var components = calendar.dateComponents(in: TimeZone(identifier: "UTC")!, from: session.startTime!)
        XCTAssertEqual(components.year, 2026)
        XCTAssertEqual(components.month, 1)
        XCTAssertEqual(components.day, 21)
        XCTAssertEqual(components.hour, 10)
        XCTAssertEqual(components.minute, 30)
    }

    func testSessionHandlesMissingOptionalFields() throws {
        // Given: Minimal session JSON with only required fields
        let json = """
        {
            "id": "session-minimal",
            "iteration": 0
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        let session = try decoder.decode(Session.self, from: json)

        // Then: Optional fields are nil
        XCTAssertEqual(session.id, "session-minimal")
        XCTAssertEqual(session.iteration, 0)
        XCTAssertNil(session.total)
        XCTAssertNil(session.hat)
        XCTAssertNil(session.elapsedSeconds)
        XCTAssertNil(session.mode)
        XCTAssertNil(session.startedAt)
        XCTAssertNil(session.status)
        XCTAssertNil(session.startTime)
    }

    // MARK: - Event Tests

    func testEventDecodesWithAllFields() throws {
        // Given: Full event JSON with timestamp
        let json = """
        {
            "ts": "2026-01-21T15:30:00.000Z",
            "topic": "task.complete",
            "payload": "Build successful",
            "iteration": 5,
            "hat": "Builder",
            "triggered": "task.start",
            "type": "event.published"
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let event = try decoder.decode(Event.self, from: json)

        // Then: All fields populated correctly
        XCTAssertEqual(event.topic, "task.complete")
        XCTAssertEqual(event.payload, "Build successful")
        XCTAssertEqual(event.iteration, 5)
        XCTAssertEqual(event.hat, "Builder")
        XCTAssertEqual(event.triggered, "task.start")
        XCTAssertEqual(event.type, "event.published")
    }

    func testEventHandlesMissingOptionalFields() throws {
        // Given: Event JSON with missing optional fields
        let json = """
        {
            "ts": "2026-01-21T15:30:00.000Z",
            "type": "tool.call"
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let event = try decoder.decode(Event.self, from: json)

        // Then: Event instance created with nil optionals
        XCTAssertNil(event.topic)
        XCTAssertNil(event.payload)
        XCTAssertNil(event.iteration)
        XCTAssertNil(event.hat)
        XCTAssertNil(event.toolName)
        XCTAssertNil(event.status)
        XCTAssertNil(event.output)
    }

    func testEventDefaultsTypeToEventPublished() throws {
        // Given: Event JSON without type field
        let json = """
        {
            "ts": "2026-01-21T15:30:00.000Z",
            "topic": "test.event"
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let event = try decoder.decode(Event.self, from: json)

        // Then: Type defaults to "event.published"
        XCTAssertEqual(event.type, "event.published")
    }

    // MARK: - Config Tests

    func testConfigDecodesCorrectly() throws {
        // Given: Config JSON
        let json = """
        {
            "path": "presets/feature.yml",
            "name": "feature",
            "description": "Feature development preset"
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        let config = try decoder.decode(Config.self, from: json)

        // Then: Config instance created correctly
        XCTAssertEqual(config.path, "presets/feature.yml")
        XCTAssertEqual(config.name, "feature")
        XCTAssertEqual(config.description, "Feature development preset")
        XCTAssertEqual(config.id, "presets/feature.yml") // id is path
    }

    // MARK: - BackpressureStatus Tests

    func testBackpressureStatusDecodesBoolValues() throws {
        // Given: Backpressure JSON with bool values
        let json = """
        {
            "tests": true,
            "lint": true,
            "typecheck": false
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        let status = try decoder.decode(BackpressureStatus.self, from: json)

        // Then: Bool values parsed correctly
        XCTAssertTrue(status.testsPass)
        XCTAssertTrue(status.lintPass)
        XCTAssertFalse(status.typecheckPass)
    }

    func testBackpressureStatusDecodesStringValues() throws {
        // Given: Backpressure JSON with string values (legacy format)
        let json = """
        {
            "tests": "pass",
            "lint": "PASS",
            "typecheck": "fail"
        }
        """.data(using: .utf8)!

        // When: Decoding
        let decoder = JSONDecoder()
        let status = try decoder.decode(BackpressureStatus.self, from: json)

        // Then: String values converted to bools correctly
        XCTAssertTrue(status.testsPass)
        XCTAssertTrue(status.lintPass)
        XCTAssertFalse(status.typecheckPass)
    }
}
