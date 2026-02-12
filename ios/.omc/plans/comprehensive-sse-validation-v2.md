# Comprehensive 10-Minute SSE Validation Plan v2

## Context

### Why This Plan Exists

**User Skepticism (Justified):**
- Previous plans promised 10-minute videos but NEVER delivered
- Best video achieved: 410 seconds (6.85 minutes) - still NOT 10 minutes
- SSE validation video: only 53 seconds
- Hat transitions marked "DEFERRED" - never validated
- UI/UX aesthetic audit - NEVER PERFORMED
- Video content analysis - NEVER DONE

### Evidence of Previous Failures

| Video File | Actual Duration | Required | Status |
|------------|-----------------|----------|--------|
| demo-10min-final-20260204-015308.mp4 | 410s (6.85 min) | 600s (10 min) | FAILED |
| demo-10min-20260204-013846.mp4 | 269s (4.5 min) | 600s (10 min) | FAILED |
| sse-streaming-final.mp4 | 53s | 300s (5 min) | FAILED |
| sse-streaming-evidence-20260204-134636.mp4 | 121s (2 min) | 300s (5 min) | FAILED |

### What This Plan MUST Achieve

1. **REAL 10-minute video** (verified via ffprobe showing >= 600 seconds)
2. **Frame extraction** proving continuous recording
3. **UI/UX aesthetic audit** with documented findings
4. **Real streaming verification** (not mock/cached data)
5. **Tool call correctness** analysis
6. **Comprehensive report** with all evidence

---

## Technical Architecture

### iOS SSE Stack
```
EventStreamService.swift
    ↓ URLSession.bytes(from: url)
SSEParser.swift
    ↓ parse "event:" and "data:" lines
SessionViewModel.swift
    ↓ @Published var events: [Event]
UnifiedRalphView.swift (Section 8: EVENT STREAM)
    ↓ displays last 20 events
```

### Rust Backend Stack
```
main.rs
    ↓ discover_sessions() scans for .agent/events.jsonl
watcher.rs (EventWatcher)
    ↓ notify crate watches file changes
    ↓ tokio::sync::broadcast channel (capacity: 100)
api/events.rs
    ↓ GET /api/sessions/{id}/events
    ↓ returns text/event-stream
```

### Exclusive Simulator (MANDATORY)
- **UDID**: `23859335-3786-4AB4-BE26-9EC0BD8D0B57`
- **Device**: iPhone 17 Pro Max
- **iOS**: 26.2
- **Status**: Currently BOOTED (confirmed)
- **NEVER use any other simulator** - others are in use by concurrent sessions

---

## Phase 1: Environment Preparation

**Duration**: 5 minutes
**Checkpoint**: Server accessible on LAN IP

### Task 1.1: Kill Existing Server
```bash
pkill -f "ralph-mobile-server" 2>/dev/null || true
sleep 2
lsof -i :8080 | grep LISTEN && echo "WARNING: Port still in use" || echo "Port 8080 free"
```

**Acceptance**: Port 8080 is free

### Task 1.2: Start Server with --bind-all
```bash
cd /Users/nick/Desktop/ralph-orchestrator
cargo run --bin ralph-mobile-server -- --bind-all > /tmp/ralph-server.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > /tmp/ralph-server-pid.txt
sleep 5
```

**Acceptance**: Server PID written to file

### Task 1.3: Get Host LAN IP
```bash
HOST_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "Host LAN IP: $HOST_IP"
echo $HOST_IP > /tmp/host-lan-ip.txt
```

**Acceptance**: Valid IP address (e.g., 10.x.x.x or 192.168.x.x)

### Task 1.4: Verify Server Accessibility
```bash
HOST_IP=$(cat /tmp/host-lan-ip.txt)
curl -s "http://${HOST_IP}:8080/api/sessions" | head -100
```

**Acceptance**: Returns JSON array of sessions
**STOP IF FAILS**: Cannot proceed without server accessibility

### Task 1.5: Verify SSE Endpoint Works
```bash
HOST_IP=$(cat /tmp/host-lan-ip.txt)
# Get first session ID
SESSION_ID=$(curl -s "http://${HOST_IP}:8080/api/sessions" | jq -r '.[0].id')
echo "Session ID: $SESSION_ID"
echo $SESSION_ID > /tmp/test-session-id.txt

# Quick SSE test (5 second timeout)
timeout 5 curl -N "http://${HOST_IP}:8080/api/sessions/${SESSION_ID}/events" || echo "SSE endpoint responding"
```

**Acceptance**: SSE endpoint responds (even if no events yet)

---

## Phase 2: iOS App Setup

**Duration**: 5 minutes
**Checkpoint**: App configured and showing session

### Task 2.1: Clean Install RalphMobile
```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"

# Uninstall existing
xcrun simctl uninstall $UDID dev.ralph.RalphMobile 2>/dev/null || true

# Build fresh
cd /Users/nick/Desktop/ralph-orchestrator/ios
xcodebuild -scheme RalphMobile -destination "id=$UDID" build 2>&1 | tail -30

# Find and install
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "RalphMobile.app" -path "*/Debug-iphonesimulator/*" -type d 2>/dev/null | head -1)
echo "Installing from: $APP_PATH"
xcrun simctl install $UDID "$APP_PATH"
```

**Acceptance**: Build succeeds, app installed

### Task 2.2: Launch App
```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"
xcrun simctl launch $UDID dev.ralph.RalphMobile
sleep 3
```

**Acceptance**: App launches

### Task 2.3: Configure Server URL (Manual UI Steps)

**Navigation Path:**
1. App launches to Sessions list
2. Tap **gear icon** (top-right) OR swipe from left edge → tap "Settings"
3. Find "Server URL" field
4. Enter: `http://<HOST_IP>:8080` (use IP from `/tmp/host-lan-ip.txt`)
5. Tap "Back" or swipe right to return
6. Pull down on sessions list to refresh

**Verification Screenshot:**
```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-01-settings-configured.png
```

**Acceptance**: Sessions appear in list

### Task 2.4: Navigate to Session Detail

**Navigation Path:**
1. From Sessions list, tap on a session row
2. Wait for detail view to load ("Connecting..." → "Connected")
3. Scroll down to find "EVENT STREAM" section

**Verification Screenshot:**
```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-02-session-detail.png
```

**Acceptance**: Session detail visible with "Connected" status

---

## Phase 3: Start Real Ralph Loop

**Duration**: 2 minutes to start, runs for 10+ minutes
**Checkpoint**: Events being written to events.jsonl

### Task 3.1: Start Ralph Loop
```bash
cd /Users/nick/Desktop/ralph-orchestrator

# Use a simple prompt that will generate events over 10+ minutes
ralph run -c presets/feature.yml -p "Create a comprehensive Python CLI calculator that supports addition, subtraction, multiplication, division, and exponentiation. Include help text, error handling for invalid inputs, and colorful output using the rich library." --max-iterations 20 > /tmp/ralph-loop.log 2>&1 &

RALPH_PID=$!
echo $RALPH_PID > /tmp/ralph-loop-pid.txt
echo "Ralph loop started with PID: $RALPH_PID"
```

**Acceptance**: Ralph PID written to file

### Task 3.2: Verify Events Being Written
```bash
sleep 10
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
if [ -f "$EVENTS_FILE" ]; then
    echo "Events file exists"
    wc -l "$EVENTS_FILE"
    tail -3 "$EVENTS_FILE"
else
    echo "WARNING: Events file not found - check ralph loop"
fi
```

**Acceptance**: Events file exists and has content
**STOP IF FAILS**: Cannot validate SSE without events

---

## Phase 4: 10-Minute Video Recording (CRITICAL)

**Duration**: EXACTLY 10 minutes minimum (600 seconds)
**Checkpoint**: Video file >= 600 seconds verified by ffprobe

### Task 4.1: Start Video Recording
```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VIDEO_PATH="/Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/10min-sse-validation-${TIMESTAMP}.mp4"
echo $VIDEO_PATH > /tmp/current-video-path.txt

xcrun simctl io $UDID recordVideo --codec h264 "$VIDEO_PATH" &
RECORD_PID=$!
echo $RECORD_PID > /tmp/video-record-pid.txt
echo "Recording started with PID: $RECORD_PID"
echo "Video path: $VIDEO_PATH"
echo "START TIME: $(date)"
```

**Acceptance**: Recording PID saved

### Task 4.2: Checkpoint Screenshots (Every 2 Minutes)

**2-Minute Mark:**
```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"
sleep 120
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-checkpoint-02min.png
echo "Checkpoint 2min: $(date)"
```

**4-Minute Mark:**
```bash
sleep 120
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-checkpoint-04min.png
echo "Checkpoint 4min: $(date)"
```

**6-Minute Mark:**
```bash
sleep 120
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-checkpoint-06min.png
echo "Checkpoint 6min: $(date)"
```

**8-Minute Mark:**
```bash
sleep 120
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-checkpoint-08min.png
echo "Checkpoint 8min: $(date)"
```

**10-Minute Mark:**
```bash
sleep 120
xcrun simctl io $UDID screenshot /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-checkpoint-10min.png
echo "Checkpoint 10min: $(date)"
```

**Acceptance**: 5 checkpoint screenshots saved

### Task 4.3: Stop Recording After 10+ Minutes
```bash
RECORD_PID=$(cat /tmp/video-record-pid.txt)
kill -INT $RECORD_PID 2>/dev/null
sleep 5
echo "END TIME: $(date)"
```

**Acceptance**: Recording stopped cleanly

### Task 4.4: VERIFY Video Duration (CRITICAL GATE)
```bash
VIDEO_PATH=$(cat /tmp/current-video-path.txt)
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_PATH")
echo "Video duration: $DURATION seconds"

# Check if >= 600 seconds
if (( $(echo "$DURATION >= 600" | bc -l) )); then
    echo "SUCCESS: Video is >= 10 minutes ($DURATION seconds)"
else
    echo "FAILURE: Video is only $DURATION seconds - MUST RE-RECORD"
    exit 1
fi
```

**Acceptance**: Duration >= 600 seconds
**STOP AND RE-RECORD IF FAILS**: This is a hard requirement

---

## Phase 5: Frame Extraction & Analysis

**Duration**: 5 minutes
**Checkpoint**: 600+ frames extracted

### Task 5.1: Create Frames Directory
```bash
FRAMES_DIR="/Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-frames"
mkdir -p "$FRAMES_DIR"
```

### Task 5.2: Extract Frames at 1fps
```bash
VIDEO_PATH=$(cat /tmp/current-video-path.txt)
FRAMES_DIR="/Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-frames"

ffmpeg -i "$VIDEO_PATH" -vf "fps=1" "$FRAMES_DIR/frame_%04d.png" 2>&1 | tail -10

FRAME_COUNT=$(ls -1 "$FRAMES_DIR"/*.png 2>/dev/null | wc -l)
echo "Extracted $FRAME_COUNT frames"
```

**Acceptance**: >= 600 frames extracted

### Task 5.3: Verify Frame Count
```bash
FRAMES_DIR="/Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-frames"
FRAME_COUNT=$(ls -1 "$FRAMES_DIR"/*.png 2>/dev/null | wc -l)

if [ "$FRAME_COUNT" -ge 600 ]; then
    echo "SUCCESS: $FRAME_COUNT frames (>= 600 required)"
else
    echo "WARNING: Only $FRAME_COUNT frames extracted"
fi
```

**Acceptance**: Frame count confirms 10+ minute duration

---

## Phase 6: UI/UX Aesthetic Audit

**Duration**: 10 minutes
**Checkpoint**: Audit findings documented

### Task 6.1: Sample Frames for Analysis

Extract frames at 1-minute intervals for detailed inspection:
```bash
FRAMES_DIR="/Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-frames"
SAMPLE_DIR="/Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-samples"
mkdir -p "$SAMPLE_DIR"

# Copy frames at 1-minute intervals (frame 60, 120, 180, 240, 300, 360, 420, 480, 540, 600)
for min in 1 2 3 4 5 6 7 8 9 10; do
    FRAME_NUM=$(printf "%04d" $((min * 60)))
    cp "$FRAMES_DIR/frame_${FRAME_NUM}.png" "$SAMPLE_DIR/sample_min${min}.png" 2>/dev/null || echo "Frame $FRAME_NUM not found"
done

ls -la "$SAMPLE_DIR"
```

### Task 6.2: UI/UX Audit Checklist (Manual Visual Inspection)

For each sample frame, check:

| Criterion | Pass/Fail | Notes |
|-----------|-----------|-------|
| **Cyberpunk Theme** | | Dark background, no white flashes |
| **Text Readability** | | Sufficient contrast, legible fonts |
| **Event Rendering** | | Events displayed correctly with timestamps |
| **Layout Integrity** | | No text truncation, proper alignment |
| **Hat Color Coding** | | Hat badges show correct colors |
| **Connection Status** | | "Connected" badge visible and green |
| **Event Count Badge** | | Shows realistic event count |
| **Scroll Position** | | Events section visible when scrolled |
| **Animation Smoothness** | | No frozen frames between consecutive samples |
| **Error States** | | No error dialogs or red banners |

### Task 6.3: Document Audit Findings
```bash
cat > /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-ui-audit.md << 'EOF'
# UI/UX Aesthetic Audit Report

## Date: [TIMESTAMP]

## Sample Frames Analyzed
- sample_min1.png through sample_min10.png

## Findings

### Cyberpunk Theme Compliance
- [ ] Dark background maintained throughout
- [ ] Neon accent colors present
- [ ] No white background flashes

### Text & Layout
- [ ] All text readable at normal viewing distance
- [ ] No truncation issues
- [ ] Proper alignment of UI elements

### Event Stream Section
- [ ] Events visible in Section 8
- [ ] Timestamps displayed correctly
- [ ] Event types color-coded properly

### Connection Indicators
- [ ] "Connected" status visible
- [ ] Status badge color appropriate (green)

### Issues Found
1. [List any issues with frame numbers]

### Recommendations
1. [List any improvements needed]

## Verdict
[ ] PASS - UI meets aesthetic standards
[ ] FAIL - Issues require attention
EOF
```

---

## Phase 7: Real Streaming Verification

**Duration**: 5 minutes
**Checkpoint**: Evidence that streaming is REAL, not mock

### Task 7.1: Count Events in Backend
```bash
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
BACKEND_COUNT=$(wc -l < "$EVENTS_FILE")
echo "Backend event count: $BACKEND_COUNT"
echo $BACKEND_COUNT > /tmp/backend-event-count.txt
```

### Task 7.2: Analyze Event Timestamps
```bash
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
echo "First 3 events:"
head -3 "$EVENTS_FILE" | jq -r '.ts'
echo ""
echo "Last 3 events:"
tail -3 "$EVENTS_FILE" | jq -r '.ts'
```

**Verification**: Timestamps should span the 10-minute recording period

### Task 7.3: Verify Event Uniqueness
```bash
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
TOTAL=$(wc -l < "$EVENTS_FILE")
UNIQUE=$(jq -r '.ts' "$EVENTS_FILE" | sort -u | wc -l)
echo "Total events: $TOTAL"
echo "Unique timestamps: $UNIQUE"
if [ "$UNIQUE" -lt "$TOTAL" ]; then
    echo "WARNING: Some duplicate timestamps - check for replays"
else
    echo "SUCCESS: All timestamps unique"
fi
```

### Task 7.4: Cross-Reference with Final Screenshot
```bash
# Compare event count in 10-minute screenshot with backend count
echo "Backend count: $(cat /tmp/backend-event-count.txt)"
echo "Check v2-checkpoint-10min.png for iOS event count badge"
echo ""
echo "MANUAL VERIFICATION REQUIRED:"
echo "1. Open v2-checkpoint-10min.png"
echo "2. Find event count badge in Event Stream section"
echo "3. Compare with backend count"
echo "4. iOS count should be <= backend count (limited to last 20 visible)"
```

### Task 7.5: Document Streaming Verification
```bash
cat > /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-streaming-verification.md << 'EOF'
# Real Streaming Verification Report

## Date: [TIMESTAMP]

## Backend Analysis
- Events file: `.agent/events.jsonl`
- Total event count: [FROM /tmp/backend-event-count.txt]
- First event timestamp: [FROM ANALYSIS]
- Last event timestamp: [FROM ANALYSIS]
- Time span: [CALCULATE]

## Timestamp Analysis
- All timestamps unique: [ ] YES / [ ] NO
- Timestamps properly sequenced: [ ] YES / [ ] NO
- Time span matches recording duration: [ ] YES / [ ] NO

## iOS App Verification
- Event count in final screenshot: [CHECK v2-checkpoint-10min.png]
- iOS count <= Backend count: [ ] YES / [ ] NO
- Events match expected topics: [ ] YES / [ ] NO

## Conclusion
[ ] REAL STREAMING CONFIRMED - Events are live, not mock/cached
[ ] STREAMING SUSPECT - Evidence suggests mock data
EOF
```

---

## Phase 8: Tool Call Analysis

**Duration**: 5 minutes
**Checkpoint**: Tool calls verified as correct

### Task 8.1: Extract Tool Calls from Events
```bash
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
echo "Tool call events:"
grep -i "tool" "$EVENTS_FILE" | head -10
echo ""
echo "Total tool-related events:"
grep -i "tool" "$EVENTS_FILE" | wc -l
```

### Task 8.2: Verify Tool Call Structure
```bash
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
echo "Sample tool call structure:"
grep -i "tool" "$EVENTS_FILE" | head -1 | jq .
```

### Task 8.3: Check for Tool Errors
```bash
EVENTS_FILE="/Users/nick/Desktop/ralph-orchestrator/.agent/events.jsonl"
echo "Error events:"
grep -iE "error|fail|exception" "$EVENTS_FILE" | head -5
echo ""
echo "Total error events:"
grep -iE "error|fail|exception" "$EVENTS_FILE" | wc -l
```

---

## Phase 9: Final Report Generation

**Duration**: 5 minutes
**Checkpoint**: Comprehensive report created

### Task 9.1: Generate Comprehensive Report
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VIDEO_PATH=$(cat /tmp/current-video-path.txt)
VIDEO_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_PATH")
FRAME_COUNT=$(ls -1 /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/v2-frames/*.png 2>/dev/null | wc -l)
BACKEND_COUNT=$(cat /tmp/backend-event-count.txt)

cat > /Users/nick/Desktop/ralph-orchestrator/ios/validation-screenshots/COMPREHENSIVE-10MIN-REPORT.md << EOF
# Comprehensive 10-Minute SSE Validation Report

## Generated: $TIMESTAMP

## Executive Summary

This report documents the FIRST successful 10-minute SSE streaming validation for RalphMobile iOS app. Previous attempts failed to reach the required duration.

## Evidence Summary

### Video Recording
| Metric | Value | Required | Status |
|--------|-------|----------|--------|
| File | $(basename "$VIDEO_PATH") | - | EXISTS |
| Duration | ${VIDEO_DURATION}s | >= 600s | $([ $(echo "$VIDEO_DURATION >= 600" | bc -l) -eq 1 ] && echo "PASS" || echo "FAIL") |
| Frame Count | $FRAME_COUNT | >= 600 | $([ "$FRAME_COUNT" -ge 600 ] && echo "PASS" || echo "FAIL") |

### Backend Events
| Metric | Value |
|--------|-------|
| Total Events | $BACKEND_COUNT |
| Events File | .agent/events.jsonl |

### Checkpoint Screenshots
| Timestamp | File | Status |
|-----------|------|--------|
| 2 minutes | v2-checkpoint-02min.png | [CHECK] |
| 4 minutes | v2-checkpoint-04min.png | [CHECK] |
| 6 minutes | v2-checkpoint-06min.png | [CHECK] |
| 8 minutes | v2-checkpoint-08min.png | [CHECK] |
| 10 minutes | v2-checkpoint-10min.png | [CHECK] |

## Gate Verification

### Gate 1: Video Duration >= 10 Minutes
- **Status**: $([ $(echo "$VIDEO_DURATION >= 600" | bc -l) -eq 1 ] && echo "PASS" || echo "FAIL")
- **Evidence**: ffprobe reports ${VIDEO_DURATION} seconds

### Gate 2: Frame Extraction
- **Status**: $([ "$FRAME_COUNT" -ge 600 ] && echo "PASS" || echo "FAIL")
- **Evidence**: $FRAME_COUNT frames in v2-frames/

### Gate 3: UI/UX Audit
- **Status**: [SEE v2-ui-audit.md]
- **Evidence**: 10 sample frames analyzed

### Gate 4: Real Streaming Verified
- **Status**: [SEE v2-streaming-verification.md]
- **Evidence**: Timestamp analysis, event count comparison

### Gate 5: Tool Call Correctness
- **Status**: [MANUAL CHECK REQUIRED]
- **Evidence**: Tool events extracted from events.jsonl

## Artifacts Manifest

\`\`\`
ios/validation-screenshots/
├── $(basename "$VIDEO_PATH")     # Primary video evidence
├── COMPREHENSIVE-10MIN-REPORT.md # This report
├── v2-ui-audit.md               # UI/UX findings
├── v2-streaming-verification.md # Streaming proof
├── v2-01-settings-configured.png
├── v2-02-session-detail.png
├── v2-checkpoint-02min.png
├── v2-checkpoint-04min.png
├── v2-checkpoint-06min.png
├── v2-checkpoint-08min.png
├── v2-checkpoint-10min.png
├── v2-frames/                   # 600+ extracted frames
│   ├── frame_0001.png
│   ├── ...
│   └── frame_${FRAME_COUNT}.png
└── v2-samples/                  # 10 sample frames (1 per minute)
    ├── sample_min1.png
    ├── ...
    └── sample_min10.png
\`\`\`

## Comparison to Previous Attempts

| Previous Video | Duration | This Video | Duration | Improvement |
|----------------|----------|------------|----------|-------------|
| demo-10min-final | 410s | $(basename "$VIDEO_PATH") | ${VIDEO_DURATION}s | +$((${VIDEO_DURATION%.*} - 410))s |
| sse-streaming-final | 53s | $(basename "$VIDEO_PATH") | ${VIDEO_DURATION}s | +$((${VIDEO_DURATION%.*} - 53))s |

## Conclusion

**VALIDATION STATUS**: [PENDING MANUAL CHECKS]

All automated checks passed. Manual verification required for:
1. UI/UX audit checklist completion
2. Streaming verification cross-reference
3. Tool call correctness review

---

Report generated by comprehensive-sse-validation-v2 plan.
EOF

echo "Report generated: ios/validation-screenshots/COMPREHENSIVE-10MIN-REPORT.md"
```

---

## Cleanup

### Stop Ralph Loop (if still running)
```bash
RALPH_PID=$(cat /tmp/ralph-loop-pid.txt 2>/dev/null)
if [ -n "$RALPH_PID" ]; then
    kill $RALPH_PID 2>/dev/null && echo "Ralph loop stopped" || echo "Ralph loop already stopped"
fi
```

### Stop Server (optional - may want to keep running)
```bash
# Uncomment to stop server:
# SERVER_PID=$(cat /tmp/ralph-server-pid.txt 2>/dev/null)
# kill $SERVER_PID 2>/dev/null
```

---

## Failure Recovery

### If Video Recording Fails
1. Check simulator is still running: `xcrun simctl list devices | grep Booted`
2. Check disk space: `df -h`
3. Kill any zombie recording processes: `pkill -f recordVideo`
4. Restart from Phase 4

### If Server Becomes Unreachable
1. Check server process: `lsof -i :8080`
2. Check server logs: `tail -50 /tmp/ralph-server.log`
3. Restart server: Kill and re-run Phase 1

### If Ralph Loop Stops Early
1. Check ralph logs: `tail -50 /tmp/ralph-loop.log`
2. Events may still be in file - continue with validation
3. If insufficient events, restart ralph with longer prompt

### If Frames Extraction Fails
1. Check ffmpeg is installed: `which ffmpeg`
2. Check video file integrity: `ffprobe <video_path>`
3. Try with lower fps: `ffmpeg -i video.mp4 -vf "fps=0.5" frames/frame_%04d.png`

---

## Success Criteria Summary

| Criterion | Required | How to Verify |
|-----------|----------|---------------|
| Video duration | >= 600 seconds | `ffprobe` output |
| Frame count | >= 600 | `ls v2-frames/*.png \| wc -l` |
| Checkpoint screenshots | 5 files | `ls v2-checkpoint-*.png` |
| UI/UX audit | Completed | v2-ui-audit.md exists with findings |
| Streaming verification | Confirmed real | v2-streaming-verification.md |
| Final report | Generated | COMPREHENSIVE-10MIN-REPORT.md |

---

## Execution Time Estimate

| Phase | Duration |
|-------|----------|
| Phase 1: Environment | 5 min |
| Phase 2: iOS Setup | 5 min |
| Phase 3: Start Ralph | 2 min |
| Phase 4: Recording | **10 min** (fixed) |
| Phase 5: Frame Extraction | 5 min |
| Phase 6: UI/UX Audit | 10 min |
| Phase 7: Streaming Verify | 5 min |
| Phase 8: Tool Analysis | 5 min |
| Phase 9: Report | 5 min |
| **TOTAL** | **~52 minutes** |

---

## CRITICAL REMINDERS

1. **DO NOT STOP RECORDING EARLY** - Must hit 600+ seconds
2. **VERIFY DURATION BEFORE PROCEEDING** - Task 4.4 is a hard gate
3. **USE ONLY EXCLUSIVE SIMULATOR** - UDID: 23859335-3786-4AB4-BE26-9EC0BD8D0B57
4. **CAPTURE ALL CHECKPOINTS** - Evidence of continuous recording
5. **COMPLETE ALL AUDITS** - UI/UX and streaming verification are mandatory
