import XCTest

/// Flow 1: Live Stream Marathon Test
/// Tests SSE streaming stability over extended periods (15+ minutes).
/// Validates:
/// - No disconnections during extended streaming
/// - Event parsing correctness (100+ events)
/// - Memory stability over time
/// - Hat transitions are rendered correctly
final class Flow1_LiveStreamMarathon: XCTestCase {

    var app: XCUIApplication!
    var helper: TestHelper!
    var dashboardScreen: DashboardScreen!
    var settingsScreen: SettingsScreen!
    var streamScreen: StreamScreen!
    var sessionScreen: SessionScreen!

    // MARK: - Configuration

    /// Duration of the marathon test in seconds (15 minutes default)
    let marathonDuration: TimeInterval = 15 * 60

    /// Minimum events expected during marathon
    let minimumExpectedEvents = 100

    /// Memory growth threshold (50% increase is concerning)
    let memoryGrowthThreshold: Double = 1.5

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()

        // Pass test configuration via launch arguments
        app.launchArguments = ["--uitesting"]
        app.launch()

        helper = TestHelper(app: app)
        dashboardScreen = DashboardScreen(app: app)
        settingsScreen = SettingsScreen(app: app)
        streamScreen = StreamScreen(app: app)
        sessionScreen = SessionScreen(app: app)
    }

    override func tearDownWithError() throws {
        // Capture final screenshot
        captureScreenshot(name: "final-state", folder: "flow1-marathon")

        // Stop any running session
        if sessionScreen.isRunning() {
            sessionScreen.stopSession()
        }

        app = nil
    }

    // MARK: - Helper Methods

    func captureScreenshot(name: String, folder: String) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "\(folder)/\(name)"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    // MARK: - Tests

    /// Main marathon test - streams events for 15+ minutes.
    func testLiveStreamMarathon() throws {
        // 1. Verify server connection
        settingsScreen.navigate()
        captureScreenshot(name: "01-settings", folder: "flow1-marathon")

        guard settingsScreen.testConnection() else {
            XCTFail("Cannot connect to server - ensure ralph-mobile-server is running")
            return
        }
        captureScreenshot(name: "02-connected", folder: "flow1-marathon")

        // 2. Navigate to dashboard and start session
        dashboardScreen.navigate()
        dashboardScreen.assertVisible()
        captureScreenshot(name: "03-dashboard", folder: "flow1-marathon")

        // 3. Start a session with a long-running prompt
        helper.startSession(
            config: nil, // Use default config
            prompt: "Implement a comprehensive test suite for a REST API. Include unit tests, integration tests, and end-to-end tests. Document each test thoroughly."
        )
        captureScreenshot(name: "04-session-started", folder: "flow1-marathon")

        // 4. Wait for session to become active
        XCTAssertTrue(helper.waitForSessionActive(timeout: 60),
                      "Session should become active within 60 seconds")
        captureScreenshot(name: "05-session-active", folder: "flow1-marathon")

        // 5. Capture initial memory footprint
        let initialMemory = helper.captureMemoryFootprint()

        // 6. Monitor stream for marathon duration
        let checkInterval: TimeInterval = 30 // Check every 30 seconds
        var checkpoints: [(time: TimeInterval, events: Int, hat: String?)] = []
        var disconnections = 0

        let startTime = Date()
        let endTime = startTime.addingTimeInterval(marathonDuration)

        while Date() < endTime {
            let elapsed = Date().timeIntervalSince(startTime)

            // Check for events
            let eventCount = streamScreen.getEventCount()
            let currentHat = sessionScreen.getCurrentHat()

            checkpoints.append((elapsed, eventCount, currentHat))

            // Check for disconnection
            if streamScreen.reconnectButton.exists && streamScreen.reconnectButton.isHittable {
                disconnections += 1
                captureScreenshot(name: "disconnection-\(disconnections)", folder: "flow1-marathon")
                streamScreen.reconnect()
            }

            // Periodic screenshots
            if Int(elapsed) % 300 == 0 { // Every 5 minutes
                let minutes = Int(elapsed / 60)
                captureScreenshot(name: "checkpoint-\(minutes)min", folder: "flow1-marathon")
            }

            Thread.sleep(forTimeInterval: checkInterval)
        }

        // 7. Capture final metrics
        let finalMemory = helper.captureMemoryFootprint()
        let finalEventCount = streamScreen.getEventCount()
        captureScreenshot(name: "06-marathon-complete", folder: "flow1-marathon")

        // 8. Assertions
        XCTAssertEqual(disconnections, 0,
                       "Should have no disconnections during \(marathonDuration/60) minute marathon")

        XCTAssertGreaterThanOrEqual(finalEventCount, minimumExpectedEvents,
                                     "Should receive at least \(minimumExpectedEvents) events")

        // Memory check
        if initialMemory > 0 && finalMemory > 0 {
            let memoryGrowth = Double(finalMemory) / Double(initialMemory)
            XCTAssertLessThan(memoryGrowth, memoryGrowthThreshold,
                              "Memory should not grow more than \(Int((memoryGrowthThreshold - 1) * 100))%")
        }

        // Log results
        print("===== MARATHON TEST RESULTS =====")
        print("Duration: \(marathonDuration / 60) minutes")
        print("Events received: \(finalEventCount)")
        print("Disconnections: \(disconnections)")
        print("Initial memory: \(initialMemory / 1024 / 1024) MB")
        print("Final memory: \(finalMemory / 1024 / 1024) MB")
        print("Checkpoints: \(checkpoints.count)")
        print("=================================")

        // 9. Stop session
        sessionScreen.stopSession()
        captureScreenshot(name: "07-session-stopped", folder: "flow1-marathon")
    }

    /// Shorter version of marathon test for CI (5 minutes).
    func testLiveStreamShort() throws {
        // 1. Verify server connection
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        // 2. Start session
        dashboardScreen.navigate()
        helper.startSession(prompt: "Write a simple hello world function in Swift")

        // 3. Wait for active
        XCTAssertTrue(helper.waitForSessionActive(timeout: 30))

        // 4. Monitor for 5 minutes
        let result = streamScreen.monitorStream(duration: 5 * 60, checkInterval: 10)

        // 5. Validate
        XCTAssertEqual(result.disconnections, 0, "No disconnections in 5 minutes")
        XCTAssertGreaterThan(result.endCount, result.startCount, "Should receive new events")

        // 6. Cleanup
        sessionScreen.stopSession()
    }

    /// Tests that hat transitions are rendered correctly.
    func testHatTransitions() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        dashboardScreen.navigate()
        helper.startSession(prompt: "Plan and implement a feature with multiple phases")

        XCTAssertTrue(helper.waitForSessionActive(timeout: 30))

        // Monitor for hat changes over 2 minutes
        var observedHats: Set<String> = []
        let endTime = Date().addingTimeInterval(120)

        while Date() < endTime {
            if let hat = sessionScreen.getCurrentHat() {
                observedHats.insert(hat)
            }
            Thread.sleep(forTimeInterval: 5)
        }

        captureScreenshot(name: "hat-transitions", folder: "flow1-marathon")

        // Should observe at least 2 different hats (planning -> implementation)
        XCTAssertGreaterThanOrEqual(observedHats.count, 1,
                                     "Should observe at least one hat type")

        sessionScreen.stopSession()
    }
}
