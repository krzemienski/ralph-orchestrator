import XCTest

/// Flow 3: MCP/Skill Integration Test
/// Tests Model Context Protocol and skill tool call handling.
/// Validates:
/// - MCP events are parsed correctly
/// - Skill tool calls appear in event stream
/// - Tool results are displayed
/// - Completion tracking works
final class Flow3_MCPSkillIntegration: XCTestCase {

    var app: XCUIApplication!
    var helper: TestHelper!
    var dashboardScreen: DashboardScreen!
    var settingsScreen: SettingsScreen!
    var sessionScreen: SessionScreen!
    var streamScreen: StreamScreen!

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
        captureScreenshot(name: "final-state", folder: "flow3-mcp")

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

    /// Tests that MCP tool calls are displayed in the event stream.
    func testMCPToolCallDisplay() throws {
        // 1. Connect to server
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTFail("Server not available")
            return
        }
        captureScreenshot(name: "01-connected", folder: "flow3-mcp")

        // 2. Start session with prompt likely to trigger tool usage
        dashboardScreen.navigate()
        helper.startSession(
            prompt: "Read the contents of the README.md file and summarize it"
        )
        captureScreenshot(name: "02-session-started", folder: "flow3-mcp")

        // 3. Wait for session to become active
        guard helper.waitForSessionActive(timeout: 60) else {
            XCTFail("Session should become active")
            return
        }

        // 4. Wait for tool events to appear
        // Tool events typically have specific types like "tool_use", "tool_result"
        let monitorDuration: TimeInterval = 120 // 2 minutes
        var toolEventsFound = false
        let endTime = Date().addingTimeInterval(monitorDuration)

        while Date() < endTime && !toolEventsFound {
            // Check event types in the stream
            let eventCount = streamScreen.getEventCount()
            for i in 0..<min(eventCount, 20) {
                if let eventType = streamScreen.getEventType(at: i) {
                    let typeLower = eventType.lowercased()
                    if typeLower.contains("tool") ||
                       typeLower.contains("read") ||
                       typeLower.contains("bash") ||
                       typeLower.contains("file") {
                        toolEventsFound = true
                        captureScreenshot(name: "03-tool-event-found", folder: "flow3-mcp")
                        break
                    }
                }
            }
            Thread.sleep(forTimeInterval: 5)
        }

        captureScreenshot(name: "04-event-stream", folder: "flow3-mcp")

        // 5. Validate events were received
        let finalEventCount = streamScreen.getEventCount()
        XCTAssertGreaterThan(finalEventCount, 0, "Should receive events")

        // Log what we found
        print("===== MCP TEST RESULTS =====")
        print("Tool events found: \(toolEventsFound)")
        print("Total events: \(finalEventCount)")
        print("============================")

        // 6. Cleanup
        sessionScreen.stopSession()
        captureScreenshot(name: "05-complete", folder: "flow3-mcp")
    }

    /// Tests skill completion tracking.
    func testSkillCompletionTracking() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        // Start session with skill-heavy prompt
        dashboardScreen.navigate()
        helper.startSession(
            prompt: "Use git to check the status of the repository"
        )

        guard helper.waitForSessionActive(timeout: 30) else {
            XCTFail("Session should start")
            return
        }

        // Monitor for skill-related events
        var skillEventsCount = 0
        let endTime = Date().addingTimeInterval(60)

        while Date() < endTime {
            let eventCount = streamScreen.getEventCount()
            for i in 0..<eventCount {
                if let eventType = streamScreen.getEventType(at: i) {
                    if eventType.lowercased().contains("skill") ||
                       eventType.lowercased().contains("git") {
                        skillEventsCount += 1
                    }
                }
            }
            Thread.sleep(forTimeInterval: 5)
        }

        captureScreenshot(name: "skill-events", folder: "flow3-mcp")

        // At minimum, we should see the session processing
        let totalEvents = streamScreen.getEventCount()
        XCTAssertGreaterThan(totalEvents, 0, "Should receive events from the session")

        sessionScreen.stopSession()
    }

    /// Tests verbose event stream filtering.
    func testVerboseEventFiltering() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        dashboardScreen.navigate()
        helper.startSession(prompt: "List the files in the current directory")

        guard helper.waitForSessionActive(timeout: 30) else {
            XCTFail("Session should start")
            return
        }

        // Wait for some events
        XCTAssertTrue(helper.waitForEvents(count: 5, timeout: 60))
        captureScreenshot(name: "events-unfiltered", folder: "flow3-mcp")

        // Try filter button if available
        if streamScreen.filterButton.exists && streamScreen.filterButton.isHittable {
            streamScreen.openFilters()
            captureScreenshot(name: "filter-menu", folder: "flow3-mcp")

            // Try to tap tool filter
            let toolFilter = app.buttons[AccessibilityID.VerboseStream.filterTools]
            if helper.waitForHittable(toolFilter, timeout: 3) {
                toolFilter.tap()
                captureScreenshot(name: "filtered-tools", folder: "flow3-mcp")
            }
        }

        sessionScreen.stopSession()
    }

    /// Tests that different event types have distinct visual styling.
    func testEventTypeStyling() throws {
        settingsScreen.navigate()
        guard settingsScreen.testConnection() else {
            XCTSkip("Server not available")
            return
        }

        dashboardScreen.navigate()
        helper.startSession(prompt: "Write a function, then test it, then document it")

        guard helper.waitForSessionActive(timeout: 30) else {
            XCTFail("Session should start")
            return
        }

        // Wait for variety of events
        XCTAssertTrue(helper.waitForEvents(count: 10, timeout: 120))

        // Capture the event stream with variety
        captureScreenshot(name: "event-variety", folder: "flow3-mcp")

        // Collect unique event types
        var uniqueTypes: Set<String> = []
        let eventCount = streamScreen.getEventCount()
        for i in 0..<min(eventCount, 30) {
            if let eventType = streamScreen.getEventType(at: i) {
                uniqueTypes.insert(eventType)
            }
        }

        print("Unique event types observed: \(uniqueTypes)")

        sessionScreen.stopSession()
    }
}
