import XCTest

/// Page object for the Stream/Event view.
class StreamScreen {

    let app: XCUIApplication
    let helper: TestHelper

    init(app: XCUIApplication) {
        self.app = app
        self.helper = TestHelper(app: app)
    }

    // MARK: - Elements

    var view: XCUIElement {
        app.scrollViews[AccessibilityID.Stream.view]
    }

    var eventList: XCUIElement {
        app.scrollViews[AccessibilityID.Stream.eventList]
    }

    var connectionStatus: XCUIElement {
        app.staticTexts[AccessibilityID.Stream.connectionStatus]
    }

    var reconnectButton: XCUIElement {
        app.buttons[AccessibilityID.Stream.reconnectButton]
    }

    var filterButton: XCUIElement {
        app.buttons[AccessibilityID.Stream.filterButton]
    }

    var autoScrollToggle: XCUIElement {
        app.switches[AccessibilityID.Stream.autoScrollToggle]
    }

    var eventRows: XCUIElementQuery {
        app.otherElements.matching(identifier: AccessibilityID.EventRow.container)
    }

    // MARK: - Event Feed Elements

    var eventFeed: XCUIElement {
        app.scrollViews[AccessibilityID.EventFeed.list]
    }

    var eventFeedEmpty: XCUIElement {
        app.staticTexts[AccessibilityID.EventFeed.empty]
    }

    var eventFeedLoading: XCUIElement {
        app.activityIndicators[AccessibilityID.EventFeed.loading]
    }

    // MARK: - Actions

    /// Waits for the stream to connect.
    @discardableResult
    func waitForConnection(timeout: TimeInterval = 30) -> Bool {
        helper.waitForElement(eventList, timeout: timeout)
    }

    /// Gets the current event count.
    func getEventCount() -> Int {
        eventRows.count
    }

    /// Waits for at least N events.
    @discardableResult
    func waitForEvents(count: Int, timeout: TimeInterval = 60) -> Bool {
        helper.waitForMinCount(eventRows, minCount: count, timeout: timeout)
    }

    /// Taps reconnect button if visible.
    func reconnect() {
        if helper.waitForHittable(reconnectButton, timeout: 2) {
            reconnectButton.tap()
        }
    }

    /// Toggles auto-scroll.
    func toggleAutoScroll() {
        if helper.waitForHittable(autoScrollToggle) {
            autoScrollToggle.tap()
        }
    }

    /// Opens filter menu.
    func openFilters() {
        if helper.waitForHittable(filterButton) {
            filterButton.tap()
        }
    }

    /// Gets the hat badge text from an event row.
    func getEventHat(at index: Int) -> String? {
        let row = eventRows.element(boundBy: index)
        guard row.exists else { return nil }
        let hatBadge = row.staticTexts[AccessibilityID.EventRow.hatBadge]
        return hatBadge.exists ? hatBadge.label : nil
    }

    /// Gets the event type from an event row.
    func getEventType(at index: Int) -> String? {
        let row = eventRows.element(boundBy: index)
        guard row.exists else { return nil }
        let typeLabel = row.staticTexts[AccessibilityID.EventRow.eventType]
        return typeLabel.exists ? typeLabel.label : nil
    }

    /// Scrolls to bottom of event feed.
    func scrollToBottom() {
        eventList.swipeUp()
    }

    /// Scrolls to top of event feed.
    func scrollToTop() {
        eventList.swipeDown()
    }

    // MARK: - Monitoring

    /// Monitors event stream for a duration, returning event count.
    func monitorStream(duration: TimeInterval, checkInterval: TimeInterval = 5) -> (startCount: Int, endCount: Int, disconnections: Int) {
        let startCount = getEventCount()
        var disconnections = 0

        let endTime = Date().addingTimeInterval(duration)
        while Date() < endTime {
            Thread.sleep(forTimeInterval: checkInterval)

            // Check for disconnection
            if reconnectButton.exists && reconnectButton.isHittable {
                disconnections += 1
                reconnect()
            }
        }

        let endCount = getEventCount()
        return (startCount, endCount, disconnections)
    }

    // MARK: - Assertions

    /// Asserts the stream is visible.
    func assertVisible() {
        XCTAssertTrue(helper.waitForElement(view), "Stream view should be visible")
    }

    /// Asserts connection is active.
    func assertConnected() {
        XCTAssertTrue(waitForConnection(), "Stream should be connected")
    }

    /// Asserts events are being received.
    func assertEventsReceived(minCount: Int = 1, timeout: TimeInterval = 30) {
        XCTAssertTrue(waitForEvents(count: minCount, timeout: timeout),
                      "Should receive at least \(minCount) events")
    }

    /// Asserts no disconnections during monitoring period.
    func assertNoDisconnections(during duration: TimeInterval) {
        let result = monitorStream(duration: duration)
        XCTAssertEqual(result.disconnections, 0, "Should have no disconnections during \(duration)s monitoring")
    }
}
