import SwiftUI

/// Remote backend setup view with two paths:
/// 1. **Automated SSH** (primary): Connects via SSH and runs setup remotely
///    with real-time streaming output in a terminal-style view.
/// 2. **Manual script** (secondary): Generates a bash script for the user
///    to copy and run on their server themselves.
struct SetupScriptView: View {
    let onConnected: (String) -> Void
    let onBack: () -> Void

    // MARK: - Form State

    @State private var hostname: String = ""
    @State private var username: String = "root"
    @State private var password: String = ""
    @State private var sshPort: String = "22"
    @State private var serverPort: String = "8080"

    // MARK: - View State

    @State private var showProgress = false
    @State private var showScript = false
    @State private var copied = false
    @State private var serverURL: String = ""
    @State private var isChecking = false
    @State private var errorMessage: String?

    // MARK: - Computed

    private var credentials: SSHCredentials {
        SSHCredentials(
            host: hostname.trimmingCharacters(in: .whitespaces),
            port: Int(sshPort) ?? 22,
            username: username.trimmingCharacters(in: .whitespaces),
            password: password,
            serverPort: Int(serverPort) ?? 8080
        )
    }

    private var formIsValid: Bool {
        !hostname.trimmingCharacters(in: .whitespaces).isEmpty
            && !username.trimmingCharacters(in: .whitespaces).isEmpty
    }

    private var sshFormIsValid: Bool {
        formIsValid && !password.isEmpty
    }

    // MARK: - Body

    var body: some View {
        if showProgress {
            SetupProgressView(
                credentials: credentials,
                onConnected: onConnected,
                onCancel: { showProgress = false }
            )
        } else {
            mainView
        }
    }

    private var mainView: some View {
        VStack(spacing: 0) {
            // Back button
            HStack {
                Button {
                    if showScript {
                        showScript = false
                    } else {
                        onBack()
                    }
                } label: {
                    HStack(spacing: 6) {
                        Image(systemName: "chevron.left")
                        Text("BACK")
                            .font(.system(.caption, design: .monospaced).bold())
                    }
                    .foregroundColor(CyberpunkTheme.textSecondary)
                }
                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.top, 8)

            ScrollView {
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 12) {
                        Image(systemName: "terminal")
                            .font(.largeTitle)
                            .foregroundColor(CyberpunkTheme.accentCyan)
                            .glow(CyberpunkTheme.accentCyan, radius: 12, opacity: 0.5)

                        Text("SET UP BACKEND")
                            .font(.system(.title2, design: .monospaced).bold())
                            .foregroundColor(CyberpunkTheme.textPrimary)
                            .kerning(2)

                        Text(showScript ? "Copy and run this script on your server" : "Enter your server details")
                            .font(.system(.caption, design: .monospaced))
                            .foregroundColor(CyberpunkTheme.textSecondary)
                    }
                    .padding(.top, 16)

                    if showScript {
                        scriptView
                    } else {
                        detailsForm
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 32)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(CyberpunkTheme.bgPrimary)
        .onAppear(perform: loadSavedCredentials)
    }

    // MARK: - Credential Form

    private var detailsForm: some View {
        VStack(spacing: 16) {
            formField(label: "HOSTNAME / IP", placeholder: "192.168.1.100 or home.example.com", text: $hostname, keyboardType: .URL)
            formField(label: "SSH USERNAME", placeholder: "root", text: $username)
            secureFormField(label: "SSH PASSWORD", placeholder: "Required for automated setup", text: $password)

            HStack(spacing: 12) {
                formField(label: "SSH PORT", placeholder: "22", text: $sshPort, keyboardType: .numberPad)
                formField(label: "SERVER PORT", placeholder: "8080", text: $serverPort, keyboardType: .numberPad)
            }

            // Primary action: Automated SSH setup
            Button {
                showProgress = true
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "bolt.fill")
                    Text("SET UP & CONNECT")
                }
                .font(.system(.body, design: .monospaced).bold())
                .frame(maxWidth: .infinity)
                .padding()
                .background(sshFormIsValid ? CyberpunkTheme.accentCyan : CyberpunkTheme.textMuted)
                .foregroundColor(CyberpunkTheme.bgPrimary)
                .cornerRadius(8)
            }
            .disabled(!sshFormIsValid)

            // Divider with "or"
            HStack {
                Rectangle()
                    .fill(CyberpunkTheme.border)
                    .frame(height: 1)
                Text("OR")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textMuted)
                Rectangle()
                    .fill(CyberpunkTheme.border)
                    .frame(height: 1)
            }

            // Secondary action: Generate script (manual path)
            Button {
                showScript = true
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "doc.text")
                    Text("GENERATE SCRIPT")
                }
                .font(.system(.caption, design: .monospaced).bold())
                .frame(maxWidth: .infinity)
                .padding(12)
                .background(CyberpunkTheme.bgTertiary)
                .foregroundColor(formIsValid ? CyberpunkTheme.textSecondary : CyberpunkTheme.textMuted)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(CyberpunkTheme.border, lineWidth: 1)
                )
            }
            .disabled(!formIsValid)

            // Hint text
            Text("Automated setup connects via SSH and installs everything for you. Generate Script creates a bash script you can run manually.")
                .font(.system(.caption2, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textMuted)
                .multilineTextAlignment(.center)
        }
        .padding(24)
        .background(CyberpunkTheme.bgCard)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(CyberpunkTheme.border, lineWidth: 1)
        )
    }

    // MARK: - Script View (Manual Path)

    private var scriptView: some View {
        VStack(spacing: 16) {
            // Script display
            ScrollView(.horizontal, showsIndicators: false) {
                Text(generatedScript)
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentGreen)
                    .padding(16)
            }
            .frame(maxHeight: 200)
            .background(Color.black)
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(CyberpunkTheme.border, lineWidth: 1)
            )

            // Copy button
            Button {
                UIPasteboard.general.string = generatedScript
                copied = true
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    copied = false
                }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: copied ? "checkmark" : "doc.on.doc")
                    Text(copied ? "COPIED!" : "COPY TO CLIPBOARD")
                }
                .font(.system(.body, design: .monospaced).bold())
                .frame(maxWidth: .infinity)
                .padding()
                .background(copied ? CyberpunkTheme.accentGreen : CyberpunkTheme.accentCyan)
                .foregroundColor(CyberpunkTheme.bgPrimary)
                .cornerRadius(8)
            }

            // SSH command hint
            VStack(alignment: .leading, spacing: 8) {
                HStack(spacing: 8) {
                    Image(systemName: "info.circle")
                        .foregroundColor(CyberpunkTheme.accentCyan)
                    Text("HOW TO RUN")
                        .font(.system(.caption2, design: .monospaced).bold())
                        .foregroundColor(CyberpunkTheme.textSecondary)
                }

                let port = sshPort.isEmpty ? "22" : sshPort
                Text("ssh -p \(port) \(username)@\(hostname) 'bash -s' < script.sh")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.accentGreen)
                    .padding(8)
                    .background(Color.black)
                    .cornerRadius(4)

                Text("Or paste the script directly into your SSH session.")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textMuted)

                Text("Note: The script may need to run twice — first to install cloudflared and authenticate, second to start all services.")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textSecondary)
                    .padding(.top, 4)
            }
            .padding(12)
            .background(CyberpunkTheme.bgTertiary)
            .cornerRadius(8)

            Divider()
                .background(CyberpunkTheme.border)

            // After running the script, test connection
            VStack(spacing: 12) {
                Text("Enter the tunnel URL printed by the script:")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textSecondary)
                    .multilineTextAlignment(.center)

                let defaultURL = "https://ralph-mobile.cfargotunnel.com"

                TextField(defaultURL, text: $serverURL)
                    .font(.system(.body, design: .monospaced))
                    .foregroundColor(CyberpunkTheme.textPrimary)
                    .padding()
                    .background(CyberpunkTheme.bgTertiary)
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(CyberpunkTheme.border, lineWidth: 1)
                    )
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
                    .onAppear {
                        if serverURL.isEmpty {
                            serverURL = defaultURL
                        }
                    }

                if let error = errorMessage {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(CyberpunkTheme.accentRed)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(CyberpunkTheme.accentRed)
                    }
                }

                Button {
                    Task { await testConnection() }
                } label: {
                    HStack(spacing: 8) {
                        if isChecking {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: CyberpunkTheme.bgPrimary))
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "link")
                        }
                        Text(isChecking ? "TESTING..." : "TEST CONNECTION")
                    }
                    .font(.system(.body, design: .monospaced).bold())
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isChecking ? CyberpunkTheme.textMuted : CyberpunkTheme.accentCyan)
                    .foregroundColor(CyberpunkTheme.bgPrimary)
                    .cornerRadius(8)
                }
                .disabled(isChecking || serverURL.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
        .padding(24)
        .background(CyberpunkTheme.bgCard)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(CyberpunkTheme.border, lineWidth: 1)
        )
    }

    // MARK: - Generated Script (Manual Path)

    private var generatedScript: String {
        let port = sshPort.isEmpty ? "22" : sshPort
        let srvPort = serverPort.isEmpty ? "8080" : serverPort
        let releaseTag = "v0.1.0-mobile"
        let releaseBase = "https://github.com/krzemienski/ralph-orchestrator/releases/download"
        return """
        #!/bin/bash
        set -euo pipefail

        # Ralph Mobile — Remote Backend Setup Script
        # Generated by Ralph Mobile
        # Target: \(username)@\(hostname):\(port)
        # Server Port: \(srvPort)

        echo "=========================================="
        echo "  Ralph Mobile — Remote Backend Setup"
        echo "=========================================="
        echo ""

        OS=$(uname -s)
        ARCH=$(uname -m)
        RALPH_DIR="$HOME/ralph-mobile-server"

        # ── Step 1: Check dependencies ──
        echo "==> [1/6] Checking dependencies..."
        command -v curl >/dev/null 2>&1 || { echo "ERROR: curl not found. Install curl first."; exit 1; }
        echo "    curl: $(curl --version | head -1)"

        # ── Step 2: Download prebuilt binaries ──
        echo "==> [2/6] Downloading prebuilt binaries..."
        mkdir -p "$RALPH_DIR" && cd "$RALPH_DIR"

        # Detect OS
        case "$OS" in
            Darwin) OS_TAG="darwin" ;;
            Linux)  OS_TAG="linux" ;;
            *) echo "ERROR: Unsupported OS: $OS"; exit 1 ;;
        esac

        # Detect architecture
        case "$ARCH" in
            x86_64|amd64)   ARCH_TAG="x86_64" ;;
            aarch64|arm64)  ARCH_TAG="arm64" ;;
            *) echo "ERROR: Unsupported architecture: $ARCH"; exit 1 ;;
        esac

        SUFFIX="${OS_TAG}-${ARCH_TAG}"

        echo "    Platform: ${OS_TAG}-${ARCH_TAG}"
        echo "    Downloading ralph-mobile-server..."
        curl -fSL "\(releaseBase)/\(releaseTag)/ralph-mobile-server-${SUFFIX}" -o ralph-mobile-server
        chmod +x ralph-mobile-server

        echo "    Downloading ralph CLI..."
        curl -fSL "\(releaseBase)/\(releaseTag)/ralph-${SUFFIX}" -o ralph
        chmod +x ralph

        ls -lh ralph-mobile-server ralph

        # ── Step 3: Install cloudflared ──
        if ! command -v cloudflared >/dev/null 2>&1; then
            echo "==> [3/6] Installing cloudflared..."
            if [ "$OS" = "Darwin" ]; then
                brew install cloudflare/cloudflare/cloudflared
            else
                case "$ARCH" in
                    x86_64|amd64)  CF_ARCH="amd64" ;;
                    aarch64|arm64) CF_ARCH="arm64" ;;
                    armv7l|armhf)  CF_ARCH="arm"   ;;
                    *) echo "ERROR: Unsupported architecture: $ARCH"; exit 1 ;;
                esac
                CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
                sudo curl -L "$CF_URL" -o /usr/local/bin/cloudflared
                sudo chmod +x /usr/local/bin/cloudflared
            fi
            echo "    Installed: $(cloudflared --version)"
        else
            echo "==> [3/6] cloudflared already installed: $(cloudflared --version)"
        fi

        # ── Step 4: Check cloudflared authentication ──
        if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then
            echo ""
            echo "=========================================="
            echo "  ACTION REQUIRED: Cloudflare Login"
            echo "=========================================="
            echo ""
            echo "  cloudflared is not authenticated yet."
            echo "  Run this command and follow the browser link:"
            echo ""
            echo "    cloudflared tunnel login"
            echo ""
            echo "  After authenticating, re-run this script."
            echo "=========================================="
            exit 0
        fi
        echo "==> [4/6] cloudflared authenticated (cert.pem found)"

        # ── Step 5: Start ralph-mobile-server ──
        cd "$RALPH_DIR"
        echo "==> [5/6] Starting ralph-mobile-server on port \(srvPort)..."
        pkill -f 'ralph-mobile-server' 2>/dev/null || true
        sleep 1
        setsid nohup ./ralph-mobile-server --port \(srvPort) --bind-all > ralph-mobile-server.log 2>&1 &
        SERVER_PID=$!
        echo "    Server PID: $SERVER_PID"

        for i in $(seq 1 30); do
            if curl -sf "http://127.0.0.1:\(srvPort)/health" >/dev/null 2>&1; then
                echo "    Server is ready!"
                break
            fi
            sleep 1
        done

        if ! curl -sf "http://127.0.0.1:\(srvPort)/health" >/dev/null 2>&1; then
            echo "ERROR: Server failed to start within 30 seconds"
            echo "Check logs: $RALPH_DIR/ralph-mobile-server.log"
            exit 1
        fi

        # ── Step 6: Start Cloudflare Named Tunnel ──
        echo "==> [6/6] Starting Cloudflare Named Tunnel..."
        cd "$RALPH_DIR"
        ./ralph tunnel start --name ralph-mobile --port \(srvPort)

        # ── Done ──
        LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo "unknown")
        echo ""
        echo "=========================================="
        echo "  Ralph Mobile Backend is Running!"
        echo "=========================================="
        echo ""
        echo "  Tunnel URL: https://ralph-mobile.cfargotunnel.com"
        echo "  LAN URL:    http://${LAN_IP}:\(srvPort)"
        echo "  API Key:    (none required)"
        echo ""
        echo "  Enter the Tunnel URL in Ralph Mobile to connect."
        echo "=========================================="
        """
    }

    // MARK: - Form Helpers

    private func formField(label: String, placeholder: String, text: Binding<String>, keyboardType: UIKeyboardType = .default) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textMuted)
                .kerning(1)

            TextField(placeholder, text: text)
                .font(.system(.body, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textPrimary)
                .padding()
                .background(CyberpunkTheme.bgTertiary)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(CyberpunkTheme.border, lineWidth: 1)
                )
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .keyboardType(keyboardType)
        }
    }

    private func secureFormField(label: String, placeholder: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textMuted)
                .kerning(1)

            SecureField(placeholder, text: text)
                .font(.system(.body, design: .monospaced))
                .foregroundColor(CyberpunkTheme.textPrimary)
                .padding()
                .background(CyberpunkTheme.bgTertiary)
                .cornerRadius(8)
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(CyberpunkTheme.border, lineWidth: 1)
                )
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
        }
    }

    // MARK: - Actions

    private func loadSavedCredentials() {
        if let saved = SSHCredentialStore.loadMostRecent() {
            hostname = saved.host
            username = saved.username
            password = saved.password
            sshPort = String(saved.port)
            serverPort = String(saved.serverPort)
        }
    }

    private func testConnection() async {
        isChecking = true
        errorMessage = nil

        guard let url = URL(string: serverURL) else {
            errorMessage = "Invalid URL format"
            isChecking = false
            return
        }

        RalphAPIClient.configure(baseURL: url, apiKey: "")
        let healthy = await RalphAPIClient.checkHealth()

        if healthy {
            onConnected(serverURL)
        } else {
            errorMessage = "Could not connect. Ensure the setup script completed and the server is running."
        }

        isChecking = false
    }
}

#Preview {
    SetupScriptView(
        onConnected: { _ in },
        onBack: {}
    )
    .preferredColorScheme(.dark)
}
