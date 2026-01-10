# ACE + RALPH Benchmark & Iteration

<objective>
Execute phases 3-5 of the plan: Create benchmarks, measure improvement, iterate until learning demonstrably improves RALPH.

Purpose: Prove and document that ACE learning provides measurable benefits
Output: Benchmark suite, results comparison, improvement documentation
</objective>

<context>
ACE Research: @.prompts/006-ace-docs-research/ace-docs-research.md
RALPH Research: @.prompts/007-ralph-integration-research/ralph-integration-research.md
Implementation Plan: @.prompts/008-ace-ralph-plan/ace-ralph-plan.md
Implementation: @.prompts/009-ace-ralph-implement/SUMMARY.md

ACE integration should now be working. Time to measure its impact.
</context>

<requirements>
**Phase 3 - Benchmark Infrastructure:**
- Create benchmark prompt suite (5-10 carefully designed prompts)
- Create `scripts/run-benchmark.sh` runner script
- Integrate with monitoring dashboard for metrics capture
- Document baseline methodology

**Phase 4 - Measure Improvement:**
- Run benchmarks WITHOUT learning (baseline)
- Run benchmarks WITH learning enabled
- Capture metrics: iteration count, tokens, time, success rate
- Compare and document differences

**Phase 5 - Document & Iterate:**
- Analyze skillbook contents after learning runs
- Document which skills contributed to improvements
- If no improvement: tune prompts, reflection, retry
- Create final improvement report
</requirements>

<implementation>
**Benchmark Prompt Design Principles:**
1. **Repetitive Pattern Tasks** - Benefits from remembering patterns
   - Multiple similar file modifications
   - Repeated code structure creation

2. **Error-Prone Tasks** - Benefits from learning pitfalls
   - Tasks that commonly fail first attempt
   - Tasks with non-obvious requirements

3. **Project-Specific Tasks** - Benefits from learning conventions
   - Tasks following RALPH coding patterns
   - Tasks using project-specific structures

**Metrics Capture:**
Use monitoring dashboard and JSONL logs to capture:
- `.agent/logs/ralph-*.jsonl` for iteration data
- `.agent/metrics/*.json` for aggregated stats
- Timestamps for duration calculation
- Token counts from cost tracker

**Iteration Strategy:**
If initial benchmarks show no improvement:
1. Analyze skillbook - are skills being extracted?
2. Check skill quality - are they actionable?
3. Tune reflection prompts in ACE adapter
4. Try different prompt categories
5. Increase learning iterations before measurement
</implementation>

<output>
Create files:
- `scripts/run-benchmark.sh` - Benchmark runner with metrics capture
- `scripts/benchmark-prompts/` - Directory of benchmark prompt files
  - `01-repetitive-pattern.txt`
  - `02-error-recovery.txt`
  - `03-project-specific.txt`
  - ... (5-10 prompts total)
- `docs/benchmarks/BASELINE.md` - Baseline results
- `docs/benchmarks/LEARNING_RESULTS.md` - Learning-enabled results
- `docs/benchmarks/ANALYSIS.md` - Comparison and analysis
- `docs/ACE_LEARNING_ANALYSIS.md` - What causes improvements
</output>

<benchmark_runner_spec>
```bash
#!/bin/bash
# scripts/run-benchmark.sh
# ABOUTME: Run benchmark suite with or without learning, capture metrics

LEARNING_MODE="${1:-disabled}"  # "enabled" or "disabled"
OUTPUT_DIR="docs/benchmarks/run-$(date +%Y%m%d-%H%M%S)"

# Clear skillbook for fresh start (if baseline)
# Run each prompt in benchmark-prompts/
# Capture metrics for each run
# Generate summary report
```

Key features:
- Clear skillbook option for baseline runs
- Sequential execution of all prompts
- Metrics capture per-prompt and aggregate
- Markdown report generation
</benchmark_runner_spec>

<verification>
**Phase 3 Validation:**
```bash
# Benchmark runner script works
./scripts/run-benchmark.sh disabled --dry-run

# Prompts directory exists with 5+ prompts
ls scripts/benchmark-prompts/

# Metrics captured properly
cat docs/benchmarks/run-*/summary.json
```

**Phase 4 Validation:**
```bash
# Baseline run completes
./scripts/run-benchmark.sh disabled

# Learning run completes
./scripts/run-benchmark.sh enabled

# Results documented
cat docs/benchmarks/BASELINE.md
cat docs/benchmarks/LEARNING_RESULTS.md
```

**Phase 5 Validation:**
```bash
# Skillbook has learned skills
cat .agent/skillbook/skillbook.json | jq '.skills | length'

# Analysis document exists and shows improvement
cat docs/benchmarks/ANALYSIS.md
cat docs/ACE_LEARNING_ANALYSIS.md
```
</verification>

<success_criteria>
**Minimum Success:**
- Benchmark suite created with 5+ prompts
- Baseline metrics documented
- Learning-enabled metrics documented
- At least ONE measurable improvement demonstrated:
  - Fewer iterations (≥10% reduction)
  - Lower token usage (≥10% reduction)
  - Faster completion (≥10% reduction)
  - Higher success rate (any improvement)

**Full Success:**
- Multiple metrics show improvement
- Clear documentation of what causes improvement
- Reproducible methodology for future benchmarks
- Skills in skillbook directly correlate to improvements
- SUMMARY.md with quantified improvement percentages
</success_criteria>

<iteration_protocol>
If benchmarks show NO improvement after initial run:

1. **Check Skillbook Quality**
   - Are skills being extracted? (skillbook.json not empty)
   - Are skills relevant to tasks? (review skill text)

2. **Check Skill Injection**
   - Are skills being injected? (check enhanced prompts)
   - Is injection happening at right point?

3. **Tune Reflection**
   - Adjust reflection prompts in ace_adapter.py
   - Make skill extraction more targeted

4. **Adjust Benchmark Prompts**
   - Make prompts more repetitive (easier to learn)
   - Add more iterations before measurement
   - Use simpler, more focused tasks

5. **Document Findings**
   - Even "no improvement" is a valid finding
   - Document what was tried and why it didn't work
   - Propose next steps
</iteration_protocol>

<summary_requirements>
Create `.prompts/010-ace-ralph-benchmark/SUMMARY.md`

Must include:
- **One-liner**: Improvement percentage or "baseline established"
- **Benchmark Results**: Table comparing baseline vs learning
- **Key Improvements**: Which metrics improved, by how much
- **Skillbook Analysis**: What skills were learned
- **What Causes Improvement**: Explanation of learning benefits
- **Decisions Made**: Benchmark design choices
- **Blockers Encountered**: Issues during benchmarking
- **Next Step**: Either "Learning working - iterate further" or "Investigate no improvement"
</summary_requirements>

<constraints>
**CRITICAL:**
- Do NOT write pytest or unit tests
- Use ONLY end-to-end benchmark execution
- Measure with monitoring dashboard and logs
- Document real execution results, not simulated
</constraints>
