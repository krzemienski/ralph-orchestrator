import SwiftUI

/// Server onboarding view shown when health check fails.
/// Allows user to enter/edit server URL and optional API key, then test connection.
struct ServerOnboardingView: View {
    @Binding var serverURLString: String
    let onConnected: (String) -> Void
    var onBack: (() -> Void)? = nil

    @State private var apiKeyText: String = ""
    @State private var isChecking = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 32) {
            // Back button (shown when used in onboarding flow)
            if let onBack {
                HStack {
                    Button {
                        onBack()
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                            Text("BACK")
                                .font(.system(.caption, design: .monospaced).bold())
                        }
                        .foregroundColor(CyberpunkTheme.textSecondary)
                    }
                    Spacer()
                }
                .padding(.horizontal, 24)
            }

            Spacer()

            // Branding
            VStack(spacing: 12) {
                Image(systemName: "bolt.circle.fill")
                    .font(.largeTitle)
                    .foregroundColor(CyberpunkTheme.accentCyan)
                    .shadow(color: CyberpunkTheme.accentCyan.opacity(0.5), radius: 16)

                Text("RALPH MOBILE")
                    .font(.system(.title, design: .monospaced).bold())
                    .foregroundColor(CyberpunkTheme.textPrimary)
                    .kerning(4)

                Text("CONNECT TO SERVER")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textMuted)
                    .kerning(2)
            }

            // Connection form
            VStack(spacing: 16) {
                Text("Enter your Ralph server URL to get started.")
                    .font(.subheadline)
                    .foregroundColor(CyberpunkTheme.textSecondary)
                    .multilineTextAlignment(.center)

                VStack(alignment: .leading, spacing: 8) {
                    Text("SERVER URL")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textMuted)
                        .kerning(1)

                    TextField("http://127.0.0.1:8080", text: $serverURLString)
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textPrimary)
                        .padding()
                        .background(CyberpunkTheme.bgTertiary)
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(CyberpunkTheme.border, lineWidth: 1)
                        )
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                        .textContentType(.URL)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("API KEY (OPTIONAL)")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textMuted)
                        .kerning(1)

                    SecureField("Leave empty if not required", text: $apiKeyText)
                        .font(.system(.body, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textPrimary)
                        .padding()
                        .background(CyberpunkTheme.bgTertiary)
                        .cornerRadius(8)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(CyberpunkTheme.border, lineWidth: 1)
                        )
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textContentType(.password)
                }

                if let error = errorMessage {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(CyberpunkTheme.accentRed)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(CyberpunkTheme.accentRed)
                    }
                    .padding(.horizontal)
                }

                Button {
                    Task { await attemptConnection() }
                } label: {
                    HStack(spacing: 8) {
                        if isChecking {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: CyberpunkTheme.bgPrimary))
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "link")
                        }
                        Text(isChecking ? "CONNECTING..." : "CONNECT")
                    }
                    .font(.system(.body, design: .monospaced).bold())
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isChecking ? CyberpunkTheme.textMuted : CyberpunkTheme.accentCyan)
                    .foregroundColor(CyberpunkTheme.bgPrimary)
                    .cornerRadius(8)
                }
                .disabled(isChecking || serverURLString.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            .padding(24)
            .background(CyberpunkTheme.bgCard)
            .cornerRadius(16)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(CyberpunkTheme.border, lineWidth: 1)
            )
            .padding(.horizontal, 24)

            Spacer()
        }
    }

    private func attemptConnection() async {
        isChecking = true
        errorMessage = nil

        guard let url = URL(string: serverURLString) else {
            errorMessage = "Invalid URL format"
            isChecking = false
            return
        }

        let key = apiKeyText.trimmingCharacters(in: .whitespaces)

        // Configure the API client with the new URL and optional API key
        RalphAPIClient.configure(baseURL: url, apiKey: key)

        let healthy = await RalphAPIClient.checkHealth()

        if healthy {
            // Save API key to Keychain if provided
            if !key.isEmpty {
                KeychainService.saveAPIKey(key, for: serverURLString)
            }
            onConnected(serverURLString)
        } else {
            errorMessage = "Could not connect to server at \(serverURLString). Check the URL and ensure the server is running."
        }

        isChecking = false
    }
}

#Preview {
    ZStack {
        CyberpunkTheme.bgPrimary.ignoresSafeArea()
        ServerOnboardingView(
            serverURLString: .constant("http://127.0.0.1:8080"),
            onConnected: { _ in }
        )
    }
    .preferredColorScheme(.dark)
}
