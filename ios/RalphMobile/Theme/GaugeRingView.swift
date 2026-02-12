import SwiftUI
import RalphShared

/// Circular gauge ring view for displaying percentage metrics.
/// Used in HostMetricsView for CPU, Memory, and Disk usage per Stitch design.
struct GaugeRingView: View {
    let value: Double // 0.0 - 1.0
    let label: String
    let color: Color
    var lineWidth: CGFloat = 8

    var body: some View {
        ZStack {
            // Background ring
            Circle()
                .stroke(CyberpunkTheme.bgTertiary, lineWidth: lineWidth)

            // Value ring
            Circle()
                .trim(from: 0, to: min(max(value, 0), 1))
                .stroke(color, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 0.5), value: value)

            // Center label
            VStack(spacing: 2) {
                Text("\(Int(value * 100))%")
                    .font(.system(.title3, design: .monospaced).bold())
                    .foregroundColor(CyberpunkTheme.textPrimary)

                Text(label.uppercased())
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textMuted)
                    .kerning(1)
            }
        }
    }
}

#Preview {
    ZStack {
        CyberpunkTheme.bgPrimary.ignoresSafeArea()
        HStack(spacing: 24) {
            GaugeRingView(value: 0.34, label: "CPU", color: CyberpunkTheme.accentCyan)
                .frame(width: 100, height: 100)
            GaugeRingView(value: 0.67, label: "Memory", color: CyberpunkTheme.accentYellow)
                .frame(width: 100, height: 100)
            GaugeRingView(value: 0.45, label: "Disk", color: CyberpunkTheme.accentGreen)
                .frame(width: 100, height: 100)
        }
    }
    .preferredColorScheme(.dark)
}
