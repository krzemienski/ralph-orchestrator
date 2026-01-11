# RALF Context Optimization - Roadmap

**Project:** RALF-CTXOPT
**Version:** v1.0 (Context Optimization Foundation)
**Status:** Planning Complete - Ready for Execution
**Updated:** 2026-01-10 (Post Deep-Research Revision)

---

## Key Insight from Deep Research

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  VALIDATION LOOPS ARE INTENTIONAL - NOT WASTE!                               ║
║                                                                              ║
║  The loop is designed to verify work. The REAL problem is:                   ║
║  → No completion detection after verification succeeds                       ║
║  → Orchestrator doesn't know "verified = done"                               ║
║  → Keeps running until max iterations                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│ v1.0 CONTEXT OPTIMIZATION MILESTONE                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 01: Completion Detection ★ CRITICAL                              │
│  ├─ Problem: Orchestrator doesn't stop after verification              │
│  ├─ Impact: Eliminate unnecessary iterations (~29%)                    │
│  ├─ Risk: Low                                                          │
│  └─ Effort: 2-3 hours                                                   │
│                                                                         │
│  Phase 02: Wire ContextTracker (Foundation)                             │
│  ├─ Problem: Exists but NOT integrated into orchestrator               │
│  ├─ Impact: Enables per-component token measurement                    │
│  ├─ Risk: Very Low                                                     │
│  └─ Effort: 2-4 hours                                                   │
│                                                                         │
│  Phase 03: Fix Path Hallucination (Quick Win)                           │
│  ├─ Problem: Claude hallucinates wrong paths each iteration            │
│  ├─ Impact: Faster iterations, fewer tool calls                        │
│  ├─ Risk: Very Low                                                     │
│  └─ Effort: 1-2 hours                                                   │
│                                                                         │
│  Phase 04: Semantic Skill Injection                                     │
│  ├─ Problem: Full skillbook injected every iteration                   │
│  ├─ Impact: 40-60% skillbook token reduction                           │
│  ├─ Risk: Low-Medium                                                   │
│  └─ Effort: 8-12 hours                                                  │
│                                                                         │
│  Phase 05: Dynamic Prompt Templates                                     │
│  ├─ Problem: Same 800+ token instructions every iteration              │
│  ├─ Impact: ~650 tokens/iteration saved for iter 4+                    │
│  ├─ Risk: Very Low                                                     │
│  └─ Effort: 3-5 hours                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## v1.0 Milestone: Context Optimization Foundation

### Phase 01: Completion Detection
**Directory:** `.planning/phases/01-completion-detection/`
**Status:** [ ] NOT STARTED
**Priority:** ★★★ CRITICAL

**Objective:** Detect when task is complete AND verified, stop the loop.

**The Problem (Observed in tier0 benchmark):**
- Iteration 1: Does the work ($0.0144)
- Iteration 2: Verifies complete ($0.0179)
- Iteration 3: Verifies AGAIN ($0.0056) ← Unnecessary!
- Orchestrator hit max_iterations (3), not completion detection

**Solution:**
1. Detect consecutive "task complete" confirmations
2. Parse output for explicit completion signals
3. Add `VERIFIED_COMPLETE` pattern matching
4. Stop after first successful verification

**Deliverables:**
1. `_detect_completion_verification()` method in orchestrator
2. Output pattern matching for completion phrases
3. Consecutive success detection (if iter N and N-1 both confirm done)
4. Updated benchmark showing earlier termination

**Validation Gate:**
- [ ] Tier 0: 1-2 iterations max (was 3)
- [ ] Tier 1: 2-3 iterations max (was 5)
- [ ] Tier 3: 2-3 iterations max (was 5)
- [ ] Tier 4: 2-3 iterations max (was 10)
- [ ] Success rate: 100%
- [ ] Cost reduction observed

**Files to Modify:**
- `src/ralph_orchestrator/orchestrator.py` (main loop, completion detection)

---

### Phase 02: Wire ContextTracker
**Directory:** `.planning/phases/02-wire-context-tracker/`
**Status:** [ ] NOT STARTED
**Priority:** ★★☆ Foundation

**Objective:** Integrate existing ContextTracker into orchestrator for per-component metrics.

**The Problem:**
- ContextTracker exists at `monitoring/context_tracker.py`
- Has MeasurePoint enum, ContextMeasurement dataclass
- ZERO usage in orchestrator.py (confirmed via grep)
- No per-component token breakdown in metrics

**Solution:**
1. Instantiate ContextTracker in orchestrator.__init__()
2. Add measure() calls at key points
3. Include measurements in metrics JSON output

**Deliverables:**
1. ContextTracker instantiation in orchestrator
2. measure() calls at:
   - ITERATION_START (prompt before enhancement)
   - AFTER_PROMPT_INJECT (after _enhance_prompt_with_instructions)
   - AFTER_SKILLBOOK_INJECT (after learning_adapter.inject_context)
   - AFTER_RESPONSE (response text)
   - ITERATION_END (final state)
3. Per-iteration component breakdown in metrics
4. Reproducibility test (3 runs, variance <30%)

**Validation Gate:**
- [ ] Metrics files include per-component token counts
- [ ] Can visualize: base_prompt vs skillbook vs instructions vs response
- [ ] Measurements match API billing (sanity check)
- [ ] No performance regression

**Files to Modify:**
- `src/ralph_orchestrator/orchestrator.py` (add ContextTracker)

**Files Already Exist:**
- `src/ralph_orchestrator/monitoring/context_tracker.py` (ready to use!)

---

### Phase 03: Fix Path Hallucination
**Directory:** `.planning/phases/03-fix-path-hallucination/`
**Status:** [ ] NOT STARTED
**Priority:** ★★☆ Quick Win

**Objective:** Prevent Claude from hallucinating wrong paths each iteration.

**The Problem (Observed in benchmarks):**
- Iteration 1: Claude uses `/Users/rtorres/Development/...`
- Iteration 2: Claude uses `/Users/alpindale/repos/...`
- Iteration 3: Claude uses `/Users/hkr/Projects/...`
- Each iteration has to run `pwd` to discover actual directory
- Wastes tool calls and tokens

**Solution:**
1. Add explicit CWD to ORCHESTRATION CONTEXT
2. Add project root path to prompt
3. Claude will use correct paths from the start

**Deliverables:**
1. Modify `_enhance_prompt_with_instructions()` in `adapters/base.py`
2. Add:
   ```
   WORKING DIRECTORY: /Users/nick/Desktop/ralph-orchestrator
   PROJECT ROOT: /Users/nick/Desktop/ralph-orchestrator
   ```
3. Test that Claude uses correct paths immediately

**Validation Gate:**
- [ ] Iterations don't need `pwd` to find files
- [ ] First tool call uses correct paths
- [ ] No path-related errors

**Files to Modify:**
- `src/ralph_orchestrator/adapters/base.py` (_enhance_prompt_with_instructions)

---

### Phase 04: Semantic Skill Injection
**Directory:** `.planning/phases/04-semantic-skill-injection/`
**Status:** [ ] NOT STARTED
**Priority:** ★★★ High Impact

**Objective:** Inject only relevant skills based on task, not entire skillbook.

**The Problem:**
- Full skillbook (~1000-3000 tokens) appended every iteration
- Most skills irrelevant to current task
- Same tokens wasted on every iteration

**Solution:**
1. Use claude-mem or local embeddings for skill similarity
2. Compare task to skill descriptions
3. Inject TOP-K most relevant skills (K=3 or 5)
4. A/B test to validate

**Deliverables:**
1. `SemanticInjector` class with TOP-K retrieval
2. Integration with ACE adapter
3. A/B testing harness (inject-all vs TOP-3 vs TOP-5)
4. Benchmark comparison report

**Available MCP Servers for Embeddings:**
- claude-mem (memory) - Already enabled, has embedding capabilities
- serena - Semantic code navigation
- Context7 - Could be adapted

**Validation Gate:**
- [ ] Skillbook tokens reduced by 40-60%
- [ ] Success rate: 100%
- [ ] No "missing skill" failures observed
- [ ] A/B test shows TOP-K matches or beats inject-all

**Files to Create:**
- `src/ralph_orchestrator/memory/injector.py`

**Files to Modify:**
- `src/ralph_orchestrator/learning/ace_adapter.py` (use SemanticInjector)

---

### Phase 05: Dynamic Prompt Templates
**Directory:** `.planning/phases/05-dynamic-prompts/`
**Status:** [ ] NOT STARTED
**Priority:** ★★☆ Medium Impact

**Objective:** Scale instruction verbosity based on iteration number.

**The Problem:**
- Same 800+ token ORCHESTRATION CONTEXT every iteration
- By iteration 4+, Claude already understands the context
- Redundant instructions waste tokens

**Solution:**
1. `_enhance_prompt_with_instructions(prompt, iteration)` accepts iteration
2. Full instructions template (iterations 1-3): ~800 tokens
3. Condensed instructions template (iterations 4+): ~150 tokens

**Deliverables:**
1. Modify `_enhance_prompt_with_instructions()` to accept iteration
2. Create FULL_INSTRUCTIONS constant (~800 tokens)
3. Create CONDENSED_INSTRUCTIONS constant (~150 tokens)
4. Select based on iteration number
5. Benchmark comparison showing token savings

**Validation Gate:**
- [ ] Iterations 4+: ~650 fewer tokens per iteration
- [ ] Success rate: 100%
- [ ] No behavior drift observed
- [ ] For 10-iteration run: ~4,550 tokens saved

**Files to Modify:**
- `src/ralph_orchestrator/adapters/base.py`
- `src/ralph_orchestrator/orchestrator.py` (pass iteration to enhance)

---

## Phase Tracking

| Phase | Status | Started | Completed | Validated |
|-------|--------|---------|-----------|-----------|
| 01 - Completion Detection | 🔴 Not Started | - | - | - |
| 02 - Wire ContextTracker | 🔴 Not Started | - | - | - |
| 03 - Fix Path Hallucination | 🔴 Not Started | - | - | - |
| 04 - Semantic Skill Injection | 🔴 Not Started | - | - | - |
| 05 - Dynamic Prompts | 🔴 Not Started | - | - | - |

---

## Execution Order

The phases are ordered by impact and dependency:

```
Phase 01 (Critical) ──┐
                      ├──> Phase 03 (Quick win, no dependencies)
Phase 02 (Foundation)─┤
                      └──> Phase 04 (Needs 02 for measurement)
                              │
                              └──> Phase 05 (Needs 02 for measurement)
```

**Parallelization:**
- Phase 01 and Phase 02 CAN run in parallel (no dependencies)
- Phase 03 can run anytime (no dependencies)
- Phase 04 benefits from Phase 02 (measurement)
- Phase 05 benefits from Phase 02 (measurement)

---

## Success Metrics (v1.0)

| Metric | Baseline | Target | Stretch |
|--------|----------|--------|---------|
| Cost per benchmark | $0.77 | $0.55 (-29%) | $0.40 (-48%) |
| Iterations after verification | Unlimited | 0-1 | 0 |
| Skillbook tokens | 100% | 60% | 40% |
| Tokens/iteration (complex) | ~12K | ~8K | ~6K |
| Success rate | 100% | 100% | 100% |
| Per-component metrics | None | Full | Full + visualization |

---

## Available Resources

### MCP Servers (15 Enabled)
- **claude-mem** - Memory persistence, embeddings
- **serena** - Semantic code navigation
- **Context7** - Library documentation
- **sequential-thinking** - Structured reasoning
- **repomix** - Code context aggregation
- **firecrawl-mcp**, **tavily** - Research

### Existing Infrastructure
- ContextTracker (ready to wire in)
- ACE adapter (working, needs TOP-K injection)
- Metrics system (working, needs ContextTracker data)
- Benchmark suite (5 tiers, baseline established)

---

## Decision Log

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| 2026-01-10 | All | Deep research before planning | User feedback: understand before optimizing |
| 2026-01-10 | 01 | Completion detection is P0 | Real problem is not knowing when to stop |
| 2026-01-10 | 02 | Wire existing ContextTracker | Already built, just not integrated |
| 2026-01-10 | 03 | Add path context to prompt | Quick win, eliminates pwd calls |
| 2026-01-10 | 04 | Use existing MCP servers | claude-mem has embeddings, no new build |
| 2026-01-10 | 05 | Iteration-aware instructions | Full context only needed early |

---

**Next Action:** Execute Phase 01 (Completion Detection) - highest impact, directly addresses real problem.
