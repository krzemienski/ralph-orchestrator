import XCTest

/// Base class for screenshot automation tests.
/// Provides helpers for capturing screenshots with XCTAttachment for CI integration.
class ScreenshotTests: XCTestCase {

    var app: XCUIApplication!

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    override func tearDownWithError() throws {
        // Capture screenshot on failure
        if let failureCount = testRun?.failureCount, failureCount > 0 {
            captureScreenshot(name: "failure-\(name)", folder: "failures")
        }
        app = nil
    }

    // MARK: - Screenshot Helpers

    /// Captures a screenshot and attaches it to the test results.
    /// - Parameters:
    ///   - name: Screenshot filename (without extension)
    ///   - folder: Subfolder for organization (e.g., "session-list", "editor")
    func captureScreenshot(name: String, folder: String) {
        let screenshot = XCUIScreen.main.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "\(folder)/\(name)"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    /// Waits for an element to exist with timeout.
    /// - Parameters:
    ///   - element: The XCUIElement to wait for
    ///   - timeout: Maximum wait time in seconds
    /// - Returns: True if element exists within timeout
    @discardableResult
    func waitForElement(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        element.waitForExistence(timeout: timeout)
    }

    /// Waits for an element to be hittable (visible and enabled).
    /// - Parameters:
    ///   - element: The XCUIElement to wait for
    ///   - timeout: Maximum wait time in seconds
    /// - Returns: True if element is hittable within timeout
    @discardableResult
    func waitForHittable(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        let predicate = NSPredicate(format: "isHittable == true")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }

    /// Waits for an element to disappear.
    /// - Parameters:
    ///   - element: The XCUIElement to wait for disappearance
    ///   - timeout: Maximum wait time in seconds
    /// - Returns: True if element disappeared within timeout
    @discardableResult
    func waitForDisappear(_ element: XCUIElement, timeout: TimeInterval = 5) -> Bool {
        let predicate = NSPredicate(format: "exists == false")
        let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
        let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
        return result == .completed
    }
}

// MARK: - Session List Tests

final class SessionListScreenshotTests: ScreenshotTests {

    func testSessionListEmpty() throws {
        // Given: App launched with no sessions
        let sessionList = app.collectionViews["session-list"]
        waitForElement(sessionList)

        // Then: Capture empty state
        captureScreenshot(name: "01-empty-state", folder: "01-session-list")
    }

    func testSessionListWithSessions() throws {
        // Given: App launched
        // Note: This requires sessions to exist or mock data
        let sessionList = app.collectionViews["session-list"]
        waitForElement(sessionList)

        // Then: Capture list with sessions
        captureScreenshot(name: "02-with-sessions", folder: "01-session-list")
    }

    func testSessionListLoading() throws {
        // Given: App loading sessions
        let loadingIndicator = app.activityIndicators.firstMatch

        // Then: Capture loading state if visible
        if loadingIndicator.exists {
            captureScreenshot(name: "03-loading", folder: "01-session-list")
        }
    }
}

// MARK: - Session Detail Tests

final class SessionDetailScreenshotTests: ScreenshotTests {

    func testSessionDetailHeader() throws {
        // Navigate to session detail (requires existing session)
        let firstSession = app.buttons["session-row"].firstMatch
        guard waitForElement(firstSession) else {
            XCTSkip("No sessions available for detail view")
            return
        }
        firstSession.tap()

        // Capture header
        captureScreenshot(name: "01-header", folder: "02-session-detail")
    }

    func testSessionDetailEvents() throws {
        // Navigate to session detail
        let firstSession = app.buttons["session-row"].firstMatch
        guard waitForElement(firstSession) else {
            XCTSkip("No sessions available")
            return
        }
        firstSession.tap()

        // Wait for events to load
        let eventFeed = app.scrollViews["event-feed"]
        waitForElement(eventFeed)

        // Capture events list
        captureScreenshot(name: "02-events-list", folder: "02-session-detail")
    }

    func testSessionDetailMetrics() throws {
        // Navigate to session detail
        let firstSession = app.buttons["session-row"].firstMatch
        guard waitForElement(firstSession) else {
            XCTSkip("No sessions available")
            return
        }
        firstSession.tap()

        // Capture metrics view
        captureScreenshot(name: "03-metrics", folder: "02-session-detail")
    }
}

// MARK: - Markdown Editor Tests

final class MarkdownEditorScreenshotTests: ScreenshotTests {

    private func navigateToEditor() {
        // Navigate to markdown editor tab or button
        let editorTab = app.buttons["Editor"]
        if editorTab.exists {
            editorTab.tap()
        }
    }

    func testEditorEmpty() throws {
        navigateToEditor()

        let editor = app.textViews["markdown-editor-source"]
        waitForElement(editor)

        captureScreenshot(name: "01-empty", folder: "03-markdown-editor")
    }

    func testEditorWithContent() throws {
        navigateToEditor()

        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else {
            XCTFail("Editor not found")
            return
        }

        // Type sample content
        editor.tap()
        editor.typeText("# Sample Prompt\n\nThis is a **bold** test with `code`.")

        captureScreenshot(name: "02-with-content", folder: "03-markdown-editor")
    }

    func testEditorToolbar() throws {
        navigateToEditor()

        let boldButton = app.buttons["toolbar-bold"]
        waitForElement(boldButton)

        captureScreenshot(name: "03-toolbar", folder: "03-markdown-editor")
    }

    func testEditorPreviewMode() throws {
        navigateToEditor()

        // Add content first
        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else {
            XCTFail("Editor not found")
            return
        }
        editor.tap()
        editor.typeText("# Preview Test\n\nContent here.")

        // Toggle to preview mode
        let modeToggle = app.buttons["markdown-editor-mode-toggle"]
        if waitForElement(modeToggle) {
            modeToggle.tap()
        }

        captureScreenshot(name: "04-preview-mode", folder: "03-markdown-editor")
    }

    func testEditorSplitPane() throws {
        navigateToEditor()

        // On iPad, check for split pane
        let sourceEditor = app.textViews["markdown-editor-source"]
        let preview = app.scrollViews["markdown-editor-preview"]

        waitForElement(sourceEditor)

        // If both visible, we're in split mode
        if sourceEditor.exists && preview.exists {
            captureScreenshot(name: "05-split-pane", folder: "03-markdown-editor")
        } else {
            XCTSkip("Split pane only available on iPad")
        }
    }
}

// MARK: - Templates Sheet Tests

final class TemplatesScreenshotTests: ScreenshotTests {

    private func openTemplatesSheet() {
        // Navigate to editor first
        let editorTab = app.buttons["Editor"]
        if editorTab.exists {
            editorTab.tap()
        }

        // Open templates sheet
        let templatesButton = app.buttons["toolbar-templates"]
        if waitForElement(templatesButton) {
            templatesButton.tap()
        }
    }

    func testTemplatesBundledList() throws {
        openTemplatesSheet()

        let searchField = app.textFields["templates-search"]
        waitForElement(searchField)

        captureScreenshot(name: "01-bundled-list", folder: "04-templates")
    }

    func testTemplatesSearch() throws {
        openTemplatesSheet()

        let searchField = app.textFields["templates-search"]
        guard waitForElement(searchField) else {
            XCTFail("Search field not found")
            return
        }

        searchField.tap()
        searchField.typeText("design")

        captureScreenshot(name: "02-search-results", folder: "04-templates")
    }

    func testTemplatesSaveButton() throws {
        openTemplatesSheet()

        let saveButton = app.buttons["templates-save-current"]
        waitForElement(saveButton)

        captureScreenshot(name: "03-save-button", folder: "04-templates")
    }
}

// MARK: - Settings Tests

final class SettingsScreenshotTests: ScreenshotTests {

    private func openSettings() {
        let settingsButton = app.buttons["Settings"]
        if settingsButton.exists {
            settingsButton.tap()
        }
    }

    func testSettingsView() throws {
        openSettings()

        let serverURL = app.textFields["settings-server-url"]
        waitForElement(serverURL)

        captureScreenshot(name: "01-settings-view", folder: "05-settings")
    }

    func testSettingsKeyHidden() throws {
        openSettings()

        let serverKey = app.secureTextFields["settings-server-key"]
        waitForElement(serverKey)

        captureScreenshot(name: "02-key-hidden", folder: "05-settings")
    }

    func testSettingsAIStatus() throws {
        openSettings()

        let aiStatus = app.staticTexts["settings-ai-status"]
        waitForElement(aiStatus)

        captureScreenshot(name: "03-ai-status", folder: "05-settings")
    }
}

// MARK: - AI Improvement Tests

final class AIImprovementScreenshotTests: ScreenshotTests {

    private func navigateToEditor() {
        let editorTab = app.buttons["Editor"]
        if editorTab.exists {
            editorTab.tap()
        }
    }

    func testAIButtonVisible() throws {
        navigateToEditor()

        // Add some content first
        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else {
            XCTFail("Editor not found")
            return
        }
        editor.tap()
        editor.typeText("Fix the login bug")

        // Check AI button
        let aiButton = app.buttons["toolbar-ai-improve"]
        waitForElement(aiButton)

        captureScreenshot(name: "01-button-visible", folder: "06-ai-improvement")
    }

    func testAIButtonDisabled() throws {
        navigateToEditor()

        // Empty editor - AI button should be disabled
        let aiButton = app.buttons["toolbar-ai-improve"]
        waitForElement(aiButton)

        captureScreenshot(name: "02-button-disabled", folder: "06-ai-improvement")
    }

    func testAILoading() throws {
        navigateToEditor()

        // Add content and tap AI button
        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else {
            XCTFail("Editor not found")
            return
        }
        editor.tap()
        editor.typeText("Fix the login bug")

        let aiButton = app.buttons["toolbar-ai-improve"]
        guard waitForHittable(aiButton) else {
            XCTSkip("AI button not available - API key may not be configured")
            return
        }
        aiButton.tap()

        // Capture loading state
        let loadingView = app.otherElements["ai-improvement-loading"]
        if loadingView.exists {
            captureScreenshot(name: "03-loading", folder: "06-ai-improvement")
        }
    }

    func testAISuggestion() throws {
        // This test requires Anthropic API key to be configured
        navigateToEditor()

        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else {
            XCTFail("Editor not found")
            return
        }
        editor.tap()
        editor.typeText("Fix the login bug")

        let aiButton = app.buttons["toolbar-ai-improve"]
        guard waitForHittable(aiButton) else {
            XCTSkip("AI button not available")
            return
        }
        aiButton.tap()

        // Wait for suggestion
        let acceptButton = app.buttons["ai-improvement-accept"]
        if waitForElement(acceptButton, timeout: 30) {
            captureScreenshot(name: "04-suggestion", folder: "06-ai-improvement")
        }
    }

    func testAIAccept() throws {
        // Follow same flow as testAISuggestion
        navigateToEditor()

        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else { return }
        editor.tap()
        editor.typeText("Fix the login bug")

        let aiButton = app.buttons["toolbar-ai-improve"]
        guard waitForHittable(aiButton) else {
            XCTSkip("AI button not available")
            return
        }
        aiButton.tap()

        let acceptButton = app.buttons["ai-improvement-accept"]
        if waitForElement(acceptButton, timeout: 30) {
            captureScreenshot(name: "05-before-accept", folder: "06-ai-improvement")
            acceptButton.tap()
            captureScreenshot(name: "06-after-accept", folder: "06-ai-improvement")
        }
    }

    func testAIReject() throws {
        navigateToEditor()

        let editor = app.textViews["markdown-editor-source"]
        guard waitForElement(editor) else { return }
        editor.tap()
        editor.typeText("Fix the login bug")

        let aiButton = app.buttons["toolbar-ai-improve"]
        guard waitForHittable(aiButton) else {
            XCTSkip("AI button not available")
            return
        }
        aiButton.tap()

        let rejectButton = app.buttons["ai-improvement-reject"]
        if waitForElement(rejectButton, timeout: 30) {
            rejectButton.tap()
            captureScreenshot(name: "07-after-reject", folder: "06-ai-improvement")
        }
    }
}

// MARK: - Error State Tests

final class ErrorStateScreenshotTests: ScreenshotTests {

    func testNetworkError() throws {
        // Trigger network error by using invalid server URL
        // This would require configuration changes
        captureScreenshot(name: "01-network-error", folder: "07-errors")
    }

    func testAIError() throws {
        // AI error state
        let errorView = app.otherElements["ai-improvement-error"]
        if errorView.exists {
            captureScreenshot(name: "02-ai-error", folder: "07-errors")
        }
    }
}
