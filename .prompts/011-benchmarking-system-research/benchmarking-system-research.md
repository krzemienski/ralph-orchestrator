# Ralph Orchestrator Benchmarking System Research

<metadata>
<type>research</type>
<topic>benchmarking-system</topic>
<version>v1</version>
<generated_at>2026-01-10T16:55:00-05:00</generated_at>
<prior_research>
- docs/plans/260110-context-optimization-design.md (6 Opus 4.5 agents)
- Memory observations #12659-#12704 (ACE integration analysis)
</prior_research>
</metadata>

---

## Executive Summary

This research establishes a comprehensive benchmarking system for Ralph orchestrator using REAL prompts from the `examples/` directory and a 5-tier cascading complexity design. The critical finding is that **ContextTracker EXISTS but is NOT integrated** into the orchestrator, meaning we cannot currently measure per-component token usage without manual integration work.

<confidence level="high">
The examples directory analysis, measurement infrastructure validation, and benchmark design are all based on direct code review. The execution approach recommendation is high-confidence based on infrastructure analysis.
</confidence>

---

## Section 1: Examples Directory Analysis

### 1.1 Complete Inventory

| File | Lines | Complexity | Category | Real-World Applicability |
|------|-------|------------|----------|--------------------------|
| `simple-task.md` | 13 | Trivial | Script | Low - Hello World test |
| `simple_function.md` | 17 | Simple | Script | Medium - Function creation |
| `cli_tool.md` | 45 | Medium | CLI Tool | High - Real CLI patterns |
| `web_scraper.md` | 58 | Medium-High | Web/HTTP | High - HTTP/parsing |
| `web-api.md` | 67 | High | Web API | Very High - Full API project |

### 1.2 Example Details

#### simple-task.md (Tier 0 - Trivial)
```markdown
Create a simple Python script that prints "Hello, World!"
to the console.
```
- **Purpose**: Basic sanity check
- **Expected tokens**: ~1,000-1,500
- **Expected iterations**: 1
- **Measurement value**: Baseline for minimum viable execution

#### simple_function.md (Tier 1 - Simple)
```markdown
Create a Python function called `fibonacci` that:
1. Takes a single integer argument `n`
2. Returns the nth Fibonacci number
3. Handles edge cases (negative numbers, 0, 1)
4. Include a docstring with examples
```
- **Purpose**: Single-file code generation
- **Expected tokens**: ~2,000-3,000
- **Expected iterations**: 1-2
- **Measurement value**: Baseline for simple code tasks

#### cli_tool.md (Tier 2 - Multi-Component)
```markdown
Create a command-line tool that:
1. Accepts a directory path as an argument
2. Recursively scans for duplicate files using MD5 hashing
3. Groups duplicates together
4. Outputs results in JSON format
5. Handles errors gracefully (permissions, symlinks)
6. Include --dry-run and --verbose flags
```
- **Purpose**: CLI tool with multiple concerns
- **Expected tokens**: ~5,000-10,000
- **Expected iterations**: 2-4
- **Measurement value**: Multi-file coordination

#### web_scraper.md (Tier 3 - Integration)
```markdown
Create a web scraper that:
1. Accepts a URL and CSS selector
2. Fetches page content with proper headers
3. Parses HTML and extracts matching elements
4. Handles pagination if present
5. Implements rate limiting and retry logic
6. Outputs structured JSON
7. Include error handling for network issues
```
- **Purpose**: HTTP client with parsing
- **Expected tokens**: ~10,000-25,000
- **Expected iterations**: 3-5
- **Measurement value**: External dependency integration

#### web-api.md (Tier 4 - Full Stack)
```markdown
Create a REST API for a todo list application:
1. FastAPI-based server
2. SQLite database with SQLAlchemy ORM
3. CRUD endpoints for todos
4. User authentication with JWT
5. Input validation with Pydantic
6. API documentation (auto-generated)
7. Docker configuration
8. Basic test suite with pytest
```
- **Purpose**: Full-stack application
- **Expected tokens**: ~50,000-90,000
- **Expected iterations**: 5-15
- **Measurement value**: Complex multi-component orchestration

### 1.3 Gap Analysis

**Missing Complexity Tiers:**
1. **iOS/Mobile** - No examples for Xcode/Swift workflows
2. **Multi-Language** - All examples are Python-only
3. **Refactoring** - No "modify existing code" examples
4. **Debugging** - No "fix this bug" examples
5. **Testing-focused** - No "add tests to existing code" examples

**Recommendation**: Create additional benchmark prompts for missing tiers, but current examples provide 80% coverage for baseline establishment.

---

## Section 2: Measurement Infrastructure Validation

### 2.1 Component Status

| Component | File | Status | Integration |
|-----------|------|--------|-------------|
| ContextTracker | `monitoring/context_tracker.py` | EXISTS | **NOT INTEGRATED** |
| Metrics | `metrics.py` | EXISTS | INTEGRATED |
| VerboseLogger | `verbose_logger.py` | EXISTS | INTEGRATED |
| ACE Adapter | `learning/ace_adapter.py` | EXISTS | INTEGRATED |
| CostTracker | `metrics.py` | EXISTS | INTEGRATED |

### 2.2 Critical Finding: ContextTracker NOT Integrated

**Evidence from grep search:**
```
Found 2 files matching "ContextTracker":
- src/ralph_orchestrator/monitoring/context_tracker.py
- src/ralph_orchestrator/monitoring/__init__.py

NOT FOUND in:
- orchestrator.py (main loop)
- Any adapter files
```

**Impact**: Cannot currently measure per-component token usage without code changes.

### 2.3 ContextTracker Capabilities (When Integrated)

The ContextTracker provides exactly what we need for benchmarking:

```python
class MeasurePoint(Enum):
    ITERATION_START = "iteration_start"
    AFTER_PROMPT_INJECT = "after_prompt_inject"
    AFTER_SKILLBOOK_INJECT = "after_skillbook_inject"
    AFTER_TOOL_CALL = "after_tool_call"
    AFTER_RESPONSE = "after_response"
    ITERATION_END = "iteration_end"
```

**Features:**
- Token counting via tiktoken (4-char fallback)
- Per-iteration tracking with delta calculation
- Component attribution (prompt, skillbook, tools, response)
- ASCII visualization (`get_timeline_ascii()`)
- JSON export (`save_timeline()`)
- Context limit awareness by adapter type

### 2.4 Current Measurement Capabilities (Without ContextTracker)

**Available via metrics.py:**
- `input_tokens` - Total input per iteration
- `output_tokens` - Total output per iteration
- `cost` - Estimated cost per iteration
- `iteration_count` - Number of iterations
- `trigger_reason` - Why iteration triggered

**Available via verbose_logger.py:**
- Session-level aggregates
- Tool call counts
- Error counts
- Duration tracking

**NOT Currently Available:**
- Per-component token breakdown
- Skillbook injection cost
- Tool definition overhead
- Dynamic context growth

### 2.5 Integration Requirement for Full Benchmarking

To enable per-component measurement, ContextTracker must be integrated into `orchestrator.py`:

```python
# Required integration points in orchestrator.py:

# 1. Import
from ralph_orchestrator.monitoring.context_tracker import ContextTracker, MeasurePoint

# 2. Initialize in RalphOrchestrator.__init__
self.context_tracker = ContextTracker(adapter_type=self.adapter.name)

# 3. Measure in _aexecute_iteration at key points:
# - After prompt enhancement
# - After skillbook injection
# - After each tool call
# - After response received
```

**Estimated Integration Effort**: 2-4 hours

---

## Section 3: Cascading Complexity Benchmark Design

### 3.1 Five-Tier System

```
Tier 0: Sanity     [simple-task.md]        ~1,000 tokens, 1 iteration
Tier 1: Simple     [simple_function.md]    ~2,500 tokens, 1-2 iterations
Tier 2: Medium     [cli_tool.md]           ~7,500 tokens, 2-4 iterations
Tier 3: Complex    [web_scraper.md]        ~17,500 tokens, 3-5 iterations
Tier 4: Full Stack [web-api.md]            ~70,000 tokens, 5-15 iterations
```

### 3.2 Tier Definitions and Prompts

#### Tier 0: Sanity Check (Validates Infrastructure)
**Prompt Source**: `examples/simple-task.md`
**Purpose**: Confirm orchestrator runs, metrics captured, output created
**Pass Criteria**:
- Completes in < 2 iterations
- Creates `hello.py`
- Metrics JSON has valid structure
- Cost > $0.00

**Success signals infrastructure works**

#### Tier 1: Simple Code Generation
**Prompt Source**: `examples/simple_function.md`
**Purpose**: Single-file code with logic
**Measurements**:
- Token count per component
- Iteration count (expect 1-2)
- Time to completion
- Code quality (function runs correctly)

**Baseline for "simple task" category**

#### Tier 2: Multi-Component CLI Tool
**Prompt Source**: `examples/cli_tool.md`
**Purpose**: Multiple files, error handling, CLI parsing
**Measurements**:
- Token growth across iterations
- Tool call frequency
- File creation count
- Iteration count (expect 2-4)

**Tests multi-file coordination**

#### Tier 3: Integration with External Dependencies
**Prompt Source**: `examples/web_scraper.md`
**Purpose**: HTTP, parsing, error handling, rate limiting
**Measurements**:
- All Tier 2 metrics
- External package imports
- Retry/recovery patterns
- Iteration count (expect 3-5)

**Tests real-world integration patterns**

#### Tier 4: Full-Stack Application
**Prompt Source**: `examples/web-api.md`
**Purpose**: Database, API, auth, tests, Docker
**Measurements**:
- All previous tier metrics
- Component breakdown (API, DB, Auth, Tests)
- Total context window utilization
- Peak vs average usage
- Iteration count (expect 5-15)

**Tests complex orchestration at scale**

### 3.3 Benchmark Execution Order

```
1. Run Tier 0 first
   - If fails: Stop, fix infrastructure
   - If passes: Continue

2. Run Tiers 1-4 sequentially
   - Record all metrics per tier
   - Compare actual vs expected
   - Identify anomalies

3. Repeat 3x for statistical significance
   - Calculate mean, std dev
   - Identify variance sources
```

---

## Section 4: Execution Approach Analysis

### 4.1 Option A: run-benchmark.sh

**Location**: `scripts/run-benchmark.sh`

**Analysis of Script**:
```bash
# Key features observed:
- Uses benchmark-prompts/ directory (different from examples/)
- Creates runs/benchmark-YYYYMMDD-HHMMSS/ output
- Captures JSON metrics
- Supports --dry-run flag
```

**Pros**:
- Already exists
- Standardized output structure
- Timestamped runs

**Cons**:
- Uses different prompts than examples/ (benchmark-prompts/)
- Not integrated with ContextTracker
- Limited metric capture (no per-component)
- Has NEVER been successfully run (runs/ directory empty per prior research)

### 4.2 Option B: Direct Orchestrator with Real Prompts

**Approach**: Run `ralph run` directly with examples/ prompts

**Pros**:
- Uses REAL example prompts
- Can integrate ContextTracker
- Full control over measurement
- Matches actual user workflow

**Cons**:
- Need to manually capture metrics
- No standardized output structure
- Need to create benchmark harness

### 4.3 Recommendation: Hybrid Approach

**Execute in phases:**

**Phase 1: Quick Baseline (No ContextTracker)**
```bash
# Run each tier, capture existing metrics
for tier in simple-task simple_function cli_tool web_scraper web-api; do
  ralph run -p examples/${tier}.md -o runs/${tier}-baseline/
done
```
- Uses existing infrastructure
- Gets iteration counts, total tokens, costs, success rates
- 1-2 hours to execute

**Phase 2: Integrate ContextTracker (2-4 hours development)**
- Add ContextTracker to orchestrator.py
- Hook into all measurement points
- Re-run benchmarks with per-component data

**Phase 3: Full Benchmark Suite**
- Create standardized benchmark runner
- 3x repetition per tier
- Statistical analysis
- Export comparison data

---

## Section 5: Metrics Definition

### 5.1 Primary Metrics (Required)

| Metric | Source | Calculation | Unit |
|--------|--------|-------------|------|
| Total Tokens | metrics.py | input_tokens + output_tokens | tokens |
| Iterations | metrics.py | iteration_count | count |
| Cost | metrics.py | sum(cost) | USD |
| Duration | verbose_logger | end - start | seconds |
| Success Rate | metrics.py | success / total | percentage |

### 5.2 Component Metrics (Requires ContextTracker)

| Metric | Source | Measurement Point | Unit |
|--------|--------|-------------------|------|
| System Prompt Tokens | context_tracker | ITERATION_START | tokens |
| Skillbook Tokens | context_tracker | AFTER_SKILLBOOK_INJECT - AFTER_PROMPT_INJECT | tokens |
| Tool Definition Tokens | context_tracker | Calculated from tool count | tokens |
| Dynamic Context Tokens | context_tracker | AFTER_TOOL_CALL deltas | tokens |
| Response Tokens | context_tracker | AFTER_RESPONSE - previous | tokens |

### 5.3 Derived Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| Tokens per Iteration | total_tokens / iterations | Efficiency |
| Cost per Iteration | total_cost / iterations | Economic |
| Context Efficiency | useful_tokens / total_tokens | Waste detection |
| Overhead Ratio | (system + tools) / total | Fixed cost |
| Growth Rate | (iter_n - iter_1) / n | Accumulation |

### 5.4 ACE Learning Metrics (From ace_adapter.py)

| Metric | Source | Purpose |
|--------|--------|---------|
| Skills Added | ace_adapter._stats | Learning effectiveness |
| Reflections Count | ace_adapter._stats | Learning activity |
| Learning Time | ace_adapter._stats | Overhead cost |
| Inject Count | ace_adapter._stats | Skillbook usage |

---

## Section 6: Verification Checklist

### 6.1 Pre-Benchmark Verification

- [x] Examples directory exists with 5 prompts
- [x] metrics.py captures iteration-level data
- [x] verbose_logger.py provides session aggregates
- [ ] **ContextTracker integrated into orchestrator** (BLOCKED)
- [x] ACE adapter has telemetry hooks
- [x] Output directories writable

### 6.2 Infrastructure Gaps

| Gap | Severity | Mitigation |
|-----|----------|------------|
| ContextTracker not integrated | HIGH | Integrate before Phase 2 |
| run-benchmark.sh untested | MEDIUM | Use direct orchestrator |
| No iOS/mobile examples | LOW | Create for future tiers |
| Single repetition | MEDIUM | Run 3x for statistics |

### 6.3 Data Quality Verification

After each benchmark run, verify:
1. Metrics JSON parseable
2. Token counts > 0
3. Iterations > 0
4. Cost > $0.00
5. Duration reasonable for tier

---

## Section 7: Recommended Benchmark Protocol

### 7.1 Immediate Actions (Phase 1)

```bash
# 1. Create benchmark output directory
mkdir -p runs/baseline-$(date +%Y%m%d)

# 2. Run Tier 0 sanity check
ralph run -p examples/simple-task.md \
  --output runs/baseline-$(date +%Y%m%d)/tier0-sanity/ \
  --max-iterations 3

# 3. Verify output
ls -la runs/baseline-$(date +%Y%m%d)/tier0-sanity/
cat runs/baseline-$(date +%Y%m%d)/tier0-sanity/metrics.json

# 4. If Tier 0 passes, continue with Tiers 1-4
```

### 7.2 Integration Phase (Phase 2)

1. Add ContextTracker import to `orchestrator.py`
2. Initialize tracker in `__init__`
3. Add measurement calls at:
   - `_aexecute_iteration` start
   - After `_enhance_prompt_with_instructions`
   - After each tool execution
   - After response received
4. Save timeline at run completion
5. Re-run Tier 0-4 with component data

### 7.3 Full Baseline Establishment (Phase 3)

Run each tier 3 times:
```bash
for run in 1 2 3; do
  for tier in 0 1 2 3 4; do
    ralph run -p examples/tier${tier}.md \
      --output runs/baseline/run${run}/tier${tier}/
  done
done
```

Aggregate results into baseline report.

---

## Conclusions

<findings>

### Key Finding 1: ContextTracker Exists But Is Not Integrated
The measurement infrastructure for per-component token tracking EXISTS in `monitoring/context_tracker.py` but is NOT wired into the main orchestrator. This is the primary blocker for detailed benchmarking.

### Key Finding 2: Examples Provide Good Tier Coverage
The 5 examples in `examples/` map well to a 5-tier complexity model (Tiers 0-4), covering trivial to full-stack scenarios. Gap: No iOS/mobile examples.

### Key Finding 3: Existing Metrics Sufficient for Baseline
Without ContextTracker integration, we can still capture:
- Total tokens per iteration
- Iteration count
- Cost
- Duration
- Success/failure

This is sufficient for Phase 1 baseline establishment.

### Key Finding 4: run-benchmark.sh Is Risky
The existing benchmark script has never been successfully run and uses different prompts than the real examples. Recommend direct orchestrator execution with examples/ prompts instead.

### Key Finding 5: ACE Adapter Has Comprehensive Telemetry
The ace_adapter.py already tracks learning metrics that can supplement benchmark data: skills added, reflections, learning time, inject count.

</findings>

<dependencies>
- ContextTracker integration for per-component metrics (2-4 hours)
- Clean test environment for reproducible runs
- Sufficient API credits for 15+ benchmark runs (5 tiers x 3 repetitions)
</dependencies>

<open_questions>
1. Should we add iOS/mobile benchmark prompts for Tier 5+?
2. What is the acceptable variance threshold for benchmark results?
3. Should benchmarks run with ACE learning enabled or disabled?
4. How to handle network-dependent benchmarks (web_scraper, web-api)?
</open_questions>

<assumptions>
1. Claude adapter is the primary target for benchmarking
2. API costs are acceptable for multiple benchmark runs
3. Local execution (no CI/CD integration required)
4. Reproducibility more important than speed
</assumptions>

---

## Appendix A: File References

| File | Purpose | Lines |
|------|---------|-------|
| `/Users/nick/Desktop/ralph-orchestrator/examples/simple-task.md` | Tier 0 prompt | 13 |
| `/Users/nick/Desktop/ralph-orchestrator/examples/simple_function.md` | Tier 1 prompt | 17 |
| `/Users/nick/Desktop/ralph-orchestrator/examples/cli_tool.md` | Tier 2 prompt | 45 |
| `/Users/nick/Desktop/ralph-orchestrator/examples/web_scraper.md` | Tier 3 prompt | 58 |
| `/Users/nick/Desktop/ralph-orchestrator/examples/web-api.md` | Tier 4 prompt | 67 |
| `/Users/nick/Desktop/ralph-orchestrator/src/ralph_orchestrator/monitoring/context_tracker.py` | Token tracking | 329 |
| `/Users/nick/Desktop/ralph-orchestrator/src/ralph_orchestrator/metrics.py` | Metrics capture | ~200 |
| `/Users/nick/Desktop/ralph-orchestrator/src/ralph_orchestrator/verbose_logger.py` | Session logging | ~400 |
| `/Users/nick/Desktop/ralph-orchestrator/src/ralph_orchestrator/learning/ace_adapter.py` | ACE learning | ~1100 |
| `/Users/nick/Desktop/ralph-orchestrator/src/ralph_orchestrator/orchestrator.py` | Main loop | ~800 |

## Appendix B: Expected Token Ranges by Tier

Based on prior research finding of 66x variation (1,360 to 90,000 tokens):

| Tier | Min Tokens | Max Tokens | Expected Mean | Iterations |
|------|------------|------------|---------------|------------|
| 0 | 1,000 | 2,000 | 1,360 | 1 |
| 1 | 2,000 | 4,000 | 2,500 | 1-2 |
| 2 | 5,000 | 12,000 | 7,500 | 2-4 |
| 3 | 10,000 | 30,000 | 17,500 | 3-5 |
| 4 | 40,000 | 100,000 | 70,000 | 5-15 |

## Appendix C: ContextTracker Integration Code

```python
# File: src/ralph_orchestrator/orchestrator.py
# Add these changes for Phase 2 integration:

# At top of file, add import:
from ralph_orchestrator.monitoring.context_tracker import ContextTracker, MeasurePoint

# In RalphOrchestrator.__init__(), add:
self.context_tracker = ContextTracker(
    adapter_type=self.adapter.name if self.adapter else "claude",
    output_dir=self.output_dir / "metrics"
)

# In _aexecute_iteration(), add measurements:
async def _aexecute_iteration(self, iteration: int, ...):
    # After prompt enhancement
    enhanced_prompt = self._enhance_prompt_with_instructions(prompt)
    self.context_tracker.measure(
        MeasurePoint.AFTER_PROMPT_INJECT,
        enhanced_prompt,
        "prompt_with_instructions",
        iteration=iteration
    )

    # After skillbook injection (if ACE enabled)
    if self.ace_learning:
        prompt_with_skills = self.ace_learning.inject_context(enhanced_prompt, ...)
        self.context_tracker.measure(
            MeasurePoint.AFTER_SKILLBOOK_INJECT,
            prompt_with_skills,
            "skillbook_injection",
            iteration=iteration
        )

    # After response
    self.context_tracker.measure(
        MeasurePoint.AFTER_RESPONSE,
        full_context_with_response,
        "agent_response",
        iteration=iteration
    )

# In run completion, add:
timeline_path = self.context_tracker.save_timeline()
```
