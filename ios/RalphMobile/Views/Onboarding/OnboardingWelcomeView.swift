import SwiftUI

/// Welcome screen shown on first app launch
/// Displays Ralph branding and entry point to onboarding flow
struct OnboardingWelcomeView: View {
    let onGetStarted: () -> Void

    var body: some View {
        VStack(spacing: 40) {
            Spacer()

            // Branding Section
            VStack(spacing: 20) {
                // Glowing "R" logo
                ZStack {
                    Circle()
                        .fill(CyberpunkTheme.bgCard)
                        .frame(width: 72, height: 72)

                    Circle()
                        .stroke(CyberpunkTheme.accentCyan, lineWidth: 2)
                        .frame(width: 72, height: 72)
                        .glow(CyberpunkTheme.accentCyan, radius: 12, opacity: 0.6)

                    Text("R")
                        .font(.system(.largeTitle, design: .monospaced).bold())
                        .foregroundColor(CyberpunkTheme.accentCyan)
                }

                VStack(spacing: 8) {
                    Text("RALPH MOBILE")
                        .font(.system(.title, design: .monospaced).bold())
                        .foregroundColor(CyberpunkTheme.textPrimary)
                        .kerning(4)

                    Text("ORCHESTRATOR")
                        .font(.system(.caption, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textSecondary)
                        .kerning(2)
                }
            }

            Spacer()

            // Get Started Button
            VStack(spacing: 16) {
                Button {
                    onGetStarted()
                } label: {
                    HStack(spacing: 8) {
                        Text("GET STARTED")
                            .font(.system(.body, design: .monospaced).bold())
                        Image(systemName: "arrow.right")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(CyberpunkTheme.accentCyan)
                    .foregroundColor(CyberpunkTheme.bgPrimary)
                    .cornerRadius(8)
                }
                .padding(.horizontal, 24)

                // Version String
                if let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String,
                   let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String {
                    Text("v\(version) (\(build))")
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundColor(CyberpunkTheme.textMuted)
                }
            }
            .padding(.bottom, 40)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(CyberpunkTheme.bgPrimary)
    }
}

#Preview {
    OnboardingWelcomeView(onGetStarted: {})
        .preferredColorScheme(.dark)
}
