# Adding Backend Auto-Start to Xcode

Follow these steps to enable automatic backend startup when building RalphMobile.

## Step-by-Step Instructions

### 1. Open Xcode Project

```bash
cd /Users/nick/Desktop/ralph-orchestrator/ios
open RalphMobile.xcodeproj
```

### 2. Select RalphMobile Target

1. In Xcode, click on the **RalphMobile** project in the navigator (blue icon at top)
2. In the main editor, ensure **RalphMobile** target is selected (not RalphMobileTests or RalphMobileUITests)

### 3. Go to Build Phases

1. Click on the **Build Phases** tab at the top
2. You'll see sections like "Dependencies", "Compile Sources", "Link Binary", etc.

### 4. Add New Run Script Phase

1. Click the **"+"** button at the top left (above the phase list)
2. Select **"New Run Script Phase"**
3. A new section called "Run Script" appears at the bottom

### 5. Move Run Script Before Compile Sources

1. **Drag** the new "Run Script" phase
2. **Drop** it above the "Compile Sources" phase
3. Order should be:
   ```
   - Dependencies
   - Run Script          ← Your new phase here
   - Compile Sources
   - Link Binary
   - ...
   ```

### 6. Configure the Run Script

1. Click the **disclosure triangle** next to "Run Script" to expand it
2. In the script text area, paste exactly:
   ```bash
   "${SRCROOT}/scripts/xcode-prebuild.sh"
   ```
3. Leave "Shell" as `/bin/sh`
4. Leave "Based on dependency analysis" **unchecked**

### 7. Rename the Phase (Optional)

1. Double-click on "Run Script"
2. Rename it to: `Start Ralph Backend (Debug Only)`

### 8. Verify Configuration

Your Run Script phase should have:

| Setting | Value |
|---------|-------|
| Shell | `/bin/sh` |
| Script | `"${SRCROOT}/scripts/xcode-prebuild.sh"` |
| Show environment variables | Unchecked (default) |
| Run script only when installing | Unchecked (default) |
| Based on dependency analysis | Unchecked (default) |
| Input Files | (empty) |
| Output Files | (empty) |

### 9. Save and Test

1. Press **Cmd+S** to save the project
2. Close Xcode (Cmd+Q)
3. Reopen the project
4. Build with **Cmd+B**

## Expected Build Output

When you build, you should see in the build log:

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
✓ Configure iOS app with: http://127.0.0.1:8080
```

## Viewing Build Phase Output

### During Build
- Look for the "Run Script" phase in the build progress bar
- Check the Report Navigator (Cmd+9) → Latest build

### After Build
1. Open Report Navigator (Cmd+9)
2. Select latest build
3. Expand "RalphMobile" target
4. Click on "Start Ralph Backend (Debug Only)"
5. View full script output

## Troubleshooting

### Script not running?

**Check script is executable:**
```bash
ls -la scripts/xcode-prebuild.sh
# Should show: -rwxr-xr-x
```

If not:
```bash
chmod +x scripts/xcode-prebuild.sh
chmod +x scripts/start-backend.sh
chmod +x scripts/stop-backend.sh
chmod +x scripts/backend
```

### Permission denied error?

**Xcode may block script execution.**

Solution:
1. Open **System Settings** → **Privacy & Security**
2. Scroll down to "Developer Tools"
3. Ensure Xcode is allowed

### Backend doesn't start?

**Verify Rust is installed:**
```bash
cargo --version
# Should output: cargo 1.x.x
```

If not installed:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then restart Xcode.

### Build phase runs but nothing happens?

**Check configuration:**
1. Ensure you're building **Debug** configuration
   - Product → Scheme → Edit Scheme → Run → Build Configuration → Debug
2. Script only runs for Debug builds (skips Release/Archive)

### Build log missing script output?

**View the raw build log:**
1. Open Xcode build folder:
   ```bash
   open ~/Library/Developer/Xcode/DerivedData/RalphMobile-*/Logs/Build/
   ```
2. Open the latest `.xcactivitylog` file in Console.app
3. Search for "Ralph Backend"

## Manual Testing

Before relying on Xcode integration, test manually:

```bash
# Test script directly
cd /Users/nick/Desktop/ralph-orchestrator/ios
export SRCROOT="$(pwd)"
./scripts/xcode-prebuild.sh

# Should output:
# 🚀 Ralph Backend Auto-Start
# ✓ Backend started...

# Verify backend is running
./scripts/backend status
```

## Advanced Configuration

### Change when script runs

Edit `scripts/xcode-prebuild.sh` line 5:

```bash
# Current: Only Debug builds
if [ "${CONFIGURATION}" != "Debug" ]; then
    exit 0
fi

# Option 1: All builds
# (remove the if block)

# Option 2: Debug and Release (not Archive)
if [ "${CONFIGURATION}" = "Archive" ]; then
    exit 0
fi
```

### Add input/output files for caching

If you want Xcode to skip the script when nothing changed:

**Input Files:**
```
$(SRCROOT)/scripts/start-backend.sh
$(SRCROOT)/scripts/xcode-prebuild.sh
```

**Output Files:**
```
$(SRCROOT)/.ralph-backend-pid
```

This makes Xcode skip the script if inputs haven't changed and output exists.

## Removing the Integration

To disable auto-start:

1. Open Xcode → RalphMobile target → Build Phases
2. Find "Start Ralph Backend" phase
3. Delete it (select and press backspace)
4. Save (Cmd+S)

Or temporarily disable:
1. Select the phase
2. Uncheck "Run script only when installing"
3. Check "Run script only when installing" (effectively disables it for regular builds)

## See Also

- [QUICK-START.md](../QUICK-START.md) - Getting started guide
- [README.md](README.md) - Full script documentation
- [BACKEND-AUTO-START-SUMMARY.md](../BACKEND-AUTO-START-SUMMARY.md) - Implementation details
