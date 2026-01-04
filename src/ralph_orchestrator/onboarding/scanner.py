"""ProjectScanner - Discovers all analyzable data sources for a project.

This module scans a project directory to find:
- Claude Code conversation history files
- CLAUDE.md instruction files
- MCP server configurations
- Project type from manifest files
"""

import hashlib
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ralph_orchestrator.onboarding.settings_loader import SettingsLoader

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """Enum representing different project types."""

    NODEJS = "nodejs"
    PYTHON = "python"
    RUST = "rust"
    GO = "go"
    EXPO = "expo"
    REACT = "react"
    FLUTTER = "flutter"
    UNKNOWN = "unknown"


class ProjectScanner:
    """Discovers all analyzable data sources for a project.

    Scans a project directory to find conversation history, instruction files,
    MCP configurations, and determines project type from manifest files.

    Attributes:
        project_path: Path to the project directory
        settings: SettingsLoader instance for loading settings
    """

    def __init__(
        self, project_path: Path | str, settings: Optional[SettingsLoader] = None
    ):
        """Initialize ProjectScanner with a project path.

        Args:
            project_path: Path to the project directory
            settings: Optional SettingsLoader instance. Created if not provided.
        """
        self.project_path = Path(project_path).resolve()
        self.settings = settings or SettingsLoader(self.project_path)

    def detect_project_type(self) -> ProjectType:
        """Determine project type from manifest files.

        Checks for various manifest files (package.json, pyproject.toml, etc.)
        and examines their contents to determine the project type.

        Returns:
            ProjectType enum indicating the detected project type.
        """
        # Check package.json first for Node.js/React/Expo projects
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text())
                deps = content.get("dependencies", {})
                dev_deps = content.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}

                # Check for Expo (takes precedence over React)
                if "expo" in all_deps:
                    return ProjectType.EXPO

                # Check for React
                if "react" in all_deps:
                    return ProjectType.REACT

                # Plain Node.js
                return ProjectType.NODEJS
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Failed to parse package.json: {e}")
                return ProjectType.NODEJS

        # Check for Python projects
        if (self.project_path / "pyproject.toml").exists():
            return ProjectType.PYTHON
        if (self.project_path / "setup.py").exists():
            return ProjectType.PYTHON

        # Check for Rust projects
        if (self.project_path / "Cargo.toml").exists():
            return ProjectType.RUST

        # Check for Go projects
        if (self.project_path / "go.mod").exists():
            return ProjectType.GO

        # Check for Flutter/Dart projects
        pubspec = self.project_path / "pubspec.yaml"
        if pubspec.exists():
            try:
                content = pubspec.read_text()
                if "flutter:" in content:
                    return ProjectType.FLUTTER
            except Exception as e:
                logger.debug(f"Failed to read pubspec.yaml: {e}")

        return ProjectType.UNKNOWN

    def get_project_hash(self) -> str:
        """Get the hash Claude Code uses for this project.

        Claude Code uses a hash of the project path to organize conversation
        history in ~/.claude/projects/[hash]/.

        Returns:
            String hash of the project path.
        """
        # Claude Code uses a hash of the absolute path
        path_bytes = str(self.project_path).encode("utf-8")
        return hashlib.sha256(path_bytes).hexdigest()[:16]

    def _get_claude_home(self) -> Path:
        """Get the Claude home directory.

        Returns:
            Path to ~/.claude directory.
        """
        return Path.home() / ".claude"

    def find_claude_history(self) -> List[Path]:
        """Find Claude Code conversation history files.

        Looks for JSONL files in ~/.claude/projects/[project-hash]/.

        Returns:
            List of paths to conversation JSONL files.
        """
        claude_home = self._get_claude_home()
        project_hash = self.get_project_hash()
        history_dir = claude_home / "projects" / project_hash

        if not history_dir.exists():
            logger.debug(f"No history directory at {history_dir}")
            return []

        jsonl_files = list(history_dir.glob("*.jsonl"))
        logger.debug(f"Found {len(jsonl_files)} JSONL files in {history_dir}")
        return jsonl_files

    def find_claude_md_files(self) -> List[Path]:
        """Find CLAUDE.md instruction files.

        Looks for:
        - [project]/CLAUDE.md
        - [project]/.claude/CLAUDE.md
        - [project]/.claude/rules/*.md

        Returns:
            List of paths to instruction files.
        """
        files = []

        # Check project root CLAUDE.md
        root_claude_md = self.project_path / "CLAUDE.md"
        if root_claude_md.exists():
            files.append(root_claude_md)

        # Check hidden .claude directory
        claude_dir = self.project_path / ".claude"
        if claude_dir.exists():
            # Check .claude/CLAUDE.md
            hidden_claude_md = claude_dir / "CLAUDE.md"
            if hidden_claude_md.exists():
                files.append(hidden_claude_md)

            # Check .claude/rules/*.md
            rules_dir = claude_dir / "rules"
            if rules_dir.exists():
                files.extend(rules_dir.glob("*.md"))

        return files

    def find_mcp_config(self) -> Dict[str, Dict[str, Any]]:
        """Get merged MCP server configurations.

        Delegates to SettingsLoader to get merged MCP configurations
        from user and project settings.

        Returns:
            Dictionary mapping server names to their configurations.
        """
        return self.settings.get_mcp_servers()
