# ACE Learning Benchmark Methodology

This document describes the methodology for benchmarking ACE learning improvements in RALPH orchestrator.

## Purpose

The benchmark suite measures whether ACE learning provides measurable improvements to RALPH's execution:
- **Iteration count reduction**: Tasks complete in fewer iterations
- **Token efficiency**: Less context needed per iteration
- **Success rate**: Higher first-try success rate
- **Error recovery**: Faster recovery from common mistakes

## Benchmark Design Principles

### 1. Repetitive Pattern Tasks

Tasks that repeat similar patterns across multiple operations. Learning should:
- Recognize the pattern after 1-2 examples
- Apply the pattern more efficiently to subsequent items
- Reduce iterations for the complete task

**Examples:**
- Creating multiple validation functions
- Adding logging to multiple modules
- Creating multiple test fixtures

### 2. Error-Prone Tasks

Tasks that commonly fail on first attempt. Learning should:
- Remember what went wrong previously
- Avoid the same mistakes in future runs
- Apply learned error-recovery patterns

**Examples:**
- Fixing import errors
- Handling async/await correctly
- Cross-platform path handling

### 3. Project-Specific Tasks

Tasks requiring understanding of RALPH's conventions. Learning should:
- Capture project-specific patterns
- Apply consistent coding style
- Follow established conventions

**Examples:**
- Creating new adapters
- Adding CLI flags
- Extending the metrics system

## Benchmark Prompts

The benchmark suite includes 10 prompts across three categories:

| ID | Category | Prompt | What It Tests |
|----|----------|--------|---------------|
| 01 | Repetitive | Create 4 validators | Pattern recognition |
| 02 | Repetitive | Create 4 fixtures | Pattern application |
| 03 | Repetitive | Add logging | Consistency |
| 04 | Error | Fix imports | Error recovery |
| 05 | Error | Async patterns | Common pitfalls |
| 06 | Error | Path handling | Cross-platform |
| 07 | Project | Create adapter | Convention learning |
| 08 | Project | Add CLI flag | Pattern matching |
| 09 | Project | Add metric | System understanding |
| 10 | Project | Add config | Multi-file changes |

## Running Benchmarks

### Prerequisites

```bash
# Ensure ralph is installed
pip install ralph-orchestrator[learning]

# Ensure jq is installed (for JSON parsing)
brew install jq  # macOS
apt install jq   # Linux
```

### Running Baseline (No Learning)

```bash
# Run without learning to establish baseline
./scripts/run-benchmark.sh disabled
```

This creates a baseline measurement with:
- Learning completely disabled
- No skillbook injection
- Pure agent performance

### Running with Learning (Pass 1 - Training)

```bash
# Clear skillbook and run with learning
CLEAR_SKILLBOOK=true ./scripts/run-benchmark.sh enabled
```

This "trains" the skillbook by:
- Starting with empty skillbook
- Learning from each prompt execution
- Building up skills progressively

### Running with Learning (Pass 2 - Evaluation)

```bash
# Run again with trained skillbook
./scripts/run-benchmark.sh enabled
```

This measures improvement by:
- Using skillbook from Pass 1
- Comparing against baseline
- Showing learning retention

### Dry Run

```bash
# See what would be run without executing
DRY_RUN=true ./scripts/run-benchmark.sh enabled
```

## Metrics Captured

### Per-Prompt Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| `iterations` | Number of iterations to complete | RALPH output |
| `tokens` | Total tokens used | RALPH metrics |
| `duration_seconds` | Wall clock time | Script timing |
| `success` | Whether task completed | Exit status |
| `skills_learned` | New skills added | Skillbook diff |

### Aggregate Metrics

| Metric | Calculation | Target |
|--------|-------------|--------|
| `avg_iterations` | Total / prompts | 20% reduction |
| `avg_tokens` | Total / prompts | 15% reduction |
| `success_rate` | Successful / total | Higher is better |
| `skills_learned` | Net new skills | Positive growth |

## Expected Improvements

Based on ACE framework research (+17.1% on AppWorld benchmark):

| Metric | Baseline | Learning Pass 2 | Target Improvement |
|--------|----------|-----------------|-------------------|
| Iterations | ~8 avg | ~6.4 avg | 20% reduction |
| Tokens | ~10K avg | ~8.5K avg | 15% reduction |
| Success Rate | ~75% | ~85%+ | +10% absolute |

## Comparison Methodology

### Statistical Significance

1. **Multiple runs**: Run baseline 3 times to establish variance
2. **Mean comparison**: Compare mean of learning runs to baseline mean
3. **Per-prompt analysis**: Identify which prompts benefit most

### A/B Comparison

```bash
# Run baseline 3 times
for i in 1 2 3; do
  ./scripts/run-benchmark.sh disabled
done

# Run learning sequence
CLEAR_SKILLBOOK=true ./scripts/run-benchmark.sh enabled  # Training
./scripts/run-benchmark.sh enabled  # Evaluation

# Compare results in docs/benchmarks/runs/
```

### Output Structure

```
docs/benchmarks/runs/
├── disabled-20260110-100000/
│   ├── 01-repetitive-validators.json
│   ├── 02-repetitive-fixtures.json
│   ├── ...
│   ├── summary.json
│   └── REPORT.md
├── enabled-20260110-110000/
│   ├── ...
│   ├── summary.json
│   └── REPORT.md
└── enabled-20260110-120000/
    └── ...
```

## Environment Configuration

### Recommended Settings

```bash
export MAX_ITERATIONS=15          # Enough for complex tasks
export MODEL=claude-sonnet-4-5-20250929     # Main agent
export LEARNING_MODEL=gpt-4o-mini # ACE operations (cheaper)
export SKILLBOOK_PATH=.agent/skillbook/skillbook.json
```

### Reproducibility

For reproducible results:
1. Use same model versions
2. Run on same hardware
3. Control for API latency (run at similar times)
4. Clear any cached state between baseline runs

## Interpreting Results

### Good Results

- **20%+ iteration reduction**: Learning is working well
- **Consistent improvement**: Benefits across prompt categories
- **Skill accumulation**: Skillbook growing with relevant skills

### Marginal Results

- **5-15% improvement**: Learning working but limited benefit
- **Inconsistent improvement**: Only some prompts benefit
- **Consider**: Task complexity, prompt design, skillbook quality

### No Improvement

- **0% or negative**: Learning may not help these task types
- **Investigate**: Skillbook contents, reflection quality, prompt design
- **Consider**: These tasks may not benefit from memory

## Troubleshooting

### High Variance Between Runs

- Increase MAX_ITERATIONS to allow more attempts
- Check for non-deterministic elements in prompts
- Consider API rate limiting effects

### Learning Not Improving Results

- Check skillbook is being saved (`ls -la .agent/skillbook/`)
- Verify skills are being injected (check logs)
- Review skill quality in skillbook.json

### Benchmark Takes Too Long

- Reduce MAX_ITERATIONS
- Use cheaper model for testing
- Run subset of prompts first

## Next Steps

After running benchmarks:

1. **Analyze results**: Compare `summary.json` files
2. **Review skillbook**: Check quality of learned skills
3. **Iterate on prompts**: Add more effective benchmark prompts
4. **Document findings**: Update `docs/ACE_LEARNING_ANALYSIS.md`
