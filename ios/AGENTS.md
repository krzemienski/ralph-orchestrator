<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-01-27 | Updated: 2026-01-27 -->

# ios

## Purpose

RalphMobile iOS companion app for monitoring and controlling Ralph orchestrator sessions from mobile devices. Built with SwiftUI, connects to `ralph-mobile-server` via REST API and Server-Sent Events (SSE).

## Key Files

| File | Description |
|------|-------------|
| `RalphMobile.xcodeproj/` | Xcode project configuration |
| `RalphMobile/` | Main app source code |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `RalphMobile/Models/` | Data models (Event, Session, Config, TokenMetrics) |
| `RalphMobile/Views/` | SwiftUI views organized by feature |
| `RalphMobile/ViewModels/` | ObservableObject view models |
| `RalphMobile/Services/` | API client, SSE parser, Keychain |
| `RalphMobile/Theme/` | Cyberpunk visual theme and components |
| `RalphMobile/Utilities/` | SSE parsing, time formatting |
| `RalphMobileTests/` | Unit tests |
| `RalphMobileUITests/` | UI automation tests |

## For AI Agents

### Architecture
- **MVVM pattern**: Views observe ViewModels, ViewModels call Services
- **Cyberpunk theme**: Neon colors, terminal aesthetic
- **Real-time updates**: SSE streaming from ralph-mobile-server

### Key Views
| View | Purpose |
|------|---------|
| `MainNavigationView` | Root navigation with sidebar |
| `UnifiedRalphView` | Main session monitoring dashboard |
| `CreateRalphWizard` | Wizard for starting new sessions |
| `LibraryView` | Browse configs and prompts |
| `SettingsView` | API key and server configuration |

### Services
| Service | Purpose |
|---------|---------|
| `RalphAPIClient` | REST API calls to ralph-mobile-server |
| `EventStreamService` | SSE connection for real-time events |
| `KeychainManager` | Secure API key storage |
| `AnthropicClient` | Direct Anthropic API for AI features |

### Testing Requirements
- Build: `xcodebuild -scheme RalphMobile build`
- Test: `xcodebuild -scheme RalphMobile test`
- Requires iOS 17+ deployment target

### Common Patterns
- Use `@Observable` macro for view models (iOS 17+)
- Use `async/await` for all network calls
- Use `AsyncStream` for SSE event parsing

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
