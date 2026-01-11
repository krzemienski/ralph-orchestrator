# RALF Context Optimization - Implementation Roadmap

**Project:** RALF-CTXOPT
**Version:** v1.0
**Status:** Research Complete - Ready for Implementation
**Updated:** 2026-01-10 (Post Deep Research)

---

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ IMPLEMENTATION ORDER (by impact and dependency)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Phase 1: Fix Prompt Templates ────────┐  [1-2 hours] Quick Win              │
│                                       │                                     │
│ Phase 2: Wire ContextTracker ─────────┼──[2-4 hours] Foundation             │
│                                       │                                     │
│ Phase 3: Fix Path Hallucination ──────┘  [30 min] Quick Win                 │
│                                                                             │
│ Phase 4: Dynamic Instruction Templates ──[3-5 hours] Needs Phase 2          │
│                                                                             │
│ Phase 5: Semantic Skill Injection ───────[8-80 hours] Needs Phase 2         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Fix Prompt Templates

**Directory:** `.planning/phases/01-prompt-templates/`
**Status:** [ ] NOT STARTED
**Effort:** 1-2 hours
**Priority:** ★★★ Critical (enables reliable completion)

### Problem

The orchestration instructions don't tell Claude how to signal completion:
- Instructions say "mark subtasks complete" but don't specify format
- Example prompts use `**Status: COMPLETE**` (not detected)
- Only `- [x] TASK_COMPLETE` or `[x] TASK_COMPLETE` trigger detection
- Agent can also output "LOOP_COMPLETE" but instructions don't mention this

### Solution

**1. Update `_enhance_prompt_with_instructions()` in `base.py`:**

Add explicit completion instructions:
```python
## Task Completion
When ALL requirements are complete and verified:
1. Write this EXACT line to the prompt file: `- [x] TASK_COMPLETE`
   OR
2. Include "LOOP_COMPLETE" in your response

The orchestrator ONLY recognizes these specific signals.
```

**2. Update example prompts:**

Change from:
```markdown
**Status: COMPLETE** ✓
```

To:
```markdown
## Completion Status
- [x] TASK_COMPLETE
```

**3. Update documentation:**

Add "Completion Signals" section to `docs/guide/prompts.md`

### Deliverables

- [ ] Updated `base.py` with completion instructions
- [ ] Updated `examples/simple-task.md`
- [ ] Updated `examples/cli_tool.md`
- [ ] Updated `examples/web_scraper.md`
- [ ] Added completion section to prompts.md

### Validation Gate

- [ ] Agent outputs completion signal correctly
- [ ] Orchestrator stops after signal detected
- [ ] Benchmark runs complete in fewer iterations

---

## Phase 2: Wire ContextTracker

**Directory:** `.planning/phases/02-context-tracker/`
**Status:** [ ] NOT STARTED
**Effort:** 2-4 hours
**Priority:** ★★★ Foundation (enables measurement)

### Problem

ContextTracker exists at `monitoring/context_tracker.py` with:
- 6 MeasurePoints (ITERATION_START, AFTER_PROMPT_INJECT, AFTER_SKILLBOOK_INJECT, AFTER_TOOL_CALL, AFTER_RESPONSE, ITERATION_END)
- tiktoken-based token counting
- ASCII visualization and JSON export
- Stream logger integration

But it has ZERO usage in orchestrator.py.

### Solution

**1. Import in orchestrator.py (after line 27):**
```python
from .monitoring import ContextTracker, MeasurePoint
```

**2. Initialize in `__init__()` (after line 128):**
```python
self.context_tracker = ContextTracker(
    adapter_type=self.primary_tool,
    stream_logger=self.stream_logger
)
```

**3. Add measurements in `_aexecute_iteration()` (line 752+):**

```python
# After getting prompt (line 755)
self.context_tracker.measure(
    MeasurePoint.ITERATION_START,
    prompt,
    "initial_prompt",
    iteration=self.metrics.iterations
)

# After skillbook injection (line 760)
if self.learning_adapter:
    prompt = self.learning_adapter.inject_context(prompt)
    self.context_tracker.measure(
        MeasurePoint.AFTER_SKILLBOOK_INJECT,
        prompt,
        "skillbook_context",
        iteration=self.metrics.iterations
    )

# After response (line 795)
self.context_tracker.measure(
    MeasurePoint.AFTER_RESPONSE,
    prompt + (response.output or ""),
    "agent_response",
    iteration=self.metrics.iterations
)
```

**4. Add to summary output in `_print_summary()` (line 1057+):**
```python
if self.context_tracker:
    self.console.print_header("Context Usage Timeline")
    self.console.print_message(self.context_tracker.get_timeline_ascii())
    timeline_path = self.context_tracker.save_timeline()
```

### Deliverables

- [ ] ContextTracker imported and initialized
- [ ] 4+ measure() calls in iteration loop
- [ ] Timeline in console summary output
- [ ] Timeline JSON saved to metrics directory

### Validation Gate

- [ ] Metrics files include per-component token counts
- [ ] Can visualize: base_prompt vs skillbook vs response
- [ ] No performance regression (<5% slower)

---

## Phase 3: Fix Path Hallucination

**Directory:** `.planning/phases/03-path-hallucination/`
**Status:** [ ] NOT STARTED
**Effort:** 30 minutes
**Priority:** ★★☆ Quick Win

### Problem

Claude hallucinates paths each iteration:
- Iteration 1: `/Users/rtorres/Development/...`
- Iteration 2: `/Users/alpindale/repos/...`
- Iteration 3: `/Users/hkr/Projects/...`

Root cause: CWD is set in SDK options (`claude.py:217`) but NOT in the prompt text that Claude reads.

### Solution

**1. Update `_enhance_prompt_with_instructions()` signature:**
```python
def _enhance_prompt_with_instructions(self, prompt: str, cwd: str = None) -> str:
```

**2. Add CWD to instructions:**
```python
orchestration_instructions = f"""
ORCHESTRATION CONTEXT:
Working Directory: {cwd or os.getcwd()}

You are running within the Ralph Orchestrator loop...
"""
```

**3. Pass CWD from adapters:**
```python
# In claude.py aexecute():
enhanced_prompt = self._enhance_prompt_with_instructions(
    prompt,
    cwd=kwargs.get('cwd', os.getcwd())
)
```

### Deliverables

- [ ] Updated `base.py` with cwd parameter
- [ ] Updated `claude.py` to pass cwd
- [ ] CWD visible in enhanced prompt

### Validation Gate

- [ ] First tool call uses correct paths
- [ ] No `pwd` calls needed to discover directory
- [ ] No path-related errors

---

## Phase 4: Dynamic Instruction Templates

**Directory:** `.planning/phases/04-dynamic-templates/`
**Status:** [ ] NOT STARTED
**Effort:** 3-5 hours
**Priority:** ★★☆ Medium Impact
**Depends On:** Phase 2 (for measurement)

### Problem

Same ~800 token instructions appended every iteration:
- Iteration 1: ~800 tokens (needed)
- Iteration 4: ~800 tokens (redundant - Claude read scratchpad)
- Iteration 10: ~800 tokens (very redundant)

### Solution

**1. Pass iteration to enhancement method:**
```python
# In orchestrator.py _aexecute_iteration():
response = await self.current_adapter.aexecute(
    prompt,
    iteration=self.metrics.iterations,  # NEW
    ...
)

# In adapter aexecute():
iteration = kwargs.get('iteration', 1)
enhanced_prompt = self._enhance_prompt_with_instructions(prompt, iteration=iteration)
```

**2. Create two templates in base.py:**
```python
FULL_INSTRUCTIONS = """
ORCHESTRATION CONTEXT:
[Full 800-token instructions for iterations 1-3]
"""

CONDENSED_INSTRUCTIONS = """
ORCHESTRATION CONTEXT:
Iteration {iteration}. Continue from .agent/scratchpad.md.

KEY REMINDERS:
- One focused task per iteration
- Update scratchpad at end
- Signal completion: `- [x] TASK_COMPLETE` or output "LOOP_COMPLETE"
"""

def _enhance_prompt_with_instructions(self, prompt: str, iteration: int = 1) -> str:
    if iteration <= 3:
        template = FULL_INSTRUCTIONS
    else:
        template = CONDENSED_INSTRUCTIONS.format(iteration=iteration)
    return template + prompt
```

**3. Handle idempotency:**
```python
# Check for BOTH markers
if "ORCHESTRATION CONTEXT:" in prompt:
    return prompt  # Already enhanced
```

### Deliverables

- [ ] Iteration passed through adapter chain
- [ ] FULL_INSTRUCTIONS constant (~800 tokens)
- [ ] CONDENSED_INSTRUCTIONS constant (~150 tokens)
- [ ] Selection logic based on iteration

### Validation Gate

- [ ] Iterations 4+: ~650 fewer tokens
- [ ] Success rate: 100%
- [ ] No behavior drift
- [ ] Measured via ContextTracker (Phase 2)

---

## Phase 5: Semantic Skill Injection

**Directory:** `.planning/phases/05-skill-injection/`
**Status:** [ ] NOT STARTED
**Effort:** 8-80 hours (see options)
**Priority:** ★★☆ Scales with skillbook growth
**Depends On:** Phase 2 (for measurement)

### Problem

All skills injected regardless of relevance:
- Current: 2 skills (~55 tokens) - not a problem
- At 100 skills: ~3,000 tokens wasted if only 5 are relevant

### Solution Options

**Option A: Quick TOP-K by Score (8-16 hours)**

Sort skills by (helpful - harmful) score, inject TOP-5:
```python
def inject_context(self, prompt: str) -> str:
    skills = sorted(
        self.skillbook.skills(),
        key=lambda s: s.helpful - s.harmful,
        reverse=True
    )[:5]  # TOP-5

    skillbook_context = format_skills(skills)
    return f"{prompt}\n\n{skillbook_context}"
```

**Option B: Semantic Retrieval (40-80 hours)**

Full embedding-based approach:
1. Generate embeddings for each skill (all-MiniLM-L6-v2)
2. Store in skill schema (field exists but unused)
3. Embed current task/prompt
4. Retrieve TOP-5 by cosine similarity
5. Cache embeddings

### Deliverables (Option A)

- [ ] Skill sorting by score
- [ ] TOP-K selection (configurable K)
- [ ] Benchmark comparison

### Validation Gate

- [ ] Skillbook tokens reduced by 40-60% (at scale)
- [ ] Success rate maintained: 100%
- [ ] No "missing skill" failures

---

## Phase Tracking

| Phase | Status | Started | Completed | Validated |
|-------|--------|---------|-----------|-----------|
| 01 - Prompt Templates | 🟢 Complete | 2026-01-10 | 2026-01-10 | ✅ Unit Tests |
| 02 - Wire ContextTracker | 🟢 Complete | 2026-01-10 | 2026-01-10 | ✅ Unit Tests |
| 03 - Fix Path Hallucination | 🟢 Complete | 2026-01-10 | 2026-01-10 | ✅ Unit Tests |
| 04 - Dynamic Templates | 🟢 Complete | 2026-01-10 | 2026-01-10 | ✅ Unit Tests (~493 tokens saved) |
| 05 - Skill Injection (TOP-K) | 🟢 Complete | 2026-01-10 | 2026-01-10 | ✅ Unit Tests |

---

## Execution Strategy

**Recommended Order:**
1. Phase 1 (Prompt Templates) - Fixes completion reliability
2. Phase 3 (Path Hallucination) - Quick win, 30 min
3. Phase 2 (ContextTracker) - Enables measurement
4. Phase 4 (Dynamic Templates) - Uses measurement
5. Phase 5 (Skill Injection) - Uses measurement

**Parallelization:**
- Phases 1, 2, 3 can run in parallel (no dependencies)
- Phase 4 depends on Phase 2
- Phase 5 depends on Phase 2

---

## Available Infrastructure

### MCP Servers (15 Enabled)
- **claude-mem** - Memory persistence, potential for embeddings
- **serena** - Semantic code navigation
- **Context7** - Library documentation
- **sequential-thinking** - Structured reasoning
- **repomix** - Code context aggregation

### Existing Components
- ContextTracker (ready to wire in)
- ACE adapter (working, needs TOP-K)
- Metrics system (working, needs ContextTracker data)
- Completion detection (working, needs prompt updates)
