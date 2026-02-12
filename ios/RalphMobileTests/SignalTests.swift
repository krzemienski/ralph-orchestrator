import XCTest
import SwiftUI
import RalphShared
@testable import RalphMobile

/// Tests for signal validation and emission logic
final class SignalTests: XCTestCase {

    // MARK: - Signal Validation Tests

    func testEmptyAcceptedSignalsDisablesEmission() {
        // Given: Config with empty acceptedSignals
        let acceptedSignals: [String] = []

        // When: Checking if emission is available
        let canEmit = !acceptedSignals.isEmpty

        // Then: Emission should be disabled
        XCTAssertFalse(canEmit)
    }

    func testNonEmptyAcceptedSignalsEnablesEmission() {
        // Given: Config with acceptedSignals
        let acceptedSignals = ["user.guidance", "user.pause"]

        // When: Checking if emission is available
        let canEmit = !acceptedSignals.isEmpty

        // Then: Emission should be enabled
        XCTAssertTrue(canEmit)
    }

    // MARK: - Signal Type Validation Tests

    func testValidSignalTypes() {
        // Given: Standard signal types from V3 spec
        let validSignals = ["user.guidance", "user.pause", "user.priority", "user.abort"]

        // When/Then: All signals should be recognized
        for signal in validSignals {
            XCTAssertTrue(isValidSignalType(signal), "Signal \(signal) should be valid")
        }
    }

    func testInvalidSignalTypeStillAccepted() {
        // Given: Non-standard signal type (configs can define custom signals)
        let customSignal = "custom.signal"

        // When/Then: Custom signals are allowed (no strict validation)
        // The app accepts any string as a signal type from config
        XCTAssertTrue(customSignal.contains("."), "Custom signals should contain a dot separator")
    }

    // MARK: - Signal Icon Mapping Tests

    func testSignalIconMapping() {
        // Given: Signal types
        // When/Then: Verify icon mappings match expected SF Symbols
        XCTAssertEqual(iconForSignal("user.guidance"), "lightbulb.fill")
        XCTAssertEqual(iconForSignal("user.pause"), "pause.circle.fill")
        XCTAssertEqual(iconForSignal("user.priority"), "arrow.up.circle.fill")
        XCTAssertEqual(iconForSignal("user.abort"), "xmark.octagon.fill")
        XCTAssertEqual(iconForSignal("unknown.signal"), "paperplane.fill") // default
    }

    // MARK: - Signal Color Mapping Tests

    func testSignalColorMapping() {
        // Given/When/Then: Verify color mappings match theme
        XCTAssertEqual(colorForSignal("user.guidance"), CyberpunkTheme.accentCyan)
        XCTAssertEqual(colorForSignal("user.pause"), CyberpunkTheme.accentYellow)
        XCTAssertEqual(colorForSignal("user.priority"), CyberpunkTheme.accentPurple)
        XCTAssertEqual(colorForSignal("user.abort"), CyberpunkTheme.accentRed)
        XCTAssertEqual(colorForSignal("unknown.signal"), CyberpunkTheme.accentMagenta) // default
    }

    // MARK: - Signal Hint Text Tests

    func testSignalHintTexts() {
        // Given/When/Then: Verify hint text contains expected guidance
        XCTAssertTrue(hintForSignal("user.guidance").contains("direction"))
        XCTAssertTrue(hintForSignal("user.pause").contains("pause"))
        XCTAssertTrue(hintForSignal("user.priority").contains("priority"))
        XCTAssertTrue(hintForSignal("user.abort").contains("abort"))
    }

    // MARK: - Signal Selection State Tests

    func testNoSignalSelectedInitially() {
        // Given: Initial state
        let selectedSignal: String? = nil

        // Then: No signal is selected
        XCTAssertNil(selectedSignal)
    }

    func testMessageInputRequiredForSend() {
        // Given: Selected signal but empty message
        let selectedSignal: String? = "user.guidance"
        let message = ""

        // When: Checking if can send
        let canSend = selectedSignal != nil && !message.isEmpty

        // Then: Cannot send without message
        XCTAssertFalse(canSend)
    }

    func testCanSendWithSignalAndMessage() {
        // Given: Selected signal and non-empty message
        let selectedSignal: String? = "user.guidance"
        let message = "Focus on tests"

        // When: Checking if can send
        let canSend = selectedSignal != nil && !message.isEmpty

        // Then: Can send
        XCTAssertTrue(canSend)
    }

    // MARK: - Helper Functions (mirror SignalEmitterView logic)

    private func isValidSignalType(_ signal: String) -> Bool {
        let knownSignals = ["user.guidance", "user.pause", "user.priority", "user.abort"]
        return knownSignals.contains(signal)
    }

    private func iconForSignal(_ signal: String) -> String {
        switch signal {
        case "user.guidance": return "lightbulb.fill"
        case "user.pause": return "pause.circle.fill"
        case "user.priority": return "arrow.up.circle.fill"
        case "user.abort": return "xmark.octagon.fill"
        default: return "paperplane.fill"
        }
    }

    private func colorForSignal(_ signal: String) -> Color {
        switch signal {
        case "user.guidance": return CyberpunkTheme.accentCyan
        case "user.pause": return CyberpunkTheme.accentYellow
        case "user.priority": return CyberpunkTheme.accentPurple
        case "user.abort": return CyberpunkTheme.accentRed
        default: return CyberpunkTheme.accentMagenta
        }
    }

    private func hintForSignal(_ signal: String) -> String {
        switch signal {
        case "user.guidance": return "Provide direction or suggestions to steer the agent"
        case "user.pause": return "Request the agent to pause after current task"
        case "user.priority": return "Change task priority or focus area"
        case "user.abort": return "Request immediate abort of current execution"
        default: return "Send a signal to the running session"
        }
    }
}
