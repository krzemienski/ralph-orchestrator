# RALF Context Optimization - Project Brief

**Created:** 2026-01-10 (Post Deep Research)
**Status:** Ready for Implementation
**Project Code:** RALF-CTXOPT

---

## How RALF Actually Works (Verified Understanding)

### The Orchestration Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Each iteration = FRESH Claude conversation                                  │
│                                                                             │
│ Context persistence via FILE SYSTEM:                                        │
│   - .agent/scratchpad.md  → Agent reads/updates each iteration              │
│   - Prompt file           → Can contain completion markers                  │
│   - dynamic_context       → Adds "## Previous Context" section              │
│   - ACE skillbook         → Appended to every prompt                        │
└─────────────────────────────────────────────────────────────────────────────┘

Iteration Flow:
1. Load prompt from file
2. inject_context() adds skillbook (if learning enabled)
3. _enhance_prompt_with_instructions() adds ~800 tokens
4. Send to Claude adapter
5. Check completion signals
6. If not complete: next iteration
```

### Completion Detection (ALREADY EXISTS - Two Mechanisms)

**Mechanism A: TASK_COMPLETE Marker** (orchestrator.py:597, 1211-1233)
- Checks prompt file for: `- [x] TASK_COMPLETE` or `[x] TASK_COMPLETE`
- EXACT MATCH only - no variations accepted
- Called BEFORE each iteration starts

**Mechanism B: LOOP_COMPLETE Promise** (orchestrator.py:710, 1235-1244)
- Checks agent output for configurable string (default: "LOOP_COMPLETE")
- Called AFTER successful iteration
- Substring match - more flexible

**Why Benchmarks Show "Unnecessary" Iterations:**
- Prompts use `**Status: COMPLETE**` (not detected)
- Example prompts don't have `- [x] TASK_COMPLETE`
- Instructions don't tell Claude to output "LOOP_COMPLETE"
- This is PROMPT DESIGN, not a code bug

---

## Research Findings Summary

### Issue 1: ContextTracker NOT Wired In

| Aspect | Finding |
|--------|---------|
| **Component** | `monitoring/context_tracker.py` - fully implemented |
| **MeasurePoints** | 6: ITERATION_START, AFTER_PROMPT_INJECT, AFTER_SKILLBOOK_INJECT, AFTER_TOOL_CALL, AFTER_RESPONSE, ITERATION_END |
| **Token Counting** | tiktoken (accurate) or 4-chars/token fallback |
| **Context Limits** | Claude: 200K, Gemini: 32K, QChat/Kiro: 8K |
| **Current Usage** | ZERO - not imported or initialized in orchestrator.py |
| **Impact** | Cannot measure where tokens go per-component |
| **Fix Effort** | ~2-4 hours - just wire it in |

### Issue 2: Prompt Templates Missing Completion Instructions

| Aspect | Finding |
|--------|---------|
| **Detection Mechanisms** | 2 exist, both working |
| **Agent Instructions** | DON'T explicitly tell Claude to write `- [x] TASK_COMPLETE` |
| **Example Prompts** | Use wrong formats (`**Status: COMPLETE**` won't trigger) |
| **Documentation** | Mentions marker in overview but not prompts guide |
| **Impact** | Prompts run until max_iterations even when done |
| **Fix Effort** | ~1-2 hours - update templates + documentation |

### Issue 3: Path Hallucination

| Aspect | Finding |
|--------|---------|
| **Root Cause** | CWD set in SDK options but NOT in prompt text |
| **Behavior** | Claude hallucinates `/Users/alpindale/`, `/Users/hkr/`, etc. |
| **Self-Correction** | Claude corrects after `pwd` but wastes tool calls |
| **Code Location** | `claude.py:214-219` has CWD, `base.py:95-160` doesn't use it |
| **Impact** | Extra tool calls, wasted time per iteration |
| **Fix Effort** | ~30 minutes - add CWD to instructions |

### Issue 4: Full Skillbook Injection

| Aspect | Finding |
|--------|---------|
| **Current Behavior** | ALL skills injected via `wrap_skillbook_context()` |
| **Current Size** | 2 skills (~55 tokens) |
| **At Scale** | 100 skills would be ~3,000 tokens |
| **Filtering** | None - no TOP-K, no semantic matching |
| **Infrastructure** | Embedding field exists in schema but unused |
| **Impact** | Scales poorly as skillbook grows |
| **Fix Effort** | Quick (8-16h): TOP-K by score. Full (40-80h): semantic embeddings |

### Issue 5: Same Instructions Every Iteration

| Aspect | Finding |
|--------|---------|
| **Current Size** | ~600-800 tokens per iteration |
| **Iteration Awareness** | NOT passed to `_enhance_prompt_with_instructions()` |
| **Condensed Template** | Does not exist |
| **Idempotency** | Protected by marker check - complicates iteration-aware logic |
| **Impact** | ~650 wasted tokens per iteration 4+ |
| **Fix Effort** | ~3-5 hours - pass iteration, create condensed template |

---

## Optimization Phases (Prioritized)

### Phase 1: Fix Prompt Templates (Quick Win - 1-2 hours)
**Problem:** Prompts don't tell Claude how to signal completion
**Solution:**
- Update `_enhance_prompt_with_instructions()` to include explicit completion instructions
- Update example prompts to use proper `- [x] TASK_COMPLETE` format
- Add "Completion Signals" section to documentation

### Phase 2: Wire ContextTracker (Foundation - 2-4 hours)
**Problem:** No per-component token visibility
**Solution:**
- Import ContextTracker in orchestrator.py
- Add measure() calls at 4-5 key points in iteration loop
- Include timeline in metrics output

### Phase 3: Fix Path Hallucination (Quick Win - 30 min)
**Problem:** Claude hallucinates wrong paths
**Solution:**
- Add `WORKING DIRECTORY: {cwd}` to orchestration instructions
- Pass cwd from adapter to enhancement method

### Phase 4: Dynamic Instruction Templates (Medium - 3-5 hours)
**Problem:** Same 800-token instructions every iteration
**Solution:**
- Pass iteration number to enhancement method
- Create FULL_INSTRUCTIONS (~800 tokens) for iterations 1-3
- Create CONDENSED_INSTRUCTIONS (~150 tokens) for iterations 4+

### Phase 5: Semantic Skill Injection (Larger - 8-80 hours)
**Problem:** All skills injected regardless of relevance
**Solution Options:**
- Quick (8-16h): TOP-K by helpful-harmful score
- Full (40-80h): Embedding-based semantic retrieval

---

## Success Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| Per-component token visibility | None | Full |
| Path hallucination | Every iteration | Eliminated |
| Instructions (iter 4+) | ~800 tokens | ~150 tokens |
| Completion detection | Prompt-dependent | Reliable |
| Skillbook tokens (at 100 skills) | ~3000 | ~600 (TOP-5) |

---

## Key Files

```
src/ralph_orchestrator/
├── orchestrator.py          # Main loop - needs ContextTracker + iteration passing
├── context.py               # ContextManager (working)
├── monitoring/
│   └── context_tracker.py   # Token tracking (ready to wire in)
├── learning/
│   └── ace_adapter.py       # Skillbook injection (needs TOP-K)
└── adapters/
    ├── base.py              # _enhance_prompt_with_instructions (needs updates)
    └── claude.py            # Has CWD, needs to pass to base.py

examples/                    # Need completion marker examples
docs/guide/prompts.md        # Needs completion section
```
