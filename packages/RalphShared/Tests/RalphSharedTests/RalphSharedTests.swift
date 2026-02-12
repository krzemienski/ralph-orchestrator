import XCTest
@testable import RalphShared

final class RalphSharedTests: XCTestCase {
    func testSessionDecoding() throws {
        let json = """
        {"id":"abc-123","iteration":5,"hat":"planner","started_at":"2026-02-10T12:00:00Z"}
        """
        let data = json.data(using: .utf8)!
        let session = try JSONDecoder().decode(Session.self, from: data)
        XCTAssertEqual(session.id, "abc-123")
        XCTAssertEqual(session.iteration, 5)
        XCTAssertEqual(session.hat, "planner")
    }
}
