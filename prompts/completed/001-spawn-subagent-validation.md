<objective>
Validate spawn_subagent() with REAL Claude CLI execution - no mocking, no simulation.

This is Phase 1 of comprehensive functional validation for ralph-orchestrator.
Tests must spawn actual Claude processes and verify real output parsing.
</objective>

<context>
Target module: src/ralph_orchestrator/orchestration/manager.py
Method: OrchestrationManager.spawn_subagent()

The spawn_subagent() method:
- Uses asyncio.create_subprocess_exec to call 'claude' CLI
- Captures stdout/stderr
- Parses JSON responses
- Handles timeouts with subprocess termination
- Returns structured result dict

This validation confirms the implementation ACTUALLY WORKS with real Claude calls.
</context>

<execution_requirements>
Use sequential-thinking MCP for structured analysis.
Use Opus 4.5 model for maximum capability.
Use claude-mem for context preservation.

MANDATORY: All tests must execute REAL code paths - no mocking permitted.
</execution_requirements>

<validation_scenarios>
Execute each scenario and capture evidence:

**Scenario 1: Simple Text Response**
```python
import asyncio
from ralph_orchestrator.orchestration.manager import OrchestrationManager
from ralph_orchestrator.main import RalphConfig

async def test_simple_spawn():
    config = RalphConfig(orchestration_enabled=True)
    manager = OrchestrationManager(config)

    result = await manager.spawn_subagent(
        subagent_type="validator",
        prompt="Say exactly: hello",
        timeout=30
    )

    # Verify structure
    assert "success" in result
    assert "return_code" in result
    assert "stdout" in result
    assert "parsed_json" in result

    # Verify real execution
    assert result["success"] == True
    assert result["return_code"] == 0
    assert len(result["stdout"]) > 0

    return result

result = asyncio.run(test_simple_spawn())
```

**Scenario 2: JSON Response Parsing**
```python
async def test_json_parsing():
    config = RalphConfig(orchestration_enabled=True)
    manager = OrchestrationManager(config)

    result = await manager.spawn_subagent(
        subagent_type="analyst",
        prompt='Respond with valid JSON: {"status": "ok", "count": 42}',
        timeout=30
    )

    # Verify JSON was parsed
    assert result["parsed_json"] is not None
    assert result["parsed_json"]["type"] == "result"  # Claude CLI wrapper

    return result

result = asyncio.run(test_json_parsing())
```

**Scenario 3: Timeout Handling**
```python
async def test_timeout_cleanup():
    import subprocess
    import os

    config = RalphConfig(orchestration_enabled=True)
    manager = OrchestrationManager(config)

    # Count claude processes before
    before = subprocess.run(
        ["pgrep", "-f", "claude"],
        capture_output=True
    ).stdout.decode().strip().split('\n')
    before_count = len([p for p in before if p])

    result = await manager.spawn_subagent(
        subagent_type="validator",
        prompt="Count to 1000000 slowly, one number per line",
        timeout=2  # Very short timeout
    )

    # Should timeout
    assert result["success"] == False
    assert "Timeout" in result["error"]

    # Wait for cleanup
    await asyncio.sleep(1)

    # Count claude processes after
    after = subprocess.run(
        ["pgrep", "-f", "claude"],
        capture_output=True
    ).stdout.decode().strip().split('\n')
    after_count = len([p for p in after if p])

    # No orphaned processes
    assert after_count <= before_count, "Orphaned subprocess detected!"

    return {"timeout_handled": True, "no_orphans": after_count <= before_count}

result = asyncio.run(test_timeout_cleanup())
```

**Scenario 4: Error Handling - Missing CLI**
```python
async def test_missing_cli():
    import os
    config = RalphConfig(orchestration_enabled=True)
    manager = OrchestrationManager(config)

    # Temporarily break PATH
    original_path = os.environ.get("PATH", "")
    os.environ["PATH"] = "/nonexistent"

    try:
        result = await manager.spawn_subagent(
            subagent_type="validator",
            prompt="test",
            timeout=5
        )

        assert result["success"] == False
        assert "not found" in result["error"].lower()
    finally:
        os.environ["PATH"] = original_path

    return {"error_handling": "verified"}
```
</validation_scenarios>

<success_criteria>
All 4 scenarios must PASS with real execution:

| Scenario | Success Condition |
|----------|-------------------|
| Simple Text | success=True, return_code=0, stdout has content |
| JSON Parsing | parsed_json not None, has "type" key |
| Timeout Cleanup | error contains "Timeout", no orphaned processes |
| Missing CLI | success=False, error mentions "not found" |

Functional: 4/4 scenarios pass
Evidence: Save raw results to validation-evidence/functional-01/
</success_criteria>

<output>
1. Execute each scenario capturing full output
2. Create evidence file: `./validation-evidence/functional-01/spawn-validation.txt`
3. Report results in structured format:
   ```
   SPAWN_SUBAGENT FUNCTIONAL VALIDATION
   =====================================
   Scenario 1 (Simple): PASS/FAIL - [details]
   Scenario 2 (JSON): PASS/FAIL - [details]
   Scenario 3 (Timeout): PASS/FAIL - [details]
   Scenario 4 (Error): PASS/FAIL - [details]

   Overall: X/4 PASS
   ```
4. If any FAIL: Document failure reason and exit
5. If all PASS: Signal ready for next validation phase
</output>

<iteration_protocol>
If ANY scenario fails:
1. Document the failure with full stack trace
2. Identify root cause
3. Create fix hypothesis
4. Apply minimal fix
5. Re-run ONLY the failed scenario
6. Repeat until PASS

Maximum 3 iterations per scenario before escalating.
</iteration_protocol>
