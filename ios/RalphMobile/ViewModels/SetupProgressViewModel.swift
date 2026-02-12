import Foundation

/// A single line of terminal output from the remote setup process.
struct LogEntry: Identifiable, Sendable {
    let id = UUID()
    let text: String
    let channel: OutputChannel
    let step: SetupStep
    let timestamp = Date()
}

/// ViewModel that drives the SetupProgressView, bridging SSHSetupService
/// delegate callbacks into @Published state that SwiftUI observes.
///
/// Acts as both the data source for the terminal log view and the
/// SetupProgressDelegate that receives real-time streaming output.
@MainActor
final class SetupProgressViewModel: ObservableObject {

    // MARK: - Published State

    /// The step currently executing (nil before connect or after completion).
    @Published var currentStep: SetupStep?

    /// Steps that have finished successfully.
    @Published var completedSteps: Set<SetupStep> = []

    /// Every line of output received, in order. Drives the terminal scroll view.
    @Published var logLines: [LogEntry] = []

    /// True while establishing the initial SSH connection.
    @Published var isConnecting = false

    /// True while the setup sequence is actively running.
    @Published var isRunning = false

    /// Set when a step fails or connection drops.
    @Published var error: SSHSetupError?

    /// True when cloudflared requires interactive browser authentication.
    @Published var authRequired = false

    /// The message to display when auth is required.
    @Published var authMessage = ""

    /// The tunnel URL extracted after the final step completes.
    @Published var tunnelURL: String?

    /// True when the entire 8-step setup has completed successfully.
    @Published var isComplete = false

    /// The detected remote platform.
    @Published var detectedPlatform: String?

    // MARK: - Private

    private let service = SSHSetupService()
    private var credentials: SSHCredentials?

    // MARK: - Computed

    /// Progress as a fraction of completed steps (0.0 to 1.0).
    var progress: Double {
        Double(completedSteps.count) / Double(SetupStep.allCases.count)
    }

    /// Human-readable status line for the current state.
    var statusText: String {
        if isComplete { return "Setup complete" }
        if let error { return error.localizedDescription ?? "Unknown error" }
        if authRequired { return "Action required" }
        if isConnecting { return "Connecting via SSH..." }
        if let step = currentStep { return "Step \(step.rawValue)/8: \(step.title)" }
        return "Preparing..."
    }

    // MARK: - Actions

    /// Start the full setup sequence with the given credentials.
    func startSetup(credentials: SSHCredentials) async {
        self.credentials = credentials
        isRunning = true
        isConnecting = true
        error = nil
        logLines = []
        completedSteps = []
        currentStep = nil
        isComplete = false
        authRequired = false
        tunnelURL = nil

        addLog("Connecting to \(credentials.host):\(credentials.port)...", channel: .stdout, step: .checkDependencies)

        do {
            let url = try await service.executeSetup(credentials: credentials, delegate: self)
            if !url.isEmpty {
                tunnelURL = url
                isComplete = true

                // Save credentials on success
                SSHCredentialStore.save(credentials)
            }
        } catch {
            // Error already reported via delegate
        }

        isRunning = false
        isConnecting = false
    }

    /// Retry the setup from the beginning (e.g. after cloudflared auth).
    func retry() async {
        authRequired = false
        error = nil
        guard let creds = credentials else { return }
        await startSetup(credentials: creds)
    }

    /// Cancel the in-progress setup.
    func cancel() {
        Task { await service.cancel() }
        isRunning = false
        addLog("Setup cancelled by user.", channel: .stderr, step: currentStep ?? .checkDependencies)
    }

    // MARK: - Helpers

    private func addLog(_ text: String, channel: OutputChannel, step: SetupStep) {
        logLines.append(LogEntry(text: text, channel: channel, step: step))
    }
}

// MARK: - SetupProgressDelegate

extension SetupProgressViewModel: SetupProgressDelegate {

    func setupDidStartStep(_ step: SetupStep) {
        currentStep = step
        isConnecting = false
        addLog("", channel: .stdout, step: step)
        addLog("--- Step \(step.rawValue)/8: \(step.title) ---", channel: .stdout, step: step)
    }

    func setupDidReceiveOutput(_ line: String, channel: OutputChannel, for step: SetupStep) {
        addLog(line, channel: channel, step: step)
    }

    func setupDidCompleteStep(_ step: SetupStep) {
        completedSteps.insert(step)
    }

    func setupRequiresAuth(message: String) {
        authRequired = true
        authMessage = message
        isRunning = false
    }

    func setupDidComplete(tunnelURL: String) {
        self.tunnelURL = tunnelURL
        isComplete = true
        isRunning = false
        addLog("", channel: .stdout, step: .startTunnel)
        addLog("Setup complete! Tunnel: \(tunnelURL)", channel: .stdout, step: .startTunnel)
    }

    func setupDidFail(error: SSHSetupError) {
        self.error = error
        isRunning = false
        let step = currentStep ?? .checkDependencies
        addLog("ERROR: \(error.localizedDescription ?? "Unknown error")", channel: .stderr, step: step)
    }
}
