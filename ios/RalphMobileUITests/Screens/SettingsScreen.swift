import XCTest

/// Page object for the Settings view.
class SettingsScreen {

    let app: XCUIApplication
    let helper: TestHelper

    init(app: XCUIApplication) {
        self.app = app
        self.helper = TestHelper(app: app)
    }

    // MARK: - Elements

    var view: XCUIElement {
        app.scrollViews[AccessibilityID.Settings.view]
    }

    var serverURLField: XCUIElement {
        app.textFields[AccessibilityID.Settings.serverURL]
    }

    var serverKeyField: XCUIElement {
        app.secureTextFields[AccessibilityID.Settings.serverKey]
    }

    var testConnectionButton: XCUIElement {
        app.buttons[AccessibilityID.Settings.testConnectionButton]
    }

    var connectionStatus: XCUIElement {
        app.staticTexts[AccessibilityID.Settings.connectionStatus]
    }

    var aiStatus: XCUIElement {
        app.staticTexts[AccessibilityID.Settings.aiStatus]
    }

    var anthropicKeyField: XCUIElement {
        app.secureTextFields[AccessibilityID.Settings.anthropicKey]
    }

    var saveButton: XCUIElement {
        app.buttons[AccessibilityID.Settings.saveButton]
    }

    var resetButton: XCUIElement {
        app.buttons[AccessibilityID.Settings.resetButton]
    }

    var exportButton: XCUIElement {
        app.buttons[AccessibilityID.Settings.exportButton]
    }

    var importButton: XCUIElement {
        app.buttons[AccessibilityID.Settings.importButton]
    }

    // MARK: - Actions

    /// Navigates to this screen.
    func navigate() {
        helper.navigateToSettings()
    }

    /// Enters server URL.
    func enterServerURL(_ url: String) {
        helper.waitForHittable(serverURLField)
        serverURLField.tap()
        serverURLField.clearAndTypeText(url)
    }

    /// Enters server API key.
    func enterServerKey(_ key: String) {
        helper.waitForHittable(serverKeyField)
        serverKeyField.tap()
        serverKeyField.clearAndTypeText(key)
    }

    /// Enters Anthropic API key.
    func enterAnthropicKey(_ key: String) {
        helper.waitForHittable(anthropicKeyField)
        anthropicKeyField.tap()
        anthropicKeyField.clearAndTypeText(key)
    }

    /// Tests connection to server.
    func testConnection() -> Bool {
        helper.waitForHittable(testConnectionButton)
        testConnectionButton.tap()

        // Wait for status update
        Thread.sleep(forTimeInterval: 2)

        guard helper.waitForElement(connectionStatus) else { return false }
        let status = connectionStatus.label.lowercased()
        return status.contains("connected") || status.contains("success")
    }

    /// Saves current settings.
    func save() {
        helper.waitForHittable(saveButton)
        saveButton.tap()
    }

    /// Resets settings to defaults.
    func reset() {
        helper.waitForHittable(resetButton)
        resetButton.tap()
    }

    /// Exports configuration.
    func exportConfig() {
        helper.waitForHittable(exportButton)
        exportButton.tap()
    }

    /// Imports configuration.
    func importConfig() {
        helper.waitForHittable(importButton)
        importButton.tap()
    }

    /// Configures server with URL and key.
    func configureServer(url: String, key: String) {
        enterServerURL(url)
        enterServerKey(key)
        save()
    }

    // MARK: - Assertions

    /// Asserts the settings view is visible.
    func assertVisible() {
        XCTAssertTrue(helper.waitForElement(view), "Settings view should be visible")
    }

    /// Asserts connection is successful.
    func assertConnected() {
        XCTAssertTrue(testConnection(), "Server connection should succeed")
    }

    /// Asserts server URL field contains expected value.
    func assertServerURL(_ expected: String) {
        guard let value = serverURLField.value as? String else {
            XCTFail("Server URL field has no value")
            return
        }
        XCTAssertEqual(value, expected, "Server URL should match")
    }
}
