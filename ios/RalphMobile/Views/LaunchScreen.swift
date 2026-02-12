import SwiftUI

/// Launch screen following Liquid Glass design principles with cyberpunk theming
struct LaunchScreen: View {
    @State private var isAnimating = false
    @State private var glowIntensity: Double = 0.3
    
    var body: some View {
        ZStack {
            // Deep background
            CyberpunkTheme.bgPrimary
                .ignoresSafeArea()
            
            // Scanline overlay for cyberpunk effect
            ScanlineOverlay()
                .opacity(0.05)
            
            VStack(spacing: 40) {
                // Main icon representation
                ZStack {
                    // Outer glow ring - Liquid Glass inspired
                    Circle()
                        .stroke(
                            LinearGradient(
                                colors: [
                                    CyberpunkTheme.accentCyan.opacity(0.6),
                                    CyberpunkTheme.accentMagenta.opacity(0.4),
                                    CyberpunkTheme.accentCyan.opacity(0.6)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 3
                        )
                        .frame(width: 160, height: 160)
                        .blur(radius: 2)
                        .opacity(isAnimating ? 1.0 : 0.3)
                    
                    // Middle glass layer
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [
                                    CyberpunkTheme.bgElevated.opacity(0.9),
                                    CyberpunkTheme.bgPrimary.opacity(0.95)
                                ],
                                center: .center,
                                startRadius: 40,
                                endRadius: 80
                            )
                        )
                        .frame(width: 140, height: 140)
                        .overlay(
                            Circle()
                                .stroke(
                                    CyberpunkTheme.accentCyan.opacity(0.3),
                                    lineWidth: 1
                                )
                        )
                    
                    // Ralph "R" symbol with neon effect
                    VStack(spacing: 4) {
                        Text("R")
                            .font(.system(size: 72, weight: .bold, design: .rounded))
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
                            .shadow(color: CyberpunkTheme.accentCyan.opacity(glowIntensity), radius: 20)
                            .shadow(color: CyberpunkTheme.accentMagenta.opacity(glowIntensity), radius: 30)
                        
                        // Subtitle indicator
                        HStack(spacing: 2) {
                            ForEach(0..<3) { index in
                                Capsule()
                                    .fill(CyberpunkTheme.accentCyan)
                                    .frame(width: 6, height: 2)
                                    .opacity(isAnimating ? 1.0 : 0.3)
                                    .animation(
                                        .easeInOut(duration: 0.8)
                                        .repeatForever()
                                        .delay(Double(index) * 0.2),
                                        value: isAnimating
                                    )
                            }
                        }
                    }
                }
                .scaleEffect(isAnimating ? 1.0 : 0.9)
                
                // App name with liquid glass effect
                VStack(spacing: 8) {
                    Text("RALPH")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(CyberpunkTheme.textPrimary)
                        .tracking(8)
                        .shadow(color: CyberpunkTheme.accentCyan.opacity(0.5), radius: 10)
                    
                    Text("MOBILE")
                        .font(.system(size: 12, weight: .medium, design: .rounded))
                        .foregroundColor(CyberpunkTheme.textSecondary)
                        .tracking(4)
                }
                .opacity(isAnimating ? 1.0 : 0.0)
            }
            
            // Bottom accent line
            VStack {
                Spacer()
                
                HStack(spacing: 4) {
                    ForEach(0..<5) { index in
                        Capsule()
                            .fill(
                                LinearGradient(
                                    colors: [
                                        CyberpunkTheme.accentCyan.opacity(0.6),
                                        CyberpunkTheme.accentMagenta.opacity(0.6)
                                    ],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: 40, height: 3)
                            .opacity(isAnimating ? 1.0 : 0.0)
                            .animation(
                                .easeInOut(duration: 0.6)
                                .delay(Double(index) * 0.1),
                                value: isAnimating
                            )
                    }
                }
                .padding(.bottom, 60)
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.2)) {
                isAnimating = true
            }
            
            // Pulsing glow effect
            withAnimation(
                .easeInOut(duration: 2.0)
                .repeatForever(autoreverses: true)
            ) {
                glowIntensity = 0.8
            }
        }
    }
}

#Preview {
    LaunchScreen()
}
