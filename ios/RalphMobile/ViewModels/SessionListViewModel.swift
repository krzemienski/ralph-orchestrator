import Foundation
import SwiftUI
import RalphShared

// MARK: - Session List ViewModel

@MainActor
class SessionListViewModel: ObservableObject {
    @Published var sessions: [Session] = []
    @Published var isLoading: Bool = true  // Start as true to show loading on first render
    @Published var error: String? = nil
    @Published var isServerReachable: Bool = true

    var activeSessionCount: Int {
        sessions.filter { $0.status == "running" }.count
    }

    func fetchSessions() async {
        guard RalphAPIClient.isConfigured else {
            error = "API client not configured"
            isLoading = false
            return
        }

        isLoading = true
        error = nil

        do {
            sessions = try await RalphAPIClient.shared.getSessions()
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func checkHealth() async {
        isServerReachable = await RalphAPIClient.checkHealth()
    }
}
