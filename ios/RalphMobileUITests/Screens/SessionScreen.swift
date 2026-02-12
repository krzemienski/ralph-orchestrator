import XCTest

/// Page object for Session Detail view.
class SessionScreen {

    let app: XCUIApplication
    let helper: TestHelper

    init(app: XCUIApplication) {
        self.app = app
        self.helper = TestHelper(app: app)
    }

    // MARK: - Elements

    var view: XCUIElement {
        app.otherElements[AccessibilityID.SessionDetail.view]
    }

    var header: XCUIElement {
        app.otherElements[AccessibilityID.SessionDetail.header]
    }

    var statusBadge: XCUIElement {
        app.staticTexts[AccessibilityID.SessionDetail.statusBadge]
    }

    var configName: XCUIElement {
        app.staticTexts[AccessibilityID.SessionDetail.configName]
    }

    var promptText: XCUIElement {
        app.staticTexts[AccessibilityID.SessionDetail.promptText]
    }

    var eventFeed: XCUIElement {
        app.scrollViews[AccessibilityID.SessionDetail.eventFeed]
    }

    var eventCount: XCUIElement {
        app.staticTexts[AccessibilityID.SessionDetail.eventCount]
    }

    var stopButton: XCUIElement {
        app.buttons[AccessibilityID.SessionDetail.stopButton]
    }

    var steeringButton: XCUIElement {
        app.buttons[AccessibilityID.SessionDetail.steeringButton]
    }

    // MARK: - Status Header Elements

    var connectionIndicator: XCUIElement {
        app.otherElements[AccessibilityID.StatusHeader.connectionIndicator]
    }

    var hatDisplay: XCUIElement {
        app.staticTexts[AccessibilityID.StatusHeader.hatDisplay]
    }

    var iterationCount: XCUIElement {
        app.staticTexts[AccessibilityID.StatusHeader.iterationCount]
    }

    var tokenCount: XCUIElement {
        app.staticTexts[AccessibilityID.StatusHeader.tokenCount]
    }

    // MARK: - Session List Elements

    var sessionList: XCUIElement {
        app.collectionViews[AccessibilityID.SessionList.list]
    }

    var sessionRows: XCUIElementQuery {
        app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "session-row-"))
    }

    // MARK: - Actions

    /// Navigates to sessions list.
    func navigateToList() {
        helper.navigateToSessions()
    }

    /// Selects a session by index.
    func selectSession(at index: Int) {
        let row = sessionRows.element(boundBy: index)
        if helper.waitForHittable(row) {
            row.tap()
        }
    }

    /// Selects a session by ID.
    func selectSession(id: String) {
        let row = app.buttons[AccessibilityID.SessionList.row(id: id)]
        if helper.waitForHittable(row) {
            row.tap()
        }
    }

    /// Stops the current session.
    func stopSession() {
        if helper.waitForHittable(stopButton) {
            stopButton.tap()
        }
    }

    /// Opens steering/guidance input.
    func openSteering() {
        if helper.waitForHittable(steeringButton) {
            steeringButton.tap()
        }
    }

    /// Sends steering guidance to the session.
    func sendSteering(_ text: String) {
        openSteering()

        // Wait for input sheet and type
        let steeringInput = app.textViews.firstMatch
        if helper.waitForHittable(steeringInput) {
            steeringInput.tap()
            steeringInput.typeText(text)
        }

        // Submit
        let submitButton = app.buttons["steering-submit"]
        if helper.waitForHittable(submitButton) {
            submitButton.tap()
        }
    }

    /// Gets the current hat from the status header.
    func getCurrentHat() -> String? {
        guard helper.waitForElement(hatDisplay) else { return nil }
        return hatDisplay.label
    }

    /// Gets the current iteration count.
    func getIterationCount() -> Int? {
        guard helper.waitForElement(iterationCount) else { return nil }
        let text = iterationCount.label
        return Int(text.components(separatedBy: CharacterSet.decimalDigits.inverted).joined())
    }

    /// Gets the current status.
    func getStatus() -> String? {
        guard helper.waitForElement(statusBadge) else { return nil }
        return statusBadge.label
    }

    /// Checks if session is running.
    func isRunning() -> Bool {
        guard let status = getStatus() else { return false }
        return status.lowercased().contains("running") || status.lowercased().contains("active")
    }

    /// Waits for session to complete.
    @discardableResult
    func waitForCompletion(timeout: TimeInterval = 300) -> Bool {
        let predicate = NSPredicate { _, _ in
            !self.isRunning()
        }
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: nil)
        return XCTWaiter.wait(for: [expectation], timeout: timeout) == .completed
    }

    // MARK: - Assertions

    /// Asserts session detail is visible.
    func assertVisible() {
        XCTAssertTrue(helper.waitForElement(view), "Session detail should be visible")
    }

    /// Asserts session is running.
    func assertRunning() {
        XCTAssertTrue(isRunning(), "Session should be running")
    }

    /// Asserts event feed is visible.
    func assertEventFeedVisible() {
        XCTAssertTrue(helper.waitForElement(eventFeed), "Event feed should be visible")
    }

    /// Asserts stop button is available.
    func assertStopButtonEnabled() {
        XCTAssertTrue(helper.waitForHittable(stopButton), "Stop button should be enabled")
    }
}
