import SwiftUI

/// Reusable empty state view used across all data-driven screens.
/// Replaces 9 inline empty views for DRY consistency.
struct SharedEmptyView: View {
    let icon: String
    let title: String
    let subtitle: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.largeTitle)
                .foregroundColor(CyberpunkTheme.textMuted)

            Text(title)
                .font(.system(.headline, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textPrimary)

            Text(subtitle)
                .font(.subheadline)
                .foregroundColor(CyberpunkTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    ZStack {
        CyberpunkTheme.bgPrimary.ignoresSafeArea()
        SharedEmptyView(
            icon: "tray",
            title: "No Sessions",
            subtitle: "Start a new orchestration session to get going."
        )
    }
    .preferredColorScheme(.dark)
}
