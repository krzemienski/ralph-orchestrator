# Backend Auto-Start Installation Checklist

Use this checklist to verify the backend auto-start system is properly installed and working.

## Prerequisites Check

- [ ] **Rust installed**
  ```bash
  cargo --version
  # Should output: cargo 1.x.x
  ```
  If not: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

- [ ] **Xcode installed**
  ```bash
  xcodebuild -version
  # Should output: Xcode 14.0+
  ```

- [ ] **Project cloned**
  ```bash
  cd /Users/nick/Desktop/ralph-orchestrator
  ls ios/RalphMobile.xcodeproj
  # Should exist
  ```

## File Installation Check

- [ ] **Scripts directory exists**
  ```bash
  cd ios
  ls scripts/
  # Should show: backend, start-backend.sh, stop-backend.sh, xcode-prebuild.sh, README.md, etc.
  ```

- [ ] **Scripts are executable**
  ```bash
  ls -la scripts/ | grep "rwxr-xr-x"
  # All .sh files and 'backend' should be executable
  ```
  If not: `chmod +x scripts/*.sh scripts/backend`

- [ ] **.gitignore configured**
  ```bash
  grep "ralph-backend" .gitignore
  # Should show:
  # .ralph-backend-pid
  # .ralph-backend.log
  ```

## Manual Script Test

- [ ] **Backend starts manually**
  ```bash
  export SRCROOT="$(pwd)"
  ./scripts/backend start
  ```
  Expected output:
  ```
  🚀 Ralph Backend Auto-Start
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📦 Building ralph-mobile-server...
  🔧 Starting ralph-mobile-server...
  ✓ Backend started (PID: xxxxx)
  ⏳ Waiting for backend to be ready...
  ✓ Backend is ready!
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Backend ready at http://127.0.0.1:8080
  ```

- [ ] **Health check passes**
  ```bash
  curl http://127.0.0.1:8080/health
  # Should output: OK
  ```

- [ ] **API endpoint responds**
  ```bash
  curl http://127.0.0.1:8080/api/sessions
  # Should output: [] or JSON array
  ```

- [ ] **Status command works**
  ```bash
  ./scripts/backend status
  ```
  Expected:
  ```
  ✓ Backend is running (PID: xxxxx)
  ✓ Health check: OK
  📍 Server: http://127.0.0.1:8080
  ✓ No authentication required
  ```

- [ ] **Stop command works**
  ```bash
  ./scripts/backend stop
  ```
  Expected:
  ```
  🛑 Stopping Ralph Backend
  ⚠ Killing backend (PID: xxxxx)
  ✓ Backend stopped
  ✓ Cleanup complete
  ```

- [ ] **Files cleaned up**
  ```bash
  ls .ralph-backend-pid .ralph-backend.log
  # Should show: No such file or directory
  ```

## Xcode Integration Check

- [ ] **Xcode build phase added** (see [scripts/ADD-TO-XCODE.md](scripts/ADD-TO-XCODE.md))
  - Open RalphMobile.xcodeproj in Xcode
  - Select RalphMobile target → Build Phases
  - Verify "Run Script" phase exists before "Compile Sources"
  - Script contains: `"${SRCROOT}/scripts/xcode-prebuild.sh"`

- [ ] **Build with auto-start works**
  1. Clean build folder: `Cmd+Shift+K`
  2. Build: `Cmd+B`
  3. Check build log for:
     ```
     🚀 Ralph Backend Auto-Start
     ✓ Backend started...
     ✓ Backend is ready!
     ```

- [ ] **Backend running after build**
  ```bash
  ./scripts/backend status
  # Should show: ✓ Backend is running
  ```

## iOS App Connection Check

- [ ] **App builds successfully**
  - In Xcode: `Cmd+R`
  - App launches in Simulator
  - No build errors

- [ ] **App Settings configured**
  - Open Settings (⚙️ icon)
  - Server URL: `http://127.0.0.1:8080`
  - Save settings

- [ ] **App connects to backend**
  - Navigate to Sessions (first tab)
  - No "Connection Error" message
  - Sessions list loads (may be empty)

- [ ] **Real-time updates work**
  1. Start a Ralph loop:
     ```bash
     cd /Users/nick/Desktop/ralph-orchestrator
     ralph run -c presets/feature.yml -p "test prompt" --max-iterations 5
     ```
  2. In iOS app:
     - Session appears in list
     - Events stream in real-time
     - Hat transitions show
     - Token metrics update

## Cleanup Test

- [ ] **Clean command works**
  ```bash
  ./scripts/backend clean
  ```
  Expected:
  ```
  🧹 Cleaning up...
  🛑 Stopping Ralph Backend
  ✓ Backend stopped
  ✓ All backend files removed
  ```

- [ ] **No processes remain**
  ```bash
  lsof -i:8080
  # Should show: (nothing) or command not found
  ```

- [ ] **No files remain**
  ```bash
  ls -a | grep ralph-backend
  # Should show: (nothing)
  ```

## Restart Test

- [ ] **Restart command works**
  ```bash
  ./scripts/backend restart
  ```
  Expected:
  ```
  ♻️  Restarting backend...
  🛑 Stopping Ralph Backend
  ...
  🚀 Ralph Backend Auto-Start
  ...
  ✓ Backend is ready!
  ```

- [ ] **Backend running after restart**
  ```bash
  ./scripts/backend status
  curl http://127.0.0.1:8080/health
  ```

## Error Handling Test

- [ ] **Port conflict handled**
  1. Start backend: `./scripts/backend start`
  2. Try again: `./scripts/backend start`
  3. Should detect existing backend and exit cleanly

- [ ] **Stale PID handled**
  1. Start backend
  2. Manually kill process: `kill -9 $(cat .ralph-backend-pid)`
  3. Start again: `./scripts/backend start`
  4. Should detect stale PID and start fresh

- [ ] **Release build skips auto-start**
  1. In Xcode: Product → Scheme → Edit Scheme
  2. Run → Build Configuration → Release
  3. Build: `Cmd+B`
  4. Check build log - should NOT show backend startup
  5. Reset: Build Configuration → Debug

## Documentation Check

- [ ] **README updated**
  ```bash
  grep "auto-start" README.md
  # Should find references to auto-start feature
  ```

- [ ] **QUICK-START.md exists**
  ```bash
  ls QUICK-START.md
  # Should exist
  ```

- [ ] **scripts/README.md detailed**
  ```bash
  wc -l scripts/README.md
  # Should be >100 lines
  ```

## Final Verification

- [ ] **Full workflow test**
  1. Stop all: `./scripts/backend stop`
  2. Clean Xcode: `Cmd+Shift+K`
  3. Build in Xcode: `Cmd+R`
  4. Backend auto-starts
  5. App launches
  6. Configure Settings
  7. Start Ralph loop
  8. Watch events stream
  9. Stop Ralph loop
  10. Quit Xcode
  11. Backend still running: `./scripts/backend status`
  12. Manual stop: `./scripts/backend stop`

## Completion

If all items are checked ✅, the backend auto-start system is fully installed and operational!

## Troubleshooting

If any checks fail:

1. **Review logs**: `./scripts/backend logs`
2. **Check documentation**: `scripts/README.md`
3. **Consult architecture**: `scripts/ARCHITECTURE.md`
4. **Manual test**: Follow [ADD-TO-XCODE.md](scripts/ADD-TO-XCODE.md)

## Maintenance

Regular checks:

- **Weekly**: Verify backend tests pass
  ```bash
  cd /Users/nick/Desktop/ralph-orchestrator
  cargo test -p ralph-mobile-server
  ```

- **After Rust updates**: Rebuild backend
  ```bash
  ./scripts/backend restart
  ```

- **After script changes**: Test manually before committing
  ```bash
  ./scripts/backend clean
  ./scripts/backend start
  ```

## Sign-off

Installation completed by: ________________
Date: ________________
All checks passed: ☐ Yes  ☐ No
Notes: _________________________________
