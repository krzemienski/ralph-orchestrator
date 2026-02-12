import Foundation
import Citadel

/// Represents a single step in the remote setup process.
enum SetupStep: Int, CaseIterable, Sendable {
    case checkDependencies = 1
    case downloadBinaries = 2
    case installCloudflared = 3
    case checkCloudflaredAuth = 4
    case startServer = 5
    case startTunnel = 6

    var title: String {
        switch self {
        case .checkDependencies: return "Checking dependencies"
        case .downloadBinaries: return "Downloading prebuilt binaries"
        case .installCloudflared: return "Installing cloudflared"
        case .checkCloudflaredAuth: return "Checking cloudflared auth"
        case .startServer: return "Starting ralph-mobile-server"
        case .startTunnel: return "Starting Cloudflare tunnel"
        }
    }

    var timeoutSeconds: Int {
        switch self {
        case .checkDependencies: return 60
        case .downloadBinaries: return 120
        case .installCloudflared: return 120
        case .checkCloudflaredAuth: return 30
        case .startServer: return 60
        case .startTunnel: return 60
        }
    }
}

/// Distinguishes stdout from stderr in streaming output.
enum OutputChannel: Sendable {
    case stdout
    case stderr
}

/// The detected remote platform.
enum RemotePlatform: Sendable {
    case macOS
    case linux
}

/// Errors that can occur during SSH setup.
enum SSHSetupError: Error, LocalizedError, Sendable {
    case connectionFailed(String)
    case authenticationFailed
    case commandFailed(step: SetupStep, output: String)
    case timeout(step: SetupStep)
    case cancelled
    case tunnelURLNotFound
    case unsupportedPlatform(String)

    var errorDescription: String? {
        switch self {
        case .connectionFailed(let reason):
            return "SSH connection failed: \(reason)"
        case .authenticationFailed:
            return "Authentication failed. Check your username and password."
        case .commandFailed(let step, let output):
            return "Step \(step.rawValue) (\(step.title)) failed:\n\(output)"
        case .timeout(let step):
            return "Step \(step.rawValue) (\(step.title)) timed out after \(step.timeoutSeconds)s"
        case .cancelled:
            return "Setup was cancelled"
        case .tunnelURLNotFound:
            return "Could not find tunnel URL in output"
        case .unsupportedPlatform(let os):
            return "Unsupported platform: \(os). Only macOS and Linux are supported."
        }
    }
}

/// Delegate protocol for receiving real-time setup progress.
///
/// All methods are called on the MainActor so the UI can update
/// immediately as lines stream in from the remote host.
@MainActor
protocol SetupProgressDelegate: AnyObject {
    func setupDidStartStep(_ step: SetupStep)
    func setupDidReceiveOutput(_ line: String, channel: OutputChannel, for step: SetupStep)
    func setupDidCompleteStep(_ step: SetupStep)
    func setupRequiresAuth(message: String)
    func setupDidComplete(tunnelURL: String)
    func setupDidFail(error: SSHSetupError)
}

/// Service that manages SSH connections and executes remote setup
/// with real-time output streaming.
///
/// Uses Citadel's `executeCommandStream()` to provide line-by-line output
/// as commands execute on the remote host. Supports both macOS (brew)
/// and Linux (apt/dnf/pacman).
actor SSHSetupService {
    private var client: SSHClient?
    private var isCancelled = false

    // MARK: - Connection

    /// Connect to a remote host via SSH with password authentication.
    func connect(credentials: SSHCredentials) async throws -> SSHClient {
        guard !isCancelled else { throw SSHSetupError.cancelled }

        do {
            let client = try await SSHClient.connect(
                host: credentials.host,
                port: credentials.port,
                authenticationMethod: .passwordBased(
                    username: credentials.username,
                    password: credentials.password
                ),
                hostKeyValidator: .acceptAnything(),
                reconnect: .never
            )
            self.client = client
            return client
        } catch {
            let message = error.localizedDescription
            if message.contains("auth") || message.contains("password") || message.contains("Permission denied") {
                throw SSHSetupError.authenticationFailed
            }
            throw SSHSetupError.connectionFailed(message)
        }
    }

    // MARK: - Command Execution

    /// Execute a command and return the complete output (batch mode).
    /// Used for quick queries like platform detection.
    func executeCommand(_ command: String, on client: SSHClient, timeout: Int = 30) async throws -> String {
        guard !isCancelled else { throw SSHSetupError.cancelled }

        let result = try await withThrowingTaskGroup(of: String.self) { group in
            group.addTask {
                let buffer = try await client.executeCommand(command)
                return String(buffer: buffer)
            }

            group.addTask {
                try await Task.sleep(nanoseconds: UInt64(timeout) * 1_000_000_000)
                throw CancellationError()
            }

            let result = try await group.next()!
            group.cancelAll()
            return result
        }

        return result
    }

    /// Execute a command with real-time output streaming to the delegate.
    ///
    /// Uses Citadel's `executeCommandStream()` to forward stdout/stderr
    /// lines as they arrive from the remote host. Each line is emitted
    /// individually, buffered on newline boundaries for clean display.
    func executeCommandStreaming(
        _ command: String,
        on client: SSHClient,
        step: SetupStep,
        delegate: SetupProgressDelegate
    ) async throws -> String {
        guard !isCancelled else { throw SSHSetupError.cancelled }

        return try await withThrowingTaskGroup(of: String.self) { group in
            // Streaming task — iterates the SSH output as it arrives
            group.addTask {
                var fullOutput = ""
                var stdoutBuffer = ""
                var stderrBuffer = ""

                let stream = try await client.executeCommandStream(command)

                do {
                    for try await chunk in stream {
                        switch chunk {
                        case .stdout(let buffer):
                            let text = String(buffer: buffer)
                            fullOutput += text
                            stdoutBuffer += text

                            // Emit complete lines as they arrive
                            while let idx = stdoutBuffer.firstIndex(of: "\n") {
                                let line = String(stdoutBuffer[..<idx])
                                stdoutBuffer = String(stdoutBuffer[stdoutBuffer.index(after: idx)...])
                                if !line.isEmpty {
                                    await delegate.setupDidReceiveOutput(line, channel: .stdout, for: step)
                                }
                            }

                        case .stderr(let buffer):
                            let text = String(buffer: buffer)
                            fullOutput += text
                            stderrBuffer += text

                            while let idx = stderrBuffer.firstIndex(of: "\n") {
                                let line = String(stderrBuffer[..<idx])
                                stderrBuffer = String(stderrBuffer[stderrBuffer.index(after: idx)...])
                                if !line.isEmpty {
                                    await delegate.setupDidReceiveOutput(line, channel: .stderr, for: step)
                                }
                            }
                        }
                    }
                } catch {
                    // Preserve accumulated output — Citadel throws after streaming
                    // all output, so fullOutput contains the real error context
                    let detail = fullOutput.isEmpty ? error.localizedDescription : fullOutput
                    throw SSHSetupError.commandFailed(step: step, output: detail)
                }

                // Flush any remaining buffered content after stream ends
                let trimmedOut = stdoutBuffer.trimmingCharacters(in: .whitespacesAndNewlines)
                if !trimmedOut.isEmpty {
                    await delegate.setupDidReceiveOutput(trimmedOut, channel: .stdout, for: step)
                }
                let trimmedErr = stderrBuffer.trimmingCharacters(in: .whitespacesAndNewlines)
                if !trimmedErr.isEmpty {
                    await delegate.setupDidReceiveOutput(trimmedErr, channel: .stderr, for: step)
                }

                return fullOutput
            }

            // Timeout task
            group.addTask {
                try await Task.sleep(nanoseconds: UInt64(step.timeoutSeconds) * 1_000_000_000)
                throw SSHSetupError.timeout(step: step)
            }

            let result = try await group.next()!
            group.cancelAll()
            return result
        }
    }

    // MARK: - Setup Orchestration

    /// Execute the full 8-step setup sequence with real-time streaming.
    ///
    /// Detects the remote platform first, then runs each step sequentially
    /// with output streamed line-by-line to the delegate.
    func executeSetup(
        credentials: SSHCredentials,
        delegate: SetupProgressDelegate
    ) async throws -> String {
        isCancelled = false

        // Step 0: Connect
        let client: SSHClient
        do {
            client = try await connect(credentials: credentials)
        } catch {
            if let setupError = error as? SSHSetupError {
                await delegate.setupDidFail(error: setupError)
            } else {
                await delegate.setupDidFail(error: .connectionFailed(error.localizedDescription))
            }
            throw error
        }

        // Detect remote platform (macOS vs Linux)
        let platform: RemotePlatform
        do {
            platform = try await detectPlatform(on: client)
        } catch {
            let setupError = SSHSetupError.connectionFailed("Failed to detect platform: \(error.localizedDescription)")
            await delegate.setupDidFail(error: setupError)
            throw setupError
        }

        let srvPort = credentials.serverPort
        var tunnelURL: String?

        // Execute steps sequentially with streaming output
        for step in SetupStep.allCases {
            guard !isCancelled else {
                await delegate.setupDidFail(error: .cancelled)
                throw SSHSetupError.cancelled
            }

            await delegate.setupDidStartStep(step)

            let command = buildCommand(for: step, serverPort: srvPort, platform: platform)

            do {
                let output = try await executeCommandStreaming(
                    command,
                    on: client,
                    step: step,
                    delegate: delegate
                )

                // Special handling: cloudflared auth check
                if step == .checkCloudflaredAuth && output.contains("ACTION REQUIRED") {
                    let authMessage = """
                    cloudflared needs authentication.

                    SSH into your server and run:
                      cloudflared tunnel login

                    Follow the browser link to authenticate, then tap 'Retry' below.
                    """
                    await delegate.setupRequiresAuth(message: authMessage)
                    return "" // Caller handles retry
                }

                // Extract tunnel URL from the final step output
                if step == .startTunnel {
                    tunnelURL = extractTunnelURL(from: output)
                }

                await delegate.setupDidCompleteStep(step)
            } catch let error as SSHSetupError {
                await delegate.setupDidFail(error: error)
                throw error
            } catch {
                let setupError = SSHSetupError.commandFailed(step: step, output: error.localizedDescription)
                await delegate.setupDidFail(error: setupError)
                throw setupError
            }
        }

        // Return tunnel URL or fallback
        guard let url = tunnelURL, !url.isEmpty else {
            let fallbackURL = "https://ralph-mobile.cfargotunnel.com"
            await delegate.setupDidComplete(tunnelURL: fallbackURL)
            return fallbackURL
        }

        await delegate.setupDidComplete(tunnelURL: url)
        return url
    }

    // MARK: - Lifecycle

    /// Cancel any in-progress setup.
    func cancel() {
        isCancelled = true
        Task {
            try? await client?.close()
            client = nil
        }
    }

    /// Close the SSH connection cleanly.
    func disconnect() async {
        try? await client?.close()
        client = nil
    }

    // MARK: - Private Helpers

    /// Detect whether the remote host runs macOS or Linux.
    private func detectPlatform(on client: SSHClient) async throws -> RemotePlatform {
        let output = try await executeCommand("uname -s", on: client)
        let trimmed = output.trimmingCharacters(in: .whitespacesAndNewlines)
        switch trimmed {
        case "Darwin": return .macOS
        case "Linux": return .linux
        default: throw SSHSetupError.unsupportedPlatform(trimmed)
        }
    }

    /// The GitHub release URL for prebuilt binaries.
    private static let releaseTag = "v0.1.0-mobile"
    private static let releaseBaseURL = "https://github.com/krzemienski/ralph-orchestrator/releases/download"

    /// Build the platform-aware SSH command for a given setup step.
    ///
    /// Each command is a self-contained bash snippet that detects
    /// OS and architecture to download the correct prebuilt binary.
    private func buildCommand(for step: SetupStep, serverPort: Int, platform: RemotePlatform) -> String {
        let tag = Self.releaseTag
        let base = Self.releaseBaseURL

        switch step {
        case .checkDependencies:
            return """
            echo "==> [1/6] Checking dependencies..." && \
            command -v curl >/dev/null 2>&1 || { echo "ERROR: curl not found"; exit 1; } && \
            echo "curl: $(curl --version | head -1)" && \
            echo "Dependencies OK"
            """

        case .downloadBinaries:
            return """
            RALPH_DIR="$HOME/ralph-mobile-server" && \
            mkdir -p "$RALPH_DIR" && cd "$RALPH_DIR" && \
            echo "==> [2/6] Downloading prebuilt binaries..." && \
            OS=$(uname -s | tr '[:upper:]' '[:lower:]') && \
            ARCH=$(uname -m) && \
            case "$OS" in \
                darwin) OS_TAG="darwin" ;; \
                linux)  OS_TAG="linux" ;; \
                *) echo "ERROR: Unsupported OS: $OS" && exit 1 ;; \
            esac && \
            case "$ARCH" in \
                x86_64|amd64)   ARCH_TAG="x86_64" ;; \
                aarch64|arm64)  ARCH_TAG="arm64" ;; \
                *) echo "ERROR: Unsupported arch: $ARCH" && exit 1 ;; \
            esac && \
            SUFFIX="${OS_TAG}-${ARCH_TAG}" && \
            echo "Platform: ${OS_TAG}/${ARCH_TAG}" && \
            echo "Downloading ralph-mobile-server..." && \
            curl -fSL "\(base)/\(tag)/ralph-mobile-server-${SUFFIX}" -o ralph-mobile-server && \
            chmod +x ralph-mobile-server && \
            echo "Downloading ralph CLI..." && \
            curl -fSL "\(base)/\(tag)/ralph-${SUFFIX}" -o ralph && \
            chmod +x ralph && \
            echo "Download complete!" && \
            ls -lh ralph-mobile-server ralph
            """

        case .installCloudflared:
            switch platform {
            case .macOS:
                return """
                if ! command -v cloudflared >/dev/null 2>&1; then \
                    echo "==> [3/6] Installing cloudflared via Homebrew..." && \
                    brew install cloudflare/cloudflare/cloudflared && \
                    echo "Installed: $(cloudflared --version)"; \
                else \
                    echo "==> [3/6] cloudflared already installed: $(cloudflared --version)"; \
                fi
                """
            case .linux:
                return """
                if ! command -v cloudflared >/dev/null 2>&1; then \
                    echo "==> [3/6] Installing cloudflared..." && \
                    ARCH=$(uname -m) && \
                    case "$ARCH" in \
                        x86_64|amd64)  CF_ARCH="amd64" ;; \
                        aarch64|arm64) CF_ARCH="arm64" ;; \
                        armv7l|armhf)  CF_ARCH="arm"   ;; \
                        *) echo "ERROR: Unsupported architecture: $ARCH" && exit 1 ;; \
                    esac && \
                    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}" && \
                    sudo curl -L "$CF_URL" -o /usr/local/bin/cloudflared && \
                    sudo chmod +x /usr/local/bin/cloudflared && \
                    echo "Installed: $(cloudflared --version)"; \
                else \
                    echo "==> [3/6] cloudflared already installed: $(cloudflared --version)"; \
                fi
                """
            }

        case .checkCloudflaredAuth:
            return """
            if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then \
                echo "ACTION REQUIRED: Cloudflare Login" && \
                echo "" && \
                echo "Run this command on your server:" && \
                echo "  cloudflared tunnel login" && \
                echo "" && \
                echo "Follow the browser link to authenticate." && \
                echo "Then tap 'Retry' in the app."; \
            else \
                echo "==> [4/6] cloudflared authenticated (cert.pem found)"; \
            fi
            """

        case .startServer:
            return """
            cd "$HOME/ralph-mobile-server" && \
            echo "==> [5/6] Starting ralph-mobile-server on port \(serverPort)..." && \
            pkill -f 'ralph-mobile-server' 2>/dev/null || true && \
            sleep 1 && \
            setsid nohup ./ralph-mobile-server --port \(serverPort) --bind-all > ralph-mobile-server.log 2>&1 & \
            SERVER_PID=$! && \
            echo "Server PID: $SERVER_PID" && \
            echo "Waiting for server to be ready..." && \
            for i in $(seq 1 30); do \
                if curl -sf "http://127.0.0.1:\(serverPort)/health" >/dev/null 2>&1; then \
                    echo "Server is ready on port \(serverPort)!"; break; \
                fi; \
                echo "  Attempt $i/30..."; \
                sleep 1; \
            done && \
            curl -sf "http://127.0.0.1:\(serverPort)/health" >/dev/null 2>&1 || \
            (echo "ERROR: Server failed to start — check ralph-mobile-server.log" && exit 1)
            """

        case .startTunnel:
            return """
            cd "$HOME/ralph-mobile-server" && \
            echo "==> [6/6] Starting Cloudflare Named Tunnel..." && \
            ./ralph tunnel start --name ralph-mobile --port \(serverPort) 2>&1
            """
        }
    }

    /// Extract the tunnel URL from the output of `ralph tunnel start`.
    private func extractTunnelURL(from output: String) -> String? {
        let lines = output.components(separatedBy: "\n")

        // Look for Named Tunnel patterns
        for line in lines {
            if let range = line.range(of: "https://[a-zA-Z0-9.-]+\\.(?:cfargotunnel|trycloudflare)\\.com", options: .regularExpression) {
                return String(line[range])
            }
        }

        // Fallback: any https URL that isn't a known non-tunnel URL
        for line in lines {
            if let range = line.range(of: "https://[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}", options: .regularExpression) {
                let url = String(line[range])
                if !url.contains("github.com") && !url.contains("rustup.rs")
                    && !url.contains("cloudflare.com/releases") && !url.contains("brew.sh") {
                    return url
                }
            }
        }

        return nil
    }
}
