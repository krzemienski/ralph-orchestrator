import SwiftUI

/// Cloudflare tunnel connection setup view
/// Allows user to enter tunnel domain and test connection
struct TunnelOnboardingView: View {
    let onConnected: (String) -> Void
    let onBack: () -> Void

    @State private var tunnelDomain: String = ""
    @State private var apiKeyText: String = ""
    @State private var isChecking = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 32) {
            // Back button
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

            Spacer()

            // Branding
            VStack(spacing: 12) {
                Image(systemName: "globe")
                    .font(.largeTitle)
                    .foregroundColor(CyberpunkTheme.accentCyan)
                    .glow(CyberpunkTheme.accentCyan, radius: 12, opacity: 0.5)

                Text("CLOUDFLARE TUNNEL")
                    .font(.system(.title2, design: .monospaced).bold())
                    .foregroundColor(CyberpunkTheme.textPrimary)
                    .kerning(2)

                Text("Connect via tunnel")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textSecondary)
                    .kerning(1)
            }

            // Connection form
            VStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("TUNNEL DOMAIN")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textMuted)
                        .kerning(1)

                    TextField("ralph.yourdomain.com", text: $tunnelDomain)
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
                }

                // Guidance
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) {
                        Image(systemName: "info.circle")
                            .foregroundColor(CyberpunkTheme.accentCyan)
                        Text("REQUIREMENTS")
                            .font(.system(.caption2, design: .monospaced).bold())
                            .foregroundColor(CyberpunkTheme.textSecondary)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        guidanceRow("Named tunnel required (Quick Tunnels don't support SSE)")
                        guidanceRow("Ensure tunnel is running before connecting")
                        guidanceRow("Use your custom domain or *.cfargotunnel.com")
                    }
                }
                .padding(12)
                .background(CyberpunkTheme.bgTertiary)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(CyberpunkTheme.border, lineWidth: 1)
                )

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
                        Text(isChecking ? "CONNECTING..." : "TEST CONNECTION")
                    }
                    .font(.system(.body, design: .monospaced).bold())
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isChecking ? CyberpunkTheme.textMuted : CyberpunkTheme.accentCyan)
                    .foregroundColor(CyberpunkTheme.bgPrimary)
                    .cornerRadius(8)
                }
                .disabled(isChecking || tunnelDomain.trimmingCharacters(in: .whitespaces).isEmpty)
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
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(CyberpunkTheme.bgPrimary)
    }

    private func guidanceRow(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 6) {
            Text("•")
                .foregroundColor(CyberpunkTheme.accentCyan)
            Text(text)
                .font(.system(.caption2, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textSecondary)
        }
    }

    private func attemptConnection() async {
        isChecking = true
        errorMessage = nil

        let domain = tunnelDomain.trimmingCharacters(in: .whitespaces)
        guard !domain.isEmpty else {
            errorMessage = "Please enter a tunnel domain"
            isChecking = false
            return
        }

        // Build URL
        let urlString: String
        if domain.hasPrefix("http://") || domain.hasPrefix("https://") {
            urlString = domain
        } else {
            urlString = "https://\(domain)"
        }

        guard let url = URL(string: urlString) else {
            errorMessage = "Invalid URL format"
            isChecking = false
            return
        }

        // Test connection
        let key = apiKeyText.trimmingCharacters(in: .whitespaces)
        RalphAPIClient.configure(baseURL: url, apiKey: key)
        let healthy = await RalphAPIClient.checkHealth()

        if healthy {
            if !key.isEmpty {
                KeychainService.saveAPIKey(key, for: urlString)
            }
            onConnected(urlString)
        } else {
            errorMessage = "Could not connect via tunnel. Ensure the tunnel is running and the domain is correct. Note: Only named tunnels support SSE streaming."
        }

        isChecking = false
    }
}

#Preview {
    ZStack {
        CyberpunkTheme.bgPrimary.ignoresSafeArea()
        TunnelOnboardingView(
            onConnected: { _ in },
            onBack: {}
        )
    }
    .preferredColorScheme(.dark)
}
