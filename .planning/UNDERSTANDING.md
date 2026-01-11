# RALF Orchestrator - Correct Understanding

**Created:** 2026-01-10 (Post-Correction)
**Status:** Verified Understanding - Awaiting Goal Definition

---

## How RALF Actually Works

### Orchestration Loop
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Each iteration = FRESH Claude conversation                                  │
│                                                                             │
│ Context persistence is via FILE SYSTEM:                                     │
│   - .agent/scratchpad.md    → Agent reads/updates each iteration            │
│   - Prompt file             → Can contain completion markers                │
│   - dynamic_context         → Adds previous context section                 │
│   - ACE skillbook           → Appended to every prompt                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Completion Detection (ALREADY EXISTS)

**Two mechanisms are implemented and working:**

1. **`_check_completion_marker()`** (orchestrator.py:1211)
   - Checks prompt file for: `- [x] TASK_COMPLETE` or `[x] TASK_COMPLETE`
   - Called BEFORE each iteration (line 597)
   - When found: logs "Completion marker found" and breaks loop

2. **`_check_completion_promise(output)`** (orchestrator.py:1235)
   - Checks agent output for configurable string (default: "LOOP_COMPLETE")
   - Called AFTER successful iteration (line 710)
   - When found: logs "Completion promise matched" and breaks loop

### The Prompt Design Contract

For completion to work, prompts should instruct Claude to:
- Write `- [x] TASK_COMPLETE` to the prompt file when done, OR
- Output `LOOP_COMPLETE` in its response when done

**If prompts don't use these signals, the orchestrator runs until max_iterations.**
This is BY DESIGN, not a bug.

### Validation Loops are INTENTIONAL

- Iteration 1: Does the work
- Iterations 2+: Verify the work (re-reads scratchpad, confirms completion)
- This continues until a completion signal OR max_iterations
- The system is designed this way to allow recovery and verification

---

## What Was Wrong in Previous Analysis

| Previous Claim | Reality |
|----------------|---------|
| "29% verification waste" | Intentional behavior - prompts lack completion markers |
| "Need to build completion detection" | Already exists and is tested |
| "Phase 01: Completion Detection" | Nonsensical - it's already implemented |

---

## What Actually Exists vs What's Missing

### EXISTS (Working):
- [x] Completion marker detection (`_check_completion_marker`)
- [x] Completion promise detection (`_check_completion_promise`)
- [x] Scratchpad persistence pattern
- [x] Dynamic context injection
- [x] ACE skillbook injection
- [x] Metrics collection (per-iteration)

### NOT WIRED IN (Confirmed):
- [ ] ContextTracker (`monitoring/context_tracker.py`) - EXISTS but ZERO usage in orchestrator.py
- [ ] Per-component token breakdown (ContextTracker has MeasurePoints but not called)
- [ ] `tools_used` in metrics (always empty [])
- [ ] `learning` in metrics (always empty {})

### OBSERVED ISSUES (Quality of Life):
- [ ] Path hallucination (agent uses `/Users/alpindale/...` instead of actual CWD)
- [ ] Full skillbook injection every iteration (could be TOP-K)
- [ ] Same 800-token instructions every iteration (could condense later)

---

## Research Status: COMPLETE

Deep research completed on 2026-01-10 with 5 parallel exploration agents:

1. **ContextTracker** - Full component analysis, integration plan ready
2. **Prompt Completion** - Gap identified between detection and instructions
3. **Path Hallucination** - Root cause found (CWD not in prompt text)
4. **ACE/Skillbook** - All-skills injection confirmed, TOP-K plan ready
5. **Instruction Templates** - Iteration not passed, condensed plan ready

**All findings documented in:**
- `.planning/BRIEF.md` - Project brief with research summary
- `.planning/ROADMAP.md` - Implementation roadmap with 5 phases

---

## Previous Documents (Archived)

Incorrect planning documents archived to: `.planning/_archived_20260110/`
- BRIEF.md (incorrect framing - treated completion detection as missing)
- ROADMAP.md (incorrect phases - planned to build what exists)
- phases/ (empty directory structure)
