# ACE + RALPH Integration Plan

<plan>
<summary>
## Executive Summary

This plan provides a 5-phase implementation roadmap for properly integrating ACE learning capabilities into the RALPH orchestrator, culminating in measurable benchmark proof that learning improves agent performance.

**Current State**: RALPH has a functional ACE integration (`ace_adapter.py`) with API key handling resolved, but several critical features are incomplete or missing:
- `async_learning` config exists but no background worker is implemented
- Limited execution trace data passed to Reflector
- No learning from checkpoint rollbacks (strong negative signals lost)
- No skillbook persistence on graceful shutdown
- No benchmark infrastructure to measure improvement

**Target State**: Full ACE integration with proven, measurable improvement on benchmark tasks, documented and ready for production use.

**Expected Outcomes**:
- 15-25% reduction in iteration count for repetitive tasks
- Demonstrable learning persistence across sessions
- Comprehensive benchmark suite with reproducible results
- Documentation of what learning achieves and when to use it
</summary>

<phases>
<phase number="1" name="fix-critical-bugs">
  <objective>Fix remaining bugs and implement missing critical features in ace_adapter.py</objective>

  <rationale>
  The research identified that while API key handling is fixed, several gaps prevent effective learning:
  - async_learning flag is ignored (learning blocks iteration)
  - Skillbook not saved on shutdown (data loss risk)
  - Checkpoint rollbacks don't trigger negative learning
  These must be fixed before benchmarking can produce meaningful results.
  </rationale>

  <tasks>
    <task priority="critical" id="1.1">
      <name>Implement async learning worker</name>
      <description>
        Create asyncio.Queue-based background worker for learning operations.
        Currently learn_from_execution() blocks the main loop. When config.async_learning=True,
        learning tasks should be queued and processed in background.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Add asyncio.Queue for learning tasks
        - Create background asyncio.Task worker
        - Add graceful shutdown with queue drain
        - Track queue depth in telemetry
        - Fallback to sync if queue full (configurable threshold)
      </implementation_notes>
    </task>

    <task priority="critical" id="1.2">
      <name>Add skillbook save on orchestrator shutdown</name>
      <description>
        Ensure skillbook is persisted when orchestrator exits (graceful or SIGINT).
        Currently skills learned in a session may be lost if not explicitly saved.
      </description>
      <location>
        src/ralph_orchestrator/orchestrator.py (shutdown handler)
        src/ralph_orchestrator/learning/ace_adapter.py (shutdown method)
      </location>
      <implementation_notes>
        - Add shutdown() method to ACELearningAdapter
        - Call from orchestrator's cleanup path
        - Wait for async queue drain before save
        - Register atexit handler as backup
      </implementation_notes>
    </task>

    <task priority="high" id="1.3">
      <name>Add learning from checkpoint rollbacks</name>
      <description>
        When RALPH rolls back to a checkpoint after failure, this is a strong negative signal.
        Currently this signal is lost. The rollback should trigger learn_from_execution() with
        success=False and context about what was rolled back.
      </description>
      <location>src/ralph_orchestrator/orchestrator.py (rollback flow)</location>
      <implementation_notes>
        - Hook into checkpoint rollback flow
        - Capture diff of rolled-back changes
        - Call learn_from_execution(success=False, error=rollback_reason, execution_trace=diff)
        - Mark as high-value negative example for Reflector
      </implementation_notes>
    </task>

    <task priority="medium" id="1.4">
      <name>Enrich execution trace data</name>
      <description>
        Pass richer execution context to Reflector for better learning.
        Currently only "iteration={N}, adapter={name}" is passed.
      </description>
      <location>src/ralph_orchestrator/orchestrator.py:828-861</location>
      <implementation_notes>
        - Include tool calls from VerboseLogger if available
        - Include ACP session data (thoughts, tool_calls) when using ACP adapter
        - Include iteration metrics (tokens, cost, time)
        - Cap trace length to prevent token bloat
      </implementation_notes>
    </task>

    <task priority="low" id="1.5">
      <name>Add optional skillbook seed file</name>
      <description>
        Allow seeding initial skillbook from a template file for cold start scenarios.
        New projects start with no learned skills, reducing effectiveness of first runs.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Add skillbook_seed_path to LearningConfig
        - Copy seed to skillbook_path if skillbook doesn't exist
        - Log warning that seed was used
        - Provide default seed with common patterns (optional)
      </implementation_notes>
    </task>
  </tasks>

  <deliverables>
    <deliverable>Updated ace_adapter.py with async learning worker</deliverable>
    <deliverable>Skillbook persistence on shutdown</deliverable>
    <deliverable>Checkpoint rollback learning integration</deliverable>
    <deliverable>Richer execution traces for Reflector</deliverable>
  </deliverables>

  <dependencies>None - can start immediately</dependencies>

  <validation>
    <criterion>Run `ralph run --learning -p "simple task"` - completes without blocking</criterion>
    <criterion>SIGINT during run preserves skillbook</criterion>
    <criterion>Force a rollback, verify negative learning event logged</criterion>
    <criterion>Check execution_trace in telemetry includes tool calls</criterion>
  </validation>

  <estimated_effort>4-6 hours</estimated_effort>
</phase>

<phase number="2" name="proper-ace-integration">
  <objective>Ensure ACE integration follows official patterns with proper v2.1 prompts</objective>

  <rationale>
  The research documented ACE's three-agent architecture (Agent, Reflector, SkillManager)
  and the INJECT->EXECUTE->LEARN cycle. Current implementation follows this pattern
  but may not be using optimal configurations or v2.1 prompt improvements (+17% success rate).
  This phase validates and optimizes the integration.
  </rationale>

  <tasks>
    <task priority="high" id="2.1">
      <name>Verify v2.1 prompts are active</name>
      <description>
        ACE v2.1 prompts show +17% success rate over v1.0. Verify RALPH is using them.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py:281-294</location>
      <implementation_notes>
        - Confirm PromptManager().get_reflector_prompt() returns v2.1
        - Confirm PromptManager().get_skill_manager_prompt() returns v2.1
        - Add logging of prompt version on init
        - Add config option to force specific version if needed
      </implementation_notes>
    </task>

    <task priority="high" id="2.2">
      <name>Add skill deduplication configuration</name>
      <description>
        Enable embedding-based skill deduplication to prevent redundant skills.
        ACE supports this via DeduplicationConfig but it's not currently configured.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Add deduplication config to LearningConfig
        - Enable with similarity_threshold=0.85 (default)
        - Use text-embedding-3-small for cost efficiency
        - Log when duplicates are merged
      </implementation_notes>
    </task>

    <task priority="medium" id="2.3">
      <name>Configure efficient ACE models</name>
      <description>
        Use cheaper/faster models for Reflector and SkillManager operations.
        These are internal operations that don't need the main agent's model.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Default to gpt-4o-mini for ACE operations (vs claude-sonnet-4-5-20250929)
        - Add separate config for ace_model vs learning_model if needed
        - Document cost savings in logging
        - Allow override via config
      </implementation_notes>
    </task>

    <task priority="medium" id="2.4">
      <name>Add Meso-level learning configuration</name>
      <description>
        Configure ACE to learn at iteration level (Meso), not tool-call level (Micro).
        This matches RALPH's iteration-based execution model.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Set insight_level="meso" in Reflector config
        - Document why iteration-level learning is preferred for RALPH
        - Consider adding config option for micro-level learning (experimental)
      </implementation_notes>
    </task>

    <task priority="low" id="2.5">
      <name>Add skill effectiveness pruning</name>
      <description>
        Periodically remove skills with negative effectiveness scores.
        Prevents context bloat from accumulated harmful skills.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Add prune_threshold to LearningConfig (default -0.3)
        - Prune skills where (helpful-harmful)/(helpful+harmful+neutral) < threshold
        - Require minimum harmful count (e.g., 3) before pruning
        - Log pruned skills for analysis
      </implementation_notes>
    </task>
  </tasks>

  <deliverables>
    <deliverable>Verified v2.1 prompts active with logging</deliverable>
    <deliverable>Skill deduplication enabled</deliverable>
    <deliverable>Efficient model configuration documented</deliverable>
    <deliverable>Effectiveness-based skill pruning</deliverable>
  </deliverables>

  <dependencies>Phase 1 complete</dependencies>

  <validation>
    <criterion>Logs show "v2.1" or equivalent prompt version</criterion>
    <criterion>Duplicate skills are merged (check skillbook.json)</criterion>
    <criterion>ACE operations use configured model (check API logs)</criterion>
    <criterion>Skills with negative effectiveness are pruned</criterion>
  </validation>

  <estimated_effort>3-4 hours</estimated_effort>
</phase>

<phase number="3" name="benchmark-infrastructure">
  <objective>Create benchmark test framework and establish baseline measurements</objective>

  <rationale>
  To prove ACE learning improves performance, we need:
  1. Reproducible benchmark prompts that exercise learning scenarios
  2. Automated benchmark runner that captures metrics
  3. Baseline measurements with learning disabled
  4. Clear methodology for comparison
  </rationale>

  <tasks>
    <task priority="critical" id="3.1">
      <name>Design benchmark prompt suite</name>
      <description>
        Create 8-12 benchmark prompts across three categories designed to show learning improvement.
      </description>
      <location>.benchmarks/prompts/</location>
      <implementation_notes>
        See benchmark_design section below for full prompt specifications.
        Prompts should be:
        - Deterministic (same starting conditions)
        - Measurable (clear success criteria)
        - Representative of real RALPH usage
        - Varied in complexity and type
      </implementation_notes>
    </task>

    <task priority="critical" id="3.2">
      <name>Create benchmark runner script</name>
      <description>
        Script to run benchmark suite with consistent configuration and metric capture.
      </description>
      <location>scripts/run-benchmark.sh or scripts/benchmark.py</location>
      <implementation_notes>
        - Accept mode: baseline (no learning) vs learning (enabled)
        - Run all prompts in sequence
        - Capture metrics per-prompt and aggregate
        - Output JSON results for analysis
        - Support git reset between runs for clean state
        - Integrate with monitoring dashboard if available
      </implementation_notes>
    </task>

    <task priority="high" id="3.3">
      <name>Create benchmark analysis script</name>
      <description>
        Script to compare baseline vs learning results and generate report.
      </description>
      <location>scripts/analyze-benchmark.py</location>
      <implementation_notes>
        - Load baseline and learning result JSONs
        - Calculate per-prompt and aggregate deltas
        - Generate markdown report with tables
        - Highlight significant improvements
        - Flag regressions if any
      </implementation_notes>
    </task>

    <task priority="medium" id="3.4">
      <name>Document baseline results</name>
      <description>
        Run full benchmark suite without learning, document baseline metrics.
      </description>
      <location>.benchmarks/results/baseline-{date}.json</location>
      <implementation_notes>
        - Run 2-3 times for consistency
        - Document environment (model, version, etc.)
        - Calculate mean and standard deviation
        - Identify prompts with high variance
      </implementation_notes>
    </task>
  </tasks>

  <deliverables>
    <deliverable>Benchmark prompt suite (8-12 prompts in 3 categories)</deliverable>
    <deliverable>scripts/run-benchmark.sh</deliverable>
    <deliverable>scripts/analyze-benchmark.py</deliverable>
    <deliverable>Baseline results JSON with 2-3 runs</deliverable>
    <deliverable>.benchmarks/README.md documenting methodology</deliverable>
  </deliverables>

  <dependencies>Phase 2 complete</dependencies>

  <validation>
    <criterion>Benchmark runner executes all prompts</criterion>
    <criterion>Metrics captured: iteration_count, token_usage, time, success</criterion>
    <criterion>Baseline results documented with variance analysis</criterion>
    <criterion>Analysis script produces readable comparison report</criterion>
  </validation>

  <estimated_effort>5-7 hours</estimated_effort>
</phase>

<phase number="4" name="measure-improvement">
  <objective>Run benchmarks with learning enabled, measure and document improvement</objective>

  <rationale>
  This phase produces the proof that ACE learning improves RALPH performance.
  We run the same benchmark suite with learning enabled and compare against baseline.
  Multiple runs build the skillbook and should show progressive improvement.
  </rationale>

  <tasks>
    <task priority="critical" id="4.1">
      <name>Run learning-enabled benchmark suite (first pass)</name>
      <description>
        Run benchmark with empty skillbook, learning enabled. This is the "training" pass.
      </description>
      <location>.benchmarks/results/learning-pass1-{date}.json</location>
      <implementation_notes>
        - Clear skillbook before run
        - Enable learning
        - Run full prompt suite
        - Capture skillbook state after each prompt
        - Expect similar or slightly worse than baseline (learning overhead)
      </implementation_notes>
    </task>

    <task priority="critical" id="4.2">
      <name>Run learning-enabled benchmark suite (second pass)</name>
      <description>
        Run benchmark with trained skillbook from pass 1. This should show improvement.
      </description>
      <location>.benchmarks/results/learning-pass2-{date}.json</location>
      <implementation_notes>
        - Keep skillbook from pass 1
        - Run full prompt suite again
        - Compare against pass 1 and baseline
        - Document which prompts improved most
      </implementation_notes>
    </task>

    <task priority="high" id="4.3">
      <name>Analyze and document improvement</name>
      <description>
        Generate comprehensive comparison report.
      </description>
      <location>.benchmarks/results/analysis-{date}.md</location>
      <implementation_notes>
        - Baseline vs Pass 1 vs Pass 2 comparison
        - Per-prompt improvement breakdown
        - Aggregate metrics improvement
        - Skillbook size and content analysis
        - Cost analysis (learning overhead vs iteration savings)
      </implementation_notes>
    </task>

    <task priority="medium" id="4.4">
      <name>Iterate on prompts if no improvement</name>
      <description>
        If improvement is not significant, analyze why and adjust prompts or configuration.
      </description>
      <location>N/A - conditional task</location>
      <implementation_notes>
        - Check if skills being learned are relevant
        - Analyze Reflector output for quality
        - Consider prompt types that benefit more from memory
        - Adjust ACE configuration if needed
        - May need to add more repetitive prompts
      </implementation_notes>
    </task>
  </tasks>

  <deliverables>
    <deliverable>Learning pass 1 results JSON</deliverable>
    <deliverable>Learning pass 2 results JSON</deliverable>
    <deliverable>Comprehensive analysis report (markdown)</deliverable>
    <deliverable>Trained skillbook with proven improvements</deliverable>
  </deliverables>

  <dependencies>Phase 3 complete with baseline results</dependencies>

  <validation>
    <criterion>Demonstrable improvement in at least 2 metrics</criterion>
    <criterion>Pass 2 shows improvement over Pass 1 (learning retention)</criterion>
    <criterion>Analysis report documents specific improvements</criterion>
    <criterion>Skillbook contains relevant, high-quality skills</criterion>
  </validation>

  <estimated_effort>4-6 hours (may need iteration)</estimated_effort>
</phase>

<phase number="5" name="documentation-iteration">
  <objective>Document what causes improvements, iterate until significant gains achieved</objective>

  <rationale>
  The final phase ensures findings are documented, reproducible, and actionable.
  If initial results are marginal, we iterate on configuration and prompts.
  The goal is to have clear documentation of when and how ACE learning helps.
  </rationale>

  <tasks>
    <task priority="critical" id="5.1">
      <name>Create ACE learning analysis documentation</name>
      <description>
        Comprehensive documentation of what learning achieves and how to use it effectively.
      </description>
      <location>docs/ACE_LEARNING_ANALYSIS.md</location>
      <implementation_notes>
        - What types of tasks benefit most from learning
        - How many iterations needed before improvement visible
        - Optimal skillbook size and configuration
        - Cost-benefit analysis
        - When NOT to use learning (overhead > benefit)
      </implementation_notes>
    </task>

    <task priority="high" id="5.2">
      <name>Analyze skillbook contents</name>
      <description>
        Deep dive into what skills were learned and which correlate with improvement.
      </description>
      <location>.benchmarks/results/skillbook-analysis.md</location>
      <implementation_notes>
        - List top skills by effectiveness score
        - Categorize skills by type (error handling, patterns, etc.)
        - Identify which skills contributed to specific improvements
        - Document any harmful skills that were pruned
      </implementation_notes>
    </task>

    <task priority="medium" id="5.3">
      <name>Tune reflection prompts if needed</name>
      <description>
        If skills are low quality, consider customizing Reflector prompts.
      </description>
      <location>src/ralph_orchestrator/learning/ace_adapter.py</location>
      <implementation_notes>
        - Add RALPH-specific context to Reflector prompt
        - Emphasize iteration-level learning
        - Guide skill extraction for orchestration patterns
        - Test with subset of benchmarks
      </implementation_notes>
    </task>

    <task priority="medium" id="5.4">
      <name>Create production skillbook</name>
      <description>
        Curate a production-ready skillbook with proven high-value skills.
      </description>
      <location>.agent/skillbook/production-skillbook.json</location>
      <implementation_notes>
        - Export top skills from benchmark runs
        - Remove low-value or experimental skills
        - Consider as seed file for new projects
        - Version control for team sharing
      </implementation_notes>
    </task>

    <task priority="low" id="5.5">
      <name>Create final benchmark report</name>
      <description>
        Publishable report summarizing the ACE + RALPH integration success.
      </description>
      <location>docs/ACE_BENCHMARK_REPORT.md</location>
      <implementation_notes>
        - Executive summary of results
        - Methodology documentation
        - Results with visualizations (tables, charts)
        - Recommendations for users
        - Future improvement ideas
      </implementation_notes>
    </task>
  </tasks>

  <deliverables>
    <deliverable>docs/ACE_LEARNING_ANALYSIS.md</deliverable>
    <deliverable>Skillbook analysis with top skills identified</deliverable>
    <deliverable>Production-ready skillbook</deliverable>
    <deliverable>docs/ACE_BENCHMARK_REPORT.md</deliverable>
  </deliverables>

  <dependencies>Phase 4 shows some improvement</dependencies>

  <validation>
    <criterion>Clear documentation of what learning achieves</criterion>
    <criterion>Optimized skillbook with proven improvements</criterion>
    <criterion>Reproducible benchmark methodology documented</criterion>
    <criterion>Cost-benefit analysis complete</criterion>
  </validation>

  <estimated_effort>3-5 hours</estimated_effort>
</phase>
</phases>

<benchmark_design>
  <prompt_categories>
    <category name="repetitive-tasks" count="4">
      <description>
        Tasks that repeat patterns across multiple operations. Learning should remember
        the pattern and apply it more efficiently in subsequent iterations.
      </description>
      <prompts>
        <prompt id="RT-1">
          <name>Create similar functions</name>
          <task>Create 5 Python functions that each validate a different input type (email, phone, date, URL, UUID). Each should return True/False and include docstrings.</task>
          <expected_improvement>After learning the validation pattern, later functions should be created faster with fewer iterations.</expected_improvement>
          <success_criteria>All 5 functions created, pass basic tests</success_criteria>
        </prompt>
        <prompt id="RT-2">
          <name>Add logging to modules</name>
          <task>Add structured logging (using loguru or logging) to the 3 main modules: orchestrator.py, adapters/base.py, and main.py. Follow consistent patterns.</task>
          <expected_improvement>After learning logging pattern in first module, subsequent modules should be faster.</expected_improvement>
          <success_criteria>All 3 modules have consistent logging added</success_criteria>
        </prompt>
        <prompt id="RT-3">
          <name>Create test fixtures</name>
          <task>Create pytest fixtures for 4 different test scenarios: mock API client, temporary directory, sample config, and mock subprocess. Place in conftest.py.</task>
          <expected_improvement>After learning fixture pattern, later fixtures created with fewer iterations.</expected_improvement>
          <success_criteria>All 4 fixtures created and importable</success_criteria>
        </prompt>
        <prompt id="RT-4">
          <name>Add type hints</name>
          <task>Add comprehensive type hints to the learning/ace_adapter.py file. Include all function signatures and class attributes.</task>
          <expected_improvement>Pattern recognition for type hint syntax should improve over file.</expected_improvement>
          <success_criteria>mypy passes on the file</success_criteria>
        </prompt>
      </prompts>
      <metrics>
        <metric>Iterations for first vs last item in sequence</metric>
        <metric>Total iterations for complete task</metric>
        <metric>Tokens per item in sequence</metric>
      </metrics>
    </category>

    <category name="error-recovery" count="4">
      <description>
        Tasks that commonly fail on first attempt due to common pitfalls. Learning should
        remember what went wrong and avoid the same mistakes in future runs.
      </description>
      <prompts>
        <prompt id="ER-1">
          <name>Fix import errors</name>
          <task>The file tests/test_broken_imports.py has intentionally broken imports. Fix all import errors and make the file importable.</task>
          <expected_improvement>Should learn common import error patterns and fix faster on subsequent runs.</expected_improvement>
          <success_criteria>File imports successfully, all tests can be discovered</success_criteria>
        </prompt>
        <prompt id="ER-2">
          <name>Handle async context</name>
          <task>Fix the async/await errors in tests/test_async_broken.py. The file mixes sync and async incorrectly.</task>
          <expected_improvement>Should learn async patterns and avoid sync/async mixing errors.</expected_improvement>
          <success_criteria>All async tests run and pass</success_criteria>
        </prompt>
        <prompt id="ER-3">
          <name>Fix path handling</name>
          <task>Fix the path handling bugs in scripts/broken_paths.py. The script has Windows/Unix path compatibility issues.</task>
          <expected_improvement>Should learn Path vs string patterns and cross-platform handling.</expected_improvement>
          <success_criteria>Script runs on both Windows and Unix paths</success_criteria>
        </prompt>
        <prompt id="ER-4">
          <name>Fix environment variable handling</name>
          <task>Fix the environment variable handling in scripts/broken_env.py. Missing defaults, type errors, and validation issues.</task>
          <expected_improvement>Should learn robust environment variable patterns.</expected_improvement>
          <success_criteria>Script handles missing, malformed, and valid env vars correctly</success_criteria>
        </prompt>
      </prompts>
      <metrics>
        <metric>Iterations to complete fix</metric>
        <metric>Rollbacks/retries during task</metric>
        <metric>Success rate on first attempt (learning vs baseline)</metric>
      </metrics>
    </category>

    <category name="project-specific" count="4">
      <description>
        Tasks specific to the RALPH codebase that require understanding project conventions.
        Learning should capture project-specific patterns and conventions.
      </description>
      <prompts>
        <prompt id="PS-1">
          <name>Add new adapter</name>
          <task>Create a new adapter (RooAdapter) following the existing adapter patterns in src/ralph_orchestrator/adapters/. Should inherit from ToolAdapter and implement execute().</task>
          <expected_improvement>Should learn RALPH's adapter patterns and apply them correctly.</expected_improvement>
          <success_criteria>New adapter follows existing patterns, passes type check</success_criteria>
        </prompt>
        <prompt id="PS-2">
          <name>Add CLI flag</name>
          <task>Add a new CLI flag --dry-run-verbose to main.py that shows what would be executed without running. Follow existing flag patterns.</task>
          <expected_improvement>Should learn RALPH's CLI structure and argparse patterns.</expected_improvement>
          <success_criteria>Flag works correctly, --help shows it, follows existing patterns</success_criteria>
        </prompt>
        <prompt id="PS-3">
          <name>Add metrics tracking</name>
          <task>Add a new metric (rollback_count) to the metrics system following existing patterns in metrics.py.</task>
          <expected_improvement>Should learn metrics system conventions.</expected_improvement>
          <success_criteria>New metric tracked correctly, appears in output</success_criteria>
        </prompt>
        <prompt id="PS-4">
          <name>Add configuration option</name>
          <task>Add a new configuration option (checkpoint_interval) to RalphConfig following existing patterns. Should be configurable via CLI and env var.</task>
          <expected_improvement>Should learn RALPH's configuration patterns.</expected_improvement>
          <success_criteria>Option works via CLI, env var, and config file</success_criteria>
        </prompt>
      </prompts>
      <metrics>
        <metric>Adherence to project patterns (manual review score 1-5)</metric>
        <metric>Iterations to completion</metric>
        <metric>Errors requiring manual intervention</metric>
      </metrics>
    </category>
  </prompt_categories>

  <metrics_to_capture>
    <metric name="iteration_count" primary="true">
      <description>Number of iterations to complete the task</description>
      <capture_method>RALPH metrics output, --metrics flag</capture_method>
      <improvement_target>20% fewer iterations on trained runs</improvement_target>
      <calculation>Direct count from RALPH output</calculation>
    </metric>

    <metric name="token_usage" primary="true">
      <description>Total tokens consumed (input + output)</description>
      <capture_method>RALPH cost tracker, API logs</capture_method>
      <improvement_target>15% reduction in total tokens</improvement_target>
      <calculation>Sum of all iteration token counts</calculation>
    </metric>

    <metric name="time_to_completion" primary="false">
      <description>Wall clock time from start to completion</description>
      <capture_method>Benchmark script timestamps</capture_method>
      <improvement_target>10% faster (may vary due to API latency)</improvement_target>
      <calculation>End time - Start time in seconds</calculation>
    </metric>

    <metric name="success_rate" primary="true">
      <description>Percentage of tasks completed without human intervention</description>
      <capture_method>Exit status, completion markers</capture_method>
      <improvement_target>Higher first-try success rate</improvement_target>
      <calculation>(Successful completions / Total attempts) * 100</calculation>
    </metric>

    <metric name="rollback_count" primary="false">
      <description>Number of checkpoint rollbacks during task</description>
      <capture_method>RALPH git integration logs</capture_method>
      <improvement_target>50% fewer rollbacks</improvement_target>
      <calculation>Count of rollback events in logs</calculation>
    </metric>

    <metric name="cost_usd" primary="false">
      <description>Estimated cost in USD for the task</description>
      <capture_method>RALPH cost tracker</capture_method>
      <improvement_target>Net savings after accounting for learning overhead</improvement_target>
      <calculation>Token usage * model pricing</calculation>
    </metric>
  </metrics_to_capture>

  <methodology>
    <overview>
      A/B comparison methodology with statistical rigor. Each configuration is run
      multiple times to account for variance. Results are compared using per-prompt
      and aggregate metrics.
    </overview>

    <step order="1" name="environment_setup">
      <action>Ensure clean git state, identical environment for all runs</action>
      <details>
        - Git checkout to known clean state
        - Same model, temperature, max_iterations for all runs
        - Same API key, rate limits
        - Document exact configuration
      </details>
    </step>

    <step order="2" name="baseline_runs">
      <action>Run full benchmark suite with learning disabled (3 runs)</action>
      <details>
        - Set --no-learning flag
        - Run all 12 prompts
        - Record all metrics
        - Calculate mean and standard deviation
        - Identify prompts with high variance
      </details>
    </step>

    <step order="3" name="learning_pass_1">
      <action>Run benchmark with empty skillbook, learning enabled</action>
      <details>
        - Clear skillbook (delete or rename existing)
        - Set --learning flag
        - Run all 12 prompts in order
        - Save skillbook after each prompt
        - Record metrics and skillbook state
      </details>
    </step>

    <step order="4" name="learning_pass_2">
      <action>Run benchmark again with trained skillbook</action>
      <details>
        - Keep skillbook from pass 1
        - Run same 12 prompts in same order
        - Record metrics
        - Compare against pass 1 and baseline
      </details>
    </step>

    <step order="5" name="analysis">
      <action>Compare metrics and generate report</action>
      <details>
        - Calculate improvement percentages
        - Identify which prompts improved most
        - Analyze skillbook contents
        - Document findings
      </details>
    </step>

    <step order="6" name="iteration">
      <action>If improvement < 10%, iterate on configuration</action>
      <details>
        - Analyze why improvement is limited
        - Adjust prompts, ACE config, or skillbook seed
        - Re-run from step 3
        - Document what changes helped
      </details>
    </step>
  </methodology>

  <test_environment>
    <model>claude-sonnet-4-5-20250929 (or current default)</model>
    <ace_model>gpt-4o-mini (for cost efficiency)</ace_model>
    <max_iterations>10</max_iterations>
    <checkpoint_enabled>true</checkpoint_enabled>
    <learning_async>true</learning_async>
    <skillbook_max_skills>100</skillbook_max_skills>
  </test_environment>
</benchmark_design>

<metadata>
  <confidence level="high">
    <value>0.85</value>
    <justification>
      High confidence based on:
      - Comprehensive research of both ACE docs and RALPH integration
      - Existing ACE integration is functional, gaps are well-understood
      - Benchmark methodology follows standard A/B testing practices
      - ACE has documented +17% improvement in external benchmarks

      Uncertainty factors:
      - Unknown how well ACE patterns transfer to RALPH's iteration model
      - First time running this specific benchmark suite
      - Learning overhead may offset gains for short tasks
    </justification>
  </confidence>

  <dependencies>
    <dependency type="required" status="available">ANTHROPIC_API_KEY environment variable</dependency>
    <dependency type="required" status="available">ace-framework package installed</dependency>
    <dependency type="required" status="available">RALPH orchestrator functional</dependency>
    <dependency type="required" status="available">Git repository for checkpoints</dependency>
    <dependency type="optional" status="unknown">Monitoring dashboard for metric visualization</dependency>
    <dependency type="optional" status="unknown">gpt-4o-mini API access for efficient ACE operations</dependency>
  </dependencies>

  <risks>
    <risk severity="medium">
      <description>Learning overhead may exceed benefits for simple tasks</description>
      <mitigation>Include short and long tasks in benchmark, analyze breakeven point</mitigation>
    </risk>
    <risk severity="low">
      <description>LangChain/Pydantic conflict may resurface with ACE updates</description>
      <mitigation>Pin ACE version, monitor for breaking changes</mitigation>
    </risk>
    <risk severity="low">
      <description>Benchmark prompts may not represent real usage</description>
      <mitigation>Include variety of task types, adjust based on findings</mitigation>
    </risk>
  </risks>

  <open_questions>
    <question priority="high" phase="4">
      What task duration/complexity is the breakeven point for learning overhead?
      Hypothesis: Tasks requiring >5 iterations benefit, shorter tasks may not.
    </question>
    <question priority="medium" phase="5">
      Should skillbook be project-specific or global (user-level)?
      Recommendation: Start project-specific, consider global for common patterns.
    </question>
    <question priority="medium" phase="2">
      What's the optimal skillbook size before performance degrades?
      Research suggests max_skills=100 is reasonable default.
    </question>
    <question priority="low" phase="5">
      Should skillbook be version controlled with the project?
      Recommendation: Yes, enables team learning sharing.
    </question>
  </open_questions>

  <assumptions>
    <assumption validated="true">ACE framework API key handling is now working correctly</assumption>
    <assumption validated="true">RALPH metrics system provides necessary data for benchmarking</assumption>
    <assumption validated="false">ACE improvements transfer to RALPH's iteration model</assumption>
    <assumption validated="false">gpt-4o-mini is sufficient quality for ACE operations</assumption>
    <assumption validated="false">12 benchmark prompts are sufficient for statistical significance</assumption>
  </assumptions>

  <timeline>
    <total_estimate>19-28 hours across 5 phases</total_estimate>
    <phase_breakdown>
      <phase number="1">4-6 hours</phase>
      <phase number="2">3-4 hours</phase>
      <phase number="3">5-7 hours</phase>
      <phase number="4">4-6 hours (may need iteration)</phase>
      <phase number="5">3-5 hours</phase>
    </phase_breakdown>
    <suggested_pace>Complete Phase 1-2 in first day, Phase 3-4 in second day, Phase 5 as findings allow</suggested_pace>
  </timeline>
</metadata>
</plan>
