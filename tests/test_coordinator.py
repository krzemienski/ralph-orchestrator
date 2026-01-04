#!/usr/bin/env python3
# ABOUTME: TDD tests for CoordinationManager - Phase O4 of orchestration architecture
# ABOUTME: Tests file-based coordination protocol for subagent communication

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest


class TestCoordinationManager:
    """Tests for CoordinationManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test coordination files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def coordinator(self, temp_dir):
        """Create CoordinationManager with temp base directory."""
        from ralph_orchestrator.orchestration.coordinator import CoordinationManager

        return CoordinationManager(base_dir=temp_dir)

    def test_coordinator_import(self):
        """Test that CoordinationManager can be imported."""
        from ralph_orchestrator.orchestration.coordinator import CoordinationManager

        assert CoordinationManager is not None

    def test_coordinator_creation(self, temp_dir):
        """Test CoordinationManager instantiation."""
        from ralph_orchestrator.orchestration.coordinator import CoordinationManager

        cm = CoordinationManager(base_dir=temp_dir)
        assert cm is not None
        assert cm.base_dir == temp_dir

    def test_init_coordination_creates_directory_structure(self, coordinator, temp_dir):
        """Test init_coordination() creates required directories."""
        coordinator.init_coordination()

        coordination_dir = temp_dir / ".agent" / "coordination"
        assert coordination_dir.exists()
        assert (coordination_dir / "subagent-results").exists()

    def test_init_coordination_idempotent(self, coordinator, temp_dir):
        """Test init_coordination() can be called multiple times safely."""
        coordinator.init_coordination()
        coordinator.init_coordination()

        coordination_dir = temp_dir / ".agent" / "coordination"
        assert coordination_dir.exists()

    def test_write_attempt_start_creates_json(self, coordinator, temp_dir):
        """Test write_attempt_start() creates current-attempt.json."""
        coordinator.init_coordination()
        coordinator.write_attempt_start(
            attempt_number=1, phase="test-phase", criteria=["Criterion 1", "Criterion 2"]
        )

        attempt_file = temp_dir / ".agent" / "coordination" / "current-attempt.json"
        assert attempt_file.exists()

        data = json.loads(attempt_file.read_text())
        assert data["attempt_number"] == 1
        assert data["phase"] == "test-phase"
        assert data["criteria"] == ["Criterion 1", "Criterion 2"]
        assert "started_at" in data

    def test_write_attempt_start_overwrites_previous(self, coordinator, temp_dir):
        """Test write_attempt_start() overwrites previous attempt file."""
        coordinator.init_coordination()
        coordinator.write_attempt_start(1, "phase-1", ["Old criterion"])
        coordinator.write_attempt_start(2, "phase-2", ["New criterion"])

        attempt_file = temp_dir / ".agent" / "coordination" / "current-attempt.json"
        data = json.loads(attempt_file.read_text())
        assert data["attempt_number"] == 2
        assert data["phase"] == "phase-2"

    def test_write_shared_context_creates_markdown(self, coordinator, temp_dir):
        """Test write_shared_context() creates shared-context.md."""
        coordinator.init_coordination()
        coordinator.write_shared_context(
            {"phase": "test", "criteria": ["Test criterion"], "priority": "high"}
        )

        context_file = temp_dir / ".agent" / "coordination" / "shared-context.md"
        assert context_file.exists()

        content = context_file.read_text()
        assert "phase" in content
        assert "test" in content
        assert "criteria" in content

    def test_write_shared_context_formats_nicely(self, coordinator, temp_dir):
        """Test write_shared_context() creates readable markdown."""
        coordinator.init_coordination()
        coordinator.write_shared_context(
            {"phase": "validation", "criteria": ["A", "B", "C"]}
        )

        context_file = temp_dir / ".agent" / "coordination" / "shared-context.md"
        content = context_file.read_text()

        # Should have a header
        assert "# Shared Context" in content or "## " in content

    def test_collect_results_empty_directory(self, coordinator, temp_dir):
        """Test collect_results() returns empty list for empty directory."""
        coordinator.init_coordination()

        results = coordinator.collect_results()
        assert results == []

    def test_collect_results_reads_json_files(self, coordinator, temp_dir):
        """Test collect_results() reads all subagent result files."""
        coordinator.init_coordination()

        results_dir = temp_dir / ".agent" / "coordination" / "subagent-results"

        # Create test result files
        validator_result = {"subagent": "validator", "verdict": "PASS"}
        (results_dir / "validator-001.json").write_text(json.dumps(validator_result))

        researcher_result = {"subagent": "researcher", "findings": ["Found pattern"]}
        (results_dir / "researcher-001.json").write_text(json.dumps(researcher_result))

        results = coordinator.collect_results()
        assert len(results) == 2

        # Should contain both results
        subagents = [r.get("subagent") for r in results]
        assert "validator" in subagents
        assert "researcher" in subagents

    def test_collect_results_ignores_non_json(self, coordinator, temp_dir):
        """Test collect_results() ignores non-JSON files."""
        coordinator.init_coordination()

        results_dir = temp_dir / ".agent" / "coordination" / "subagent-results"
        (results_dir / "readme.txt").write_text("Not JSON")
        (results_dir / "validator-001.json").write_text('{"subagent": "validator"}')

        results = coordinator.collect_results()
        assert len(results) == 1
        assert results[0]["subagent"] == "validator"

    def test_collect_results_handles_invalid_json(self, coordinator, temp_dir):
        """Test collect_results() handles malformed JSON gracefully."""
        coordinator.init_coordination()

        results_dir = temp_dir / ".agent" / "coordination" / "subagent-results"
        (results_dir / "bad.json").write_text("not valid json {")
        (results_dir / "good.json").write_text('{"subagent": "implementer"}')

        results = coordinator.collect_results()
        # Should get the valid one, skip the invalid
        assert len(results) == 1
        assert results[0]["subagent"] == "implementer"

    def test_append_to_journal_creates_file(self, coordinator, temp_dir):
        """Test append_to_journal() creates attempt-journal.md if missing."""
        coordinator.init_coordination()
        coordinator.append_to_journal("First entry", attempt=1)

        journal_file = temp_dir / ".agent" / "coordination" / "attempt-journal.md"
        assert journal_file.exists()
        assert "First entry" in journal_file.read_text()

    def test_append_to_journal_appends_entries(self, coordinator, temp_dir):
        """Test append_to_journal() appends multiple entries."""
        coordinator.init_coordination()
        coordinator.append_to_journal("Entry 1", attempt=1)
        coordinator.append_to_journal("Entry 2", attempt=1)
        coordinator.append_to_journal("Entry 3", attempt=2)

        journal_file = temp_dir / ".agent" / "coordination" / "attempt-journal.md"
        content = journal_file.read_text()

        assert "Entry 1" in content
        assert "Entry 2" in content
        assert "Entry 3" in content

    def test_append_to_journal_includes_timestamp(self, coordinator, temp_dir):
        """Test append_to_journal() includes timestamp in entries."""
        coordinator.init_coordination()
        coordinator.append_to_journal("Timed entry", attempt=1)

        journal_file = temp_dir / ".agent" / "coordination" / "attempt-journal.md"
        content = journal_file.read_text()

        # Should have some time indication (year or ISO format)
        assert "202" in content  # Year prefix for 2020s

    def test_write_subagent_result(self, coordinator, temp_dir):
        """Test write_subagent_result() creates result file."""
        coordinator.init_coordination()
        result = {"subagent": "validator", "verdict": "PASS", "evidence": ["test.txt"]}
        coordinator.write_subagent_result("validator", "001", result)

        result_file = (
            temp_dir / ".agent" / "coordination" / "subagent-results" / "validator-001.json"
        )
        assert result_file.exists()

        data = json.loads(result_file.read_text())
        assert data["subagent"] == "validator"
        assert data["verdict"] == "PASS"

    def test_get_shared_context(self, coordinator, temp_dir):
        """Test get_shared_context() reads previously written context."""
        coordinator.init_coordination()
        coordinator.write_shared_context({"key": "value", "items": [1, 2, 3]})

        context = coordinator.get_shared_context()
        assert context is not None
        # Should return the markdown content
        assert isinstance(context, str)
        assert "key" in context

    def test_get_shared_context_returns_none_if_missing(self, coordinator, temp_dir):
        """Test get_shared_context() returns None if file doesn't exist."""
        coordinator.init_coordination()

        context = coordinator.get_shared_context()
        assert context is None

    def test_get_current_attempt(self, coordinator, temp_dir):
        """Test get_current_attempt() returns attempt data."""
        coordinator.init_coordination()
        coordinator.write_attempt_start(5, "phase-five", ["Criterion"])

        attempt = coordinator.get_current_attempt()
        assert attempt is not None
        assert attempt["attempt_number"] == 5
        assert attempt["phase"] == "phase-five"

    def test_get_current_attempt_returns_none_if_missing(self, coordinator, temp_dir):
        """Test get_current_attempt() returns None if no attempt started."""
        coordinator.init_coordination()

        attempt = coordinator.get_current_attempt()
        assert attempt is None

    def test_clear_subagent_results(self, coordinator, temp_dir):
        """Test clear_subagent_results() removes all result files."""
        coordinator.init_coordination()

        results_dir = temp_dir / ".agent" / "coordination" / "subagent-results"
        (results_dir / "validator-001.json").write_text('{"test": true}')
        (results_dir / "researcher-001.json").write_text('{"test": true}')

        coordinator.clear_subagent_results()

        assert len(list(results_dir.glob("*.json"))) == 0


class TestCoordinationManagerDefaultDirectory:
    """Tests for CoordinationManager with default directory."""

    def test_default_base_dir_is_cwd(self):
        """Test CoordinationManager uses current working directory by default."""
        from ralph_orchestrator.orchestration.coordinator import CoordinationManager

        cm = CoordinationManager()
        # Should use current working directory
        assert cm.base_dir == Path.cwd()
