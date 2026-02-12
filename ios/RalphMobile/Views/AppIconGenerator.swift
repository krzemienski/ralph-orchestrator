import SwiftUI

/// Programmatic app icon generator following the design specification
/// This view can be rendered and captured as an image for use as the app icon
struct AppIconGenerator: View {
    let size: CGFloat
    
    init(size: CGFloat = 1024) {
        self.size = size
    }
    
    var body: some View {
        ZStack {
            // Layer 1: Background gradient
            RadialGradient(
                colors: [
                    Color(hex: "#07070c"),
                    Color(hex: "#030306")
                ],
                center: .center,
                startRadius: 0,
                endRadius: size * 0.6
            )
            
            // Layer 2: Glass ring with gradient
            Circle()
                .stroke(
                    LinearGradient(
                        colors: [
                            CyberpunkTheme.accentCyan.opacity(0.7),
                            CyberpunkTheme.accentMagenta.opacity(0.7),
                            CyberpunkTheme.accentCyan.opacity(0.7)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: size * 0.08
                )
                .frame(width: size * 0.75, height: size * 0.75)
                .shadow(color: CyberpunkTheme.accentCyan.opacity(0.4), radius: size * 0.01)
                .shadow(color: CyberpunkTheme.accentMagenta.opacity(0.3), radius: size * 0.015)
            
            // Layer 3: Inner glass surface
            Circle()
                .fill(
                    RadialGradient(
                        colors: [
                            Color(hex: "#0e0e16").opacity(0.95),
                            Color(hex: "#0e0e16").opacity(0.85)
                        ],
                        center: .center,
                        startRadius: 0,
                        endRadius: size * 0.3
                    )
                )
                .frame(width: size * 0.6, height: size * 0.6)
                .overlay(
                    Circle()
                        .stroke(CyberpunkTheme.accentCyan.opacity(0.2), lineWidth: size * 0.005)
                )
                .shadow(color: .black.opacity(0.3), radius: size * 0.005, y: size * 0.003)
            
            // Layer 4: "R" symbol with gradient and glow
            VStack(spacing: size * 0.04) {
                Text("R")
                    .font(.system(size: size * 0.5, weight: .black, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [
                                CyberpunkTheme.accentCyan,
                                CyberpunkTheme.accentMagenta
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .shadow(color: CyberpunkTheme.accentCyan.opacity(0.6), radius: size * 0.012)
                    .shadow(color: CyberpunkTheme.accentCyan.opacity(0.4), radius: size * 0.024)
                    .shadow(color: CyberpunkTheme.accentMagenta.opacity(0.4), radius: size * 0.02)
                    .shadow(color: .black.opacity(0.8), radius: size * 0.002, y: size * 0.002)
                
                // Layer 5: Accent indicators
                HStack(spacing: size * 0.015) {
                    ForEach(0..<3) { _ in
                        Capsule()
                            .fill(CyberpunkTheme.accentCyan)
                            .frame(width: size * 0.08, height: size * 0.015)
                            .shadow(color: CyberpunkTheme.accentCyan.opacity(0.5), radius: size * 0.005)
                    }
                }
                .opacity(0.8)
            }
        }
        .frame(width: size, height: size)
    }
}

/// Preview helper that shows multiple sizes
struct AppIconSizePreview: View {
    var body: some View {
        VStack(spacing: 40) {
            Text("App Icon Sizes")
                .font(.headline)
                .foregroundColor(.white)
            
            HStack(spacing: 30) {
                VStack {
                    AppIconGenerator(size: 180)
                    Text("180x180\niPhone @3x")
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.gray)
                }
                
                VStack {
                    AppIconGenerator(size: 120)
                    Text("120x120\niPhone @2x")
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.gray)
                }
                
                VStack {
                    AppIconGenerator(size: 80)
                    Text("80x80\nSpotlight")
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.gray)
                }
                
                VStack {
                    AppIconGenerator(size: 40)
                    Text("40x40\nSmall")
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .foregroundColor(.gray)
                }
            }
        }
        .padding(40)
        .background(Color(hex: "#030306"))
    }
}

#Preview("Single Icon") {
    AppIconGenerator(size: 512)
        .background(Color(hex: "#030306"))
}

#Preview("Size Comparison") {
    AppIconSizePreview()
}

#Preview("On Dark Background") {
    ZStack {
        Color.black
        AppIconGenerator(size: 256)
    }
}

#Preview("On Light Background") {
    ZStack {
        Color(white: 0.95)
        AppIconGenerator(size: 256)
    }
}
