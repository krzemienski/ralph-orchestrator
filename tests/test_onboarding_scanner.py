"""Tests for ProjectScanner - discovers all analyzable data sources for a project.

Following TDD: Writing tests FIRST, then implementing to make them pass.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from enum import Enum

from ralph_orchestrator.onboarding.scanner import ProjectScanner, ProjectType
from ralph_orchestrator.onboarding.settings_loader import SettingsLoader


class TestProjectScannerInit:
    """Tests for ProjectScanner initialization."""

    def test_init_with_project_path(self, tmp_path: Path):
        """ProjectScanner initializes with project path and settings loader."""
        settings = SettingsLoader(tmp_path)
        scanner = ProjectScanner(tmp_path, settings)
        assert scanner.project_path == tmp_path
        assert scanner.settings is settings

    def test_init_creates_settings_loader_if_not_provided(self, tmp_path: Path):
        """ProjectScanner creates SettingsLoader if not provided."""
        scanner = ProjectScanner(tmp_path)
        assert scanner.project_path == tmp_path
        assert isinstance(scanner.settings, SettingsLoader)


class TestDetectProjectType:
    """Tests for detecting project type from manifest files."""

    def test_detects_nodejs_from_package_json(self, tmp_path: Path):
        """Detects Node.js project from package.json."""
        (tmp_path / "package.json").write_text('{"name": "my-app"}')

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.NODEJS

    def test_detects_expo_from_package_json(self, tmp_path: Path):
        """Detects Expo project from package.json with expo dependency."""
        package = {"name": "my-app", "dependencies": {"expo": "~49.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(package))

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.EXPO

    def test_detects_react_from_package_json(self, tmp_path: Path):
        """Detects React project from package.json with react dependency."""
        package = {"name": "my-app", "dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(package))

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.REACT

    def test_detects_python_from_pyproject_toml(self, tmp_path: Path):
        """Detects Python project from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-pkg"')

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.PYTHON

    def test_detects_python_from_setup_py(self, tmp_path: Path):
        """Detects Python project from setup.py."""
        (tmp_path / "setup.py").write_text('from setuptools import setup')

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.PYTHON

    def test_detects_rust_from_cargo_toml(self, tmp_path: Path):
        """Detects Rust project from Cargo.toml."""
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "my-crate"')

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.RUST

    def test_detects_go_from_go_mod(self, tmp_path: Path):
        """Detects Go project from go.mod."""
        (tmp_path / "go.mod").write_text("module github.com/user/repo")

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.GO

    def test_detects_flutter_from_pubspec_yaml(self, tmp_path: Path):
        """Detects Flutter project from pubspec.yaml with flutter dependency."""
        pubspec = "name: my_app\ndependencies:\n  flutter:\n    sdk: flutter"
        (tmp_path / "pubspec.yaml").write_text(pubspec)

        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.FLUTTER

    def test_returns_unknown_for_no_manifest(self, tmp_path: Path):
        """Returns UNKNOWN when no manifest files found."""
        scanner = ProjectScanner(tmp_path)
        project_type = scanner.detect_project_type()

        assert project_type == ProjectType.UNKNOWN


class TestFindClaudeHistory:
    """Tests for finding Claude Code conversation history files."""

    def test_finds_history_in_claude_projects(self, tmp_path: Path):
        """Finds JSONL files in ~/.claude/projects/[hash]/."""
        # Create mock Claude projects directory with project hash
        claude_projects = tmp_path / ".claude" / "projects"
        project_hash = "abc123"
        project_dir = claude_projects / project_hash
        project_dir.mkdir(parents=True)

        # Create some conversation files
        (project_dir / "chat-001.jsonl").write_text('{"type": "user"}')
        (project_dir / "chat-002.jsonl").write_text('{"type": "user"}')

        scanner = ProjectScanner(tmp_path)
        with patch.object(scanner, "_get_claude_home", return_value=tmp_path / ".claude"):
            with patch.object(scanner, "get_project_hash", return_value=project_hash):
                history_files = scanner.find_claude_history()

        assert len(history_files) == 2
        assert all(f.suffix == ".jsonl" for f in history_files)

    def test_returns_empty_list_when_no_history(self, tmp_path: Path):
        """Returns empty list when no history directory exists."""
        scanner = ProjectScanner(tmp_path)
        with patch.object(scanner, "_get_claude_home", return_value=tmp_path / ".claude"):
            history_files = scanner.find_claude_history()

        assert history_files == []


class TestGetProjectHash:
    """Tests for computing the project hash Claude Code uses."""

    def test_computes_consistent_hash(self, tmp_path: Path):
        """Computes consistent hash for same project path."""
        scanner = ProjectScanner(tmp_path)

        hash1 = scanner.get_project_hash()
        hash2 = scanner.get_project_hash()

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0

    def test_different_paths_get_different_hashes(self, tmp_path: Path):
        """Different project paths get different hashes."""
        dir1 = tmp_path / "project1"
        dir2 = tmp_path / "project2"
        dir1.mkdir()
        dir2.mkdir()

        scanner1 = ProjectScanner(dir1)
        scanner2 = ProjectScanner(dir2)

        assert scanner1.get_project_hash() != scanner2.get_project_hash()


class TestFindClaudeMdFiles:
    """Tests for finding CLAUDE.md instruction files."""

    def test_finds_root_claude_md(self, tmp_path: Path):
        """Finds CLAUDE.md at project root."""
        (tmp_path / "CLAUDE.md").write_text("# Instructions")

        scanner = ProjectScanner(tmp_path)
        files = scanner.find_claude_md_files()

        assert len(files) == 1
        assert files[0].name == "CLAUDE.md"

    def test_finds_hidden_claude_md(self, tmp_path: Path):
        """Finds .claude/CLAUDE.md."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "CLAUDE.md").write_text("# Hidden instructions")

        scanner = ProjectScanner(tmp_path)
        files = scanner.find_claude_md_files()

        assert len(files) == 1
        assert ".claude" in str(files[0])

    def test_finds_rule_files(self, tmp_path: Path):
        """Finds .claude/rules/*.md files."""
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "testing.md").write_text("# Testing rules")
        (rules_dir / "styling.md").write_text("# Style rules")

        scanner = ProjectScanner(tmp_path)
        files = scanner.find_claude_md_files()

        assert len(files) == 2
        names = {f.name for f in files}
        assert "testing.md" in names
        assert "styling.md" in names

    def test_returns_empty_when_no_instructions(self, tmp_path: Path):
        """Returns empty list when no instruction files exist."""
        scanner = ProjectScanner(tmp_path)
        files = scanner.find_claude_md_files()

        assert files == []


class TestFindMCPConfig:
    """Tests for finding MCP configuration (delegates to SettingsLoader)."""

    def test_delegates_to_settings_loader(self, tmp_path: Path):
        """Delegates MCP config loading to SettingsLoader."""
        settings = MagicMock(spec=SettingsLoader)
        expected_servers = {"github": {"command": "github-mcp"}}
        settings.get_mcp_servers.return_value = expected_servers

        scanner = ProjectScanner(tmp_path, settings)
        result = scanner.find_mcp_config()

        settings.get_mcp_servers.assert_called_once()
        assert result == expected_servers


class TestProjectTypeEnum:
    """Tests for ProjectType enum values."""

    def test_has_expected_project_types(self):
        """ProjectType enum has all expected types."""
        assert hasattr(ProjectType, "NODEJS")
        assert hasattr(ProjectType, "PYTHON")
        assert hasattr(ProjectType, "RUST")
        assert hasattr(ProjectType, "GO")
        assert hasattr(ProjectType, "EXPO")
        assert hasattr(ProjectType, "REACT")
        assert hasattr(ProjectType, "FLUTTER")
        assert hasattr(ProjectType, "UNKNOWN")
