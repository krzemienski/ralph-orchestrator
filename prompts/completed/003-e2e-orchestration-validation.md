<objective>
Validate END-TO-END orchestration workflow with REAL subagent spawning and validation.

This is Phase 3 of comprehensive functional validation for ralph-orchestrator.
Tests complete orchestration cycles: prompt generation → spawn → result aggregation → validation.
</objective>

<context>
Full orchestration flow:
1. OrchestrationManager generates subagent prompt
2. spawn_subagent() executes real Claude CLI
3. Results collected via CoordinationManager
4. aggregate_results() determines verdict
5. Validation system checks evidence

This tests the INTEGRATION of all components working together.
</context>

<execution_requirements>
Use sequential-thinking MCP for structured analysis.
Use Opus 4.5 model for maximum capability.
Use claude-mem for context preservation.

MANDATORY: Real Claude CLI calls. Real file I/O. No mocking.
Isolated test directories for each scenario.
</execution_requirements>

<validation_scenarios>

**Scenario 1: Full Orchestration Cycle - Single Subagent**
```python
import asyncio
import tempfile
from pathlib import Path
from ralph_orchestrator.orchestration.manager import OrchestrationManager
from ralph_orchestrator.main import RalphConfig

async def test_full_orchestration_single():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        config = RalphConfig(orchestration_enabled=True)
        manager = OrchestrationManager(config, base_dir=base_dir)

        # Step 1: Generate prompt
        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="test-phase",
            criteria=["Verify system responds", "Check JSON format"],
            subagent_id="001"
        )

        assert "validator" in prompt.lower() or "validation" in prompt.lower()
        assert "test-phase" in prompt

        # Step 2: Spawn subagent (REAL Claude call)
        result = await manager.spawn_subagent(
            subagent_type="validator",
            prompt="Say 'validation complete' in JSON format: {\"status\": \"complete\"}",
            timeout=60
        )

        assert result["success"] == True
        assert result["parsed_json"] is not None

        # Step 3: Write result to coordination file
        coord_file = base_dir / ".ralph-coordination" / "subagent-001-result.json"
        coord_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        coord_file.write_text(json.dumps({
            "subagent_id": "001",
            "verdict": "PASS",
            "evidence": result["parsed_json"]
        }))

        # Step 4: Aggregate results
        aggregated = manager.aggregate_results()

        assert aggregated["verdict"] == "PASS"
        assert len(aggregated["subagent_results"]) == 1

        return {
            "scenario": "full_single",
            "prompt_generated": len(prompt) > 100,
            "spawn_success": result["success"],
            "aggregation_verdict": aggregated["verdict"]
        }

result = asyncio.run(test_full_orchestration_single())
```

**Scenario 2: Multi-Subagent Orchestration**
```python
async def test_multi_subagent_orchestration():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        config = RalphConfig(orchestration_enabled=True)
        manager = OrchestrationManager(config, base_dir=base_dir)

        subagent_types = ["validator", "analyst"]
        results = []

        for i, sa_type in enumerate(subagent_types):
            # Spawn each subagent
            result = await manager.spawn_subagent(
                subagent_type=sa_type,
                prompt=f"Respond: {sa_type} complete",
                timeout=60
            )

            # Write coordination file
            coord_file = base_dir / ".ralph-coordination" / f"subagent-{i:03d}-result.json"
            coord_file.parent.mkdir(parents=True, exist_ok=True)

            import json
            coord_file.write_text(json.dumps({
                "subagent_id": f"{i:03d}",
                "verdict": "PASS" if result["success"] else "FAIL",
                "type": sa_type
            }))

            results.append(result)

        # Aggregate all results
        aggregated = manager.aggregate_results()

        assert aggregated["verdict"] == "PASS"
        assert len(aggregated["subagent_results"]) == 2

        return {
            "scenario": "multi_subagent",
            "subagents_spawned": len(results),
            "all_success": all(r["success"] for r in results),
            "final_verdict": aggregated["verdict"]
        }

result = asyncio.run(test_multi_subagent_orchestration())
```

**Scenario 3: Orchestration with Failure Detection**
```python
async def test_orchestration_failure_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        config = RalphConfig(orchestration_enabled=True)
        manager = OrchestrationManager(config, base_dir=base_dir)

        # Create mixed results - one pass, one fail
        coord_dir = base_dir / ".ralph-coordination"
        coord_dir.mkdir(parents=True, exist_ok=True)

        import json

        (coord_dir / "subagent-001-result.json").write_text(json.dumps({
            "subagent_id": "001",
            "verdict": "PASS"
        }))

        (coord_dir / "subagent-002-result.json").write_text(json.dumps({
            "subagent_id": "002",
            "verdict": "FAIL",
            "reason": "Test failed"
        }))

        aggregated = manager.aggregate_results()

        # Should be FAIL because one subagent failed
        assert aggregated["verdict"] == "FAIL"

        return {
            "scenario": "failure_detection",
            "detected_failure": aggregated["verdict"] == "FAIL",
            "summary": aggregated["summary"]
        }

result = asyncio.run(test_orchestration_failure_detection())
```

**Scenario 4: Orchestration → Validation Chain**
```python
async def test_orchestration_validation_chain():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        evidence_dir = base_dir / "validation-evidence" / "test-run"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        config = RalphConfig(orchestration_enabled=True)
        manager = OrchestrationManager(config, base_dir=base_dir)

        # Spawn a subagent
        result = await manager.spawn_subagent(
            subagent_type="validator",
            prompt="Output valid JSON: {\"validated\": true}",
            timeout=60
        )

        # Write evidence file
        import json
        evidence_file = evidence_dir / "spawn-result.json"
        evidence_file.write_text(json.dumps(result["parsed_json"] or {"result": result["stdout"]}))

        # Now validate the evidence
        from ralph_orchestrator.validation import validate_evidence_directory
        validation = validate_evidence_directory(str(evidence_dir))

        # Should pass - no error patterns in valid response
        assert validation.success == True, f"Validation failed: {validation.errors}"

        return {
            "scenario": "orchestration_validation_chain",
            "spawn_success": result["success"],
            "validation_success": validation.success,
            "chain_complete": result["success"] and validation.success
        }

result = asyncio.run(test_orchestration_validation_chain())
```

**Scenario 5: Prompt Template Verification**
```python
def test_prompt_templates():
    from ralph_orchestrator.orchestration.config import SUBAGENT_PROFILES
    from ralph_orchestrator.main import RalphConfig
    from ralph_orchestrator.orchestration.manager import OrchestrationManager

    config = RalphConfig(orchestration_enabled=True)
    manager = OrchestrationManager(config)

    results = []

    for subagent_type in SUBAGENT_PROFILES.keys():
        prompt = manager.generate_subagent_prompt(
            subagent_type=subagent_type,
            phase="test-phase",
            criteria=["Test criterion 1", "Test criterion 2"],
            subagent_id="TEST"
        )

        # Verify prompt has required elements
        checks = {
            "has_content": len(prompt) > 50,
            "has_phase": "test-phase" in prompt,
            "has_criteria": "Test criterion" in prompt,
            "has_id": "TEST" in prompt
        }

        results.append({
            "type": subagent_type,
            "checks": checks,
            "all_pass": all(checks.values())
        })

    return {
        "scenario": "prompt_templates",
        "types_tested": len(results),
        "all_valid": all(r["all_pass"] for r in results),
        "details": results
    }

result = test_prompt_templates()
```
</validation_scenarios>

<success_criteria>
All 5 E2E scenarios must PASS:

| Scenario | Success Condition |
|----------|-------------------|
| Full Single | Prompt→Spawn→Aggregate all work |
| Multi-Subagent | 2+ subagents coordinated |
| Failure Detection | FAIL verdict when subagent fails |
| Validation Chain | Spawn output validates successfully |
| Prompt Templates | All subagent types generate valid prompts |

Functional: 5/5 scenarios pass
Evidence: Save to validation-evidence/functional-03/
</success_criteria>

<output>
1. Execute each E2E scenario
2. Create evidence file: `./validation-evidence/functional-03/e2e-orchestration.txt`
3. Report structured results:
   ```
   END-TO-END ORCHESTRATION VALIDATION
   ===================================
   Scenario 1 (Full Single): PASS/FAIL
   Scenario 2 (Multi-Subagent): PASS/FAIL
   Scenario 3 (Failure Detection): PASS/FAIL
   Scenario 4 (Validation Chain): PASS/FAIL
   Scenario 5 (Prompt Templates): PASS/FAIL

   Overall: X/5 PASS
   ```
4. If any FAIL: Document and iterate
5. If all PASS: Proceed to iteration runner
</output>

<iteration_protocol>
If ANY scenario fails:
1. Isolate the failing component
2. Trace the data flow to find failure point
3. Apply targeted fix
4. Re-run only the affected scenario
5. Verify no regressions in other scenarios

Maximum 3 iterations per scenario.
</iteration_protocol>
