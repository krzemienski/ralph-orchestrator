#!/usr/bin/env python3
"""Integration tests for the ralph onboard CLI command.

Tests the end-to-end flow of the onboard command with various options.
Uses mocked components to avoid real API calls while validating CLI behavior.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestOnboardCLIBasic:
    """Basic CLI invocation tests."""

    def test_onboard_command_exists(self):
        """Test that the onboard command is registered in argparse."""
        from ralph_orchestrator.__main__ import main

        # Calling with --help should succeed and mention 'onboard'
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, 'argv', ['ralph', 'onboard', '--help']):
                main()

        # --help exits with code 0
        assert exc_info.value.code == 0

    def test_onboard_with_nonexistent_path(self, capsys):
        """Test error handling when project path doesn't exist."""
        from ralph_orchestrator.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, 'argv', ['ralph', 'onboard', '/nonexistent/path/xyz']):
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert 'does not exist' in captured.out.lower() or 'does not exist' in captured.err.lower()

    def test_onboard_with_file_instead_of_directory(self, tmp_path, capsys):
        """Test error handling when path is a file, not directory."""
        from ralph_orchestrator.__main__ import main

        # Create a file instead of directory
        test_file = tmp_path / "not_a_dir.txt"
        test_file.write_text("content")

        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, 'argv', ['ralph', 'onboard', str(test_file)]):
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert 'not a directory' in captured.out.lower() or 'not a directory' in captured.err.lower()


class TestOnboardStaticMode:
    """Tests for --static mode (no API calls)."""

    def test_onboard_static_minimal_project(self, tmp_path, capsys):
        """Test static mode on minimal project without Claude history."""
        from ralph_orchestrator.__main__ import main

        # Create minimal Python project
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--dry-run']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # --dry-run should exit with 0
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert 'ralph.yml' in captured.out.lower()

    def test_onboard_static_generates_files(self, tmp_path):
        """Test that static mode actually creates configuration files."""
        from ralph_orchestrator.__main__ import main

        # Create a basic project structure
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "test-node-project",
            "version": "1.0.0",
            "dependencies": {"express": "^4.18.0"}
        }))

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static']):
            try:
                main()
            except SystemExit:
                pass  # Expected

        # Check files were created
        assert (tmp_path / "ralph.yml").exists()
        assert (tmp_path / "RALPH_INSTRUCTIONS.md").exists()
        assert (tmp_path / "PROMPT.md").exists()

        # Check ralph.yml has expected content
        ralph_yml = (tmp_path / "ralph.yml").read_text()
        assert "agent:" in ralph_yml
        assert "prompt_file:" in ralph_yml

    def test_onboard_static_detects_project_type(self, tmp_path, capsys):
        """Test that static mode correctly detects project types."""
        from ralph_orchestrator.__main__ import main

        # Create Python project
        (tmp_path / "setup.py").write_text("from setuptools import setup; setup()")

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--analyze-only']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # Should detect as Python
        assert 'python' in captured.out.lower()


class TestOnboardAnalyzeOnlyMode:
    """Tests for --analyze-only mode."""

    def test_analyze_only_does_not_write_files(self, tmp_path, capsys):
        """Test that --analyze-only shows output but doesn't write files."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "Cargo.toml").write_text("""
[package]
name = "test-rust-project"
version = "0.1.0"
""")

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--analyze-only']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

        # Files should NOT be created
        assert not (tmp_path / "ralph.yml").exists()
        assert not (tmp_path / "RALPH_INSTRUCTIONS.md").exists()

        # But output should show preview
        captured = capsys.readouterr()
        assert 'ralph.yml preview' in captured.out.lower()

    def test_analyze_only_shows_instructions_preview(self, tmp_path, capsys):
        """Test that --analyze-only includes RALPH_INSTRUCTIONS.md preview."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "go.mod").write_text("module test/project\ngo 1.21\n")

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--analyze-only']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert 'ralph_instructions.md preview' in captured.out.lower()


class TestOnboardDryRunMode:
    """Tests for --dry-run mode."""

    def test_dry_run_lists_files_without_creating(self, tmp_path, capsys):
        """Test that --dry-run shows files that would be created."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "package.json").write_text('{"name": "test"}')

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--dry-run']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

        # Files should NOT be created
        assert not (tmp_path / "ralph.yml").exists()

        # But output should list what would be created
        captured = capsys.readouterr()
        assert 'ralph.yml' in captured.out
        assert 'RALPH_INSTRUCTIONS.md' in captured.out


class TestOnboardOutputDirectory:
    """Tests for -o/--output-dir option."""

    def test_output_dir_creates_files_in_specified_location(self, tmp_path):
        """Test that -o/--output-dir puts files in the right place."""
        from ralph_orchestrator.__main__ import main

        project_dir = tmp_path / "project"
        output_dir = tmp_path / "output"
        project_dir.mkdir()
        output_dir.mkdir()

        (project_dir / "pyproject.toml").write_text('[project]\nname = "test"\n')

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(project_dir), '--static', '-o', str(output_dir)]):
            try:
                main()
            except SystemExit:
                pass

        # Files should be in output_dir, not project_dir
        assert (output_dir / "ralph.yml").exists()
        assert not (project_dir / "ralph.yml").exists()


class TestOnboardSettingsInheritance:
    """Tests for --inherit-settings and --no-inherit options."""

    def test_no_inherit_skips_user_settings(self, tmp_path, capsys):
        """Test that --no-inherit doesn't load user settings."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "package.json").write_text('{"name": "test"}')

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--no-inherit', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # Should NOT mention inheriting settings
        assert 'inheriting user settings' not in captured.out.lower()

    def test_inherit_settings_logs_message(self, tmp_path, capsys):
        """Test that inheriting settings is logged by default."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "package.json").write_text('{"name": "test"}')

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # Default is to inherit, so should mention it
        assert 'inheriting' in captured.out.lower() or 'settings' in captured.out.lower()


class TestOnboardAgentMode:
    """Tests for agent-assisted analysis (default mode)."""

    def test_agent_mode_falls_back_on_error(self, tmp_path, capsys):
        """Test that agent mode falls back to static when agent fails."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.onboarding.agent_analyzer import AgentAnalyzer

        (tmp_path / "package.json").write_text('{"name": "test"}')

        # Mock the agent analyzer to fail
        with patch.object(AgentAnalyzer, 'sync_analyze', side_effect=Exception("Mock API error")):
            with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--dry-run']):
                with pytest.raises(SystemExit):
                    main()

        captured = capsys.readouterr()
        # Should mention fallback
        assert 'falling back' in captured.out.lower() or 'static' in captured.out.lower()

    def test_agent_mode_with_mocked_success(self, tmp_path, capsys):
        """Test agent mode with successful mock response."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.onboarding.agent_analyzer import AgentAnalyzer, AnalysisResult

        (tmp_path / "package.json").write_text('{"name": "test-project"}')

        # Create a mock successful result
        mock_result = AnalysisResult(
            project_type="javascript",
            frameworks=["express", "jest"],
            common_tools={"Edit": 0.95, "Bash": 0.90, "Read": 0.85},
            workflows=[["Edit", "Bash", "Bash"]],
            recommended_config={"max_iterations": 75}
        )

        with patch.object(AgentAnalyzer, 'sync_analyze', return_value=mock_result):
            with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--dry-run']):
                with pytest.raises(SystemExit):
                    main()

        captured = capsys.readouterr()
        assert 'agent analysis completed' in captured.out.lower()


class TestOnboardWithClaudeHistory:
    """Tests for projects with Claude Code conversation history."""

    def test_detects_claude_history_files(self, tmp_path, capsys, monkeypatch):
        """Test detection of Claude history in ~/.claude/projects/."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.onboarding.scanner import ProjectScanner

        (tmp_path / "package.json").write_text('{"name": "test"}')

        # Mock the history detection to return some files
        def mock_find_history(self):
            return [Path("/mock/history/file1.jsonl")]

        with patch.object(ProjectScanner, 'find_claude_history', mock_find_history):
            with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--dry-run']):
                with pytest.raises(SystemExit):
                    main()

        captured = capsys.readouterr()
        assert 'conversation file' in captured.out.lower() or 'history' in captured.out.lower()


class TestOnboardMergeMode:
    """Tests for --merge mode."""

    def test_merge_mode_warns_about_incomplete_impl(self, tmp_path, capsys):
        """Test that merge mode mentions it's not fully implemented."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "package.json").write_text('{"name": "test"}')

        # Create existing ralph.yml
        (tmp_path / "ralph.yml").write_text("agent: claude\nmax_iterations: 50\n")

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--merge']):
            try:
                main()
            except SystemExit:
                pass

        captured = capsys.readouterr()
        # Should mention merge or warning about incomplete implementation
        assert 'merge' in captured.out.lower() or 'overwriting' in captured.out.lower()


class TestOnboardMultipleProjectTypes:
    """Tests for different project types."""

    @pytest.mark.parametrize("manifest_file,content,expected_type", [
        ("package.json", '{"name": "test", "dependencies": {"expo": "^51.0.0"}}', "expo"),
        ("package.json", '{"name": "test", "dependencies": {"react": "^18.0.0"}}', "react"),
        ("pyproject.toml", '[project]\nname = "test"\n', "python"),
        ("Cargo.toml", '[package]\nname = "test"\nversion = "0.1.0"\n', "rust"),
        ("go.mod", 'module test\ngo 1.21\n', "go"),
        ("pubspec.yaml", 'name: test\nversion: 1.0.0\nflutter:\n  sdk: flutter\n', "flutter"),
    ])
    def test_detects_various_project_types(self, tmp_path, capsys, manifest_file, content, expected_type):
        """Test detection of various project types from manifest files."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / manifest_file).write_text(content)

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert expected_type.lower() in captured.out.lower()


class TestOnboardSuccessCompletion:
    """Tests for successful onboarding completion."""

    def test_success_message_and_next_steps(self, tmp_path, capsys):
        """Test that successful onboarding shows completion message and next steps."""
        from ralph_orchestrator.__main__ import main

        (tmp_path / "package.json").write_text('{"name": "test"}')

        with patch.object(sys, 'argv', ['ralph', 'onboard', str(tmp_path), '--static']):
            try:
                main()
            except SystemExit:
                pass

        captured = capsys.readouterr()
        assert 'complete' in captured.out.lower()
        assert 'ralph run' in captured.out.lower() or 'next steps' in captured.out.lower()
