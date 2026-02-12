# Ralph Mobile Server

REST API + Server-Sent Events (SSE) server for real-time monitoring and control of Ralph orchestrator sessions from mobile clients.

## Overview

Ralph Mobile Server provides a thin HTTP layer over Ralph's event-driven orchestration engine. It:

1. **Discovers** Ralph sessions in the current working directory
2. **Watches** `events.jsonl` files for real-time event changes
3. **Streams** events to connected clients via SSE
4. **Controls** running sessions (pause, resume, stop, steer)
5. **Exposes** configuration, prompt, skill, and hat metadata
6. **Manages** session lifecycle (create, list, delete)

The server is designed for local network deployment (trusted environments only).

## Quick Start

### Prerequisites

- Rust 1.70+ (via rustup)
- Ralph orchestrator project with `.ralph/` directory
- macOS, Linux, or Windows

### Building

```bash
# Build debug binary (faster compilation, slower runtime)
cargo build -p ralph-mobile-server

# Build release binary (slower compilation, optimized runtime)
cargo build -p ralph-mobile-server --release

# Run tests
cargo test -p ralph-mobile-server
```

### Running

```bash
# Start server (discover sessions in current directory)
cargo run -p ralph-mobile-server

# Or use release binary
./target/release/ralph-mobile-server

# Advanced options
cargo run -p ralph-mobile-server -- --help
```

### Server Output

On startup, the server will:
```
Discovered 3 session(s)
  Session abc12345: "/Users/nick/Desktop/.ralph/sessions/abc12345" (task: "planning")
  Session def67890: "/Users/nick/Desktop/.ralph/sessions/def67890" (task: nil)
  Session ghi01234: "/Users/nick/Desktop/.ralph/sessions/ghi01234" (task: "execution")
Starting ralph-mobile-server on 127.0.0.1:8080
```

## Architecture

### Components

#### Session Discovery (`session.rs`)
- Scans current working directory for `.ralph/sessions/`
- Reads `session.jsonl` metadata file
- Extracts session ID, iteration, hat, start time
- Invoked once at startup

#### Event Watcher (`watcher.rs`)
- Monitors `events.jsonl` for each discovered session
- Implements file-based event broadcasting
- Uses `tokio::sync::broadcast` channel for multi-client streaming
- Spawned as background task for each session

#### API Endpoints (`api/`)
- Session management: list, status, create, delete
- Event streaming: SSE endpoint
- Configuration discovery: configs, prompts, hats, presets
- Skill registry: skills, skill content
- Control operations: pause, resume, stop, steer
- Metadata: memories, tasks, loops, host metrics

#### Process Manager (`runner.rs`)
- Spawns ralph processes for new sessions
- Manages process lifecycle (pause via SIGSTOP, resume via SIGCONT)
- Tracks working directories for file operations
- Unix signal handling for clean termination

#### Application State (`events.rs`)
- Holds discovered sessions
- Manages watchers and broadcast channels
- Tracks active sessions created after startup
- Thread-safe via Arc<RwLock<>>

### Data Flow

```
┌─────────────────────────────────────────────────┐
│        Ralph Mobile Client (iOS App)            │
└──────────────────┬──────────────────────────────┘
                   │ HTTP + SSE
                   ▼
┌─────────────────────────────────────────────────┐
│    Ralph Mobile Server (this crate)             │
├─────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌──────────────────────┐  │
│  │ Session Disc.  │  │ Event Watcher Pool   │  │
│  └────────────────┘  └──────────────────────┘  │
│        │                      │                 │
│        └──────────┬───────────┘                 │
│                   │                             │
│        ┌──────────▼──────────┐                 │
│        │ Broadcast Channels  │                 │
│        └──────────┬──────────┘                 │
│                   │                             │
│        ┌──────────▼──────────┐                 │
│        │  API Handlers       │                 │
│        │  - Sessions         │                 │
│        │  - Events (SSE)     │                 │
│        │  - Configs          │                 │
│        │  - Skills           │                 │
│        │  - Control Ops      │                 │
│        └─────────────────────┘                 │
└─────────────────────────────────────────────────┘
           │
           ▼
    ┌────────────────┐
    │ Ralph Sessions │
    │ (.ralph/)      │
    │ - session.jsonl│
    │ - events.jsonl │
    │ - scratchpad.md│
    └────────────────┘
```

## API Endpoints

See [API.md](./API.md) for complete endpoint documentation including request/response examples.

### Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{id}/status` | Get session status |
| GET | `/api/sessions/{id}/events` | Stream events (SSE) |
| POST | `/api/sessions/{id}/emit` | Send custom event |
| POST | `/api/sessions` | Start new session |
| DELETE | `/api/sessions/{id}` | Stop session |
| POST | `/api/sessions/{id}/pause` | Pause session |
| POST | `/api/sessions/{id}/resume` | Resume session |
| POST | `/api/sessions/{id}/steer` | Send steering message |
| GET | `/api/sessions/{id}/scratchpad` | Get scratchpad content |
| GET | `/api/configs` | List configs |
| GET | `/api/prompts` | List prompts |
| GET | `/api/skills` | List skills |
| GET | `/api/skills/{name}/load` | Get skill content |
| GET | `/api/hats` | List hats |
| GET | `/api/host/metrics` | Host system metrics |

## Command Line Options

```bash
ralph-mobile-server [OPTIONS]

OPTIONS:
  --bind <ADDRESS>       Bind address (default: 127.0.0.1:8080)
  --bind-all            Bind to 0.0.0.0:8080 (all interfaces)
  --port <PORT>         Override port (default: 8080)
  --show-key            Display API key on startup
  --help                Show this help message
  --version             Show version
```

### Examples

```bash
# Local development (localhost only)
ralph-mobile-server

# Local development on custom port
ralph-mobile-server --port 3000

# Network deployment (all interfaces)
ralph-mobile-server --bind-all

# Specific interface binding
ralph-mobile-server --bind 192.168.1.100:8080

# With API key display
ralph-mobile-server --show-key
```

## Configuration

### Environment Variables

```bash
# Server bind address (overrides --bind flag)
RALPH_MOBILE_SERVER_BIND=0.0.0.0:8080

# Logging level
RUST_LOG=debug,actix_web=info,tokio=info

# Working directory for session discovery
RALPH_HOME=/path/to/ralph/project
```

### Discover Session Search Paths

Sessions are discovered in this order:
1. Current working directory (`.ralph/sessions/`)
2. Subdirectories with `.ralph/sessions/`
3. Git worktrees (if using parallel loops)

To discover sessions in a specific location:

```bash
cd /path/to/ralph/project
ralph-mobile-server
```

## Event System

### Event Format

Events are JSON-serialized lines in `events.jsonl`:

```json
{
  "id": "evt_abc123",
  "type": "hat.transition",
  "ts": "2026-02-05T10:30:45.123Z",
  "topic": "hat.changed",
  "payload": {
    "from": "planner",
    "to": "builder",
    "reason": "planning_complete"
  },
  "hat": "builder"
}
```

### Event Streaming

When a client connects to `/api/sessions/{id}/events`:

1. **Connection Established**: SSE connection opens
2. **Event File Read**: Existing events up to current position are sent
3. **File Watching**: New lines in `events.jsonl` are watched
4. **Broadcasting**: New events broadcast to all connected clients
5. **Reconnection**: If client disconnects and reconnects, new events are sent

### Event Types

- `iteration.started`: New iteration began
- `iteration.planning`: Planning phase started
- `iteration.executing`: Execution phase started
- `iteration.reviewing`: Review phase started
- `hat.transition`: Hat changed (old_hat → new_hat)
- `tool.call`: Tool was invoked
- `tool.result`: Tool execution completed
- `backpressure`: Tests/lint/typecheck results
- `session.paused`: Session paused
- `session.resumed`: Session resumed
- `session.stopped`: Session terminated
- Custom events from `/api/sessions/{id}/emit`

## Session Lifecycle

### 1. Discovery

At server startup, existing sessions are discovered:
```
Session discovered from .ralph/sessions/{id}/session.jsonl
↓
Session added to AppState
↓
EventWatcher spawned for events.jsonl
↓
BroadcastChannel created for SSE clients
```

### 2. Active Sessions

Sessions created after server startup:
```
POST /api/sessions (config, prompt, working_dir)
↓
ralph process spawned
↓
Session added to active_sessions map
↓
EventWatcher attached to new session
```

### 3. Streaming

When a client connects to `/api/sessions/{id}/events`:
```
Client connects (SSE)
↓
BroadcastStream created
↓
Events stream to client as they arrive
↓
Client disconnects or connection lost
↓
BroadcastStream closed (others unaffected)
```

### 4. Termination

When a session is stopped:
```
DELETE /api/sessions/{id}
↓
SIGTERM sent to ralph process
↓
Process terminated (or SIGKILL after timeout)
↓
EventWatcher closed
↓
BroadcastChannel dropped
```

## Building and Testing

### Build Targets

```bash
# Debug (dev)
cargo build -p ralph-mobile-server

# Release (optimized)
cargo build -p ralph-mobile-server --release

# Library only
cargo build -p ralph-mobile-server --lib
```

### Running Tests

```bash
# All tests
cargo test -p ralph-mobile-server

# Single test
cargo test -p ralph-mobile-server session_discovery

# With output
cargo test -p ralph-mobile-server -- --nocapture

# Specific test module
cargo test -p ralph-mobile-server api::sessions
```

### Test Categories

1. **Unit Tests**: Individual function behavior
2. **Integration Tests**: API endpoint behavior
3. **Smoke Tests**: Full system with recorded fixtures

### Coverage

```bash
# Generate coverage report
cargo tarpaulin -p ralph-mobile-server --out Html
```

## Deployment

### Local Development

```bash
# Terminal 1: Start server
cargo run -p ralph-mobile-server

# Terminal 2: Test endpoint
curl http://127.0.0.1:8080/api/sessions
```

### Network Deployment

```bash
# On server machine
cargo build -p ralph-mobile-server --release
./target/release/ralph-mobile-server --bind-all

# On client machine (iOS app)
# Settings → Server URL: http://<server-ip>:8080
```

### Docker (Optional)

```dockerfile
FROM rust:latest

WORKDIR /app
COPY . .

RUN cargo build -p ralph-mobile-server --release

EXPOSE 8080
CMD ["./target/release/ralph-mobile-server", "--bind-all"]
```

### Systemd Service (Optional)

```ini
[Unit]
Description=Ralph Mobile Server
After=network.target

[Service]
Type=simple
User=ralph
WorkingDirectory=/home/ralph/ralph-orchestrator
ExecStart=/home/ralph/ralph-orchestrator/target/release/ralph-mobile-server --bind-all
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Performance Considerations

### Session Discovery

- **Time**: O(n) where n = number of sessions in `.ralph/sessions/`
- **Frequency**: Once at startup
- **Impact**: Server startup time, not request latency

### Event Streaming

- **Memory**: ~1KB per client per session (broadcast channel overhead)
- **CPU**: Minimal (async I/O with tokio)
- **Network**: Event size (typically <1KB) + SSE framing

### Scalability Limits

- **Concurrent Sessions**: 100+ supported (depends on disk I/O)
- **Concurrent Clients**: 1000+ per session (tokio async)
- **Event Rate**: 1000+ events/second per session
- **Storage**: Limited by disk space for `events.jsonl`

### Optimization Tips

1. **Batch Events**: Combine small events into larger batches
2. **Compress SSE**: Use gzip compression for SSE streams
3. **Cache Metadata**: Cache config/prompt lists (rarely change)
4. **Prune Events**: Archive old `events.jsonl` files periodically
5. **Monitor Memory**: Watch for unbounded broadcast channel growth

## Security

### Current Limitations

⚠️ **This server is designed for local/trusted networks only.**

- No authentication or authorization
- No SSL/TLS (HTTP only)
- No rate limiting
- Full filesystem access to `.ralph/` directory
- Can spawn arbitrary processes

### Recommended Practices

1. **Firewall**: Restrict access to trusted IPs only
2. **Network**: Deploy on internal networks or VPN
3. **Process**: Run as non-privileged user
4. **Monitoring**: Log all API requests and process spawning
5. **Updates**: Keep ralph and dependencies up-to-date

### Future Hardening

- [ ] JWT authentication
- [ ] TLS/HTTPS support
- [ ] Request rate limiting
- [ ] API key rotation
- [ ] Audit logging
- [ ] Sandboxed process execution

## Troubleshooting

### Server Fails to Start

```
Error: bind: Address already in use
```

**Fix**: Another process is using port 8080. Change port:
```bash
ralph-mobile-server --port 3000
```

Or kill existing process:
```bash
lsof -i :8080
kill -9 <PID>
```

### No Sessions Discovered

```
Discovered 0 session(s)
```

**Fixes**:
1. Verify `.ralph/` exists: `ls -la .ralph/sessions/`
2. Run a ralph loop: `ralph run -p "test" --max-iterations 2`
3. Check working directory: Sessions are discovered relative to server's cwd
4. Restart server: `Ctrl+C`, then restart

### SSE Connection Drops

**Symptoms**: Mobile app shows "disconnected"

**Fixes**:
1. Check network connectivity
2. Verify firewall allows port 8080
3. Check server logs: `RUST_LOG=debug`
4. Reconnect: Tap back to Sessions, then tap again
5. Restart server: Clean state

### Events Not Appearing

**Symptoms**: Event feed empty despite running session

**Fixes**:
1. Verify `events.jsonl` exists: `ls -la .ralph/sessions/{id}/events.jsonl`
2. Check permissions: File must be readable by server process
3. Verify ralph is writing events: `tail -f .ralph/sessions/{id}/events.jsonl`
4. Check SSE subscription: Verify mobile app is connected to `/api/sessions/{id}/events`
5. Restart watcher: Restart server to re-initialize watchers

### High CPU Usage

**Fixes**:
1. Reduce event rate: Session may be emitting too many events
2. Check for spinning loops: Look for rapid hat transitions
3. Monitor file I/O: `iotop` on Linux, `iostat` on macOS
4. Reduce client count: Close unused mobile app instances
5. Profile server: `cargo flamegraph` to identify hot paths

## Development

### Project Structure

```
crates/ralph-mobile-server/
├── src/
│   ├── main.rs              # Server entry point, CLI args
│   ├── lib.rs               # Library exports
│   ├── cli.rs               # Command-line parsing
│   ├── session.rs           # Session discovery
│   ├── watcher.rs           # Event file watching + broadcasting
│   └── api/
│       ├── mod.rs           # Route configuration
│       ├── sessions.rs      # Session list/status endpoints
│       ├── events.rs        # SSE streaming endpoint
│       ├── runner.rs        # Process management + control
│       ├── skills.rs        # Skill registry endpoints
│       ├── configs.rs       # Config discovery
│       ├── prompts.rs       # Prompt discovery
│       ├── hats.rs          # Hat listing
│       ├── presets.rs       # Preset discovery
│       ├── host.rs          # System metrics
│       ├── memories.rs      # Memory operations
│       ├── tasks.rs         # Task management
│       ├── loops.rs         # Loop registry
│       ├── robot.rs         # Human-in-the-loop
│       ├── health.rs        # Health check
│       └── ...
├── tests/
│   ├── fixtures/            # Recorded JSONL fixtures
│   └── integration_tests.rs  # Integration tests
├── Cargo.toml               # Manifest
└── README.md                # This file
```

### Adding New Endpoints

1. Create handler in `src/api/new_feature.rs`:
```rust
pub async fn my_handler(state: web::Data<AppState>) -> impl Responder {
    HttpResponse::Ok().json(json!({"message": "Hello"}))
}
```

2. Register in `src/api/mod.rs`:
```rust
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.route("/api/my-endpoint", web::get().to(new_feature::my_handler));
}
```

3. Write tests in `tests/integration_tests.rs`

4. Update `API.md` documentation

### Code Style

- Use idiomatic Rust patterns
- Prefer `async/await` over callbacks
- Handle errors explicitly (no `.unwrap()` in production code)
- Add doc comments to public APIs
- Run `cargo fmt` before committing
- Run `cargo clippy` to check for warnings

### Dependencies

Core dependencies:
- `actix-web`: Web framework
- `tokio`: Async runtime
- `serde`: Serialization
- `tracing`: Structured logging
- `notify`: File watching
- `uuid`: Session IDs

Keep dependencies up-to-date:
```bash
cargo update -p ralph-mobile-server
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Run `cargo test` and `cargo fmt`
5. Commit with descriptive message
6. Push and create pull request

## License

See LICENSE file in repository root.

## Related Documentation

- [API Reference](./API.md) - Complete endpoint documentation
- [iOS App Guide](../ios/README.md) - Mobile client documentation
- [Ralph Orchestrator](../../README.md) - Main project documentation
- [Architecture Notes](./CLAUDE.md) - Development notes
