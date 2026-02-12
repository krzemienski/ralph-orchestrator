# Ralph Mobile - iOS Client

Real-time monitoring and control of Ralph orchestrator sessions from your iPhone or iPad.

## Features

- **Session Monitoring**: Watch Ralph orchestration loops in real-time with live event streaming
- **Multi-Session Support**: Monitor multiple concurrent sessions from different configurations
- **Hat Visualization**: Track the current decision-making "hat" (planner, fixer, builder, etc.)
- **Backpressure Status**: View test, lint, and type-check results in real-time
- **Token Metrics**: Monitor token usage across planning, execution, and review phases
- **Steering Controls**: Pause, resume, or stop sessions directly from the app
- **Event Emission**: Send custom events to running sessions via the "Emit" button
- **Dark Cyberpunk Theme**: Immersive, professional user interface optimized for long monitoring sessions

## Quick Start

**New!** The backend now auto-starts when building in Xcode. See [QUICK-START.md](QUICK-START.md) for 60-second setup.

### Prerequisites

- iOS 15 or later
- Xcode 14+ (for building from source)
- Rust/Cargo installed ([rustup.rs](https://rustup.rs)) for local development

### Building from Source (Automatic Backend)

```bash
# Navigate to the ios directory
cd ios

# Open the Xcode project
open RalphMobile.xcodeproj

# Build and run - backend starts automatically!
# Product → Run (Cmd+R)
```

The ralph-mobile-server will automatically start in the background when building in Debug mode.

**First time setup:**
1. Build app in Xcode (Cmd+R)
2. Go to Settings in app
3. Enter Server URL: `http://127.0.0.1:8080`
4. Done!

See [scripts/README.md](scripts/README.md) for manual backend control.

### Installing Pre-built App

Download the latest `.ipa` from the releases page and install via Xcode or Apple Configurator.

## Initial Setup

### 1. Configure Server Connection

1. Launch Ralph Mobile
2. Tap the **Settings** tab (bottom right)
3. Enter your server URL (default: `http://127.0.0.1:8080`)
4. Optionally configure:
   - Default backend (Claude, Kiro, Custom)
   - API host for external services
   - Max iterations for default sessions
   - Idle timeout duration
   - Default configuration template

### 2. Start Ralph Mobile Server

On your Mac or server machine:

```bash
# From ralph-orchestrator root
cargo run --bin ralph-mobile-server -- --bind-all

# For local development (simulator only)
cargo run --bin ralph-mobile-server
```

The server will:
- Discover existing Ralph sessions in the current directory
- Start an HTTP server on port 8080 (configurable with `--bind 0.0.0.0:3000`)
- Watch `events.jsonl` files for real-time event streaming

### 3. Connect iOS App to Server

On iPhone:
1. Tap Settings
2. Update "Server URL" to match your server's IP/hostname
   - Local development: `http://127.0.0.1:8080`
   - Network: `http://<your-machine-ip>:8080`
3. Tap back to apply changes

The app will automatically fetch available sessions from the server.

## User Interface

### Main Views

#### Dashboard Tab (Home)
**Purpose**: High-level overview of a selected session

**Sections**:
- **Connection Status**: Green indicator when connected, red when disconnected
- **Hat Status Card**: Current decision-making hat with color coding
- **Control Bar**: Play/pause/stop buttons for session control
- **Backpressure Status**: Tests, lint, typecheck pass/fail indicators
- **Stats Grid**: Iteration count, token usage, elapsed time, mode
- **Recent Tool Calls**: Last 5 tool invocations with type and parameters

**Controls**:
- Play/Pause: Resume or pause an idle/paused session
- Stop: Terminate the session (confirmation required)
- Emit: Send a custom event to the session

#### Sessions Tab
**Purpose**: Browse and select from all available Ralph sessions

**Display**:
- Session ID (first 8 characters as icon)
- Current iteration number
- Active hat name
- Session start time
- Last event timestamp (if running)

**Actions**:
- Tap session to view full detail page
- Swipe to delete from tracking (local only, doesn't stop session)
- Refresh to re-fetch session list from server

#### Library Tab
**Purpose**: Browse available configurations, prompts, and skills

**Subsections**:
- **Configs**: Available `.yml` configuration files with descriptions
- **Prompts**: Prompt templates organized by category
- **Skills**: Available skills with descriptions and tags
- **Hats**: All available decision-making hats
- **Presets**: Quick-start session presets

**Actions**:
- Tap config/prompt to view content
- Copy to clipboard
- Share via AirDrop or Messages

#### Settings Tab
**Purpose**: Configure app behavior and server connection

**Sections**:
- **Server**: Ralph Mobile Server URL
- **Backend**: Default AI backend (Claude, Kiro, etc.)
- **Defaults**: Default session parameters
- **Notifications**: Alert and sound preferences
- **Appearance**: Theme and layout options

## Monitoring a Session

### Connecting to a Session

1. Tap **Sessions** tab
2. Tap a session from the list
3. The app will:
   - Connect to the server
   - Fetch session status (mode, elapsed time, iteration count)
   - Subscribe to SSE event stream if session is active
   - Display all 10 sections of the session detail view

### Understanding the Session Detail View (10 Sections)

#### 1. Status Header
- Session ID
- Current iteration number
- Hat name with color indicator
- Connection state (connected/disconnected/error)
- Last update timestamp

#### 2. Token Metrics
- Planning tokens used
- Execution tokens used
- Review tokens used
- Total token budget remaining
- Usage sparkline chart

#### 3. Hat Flow
- Timeline of hat transitions during this session
- Current hat highlighted
- Trigger event for each transition

#### 4. Backpressure Status
- Test results (pass/fail)
- Lint results (pass/fail)
- Type-check results (pass/fail)
- Last check timestamp

#### 5. Iteration Stats
- Current iteration number
- Total iterations in plan
- Estimated time remaining
- Average time per iteration

#### 6. Mode & Control
- Current mode (live, complete, paused)
- Elapsed time
- Start time
- Session directory path

#### 7. Recent Events
- Latest 10 events from the session
- Event type, timestamp, and data
- Scroll for full event history

#### 8. Event Stream (Real-time Feed)
- Live event count
- Current connection status
- Reconnection attempts

#### 9. Hats Reference
- All available hats with descriptions
- Color coding for each hat
- Usage frequency in this session

#### 10. Session Actions
- Pause/Resume buttons
- Stop Session button with confirmation
- Emit Event button
- Export Session Data button

### Understanding Connection States

**Connected (Green)**
- App is receiving real-time SSE events
- Server is reachable
- Session events are streaming

**Disconnected (Gray)**
- SSE connection dropped but session data is stale
- Server may be unreachable
- Last data shown is from final connection

**Error (Red)**
- Server returned an error
- Session does not exist
- Check server URL in Settings

### Starting a New Session from the App

1. Tap **Sessions** tab
2. Tap **Create Ralph** (+ button)
3. Fill in the wizard:
   - **Config**: Select from available configs
   - **Prompt**: Enter or select a prompt
   - **Working Directory**: Path where session files will be stored
4. Tap **Start**
5. The server will spawn a new ralph process and stream events

The new session will appear in the Sessions list immediately.

## Monitoring Real-time Events

### Event Types

The app displays events from ralph's event stream:

- **iteration.started**: New iteration began
- **iteration.planning**: Hat switched to planning phase
- **iteration.executing**: Hat switched to execution phase
- **iteration.reviewing**: Hat switched to review phase
- **tool.call**: Tool was invoked by the agent
- **tool.result**: Tool execution completed
- **hat.transition**: Hat changed (includes old→new hat names)
- **backpressure**: Tests/lint/typecheck results available

### Real-time Metrics

**Token Metrics** update as events arrive:
- Planning phase tokens consumed
- Execution phase tokens consumed
- Review phase tokens consumed
- Total remaining in session budget

**Iteration Progress** updates with each event:
- Current iteration number (incremented)
- Total iterations in plan (updated if plan changes)
- Elapsed time (recalculated from server)

### Event Feed Updates

Events stream in real-time if the session is active:

1. Server detects new lines in `events.jsonl`
2. Events are broadcast to all connected clients
3. App receives SSE updates
4. UI refreshes with new events
5. Event count increments

**Reconnection Behavior**:
- If connection drops, app attempts to reconnect
- Exponential backoff: 1s, 2s, 4s, 8s, max 30s
- When reconnected, app fetches any missed events via `GET /api/sessions/{id}/status`
- Event feed automatically resumes

## Steering Sessions

### Pause/Resume

**Pause**: Stops the session at the end of the current iteration
- Status changes to "paused"
- SSE events stop flowing (session paused)
- All controls remain available

**Resume**: Restarts a paused session
- Status changes back to "live"
- Session continues from where it left off
- SSE events resume

### Stop Session

**Stop**: Terminates the session completely
- Requires confirmation (prevent accidental stops)
- Sends SIGTERM to the ralph process
- Status changes to "stopped"
- Event stream closes
- Session becomes read-only

### Emit Event

**Send Custom Event**: Inject an event into the session
1. Tap **Emit** button
2. Enter event topic (e.g., "build.done", "review.complete")
3. Optionally add JSON payload
4. Tap **Send**

The event is:
- Published to the session's event bus
- Visible in the event feed
- Potentially triggers hat transitions
- Available to running agents

## Troubleshooting

### "Server URL not reachable"

**Symptoms**: Settings page shows red warning, Sessions tab shows error

**Fixes**:
1. Verify server is running: `cargo run --bin ralph-mobile-server`
2. Check firewall: Server must be accessible on configured port
3. Verify URL: Use `--bind-all` flag if accessing from different machine
4. Check IP: Use actual machine IP, not `127.0.0.1` for network access
5. Test with curl: `curl http://<server-url>/api/sessions`

### "No sessions found"

**Symptoms**: Sessions tab is empty despite server running

**Fixes**:
1. Verify ralph sessions exist: Check `.ralph/` directory
2. Run a ralph loop: `ralph run -p "test prompt" --max-iterations 5`
3. Check server logs: Look for session discovery messages
4. Restart server: May need to discover new sessions
5. Check working directory: Server discovers sessions in its current working directory

### "Events not updating"

**Symptoms**: Session detail view shows old data, no new events

**Fixes**:
1. Check connection status: Should be green/connected
2. Verify SSE endpoint: `curl http://<server-url>/api/sessions/{id}/events`
3. Check session status: Is ralph loop still running?
4. Reconnect: Tap back to Sessions, then tap session again
5. Check logs: `RALPH_DIAGNOSTICS=1 ralph run ...` for session events

### "Can't stop session"

**Symptoms**: Stop button doesn't work or shows "stopping..."

**Fixes**:
1. Wait 30 seconds: Process manager may be terminating
2. Check server logs: Look for process termination messages
3. Force kill on server: `pkill -f 'ralph run'`
4. Restart server: May need to reset process manager state
5. Check file permissions: Process owner must have kill permissions

### "Settings not persisting"

**Symptoms**: Server URL resets after app restart

**Fixes**:
1. Force save: Swipe/tap away from Settings view after editing
2. Check storage space: Device may have insufficient storage
3. Reinstall app: Clear UserDefaults
4. Enable iCloud sync: Settings → [Your Name] → iCloud (optional)

## Architecture

### Client-Server Communication

**Discovery** (on app launch):
```
GET /api/sessions
↓
Returns [SessionListItem]
```

**Status** (when session selected):
```
GET /api/sessions/{id}/status
↓
Returns SessionStatus (mode, elapsed_secs, hat)
```

**Event Stream** (real-time updates):
```
GET /api/sessions/{id}/events
↓
Returns text/event-stream (SSE)
```

**Controls** (user actions):
```
POST /api/sessions/{id}/pause
POST /api/sessions/{id}/resume
POST /api/sessions/{id}/steer
DELETE /api/sessions/{id}
```

### Data Models

#### Session
- `id`: Unique session identifier
- `iteration`: Current iteration number
- `total`: Total iterations in plan (if known)
- `hat`: Current decision-making hat
- `elapsed_secs`: Seconds since session start (status endpoint only)
- `mode`: "live" | "complete" | "paused" (status endpoint only)
- `status`: "running" | "paused" | "stopped" | "idle"
- `started_at`: ISO 8601 timestamp (list endpoint only)

#### Event
- `id`: Unique event identifier
- `type`: Event type (iteration.started, hat.transition, tool.call, etc.)
- `ts`: ISO 8601 timestamp
- `topic`: Event topic (for emit events)
- `payload`: Event-specific data
- `hat`: Associated hat (if applicable)

#### TokenMetrics
- `planning_tokens`: Tokens used in planning phase
- `execution_tokens`: Tokens used in execution phase
- `review_tokens`: Tokens used in review phase
- `total_remaining`: Budget remaining for session

### Dark Cyberpunk Theme

All UI elements use the Cyberpunk theme:
- **Primary Background**: `#0a0e27`
- **Accent Cyan**: `#00d9ff`
- **Accent Pink**: `#ff006e`
- **Accent Purple**: `#c71585`
- **Text Primary**: `#ffffff`
- **Text Secondary**: `#a0a0a0`
- **Border Color**: `#1a1a2e`

Hat colors:
- **Planner**: Cyan (`#00d9ff`)
- **Fixer**: Pink (`#ff006e`)
- **Builder**: Purple (`#c71585`)
- **Reviewer**: Green (`#39ff14`)
- **Architect**: Gold (`#ffd700`)

## Development

### Project Structure

```
ios/
├── RalphMobile/                 # Main app target
│   ├── Models/                  # Data structures (Session, Event, etc.)
│   ├── ViewModels/              # State management
│   ├── Views/                   # SwiftUI components
│   ├── Services/                # API client, SSE parser
│   ├── Theme/                   # Cyberpunk design system
│   └── Utilities/               # Formatting, helpers
├── RalphMobileTests/            # Unit tests
├── RalphMobileUITests/          # UI tests
└── RalphMobile.xcodeproj        # Xcode project
```

### Building

```bash
# Debug build
xcodebuild -scheme RalphMobile -configuration Debug build

# Release build for distribution
xcodebuild -scheme RalphMobile -configuration Release build

# Run tests
xcodebuild -scheme RalphMobile test

# Run UI tests
xcodebuild -scheme RalphMobileUITests test
```

### Environment Variables

```bash
# Server URL (override via Settings if needed)
RALPH_SERVER_URL=http://127.0.0.1:8080

# API key (if server requires authentication)
RALPH_API_KEY=your-key-here
```

### Code Quality

- SwiftUI with async/await for concurrency
- MVVM architecture with @StateObject and @ObservedObject
- Combine framework for reactive data flow
- Proper error handling and network resilience
- Accessibility identifiers on all interactive elements

## Testing

### Unit Tests

```bash
xcodebuild -scheme RalphMobile test -derivedDataPath build
```

Tests cover:
- Model encoding/decoding
- ViewModel state transitions
- Network request formatting
- SSE event parsing

### UI Tests

```bash
xcodebuild -scheme RalphMobileUITests test -derivedDataPath build
```

Scenarios:
- Connect to server
- Select and monitor session
- Pause/resume/stop session
- Send custom event
- Navigate all tabs
- Update settings

### Manual Testing Checklist

- [ ] Server connection at 127.0.0.1:8080
- [ ] Server connection at remote IP
- [ ] Sessions list loads
- [ ] Session detail view shows all 10 sections
- [ ] SSE events stream in real-time
- [ ] Pause/resume controls work
- [ ] Stop session confirmation dialog appears
- [ ] Emit event sends custom event
- [ ] Settings persist across app restart
- [ ] Dark theme renders correctly on all screens
- [ ] Connection indicator updates appropriately

## Deployment

### TestFlight

```bash
# Create archive
xcodebuild -scheme RalphMobile -configuration Release archive

# Export for app store
xcodebuild -exportArchive -archivePath build/RalphMobile.xcarchive \
  -exportOptionsPlist ExportOptions.plist \
  -exportPath build/DistributionArchive
```

### App Store

1. Archive the app
2. Submit to App Store Connect
3. Complete review and approve
4. Release to users

## Performance Optimization

- Lazy loading of event feed (infinite scroll)
- Debounced SSE reconnection attempts
- Efficient event filtering and sorting
- Memory-efficient image and data caching
- Background task for continuing SSE connection when app minimized

## Known Limitations

- SSE connection pauses when app goes to background (iOS limitation)
- Maximum event history retained: 1000 events (older events cleared)
- Settings use local device storage only (no iCloud sync by default)
- One server connection per app instance
- Maximum 10 concurrent sessions displayed (performance)

## Support

For issues or questions:
1. Check Troubleshooting section above
2. Review server logs: Check ralph-mobile-server output
3. Enable debug logging: Set environment variable `RUST_LOG=debug`
4. Check GitHub issues: Report bugs or request features
5. Review CLAUDE.md: Project-specific development notes
