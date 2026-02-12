import SwiftUI

/// Root content view for Ralph Mobile
/// Uses a 3-state model: loading → onboarding (if server unreachable) → connected
/// The onboarding state is further decomposed into sub-steps via OnboardingStep enum.
/// IMPORTANT: Once .connected is reached, MainNavigationView persists forever.
/// Background/settings changes only reconfigure the API client, never touch appState.
struct ContentView: View {
    enum AppState {
        case loading
        case onboarding
        case connected
    }

    /// Sub-states within the onboarding flow.
    /// Uses a simple enum instead of NavigationStack for a linear wizard.
    enum OnboardingStep {
        case welcome
        case methodPicker
        case localSetup
        case tunnelSetup
        case remoteSetup
    }

    @AppStorage("serverURL") private var serverURLString: String = "http://127.0.0.1:8080"
    @State private var appState: AppState = .loading
    @State private var onboardingStep: OnboardingStep = .welcome

    private var serverURL: URL {
        URL(string: serverURLString) ?? URL(string: "http://127.0.0.1:8080")!
    }

    /// Resolve the current API key from Keychain (or empty string if none).
    private var currentAPIKey: String {
        KeychainService.loadAPIKey(for: serverURLString) ?? ""
    }

    var body: some View {
        ZStack {
            CyberpunkTheme.bgPrimary.ignoresSafeArea()

            switch appState {
            case .loading:
                loadingView
            case .onboarding:
                onboardingFlow
            case .connected:
                MainNavigationView(serverURL: serverURL, apiKey: currentAPIKey)
            }
        }
        .preferredColorScheme(.dark)
        .task {
            await initialHealthCheck()
        }
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)) { _ in
            // ONLY reconfigure API client — NEVER touch appState (prevents P0 black screen bug)
            Task {
                await reconfigureAPIClient()
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: .serverCredentialsDidChange)) { _ in
            // ONLY reconfigure API client — NEVER touch appState
            Task {
                await reconfigureAPIClient()
            }
        }
    }

    // MARK: - Onboarding Flow (State Machine)

    @ViewBuilder
    private var onboardingFlow: some View {
        switch onboardingStep {
        case .welcome:
            OnboardingWelcomeView(
                onGetStarted: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .methodPicker
                    }
                }
            )

        case .methodPicker:
            ConnectionMethodPicker(
                onSelectLocal: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .localSetup
                    }
                },
                onSelectTunnel: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .tunnelSetup
                    }
                },
                onSelectSetup: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .remoteSetup
                    }
                },
                onBack: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .welcome
                    }
                }
            )

        case .localSetup:
            ServerOnboardingView(
                serverURLString: $serverURLString,
                onConnected: { url in
                    handleConnectionSuccess(url: url)
                },
                onBack: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .methodPicker
                    }
                }
            )

        case .tunnelSetup:
            TunnelOnboardingView(
                onConnected: { url in
                    serverURLString = url
                    handleConnectionSuccess(url: url)
                },
                onBack: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .methodPicker
                    }
                }
            )

        case .remoteSetup:
            SetupScriptView(
                onConnected: { url in
                    serverURLString = url
                    handleConnectionSuccess(url: url)
                },
                onBack: {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        onboardingStep = .methodPicker
                    }
                }
            )
        }
    }

    // MARK: - Connection Success

    private func handleConnectionSuccess(url: String) {
        serverURLString = url
        let key = KeychainService.loadAPIKey(for: url) ?? ""
        RalphAPIClient.configure(baseURL: serverURL, apiKey: key)
        withAnimation(.easeInOut(duration: 0.3)) {
            appState = .connected
        }
    }

    // MARK: - Health Check

    private func initialHealthCheck() async {
        let key = KeychainService.loadAPIKey(for: serverURLString) ?? ""
        RalphAPIClient.configure(baseURL: serverURL, apiKey: key)
        let healthy = await RalphAPIClient.checkHealth()
        withAnimation(.easeInOut(duration: 0.3)) {
            appState = healthy ? .connected : .onboarding
        }
    }

    private func reconfigureAPIClient() async {
        let key = KeychainService.loadAPIKey(for: serverURLString) ?? ""
        RalphAPIClient.configure(baseURL: serverURL, apiKey: key)
    }

    // MARK: - Loading View

    private var loadingView: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Image(systemName: "bolt.circle.fill")
                    .font(.largeTitle)
                    .foregroundColor(CyberpunkTheme.accentCyan)
                    .shadow(color: CyberpunkTheme.accentCyan.opacity(0.5), radius: 16)

                Text("RALPH MOBILE")
                    .font(.system(.title, design: .monospaced).bold())
                    .foregroundColor(CyberpunkTheme.textPrimary)
                    .kerning(4)

                Text("ORCHESTRATOR")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textMuted)
                    .kerning(2)
            }

            VStack(spacing: 12) {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: CyberpunkTheme.accentCyan))
                    .scaleEffect(1.5)

                Text("Connecting...")
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textSecondary)
            }
        }
    }
}

#Preview {
    ContentView()
}
