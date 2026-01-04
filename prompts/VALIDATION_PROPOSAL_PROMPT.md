# Validation Proposal Phase

**PHASE 0 - CREATE COMPREHENSIVE ACCEPTANCE CRITERIA**

## Your Role

You are in validation proposal mode. Your task is to analyze the ENTIRE prompt file and create acceptance criteria for ALL phases and plans before any work begins.

---

## CRITICAL: REAL EXECUTION ENFORCEMENT

### FORBIDDEN VALIDATION GATES (Instant Rejection)

These validation gates are **PROHIBITED** because they run unit tests with mocks:

```
# FORBIDDEN - These just run mocked unit tests
npm test
npm run test
jest
vitest
uv run pytest tests/
pytest tests/
python -m pytest
```

**WHY FORBIDDEN**: Unit tests use `jest.mock()`, `jest.fn()`, `unittest.mock`, etc. They test code logic with fake data, NOT real functionality. A mocked API test proves nothing about actual API behavior.

### REQUIRED VALIDATION GATES (Real Execution Only)

#### For Mobile Apps (React Native/Expo):
```bash
# REQUIRED: Actually run in simulator
npx expo start --ios          # Opens iOS Simulator
npx expo run:ios              # Builds and runs in Simulator

# REQUIRED: Take screenshots as evidence
# Use Playwright MCP, xc-mcp, or screenshot CLI tools
xcrun simctl io booted screenshot validation-evidence/mobile/dashboard.png

# REQUIRED: Verify API connectivity
curl -X GET http://localhost:8080/api/orchestrators -H "Authorization: Bearer $TOKEN"
```

#### For Web Apps:
```bash
# REQUIRED: Use Playwright for real browser testing
npx playwright test            # Real browser execution
cd playwright-skill && node run.js /tmp/test.js  # Real browser with screenshots

# REQUIRED: Capture screenshots
await page.screenshot({ path: 'validation-evidence/web/home.png' })
```

#### For Backend/API:
```bash
# REQUIRED: Actually start the server and hit endpoints
ralph daemon start             # Start actual daemon
curl -X POST http://localhost:8080/api/orchestrators  # Real API call
ralph daemon logs              # Capture actual output

# REQUIRED: Test actual process behavior
ralph run -P test.md --daemon  # Should return immediately
pgrep -f ralph                 # Verify daemon is running
```

#### For CLI Tools:
```bash
# REQUIRED: Capture actual CLI output
ralph run -P test.md 2>&1 | tee validation-evidence/cli/output.txt
ralph daemon status > validation-evidence/cli/daemon-status.txt
```

---

## VALIDATION EVIDENCE REQUIREMENTS

### Evidence Directory Structure

Every validation phase MUST produce evidence files:

```
validation-evidence/
├── phase-01/
│   ├── instance-parallel-test.txt    # CLI output showing 2 instances
│   └── port-allocation.txt           # Output showing no port conflicts
├── phase-02/
│   ├── daemon-start.txt              # "ralph daemon start" returns immediately
│   ├── daemon-status.txt             # Status shows running
│   └── daemon-logs.txt               # Log streaming works
├── phase-03/
│   ├── api-start-response.json       # POST /api/orchestrators response
│   ├── api-stop-response.json        # POST /api/.../stop response
│   └── sse-stream.txt                # SSE event stream capture
├── phase-04/
│   ├── expo-start.png                # Screenshot of app in simulator
│   └── app-bundle-success.txt        # Build output
├── phase-05/
│   ├── dashboard-view.png            # Screenshot of dashboard with data
│   ├── detail-view.png               # Screenshot of detail screen
│   └── websocket-connected.txt       # Log showing WS connection
├── phase-06/
│   ├── start-orchestration.png       # Screenshot of start UI
│   ├── control-buttons.png           # Screenshot of stop/pause/resume
│   └── api-integration-log.txt       # Actual API calls from app
└── final/
    ├── full-workflow.mp4             # (Optional) Screen recording
    └── summary.md                    # What was validated
```

### Evidence Checkpoint Rule

**BEFORE marking any phase complete**, verify:

```bash
# Check evidence exists
ls -la validation-evidence/phase-{XX}/*.{png,txt,json}

# Must have at least:
# - 1 screenshot (for UI phases)
# - 1 CLI output capture (for backend phases)
# - 1 API response (for API phases)
```

**NO EVIDENCE = NOT COMPLETE**

---

## Critical Instructions

1. **DO NOT** proceed with any implementation until user confirms your proposal
2. **DO NOT** use mock tests - real execution only for validation
3. **DO NOT** accept "npm test" or "pytest" as validation gates
4. **DO NOT** focus on just one phase - analyze EVERYTHING
5. **DO NOT** skip any phases when creating criteria
6. **DO NOT** mark complete without evidence files in validation-evidence/
7. **PROPOSE** for user approval - don't auto-configure
8. **REQUIRE** screenshots for any UI work
9. **REQUIRE** actual API calls with captured responses

---

## Step 1: Read the ENTIRE Prompt

Read the complete prompt file from start to finish. Identify:
1. ALL phases (there may be 6-7 phases with multiple plans each)
2. ALL plans within each phase
3. ALL validation gates mentioned - **REJECT if they're just unit tests**
4. The overall vision and success criteria
5. Dependencies between phases

---

## Step 2: Create COMPREHENSIVE Acceptance Criteria

Generate acceptance criteria covering the ENTIRE roadmap:

```yaml
# COMPREHENSIVE_ACCEPTANCE_CRITERIA.yaml
project_summary: |
  [Overall description of what will be built across all phases]

evidence_policy:
  required: true
  directory: validation-evidence/
  per_phase: true
  checkpoint_before_complete: true

# Repeat for EACH phase
phase_00:
  name: "[Phase name]"
  goal: "[Phase goal]"
  plans:
    - plan_id: "00-01"
      description: "[What this plan accomplishes]"
      acceptance_criteria:
        - "[Specific, measurable criterion]"
        - "[Specific, measurable criterion]"
      # REAL EXECUTION validation - NOT unit tests
      validation_gate:
        type: "real_execution"  # NOT "unit_test"
        commands:
          - "[Actual execution command]"
          - "[Evidence capture command]"
        evidence_required:
          - "validation-evidence/phase-00/[filename].txt"
          - "validation-evidence/phase-00/[filename].png"

    - plan_id: "00-02"
      # ... continue for all plans

  phase_validation:
    type: "functional"  # NOT "unit"
    command: "[Command that tests REAL functionality]"
    evidence_directory: "validation-evidence/phase-00/"
    expected_files:
      - "[evidence file 1]"
      - "[evidence file 2]"
    expected_result: "[What success looks like - with proof]"

# Overall success criteria
global_success_criteria:
  - criterion: "[From the SUCCESS CRITERIA section of prompt]"
    verification: "[How to verify - REAL execution]"
    evidence_type: "[screenshot|cli_output|api_response]"
```

---

## Step 3: Present Full Validation Plan

Format your proposal as:

```markdown
## Comprehensive Validation Proposal

### Scope Analysis
I have analyzed the prompt and identified:
- **Total Phases**: X
- **Total Plans**: X
- **Evidence Files Required**: X (screenshots + outputs)
- **Dependencies**: [Phase flow diagram]

### VALIDATION APPROACH: REAL EXECUTION ONLY

I will validate using:
- iOS Simulator screenshots (NOT Jest tests)
- Actual API calls with curl (NOT mocked fetch)
- Real CLI output captures (NOT subprocess mocks)
- Browser automation with Playwright (NOT JSDOM)

### Phase-by-Phase Acceptance Criteria

#### Phase 00: [Name]
**Goal**: [Goal]

| Plan | Acceptance Criteria | Validation Method | Evidence Required |
|------|---------------------|-------------------|-------------------|
| 00-01 | [Criteria] | [REAL command] | screenshot/output |
| 00-02 | [Criteria] | [REAL command] | screenshot/output |

**Evidence Checkpoint**: `ls validation-evidence/phase-00/`
...

[Repeat for ALL phases]

### Global Success Criteria
- [ ] [Criterion 1] - Evidence: [file]
- [ ] [Criterion 2] - Evidence: [file]
...

### Validation Strategy

**FORBIDDEN** (Unit tests with mocks):
- `npm test` alone
- `pytest` alone
- Any Jest/Vitest tests with mock()

**REQUIRED** (Real execution):
- **Python backend**: Actual daemon running, real API calls
- **Mobile app**: Expo in iOS Simulator with screenshots
- **Web UI**: Playwright browser automation
- **Evidence collection**: All output to validation-evidence/

---
Do you approve this REAL EXECUTION validation plan?
- [A]pprove - Proceed with functional validation (no mocks)
- [M]odify - I want to change something
- [S]kip - Skip validation, proceed without criteria
```

---

## Important: Full Scope Coverage

You MUST create acceptance criteria for ALL phases with REAL EXECUTION validation:

| Phase | Type | Validation Method |
|-------|------|-------------------|
| Phase 00: TUI Testing | UI | Textual pilot + screenshot |
| Phase 01: Process Isolation | Backend | CLI output, parallel process verification |
| Phase 02: Daemon Mode | Backend | `ralph daemon start` returns immediately |
| Phase 03: REST API | Backend | curl commands with captured responses |
| Phase 04: Mobile Foundation | Mobile | iOS Simulator screenshot |
| Phase 05: Mobile Dashboard | Mobile | iOS Simulator with live data screenshot |
| Phase 06: Mobile Control | Mobile | iOS Simulator showing control actions |

Do NOT only focus on the first phase. The user needs to approve the COMPLETE validation plan covering ALL work that will be done.

---

## Why Full Scope Matters

1. **Architectural planning**: Knowing all phases helps make good decisions early
2. **Resource estimation**: User understands full scope of work
3. **Validation checkpoints**: Clear gates at each phase with evidence
4. **No surprises**: User knows exactly what will be built
5. **Proof of completion**: Evidence files prove work was done correctly

---

## After User Approval

Once approved:
1. Save COMPREHENSIVE_ACCEPTANCE_CRITERIA.yaml to project root
2. Create validation-evidence/ directory structure
3. Begin with Phase 00 (or first incomplete phase)
4. **COLLECT EVIDENCE** as you complete each plan
5. **CHECKPOINT**: `ls validation-evidence/phase-XX/` before marking complete
6. Update acceptance criteria with actual evidence files
7. Only mark complete when ALL phases verified with evidence

---

## COMPLETION GATE

Before writing `TASK_COMPLETE`, verify:

```bash
# All evidence directories exist and have files
find validation-evidence -type f | wc -l  # Should be > 0

# Each completed phase has evidence
for phase in phase-00 phase-01 phase-02 phase-03 phase-04 phase-05 phase-06; do
  echo "$phase: $(ls validation-evidence/$phase 2>/dev/null | wc -l) files"
done

# Key evidence files exist
ls validation-evidence/phase-04/*.png  # Mobile screenshots
ls validation-evidence/phase-03/*.json  # API responses
ls validation-evidence/phase-02/*.txt   # Daemon output
```

**NO EVIDENCE = TASK NOT COMPLETE**
