import XCTest

/// Page object for the Dashboard view.
class DashboardScreen {

    let app: XCUIApplication
    let helper: TestHelper

    init(app: XCUIApplication) {
        self.app = app
        self.helper = TestHelper(app: app)
    }

    // MARK: - Elements

    var view: XCUIElement {
        app.otherElements[AccessibilityID.Dashboard.view]
    }

    var header: XCUIElement {
        app.otherElements[AccessibilityID.Dashboard.header]
    }

    var serverStatus: XCUIElement {
        app.staticTexts[AccessibilityID.Dashboard.serverStatus]
    }

    var activeSessionsCount: XCUIElement {
        app.staticTexts[AccessibilityID.Dashboard.activeSessionsCount]
    }

    var startButton: XCUIElement {
        app.buttons[AccessibilityID.Dashboard.startButton]
    }

    var recentSessions: XCUIElement {
        app.scrollViews[AccessibilityID.Dashboard.recentSessions]
    }

    // MARK: - Actions

    /// Navigates to this screen.
    func navigate() {
        helper.navigateToDashboard()
    }

    /// Taps the start button to begin a new session.
    func tapStart() {
        helper.waitForHittable(startButton)
        startButton.tap()
    }

    /// Gets the number of active sessions displayed.
    func getActiveSessionCount() -> Int? {
        guard helper.waitForElement(activeSessionsCount) else { return nil }
        guard let text = activeSessionsCount.label as String? else { return nil }
        return Int(text.components(separatedBy: CharacterSet.decimalDigits.inverted).joined())
    }

    /// Checks if server is connected.
    func isServerConnected() -> Bool {
        guard helper.waitForElement(serverStatus) else { return false }
        let status = serverStatus.label.lowercased()
        return status.contains("connected") || status.contains("online")
    }

    // MARK: - Assertions

    /// Asserts the dashboard is visible.
    func assertVisible() {
        XCTAssertTrue(helper.waitForElement(view), "Dashboard view should be visible")
    }

    /// Asserts start button is available.
    func assertStartButtonEnabled() {
        XCTAssertTrue(helper.waitForHittable(startButton), "Start button should be enabled")
    }

    /// Asserts server is connected.
    func assertServerConnected() {
        XCTAssertTrue(isServerConnected(), "Server should be connected")
    }
}
