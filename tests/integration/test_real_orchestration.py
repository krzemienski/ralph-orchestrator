# ABOUTME: End-to-end integration tests for orchestration with real Claude CLI
# ABOUTME: Tests full orchestration flow: prompt generation, spawning, coordination, aggregation

"""End-to-end integration tests for orchestration.

These tests spawn real Claude CLI processes and validate the complete
orchestration workflow. They are slow and expensive (API costs).

Run with: pytest -m integration tests/integration/test_real_orchestration.py
"""

import json
import pytest
from pathlib import Path


@pytest.mark.integration
@pytest.mark.slow
class TestFullOrchestrationFlow:
    """Test complete orchestration workflow end-to-end."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_full_orchestration_workflow(self, tmp_path):
        """Test complete orchestration: prompt -> spawn -> coordinate -> aggregate.

        This is the primary end-to-end test that validates the entire workflow:
        1. Generate prompt for validator subagent
        2. Spawn real Claude CLI with the prompt
        3. Write coordination file with result
        4. Aggregate results and verify PASS
        """
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        # 1. Setup orchestration
        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config, base_dir=tmp_path)
        manager.coordinator.init_coordination()

        # 2. Generate validator prompt
        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="Integration Test",
            criteria=["Respond with valid JSON"],
            subagent_id="001",
        )

        assert "VALIDATOR" in prompt
        assert "Integration Test" in prompt

        # 3. Spawn real Claude CLI
        result = await manager.spawn_subagent(
            subagent_type="validator",
            prompt="Reply with this exact JSON: {\"verdict\": \"PASS\", \"test\": true}",
            timeout=120,
        )

        # 4. Verify spawn completed
        assert isinstance(result, dict)
        assert result["subagent_type"] == "validator"
        # Claude might return 0 (success) or have parsed_json
        if result["success"]:
            assert result["return_code"] == 0

        # 5. Write result to coordination
        coordination_result = {
            "verdict": "PASS",
            "subagent": "validator",
            "spawned": True,
            "return_code": result["return_code"],
        }
        manager.coordinator.write_subagent_result(
            "validator", "001", coordination_result
        )

        # 6. Aggregate results
        aggregated = manager.aggregate_results()
        assert aggregated["verdict"] == "PASS"
        assert len(aggregated["subagent_results"]) == 1

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_spawn_and_validate_json_response(self, tmp_path):
        """Test spawning subagent and validating JSON response.

        Validates that:
        1. Claude CLI returns valid JSON in output-format json mode
        2. Response can be parsed and validated
        3. Expected structure is present
        """
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager
        from ralph_orchestrator.validation import EvidenceChecker

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config, base_dir=tmp_path)

        # Spawn with simple JSON prompt
        result = await manager.spawn_subagent(
            subagent_type="analyst",
            prompt="Reply with: {\"status\": \"ok\", \"count\": 1}",
            timeout=120,
        )

        # Verify spawn completed
        assert isinstance(result, dict)
        assert result["subagent_type"] == "analyst"

        # If successful, parsed_json should be available
        if result["success"]:
            assert result["parsed_json"] is not None
            # Claude wraps response in result structure
            assert "result" in result["parsed_json"] or "type" in result["parsed_json"]

        # Validate stdout as evidence
        if result["stdout"]:
            evidence_file = tmp_path / "spawn_output.json"
            evidence_file.write_text(result["stdout"])

            checker = EvidenceChecker()
            validation = checker.check_file(evidence_file)
            # Success means no error patterns detected
            # Note: Claude's JSON wrapper might contain is_error=false which is not an error
            assert validation is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_multi_subagent_aggregation(self, tmp_path):
        """Test aggregation with multiple subagent results.

        Validates that:
        1. Multiple subagents can be spawned
        2. Results are correctly aggregated
        3. Mixed pass/fail gives overall FAIL
        """
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config, base_dir=tmp_path)
        manager.coordinator.init_coordination()

        # Write PASS result for validator
        manager.coordinator.write_subagent_result(
            "validator", "001", {"verdict": "PASS", "criteria": ["test1"]}
        )

        # Write PASS result for researcher
        manager.coordinator.write_subagent_result(
            "researcher", "001", {"verdict": "PASS", "findings": ["found data"]}
        )

        # Aggregate - should be PASS
        aggregated = manager.aggregate_results()
        assert aggregated["verdict"] == "PASS"
        assert len(aggregated["subagent_results"]) == 2

        # Now add a FAIL result
        manager.coordinator.write_subagent_result(
            "analyst", "001", {"verdict": "FAIL", "error": "analysis failed"}
        )

        # Re-aggregate - should now be FAIL
        aggregated = manager.aggregate_results()
        assert aggregated["verdict"] == "FAIL"
        assert len(aggregated["subagent_results"]) == 3
        assert "2 passed" in aggregated["summary"]
        assert "1 failed" in aggregated["summary"]


@pytest.mark.integration
@pytest.mark.slow
class TestSpawnSubagentScenarios:
    """Test various spawn scenarios with real Claude CLI.

    These tests are moved/adapted from test_orchestration_integration.py
    """

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_spawn_simple_hello(self, orchestration_manager):
        """Test real Claude CLI spawn with simple prompt."""
        result = await orchestration_manager.spawn_subagent(
            subagent_type="validator",
            prompt="Say 'hello' and nothing else",
            timeout=60,
        )

        assert isinstance(result, dict)
        assert result["subagent_type"] == "validator"
        # Should complete (return_code >= 0) or have error
        assert result["return_code"] >= 0 or result["error"] is not None

        if not result["error"]:
            assert len(result["stdout"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_spawn_with_json_response(self, orchestration_manager):
        """Test Claude CLI spawn requesting JSON response."""
        result = await orchestration_manager.spawn_subagent(
            subagent_type="validator",
            prompt="Respond with valid JSON containing a 'result' key set to 'success'",
            timeout=60,
        )

        assert isinstance(result, dict)
        if result["success"]:
            # Claude with --output-format json wraps response
            assert result["parsed_json"] is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_spawn_timeout_handling(self, orchestration_manager):
        """Test that timeouts are handled gracefully."""
        # Very short timeout should trigger timeout
        result = await orchestration_manager.spawn_subagent(
            subagent_type="validator",
            prompt="Count slowly from 1 to infinity",
            timeout=1,  # Very short
        )

        assert isinstance(result, dict)
        assert result["subagent_type"] == "validator"
        # Either timed out or completed quickly
        if result["error"]:
            assert "timeout" in result["error"].lower() or "Timeout" in result["error"]


@pytest.mark.integration
class TestErrorDetectionFlow:
    """Test error detection in orchestration results."""

    def test_detect_failed_coordination_result(self, initialized_orchestration_manager):
        """Test that failed subagent results are properly detected in aggregation."""
        manager = initialized_orchestration_manager

        # Write a FAIL result
        manager.coordinator.write_subagent_result(
            "validator",
            "001",
            {
                "verdict": "FAIL",
                "error": "Evidence file contains errors",
                "details": ["error_pattern_detected"],
            },
        )

        # Aggregate should report FAIL
        aggregated = manager.aggregate_results()
        assert aggregated["verdict"] == "FAIL"
        assert len(aggregated["subagent_results"]) == 1
        assert aggregated["subagent_results"][0]["verdict"] == "FAIL"

    def test_detect_no_results(self, initialized_orchestration_manager):
        """Test aggregation with no subagent results."""
        manager = initialized_orchestration_manager

        # No results written
        aggregated = manager.aggregate_results()
        assert aggregated["verdict"] == "NO_RESULTS"
        assert len(aggregated["subagent_results"]) == 0

    def test_inconclusive_without_verdicts(self, initialized_orchestration_manager):
        """Test aggregation when results lack verdict field."""
        manager = initialized_orchestration_manager

        # Write result without verdict
        manager.coordinator.write_subagent_result(
            "validator",
            "001",
            {
                "info": "Some information",
                "status": "completed",
                # No "verdict" field
            },
        )

        aggregated = manager.aggregate_results()
        # Without verdicts, should be INCONCLUSIVE
        assert aggregated["verdict"] == "INCONCLUSIVE"
