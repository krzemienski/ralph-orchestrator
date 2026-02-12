import XCTest
@testable import RalphMobile

/// Tests for utility functions including time formatting
final class UtilityTests: XCTestCase {

    // MARK: - Time Formatting Tests (HH:MM:SS)

    func testFormatTime1425SecondsReturns002345() {
        // Given: 1425 seconds (23 minutes, 45 seconds)
        let seconds = 1425

        // When: Formatting
        let result = TimeFormatting.formatTime(seconds)

        // Then: Returns "00:23:45"
        XCTAssertEqual(result, "00:23:45")
    }

    func testFormatTimeZeroReturns000000() {
        // Given: 0 seconds
        let seconds = 0

        // When: Formatting
        let result = TimeFormatting.formatTime(seconds)

        // Then: Returns "00:00:00"
        XCTAssertEqual(result, "00:00:00")
    }

    func testFormatTimeOneHourReturns010000() {
        // Given: 3600 seconds (1 hour)
        let seconds = 3600

        // When: Formatting
        let result = TimeFormatting.formatTime(seconds)

        // Then: Returns "01:00:00"
        XCTAssertEqual(result, "01:00:00")
    }

    func testFormatTime86399ReturnsAlmostFullDay() {
        // Given: 86399 seconds (23:59:59)
        let seconds = 86399

        // When: Formatting
        let result = TimeFormatting.formatTime(seconds)

        // Then: Returns "23:59:59"
        XCTAssertEqual(result, "23:59:59")
    }

    func testFormatTimeHandlesMultipleHours() {
        // Given: 12 hours, 34 minutes, 56 seconds = 45296 seconds
        let seconds = (12 * 3600) + (34 * 60) + 56

        // When: Formatting
        let result = TimeFormatting.formatTime(seconds)

        // Then: Returns "12:34:56"
        XCTAssertEqual(result, "12:34:56")
    }

    // MARK: - Elapsed Time Formatting Tests (MM:SS)

    func testFormatElapsed90SecondsReturns0130() {
        // Given: 90 seconds
        let seconds = 90

        // When: Formatting
        let result = TimeFormatting.formatElapsed(seconds)

        // Then: Returns "01:30"
        XCTAssertEqual(result, "01:30")
    }

    func testFormatElapsedZeroReturns0000() {
        // Given: 0 seconds
        let seconds = 0

        // When: Formatting
        let result = TimeFormatting.formatElapsed(seconds)

        // Then: Returns "00:00"
        XCTAssertEqual(result, "00:00")
    }

    func testFormatElapsed59SecondsReturns0059() {
        // Given: 59 seconds
        let seconds = 59

        // When: Formatting
        let result = TimeFormatting.formatElapsed(seconds)

        // Then: Returns "00:59"
        XCTAssertEqual(result, "00:59")
    }

    func testFormatElapsedOneHourReturns6000() {
        // Given: 3600 seconds (60 minutes)
        let seconds = 3600

        // When: Formatting
        let result = TimeFormatting.formatElapsed(seconds)

        // Then: Returns "60:00" (minutes can exceed 59)
        XCTAssertEqual(result, "60:00")
    }

    func testFormatElapsedPadsSingleDigits() {
        // Given: 5 seconds
        let seconds = 5

        // When: Formatting
        let result = TimeFormatting.formatElapsed(seconds)

        // Then: Returns "00:05" (padded)
        XCTAssertEqual(result, "00:05")
    }
}
