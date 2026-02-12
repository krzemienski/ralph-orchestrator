import SwiftUI

/// Connection method picker - lets user choose between local network, Cloudflare tunnel, or remote setup
struct ConnectionMethodPicker: View {
    let onSelectLocal: () -> Void
    let onSelectTunnel: () -> Void
    let onSelectSetup: () -> Void
    let onBack: () -> Void

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

            // Title
            VStack(spacing: 12) {
                Text("CONNECT TO SERVER")
                    .font(.system(.title2, design: .monospaced).bold())
                    .foregroundColor(CyberpunkTheme.textPrimary)
                    .kerning(2)

                Text("Choose your connection method")
                    .font(.system(.subheadline, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textSecondary)
            }

            // Connection Method Cards
            VStack(spacing: 16) {
                // Local Network Card
                Button {
                    onSelectLocal()
                } label: {
                    connectionCard(
                        icon: "wifi",
                        title: "Local Network",
                        description: "Connect to a server on your local network"
                    )
                }
                .buttonStyle(.plain)

                // Cloudflare Tunnel Card
                Button {
                    onSelectTunnel()
                } label: {
                    connectionCard(
                        icon: "globe",
                        title: "Cloudflare Tunnel",
                        description: "Connect through a Cloudflare named tunnel"
                    )
                }
                .buttonStyle(.plain)

                // Remote Setup Card
                Button {
                    onSelectSetup()
                } label: {
                    connectionCard(
                        icon: "terminal",
                        title: "Set Up New Backend",
                        description: "Install Ralph on a remote machine via SSH"
                    )
                }
                .buttonStyle(.plain)
            }
            .padding(.horizontal, 24)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(CyberpunkTheme.bgPrimary)
    }

    private func connectionCard(icon: String, title: String, description: String) -> some View {
        HStack(spacing: 16) {
            // Icon
            Image(systemName: icon)
                .font(.title)
                .foregroundColor(CyberpunkTheme.accentCyan)
                .frame(width: 48, height: 48)

            // Text
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(.body, design: .monospaced).bold())
                    .foregroundColor(CyberpunkTheme.textPrimary)

                Text(description)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textSecondary)
                    .multilineTextAlignment(.leading)
            }

            Spacer()

            // Chevron
            Image(systemName: "chevron.right")
                .foregroundColor(CyberpunkTheme.textMuted)
        }
        .padding(20)
        .background(CyberpunkTheme.bgCard)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(CyberpunkTheme.border, lineWidth: 1)
        )
    }
}

#Preview {
    ConnectionMethodPicker(
        onSelectLocal: {},
        onSelectTunnel: {},
        onSelectSetup: {},
        onBack: {}
    )
    .preferredColorScheme(.dark)
}
