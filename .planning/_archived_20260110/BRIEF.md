# RALF Context Optimization - Project Brief

**Created:** 2026-01-10
**Updated:** 2026-01-10 (Post Deep-Research Revision)
**Status:** Ready for Implementation
**Project Code:** RALF-CTXOPT

---

## Vision

Transform the Ralph Orchestrator's context management from "inject everything every time" to an intelligent, adaptive system that:
1. **Only provides relevant context** for each iteration
2. **Learns from successful patterns** to improve future runs
3. **Detects task completion** to avoid unnecessary iterations
4. **Measures and optimizes** token efficiency continuously

---

## Deep Research Findings (Corrected Understanding)

### How RALF Actually Works

```
┌──────────────────────────────────────────────────────────────────────┐
│ EACH ITERATION IS A FRESH CLAUDE CONVERSATION                       │
│                                                                      │
│ Context persistence is via FILE SYSTEM, not conversation memory:    │
│   - .agent/scratchpad.md  → Claude reads/updates each iteration    │
│   - Task file             → Can be modified to mark progress       │
│   - dynamic_context       → Adds "## Previous Context" section     │
│   - ACE skillbook         → Appended to every prompt               │
└──────────────────────────────────────────────────────────────────────┘
```

### Validation Loops Are INTENTIONAL (Not Waste!)

**Original misconception**: 29% of iterations were "wasted" on verification.

**Corrected understanding**: Verification loops are the CORRECT behavior:
- Iteration 1: Does the actual work
- Iteration 2+: Reads scratchpad, sees task complete, VERIFIES it works
- This is the validation loop working as designed

**The REAL problem**: No completion detection after verification succeeds.
The orchestrator keeps running because it doesn't know "verified = done".

### Baseline Metrics (2026-01-10)
| Metric | Value | Source |
|--------|-------|--------|
| **Total Benchmark Cost** | $0.7729 | BASELINE_ANALYSIS.md |
| **Overall Success Rate** | 100% | 28/28 iterations |
| **Total Tokens Used** | 143,141 | 5 tier benchmark |
| **Unnecessary Iterations** | ~29% | After verification succeeds |
| **Productive Iteration Rate** | 10-100% | Varies by tier |

### Key Problems Identified (Corrected)

1. **No Completion Detection**: Orchestrator can't detect "task verified, stop now"
   - Iterations 2+ verify successfully but loop continues
   - Need explicit "COMPLETE AND VERIFIED" signal

2. **Path Hallucination**: Each iteration Claude uses wrong paths
   - Hallucinates paths like `/Users/alpindale/repos/`
   - Has to run `pwd` to discover actual directory
   - Could be fixed with explicit CWD in prompt

3. **ContextTracker Not Wired In**: Exists but not used
   - Location: `src/ralph_orchestrator/monitoring/context_tracker.py`
   - Has MeasurePoint enum, per-component tracking
   - Zero calls from orchestrator.py

4. **Metrics Collection Incomplete**:
   - `tools_used`: Always empty []
   - `learning`: Always empty {}
   - No per-component token breakdown

5. **Full Skillbook Injection**: Same tokens every iteration
   - Full skillbook appended regardless of task
   - Could use TOP-K semantic retrieval instead

### Existing Infrastructure

**Working:**
- **ContextManager**: `context.py` - Manages prompts, dynamic_context, error_history
- **ACE Adapter**: `learning/ace_adapter.py` - Async learning, skillbook injection
- **Metrics System**: Per-iteration stats in `.agent/metrics/`
- **Scratchpad Pattern**: Claude reads/writes `.agent/scratchpad.md`

**NOT Working / Not Wired In:**
- **ContextTracker**: Exists but not integrated into orchestrator loop
- **Completion Detection**: `_check_completion_promise()` exists but rarely triggers
- **tools_used / learning metrics**: Always empty in JSON

### Available MCP Servers (15 Enabled!)

| Server | Purpose | Status |
|--------|---------|--------|
| **claude-mem** (memory) | Memory persistence | ✅ Enabled |
| **Context7** | Library documentation | ✅ Enabled |
| **serena** | Semantic code navigation | ✅ Enabled |
| **sequential-thinking** | Structured reasoning | ✅ Enabled |
| **repomix** | Code context aggregation | ✅ Enabled |
| **firecrawl-mcp** | Web research | ✅ Enabled |
| **tavily** | Search and research | ✅ Enabled |
| playwright/puppeteer | Browser automation | ✅ Enabled |
| github, supabase, fetch, shadcn-ui, tuist, chrome-devtools | Various | ✅ Enabled |

**Insight**: Extensive MCP infrastructure available - can leverage for context optimization without building new server.

---

## Implementation Approach (Revised)

Based on corrected understanding, prioritize by ACTUAL impact:

### Phase 01: Completion Detection (P0 - Critical)
**Problem**: Orchestrator doesn't know when to stop after verification succeeds.

**Solution**:
1. Detect when consecutive iterations confirm "task complete"
2. Add explicit COMPLETION signal pattern
3. Stop after first successful verification (not arbitrary max)

**Deliverables**:
- Consecutive iteration similarity detector
- "VERIFIED_COMPLETE" signal in output parsing
- Smart early-stop logic

**Validation Gate**:
- [ ] Tier 0: 1-2 iterations max (was 3)
- [ ] Tier 1: 2-3 iterations max (was 5)
- [ ] Success rate: 100%

---

### Phase 02: Wire ContextTracker (P1 - Foundation)
**Problem**: ContextTracker exists but not integrated - no per-component metrics.

**Solution**:
1. Add `tracker.measure()` calls at each MeasurePoint in orchestrator
2. Track: prompt tokens, skillbook tokens, dynamic_context, response
3. Save timeline to `.agent/metrics/`

**Deliverables**:
- ContextTracker instantiation in orchestrator
- measure() calls at ITERATION_START, AFTER_SKILLBOOK_INJECT, AFTER_RESPONSE
- Per-iteration component breakdown in metrics JSON

**Validation Gate**:
- [ ] Metrics files include per-component token breakdown
- [ ] Can visualize where tokens go (prompt vs skillbook vs response)
- [ ] No performance regression

---

### Phase 03: Fix Path Hallucination (P2 - Quick Win)
**Problem**: Each iteration Claude hallucinates wrong paths, wastes time on pwd.

**Solution**:
1. Add explicit CWD and project root to enhanced prompt
2. Include in ORCHESTRATION CONTEXT section

**Deliverables**:
- Add `WORKING_DIRECTORY: {cwd}` to prompt
- Add `PROJECT_ROOT: {project_root}` to prompt

**Validation Gate**:
- [ ] Iterations don't need pwd to find files
- [ ] First tool call uses correct paths

---

### Phase 04: Semantic Skill Injection (P3 - Medium Impact)
**Problem**: Full skillbook injected every iteration regardless of task.

**Solution**:
1. Use claude-mem or local embeddings for skill similarity
2. Inject TOP-K most relevant skills based on task
3. A/B test: inject-all vs TOP-3 vs TOP-5

**Deliverables**:
- SemanticInjector class with TOP-K retrieval
- Integration with existing ACE adapter
- A/B testing harness

**Validation Gate**:
- [ ] Skillbook tokens reduced by 40-60%
- [ ] Success rate maintained at 100%
- [ ] No "missing skill" failures

---

### Phase 05: Dynamic Prompt Templates (P4 - Low Effort)
**Problem**: Same 800+ token instructions every iteration.

**Solution**:
1. Full instructions for iterations 1-3
2. Condensed instructions for iterations 4+
3. Claude already knows the context by then

**Deliverables**:
- `_enhance_prompt_with_instructions(iteration)` accepts iteration number
- Full template (~800 tokens) for early iterations
- Condensed template (~150 tokens) for later iterations

**Validation Gate**:
- [ ] ~650 tokens saved per iteration 4+
- [ ] No behavior drift in later iterations
- [ ] Success rate maintained

---

## Success Criteria

### Per-Phase Validation Gates
Each phase must pass before proceeding:
- [ ] Observed improvement matches expectation (within 25%)
- [ ] Success rate equals baseline (100%)
- [ ] No new error types emerge
- [ ] Benchmark reproducible (variance <30%)

### Overall Project Success
- [ ] Unnecessary iterations eliminated (stop after verification)
- [ ] Per-component token tracking enabled
- [ ] Cost per benchmark reduced by ≥20%
- [ ] All 5 tiers pass at 100%
- [ ] 2-3 iterative improvements committed

---

## Technical Context

### Key Files
```
src/ralph_orchestrator/
├── orchestrator.py              # Main loop (needs ContextTracker, completion detection)
├── context.py                   # ContextManager (working)
├── monitoring/
│   └── context_tracker.py       # Token tracking (NOT integrated - Phase 02)
├── learning/
│   └── ace_adapter.py           # ACE integration (inject_context working)
└── adapters/
    ├── base.py                  # _enhance_prompt_with_instructions (Phase 05)
    └── claude.py                # Claude adapter (working)

.agent/
├── scratchpad.md                # Claude reads/updates each iteration
├── skillbook/
│   └── skillbook.json           # Current skills (2 skills)
└── metrics/                     # Per-iteration stats

runs/baseline-20260110/          # Benchmark data for comparison
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-10 | Initial planning | Created phases based on research |
| 2026-01-10 | **CORRECTED**: Validation loops are intentional | Deep research revealed loops are correct behavior |
| 2026-01-10 | **CORRECTED**: Real issue is completion detection | Orchestrator doesn't know when to stop |
| 2026-01-10 | **CORRECTED**: ContextTracker NOT wired in | Confirmed via grep - zero usage in orchestrator |
| 2026-01-10 | **CORRECTED**: 15 MCP servers available | Including claude-mem, serena, Context7 |
| 2026-01-10 | Phase 01 = Completion detection | Highest impact, directly addresses real problem |
| 2026-01-10 | Use existing MCP servers | No need to build custom server initially |

---

**This brief reflects CORRECTED understanding from deep research of the actual codebase.**
