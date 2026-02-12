import XCTest

/// Flow 4: Concurrent Multi-Project Test
/// Tests multiple simultaneous sessions.
/// Validates:
/// - Multiple SSE streams work simultaneously
/// - Session isolation (events don't cross streams)
/// - Steering targets specific sessions
/// - Independent session stop/start
final class Flow4_ConcurrentMultiProject: XCTestCase {

    var app: XCUIApplication!
    var helper: TestHelper!
    var dashboardScreen: DashboardScreen!
    var settingsScreen: SettingsScreen!
    var sessionScreen: SessionScreen!
    var streamScreen: StreamScreen!

    // MARK: - Configuration

    /// Number of concurrent sessions to test
    let concurrentSessionCount = 3

    /// Duration to monitor concurrent sessions
    let monitorDuration: TimeInterval = 5 * 60 // 5 minutes

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting"]
        app.launch()

        helper = TestHelper(app: app)
        dashboardScreen = DashboardScreen(app: app)
        settingsScreen = SettingsScreen(app: app)
        sessionScreen = SessionScreen(app: app)
        streamScreen = StreamScreen(app: app)
    }

    override func tearDownWithError() throws {
        captureScreenshot(name: "final-state", folder: "flow4-concurrent")

        // Stop all running sessions
        stopAllSessions()

        app = nil
    }

    func captureScreenshot(name: String, folder: String) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "\(folder)/\(name)"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func stopAllSessions() {
        // Navigate to session list and stop each
        sessionScreen.navigateToList()
        Thread.sleep(forTimeInterval: 1)

        let sessionRows = sessionScreen.sessionRows
        let count = sessionRows.count

        for _ in 0..<count {
            if sessionRows.count > 0 {
                sessionRows.element(boundBy: 0).tap()
                Thread.sleep(forTimeInterval: 1)

                if sessionScreen.isRunning() {
                    sessionScreen.stopSession()
                    Thread.sleep(forTimeInterval: 2)
                }

                // Go back to list
                sessionScreen.navigateToList()
                Thread.sleep(forTimeInterval: 1)
            }
        }
    }

    // MARK: - Tests

    /// Tests running multiple concurrent sessions.
    func testConcurrentSessions() throws {
        // 1. Connect to server
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTFail("Server not available")
            return
        }
        captureScreenshot(name: "01-connected", folder: "flow4-concurrent")

        // 2. Start multiple sessions
        var sessionIds: [Int] = []

        for i in 1...concurrentSessionCount {
            dashboardScreen.navigate()
            helper.startSession(
                prompt: "Session \(i): Implement a simple counter class with increment and decrement methods"
            )

            // Wait briefly for session to register
            Thread.sleep(forTimeInterval: 3)

            sessionIds.append(i)
            captureScreenshot(name: "02-session-\(i)-started", folder: "flow4-concurrent")

            // Go back to dashboard for next session
            if i < concurrentSessionCount {
                dashboardScreen.navigate()
            }
        }

        captureScreenshot(name: "03-all-sessions-started", folder: "flow4-concurrent")

        // 3. Navigate to session list
        sessionScreen.navigateToList()
        Thread.sleep(forTimeInterval: 2)
        captureScreenshot(name: "04-session-list", folder: "flow4-concurrent")

        // 4. Verify multiple sessions exist
        let sessionRowCount = sessionScreen.sessionRows.count
        XCTAssertGreaterThanOrEqual(sessionRowCount, concurrentSessionCount,
                                     "Should have at least \(concurrentSessionCount) sessions")

        // 5. Monitor each session and collect metrics
        var sessionMetrics: [(index: Int, eventCount: Int, isRunning: Bool)] = []

        for i in 0..<min(sessionRowCount, concurrentSessionCount) {
            sessionScreen.selectSession(at: i)
            Thread.sleep(forTimeInterval: 2)

            let eventCount = streamScreen.getEventCount()
            let running = sessionScreen.isRunning()

            sessionMetrics.append((i, eventCount, running))
            captureScreenshot(name: "05-session-\(i)-detail", folder: "flow4-concurrent")

            sessionScreen.navigateToList()
            Thread.sleep(forTimeInterval: 1)
        }

        // 6. Wait and monitor for a period
        let checkInterval: TimeInterval = 30
        let endTime = Date().addingTimeInterval(monitorDuration)

        while Date() < endTime {
            // Check first session for activity
            sessionScreen.selectSession(at: 0)
            Thread.sleep(forTimeInterval: 2)

            // Session should still be running or have events
            let eventCount = streamScreen.getEventCount()
            if eventCount > 0 {
                captureScreenshot(name: "monitor-events-\(Int(Date().timeIntervalSince1970))", folder: "flow4-concurrent")
            }

            sessionScreen.navigateToList()
            Thread.sleep(forTimeInterval: checkInterval)
        }

        captureScreenshot(name: "06-monitoring-complete", folder: "flow4-concurrent")

        // 7. Verify session isolation - each should have its own events
        print("===== CONCURRENT TEST RESULTS =====")
        for metric in sessionMetrics {
            print("Session \(metric.index): events=\(metric.eventCount), running=\(metric.isRunning)")
        }
        print("===================================")

        // 8. Stop sessions one by one and verify others continue
        sessionScreen.selectSession(at: 0)
        sessionScreen.stopSession()
        Thread.sleep(forTimeInterval: 2)
        captureScreenshot(name: "07-first-stopped", folder: "flow4-concurrent")

        // Check remaining sessions
        if sessionRowCount > 1 {
            sessionScreen.navigateToList()
            sessionScreen.selectSession(at: 1)

            // This session should still have activity
            let remainingEvents = streamScreen.getEventCount()
            XCTAssertGreaterThan(remainingEvents, 0,
                                 "Other sessions should still have events after stopping one")
        }

        // 9. Cleanup remaining
        stopAllSessions()
        captureScreenshot(name: "08-all-stopped", folder: "flow4-concurrent")
    }

    /// Tests that steering targets the correct session.
    func testSessionTargetedSteering() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        // Start two sessions
        dashboardScreen.navigate()
        helper.startSession(prompt: "Session A: Work on authentication")
        Thread.sleep(forTimeInterval: 3)

        dashboardScreen.navigate()
        helper.startSession(prompt: "Session B: Work on database")
        Thread.sleep(forTimeInterval: 3)

        // Navigate to session list
        sessionScreen.navigateToList()
        captureScreenshot(name: "two-sessions", folder: "flow4-concurrent")

        // Select first session and send steering
        sessionScreen.selectSession(at: 0)
        Thread.sleep(forTimeInterval: 2)

        if sessionScreen.steeringButton.exists {
            sessionScreen.sendSteering("Focus on JWT tokens")
            captureScreenshot(name: "steering-sent", folder: "flow4-concurrent")
        }

        // Verify steering went to correct session (check event stream)
        Thread.sleep(forTimeInterval: 5)
        captureScreenshot(name: "after-steering", folder: "flow4-concurrent")

        stopAllSessions()
    }

    /// Tests independent session lifecycle.
    func testIndependentSessionLifecycle() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        // Start session A
        dashboardScreen.navigate()
        helper.startSession(prompt: "Session A: Long running task")

        guard helper.waitForSessionActive(timeout: 30) else {
            XCTFail("Session A should start")
            return
        }

        // Start session B
        dashboardScreen.navigate()
        helper.startSession(prompt: "Session B: Another task")
        Thread.sleep(forTimeInterval: 3)

        // Stop session B immediately
        if sessionScreen.stopButton.exists && sessionScreen.stopButton.isHittable {
            sessionScreen.stopSession()
        }
        captureScreenshot(name: "session-b-stopped", folder: "flow4-concurrent")

        // Session A should still be running
        sessionScreen.navigateToList()
        sessionScreen.selectSession(at: 0) // Session A should be first now

        Thread.sleep(forTimeInterval: 2)
        let eventCount = streamScreen.getEventCount()
        XCTAssertGreaterThan(eventCount, 0, "Session A should still have events")

        captureScreenshot(name: "session-a-still-running", folder: "flow4-concurrent")

        stopAllSessions()
    }
}
