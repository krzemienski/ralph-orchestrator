# Context Optimization Experiment Plan

## Part 1: The Problem (In Plain English)

### What's Happening

Ralph orchestrator runs AI agents in loops. Each iteration, we send a prompt to the AI that includes:

- **System instructions** - How to behave, what rules to follow
- **Skillbook** - Previously learned strategies from ACE
- **Tool definitions** - What tools are available (MCP servers, etc.)
- **Dynamic context** - Recent outputs, error history
- **The actual task** - What we're asking the agent to do

Every one of these pieces uses **tokens**. Tokens cost money and take time to process.

### What We BELIEVE Is Happening

We believe some of these tokens are "wasted" - they don't contribute to task success. Examples:

1. **Repeated instructions**: We send the same 800-token instruction block on iteration 1 AND iteration 50. Does the agent really need to be told "commit your changes" for the 50th time?

2. **Irrelevant skills**: We inject ALL learned skills, even if only 1-2 are relevant to the current task.

3. **Duplicate skills**: Our skillbook currently has skills that say the same thing in slightly different words.

4. **Stale context**: Old error messages from 20 iterations ago that are no longer relevant.

### What We DON'T Know

**We don't actually have proof that any of this is waste.**

Our agents analyzed the code and made estimates, but:
- We haven't run the benchmark suite (the `docs/benchmarks/runs/` directory is empty)
- We don't measure WHERE tokens go (our ContextTracker exists but isn't wired in)
- We don't know if removing any of this context will break things

### Why This Matters

If we CAN reduce token usage without hurting success rate:
- **Cost savings**: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **Speed**: Less to process = faster iterations
- **Quality**: More "headroom" for actual work, less noise
- **Sustainability**: Long runs don't exhaust the context window

But if we reduce tokens and success rate drops, we've made things WORSE.

---

## Part 2: The Goal

### Primary Goal
Reduce tokens per iteration by **30%** without any regression in success rate.

### Constraints (Non-Negotiable)
- Success rate must be **equal or better** than baseline
- Iterations to complete must be **equal or fewer** than baseline
- No increase in errors or weird behaviors

### Secondary Goals (Nice to Have)
- Reduce total cost per benchmark run
- Reduce total time per benchmark run
- Better understand where tokens actually go

---

## Part 3: How We'll Know If We Succeeded

### Metrics We'll Track

| Metric | What It Measures | How We Measure It |
|--------|-----------------|-------------------|
| **Tokens/iteration** | Raw efficiency | ContextTracker measurements |
| **Tokens by component** | Where tokens go | Per-component breakdown |
| **Success rate** | Did tasks complete correctly? | Manual verification |
| **Iterations to complete** | How many loops needed? | Orchestrator metrics |
| **Total cost** | Money spent | CostTracker |
| **Total time** | Wall clock time | Timestamps |

### What "Success" Looks Like

For each optimization phase:
- Tokens/iteration decreases by expected amount (within 10% of hypothesis)
- Success rate stays at 100% (or improves)
- No new error types emerge

### What "Failure" Looks Like

Any of these means we STOP and investigate:
- Success rate drops below baseline (even by 1 task)
- New types of errors appear
- Iterations to complete increases
- Measured token savings don't match hypothesis (off by >25%)

---

## Part 4: The Experiment Phases

### Phase 0: Instrumentation (MUST DO FIRST)

**Objective**: Be able to measure where tokens go.

**Hypothesis**: N/A - this is measurement infrastructure.

**Action**:
1. Wire ContextTracker into the orchestrator loop
2. Add measurement points: iteration start, after prompt, after skills, after tools, iteration end
3. Output per-component token breakdown in benchmark results

**Measurement**: Can produce a report showing:
```
Iteration 1:
  System prompt:     500 tokens (12%)
  Skillbook:         150 tokens (4%)
  Tool definitions:  2000 tokens (48%)
  Dynamic context:   300 tokens (7%)
  Actual prompt:     400 tokens (10%)
  Response:          800 tokens (19%)
  TOTAL:             4150 tokens
```

**Validation Gate**:
- [ ] ContextTracker integrated into orchestrator
- [ ] Benchmark produces per-component token breakdown
- [ ] Can run same benchmark twice and get comparable numbers

**Failure Protocol**: This is infrastructure - if it doesn't work, we debug until it does. No optimization proceeds without measurement capability.

---

### Phase 1: Establish Baseline

**Objective**: Know our current numbers before making any changes.

**Hypothesis**: N/A - this is data collection.

**Action**:
1. Run the benchmark suite 3 times
2. Record all metrics for each run
3. Calculate mean and variance

**Expected Outcome** (our hypothesis to validate):
Based on agent analysis, we expect to see:
- Simple task (hello.py type): ~1,500 tokens/iteration
- Medium task: ~30,000 tokens/iteration
- Complex task: ~90,000 tokens/iteration

These are GUESSES. The baseline will give us REAL numbers.

**Validation Gate**:
- [ ] 3+ complete benchmark runs
- [ ] Metrics documented with variance
- [ ] Baseline document created with specific numbers
- [ ] Understand which component uses the most tokens

**Failure Protocol**: If variance is too high (>30%), investigate why benchmarks aren't reproducible before proceeding.

---

### Phase 2: Skillbook Deduplication (Low Risk)

**Objective**: Remove duplicate skills that say the same thing.

**Hypothesis**: Duplicate skills waste tokens and provide no additional value.

**Action**:
1. ✅ Already done - reduced from 4 skills to 2
2. Run benchmark suite 3 times
3. Compare to baseline

**Expected Outcome**:
- Skillbook tokens reduced by ~50% (was 4 skills, now 2)
- Success rate: Same as baseline
- No new errors

**Validation Gate**:
- [ ] Benchmark shows reduced skillbook tokens
- [ ] Success rate equals baseline
- [ ] No new error types

**Failure Protocol**: If success rate drops or new errors appear, the "duplicates" weren't actually duplicates - they provided value. Revert and investigate.

---

### Phase 3: Iteration-Aware Instruction Scaling (Low Risk)

**Objective**: Send shorter instructions on later iterations.

**Hypothesis**: After 5+ iterations, the agent has "learned" the instructions and doesn't need the full verbose version every time.

**Action**:
1. Modify `_enhance_prompt_with_instructions()` to accept iteration number
2. Iterations 1-5: Full instructions (~800 tokens)
3. Iterations 6+: Condensed instructions (~150 tokens)
4. Run benchmark suite 3 times
5. Compare to post-Phase-2 baseline

**Expected Outcome**:
- Iterations 1-5: Same tokens as baseline
- Iterations 6+: ~650 fewer tokens per iteration
- Success rate: Same as baseline
- For a 20-iteration run: ~9,750 tokens saved (650 × 15)

**Validation Gate**:
- [ ] Token reduction observed on iterations 6+
- [ ] Reduction matches expectation (650 ± 100 tokens)
- [ ] Success rate equals baseline
- [ ] No new errors, no behavior drift

**Failure Protocol**: If success rate drops, the agent DID need those instructions. Options:
- Try condensed version at iteration 10+ instead of 5+
- Try different condensed wording
- Abandon this optimization if it can't work

---

### Phase 4: Task-Aware Skill Filtering (Medium Risk)

**Objective**: Only inject skills relevant to the current task phase.

**Hypothesis**: Injecting irrelevant skills wastes tokens and may confuse the agent.

**Action**:
1. Add task phase detection (exploration, implementation, debugging, completion)
2. Tag skills with relevant phases
3. Only inject skills matching current phase
4. Run benchmark suite 3 times
5. Compare to post-Phase-3 baseline

**Expected Outcome**:
- Skillbook tokens reduced by 50-80% (only relevant skills injected)
- Success rate: Same or BETTER (more relevant skills = better guidance)
- No new errors

**Validation Gate**:
- [ ] Token reduction observed in skillbook portion
- [ ] Success rate equals or exceeds baseline
- [ ] Skills used in successful iterations match injected skills
- [ ] No evidence of "missing skill" causing failures

**Failure Protocol**: If success rate drops, our relevance scoring is wrong. Options:
- Improve phase detection
- Improve skill tagging
- Fall back to "inject all skills" for certain phases
- Abandon if filtering fundamentally doesn't work

---

### Phase 5+: Further Optimizations

**Only proceed here if Phases 2-4 passed validation gates.**

Candidates (in order of risk):
- State-based prompt templates
- Error pattern distillation
- Context compression (higher risk)
- MCP context server (highest complexity)

Each would follow the same structure:
- Clear hypothesis
- Expected outcome (numbers)
- Validation gate
- Failure protocol

---

## Part 5: Benchmark Methodology

### Benchmark Tasks

| Task | Type | Expected Iterations | Purpose |
|------|------|---------------------|---------|
| hello.py | Simple | 1-2 | Baseline simple task |
| goodbye.py | Simple | 1-2 | Verify repeatability |
| Add feature X | Medium | 5-10 | Real coding task |
| Debug issue Y | Complex | 10-20 | Error recovery |

### Statistical Significance

- Run each benchmark **3 times minimum**
- Calculate mean and standard deviation
- A change is "significant" if the difference is **>2 standard deviations**
- If variance is high, run 5 times instead

### Fair Comparison

- Same machine, same conditions
- Same git commit for baseline
- Clear git tag for each optimization phase
- No other changes between phases

---

## Part 6: Risks and Mitigations

### Risk: Optimization breaks something

**Mitigation**:
- Make one change at a time
- Full benchmark suite after each change
- Easy rollback (git revert)

### Risk: Measurements are wrong

**Mitigation**:
- Verify ContextTracker math manually
- Cross-check with Anthropic API usage reports
- Sanity check: tokens × cost should match actual billing

### Risk: Variance too high to detect changes

**Mitigation**:
- More benchmark runs
- Control for external factors (time of day, system load)
- Use percentage change, not absolute numbers

### Risk: We're optimizing the wrong thing

**Mitigation**:
- Phase 0 tells us WHERE tokens actually go
- Maybe tool definitions are 48% and skills are 2% - then optimize tools first
- Let data drive priorities, not assumptions

---

## Appendix: Current State

### What We Know
- ContextTracker exists in `src/ralph_orchestrator/monitoring/context_tracker.py`
- ContextTracker is NOT integrated into the orchestrator loop
- Benchmark methodology exists in `docs/benchmarks/METHODOLOGY.md`
- Benchmark runs directory is EMPTY

### What We've Done
- ✅ Analyzed codebase with 6 research agents
- ✅ Deduplicated skillbook (4 → 2 skills)
- ✅ Documented similarity_decisions for audit trail

### What We Haven't Done
- ❌ Integrated ContextTracker
- ❌ Run any benchmarks
- ❌ Established a baseline
- ❌ Validated any optimization hypothesis

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-10 | Create this experiment plan | Moving from "list of features" to "validated experiments" |
| 2026-01-10 | Phase 0 must be measurement | Can't optimize what we can't measure |
| 2026-01-10 | Validation gates required | Don't stack unvalidated changes |

---

**This document is the source of truth for context optimization work. Do not proceed to the next phase until the current phase's validation gate passes.**
