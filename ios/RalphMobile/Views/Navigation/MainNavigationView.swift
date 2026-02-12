import SwiftUI
import RalphShared

/// Main navigation structure for Ralph Mobile v5
/// Uses NavigationSplitView for iPad 3-column layout, collapses to stack on iPhone
struct MainNavigationView: View {
    /// Server configuration from parent (ContentView)
    let serverURL: URL
    let apiKey: String

    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    @EnvironmentObject var navigationManager: NavigationManager

    @StateObject private var sessionListViewModel = SessionListViewModel()
    @StateObject private var sessionViewModel: SessionViewModel

    init(serverURL: URL, apiKey: String) {
        self.serverURL = serverURL
        self.apiKey = apiKey
        _sessionViewModel = StateObject(wrappedValue: SessionViewModel(baseURL: serverURL, apiKey: apiKey))
    }

    @State private var selectedSession: Session? = nil
    @State private var selectedGlobalView: GlobalView? = nil
    @State private var showCreateRalph: Bool = false
    @State private var showSteeringSheet: Bool = false
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    // Persist sidebar selection across scene disconnects
    @SceneStorage("selectedSessionId") private var savedSessionId: String?
    @SceneStorage("selectedGlobalViewRaw") private var savedGlobalViewRaw: String?

    // Navigation path for iPhone compact mode
    @State private var navigationPath = NavigationPath()

    var body: some View {
        mainContent
            .tint(CyberpunkTheme.accentCyan)
            .task {
                await sessionListViewModel.fetchSessions()
                restoreSavedSelection()
            }
            .task {
                // Health check polling every 30 seconds
                while !Task.isCancelled {
                    await sessionListViewModel.checkHealth()
                    try? await Task.sleep(nanoseconds: 30_000_000_000)
                }
            }
            .onReceive(NotificationCenter.default.publisher(for: .serverCredentialsDidChange)) { _ in
                Task {
                    await sessionListViewModel.fetchSessions()
                    await sessionListViewModel.checkHealth()
                }
            }
            .sheet(isPresented: $showCreateRalph) {
                createWizardSheet
            }
            .task(id: selectedSession?.id) {
                handleSessionConnection()
                // Persist selection for scene restoration
                savedSessionId = selectedSession?.id
                if selectedSession != nil { savedGlobalViewRaw = nil }
            }
            .onChange(of: navigationManager.selectedGlobalView) { _, newValue in
                handleGlobalViewNavigation(newValue)
            }
            .onChange(of: navigationManager.sessionNavigationPath) { _, newPath in
                handleSessionNavigation(newPath)
            }
            .onChange(of: navigationManager.showCreateWizard) { _, newValue in
                showCreateRalph = newValue
            }
            .onAppear {
                handleProgrammaticNavigationOnAppear()
            }
    }

    private var mainContent: some View {
        Group {
            if horizontalSizeClass == .compact {
                compactNavigationView
            } else {
                regularNavigationView
            }
        }
    }

    private var createWizardSheet: some View {
        CreateRalphWizard(
            onComplete: { config, prompt, directory in
                Task {
                    await createRalph(config: config, prompt: prompt, directory: directory)
                }
            },
            onCancel: {
                showCreateRalph = false
            }
        )
    }

    private func handleSessionConnection() {
        if let session = selectedSession {
            sessionViewModel.connect(to: session)
        } else {
            sessionViewModel.disconnect()
        }
    }

    private func handleGlobalViewNavigation(_ viewName: String?) {
        guard let viewName = viewName,
              let view = GlobalView(rawValue: viewName) else {
            return
        }
        selectedSession = nil
        selectedGlobalView = view
        savedGlobalViewRaw = view.rawValue
        savedSessionId = nil
        if horizontalSizeClass == .compact {
            navigationPath.append(NavigationDestination.global(view))
        }
    }

    private func handleSessionNavigation(_ newPath: [String]) {
        guard let sessionId = newPath.first else {
            return
        }
        Task {
            await sessionListViewModel.fetchSessions()
            if let session = sessionListViewModel.sessions.first(where: { $0.id == sessionId }) {
                selectedSession = session
                selectedGlobalView = nil
                if horizontalSizeClass == .compact {
                    navigationPath.append(NavigationDestination.session(session))
                }
            }
        }
    }

    private func handleProgrammaticNavigationOnAppear() {
        guard let navigateTo = UserDefaults.standard.string(forKey: "navigateTo") else {
            return
        }

        // Clear immediately
        UserDefaults.standard.removeObject(forKey: "navigateTo")
        UserDefaults.standard.synchronize()

        #if DEBUG
        print("handleProgrammaticNavigationOnAppear: navigateTo=\(navigateTo)")
        #endif

        // Delay to ensure view hierarchy is ready
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            if navigateTo == "new-ralph" {
                self.showCreateRalph = true
            } else if let globalView = GlobalView(rawValue: navigateTo) {
                self.navigateToGlobalView(globalView)
            } else if navigateTo.hasPrefix("session/") {
                let sessionId = String(navigateTo.dropFirst("session/".count))
                self.navigateToSession(id: sessionId)
            }
        }
    }

    /// Navigate to a global view, updating selection state and navigation path.
    private func navigateToGlobalView(_ view: GlobalView) {
        selectedGlobalView = view
        selectedSession = nil
        savedGlobalViewRaw = view.rawValue
        savedSessionId = nil
        if horizontalSizeClass == .compact {
            navigationPath.append(NavigationDestination.global(view))
        }
    }

    /// Navigate to a session by ID, fetching sessions if needed.
    private func navigateToSession(id sessionId: String) {
        Task {
            await sessionListViewModel.fetchSessions()
            if let session = sessionListViewModel.sessions.first(where: { $0.id == sessionId }) {
                selectedSession = session
                selectedGlobalView = nil
                savedSessionId = session.id
                savedGlobalViewRaw = nil
                if horizontalSizeClass == .compact {
                    navigationPath.append(NavigationDestination.session(session))
                }
            }
        }
    }

    /// Restore the previously selected session or global view from SceneStorage
    /// after sessions have been fetched on launch.
    private func restoreSavedSelection() {
        if let id = savedSessionId,
           let session = sessionListViewModel.sessions.first(where: { $0.id == id }) {
            selectedSession = session
            selectedGlobalView = nil
        } else if let raw = savedGlobalViewRaw,
                  let view = GlobalView(rawValue: raw) {
            selectedGlobalView = view
            selectedSession = nil
        }
    }

    // MARK: - Compact Navigation (iPhone)

    private var compactNavigationView: some View {
        NavigationStack(path: $navigationPath) {
            SidebarView(
                viewModel: sessionListViewModel,
                selectedSession: Binding(
                    get: { selectedSession },
                    set: { newValue in
                        selectedSession = newValue
                        selectedGlobalView = nil
                        if let session = newValue {
                            navigationPath.append(NavigationDestination.session(session))
                        }
                    }
                ),
                selectedGlobalView: Binding(
                    get: { selectedGlobalView },
                    set: { newValue in
                        selectedGlobalView = newValue
                        selectedSession = nil
                        if let view = newValue {
                            navigationPath.append(NavigationDestination.global(view))
                        }
                    }
                ),
                showCreateRalph: $showCreateRalph
            )
            .navigationBarTitleDisplayMode(.inline)
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(for: NavigationDestination.self) { destination in
                switch destination {
                case .session(let session):
                    UnifiedRalphView(
                        viewModel: sessionViewModel,
                        showSteeringSheet: $showSteeringSheet
                    )
                    .onAppear {
                        // Sync selectedSession state for task(id:) to trigger connection
                        if selectedSession?.id != session.id {
                            selectedSession = session
                        }
                    }
                case .global(let view):
                    globalViewContent(for: view)
                }
            }
        }
        .refreshable {
            await sessionListViewModel.fetchSessions()
        }
    }

    // MARK: - Regular Navigation (iPad)

    private var regularNavigationView: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            // Sidebar column
            SidebarView(
                viewModel: sessionListViewModel,
                selectedSession: $selectedSession,
                selectedGlobalView: $selectedGlobalView,
                showCreateRalph: $showCreateRalph
            )
            .navigationBarTitleDisplayMode(.inline)
            .toolbar(.hidden, for: .navigationBar)
        } detail: {
            // Detail column - shows selected Ralph or global view
            detailView
                .navigationBarTitleDisplayMode(.inline)
        }
        .navigationSplitViewStyle(.balanced)
        .refreshable {
            await sessionListViewModel.fetchSessions()
        }
    }

    // MARK: - Detail View

    @ViewBuilder
    private var detailView: some View {
        if selectedSession != nil {
            // Show unified Ralph view for selected session
            UnifiedRalphView(
                viewModel: sessionViewModel,
                showSteeringSheet: $showSteeringSheet
            )
        } else if let globalView = selectedGlobalView {
            // Show global view
            globalViewContent(for: globalView)
        } else {
            // Empty state
            emptyDetailView
        }
    }

    @ViewBuilder
    private func globalViewContent(for view: GlobalView) -> some View {
        switch view {
        case .skills:
            SkillsContainerView()
        case .library:
            LibraryContainerView()
        case .tasks:
            TasksView()
        case .loops:
            LoopsView()
        case .robot:
            RobotView()
        case .host:
            HostMetricsContainerView()
        case .settings:
            SettingsContainerView()
        }
    }

    // MARK: - Navigation Destination

    enum NavigationDestination: Hashable {
        case session(Session)  // Carry the session to avoid state batching race
        case global(GlobalView)
    }

    private var emptyDetailView: some View {
        VStack(spacing: 16) {
            Image(systemName: "rectangle.stack")
                .font(.largeTitle)
                .foregroundColor(CyberpunkTheme.textMuted)

            Text("Select a Ralph session")
                .font(.headline)
                .foregroundColor(CyberpunkTheme.textSecondary)

            Text("Or create a new one to get started")
                .font(.subheadline)
                .foregroundColor(CyberpunkTheme.textMuted)

            Button {
                showCreateRalph = true
            } label: {
                Label("New Ralph", systemImage: "plus")
                    .font(.subheadline.bold())
                    .foregroundColor(CyberpunkTheme.bgPrimary)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(CyberpunkTheme.accentCyan)
                    .cornerRadius(8)
            }
            .padding(.top, 8)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(CyberpunkTheme.bgPrimary)
    }

    // MARK: - Actions

    private func createRalph(config: String, prompt: String, directory: String) async {
        do {
            let newSession = try await RalphAPIClient.shared.createSession(
                config: config,
                prompt: prompt,
                directory: directory
            )
            await sessionListViewModel.fetchSessions()
            selectedSession = newSession
            showCreateRalph = false
        } catch {
            #if DEBUG
            print("Failed to create Ralph: \(error)")
            #endif
        }
    }
}

// MARK: - Container Views (wired to actual implementations)

struct SkillsContainerView: View {
    var body: some View {
        SkillsView()
    }
}

struct LibraryContainerView: View {
    var body: some View {
        LibraryView()
    }
}

struct HostMetricsContainerView: View {
    var body: some View {
        HostMetricsView()
    }
}

struct SettingsContainerView: View {
    var body: some View {
        AppSettingsView()
    }
}

#Preview {
    MainNavigationView(
        serverURL: URL(string: "http://127.0.0.1:8080")!,
        apiKey: ""
    )
}
