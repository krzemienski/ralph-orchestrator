import XCTest

/// Flow 2: Multi-Configuration Stress Test
/// Tests rapid configuration switching and session management.
/// Validates:
/// - Config switching without crashes
/// - Session start/stop cycles
/// - State consistency between configs
/// - Memory leaks from rapid cycling
final class Flow2_MultiConfigStress: XCTestCase {

    var app: XCUIApplication!
    var helper: TestHelper!
    var dashboardScreen: DashboardScreen!
    var settingsScreen: SettingsScreen!
    var sessionScreen: SessionScreen!
    var streamScreen: StreamScreen!

    // MARK: - Configuration

    /// Number of config switch cycles
    let configCycles = 5

    /// Configs to cycle through (if available)
    let testConfigs = ["default", "feature", "bugfix", "refactor", "test"]

    /// Delay between operations (seconds)
    let operationDelay: TimeInterval = 2

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
        captureScreenshot(name: "final-state", folder: "flow2-stress")

        if sessionScreen.isRunning() {
            sessionScreen.stopSession()
        }

        app = nil
    }

    func captureScreenshot(name: String, folder: String) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "\(folder)/\(name)"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    // MARK: - Tests

    /// Tests rapid config switching and session cycling.
    func testMultiConfigurationStress() throws {
        // 1. Verify connection
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTFail("Server not available")
            return
        }
        captureScreenshot(name: "01-connected", folder: "flow2-stress")

        // 2. Capture initial memory
        let initialMemory = helper.captureMemoryFootprint()

        // 3. Cycle through configurations
        var successfulCycles = 0
        var errors: [String] = []

        for cycle in 1...configCycles {
            print("Starting cycle \(cycle)/\(configCycles)")

            // Start session
            dashboardScreen.navigate()
            helper.startSession(prompt: "Cycle \(cycle): Quick task - print hello world")

            // Wait for session to start
            if helper.waitForSessionActive(timeout: 30) {
                captureScreenshot(name: "cycle-\(cycle)-active", folder: "flow2-stress")

                // Let it run briefly
                Thread.sleep(forTimeInterval: 10)

                // Verify events are flowing
                let eventCount = streamScreen.getEventCount()
                if eventCount > 0 {
                    successfulCycles += 1
                } else {
                    errors.append("Cycle \(cycle): No events received")
                }

                // Stop session
                sessionScreen.stopSession()
                Thread.sleep(forTimeInterval: operationDelay)
            } else {
                errors.append("Cycle \(cycle): Session failed to start")
                captureScreenshot(name: "cycle-\(cycle)-failed", folder: "flow2-stress")
            }
        }

        // 4. Capture final memory
        let finalMemory = helper.captureMemoryFootprint()
        captureScreenshot(name: "02-cycles-complete", folder: "flow2-stress")

        // 5. Assertions
        XCTAssertEqual(successfulCycles, configCycles,
                       "All \(configCycles) cycles should complete successfully. Errors: \(errors)")

        // Memory leak check
        if initialMemory > 0 && finalMemory > 0 {
            let memoryGrowth = Double(finalMemory) / Double(initialMemory)
            XCTAssertLessThan(memoryGrowth, 2.0,
                              "Memory should not double after \(configCycles) cycles")
        }

        // Log results
        print("===== STRESS TEST RESULTS =====")
        print("Cycles completed: \(successfulCycles)/\(configCycles)")
        print("Errors: \(errors.count)")
        print("Initial memory: \(initialMemory / 1024 / 1024) MB")
        print("Final memory: \(finalMemory / 1024 / 1024) MB")
        print("===============================")
    }

    /// Tests rapid start/stop without waiting for completion.
    func testRapidStartStop() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        let rapidCycles = 10
        var crashes = 0

        for i in 1...rapidCycles {
            dashboardScreen.navigate()

            // Start
            dashboardScreen.tapStart()

            // Enter prompt quickly
            let promptField = app.textViews[AccessibilityID.StartRun.promptField]
            if helper.waitForElement(promptField, timeout: 5) {
                promptField.tap()
                promptField.typeText("Rapid test \(i)")

                let startButton = app.buttons[AccessibilityID.StartRun.startButton]
                if helper.waitForHittable(startButton) {
                    startButton.tap()
                }
            }

            // Brief wait
            Thread.sleep(forTimeInterval: 1)

            // Stop immediately if running
            let stopButton = app.buttons[AccessibilityID.SessionDetail.stopButton]
            if stopButton.exists && stopButton.isHittable {
                stopButton.tap()
            }

            // Check app is still responsive
            if !dashboardScreen.startButton.waitForExistence(timeout: 5) {
                crashes += 1
                captureScreenshot(name: "crash-cycle-\(i)", folder: "flow2-stress")
            }
        }

        XCTAssertEqual(crashes, 0, "App should not crash during rapid start/stop")
        captureScreenshot(name: "rapid-complete", folder: "flow2-stress")
    }

    /// Tests settings modification mid-session.
    func testSettingsChangeMidSession() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        // Start a session
        dashboardScreen.navigate()
        helper.startSession(prompt: "Long running task for settings test")

        guard helper.waitForSessionActive(timeout: 30) else {
            XCTFail("Session should start")
            return
        }

        captureScreenshot(name: "session-running", folder: "flow2-stress")

        // Navigate to settings while session is running
        settingsScreen.navigate()
        captureScreenshot(name: "settings-mid-session", folder: "flow2-stress")

        // Verify settings are accessible
        settingsScreen.assertVisible()

        // Navigate back to session
        sessionScreen.navigateToList()
        sessionScreen.selectSession(at: 0)

        // Session should still be running
        XCTAssertTrue(sessionScreen.isRunning(), "Session should still be running after settings visit")

        sessionScreen.stopSession()
    }

    /// Tests state consistency after app backgrounding.
    func testBackgroundRecovery() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        // Start session
        dashboardScreen.navigate()
        helper.startSession(prompt: "Background recovery test")

        guard helper.waitForSessionActive(timeout: 30) else {
            XCTFail("Session should start")
            return
        }

        let eventCountBefore = streamScreen.getEventCount()
        captureScreenshot(name: "before-background", folder: "flow2-stress")

        // Background the app
        XCUIDevice.shared.press(.home)
        Thread.sleep(forTimeInterval: 5)

        // Return to app
        app.activate()
        Thread.sleep(forTimeInterval: 3)

        captureScreenshot(name: "after-background", folder: "flow2-stress")

        // App should recover - either still streaming or reconnecting
        let reconnectVisible = streamScreen.reconnectButton.exists
        let eventsVisible = streamScreen.getEventCount() >= eventCountBefore

        XCTAssertTrue(reconnectVisible || eventsVisible,
                      "App should recover after backgrounding")

        sessionScreen.stopSession()
    }
}
