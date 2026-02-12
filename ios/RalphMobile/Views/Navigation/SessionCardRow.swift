import SwiftUI
import RalphShared

/// Redesigned session row as a card per Stitch sidebar mockup.
/// Rounded card with accent bar, avatar, hat badge, time-ago label.
struct SessionCardRow: View {
    let session: Session

    private var hatColor: Color {
        guard let hat = session.hat, !hat.isEmpty else {
            return CyberpunkTheme.textMuted
        }
        return CyberpunkTheme.hatColor(for: hat)
    }

    private var sessionInitial: String {
        String(session.id.prefix(1)).uppercased()
    }

    private var isActive: Bool {
        session.status == "running"
    }

    private var timeAgoText: String {
        guard let startTime = session.startTime else { return "" }
        let interval = Date().timeIntervalSince(startTime)
        if interval < 60 {
            return "\(Int(interval))s ago"
        } else if interval < 3600 {
            return "\(Int(interval / 60))m ago"
        } else if interval < 86400 {
            return "\(Int(interval / 3600))h ago"
        } else {
            return "\(Int(interval / 86400))d ago"
        }
    }

    var body: some View {
        HStack(spacing: 0) {
            // Left accent bar
            RoundedRectangle(cornerRadius: 2)
                .fill(hatColor)
                .frame(width: 3)
                .padding(.vertical, 4)

            HStack(spacing: 10) {
                // Circle avatar
                ZStack {
                    Circle()
                        .fill(CyberpunkTheme.accentCyan)
                        .frame(width: 32, height: 32)

                    Text(sessionInitial)
                        .font(.system(.subheadline, design: .monospaced).bold())
                        .foregroundColor(CyberpunkTheme.bgPrimary)
                }

                // Session info
                VStack(alignment: .leading, spacing: 4) {
                    Text(session.id)
                        .font(.system(.subheadline, design: .monospaced).bold())
                        .foregroundColor(CyberpunkTheme.textPrimary)
                        .lineLimit(1)
                        .truncationMode(.middle)

                    HStack(spacing: 6) {
                        // Hat badge pill
                        if let hat = session.hat, !hat.isEmpty {
                            Text(hat)
                                .font(.system(.caption2, design: .monospaced))
                                .foregroundColor(hatColor)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(hatColor.opacity(0.15))
                                .cornerRadius(4)
                        }

                        // Iteration text
                        if let total = session.total, total > 0 {
                            Text("Iter \(session.iteration)/\(total)")
                                .font(.caption2)
                                .foregroundColor(CyberpunkTheme.textMuted)
                        } else {
                            Text("Iter \(session.iteration)")
                                .font(.caption2)
                                .foregroundColor(CyberpunkTheme.textMuted)
                        }
                    }
                }

                Spacer()

                // Trailing info
                VStack(alignment: .trailing, spacing: 4) {
                    if !timeAgoText.isEmpty {
                        Text(timeAgoText)
                            .font(.caption2)
                            .foregroundColor(CyberpunkTheme.textMuted)
                    }

                    if isActive {
                        Circle()
                            .fill(CyberpunkTheme.accentGreen)
                            .frame(width: 8, height: 8)
                            .pulsing()
                    }
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 10)
        }
        .background(CyberpunkTheme.bgCard)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(CyberpunkTheme.border, lineWidth: 1)
        )
    }
}

#Preview {
    VStack(spacing: 8) {
        SessionCardRow(session: Session(
            id: "api-service",
            iteration: 3,
            total: 10,
            hat: "builder",
            startedAt: ISO8601DateFormatter().string(from: Date().addingTimeInterval(-120)),
            status: "running"
        ))
        SessionCardRow(session: Session(
            id: "web-client",
            iteration: 1,
            hat: "reviewer",
            status: "paused"
        ))
        SessionCardRow(session: Session(
            id: "data-pipeline",
            iteration: 5,
            hat: nil,
            status: "completed"
        ))
    }
    .padding()
    .background(CyberpunkTheme.bgPrimary)
}
