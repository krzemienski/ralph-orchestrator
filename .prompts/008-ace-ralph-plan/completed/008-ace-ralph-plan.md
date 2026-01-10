# ACE + RALPH Integration Plan

<objective>
Create a comprehensive implementation plan for properly integrating ACE learning capabilities into RALPH orchestrator, including benchmark design for measuring improvement.

Purpose: Guide phased implementation with clear milestones and measurable outcomes
Input: ACE documentation research + RALPH integration research
Output: ace-ralph-plan.md with implementation phases and benchmark strategy
</objective>

<context>
ACE Research: @.prompts/006-ace-docs-research/ace-docs-research.md
RALPH Research: @.prompts/007-ralph-integration-research/ralph-integration-research.md

Use findings from both research outputs to create actionable plan.
</context>

<planning_requirements>
**Implementation Requirements:**
- Fix all existing bugs in ace_adapter.py
- Properly integrate ACE following official patterns
- Maintain RALPH feature parity (non-learning mode must work)
- Support both sync and async learning modes
- Proper error handling and graceful degradation
- Environment variable propagation working

**Benchmark Requirements:**
- Design prompts that show measurable learning improvement
- Metrics: iteration count, token usage, task success rate
- Clear baseline (learning disabled) vs improved (learning enabled)
- Reproducible test methodology
- Use existing monitoring dashboard for measurement

**Constraints:**
- No pytest or unit tests - end-to-end validation only
- Must work with existing RALPH CLI interface
- Must preserve git checkpoint system
- Should not significantly impact non-learning performance
</planning_requirements>

<output_structure>
Save to: `.prompts/008-ace-ralph-plan/ace-ralph-plan.md`

```xml
<plan>
  <summary>
    {Overview of integration approach and expected outcomes}
  </summary>

  <phases>
    <phase number="1" name="fix-critical-bugs">
      <objective>Fix API key propagation and existing ACE adapter bugs</objective>
      <tasks>
        <task priority="critical">{Specific bug fix}</task>
        <task priority="critical">{Environment variable fix}</task>
      </tasks>
      <deliverables>
        <deliverable>Working ace_adapter.py with proper API key handling</deliverable>
        <deliverable>Validation: `ralph run --learning -p "simple task"` completes</deliverable>
      </deliverables>
      <dependencies>None - can start immediately</dependencies>
      <validation>Run ralph with --learning, verify no API key errors</validation>
    </phase>

    <phase number="2" name="proper-ace-integration">
      <objective>Implement ACE integration following official patterns</objective>
      <tasks>
        <task priority="high">Implement skillbook injection at {location}</task>
        <task priority="high">Implement learning trigger at {location}</task>
        <task priority="medium">Add proper reflection data mapping</task>
        <task priority="medium">Implement async learning queue</task>
      </tasks>
      <deliverables>
        <deliverable>Skillbook context injected into prompts</deliverable>
        <deliverable>Learning triggered after successful iterations</deliverable>
        <deliverable>Skills extracted and persisted</deliverable>
      </deliverables>
      <dependencies>Phase 1 complete</dependencies>
      <validation>Run task, check skillbook.json has new skills</validation>
    </phase>

    <phase number="3" name="benchmark-infrastructure">
      <objective>Create benchmark test framework and baseline measurements</objective>
      <tasks>
        <task priority="high">Design benchmark prompt set</task>
        <task priority="high">Create benchmark runner script</task>
        <task priority="medium">Integrate with monitoring dashboard</task>
        <task priority="medium">Document baseline results</task>
      </tasks>
      <deliverables>
        <deliverable>Benchmark prompt suite (5-10 prompts)</deliverable>
        <deliverable>scripts/run-benchmark.sh</deliverable>
        <deliverable>Baseline metrics documented</deliverable>
      </deliverables>
      <dependencies>Phase 2 complete</dependencies>
      <validation>Run benchmarks, capture metrics</validation>
    </phase>

    <phase number="4" name="measure-improvement">
      <objective>Run benchmarks with learning enabled, measure and document improvement</objective>
      <tasks>
        <task priority="high">Run benchmark suite without learning (baseline)</task>
        <task priority="high">Run benchmark suite with learning enabled</task>
        <task priority="high">Compare and document metrics</task>
        <task priority="medium">Iterate on prompts if no improvement</task>
      </tasks>
      <deliverables>
        <deliverable>Baseline results document</deliverable>
        <deliverable>Learning-enabled results document</deliverable>
        <deliverable>Improvement analysis report</deliverable>
      </deliverables>
      <dependencies>Phase 3 complete</dependencies>
      <validation>Demonstrable improvement in at least one metric</validation>
    </phase>

    <phase number="5" name="documentation-iteration">
      <objective>Document what causes improvements, iterate until significant gains</objective>
      <tasks>
        <task priority="high">Analyze skillbook contents after learning</task>
        <task priority="high">Document which skills improve performance</task>
        <task priority="medium">Tune reflection prompts if needed</task>
        <task priority="medium">Iterate benchmark runs</task>
      </tasks>
      <deliverables>
        <deliverable>docs/ACE_LEARNING_ANALYSIS.md</deliverable>
        <deliverable>Optimized skillbook with proven improvements</deliverable>
        <deliverable>Final benchmark report</deliverable>
      </deliverables>
      <dependencies>Phase 4 shows some improvement</dependencies>
      <validation>Clear documentation of what learning achieves</validation>
    </phase>
  </phases>

  <benchmark_design>
    <prompt_categories>
      <category name="repetitive-tasks">
        <description>Tasks that repeat patterns (should improve with memory)</description>
        <example_prompts>
          - "Create 5 Python functions that each validate different input types"
          - "Add logging to 3 different modules following the same pattern"
        </example_prompts>
        <expected_improvement>Faster after learning the pattern</expected_improvement>
      </category>

      <category name="error-recovery">
        <description>Tasks that commonly fail first time (should learn from failures)</description>
        <example_prompts>
          - "Fix all type errors in the project" (learns common patterns)
          - "Update deprecated API calls" (learns migration patterns)
        </example_prompts>
        <expected_improvement>Fewer iterations after learning pitfalls</expected_improvement>
      </category>

      <category name="project-specific">
        <description>Tasks specific to RALPH codebase (should learn conventions)</description>
        <example_prompts>
          - "Add a new adapter following existing patterns"
          - "Add a new CLI flag with validation"
        </example_prompts>
        <expected_improvement>Better adherence to project patterns</expected_improvement>
      </category>
    </prompt_categories>

    <metrics_to_capture>
      <metric name="iteration_count">
        <description>How many iterations to complete task</description>
        <capture_method>Monitor dashboard / metrics</capture_method>
        <improvement_target>20% fewer iterations</improvement_target>
      </metric>

      <metric name="token_usage">
        <description>Total tokens consumed</description>
        <capture_method>Cost tracker</capture_method>
        <improvement_target>15% reduction</improvement_target>
      </metric>

      <metric name="time_to_completion">
        <description>Wall clock time</description>
        <capture_method>Timestamp logging</capture_method>
        <improvement_target>10% faster</improvement_target>
      </metric>

      <metric name="success_rate">
        <description>Task completion without manual intervention</description>
        <capture_method>Exit status / completion markers</capture_method>
        <improvement_target>Higher first-try success</improvement_target>
      </metric>
    </metrics_to_capture>

    <methodology>
      <step order="1">Clear skillbook, run benchmark without learning (baseline)</step>
      <step order="2">Enable learning, run same benchmark suite</step>
      <step order="3">Run benchmark again with trained skillbook (measure retention)</step>
      <step order="4">Compare metrics across all runs</step>
      <step order="5">Document findings and iterate if needed</step>
    </methodology>
  </benchmark_design>

  <metadata>
    <confidence level="{high|medium|low}">
      {Confidence this plan will achieve demonstrable improvement}
    </confidence>
    <dependencies>
      - ANTHROPIC_API_KEY available
      - ACE research findings validated
      - RALPH research findings validated
      - Monitoring dashboard functional
    </dependencies>
    <open_questions>
      - What task types benefit most from learning?
      - How much training data (iterations) needed for improvement?
      - What's the optimal skillbook size before diminishing returns?
    </open_questions>
    <assumptions>
      - ACE framework works as documented
      - RALPH metrics provide sufficient data for reflection
      - Learning improvements are measurable
    </assumptions>
  </metadata>
</plan>
```
</output_structure>

<summary_requirements>
Create `.prompts/008-ace-ralph-plan/SUMMARY.md`

Must include:
- **One-liner**: Phase count and key deliverable
- **Phase Overview**: Each phase with objective (1 line each)
- **Benchmark Strategy**: Prompt types and metrics
- **Decisions Needed**: Any choices requiring user input
- **Blockers**: Technical/resource impediments
- **Next Step**: "Execute Phase 1: Fix critical bugs"
</summary_requirements>

<success_criteria>
- All 5 phases defined with clear objectives and deliverables
- Benchmark design includes prompt categories, metrics, methodology
- Each phase has validation criteria
- Dependencies clearly mapped
- Ready for implementation prompts to execute
- SUMMARY.md created with actionable roadmap
</success_criteria>
