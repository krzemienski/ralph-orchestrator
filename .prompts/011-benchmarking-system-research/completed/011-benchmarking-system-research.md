# Comprehensive Benchmarking System Research

## Session Initialization

Before beginning research, verify today's date:
!`date +%Y-%m-%d`

Use this date when searching for current information.

---

## Research Objective

Research and design a comprehensive benchmarking system for Ralph orchestrator that uses REAL prompts representing actual usage patterns, not synthetic test cases.

**Purpose**: Establish a TRUE baseline for context optimization experiments with validated measurement infrastructure.

**Scope**:
- Review existing examples and benchmark infrastructure
- Design cascading complexity levels
- Validate measurement capabilities
- Determine optimal execution approach
- Define what metrics actually matter

**Output**: `benchmarking-system-research.md` with structured findings

---

## Critical Context Recovery

**IMPORTANT**: Use the claude-mem MCP to recover context from prior research sessions.

### Memory Queries to Execute

Before proceeding with new research, query memory for prior work:

```
# Search for context optimization research
mcp__plugin_claude-mem_mcp-search__search(
  query="context optimization token measurement ralph orchestrator baseline",
  limit=20
)

# Search for ACE learning and skillbook analysis
mcp__plugin_claude-mem_mcp-search__search(
  query="ACE learning skillbook injection metrics compression pipeline",
  limit=15
)

# Get timeline around recent work
mcp__plugin_claude-mem_mcp-search__timeline(
  query="benchmarking validation gate experiment",
  depth_before=10,
  depth_after=10
)
```

### Key Document to Reference

Read this document that summarizes prior research from 6 parallel Opus 4.5 agents:
`@docs/plans/260110-context-optimization-design.md`

Key findings to incorporate:
- Token usage varies 66x between simple (1,360) and complex (90,000) tasks
- ~3,000 tokens repeated per iteration (tool definitions, system prompts)
- ContextTracker EXISTS but is NOT integrated
- Skillbook had 50% duplication (fixed to 0%)
- Benchmark suite has NEVER been run (runs/ directory is empty)

---

## Research Scope

### Include

1. **Examples Directory Analysis**
   - Review ALL files in `examples/` directory
   - Categorize by complexity (simple, medium, complex)
   - Identify iteration expectations per example
   - Document what makes each representative of real usage

2. **Cascading Complexity Design**
   Create 4-5 tiers of benchmark prompts:
   - **Tier 1 - Simple Scripts**: Hello World, single file creation (1-2 iterations)
   - **Tier 2 - REST API Testing**: Flask/FastAPI with CRUD, tests (5-10 iterations)
   - **Tier 3 - Web App Testing**: Full web application with UI (10-15 iterations)
   - **Tier 4 - iOS App Functional Testing**: SwiftUI app with functional tests (15-25 iterations)
   - **Tier 5 - Complex Multi-Component**: Microservices or full-stack (25+ iterations)

3. **Measurement Infrastructure Validation**
   Verify these components actually work:
   - `src/ralph_orchestrator/monitoring/context_tracker.py` - Is it integrated?
   - `src/ralph_orchestrator/metrics.py` - What does it capture?
   - `src/ralph_orchestrator/verbose_logger.py` - Token breakdown available?
   - `src/ralph_orchestrator/learning/ace_adapter.py` - Skillbook telemetry?
   - Cost tracking accuracy vs actual API billing

4. **Benchmark Execution Approach**
   Evaluate two options:
   - **Option A**: Use existing `scripts/run-benchmark.sh` (fix any issues)
   - **Option B**: Run orchestrator directly with proper PROMPT.md files

   Determine which provides:
   - More reliable measurements
   - Better reproducibility
   - Easier debugging
   - Cleaner output

5. **What We're Actually Measuring**
   Define exact metrics for each:
   - Tokens per component (system prompt, skillbook, tools, dynamic context, response)
   - Success rate (how do we define "success"?)
   - Iterations to completion
   - Total cost (input + output tokens)
   - Time per iteration and total time
   - Skill utilization (which skills were injected vs used)

### Exclude

- Implementation of the benchmarking system (that's for a Plan prompt)
- Actual benchmark runs (need infrastructure validation first)
- Changes to core orchestrator code (separate work)
- ACE framework implementation details (already researched)

---

## Verification Checklist

**Infrastructure Verification:**
- [ ] Can ContextTracker produce per-component token breakdown?
- [ ] Is ContextTracker actually called during orchestration?
- [ ] Does metrics.py capture iteration-level data?
- [ ] Can we verify cost tracking against actual API usage?
- [ ] Does run-benchmark.sh exist and what does it expect?
- [ ] Does scripts/benchmark-prompts/ directory exist?

**Examples Analysis:**
- [ ] All example files in examples/ directory documented
- [ ] Each example categorized by expected complexity
- [ ] Gap analysis: what complexity tiers are missing?

**Measurement Completeness:**
- [ ] Can measure tokens by component (not just total)?
- [ ] Can measure success rate objectively?
- [ ] Can measure iteration count reliably?
- [ ] Can measure cost per run?
- [ ] Can compare baseline vs optimized runs?

---

## Research Quality Assurance

### Completeness Check
- [ ] All verification checklist items addressed
- [ ] Both execution approaches evaluated
- [ ] All 5 complexity tiers designed with example prompts
- [ ] Measurement gaps identified with solutions

### Source Verification
- [ ] File paths verified to exist
- [ ] Code snippets extracted from actual files
- [ ] Integration points confirmed by reading source

### Blind Spots Review
- [ ] Did I check if benchmark-prompts/ directory exists?
- [ ] Did I verify ContextTracker is called from orchestrator.py?
- [ ] Did I check if run-benchmark.sh has any bugs?
- [ ] Did I consider iOS simulator requirements for Tier 4?

---

## Output Structure

Save to: `.prompts/011-benchmarking-system-research/benchmarking-system-research.md`

### Required Sections

```xml
<research>
  <summary>
    Executive summary of benchmarking system findings and recommendations
  </summary>

  <examples_analysis>
    <example file="simple-task.md">
      <complexity>simple</complexity>
      <expected_iterations>1-2</expected_iterations>
      <what_it_tests>Basic file creation, iteration completion</what_it_tests>
    </example>
    <!-- All examples documented -->
  </examples_analysis>

  <complexity_tiers>
    <tier level="1" name="Simple Scripts">
      <description>...</description>
      <example_prompts>...</example_prompts>
      <expected_iterations>1-3</expected_iterations>
      <expected_tokens>1,000-2,000</expected_tokens>
    </tier>
    <!-- All 5 tiers -->
  </complexity_tiers>

  <infrastructure_validation>
    <component name="ContextTracker">
      <file>src/ralph_orchestrator/monitoring/context_tracker.py</file>
      <integrated>true|false</integrated>
      <capabilities>What it can measure</capabilities>
      <gaps>What's missing</gaps>
    </component>
    <!-- All measurement components -->
  </infrastructure_validation>

  <execution_approach>
    <recommendation>Option A or B</recommendation>
    <rationale>Why this approach</rationale>
    <implementation_steps>How to use it</implementation_steps>
  </execution_approach>

  <metrics_definition>
    <metric name="tokens_per_component">
      <description>Breakdown of token usage by component</description>
      <how_to_measure>Which code, what calls</how_to_measure>
      <baseline_expectation>What we expect to see</baseline_expectation>
    </metric>
    <!-- All 6 key metrics -->
  </metrics_definition>

  <recommendations>
    <recommendation priority="P0">
      <action>What to do first</action>
      <rationale>Why this is critical</rationale>
    </recommendation>
    <!-- Prioritized recommendations -->
  </recommendations>

  <metadata>
    <confidence level="high|medium|low">
      Explanation of confidence level
    </confidence>
    <dependencies>
      What's needed before benchmarks can run
    </dependencies>
    <open_questions>
      What remains uncertain
    </open_questions>
    <assumptions>
      What was assumed
    </assumptions>
    <quality_report>
      <sources_consulted>List of files read</sources_consulted>
      <claims_verified>Verified findings</claims_verified>
      <claims_assumed>Assumptions made</claims_assumed>
    </quality_report>
  </metadata>
</research>
```

---

## Incremental Output

**CRITICAL: Write findings incrementally to prevent token limit failures**

1. Create output file with XML skeleton first
2. Write each section as you complete research:
   - Examples analysis → Append immediately
   - Each complexity tier → Append as designed
   - Each infrastructure component → Append as validated
3. Finalize summary and metadata after all sections complete

---

## SUMMARY.md Requirements

Create `.prompts/011-benchmarking-system-research/SUMMARY.md` with:

```markdown
# Benchmarking System Research Summary

**[SUBSTANTIVE ONE-LINER - e.g., "ContextTracker not integrated; need to wire into orchestrator.py before any benchmarks can run"]**

## Version
v1

## Key Findings
• Finding 1 with evidence
• Finding 2 with evidence
• Finding 3 with evidence

## Files Created
- benchmarking-system-research.md (full research output)
- SUMMARY.md (this file)

## Decisions Needed
- [ ] Decision 1 requiring user input
- [ ] Decision 2 requiring user input

## Blockers
- Blocker 1 (if any)
- None if no blockers

## Next Step
[Concrete action: e.g., "Create benchmarking-system-plan.md to implement ContextTracker integration"]
```

---

## Success Criteria

- [ ] All 5 complexity tiers designed with concrete example prompts
- [ ] Infrastructure validation complete (integrated vs not)
- [ ] Clear recommendation on execution approach (Option A vs B)
- [ ] All 6 key metrics defined with measurement method
- [ ] Memory MCP queries executed to incorporate prior research
- [ ] SUMMARY.md created with substantive one-liner
- [ ] Ready for planning/implementation to consume
