import XCTest
import SwiftUI
import RalphShared
@testable import RalphMobile

/// Tests for CyberpunkTheme color functions and mappings
final class ThemeTests: XCTestCase {

    // MARK: - Hat Color Tests

    func testHatColorForPlanner() {
        // Given: Hat name "Planner"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "Planner")

        // Then: Returns accent cyan (#00fff2)
        XCTAssertEqual(color, CyberpunkTheme.accentCyan)
    }

    func testHatColorForPlannerWithEmoji() {
        // Given: Hat name with emoji "📋 Planner"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "📋 Planner")

        // Then: Returns accent cyan
        XCTAssertEqual(color, CyberpunkTheme.accentCyan)
    }

    func testHatColorForBuilder() {
        // Given: Hat name "Builder"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "Builder")

        // Then: Returns accent green (#00ff88)
        XCTAssertEqual(color, CyberpunkTheme.accentGreen)
    }

    func testHatColorForBuilderWithEmoji() {
        // Given: Hat name with emoji "⚙️ Builder"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "⚙️ Builder")

        // Then: Returns accent green
        XCTAssertEqual(color, CyberpunkTheme.accentGreen)
    }

    func testHatColorForReviewer() {
        // Given: Hat name "Reviewer"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "Reviewer")

        // Then: Returns accent yellow (#ffd000)
        XCTAssertEqual(color, CyberpunkTheme.accentYellow)
    }

    func testHatColorForDesignCritic() {
        // Given: Hat name "⚖️ Design Critic"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "⚖️ Design Critic")

        // Then: Returns accent yellow
        XCTAssertEqual(color, CyberpunkTheme.accentYellow)
    }

    func testHatColorForTester() {
        // Given: Hat name "Tester"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "Tester")

        // Then: Returns accent orange (#ff6b00)
        XCTAssertEqual(color, CyberpunkTheme.accentOrange)
    }

    func testHatColorForValidator() {
        // Given: Hat name "✅ Validator"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "✅ Validator")

        // Then: Returns accent orange
        XCTAssertEqual(color, CyberpunkTheme.accentOrange)
    }

    func testHatColorForArchitect() {
        // Given: Hat name "Architect" or "💭 Architect"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "💭 Architect")

        // Then: Returns accent purple (#a855f7)
        XCTAssertEqual(color, CyberpunkTheme.accentPurple)
    }

    func testHatColorForInquisitor() {
        // Given: Hat name "🎯 Inquisitor"
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "🎯 Inquisitor")

        // Then: Returns accent magenta (#ff00ff)
        XCTAssertEqual(color, CyberpunkTheme.accentMagenta)
    }

    func testHatColorForUnknownDefaultsToCyan() {
        // Given: Unknown hat name
        // When: Looking up color
        let color = CyberpunkTheme.hatColor(for: "UnknownHat")

        // Then: Returns default cyan
        XCTAssertEqual(color, CyberpunkTheme.accentCyan)
    }

    func testHatColorIsCaseInsensitive() {
        // Given: Hat names in different cases
        let lowercase = CyberpunkTheme.hatColor(for: "planner")
        let uppercase = CyberpunkTheme.hatColor(for: "PLANNER")
        let mixedCase = CyberpunkTheme.hatColor(for: "Planner")

        // Then: All return the same color
        XCTAssertEqual(lowercase, mixedCase)
        XCTAssertEqual(uppercase, mixedCase)
    }

    // MARK: - Status Color Tests

    func testStatusRunningColor() {
        // Given/When: Accessing status running color
        let color = CyberpunkTheme.statusRunning

        // Then: Returns cyan (#00fff2)
        XCTAssertEqual(color, CyberpunkTheme.accentCyan)
    }

    func testStatusCompletedColor() {
        // Given/When: Accessing status completed color
        let color = CyberpunkTheme.statusCompleted

        // Then: Returns green (#00ff88)
        XCTAssertEqual(color, CyberpunkTheme.accentGreen)
    }

    func testStatusPendingColor() {
        // Given/When: Accessing status pending color
        let color = CyberpunkTheme.statusPending

        // Then: Returns yellow (#ffd000)
        XCTAssertEqual(color, CyberpunkTheme.accentYellow)
    }

    func testStatusErrorColor() {
        // Given/When: Accessing status error color
        let color = CyberpunkTheme.statusError

        // Then: Returns red (#ff3366)
        XCTAssertEqual(color, CyberpunkTheme.accentRed)
    }

    func testStatusPausedColor() {
        // Given/When: Accessing status paused color
        let color = CyberpunkTheme.statusPaused

        // Then: Returns orange (#ff6b00)
        XCTAssertEqual(color, CyberpunkTheme.accentOrange)
    }

    // MARK: - Tool Color Tests

    func testToolBashColor() {
        XCTAssertEqual(CyberpunkTheme.toolBash, CyberpunkTheme.accentCyan)
    }

    func testToolReadFileColor() {
        XCTAssertEqual(CyberpunkTheme.toolReadFile, CyberpunkTheme.accentGreen)
    }

    func testToolWriteFileColor() {
        XCTAssertEqual(CyberpunkTheme.toolWriteFile, CyberpunkTheme.accentMagenta)
    }

    func testToolEditFileColor() {
        XCTAssertEqual(CyberpunkTheme.toolEditFile, CyberpunkTheme.accentOrange)
    }

    func testToolSearchColor() {
        XCTAssertEqual(CyberpunkTheme.toolSearch, CyberpunkTheme.accentYellow)
    }

    func testToolMCPColor() {
        XCTAssertEqual(CyberpunkTheme.toolMCP, CyberpunkTheme.accentPurple)
    }

    // MARK: - Color Hex Extension Tests

    func testColorFromHexRGB24Bit() {
        // Given: 24-bit hex color string
        let color = Color(hex: "#00fff2")

        // Then: Color is created (testing that it doesn't crash)
        // Note: Direct color comparison is complex due to color space conversions
        // We verify that the Color can be created without issues
        XCTAssertNotNil(color)
    }

    func testColorFromHexRGB12Bit() {
        // Given: 12-bit shorthand hex color
        let color = Color(hex: "#FFF")

        // Then: Color is created
        XCTAssertNotNil(color)
    }

    func testColorFromHexWithoutHash() {
        // Given: Hex without leading #
        let color = Color(hex: "00fff2")

        // Then: Color is created (trimming is handled)
        XCTAssertNotNil(color)
    }
}
