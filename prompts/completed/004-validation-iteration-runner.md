<objective>
MASTER ITERATION RUNNER: Execute validation phases 1-3 repeatedly until PERFECTION.

This is the orchestration prompt that coordinates all functional validation.
It runs each phase, measures results, and iterates until 100% pass rate.
</objective>

<execution_requirements>
CRITICAL - Use these tools:
- sequential-thinking MCP: For structured problem analysis
- claude-mem: For context preservation across iterations
- Opus 4.5 model: For maximum reasoning capability

This prompt orchestrates subagents for each validation phase.
</execution_requirements>

<validation_phases>
**Phase 1**: spawn_subagent() validation (prompts/001-spawn-subagent-validation.md)
- 4 scenarios covering real Claude CLI spawning
- Target: 4/4 PASS

**Phase 2**: Validation system functional tests (prompts/002-validation-system-functional.md)
- 8 scenarios covering semantic content checks
- Target: 8/8 PASS

**Phase 3**: End-to-end orchestration (prompts/003-e2e-orchestration-validation.md)
- 5 scenarios covering full workflow integration
- Target: 5/5 PASS

**Total**: 17 scenarios across 3 phases
**Perfection Criteria**: 17/17 PASS
</validation_phases>

<iteration_protocol>
```
ITERATION LOOP:
===============
iteration = 0
max_iterations = 5

WHILE iteration < max_iterations:
    iteration += 1

    # Run all phases
    phase1_results = execute_phase_1()
    phase2_results = execute_phase_2()
    phase3_results = execute_phase_3()

    # Calculate totals
    total_pass = phase1_results.pass + phase2_results.pass + phase3_results.pass
    total_tests = 17

    # Check for perfection
    IF total_pass == total_tests:
        DECLARE PERFECTION
        BREAK

    # Identify failures
    failures = collect_failures(phase1_results, phase2_results, phase3_results)

    FOR each failure:
        # Diagnose
        root_cause = analyze_failure(failure)

        # Fix
        fix = generate_fix(root_cause)
        apply_fix(fix)

        # Verify fix doesn't break other tests
        regression_check(fix)

    # Log iteration
    log_iteration(iteration, total_pass, failures, fixes_applied)

IF iteration == max_iterations AND total_pass < total_tests:
    ESCALATE - Human intervention required
```
</iteration_protocol>

<execution_steps>
1. **Initialize**
   - Create validation-evidence/iteration-run-{timestamp}/
   - Initialize iteration counter
   - Record start time

2. **Execute Phase 1** (spawn_subagent)
   - Run all 4 scenarios
   - Record: pass/fail, timing, errors
   - If failures: document and continue

3. **Execute Phase 2** (validation system)
   - Run all 8 scenarios
   - Record: pass/fail, timing, errors
   - If failures: document and continue

4. **Execute Phase 3** (E2E orchestration)
   - Run all 5 scenarios
   - Record: pass/fail, timing, errors
   - If failures: document and continue

5. **Evaluate Iteration**
   - Calculate total pass rate
   - If 17/17: PERFECTION ACHIEVED → Exit
   - If <17/17: Continue to step 6

6. **Fix Failures**
   - For each failure:
     - Use sequential-thinking to analyze root cause
     - Generate minimal fix
     - Apply fix
     - Run targeted re-test

7. **Regression Check**
   - Re-run all previously passing tests
   - Ensure fixes didn't break anything
   - If regression: revert and try different fix

8. **Iterate**
   - Increment counter
   - If counter < 5: Go to step 2
   - If counter >= 5: Escalate

9. **Final Report**
   - Total iterations required
   - Pass rate history
   - Fixes applied
   - Time to perfection
</execution_steps>

<measurement_metrics>
Track these metrics each iteration:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Phase 1 Pass Rate | 100% | X/4 |
| Phase 2 Pass Rate | 100% | X/8 |
| Phase 3 Pass Rate | 100% | X/5 |
| Total Pass Rate | 100% | X/17 |
| Iteration Count | ≤3 | N |
| Total Time | <10min | T |
| Regressions | 0 | R |

**Perfection = 17/17 PASS with 0 regressions**
</measurement_metrics>

<output>
Create comprehensive report: `./validation-evidence/functional-final/iteration-report.txt`

```
FUNCTIONAL VALIDATION ITERATION REPORT
======================================
Timestamp: {timestamp}
Total Iterations: {N}
Final Result: {PERFECTION/ESCALATE}

ITERATION HISTORY:
------------------
Iteration 1: {X}/17 pass
  - Failures: {list}
  - Fixes applied: {list}

Iteration 2: {Y}/17 pass
  - Failures: {list}
  - Fixes applied: {list}

... (continue for each iteration)

FINAL STATE:
------------
Phase 1 (spawn_subagent): {4}/4 PASS
Phase 2 (validation): {8}/8 PASS
Phase 3 (E2E): {5}/5 PASS

Total: {17}/17 PASS

PERFECTION ACHIEVED: {YES/NO}

Time to completion: {T}
Fixes required: {list of all fixes}

EVIDENCE FILES:
---------------
- validation-evidence/functional-01/spawn-validation.txt
- validation-evidence/functional-02/validation-system.txt
- validation-evidence/functional-03/e2e-orchestration.txt
- validation-evidence/functional-final/iteration-report.txt
```
</output>

<success_criteria>
**PERFECTION** = ALL of:
- 17/17 test scenarios PASS
- 0 regressions introduced
- All evidence files created
- Iteration count ≤ 5

If any condition not met after 5 iterations: ESCALATE to human.
</success_criteria>

<subagent_dispatch>
For each phase, dispatch a dedicated subagent:

```python
# Phase 1 subagent
spawn_subagent(
    type="validator",
    prompt=read_file("prompts/001-spawn-subagent-validation.md"),
    timeout=300
)

# Phase 2 subagent
spawn_subagent(
    type="validator",
    prompt=read_file("prompts/002-validation-system-functional.md"),
    timeout=300
)

# Phase 3 subagent
spawn_subagent(
    type="validator",
    prompt=read_file("prompts/003-e2e-orchestration-validation.md"),
    timeout=300
)
```

Each subagent should:
- Use sequential-thinking MCP
- Use claude-mem for context
- Use Opus 4.5 model
- Report results in structured format
</subagent_dispatch>
