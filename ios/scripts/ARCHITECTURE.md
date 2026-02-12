# Backend Auto-Start Architecture

Visual guide to how the automatic backend startup works.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Xcode Build                         │
│                                                             │
│  1. User presses Cmd+R (Run)                               │
│  2. Xcode begins build process                             │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  Build Phases (sequential)                        │    │
│  │                                                     │    │
│  │  ✓ Dependencies                                    │    │
│  │  ▶ Run Script: "Start Ralph Backend (Debug Only)" │    │
│  │    └─> Calls: ${SRCROOT}/scripts/xcode-prebuild.sh│    │
│  │  ⏸️  Compile Sources (waits for script)            │    │
│  │  ⏸️  Link Binary                                    │    │
│  │  ...                                               │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              xcode-prebuild.sh (Gateway)                    │
│                                                             │
│  if [ "${CONFIGURATION}" != "Debug" ]; then                │
│      exit 0   # Skip for Release/Archive                   │
│  fi                                                         │
│                                                             │
│  "${SRCROOT}/scripts/start-backend.sh"                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           start-backend.sh (Main Logic)                     │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │ 1. PATH Setup                                │          │
│  │    Add: ~/.cargo/bin, /usr/local/bin, etc.  │          │
│  │    Verify: cargo --version                   │          │
│  └──────────────────────────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────┐          │
│  │ 2. Check Existing Backend                   │          │
│  │    if PID file exists && process alive:     │          │
│  │        Verify health check                  │          │
│  │        if OK: exit 0 (already running)      │          │
│  │        if BAD: kill and restart             │          │
│  └──────────────────────────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────┐          │
│  │ 3. Port Cleanup                             │          │
│  │    if port 8080 in use:                     │          │
│  │        kill -9 $(lsof -ti:8080)             │          │
│  └──────────────────────────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────┐          │
│  │ 4. Build Backend                            │          │
│  │    cd ../                                   │          │
│  │    cargo build --bin ralph-mobile-server   │          │
│  │                 --release                   │          │
│  └──────────────────────────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────┐          │
│  │ 5. Start Backend (Background)               │          │
│  │    cargo run --bin ralph-mobile-server     │          │
│  │              --release                      │          │
│  │              > .ralph-backend.log 2>&1 &    │          │
│  │    Save PID to .ralph-backend-pid           │          │
│  └──────────────────────────────────────────────┘          │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────┐          │
│  │ 6. Health Check Loop (max 10s)              │          │
│  │    for i in 1..10:                          │          │
│  │        curl http://127.0.0.1:8080/health    │          │
│  │        if success: exit 0                   │          │
│  │        sleep 1                               │          │
│  │    FAIL: kill backend, show logs            │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (SUCCESS)
┌─────────────────────────────────────────────────────────────┐
│                    Backend Running                          │
│                                                             │
│  Process: cargo run ralph-mobile-server (PID in file)      │
│  Listening: http://127.0.0.1:8080                          │
│  Endpoints:                                                 │
│    GET /health           → "OK"                            │
│    GET /api/sessions     → JSON array of sessions          │
│    GET /api/sessions/:id → Session details                 │
│    GET /api/configs      → Available configs               │
│    POST /api/sessions    → Start new session               │
│    ...                                                      │
│                                                             │
│  Log: .ralph-backend.log                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Xcode Build Continues                       │
│                                                             │
│  ✓ Run Script: "Start Ralph Backend" completed            │
│  ▶ Compile Sources (now proceeds)                          │
│  ▶ Link Binary                                             │
│  ▶ Code Signing                                            │
│  ✓ Build Succeeded                                         │
│                                                             │
│  App launches in Simulator with backend ready!             │
└─────────────────────────────────────────────────────────────┘
```

## File Flow

```
ios/
├── RalphMobile.xcodeproj/
│   └── project.pbxproj
│       └── [Build Phase: Run Script]
│           └─> Calls: scripts/xcode-prebuild.sh
│
├── scripts/
│   ├── xcode-prebuild.sh          [1. Entry point from Xcode]
│   │   └─> if Debug: call start-backend.sh
│   │
│   ├── start-backend.sh            [2. Main startup logic]
│   │   ├─> Check existing backend
│   │   ├─> Build backend
│   │   ├─> Start in background
│   │   └─> Wait for health check
│   │
│   ├── stop-backend.sh             [Manual cleanup]
│   │   ├─> Kill process by PID
│   │   ├─> Kill process on port
│   │   └─> Remove PID file
│   │
│   └── backend                     [CLI wrapper]
│       └─> Commands: start|stop|status|logs|restart|clean
│
├── .ralph-backend-pid              [Generated: process ID]
├── .ralph-backend.log              [Generated: stdout/stderr]
└── .gitignore                      [Excludes generated files]

../crates/ralph-mobile-server/
└── src/
    └── main.rs                     [Backend server code]
```

## Execution Timeline

```
Time  Event
─────────────────────────────────────────────────────────────
0.0s  User: Cmd+R in Xcode
0.1s  Xcode: Start build process
0.2s  Xcode: Execute Run Script phase
      ├─> xcode-prebuild.sh checks CONFIGURATION=Debug ✓
      └─> Calls start-backend.sh

0.3s  start-backend.sh: Check existing backend
      ├─> Read .ralph-backend-pid
      ├─> PID not found or stale → continue
      └─> Port 8080 available ✓

0.5s  start-backend.sh: Build backend
      └─> cargo build --release (incremental: ~3s)

3.5s  start-backend.sh: Start backend
      ├─> cargo run --release > .ralph-backend.log &
      ├─> PID 12345 → .ralph-backend-pid
      └─> Begin health check loop

3.6s  Health check attempt 1: curl http://127.0.0.1:8080/health
      └─> Connection refused (server still starting)

4.6s  Health check attempt 2: curl http://127.0.0.1:8080/health
      └─> Connection refused

5.6s  Health check attempt 3: curl http://127.0.0.1:8080/health
      └─> Success! HTTP 200 "OK"

5.7s  start-backend.sh: Exit 0 (success)
      └─> Xcode: Run Script phase complete

5.8s  Xcode: Continue with Compile Sources
      ├─> Compile Swift files
      ├─> Link binary
      └─> Code signing

12.0s Build complete
      └─> Launch app in Simulator

12.5s App running + Backend running
      ├─> App connects to http://127.0.0.1:8080
      ├─> Fetches sessions from API
      └─> Ready for use!
```

## Process Lifecycle

```
┌────────────────┐
│ Xcode launched │
└────────┬───────┘
         │
         ▼
┌────────────────┐    Cmd+R
│  User builds   ├──────────┐
└────────┬───────┘          │
         │                  │
         ▼                  ▼
┌────────────────┐    ┌─────────────────┐
│ Backend starts │    │ Xcode compiles  │
│   (PID saved)  │    │  Swift sources  │
└────────┬───────┘    └────────┬────────┘
         │                     │
         ▼                     ▼
   ┌──────────┐          ┌──────────┐
   │ Health   │          │   App    │
   │  check   │          │  binary  │
   └────┬─────┘          └────┬─────┘
        │                     │
        ▼                     ▼
   ┌──────────┐          ┌──────────┐
   │ Backend  │◀─────────│   App    │
   │ running  │  HTTP    │ running  │
   │ :8080    │          │          │
   └──────────┘          └──────────┘
        │                     │
        │                     │
        ├─────────────────────┤
        │  Persist until...   │
        └─────────────────────┘
                 │
                 ▼
         User quits Xcode
         or runs ./scripts/backend stop
                 │
                 ▼
         ┌───────────────┐
         │ Backend stops │
         │ (PID removed) │
         └───────────────┘
```

## Decision Tree

```
                    [Xcode Build Started]
                            │
                            ▼
                  ┌─────────────────┐
                  │ Configuration?  │
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
        [Debug]       [Release]      [Archive]
            │              │              │
            ▼              │              │
    [Run script]           └──────┬───────┘
            │                     │
            ▼                     ▼
   ┌────────────────┐      [Skip script]
   │ Backend check  │             │
   └───────┬────────┘             │
           │                      │
     ┌─────┴─────┐                │
     ▼           ▼                │
[Running?]  [Not running]         │
     │           │                │
     ▼           ▼                │
[Health OK?] [Start new]          │
     │           │                │
 ┌───┴───┐       ▼                │
 ▼       ▼   [Build + Run]        │
[OK]  [FAIL]     │                │
 │       │       ▼                │
 │       └──>[Restart]            │
 │              │                 │
 └──────────────┴─────────────────┤
                │                 │
                ▼                 ▼
         [Continue build]  [Continue build]
                │                 │
                └────────┬────────┘
                         │
                         ▼
                  [Compile Swift]
                         │
                         ▼
                    [Link Binary]
                         │
                         ▼
                   [Launch App]
```

## Component Interaction

```
┌────────────────────────────────────────────────────────┐
│                    Developer Machine                    │
│                                                         │
│  ┌──────────┐         ┌─────────────┐                 │
│  │  Xcode   │────────▶│ Build Phase │                 │
│  │          │         │   Scripts   │                 │
│  └──────────┘         └──────┬──────┘                 │
│       │                      │                         │
│       │                      ▼                         │
│       │              ┌──────────────┐                  │
│       │              │ start-backend│                  │
│       │              │     .sh      │                  │
│       │              └──────┬───────┘                  │
│       │                     │                          │
│       │                     ▼                          │
│       │              ┌──────────────┐                  │
│       │              │    Cargo     │                  │
│       │              │    Build     │                  │
│       │              └──────┬───────┘                  │
│       │                     │                          │
│       │                     ▼                          │
│       │         ┌────────────────────────┐             │
│       │         │ ralph-mobile-server    │             │
│       │         │   (Background Process)  │             │
│       │         │   PID → .ralph-backend │             │
│       │         │         -pid            │             │
│       │         └────────┬───────────────┘             │
│       │                  │                             │
│       │                  │ HTTP :8080                  │
│       │                  ▼                             │
│       │         ┌────────────────────────┐             │
│       │         │   REST API + SSE       │             │
│       │         │   Endpoints            │             │
│       │         └────────┬───────────────┘             │
│       │                  │                             │
│       ▼                  ▼                             │
│  ┌──────────┐    ┌──────────────┐                     │
│  │   iOS    │◀───│  RalphAPI    │                     │
│  │   App    │    │   Client     │                     │
│  │(Simulator)│    │  (URLSession)│                     │
│  └──────────┘    └──────────────┘                     │
│       │                                                │
│       ▼                                                │
│  ┌──────────────────────────────┐                     │
│  │  SwiftUI Views               │                     │
│  │  - SidebarView (sessions)    │                     │
│  │  - UnifiedRalphView (detail) │                     │
│  │  - SettingsView (config)     │                     │
│  └──────────────────────────────┘                     │
└────────────────────────────────────────────────────────┘
```

## State Management

```
┌─────────────────────────────────────────────────────────┐
│                  Filesystem State                        │
│                                                          │
│  ┌────────────────────┐       ┌────────────────────┐   │
│  │ .ralph-backend-pid │       │ .ralph-backend.log │   │
│  ├────────────────────┤       ├────────────────────┤   │
│  │ 12345              │       │ Server started     │   │
│  │                    │       │ Listening on :8080 │   │
│  │ Written by:        │       │ ...                │   │
│  │ start-backend.sh   │       │                    │   │
│  │                    │       │ Written by:        │   │
│  │ Read by:           │       │ cargo run (stdout) │   │
│  │ - start-backend.sh │       │                    │   │
│  │ - stop-backend.sh  │       │ Read by:           │   │
│  │ - backend status   │       │ - backend logs     │   │
│  └────────────────────┘       └────────────────────┘   │
│           ▲                            ▲                │
│           │                            │                │
│           └────────────┬───────────────┘                │
│                        │                                │
│               ┌────────▼────────┐                       │
│               │  Backend        │                       │
│               │  Process        │                       │
│               │  (ralph-mobile- │                       │
│               │   server)       │                       │
│               └─────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## Error Paths

```
[Start Backend Script]
        │
        ├─> cargo not found
        │   └─> EXIT 1 "Install Rust"
        │
        ├─> Port 8080 in use
        │   ├─> kill -9 process
        │   └─> Continue
        │
        ├─> Build fails
        │   ├─> Show last 5 lines
        │   └─> EXIT 1 "Build failed"
        │
        ├─> Backend crashes on start
        │   ├─> PID invalid after 1s
        │   ├─> Show .ralph-backend.log
        │   └─> EXIT 1 "Crashed"
        │
        └─> Health check timeout (10s)
            ├─> kill backend
            ├─> tail -20 .ralph-backend.log
            └─> EXIT 1 "Failed to start"
```

## Success Criteria

For backend to be considered "ready":

1. ✅ Process is alive (ps -p $PID)
2. ✅ Port 8080 is bound (lsof -i:8080)
3. ✅ Health endpoint responds (GET /health → 200 "OK")
4. ✅ Within timeout window (10 seconds)

All four must pass for script to exit 0 and allow Xcode to continue.
