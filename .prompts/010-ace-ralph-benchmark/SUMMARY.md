# ACE + RALPH Benchmark Infrastructure Summary

**Benchmark suite with 10 prompts across 3 categories, runner script with metrics capture, and comprehensive methodology documentation**

**Version:** v1.0
**Completed:** January 10, 2026

---

## One-Liner

Created complete benchmark infrastructure to measure ACE learning improvements: 10 benchmark prompts, automated runner script, methodology documentation, and expected improvements analysis.

---

## Benchmark Suite

### Prompts Created (10 total)

| File | Category | Description |
|------|----------|-------------|
| `01-repetitive-validators.txt` | Repetitive | Create 4 validation functions |
| `02-repetitive-fixtures.txt` | Repetitive | Create 4 pytest fixtures |
| `03-repetitive-logging.txt` | Repetitive | Add structured logging |
| `04-error-imports.txt` | Error Recovery | Fix broken imports |
| `05-error-async.txt` | Error Recovery | Correct async patterns |
| `06-error-paths.txt` | Error Recovery | Cross-platform path handling |
| `07-project-adapter.txt` | Project-Specific | Create new adapter |
| `08-project-cli-flag.txt` | Project-Specific | Add --dry-run flag |
| `09-project-metric.txt` | Project-Specific | Add rollback_count metric |
| `10-project-config.txt` | Project-Specific | Add checkpoint_interval config |

### Categories Rationale

1. **Repetitive (01-03)**: Tasks with repeating patterns - learning should recognize and apply patterns efficiently
2. **Error Recovery (04-06)**: Common pitfall tasks - learning should remember and avoid mistakes
3. **Project-Specific (07-10)**: RALPH convention tasks - learning should capture project patterns

---

## Runner Script

**Location:** `scripts/run-benchmark.sh`

### Key Features

- **Dual mode**: `enabled` (with learning) or `disabled` (baseline)
- **Skillbook control**: `CLEAR_SKILLBOOK=true` to start fresh
- **Metrics capture**: Iterations, tokens, duration, success, skills learned
- **JSON output**: Per-prompt and aggregate results
- **Markdown report**: Human-readable summary
- **Dry run mode**: `DRY_RUN=true` to preview without execution

### Usage Examples

```bash
# Run baseline
./scripts/run-benchmark.sh disabled

# Run with learning (training pass)
CLEAR_SKILLBOOK=true ./scripts/run-benchmark.sh enabled

# Run with learning (evaluation pass)
./scripts/run-benchmark.sh enabled

# Preview what would run
DRY_RUN=true ./scripts/run-benchmark.sh enabled
```

### Output Structure

```
docs/benchmarks/runs/
├── disabled-YYYYMMDD-HHMMSS/
│   ├── 01-repetitive-validators.json
│   ├── ...
│   ├── summary.json
│   └── REPORT.md
└── enabled-YYYYMMDD-HHMMSS/
    └── ...
```

---

## Methodology

**Location:** `docs/benchmarks/METHODOLOGY.md`

### How to Run Baseline vs Learning

1. **Baseline (3 runs for variance)**
   ```bash
   ./scripts/run-benchmark.sh disabled
   ./scripts/run-benchmark.sh disabled
   ./scripts/run-benchmark.sh disabled
   ```

2. **Learning Pass 1 (Training)**
   ```bash
   CLEAR_SKILLBOOK=true ./scripts/run-benchmark.sh enabled
   ```

3. **Learning Pass 2 (Evaluation)**
   ```bash
   ./scripts/run-benchmark.sh enabled
   ```

4. **Compare Results**
   - Compare `summary.json` files
   - Look for iteration/token reductions
   - Analyze per-prompt improvements

### Metrics Captured

| Metric | Target |
|--------|--------|
| Iterations | 20% reduction |
| Tokens | 15% reduction |
| Success Rate | +10% absolute |
| Rollbacks | 75% reduction |

---

## Expected Improvements

**Location:** `docs/ACE_LEARNING_ANALYSIS.md`

### Based on ACE Research

| Source | Improvement |
|--------|-------------|
| AppWorld Benchmark | +17.1% |
| FiNER Benchmark | +8.6% |
| v2.1 Prompts | +17% success rate |

### Projected RALPH Improvements

| Task Type | Expected Reduction |
|-----------|-------------------|
| Repetitive Patterns | 40-60% fewer iterations |
| Error Recovery | 30-50% fewer iterations |
| Project Conventions | 20-40% fewer iterations |

### Break-Even Analysis

- Learning overhead: ~4000 tokens/iteration
- Break-even: Tasks saving 2+ iterations benefit from learning
- Recommended: `max_skills=100` for optimal balance

---

## Decisions Made

1. **10 prompts chosen**: Balance of coverage vs run time
2. **3 categories**: Matches ACE benefit profiles from research
3. **JSON + Markdown output**: Machine-readable + human-readable
4. **Skillbook backup**: Automatic backup before clearing
5. **Timeout per prompt**: 600 seconds to prevent hangs
6. **gpt-4o-mini default for learning**: Cost-efficient for ACE operations

---

## Blockers Encountered

None - infrastructure created successfully without executing actual benchmarks.

---

## Next Step

**Run baseline benchmarks:**
```bash
./scripts/run-benchmark.sh disabled
```

After baseline:
```bash
CLEAR_SKILLBOOK=true ./scripts/run-benchmark.sh enabled
./scripts/run-benchmark.sh enabled
```

Then compare results in `docs/benchmarks/runs/`.
