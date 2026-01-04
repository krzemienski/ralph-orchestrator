#!/usr/bin/env python3
# ABOUTME: Tests for Phase O5 - OrchestrationManager integration
# ABOUTME: TDD tests for subagent prompt generation and orchestration

import json
import tempfile
from pathlib import Path

import pytest


class TestEnableOrchestrationField:
    """Test enable_orchestration field in RalphConfig."""

    def test_enable_orchestration_default_false(self):
        """enable_orchestration should default to False."""
        from ralph_orchestrator.main import RalphConfig

        config = RalphConfig()
        assert config.enable_orchestration is False

    def test_enable_orchestration_can_be_set_true(self):
        """enable_orchestration can be set to True."""
        from ralph_orchestrator.main import RalphConfig

        config = RalphConfig(enable_orchestration=True)
        assert config.enable_orchestration is True

    def test_enable_orchestration_from_yaml(self, tmp_path):
        """enable_orchestration should be loadable from YAML config."""
        from ralph_orchestrator.main import RalphConfig

        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
enable_orchestration: true
prompt_file: test.md
"""
        )

        config = RalphConfig.from_yaml(str(config_file))
        assert config.enable_orchestration is True


class TestOrchestrationManagerClass:
    """Test OrchestrationManager class existence and basic structure."""

    def test_orchestration_manager_exists(self):
        """OrchestrationManager class should exist in orchestration module."""
        from ralph_orchestrator.orchestration import OrchestrationManager

        assert OrchestrationManager is not None

    def test_orchestration_manager_init_with_config(self):
        """OrchestrationManager should accept RalphConfig in constructor."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        assert manager.config == config

    def test_orchestration_manager_has_coordinator(self):
        """OrchestrationManager should have a CoordinationManager instance."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import (
            CoordinationManager,
            OrchestrationManager,
        )

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        assert hasattr(manager, "coordinator")
        assert isinstance(manager.coordinator, CoordinationManager)


class TestGenerateSubagentPrompt:
    """Test generate_subagent_prompt() method."""

    def test_generate_subagent_prompt_exists(self):
        """generate_subagent_prompt method should exist."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        assert hasattr(manager, "generate_subagent_prompt")
        assert callable(manager.generate_subagent_prompt)

    def test_generate_validator_prompt(self):
        """Generate prompt for validator subagent."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="Test Phase",
            criteria=["Criterion 1", "Criterion 2"],
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "VALIDATOR" in prompt

    def test_generate_prompt_contains_skill_instructions(self):
        """Generated prompt should contain skill loading instructions."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="Test Phase",
            criteria=["Test criterion"],
        )

        # Should contain skill loading instruction (Skill tool syntax)
        assert "Skill(" in prompt or "skill" in prompt.lower()

    def test_generate_prompt_contains_mcp_list(self):
        """Generated prompt should contain MCP tool list."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="Test Phase",
            criteria=["Test criterion"],
        )

        # Should contain MCP section
        assert "MCP" in prompt or "mcp" in prompt.lower()

    def test_generate_prompt_contains_coordination_paths(self):
        """Generated prompt should contain coordination file paths."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="Test Phase",
            criteria=["Test criterion"],
        )

        assert ".agent/coordination" in prompt

    def test_generate_prompt_contains_task_description(self):
        """Generated prompt should contain the task/criteria."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        prompt = manager.generate_subagent_prompt(
            subagent_type="validator",
            phase="Test Phase",
            criteria=["Test criterion ABC"],
        )

        assert "Test criterion ABC" in prompt

    def test_generate_prompt_for_all_subagent_types(self):
        """Can generate prompts for all 4 subagent types."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        for subagent_type in ["validator", "researcher", "implementer", "analyst"]:
            prompt = manager.generate_subagent_prompt(
                subagent_type=subagent_type,
                phase="Test Phase",
                criteria=["Test criterion"],
            )

            assert isinstance(prompt, str)
            assert len(prompt) > 100
            assert subagent_type.upper() in prompt


class TestAggregateResults:
    """Test aggregate_results() method."""

    def test_aggregate_results_exists(self):
        """aggregate_results method should exist."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        config = RalphConfig(enable_orchestration=True)
        manager = OrchestrationManager(config)

        assert hasattr(manager, "aggregate_results")
        assert callable(manager.aggregate_results)

    def test_aggregate_results_returns_dict(self):
        """aggregate_results should return a dictionary."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = RalphConfig(enable_orchestration=True)
            manager = OrchestrationManager(config, base_dir=Path(tmp_dir))
            manager.coordinator.init_coordination()

            result = manager.aggregate_results()
            assert isinstance(result, dict)

    def test_aggregate_results_includes_verdict(self):
        """Aggregated results should include an overall verdict."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = RalphConfig(enable_orchestration=True)
            manager = OrchestrationManager(config, base_dir=Path(tmp_dir))
            manager.coordinator.init_coordination()

            # Write a PASS result
            manager.coordinator.write_subagent_result(
                "validator", "001", {"verdict": "PASS"}
            )

            result = manager.aggregate_results()
            assert "verdict" in result

    def test_aggregate_results_pass_when_all_pass(self):
        """Verdict should be PASS when all subagents pass."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = RalphConfig(enable_orchestration=True)
            manager = OrchestrationManager(config, base_dir=Path(tmp_dir))
            manager.coordinator.init_coordination()

            # Write multiple PASS results
            manager.coordinator.write_subagent_result(
                "validator", "001", {"verdict": "PASS"}
            )
            manager.coordinator.write_subagent_result(
                "researcher", "001", {"verdict": "PASS"}
            )

            result = manager.aggregate_results()
            assert result["verdict"] == "PASS"

    def test_aggregate_results_fail_when_any_fail(self):
        """Verdict should be FAIL when any subagent fails."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = RalphConfig(enable_orchestration=True)
            manager = OrchestrationManager(config, base_dir=Path(tmp_dir))
            manager.coordinator.init_coordination()

            # Write mixed results
            manager.coordinator.write_subagent_result(
                "validator", "001", {"verdict": "PASS"}
            )
            manager.coordinator.write_subagent_result(
                "researcher", "001", {"verdict": "FAIL"}
            )

            result = manager.aggregate_results()
            assert result["verdict"] == "FAIL"

    def test_aggregate_results_includes_subagent_results(self):
        """Aggregated results should include all subagent results."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = RalphConfig(enable_orchestration=True)
            manager = OrchestrationManager(config, base_dir=Path(tmp_dir))
            manager.coordinator.init_coordination()

            # Write results
            manager.coordinator.write_subagent_result(
                "validator", "001", {"subagent": "validator", "verdict": "PASS"}
            )

            result = manager.aggregate_results()
            assert "subagent_results" in result
            assert len(result["subagent_results"]) == 1


class TestOrchestrationManagerExport:
    """Test OrchestrationManager is properly exported."""

    def test_orchestration_manager_in_package_init(self):
        """OrchestrationManager should be exported from orchestration package."""
        from ralph_orchestrator import orchestration

        assert hasattr(orchestration, "OrchestrationManager")

    def test_orchestration_manager_in_all(self):
        """OrchestrationManager should be in __all__ list."""
        from ralph_orchestrator.orchestration import __all__

        assert "OrchestrationManager" in __all__


class TestIntegrationScenario:
    """Integration test for full orchestration workflow."""

    def test_full_orchestration_workflow(self):
        """Test complete orchestration workflow with mock subagents."""
        from ralph_orchestrator.main import RalphConfig
        from ralph_orchestrator.orchestration import OrchestrationManager

        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. Create config with orchestration enabled
            config = RalphConfig(enable_orchestration=True)

            # 2. Create OrchestrationManager
            manager = OrchestrationManager(config, base_dir=Path(tmp_dir))

            # 3. Initialize coordination
            manager.coordinator.init_coordination()

            # 4. Generate prompts for subagents
            validator_prompt = manager.generate_subagent_prompt(
                subagent_type="validator",
                phase="O5 Integration",
                criteria=["enable_orchestration field exists", "Tests pass"],
            )

            # 5. Verify prompt is valid
            assert "VALIDATOR" in validator_prompt
            assert "enable_orchestration" in validator_prompt

            # 6. Simulate subagent writing results
            manager.coordinator.write_subagent_result(
                "validator",
                "001",
                {
                    "subagent": "validator",
                    "verdict": "PASS",
                    "criteria_validated": [
                        "enable_orchestration field exists",
                        "Tests pass",
                    ],
                },
            )

            # 7. Aggregate results
            final = manager.aggregate_results()

            # 8. Verify final verdict
            assert final["verdict"] == "PASS"
            assert len(final["subagent_results"]) == 1
