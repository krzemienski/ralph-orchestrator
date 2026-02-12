# RalphMobile Quick Start

This guide gets you up and running with RalphMobile in 60 seconds.

## Prerequisites

- Xcode 16+ installed
- Rust/Cargo installed ([rustup.rs](https://rustup.rs))
- macOS with iOS Simulator

## Option 1: Automatic (Recommended)

The backend starts automatically when you build the app!

1. **Open project in Xcode**
   ```bash
   open RalphMobile.xcodeproj
   ```

2. **Build and run** (Cmd+R)
   - Backend automatically starts in background
   - App launches in simulator
   - Ready to use!

3. **Configure server URL** (one-time)
   - Open Settings in app (⚙️ icon in sidebar)
   - Enter: `http://127.0.0.1:8080`
   - Done!

## Option 2: Manual Backend Control

Start backend before building:

```bash
./scripts/backend start
```

Then build normally in Xcode.

## Verify It's Working

### Check backend status
```bash
./scripts/backend status
```

Expected output:
```
✓ Backend is running (PID: xxxxx)
✓ Health check: OK
📍 Server: http://127.0.0.1:8080
✓ No authentication required
```

### Test API endpoints
```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/sessions
```

### Check backend logs
```bash
./scripts/backend logs
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `./scripts/backend start` | Start backend |
| `./scripts/backend stop` | Stop backend |
| `./scripts/backend restart` | Restart backend |
| `./scripts/backend status` | Check status |
| `./scripts/backend logs` | View logs (Ctrl+C to exit) |
| `./scripts/backend clean` | Stop + clean all files |

## Testing With Real Ralph Loops

1. **Start a Ralph loop** (from project root):
   ```bash
   cd ..
   ralph run -c presets/feature.yml -p "test prompt" --max-iterations 10
   ```

2. **Watch in RalphMobile app**:
   - SSE events stream in real-time
   - Hat transitions show with colors
   - Iteration progress updates
   - Token metrics display

3. **Recommended test duration**: 10+ minutes to see multiple hat transitions

## Troubleshooting

### Backend won't start
```bash
# Check if cargo is installed
cargo --version

# If not, install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Port 8080 already in use
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use the stop script
./scripts/backend stop
```

### App shows "Connection Error"
1. Check backend is running: `./scripts/backend status`
2. Verify URL in Settings: `http://127.0.0.1:8080` (no trailing slash!)
3. Check logs: `./scripts/backend logs`

### Build fails in Xcode
1. Clean build folder: `Cmd+Shift+K`
2. Stop any running backend: `./scripts/backend stop`
3. Rebuild: `Cmd+B`

## Development Workflow

### Normal development
1. Open Xcode
2. Press Cmd+R
3. Backend auto-starts, app launches
4. Develop, test, iterate

### Backend code changes
If you modify backend Rust code:
```bash
./scripts/backend restart
```

### Clean slate
Stop everything and reset:
```bash
./scripts/backend clean
rm -rf ../.ralph
```

## Project Structure

```
ralph-orchestrator/
├── crates/ralph-mobile-server/    # Backend Rust server
└── ios/                            # iOS app
    ├── RalphMobile/                # Swift source
    ├── scripts/                    # Backend automation
    │   ├── backend                 # CLI wrapper
    │   ├── start-backend.sh        # Startup script
    │   ├── stop-backend.sh         # Shutdown script
    │   └── xcode-prebuild.sh       # Xcode integration
    └── .ralph-backend.log          # Backend logs (generated)
```

## Next Steps

- Read [scripts/README.md](scripts/README.md) for detailed documentation
- Check [validation-screenshots/](validation-screenshots/) for feature demos
- See [PROGRAMMATIC-NAVIGATION.md](PROGRAMMATIC-NAVIGATION.md) for navigation patterns

## Getting Help

If you encounter issues:

1. Check backend logs: `./scripts/backend logs`
2. Verify status: `./scripts/backend status`
3. Try clean restart:
   ```bash
   ./scripts/backend clean
   ./scripts/backend start
   ```
4. Check backend test suite:
   ```bash
   cd ..
   cargo test -p ralph-mobile-server
   ```

## Production Notes

- Auto-start only works for **Debug** builds
- For Release/Archive builds, backend is NOT auto-started
- Configure production backend URL in Settings
- No authentication required (local development only)
