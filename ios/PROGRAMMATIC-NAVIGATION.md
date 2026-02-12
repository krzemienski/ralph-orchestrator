# Programmatic Navigation for RalphMobile

## Overview

RalphMobile now supports programmatic navigation via UserDefaults, allowing automated testing and validation without requiring touch interaction.

## Usage

Set the `navigateTo` UserDefault before launching the app:

```bash
UDID="23859335-3786-4AB4-BE26-9EC0BD8D0B57"  # Your simulator UDID

# Set navigation target
xcrun simctl spawn "$UDID" defaults write dev.ralph.RalphMobile navigateTo -string "<target>"

# Launch app
xcrun simctl launch "$UDID" dev.ralph.RalphMobile

# Wait for navigation
sleep 2

# Capture screenshot
xcrun simctl io "$UDID" screenshot /path/to/screenshot.png
```

## Supported Navigation Targets

| Target | Description | Example |
|--------|-------------|---------|
| `settings` | Navigate to Settings view | `"settings"` |
| `library` | Navigate to Library view | `"library"` |
| `skills` | Navigate to Skills view | `"skills"` |
| `host` | Navigate to Host Metrics view | `"host"` |
| `new-ralph` | Open Create Ralph wizard | `"new-ralph"` |
| `session/<id>` | Navigate to specific session | `"session/8d56f69860f36e62"` |

## Examples

### Navigate to Settings
```bash
xcrun simctl spawn "$UDID" defaults write dev.ralph.RalphMobile navigateTo -string "settings"
xcrun simctl launch "$UDID" dev.ralph.RalphMobile
sleep 2
xcrun simctl io "$UDID" screenshot /tmp/settings.png
```

### Navigate to Session
```bash
SESSION_ID="8d56f69860f36e62"
xcrun simctl spawn "$UDID" defaults write dev.ralph.RalphMobile navigateTo -string "session/${SESSION_ID}"
xcrun simctl launch "$UDID" dev.ralph.RalphMobile
sleep 3
xcrun simctl io "$UDID" screenshot /tmp/session-detail.png
```

### Open Create Wizard
```bash
xcrun simctl spawn "$UDID" defaults write dev.ralph.RalphMobile navigateTo -string "new-ralph"
xcrun simctl launch "$UDID" dev.ralph.RalphMobile
sleep 2
xcrun simctl io "$UDID" screenshot /tmp/wizard.png
```

## Implementation Details

### Files Modified

1. **RalphMobileApp.swift**
   - Added `NavigationManager` properties for global view selection and wizard state
   - Extended `NavigationManager` with methods for Skills and Host navigation

2. **MainNavigationView.swift**
   - Added `.onAppear` handler to check `navigateTo` UserDefault
   - Added `handleProgrammaticNavigationOnAppear()` function
   - Added `.onChange` observers to sync with `NavigationManager` state
   - Refactored view modifiers to avoid compiler type-checking timeout

### Navigation Flow

1. App launches
2. `MainNavigationView.onAppear` executes
3. Checks for `navigateTo` UserDefault
4. If found, clears the default (to prevent re-navigation)
5. Waits 0.3s for view hierarchy to initialize
6. Sets appropriate state (`selectedGlobalView`, `selectedSession`, `showCreateRalph`)
7. For iPhone (compact size class), appends to `navigationPath` for push navigation
8. For iPad (regular size class), selection triggers detail view update

### Notes

- The `navigateTo` default is cleared immediately after reading to prevent re-navigation on subsequent launches
- A 0.3s delay ensures the view hierarchy is ready before navigation
- Session navigation fetches the session list first to ensure the session exists
- Works on both iPhone (NavigationStack) and iPad (NavigationSplitView) layouts

## Validation Evidence

Screenshots demonstrating all navigation modes:

- `/tmp/nav-test-settings.png` - Settings view
- `/tmp/nav-test-skills.png` - Skills view
- `/tmp/nav-test-host.png` - Host Metrics view
- `/tmp/nav-test-library.png` - Library view
- `/tmp/nav-test-new-ralph.png` - Create Ralph wizard
- `/tmp/nav-test-session.png` - Session detail view

All navigation targets verified working on iPhone 17 Pro Max simulator (iOS 26.2).
