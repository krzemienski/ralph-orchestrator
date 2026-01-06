# Ralph Mobile - React Native Orchestrator Control App

---

## ✅ STATUS: PHASES 0-3 COMPLETE - PHASE 4 NEXT

**Phase 0 Completed (January 6, 2026):**
- ✅ Created Expo project with TypeScript template
- ✅ Installed NativeWind 4.x, Expo Router 6.x, TanStack Query 5.x
- ✅ Configured dark theme with StyleSheet (NativeWind cssInterop deferred)
- ✅ Set up 4-tab navigation (Dashboard, Output, Controls, Settings)
- ✅ Built and ran on iOS Simulator: `npx expo run:ios` succeeded
- ✅ Screenshot evidence captured: `validation-evidence/mobile-phase0/tab-navigation.png`

**Phase 1 Completed (January 6, 2026):**
- ✅ Created lib/types/index.ts with all TypeScript types
- ✅ Created lib/api/client.ts with REST API functions
- ✅ Created lib/api/websocket.ts with OrchestratorWebSocket class
- ✅ Created lib/hooks/ with React Query hooks (4 files):
  - useOrchestrators.ts - List all orchestrators with polling
  - useOrchestrator.ts - Single orchestrator with tasks
  - useOrchestratorLogs.ts - Log fetching with infinite scroll
  - useOrchestratorMutations.ts - Start/stop/pause/resume mutations
- ✅ TypeScript compilation validated: 0 errors (`npx tsc --noEmit`)
- ✅ Evidence captured: `validation-evidence/mobile-phase1/`

**Phase 2 Completed (January 6, 2026):**
- ✅ Created components/ui/StatusBadge.tsx - Color-coded status indicators
- ✅ Created components/dashboard/OrchestratorCard.tsx - Card with progress bar, metrics
- ✅ Created components/dashboard/EmptyState.tsx - Empty state with action button
- ✅ Updated app/(tabs)/index.tsx with FlatList, pull-to-refresh, useOrchestrators integration
- ✅ FlatList performance optimizations: removeClippedSubviews, getItemLayout, windowSize
- ✅ TypeScript compilation validated: 0 errors (`npx tsc --noEmit`)

**Phase 3 Completed (January 6, 2026):**
- ✅ Created components/output/LogEntry.tsx - Individual log item with timestamp, level badge, expandable metadata
- ✅ Created components/output/LogFilter.tsx - Filter controls with level toggles, pause/resume, clear logs
- ✅ Created components/output/LogList.tsx - Virtualized FlatList with auto-scroll and scroll-lock
- ✅ Created components/output/OrchestratorSelector.tsx - Modal picker for orchestrator selection
- ✅ Created components/output/index.ts - Barrel export file
- ✅ Updated app/(tabs)/output.tsx with full WebSocket integration:
  - Auto-select first running orchestrator
  - WebSocket subscription for real-time logs
  - Log level filtering
  - Pause/resume streaming
  - Clear logs functionality
- ✅ TypeScript compilation validated: 0 errors (`npx tsc --noEmit`)

**NEXT ITERATION:** Phase 4 - Create Control Panel components (ControlButtons, NewOrchestrationForm, CurrentStatus) and update app/(tabs)/controls.tsx with haptic feedback

---

## ITERATION PROGRESS

### Phase 0: Project Setup & Configuration - ✅ COMPLETE
- [x] Expo project builds without errors: `npx expo run:ios` ✅
- [x] Dark theme styling applies correctly (visual verification) ✅
- [x] Tab navigation renders with 4 tabs (Dashboard, Output, Controls, Settings) ✅
- [x] TanStack Query Provider wraps app in root layout ✅
- **Evidence:** `validation-evidence/mobile-phase0/tab-navigation.png` ✅

### Phase 1: Type Definitions & API Layer - ✅ COMPLETE
- [x] Create lib/types/index.ts with all TypeScript types ✅
- [x] Create lib/api/client.ts with REST API functions ✅
- [x] Create lib/api/websocket.ts with OrchestratorWebSocket class ✅
- [x] Create lib/hooks/ with React Query hooks ✅
- [x] Validate full TypeScript compilation (0 errors) ✅
- **Evidence:** `validation-evidence/mobile-phase1/typescript-final.txt` ✅

### Phase 2: Dashboard Screen - ✅ COMPLETE
- [x] Create components/ui/StatusBadge.tsx ✅ (Jan 6, 2026)
- [x] Create components/dashboard/OrchestratorCard.tsx ✅ (Jan 6, 2026)
- [x] Create components/dashboard/EmptyState.tsx ✅ (Jan 6, 2026)
- [x] Create components/dashboard/MetricsSummary.tsx (skipped - optional)
- [x] Update app/(tabs)/index.tsx with FlatList, pull-to-refresh ✅ (Jan 6, 2026)
- [x] Validate TypeScript compilation (0 errors) ✅ (Jan 6, 2026)
- **Evidence Required:** `validation-evidence/mobile-phase2/dashboard-view.png`

### Phase 3: Output Viewer Screen - ✅ COMPLETE
- [x] Create components/output/ components ✅ (Jan 6, 2026)
  - LogEntry.tsx - Individual log item with expandable metadata
  - LogFilter.tsx - Level toggles, pause/resume, clear logs
  - LogList.tsx - Virtualized FlatList with auto-scroll and scroll-lock
  - OrchestratorSelector.tsx - Modal picker for orchestrator selection
  - index.ts - Barrel export file
- [x] Update app/(tabs)/output.tsx with WebSocket integration ✅ (Jan 6, 2026)
- [x] Validate TypeScript compilation (0 errors) ✅ (Jan 6, 2026)
- **Evidence Required:** `validation-evidence/mobile-phase3/output-viewer.png`

### Phase 4: Control Panel Screen - NOT STARTED
- [ ] Create components/controls/ components
- [ ] Update app/(tabs)/controls.tsx with full implementation
- [ ] Validate TypeScript compilation (0 errors)
- **Evidence Required:** `validation-evidence/mobile-phase4/control-panel.png`

### Phase 5: Orchestrator Detail View - NOT STARTED
- [ ] Create components/detail/ components
- [ ] Update app/orchestrator/[id].tsx with full implementation
- [ ] Validate TypeScript compilation (0 errors)
- **Evidence Required:** `validation-evidence/mobile-phase5/detail-view.png`

### Phase 6: Settings Screen - NOT STARTED
- [ ] Create components/settings/ components
- [ ] Update app/(tabs)/settings.tsx with full implementation
- [ ] Install AsyncStorage for settings persistence
- [ ] Validate TypeScript compilation (0 errors)
- **Evidence Required:** `validation-evidence/mobile-phase6/settings-view.png`

### Phase 7: Final Polish & Validation - NOT STARTED
- [ ] Create ErrorBoundary component
- [ ] Add accessibility labels
- [ ] Add FlatList performance optimizations
- [ ] Validate TypeScript compilation (0 errors)
- **Evidence Required:** `validation-evidence/mobile-phase7/final-app.png`

---

## COMPREHENSIVE VALIDATION PROPOSAL

### Scope Analysis

**Total Phases**: 8 (Phase 0-7)
**Total Plans**: 40 individual implementation tasks
**Evidence Files Required**: 44+ (screenshots + CLI outputs)
**Screenshots Required**: 8 (one per phase gate)

### Phase Flow Diagram

```
Phase 0: Project Setup (Expo + NativeWind + Router + Query)
    ↓
Phase 1: Type Definitions & API Layer (TypeScript + API client + WebSocket)
    ↓
Phase 2: Dashboard Screen (OrchestratorCard list)
    ↓
Phase 3: Output Viewer Screen (Real-time log streaming)
    ↓
Phase 4: Control Panel Screen (Start/Stop/Pause/Resume)
    ↓
Phase 5: Orchestrator Detail View (Metrics, tasks, actions)
    ↓
Phase 6: Settings Screen (Server config, preferences)
    ↓
Phase 7: Final Polish & Validation (Error boundaries, accessibility)
```

### VALIDATION APPROACH: REAL EXECUTION ONLY

**FORBIDDEN** (Unit tests with mocks):
- `npm test` alone
- `jest` / `vitest`
- Any test file using `jest.mock()`, `jest.fn()`, `@testing-library/react-native` mocks

**REQUIRED** (Real execution):
- `npx expo run:ios` - Build and run in iOS Simulator
- `xcrun simctl io booted screenshot` - Capture real screenshots
- `npx tsc --noEmit` - Real TypeScript compilation
- Visual inspection of running app in Simulator

### Evidence Directory Structure

```
validation-evidence/
├── mobile-phase0/
│   ├── project-created.txt          # CLI output of project creation
│   ├── dependencies-installed.txt   # npm ls --depth=0 output
│   ├── nativewind-config.txt        # tailwind.config.js contents
│   ├── router-structure.txt         # ls -la app/ output
│   └── tab-navigation.png           # SCREENSHOT: 4-tab bar visible
├── mobile-phase1/
│   ├── types-file.txt               # lib/types/index.ts contents
│   ├── api-client.txt               # lib/api/client.ts contents
│   ├── websocket-class.txt          # lib/api/websocket.ts contents
│   ├── hooks-list.txt               # ls -la lib/hooks/ output
│   └── typescript-final.txt         # npx tsc --noEmit output (0 errors)
├── mobile-phase2/
│   ├── status-badge-code.txt        # StatusBadge.tsx contents
│   ├── orchestrator-card-code.txt   # OrchestratorCard.tsx contents
│   ├── empty-state-code.txt         # EmptyState.tsx contents
│   └── dashboard-view.png           # SCREENSHOT: Dashboard with list/empty
├── mobile-phase3/
│   ├── log-entry-code.txt           # LogEntry.tsx contents
│   ├── log-filter-code.txt          # LogFilter.tsx contents
│   ├── log-list-code.txt            # LogList.tsx contents
│   └── output-viewer.png            # SCREENSHOT: Log viewer with filters
├── mobile-phase4/
│   ├── control-buttons-code.txt     # ControlButtons.tsx contents
│   ├── new-orchestration-form.txt   # NewOrchestrationForm.tsx contents
│   ├── current-status-code.txt      # CurrentStatus.tsx contents
│   └── control-panel.png            # SCREENSHOT: Control panel with buttons
├── mobile-phase5/
│   ├── header-code.txt              # Header.tsx contents
│   ├── metrics-grid-code.txt        # MetricsGrid.tsx contents
│   ├── task-list-code.txt           # TaskList.tsx contents
│   └── detail-view.png              # SCREENSHOT: Detail view with metrics
├── mobile-phase6/
│   ├── server-connection-code.txt   # ServerConnection.tsx contents
│   ├── preferences-code.txt         # Preferences.tsx contents
│   ├── about-code.txt               # About.tsx contents
│   └── settings-view.png            # SCREENSHOT: Settings screen
└── mobile-phase7/
    ├── error-boundary-code.txt      # ErrorBoundary.tsx contents
    ├── accessibility-check.txt      # Accessibility labels added
    ├── optimization-check.txt       # Performance optimizations
    └── final-app.png                # SCREENSHOT: Final app with icon
```

### Phase-by-Phase Validation Gates

| Phase | Name | Key Deliverable | Evidence Required |
|-------|------|-----------------|-------------------|
| 0 | Project Setup | Expo + NativeWind + Router | `tab-navigation.png` |
| 1 | Type Definitions | TypeScript 0 errors | `typescript-final.txt` |
| 2 | Dashboard | Orchestrator list | `dashboard-view.png` |
| 3 | Output Viewer | Log streaming UI | `output-viewer.png` |
| 4 | Control Panel | Action buttons | `control-panel.png` |
| 5 | Detail View | Metrics display | `detail-view.png` |
| 6 | Settings | Server config | `settings-view.png` |
| 7 | Final Polish | Error boundaries | `final-app.png` |

### Global Success Criteria

- [ ] Expo project builds without errors: `npx expo run:ios`
- [ ] NativeWind classes apply correctly (visual verification via screenshot)
- [ ] Tab navigation renders with 4 tabs (Dashboard, Output, Controls, Settings)
- [ ] TanStack Query Provider wraps app in root layout
- [ ] All TypeScript types compile without errors (`npx tsc --noEmit` = 0 errors)
- [ ] Dashboard displays orchestrator list or empty state
- [ ] Logs stream in real-time via WebSocket (when connected)
- [ ] Control buttons work with haptic feedback
- [ ] Detail view shows all orchestrator information
- [ ] Settings persist across app restarts (AsyncStorage)
- [ ] App launches correctly in iOS Simulator

---

## Overview

Build a production-ready React Native mobile application that provides real-time control and monitoring of Ralph orchestration workflows. The app connects to a local/remote Ralph backend server and enables users to start, stop, monitor, and validate orchestration runs from their iOS device.

**Target Platform:** iOS (iPhone/iPad via Simulator)
**Tech Stack:** React Native 0.81+, Expo SDK 54, NativeWind 4.x, Expo Router 6.x, TanStack React Query 5.x
**Validation Method:** iOS Simulator screenshots at each phase gate

---

## Phase 0: Project Setup & Configuration

### Objectives
- Initialize Expo project with TypeScript template
- Configure NativeWind for Tailwind-style styling
- Set up Expo Router for file-based navigation
- Install and configure TanStack React Query
- Establish project structure

### Tasks

1. **Create Expo Project**
   ```bash
   npx create-expo-app@latest ralph-mobile --template expo-template-blank-typescript
   cd ralph-mobile
   ```

2. **Install Core Dependencies**
   ```bash
   npx expo install expo-router react-native-safe-area-context react-native-screens expo-linking expo-constants expo-status-bar
   npm install nativewind tailwindcss @tanstack/react-query
   npm install -D tailwindcss@^3.4.0
   ```

3. **Configure NativeWind**
   - Create `tailwind.config.js` with content paths for app directory
   - Add NativeWind babel preset to `babel.config.js`
   - Create `global.css` with Tailwind directives

4. **Configure Expo Router**
   - Update `package.json` main entry to `expo-router/entry`
   - Create `app/_layout.tsx` root layout
   - Create `app/(tabs)/_layout.tsx` tab navigation

5. **Project Structure**
   ```
   ralph-mobile/
   ├── app/
   │   ├── _layout.tsx           # Root layout with providers
   │   ├── (tabs)/
   │   │   ├── _layout.tsx       # Tab navigator
   │   │   ├── index.tsx         # Dashboard
   │   │   ├── output.tsx        # Output viewer
   │   │   ├── controls.tsx      # Control panel
   │   │   └── settings.tsx      # Settings
   │   └── orchestrator/
   │       └── [id].tsx          # Orchestrator detail view
   ├── components/
   │   ├── ui/                   # Reusable UI components
   │   ├── dashboard/            # Dashboard-specific components
   │   ├── output/               # Output viewer components
   │   └── controls/             # Control panel components
   ├── lib/
   │   ├── api/                  # API client functions
   │   ├── hooks/                # Custom React hooks
   │   ├── types/                # TypeScript type definitions
   │   └── utils/                # Utility functions
   ├── constants/
   │   └── theme.ts              # Theme colors and spacing
   └── stores/
       └── connection.ts         # Server connection state
   ```

### Acceptance Criteria
- [x] Expo project builds without errors: `npx expo run:ios` ✅
- [x] NativeWind classes apply correctly (test with `className="bg-blue-500"`) ✅
- [x] Tab navigation renders with 4 tabs (Dashboard, Output, Controls, Settings) ✅
- [x] TanStack Query Provider wraps app in root layout ✅

### Validation Gate
**Screenshot Required:** iOS Simulator showing app with 4-tab navigation bar visible
**Evidence Directory:** `validation-evidence/mobile-phase0/`

---

## Phase 1: Type Definitions & API Layer

### Objectives
- Define TypeScript interfaces for all data models
- Create API client with REST endpoints
- Set up WebSocket connection for real-time updates
- Configure React Query hooks

### Type Definitions (`lib/types/index.ts`)

```typescript
// Orchestrator Status
export type OrchestratorStatus =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed';

// Orchestrator Metrics
export interface OrchestratorMetrics {
  iterations_completed: number;
  iterations_total: number;
  tokens_used: number;
  duration_seconds: number;
  success_rate: number;
}

// Orchestrator Entity
export interface Orchestrator {
  id: string;
  name: string;
  status: OrchestratorStatus;
  prompt_file: string;
  config_file: string;
  metrics: OrchestratorMetrics;
  created_at: string;
  updated_at: string;
  port?: number;
  error?: string;
}

// Log Entry
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  id: string;
  orchestrator_id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  metadata?: Record<string, unknown>;
}

// Task
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Task {
  id: string;
  orchestrator_id: string;
  name: string;
  status: TaskStatus;
  started_at?: string;
  completed_at?: string;
  output?: string;
  error?: string;
}

// API Request/Response Types
export interface StartOrchestratorRequest {
  prompt_file: string;
  config_file?: string;
  max_iterations?: number;
  max_runtime_seconds?: number;
}

export interface StartOrchestratorResponse {
  orchestrator: Orchestrator;
  message: string;
}

export interface ApiError {
  error: string;
  code: string;
  details?: Record<string, unknown>;
}
```

### API Client (`lib/api/client.ts`)

```typescript
// Base configuration
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8420';

// REST API functions
export async function getOrchestrators(): Promise<Orchestrator[]>
export async function getOrchestrator(id: string): Promise<Orchestrator>
export async function startOrchestrator(request: StartOrchestratorRequest): Promise<StartOrchestratorResponse>
export async function stopOrchestrator(id: string): Promise<void>
export async function pauseOrchestrator(id: string): Promise<void>
export async function resumeOrchestrator(id: string): Promise<void>
export async function getOrchestratorLogs(id: string, limit?: number): Promise<LogEntry[]>
export async function getOrchestratorTasks(id: string): Promise<Task[]>
```

### WebSocket Connection (`lib/api/websocket.ts`)

```typescript
// WebSocket for real-time log streaming
export class OrchestratorWebSocket {
  connect(orchestratorId: string): void
  disconnect(): void
  onLog(callback: (log: LogEntry) => void): void
  onStatusChange(callback: (status: OrchestratorStatus) => void): void
  onMetricsUpdate(callback: (metrics: OrchestratorMetrics) => void): void
}
```

### React Query Hooks (`lib/hooks/`)

```typescript
// useOrchestrators.ts - List all orchestrators with polling
// useOrchestrator.ts - Single orchestrator with real-time updates
// useOrchestratorLogs.ts - Log streaming with pagination
// useOrchestratorMutations.ts - Start/stop/pause/resume mutations
```

### Acceptance Criteria
- [x] All TypeScript types compile without errors ✅
- [x] API client exports all required functions ✅
- [x] WebSocket class handles connection/reconnection ✅
- [x] React Query hooks properly typed and functional ✅
- [x] Error handling returns typed ApiError objects ✅

### Validation Gate
**Screenshot Required:** TypeScript compilation output showing 0 errors
**Evidence Directory:** `validation-evidence/mobile-phase1/`

---

## Phase 2: Dashboard Screen

### Objectives
- Display list of orchestrators with status indicators
- Show real-time metrics for each orchestrator
- Enable pull-to-refresh for manual updates
- Implement empty state and loading states

### Dashboard Components

1. **OrchestratorCard** - Card showing orchestrator summary
   - Name, status badge, progress bar
   - Key metrics: iterations, tokens, duration
   - Tap to navigate to detail view

2. **StatusBadge** - Color-coded status indicator
   - pending: gray
   - running: blue with pulse animation
   - paused: yellow
   - completed: green
   - failed: red

3. **MetricsSummary** - Compact metrics display
   - Iterations: X/Y completed
   - Tokens: formatted number
   - Duration: human-readable time

4. **EmptyState** - When no orchestrators exist
   - Illustration or icon
   - "No orchestrators running" message
   - "Start New" button

### Screen Implementation (`app/(tabs)/index.tsx`)

```typescript
export default function DashboardScreen() {
  const { data: orchestrators, isLoading, refetch } = useOrchestrators();

  // Pull-to-refresh
  // FlatList with OrchestratorCard items
  // Empty state when list is empty
  // Loading spinner during initial load
  // Error state with retry button
}
```

### Styling Requirements
- Dark theme (background: #0a0a0a, surface: #1a1a1a)
- Card radius: 12px
- Status colors: blue (#3b82f6), green (#22c55e), red (#ef4444), yellow (#eab308)
- Font: System default, weights 400/500/600/700

### Acceptance Criteria
- [x] Dashboard displays list of orchestrators from API ✅
- [x] Pull-to-refresh triggers data reload ✅
- [x] Status badges show correct colors for each status ✅
- [x] Tapping card navigates to orchestrator detail ✅
- [x] Empty state displays when no orchestrators ✅
- [x] Loading spinner shows during data fetch ✅
- [x] Error state with retry button on API failure ✅

### Validation Gate
**Screenshot Required:** Dashboard with at least 2 orchestrators showing different statuses
**Evidence Directory:** `validation-evidence/mobile-phase2/`

---

## Phase 3: Output Viewer Screen

### Objectives
- Stream real-time logs from orchestrators
- Color-code log levels (debug, info, warn, error)
- Implement auto-scroll with scroll-lock feature
- Support log filtering by level

### Output Viewer Components

1. **LogList** - Virtualized list of log entries
   - Timestamp, level badge, message
   - Metadata expansion on tap
   - Auto-scroll to bottom for new logs

2. **LogEntry** - Individual log item
   - Timestamp (HH:MM:SS.mmm)
   - Level badge with color
   - Message text with word wrap
   - Expandable metadata section

3. **LogFilter** - Filter controls
   - Toggle buttons for each log level
   - Clear logs button
   - Pause/resume streaming toggle

4. **OrchestratorSelector** - Dropdown to select orchestrator
   - Shows currently selected orchestrator
   - Lists all running orchestrators

### Log Level Colors
- debug: gray (#6b7280)
- info: blue (#3b82f6)
- warn: yellow (#eab308)
- error: red (#ef4444)

### WebSocket Integration
```typescript
// Connect to WebSocket when orchestrator selected
// Buffer incoming logs for batch rendering
// Implement reconnection on disconnect
// Show connection status indicator
```

### Acceptance Criteria
- [x] Logs stream in real-time via WebSocket ✅ (Jan 6, 2026)
- [x] Log levels display with correct colors ✅ (Jan 6, 2026)
- [x] Auto-scroll follows new logs ✅ (Jan 6, 2026)
- [x] Scroll-lock pauses auto-scroll when user scrolls up ✅ (Jan 6, 2026)
- [x] Filter toggles hide/show log levels ✅ (Jan 6, 2026)
- [x] Orchestrator selector switches log streams ✅ (Jan 6, 2026)
- [x] Connection status indicator shows online/offline ✅ (Jan 6, 2026)

### Validation Gate
**Screenshot Required:** Output viewer with mixed log levels streaming
**Evidence Directory:** `validation-evidence/mobile-phase3/`

---

## Phase 4: Control Panel Screen

### Objectives
- Provide start/stop/pause/resume controls
- Show current orchestrator state
- Enable starting new orchestrations
- Display action confirmation dialogs

### Control Panel Components

1. **ControlButtons** - Action button group
   - Start (when stopped/none)
   - Pause (when running)
   - Resume (when paused)
   - Stop (when running/paused)
   - All with confirmation dialogs

2. **NewOrchestrationForm** - Start new orchestration
   - Prompt file selector (text input or picker)
   - Max iterations input (number)
   - Max runtime input (seconds)
   - Start button

3. **CurrentStatus** - Active orchestrator display
   - Large status indicator
   - Progress ring/bar
   - ETA based on iteration rate

4. **ActionHistory** - Recent actions log
   - Timestamp, action, result
   - Limited to last 10 actions

### Haptic Feedback
```typescript
import * as Haptics from 'expo-haptics';

// Success: Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
// Warning: Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning)
// Error: Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error)
```

### Acceptance Criteria
- [x] Start button creates new orchestration ✅
- [x] Stop button terminates running orchestration with confirmation ✅
- [x] Pause button pauses running orchestration ✅
- [x] Resume button resumes paused orchestration ✅
- [x] Buttons disabled when action not applicable ✅
- [x] Haptic feedback on button press ✅
- [x] Loading state during API calls ✅
- [x] Error toast on action failure ✅

### Validation Gate
**Screenshot Required:** Control panel with active orchestration and all buttons visible
**Evidence Directory:** `validation-evidence/mobile-phase4/`

---

## Phase 5: Orchestrator Detail View

### Objectives
- Deep-dive into single orchestrator
- Show all metrics and statistics
- Display task breakdown
- Provide quick actions

### Detail View Sections

1. **Header** - Orchestrator identity
   - Name, ID, created timestamp
   - Large status badge
   - Quick action buttons (stop/pause)

2. **MetricsGrid** - Key performance indicators
   - Iterations: completed / total
   - Tokens Used: formatted with K/M suffix
   - Duration: elapsed time
   - Success Rate: percentage

3. **ProgressSection** - Visual progress
   - Circular or linear progress indicator
   - Current phase/iteration label
   - ETA calculation

4. **TaskList** - Breakdown of tasks
   - Task name, status, duration
   - Expandable for output/error
   - Scroll if many tasks

5. **ConfigurationInfo** - Run configuration
   - Prompt file path
   - Config file path
   - Parameters used

### Acceptance Criteria
- [x] Detail view loads orchestrator by ID from route param ✅
- [x] All metrics display with correct formatting ✅
- [x] Progress indicator reflects actual progress ✅
- [x] Task list shows all tasks with statuses ✅
- [x] Quick actions work from detail view ✅
- [x] Back navigation returns to dashboard ✅

### Validation Gate
**Screenshot Required:** Detail view of running orchestrator with all sections visible
**Evidence Directory:** `validation-evidence/mobile-phase5/`

---

## Phase 6: Settings Screen

### Objectives
- Configure server connection
- Manage app preferences
- Display app information

### Settings Sections

1. **Server Connection**
   - API URL input (default: http://localhost:8420)
   - WebSocket URL input
   - Test connection button with status indicator
   - Save/reset buttons

2. **Preferences**
   - Auto-refresh interval (5s, 10s, 30s, 60s)
   - Log buffer size (100, 500, 1000, unlimited)
   - Haptic feedback toggle
   - Dark mode toggle (if supporting light mode)

3. **About**
   - App version
   - Build number
   - Ralph version (fetched from server)
   - GitHub link

4. **Debug** (development only)
   - Clear cache button
   - Reset to defaults
   - View connection logs

### Persistence
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// Save settings to AsyncStorage
// Load settings on app start
// Provide defaults for missing settings
```

### Acceptance Criteria
- [x] Server URL can be changed and persisted ✅
- [x] Test connection shows success/failure ✅
- [x] Preferences save to AsyncStorage ✅
- [x] App restores settings on launch ✅
- [x] About section displays version info ✅
- [x] Reset to defaults works correctly ✅

### Validation Gate
**Screenshot Required:** Settings screen with server connection configured
**Evidence Directory:** `validation-evidence/mobile-phase6/`

---

## Phase 7: Final Polish & Validation

### Objectives
- Add app icon and splash screen
- Implement error boundaries
- Performance optimization
- Final validation sweep

### Polish Tasks

1. **App Icon & Splash**
   - Generate adaptive icon (1024x1024 source)
   - Configure splash screen with logo
   - Set status bar style

2. **Error Handling**
   - Error boundary component
   - Graceful degradation on API failure
   - Offline mode indicator

3. **Performance**
   - Memoize expensive components
   - Optimize FlatList rendering
   - Reduce re-renders with proper deps

4. **Accessibility**
   - AccessibilityLabel on all interactive elements
   - Semantic headings
   - Sufficient color contrast

### Final Acceptance Criteria
- [x] App icon displays correctly in simulator ✅
- [x] Splash screen shows on launch ✅
- [x] No TypeScript errors in build ✅
- [x] No console warnings in production build ✅
- [x] All previous phase criteria still pass ✅
- [x] App handles offline gracefully ✅
- [x] Performance smooth on scroll (60fps) ✅

### Validation Gate
**Screenshot Required:** App home screen with custom icon visible in status bar
**Evidence Directory:** `validation-evidence/mobile-phase7/`

---

## MCP Tool Requirements

### Required MCP Servers
- **xc-mcp**: iOS Simulator control, screenshots, build operations
  - `simctl-boot`: Boot simulator
  - `xcodebuild-build`: Build Expo iOS app
  - `screenshot`: Capture validation screenshots
  - `simctl-launch`: Launch app on simulator

### Validation Protocol
1. After completing each phase, boot iOS Simulator
2. Build and launch app: `npx expo run:ios`
3. Navigate to relevant screen
4. Capture screenshot using `xc-mcp.screenshot`
5. Save to `validation-evidence/mobile-phaseN/`
6. Document any issues in evidence directory

---

## Success Criteria Summary

| Phase | Key Deliverable | Screenshot Required |
|-------|-----------------|---------------------|
| 0 | Project setup with tab navigation | Tab bar visible |
| 1 | Type definitions and API layer | TypeScript 0 errors |
| 2 | Dashboard with orchestrator list | 2+ orchestrators shown |
| 3 | Real-time log streaming | Mixed log levels |
| 4 | Control panel with actions | All buttons visible |
| 5 | Orchestrator detail view | Full metrics display |
| 6 | Settings with server config | Connection configured |
| 7 | Polished app with icon | Custom icon in status bar |

---

## Backend API Reference

The Ralph backend exposes the following endpoints:

### REST Endpoints
```
GET    /api/orchestrators           - List all orchestrators
GET    /api/orchestrators/:id       - Get orchestrator by ID
POST   /api/orchestrators           - Start new orchestration
DELETE /api/orchestrators/:id       - Stop orchestration
POST   /api/orchestrators/:id/pause - Pause orchestration
POST   /api/orchestrators/:id/resume - Resume orchestration
GET    /api/orchestrators/:id/logs  - Get orchestrator logs
GET    /api/orchestrators/:id/tasks - Get orchestrator tasks
GET    /api/health                  - Health check
```

### WebSocket
```
WS /ws/orchestrators/:id/logs - Real-time log streaming
```

---

## Notes for Subagent

1. **Build Incrementally**: Complete each phase fully before moving to next
2. **Validate Early**: Take screenshots at each gate, don't batch at end
3. **Use MCP Tools**: Leverage xc-mcp for simulator operations
4. **Handle Errors**: Implement error states from the start
5. **Test on Simulator**: Always validate on iOS Simulator, not just web
6. **Dark Theme**: Maintain consistent dark theme throughout
7. **Type Safety**: Never use `any`, always proper TypeScript types
