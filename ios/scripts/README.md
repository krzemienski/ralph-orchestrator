# Ralph Mobile Backend Auto-Start Scripts

This directory contains scripts that automatically start the Ralph backend server when building the iOS app.

## Overview

When you build RalphMobile in Debug mode, Xcode automatically:
1. Checks if the backend is already running
2. Kills any stale processes on port 8080
3. Builds `ralph-mobile-server` (release mode)
4. Starts the backend in the background
5. Waits for it to be ready (health check)
6. Extracts and saves the API key

## Files

| File | Purpose |
|------|---------|
| `xcode-prebuild.sh` | Called by Xcode pre-build phase (Debug only) |
| `start-backend.sh` | Main backend startup logic |
| `stop-backend.sh` | Stops the backend and cleans up |
| `backend` | Convenient CLI wrapper for manual control |

## Xcode Integration

The `xcode-prebuild.sh` script is configured as a **Run Script** build phase in the RalphMobile target.

To verify/add manually:
1. Open `RalphMobile.xcodeproj` in Xcode
2. Select the RalphMobile target
3. Go to **Build Phases**
4. Ensure there's a "Run Script" phase **before** "Compile Sources" with:
   ```bash
   "${SRCROOT}/scripts/xcode-prebuild.sh"
   ```

## Manual Backend Control

Use the `backend` CLI wrapper for manual control:

```bash
# Start backend manually
./scripts/backend start

# Stop backend
./scripts/backend stop

# Restart backend
./scripts/backend restart

# Check backend status
./scripts/backend status

# View backend logs
./scripts/backend logs
```

## Generated Files

The scripts create these files in the `ios/` directory:

| File | Purpose |
|------|---------|
| `.ralph-backend-pid` | Process ID of running backend |
| `.ralph-backend.log` | Backend stdout/stderr |

**Note:** These files are gitignored.

## Configuration

### Backend Port
Default: `8080`
To change: Edit `PORT=8080` in `start-backend.sh`

### Startup Timeout
Default: `10` seconds
To change: Edit `MAX_WAIT=10` in `start-backend.sh`

### Build Mode
Auto-start only runs for **Debug** builds (not Release/Archive).
To change: Edit the condition in `xcode-prebuild.sh`

## Troubleshooting

### Backend won't start
```bash
# Check logs
tail -f .ralph-backend.log

# Verify Rust is installed
cargo --version

# Build backend manually
cd ..
cargo build --bin ralph-mobile-server --release
```

### Port already in use
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use the stop script
./scripts/backend stop
```

### Connection refused
```bash
# Check if backend is running
./scripts/backend status

# View logs for errors
./scripts/backend logs
```

### Xcode build phase not running
1. Clean build folder: `Cmd+Shift+K`
2. Verify script is executable: `ls -la scripts/xcode-prebuild.sh`
3. Check build phase order (must be before Compile Sources)

## Disabling Auto-Start

To disable automatic backend startup:

**Option 1: Remove build phase**
- In Xcode, delete the "Run Script" phase

**Option 2: Skip for specific builds**
- Set environment variable: `SKIP_BACKEND_START=1`
- Or change `CONFIGURATION` check in `xcode-prebuild.sh`

## iOS App Configuration

The backend server runs locally without authentication.

To configure the iOS app:
1. Launch RalphMobile in Simulator
2. Go to Settings (⚙️ in sidebar)
3. Enter Server URL: `http://127.0.0.1:8080`
4. No API key required!

## Production Builds

For TestFlight/App Store builds:
- Auto-start is **disabled** (Release/Archive builds)
- You'll need to configure a production backend URL
- Use environment-specific configuration

## Development Workflow

### Normal Development
1. Build app in Xcode (`Cmd+B` or `Cmd+R`)
2. Backend automatically starts
3. App connects to `http://127.0.0.1:8080`

### Backend Code Changes
If you modify backend code:
```bash
# Restart backend to pick up changes
./scripts/backend restart
```

### Clean Slate
```bash
# Stop backend and clean all state
./scripts/backend stop
rm -rf ../.ralph
```

## See Also

- Backend server: `../crates/ralph-mobile-server/`
- API documentation: `../crates/ralph-mobile-server/API.md`
- iOS client: `RalphMobile/Services/RalphAPIClient.swift`
