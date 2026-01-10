# ACE + RALPH Integration Plan

**5-phase implementation plan to integrate ACE learning into RALPH with benchmark-proven improvement (target: 15-25% iteration reduction).**

## Version
v1 - Initial comprehensive plan based on ACE docs and RALPH integration research

## Phase Overview

| Phase | Name | Objective | Effort |
|-------|------|-----------|--------|
| 1 | fix-critical-bugs | Implement async learning worker, shutdown save, rollback learning | 4-6 hrs |
| 2 | proper-ace-integration | Verify v2.1 prompts, add deduplication, configure efficient models | 3-4 hrs |
| 3 | benchmark-infrastructure | Create 12 benchmark prompts, runner script, establish baseline | 5-7 hrs |
| 4 | measure-improvement | Run learning-enabled benchmarks, compare against baseline | 4-6 hrs |
| 5 | documentation-iteration | Document findings, create production skillbook, final report | 3-5 hrs |

**Total Estimated Effort**: 19-28 hours

## Key Deliverables

### Phase 1 (Critical)
- Async learning worker (currently blocks main loop)
- Skillbook persistence on shutdown
- Learning from checkpoint rollbacks
- Richer execution traces for Reflector

### Phase 3 (Benchmark Infrastructure)
- **12 benchmark prompts** across 3 categories:
  - Repetitive tasks (4 prompts) - pattern learning
  - Error recovery (4 prompts) - failure learning
  - Project-specific (4 prompts) - convention learning

### Phase 4 (Measurement)
- Baseline runs (learning disabled, 3 runs)
- Learning pass 1 (empty skillbook)
- Learning pass 2 (trained skillbook)
- Target: 20% fewer iterations, 15% token reduction

## Benchmark Strategy

### Prompt Types
| Category | Focus | Example |
|----------|-------|---------|
| Repetitive | Pattern learning | Create 5 similar validator functions |
| Error Recovery | Failure learning | Fix broken async/await code |
| Project-Specific | Convention learning | Add new RALPH adapter |

### Primary Metrics
| Metric | Improvement Target |
|--------|-------------------|
| Iteration count | 20% reduction |
| Token usage | 15% reduction |
| Success rate | Higher first-try success |
| Rollback count | 50% reduction |

## Decisions Needed

1. **ACE Model**: Use gpt-4o-mini for ACE operations (cheaper) or same as main agent?
   - Recommendation: gpt-4o-mini (10x cheaper, sufficient for reflection)

2. **Skillbook Scope**: Project-specific or global (user-level)?
   - Recommendation: Project-specific initially, evaluate global later

3. **Version Control**: Commit skillbook to git?
   - Recommendation: Yes, enables team learning sharing

## Blockers

| Blocker | Status | Mitigation |
|---------|--------|------------|
| None critical | - | Plan can start immediately |
| Optional: gpt-4o-mini access | Unknown | Can use claude-sonnet if needed (higher cost) |
| Optional: Monitoring dashboard | Unknown | JSON output sufficient for analysis |

## Risk Assessment

- **Medium**: Learning overhead may exceed benefits for simple tasks
  - Mitigation: Include varied task lengths, find breakeven point

- **Low**: LangChain/Pydantic conflicts may resurface
  - Mitigation: Pin ACE version

## Files Created
- `/Users/nick/Desktop/ralph-orchestrator/.prompts/008-ace-ralph-plan/ace-ralph-plan.md` - Full implementation plan with benchmark design

## Dependencies
- Phase 1: None (can start immediately)
- Phase 2: Phase 1 complete
- Phase 3: Phase 2 complete
- Phase 4: Phase 3 baseline results
- Phase 5: Phase 4 shows improvement

## Confidence
**0.85 (High)** - Based on comprehensive research, existing functional integration, and proven ACE benchmark results (+17% in external tests)

## Next Step

**Execute Phase 1: Fix critical bugs**

Start with task 1.1 (async learning worker) as it's the highest-impact fix. The current implementation blocks iteration execution during learning, which defeats the purpose of background learning.

```bash
# Verify current state
ralph run --learning -p "test task" --verbose
# Should see learning operations in logs, check if they block execution
```
