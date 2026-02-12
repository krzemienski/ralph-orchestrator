import SwiftUI

/// Reusable loading state view used across all data-driven screens.
/// Replaces 17 inline loading views for DRY consistency.
struct SharedLoadingView: View {
    let message: String

    init(_ message: String = "Loading...") {
        self.message = message
    }

    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: CyberpunkTheme.accentCyan))
                .scaleEffect(1.2)

            Text(message)
                .font(.system(.body, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textSecondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    ZStack {
        CyberpunkTheme.bgPrimary.ignoresSafeArea()
        SharedLoadingView("Loading sessions...")
    }
    .preferredColorScheme(.dark)
}
