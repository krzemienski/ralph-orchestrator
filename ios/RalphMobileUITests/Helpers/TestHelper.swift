import XCTest

/// Common test utilities and helpers for XCUITests.
class TestHelper {

    let app: XCUIApplication

    init(app: XCUIApplication) {
        self.app = app
    }

    // MARK: - Wait Helpers

    /// Waits for an element to exist with timeout.
    @discardableResult
    func waitForElement(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        element.waitForExistence(timeout: timeout)
    }

    /// Waits for an element to be hittable (visible and enabled).
    @discardableResult
    func waitForHittable(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        let predicate = NSPredicate(format: "isHittable == true")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }

    /// Waits for an element to disappear.
    @discardableResult
    func waitForDisappear(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        let predicate = NSPredicate(format: "exists == false")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }

    /// Waits for element count to reach expected value.
    @discardableResult
    func waitForCount(_ query: XCUIElementQuery, count: Int, timeout: TimeInterval = 5) -> Bool {
        let predicate = NSPredicate(format: "count == %d", count)
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: query)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }

    /// Waits for element count to be at least the expected value.
    @discardableResult
    func waitForMinCount(_ query: XCUIElementQuery, minCount: Int, timeout: TimeInterval = 5) -> Bool {
        let predicate = NSPredicate(format: "count >= %d", minCount)
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: query)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }

    // MARK: - Navigation Helpers

    /// Navigates to a specific tab.
    func navigateToTab(_ tabIdentifier: String) {
        let tab = app.buttons[tabIdentifier]
        if waitForHittable(tab) {
            tab.tap()
        }
    }

    /// Navigates to Dashboard tab.
    func navigateToDashboard() {
        navigateToTab(AccessibilityID.Navigation.dashboardTab)
    }

    /// Navigates to Sessions tab.
    func navigateToSessions() {
        navigateToTab(AccessibilityID.Navigation.sessionsTab)
    }

    /// Navigates to Library tab.
    func navigateToLibrary() {
        navigateToTab(AccessibilityID.Navigation.libraryTab)
    }

    /// Navigates to Settings tab.
    func navigateToSettings() {
        navigateToTab(AccessibilityID.Navigation.settingsTab)
    }

    // MARK: - Screenshot Helpers

    /// Captures a screenshot and attaches it to the test results.
    func captureScreenshot(name: String, folder: String, testCase: XCTestCase) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "\(folder)/\(name)"
        attachment.lifetime = .keepAlways
        testCase.add(attachment)
    }

    // MARK: - Settings Helpers

    /// Configures server settings for testing.
    func configureServer(url: String, key: String) {
        navigateToSettings()

        let urlField = app.textFields[AccessibilityID.Settings.serverURL]
        if waitForHittable(urlField) {
            urlField.tap()
            urlField.clearAndTypeText(url)
        }

        let keyField = app.secureTextFields[AccessibilityID.Settings.serverKey]
        if waitForHittable(keyField) {
            keyField.tap()
            keyField.clearAndTypeText(key)
        }

        // Save settings
        let saveButton = app.buttons[AccessibilityID.Settings.saveButton]
        if waitForHittable(saveButton) {
            saveButton.tap()
        }
    }

    /// Tests connection to server.
    @discardableResult
    func testConnection(timeout: TimeInterval = 10) -> Bool {
        let testButton = app.buttons[AccessibilityID.Settings.testConnectionButton]
        if waitForHittable(testButton) {
            testButton.tap()
        }

        // Wait for connection status to update
        let status = app.staticTexts[AccessibilityID.Settings.connectionStatus]
        return waitForElement(status, timeout: timeout)
    }

    // MARK: - Session Helpers

    /// Starts a new session with given config and prompt.
    func startSession(config: String? = nil, prompt: String) {
        navigateToDashboard()

        let startButton = app.buttons[AccessibilityID.Dashboard.startButton]
        if waitForHittable(startButton) {
            startButton.tap()
        }

        // Wait for sheet
        let sheet = app.otherElements[AccessibilityID.StartRun.sheet]
        guard waitForElement(sheet) else { return }

        // Select config if provided
        if let config = config {
            let configPicker = app.buttons[AccessibilityID.StartRun.configPicker]
            if waitForHittable(configPicker) {
                configPicker.tap()
                let configItem = app.buttons[AccessibilityID.Config.item(name: config)]
                if waitForHittable(configItem) {
                    configItem.tap()
                }
            }
        }

        // Enter prompt
        let promptField = app.textViews[AccessibilityID.StartRun.promptField]
        if waitForHittable(promptField) {
            promptField.tap()
            promptField.typeText(prompt)
        }

        // Start
        let runButton = app.buttons[AccessibilityID.StartRun.startButton]
        if waitForHittable(runButton) {
            runButton.tap()
        }
    }

    /// Stops the current session.
    func stopSession() {
        let stopButton = app.buttons[AccessibilityID.SessionDetail.stopButton]
        if waitForHittable(stopButton) {
            stopButton.tap()
        }
    }

    /// Waits for session to start streaming events.
    @discardableResult
    func waitForSessionActive(timeout: TimeInterval = 30) -> Bool {
        let eventFeed = app.scrollViews[AccessibilityID.SessionDetail.eventFeed]
        return waitForElement(eventFeed, timeout: timeout)
    }

    /// Waits for at least N events to appear.
    @discardableResult
    func waitForEvents(count: Int, timeout: TimeInterval = 60) -> Bool {
        let eventRows = app.otherElements.matching(identifier: AccessibilityID.EventRow.container)
        return waitForMinCount(eventRows, minCount: count, timeout: timeout)
    }

    // MARK: - Memory Tracking

    /// Captures memory footprint for comparison.
    func captureMemoryFootprint() -> UInt64 {
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4

        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }

        return result == KERN_SUCCESS ? info.resident_size : 0
    }
}

// MARK: - XCUIElement Extensions

extension XCUIElement {
    /// Clears existing text and types new text.
    func clearAndTypeText(_ text: String) {
        guard let currentValue = self.value as? String, !currentValue.isEmpty else {
            self.typeText(text)
            return
        }

        // Select all and delete
        self.tap()
        let deleteString = String(repeating: XCUIKeyboardKey.delete.rawValue, count: currentValue.count)
        self.typeText(deleteString)
        self.typeText(text)
    }

    /// Scrolls until the element is visible.
    func scrollToVisible(in scrollView: XCUIElement, direction: ScrollDirection = .down, maxScrolls: Int = 10) {
        var scrollCount = 0
        while !self.isHittable && scrollCount < maxScrolls {
            switch direction {
            case .up:
                scrollView.swipeDown()
            case .down:
                scrollView.swipeUp()
            case .left:
                scrollView.swipeRight()
            case .right:
                scrollView.swipeLeft()
            }
            scrollCount += 1
        }
    }
}

enum ScrollDirection {
    case up, down, left, right
}

// MARK: - Test Timing

/// Measures execution time of a block.
func measureTime(_ block: () -> Void) -> TimeInterval {
    let start = Date()
    block()
    return Date().timeIntervalSince(start)
}

/// Runs a block repeatedly for a duration.
func runFor(duration: TimeInterval, interval: TimeInterval = 1.0, block: () -> Void) {
    let endTime = Date().addingTimeInterval(duration)
    while Date() < endTime {
        block()
        Thread.sleep(forTimeInterval: interval)
    }
}
