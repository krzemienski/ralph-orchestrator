import SwiftUI

/// Reusable error state view used across all data-driven screens.
/// Replaces 13 inline error views for DRY consistency.
struct SharedErrorView: View {
    let message: String
    var onRetry: (() -> Void)?

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.largeTitle)
                .foregroundColor(CyberpunkTheme.accentRed)

            Text(message)
                .font(.subheadline)
                .foregroundColor(CyberpunkTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            if let onRetry {
                Button {
                    onRetry()
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "arrow.clockwise")
                        Text("Retry")
                    }
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentCyan)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 10)
                    .background(CyberpunkTheme.bgTertiary)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(CyberpunkTheme.accentCyan.opacity(0.3), lineWidth: 1)
                    )
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    ZStack {
        CyberpunkTheme.bgPrimary.ignoresSafeArea()
        SharedErrorView(message: "Failed to load sessions. Check your connection.", onRetry: {})
    }
    .preferredColorScheme(.dark)
}
