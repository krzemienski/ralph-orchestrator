import Foundation

/// Central registry of all accessibility identifiers used in the app.
/// Keep in sync with the identifiers defined in SwiftUI views.
enum AccessibilityID {

    // MARK: - Navigation & Tabs
    enum Navigation {
        static let sidebar = "nav-sidebar"
        static let detail = "nav-detail"
        static let sessionList = "nav-session-list"
        static let tabBar = "main-tab-bar"
        static let dashboardTab = "tab-dashboard"
        static let sessionsTab = "tab-sessions"
        static let libraryTab = "tab-library"
        static let settingsTab = "tab-settings"
    }

    // MARK: - Dashboard
    enum Dashboard {
        static let view = "dashboard-view"
        static let header = "dashboard-header"
        static let serverStatus = "dashboard-server-status"
        static let activeSessionsCount = "dashboard-active-sessions"
        static let startButton = "dashboard-start-button"
        static let recentSessions = "dashboard-recent-sessions"
    }

    // MARK: - Session List
    enum SessionList {
        static let list = "session-list"
        static let emptyState = "session-list-empty"
        static let loadingIndicator = "session-list-loading"
        static let refreshButton = "session-list-refresh"
        static func row(id: String) -> String { "session-row-\(id)" }
    }

    // MARK: - Session Detail
    enum SessionDetail {
        static let view = "session-detail-view"
        static let header = "session-detail-header"
        static let statusBadge = "session-status-badge"
        static let configName = "session-config-name"
        static let promptText = "session-prompt-text"
        static let eventFeed = "session-event-feed"
        static let eventCount = "session-event-count"
        static let stopButton = "session-stop-button"
        static let steeringButton = "session-steering-button"
    }

    // MARK: - Event Feed
    enum EventFeed {
        static let list = "event-feed-list"
        static let empty = "event-feed-empty"
        static let loading = "event-feed-loading"
        static let error = "event-feed-error"
        static func row(index: Int) -> String { "event-row-\(index)" }
    }

    // MARK: - Event Row
    enum EventRow {
        static let container = "event-row-container"
        static let timestamp = "event-row-timestamp"
        static let hatBadge = "event-row-hat"
        static let eventType = "event-row-type"
        static let content = "event-row-content"
        static let expandButton = "event-row-expand"
    }

    // MARK: - Stream View
    enum Stream {
        static let view = "stream-view"
        static let eventList = "stream-event-list"
        static let connectionStatus = "stream-connection-status"
        static let reconnectButton = "stream-reconnect-button"
        static let filterButton = "stream-filter-button"
        static let autoScrollToggle = "stream-auto-scroll"
    }

    // MARK: - Status Header
    enum StatusHeader {
        static let view = "status-header-view"
        static let connectionIndicator = "status-connection"
        static let hatDisplay = "status-hat"
        static let iterationCount = "status-iteration"
        static let tokenCount = "status-tokens"
    }

    // MARK: - Token Metrics
    enum TokenMetrics {
        static let view = "token-metrics-view"
        static let inputTokens = "metrics-input-tokens"
        static let outputTokens = "metrics-output-tokens"
        static let totalTokens = "metrics-total-tokens"
        static let costEstimate = "metrics-cost"
    }

    // MARK: - Start Run Sheet
    enum StartRun {
        static let sheet = "start-run-sheet"
        static let configPicker = "start-run-config-picker"
        static let promptField = "start-run-prompt-field"
        static let startButton = "start-run-start-button"
        static let cancelButton = "start-run-cancel-button"
        static let advancedToggle = "start-run-advanced-toggle"
    }

    // MARK: - Config
    enum Config {
        static let view = "config-view"
        static let picker = "config-picker-menu"
        static let selectedItem = "config-picker-selected"
        static func item(name: String) -> String { "config-item-\(name)" }
        static let detailHeader = "config-detail-header"
        static let detailYaml = "config-detail-yaml"
        static let copyButton = "config-detail-copy"
        static let exportButton = "config-detail-export"
    }

    // MARK: - Prompt
    enum Prompt {
        static let view = "prompt-view"
        static let picker = "prompt-picker-menu"
        static let selectedItem = "prompt-picker-selected"
        static func item(name: String) -> String { "prompt-item-\(name)" }
        static let detailHeader = "prompt-detail-header"
        static let detailContent = "prompt-detail-content"
        static let editButton = "prompt-detail-edit"
    }

    // MARK: - Settings
    enum Settings {
        static let view = "settings-view"
        static let serverURL = "settings-server-url"
        static let serverKey = "settings-server-key"
        static let testConnectionButton = "settings-test-connection"
        static let connectionStatus = "settings-connection-status"
        static let aiStatus = "settings-ai-status"
        static let anthropicKey = "settings-anthropic-key"
        static let saveButton = "settings-save"
        static let resetButton = "settings-reset"
        static let exportButton = "settings-export"
        static let importButton = "settings-import"
    }

    // MARK: - Library
    enum Library {
        static let view = "library-view"
        static let configsSection = "library-configs"
        static let promptsSection = "library-prompts"
        static let templatesSection = "library-templates"
        static let addButton = "library-add"
        static let searchField = "library-search"
    }

    // MARK: - Create Asset
    enum CreateAsset {
        static let sheet = "create-asset-sheet"
        static let typePicker = "asset-type-picker"
        static let nameField = "asset-name-field"
        static let contentEditor = "asset-content-editor"
        static let submitButton = "asset-submit"
        static let cancelButton = "asset-cancel"
    }

    // MARK: - Markdown Editor
    enum MarkdownEditor {
        static let view = "markdown-editor-view"
        static let source = "markdown-editor-source"
        static let preview = "markdown-editor-preview"
        static let modeToggle = "markdown-editor-mode-toggle"
        static let toolbar = "markdown-editor-toolbar"
        static let boldButton = "toolbar-bold"
        static let italicButton = "toolbar-italic"
        static let codeButton = "toolbar-code"
        static let headingButton = "toolbar-heading"
        static let templatesButton = "toolbar-templates"
        static let aiImproveButton = "toolbar-ai-improve"
    }

    // MARK: - Templates Sheet
    enum Templates {
        static let sheet = "templates-sheet"
        static let searchField = "templates-search"
        static let list = "templates-list"
        static let saveCurrentButton = "templates-save-current"
        static func template(name: String) -> String { "template-\(name)" }
    }

    // MARK: - AI Improvement
    enum AIImprovement {
        static let sheet = "ai-improvement-sheet"
        static let loading = "ai-improvement-loading"
        static let suggestion = "ai-improvement-suggestion"
        static let acceptButton = "ai-improvement-accept"
        static let rejectButton = "ai-improvement-reject"
        static let error = "ai-improvement-error"
    }

    // MARK: - Event Emit
    enum EventEmit {
        static let sheet = "event-emit-sheet"
        static let topicPicker = "emit-topic-picker"
        static let payloadEditor = "emit-payload-editor"
        static let submitButton = "emit-submit-button"
        static let cancelButton = "emit-cancel-button"
        static let success = "emit-success"
        static let error = "emit-error"
    }

    // MARK: - Create Ralph Wizard
    enum CreateWizard {
        static let view = "wizard-view"
        static func step(n: Int) -> String { "wizard-step-\(n)" }
        static let nextButton = "wizard-next"
        static let backButton = "wizard-back"
        static let createButton = "wizard-create"
        static let cancelButton = "wizard-cancel"
        static let progressIndicator = "wizard-progress"
    }

    // MARK: - Scratchpad
    enum Scratchpad {
        static let view = "scratchpad-view"
        static let header = "scratchpad-header"
        static let progress = "scratchpad-progress"
        static let tasks = "scratchpad-tasks"
        static let autoRefresh = "scratchpad-auto-refresh"
        static let content = "scratchpad-content-text"
        static let loading = "scratchpad-content-loading"
    }

    // MARK: - Host Metrics
    enum HostMetrics {
        static let view = "host-metrics-view"
        static let cpu = "host-cpu"
        static let memory = "host-memory"
        static let disk = "host-disk"
        static let network = "host-network"
        static let processes = "host-processes"
    }

    // MARK: - Signal Emitter
    enum SignalEmitter {
        static let view = "signal-emitter-view"
        static let picker = "signal-picker"
        static let emitButton = "signal-emit-button"
        static let status = "signal-status"
    }

    // MARK: - Hat Flow
    enum HatFlow {
        static let view = "hat-flow-view"
        static let currentHat = "hat-flow-current"
        static let timeline = "hat-flow-timeline"
        static func hatItem(index: Int) -> String { "hat-item-\(index)" }
    }

    // MARK: - Verbose Event Stream
    enum VerboseStream {
        static let view = "verbose-stream-view"
        static let filterAll = "verbose-filter-all"
        static let filterEvents = "verbose-filter-events"
        static let filterTools = "verbose-filter-tools"
        static let filterErrors = "verbose-filter-errors"
    }

    // MARK: - Errors
    enum Error {
        static let view = "error-view"
        static let message = "error-message"
        static let retryButton = "error-retry"
        static let dismissButton = "error-dismiss"
    }

    // MARK: - Unified Ralph View
    enum UnifiedRalph {
        static let view = "unified-ralph-view"
        static let eventStream = "unified-event-stream"
        static let controlPanel = "unified-control-panel"
        static let metricsPanel = "unified-metrics-panel"
    }
}
