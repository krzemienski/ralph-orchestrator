import SwiftUI

/// Terminal-style view that displays real-time SSH setup progress.
///
/// Shows streaming command output line-by-line as commands execute
/// on the remote host, with step indicators at the top and action
/// buttons at the bottom. Auto-scrolls to follow new output.
struct SetupProgressView: View {
    @StateObject private var viewModel = SetupProgressViewModel()

    let credentials: SSHCredentials
    let onConnected: (String) -> Void
    let onCancel: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            stepIndicatorBar
            progressBar
            terminalView
            statusBar
        }
        .background(CyberpunkTheme.bgPrimary)
        .task {
            await viewModel.startSetup(credentials: credentials)
        }
        .onChange(of: viewModel.isComplete) { _, complete in
            if complete, let url = viewModel.tunnelURL {
                onConnected(url)
            }
        }
    }

    // MARK: - Step Indicator Bar

    private var stepIndicatorBar: some View {
        VStack(spacing: 8) {
            HStack(spacing: 6) {
                ForEach(SetupStep.allCases, id: \.rawValue) { step in
                    VStack(spacing: 4) {
                        Circle()
                            .fill(stepColor(for: step))
                            .frame(width: 10, height: 10)
                            .overlay {
                                if viewModel.currentStep == step && viewModel.isRunning {
                                    Circle()
                                        .stroke(stepColor(for: step), lineWidth: 2)
                                        .frame(width: 16, height: 16)
                                        .opacity(0.6)
                                }
                            }

                        Text("\(step.rawValue)")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundColor(stepLabelColor(for: step))
                    }
                }
            }

            if let step = viewModel.currentStep {
                Text(step.title)
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentCyan)
                    .lineLimit(1)
            } else if viewModel.isConnecting {
                Text("Establishing SSH connection...")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentYellow)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 12)
        .background(CyberpunkTheme.bgSecondary)
    }

    // MARK: - Progress Bar

    private var progressBar: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Rectangle()
                    .fill(CyberpunkTheme.border)

                Rectangle()
                    .fill(progressBarColor)
                    .frame(width: geo.size.width * viewModel.progress)
                    .animation(.easeInOut(duration: 0.3), value: viewModel.progress)
            }
        }
        .frame(height: 3)
    }

    // MARK: - Terminal View

    private var terminalView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 1) {
                    ForEach(viewModel.logLines) { entry in
                        logLineView(entry)
                            .id(entry.id)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
            }
            .onChange(of: viewModel.logLines.count) { _, _ in
                // Auto-scroll to the latest line
                if let last = viewModel.logLines.last {
                    withAnimation(.easeOut(duration: 0.05)) {
                        proxy.scrollTo(last.id, anchor: .bottom)
                    }
                }
            }
        }
        .background(Color.black)
        .frame(maxHeight: .infinity)
    }

    private func logLineView(_ entry: LogEntry) -> some View {
        HStack(alignment: .top, spacing: 0) {
            // Step header lines get special formatting
            if entry.text.hasPrefix("---") {
                Text(entry.text)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentCyan)
                    .fontWeight(.bold)
            } else if entry.text.hasPrefix("ERROR") || entry.text.hasPrefix("WARN") {
                Text(entry.text)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(entry.text.hasPrefix("ERROR") ? CyberpunkTheme.accentRed : CyberpunkTheme.accentYellow)
            } else if entry.text.hasPrefix("Setup complete") {
                Text(entry.text)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentGreen)
                    .fontWeight(.bold)
            } else if entry.text.isEmpty {
                // Blank spacer line
                Text(" ")
                    .font(.system(.caption, design: .monospaced))
            } else {
                Text(entry.text)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(colorForChannel(entry.channel))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Status Bar

    private var statusBar: some View {
        VStack(spacing: 12) {
            Divider()
                .overlay(CyberpunkTheme.border)

            // Auth required state — show message + retry
            if viewModel.authRequired {
                authRequiredSection
            }
            // Error state — show error + retry/cancel
            else if viewModel.error != nil {
                errorSection
            }
            // Running state — show cancel button
            else if viewModel.isRunning || viewModel.isConnecting {
                runningSection
            }
            // Complete state — show success (auto-transitions via onChange)
            else if viewModel.isComplete {
                completeSection
            }
        }
        .padding(.horizontal)
        .padding(.bottom, 16)
        .background(CyberpunkTheme.bgSecondary)
    }

    private var authRequiredSection: some View {
        VStack(spacing: 12) {
            Text(viewModel.authMessage)
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(CyberpunkTheme.accentYellow)
                .multilineTextAlignment(.leading)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(CyberpunkTheme.bgCard)
                .cornerRadius(8)

            HStack(spacing: 16) {
                Button("Cancel") {
                    viewModel.cancel()
                    onCancel()
                }
                .buttonStyle(CyberpunkSecondaryButtonStyle())

                Button("Retry") {
                    Task { await viewModel.retry() }
                }
                .buttonStyle(CyberpunkButtonStyle())
            }
        }
    }

    private var errorSection: some View {
        VStack(spacing: 12) {
            if let error = viewModel.error {
                Text(error.localizedDescription ?? "Setup failed")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentRed)
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .lineLimit(4)
            }

            HStack(spacing: 16) {
                Button("Back") {
                    onCancel()
                }
                .buttonStyle(CyberpunkSecondaryButtonStyle())

                Button("Retry") {
                    Task { await viewModel.retry() }
                }
                .buttonStyle(CyberpunkButtonStyle())
            }
        }
    }

    private var runningSection: some View {
        HStack {
            ProgressView()
                .tint(CyberpunkTheme.accentCyan)

            Text(viewModel.statusText)
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textSecondary)
                .lineLimit(1)

            Spacer()

            Button("Cancel") {
                viewModel.cancel()
                onCancel()
            }
            .buttonStyle(CyberpunkSecondaryButtonStyle())
        }
    }

    private var completeSection: some View {
        HStack {
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(CyberpunkTheme.accentGreen)

            Text("Connected to \(viewModel.tunnelURL ?? "server")")
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(CyberpunkTheme.accentGreen)
                .lineLimit(1)
        }
    }

    // MARK: - Color Helpers

    private func stepColor(for step: SetupStep) -> Color {
        if viewModel.completedSteps.contains(step) {
            return CyberpunkTheme.accentGreen
        }
        if viewModel.currentStep == step {
            if viewModel.error != nil { return CyberpunkTheme.accentRed }
            return CyberpunkTheme.accentCyan
        }
        return CyberpunkTheme.border
    }

    private func stepLabelColor(for step: SetupStep) -> Color {
        if viewModel.completedSteps.contains(step) {
            return CyberpunkTheme.accentGreen
        }
        if viewModel.currentStep == step {
            return CyberpunkTheme.textPrimary
        }
        return CyberpunkTheme.textMuted
    }

    private func colorForChannel(_ channel: OutputChannel) -> Color {
        switch channel {
        case .stdout: return CyberpunkTheme.accentGreen.opacity(0.85)
        case .stderr: return CyberpunkTheme.accentYellow.opacity(0.85)
        }
    }

    private var progressBarColor: Color {
        if viewModel.error != nil { return CyberpunkTheme.accentRed }
        if viewModel.isComplete { return CyberpunkTheme.accentGreen }
        return CyberpunkTheme.accentCyan
    }
}

// MARK: - Button Styles

/// Neon-bordered primary button for the cyberpunk theme.
private struct CyberpunkButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(.subheadline, design: .monospaced))
            .fontWeight(.semibold)
            .foregroundColor(.black)
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(CyberpunkTheme.accentCyan)
            .cornerRadius(6)
            .opacity(configuration.isPressed ? 0.7 : 1.0)
    }
}

/// Subtle secondary button for the cyberpunk theme.
private struct CyberpunkSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(.subheadline, design: .monospaced))
            .foregroundColor(CyberpunkTheme.textSecondary)
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(CyberpunkTheme.bgCard)
            .cornerRadius(6)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(CyberpunkTheme.border, lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.7 : 1.0)
    }
}
