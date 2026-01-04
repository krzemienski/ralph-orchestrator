#!/usr/bin/env python3
# ABOUTME: Tests for skill and MCP discovery in Ralph orchestrator
# ABOUTME: Tests discover_skills(), SkillInfo, and get_skills_for_subagent()

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os


class TestSkillInfo:
    """Test the SkillInfo dataclass."""

    def test_skill_info_creation(self):
        """SkillInfo can be created with required fields."""
        from ralph_orchestrator.orchestration.discovery import SkillInfo

        info = SkillInfo(
            name="test-skill",
            path=Path("/path/to/skill"),
            description="A test skill",
            subagent_types=["validator", "implementer"],
        )
        assert info.name == "test-skill"
        assert info.path == Path("/path/to/skill")
        assert info.description == "A test skill"
        assert info.subagent_types == ["validator", "implementer"]

    def test_skill_info_default_subagent_types(self):
        """SkillInfo defaults to empty subagent_types list."""
        from ralph_orchestrator.orchestration.discovery import SkillInfo

        info = SkillInfo(
            name="test-skill",
            path=Path("/path/to/skill"),
            description="A test skill",
        )
        assert info.subagent_types == []


class TestDiscoverSkills:
    """Test the discover_skills() function."""

    def test_discover_skills_returns_dict(self):
        """discover_skills() returns a dict."""
        from ralph_orchestrator.orchestration.discovery import discover_skills

        result = discover_skills()
        assert isinstance(result, dict)

    def test_discover_skills_finds_skills_in_directory(self):
        """discover_skills() finds skills with SKILL.md files."""
        from ralph_orchestrator.orchestration.discovery import (
            discover_skills,
            SkillInfo,
        )

        # Create a temporary directory with skill structure
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: A test skill for testing
---

# Test Skill
"""
            )

            result = discover_skills(skills_dir=Path(tmpdir))

            assert "test-skill" in result
            assert isinstance(result["test-skill"], SkillInfo)
            assert result["test-skill"].description == "A test skill for testing"

    def test_discover_skills_parses_yaml_frontmatter(self):
        """discover_skills() correctly parses YAML frontmatter from SKILL.md."""
        from ralph_orchestrator.orchestration.discovery import discover_skills

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: my-skill
description: My special skill description
---

# My Skill Content
"""
            )

            result = discover_skills(skills_dir=Path(tmpdir))

            assert result["my-skill"].name == "my-skill"
            assert result["my-skill"].description == "My special skill description"

    def test_discover_skills_handles_missing_directory(self):
        """discover_skills() returns empty dict for missing directory."""
        from ralph_orchestrator.orchestration.discovery import discover_skills

        result = discover_skills(skills_dir=Path("/nonexistent/path"))
        assert result == {}

    def test_discover_skills_skips_invalid_skill_files(self):
        """discover_skills() skips skills without valid SKILL.md."""
        from ralph_orchestrator.orchestration.discovery import discover_skills

        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid skill
            valid_dir = Path(tmpdir) / "valid-skill"
            valid_dir.mkdir()
            (valid_dir / "SKILL.md").write_text(
                """---
name: valid-skill
description: Valid skill
---
"""
            )

            # Invalid skill (no frontmatter)
            invalid_dir = Path(tmpdir) / "invalid-skill"
            invalid_dir.mkdir()
            (invalid_dir / "SKILL.md").write_text("# No frontmatter here")

            # Not a skill (just a regular directory)
            not_skill_dir = Path(tmpdir) / "not-a-skill"
            not_skill_dir.mkdir()

            result = discover_skills(skills_dir=Path(tmpdir))

            assert "valid-skill" in result
            assert "invalid-skill" not in result
            assert "not-a-skill" not in result


class TestGetSkillsForSubagent:
    """Test the get_skills_for_subagent() function."""

    def test_get_skills_for_subagent_returns_dict(self):
        """get_skills_for_subagent() returns a dict."""
        from ralph_orchestrator.orchestration.discovery import get_skills_for_subagent

        result = get_skills_for_subagent("validator")
        assert isinstance(result, dict)

    def test_get_skills_for_subagent_filters_by_type(self):
        """get_skills_for_subagent() filters skills matching the subagent type."""
        from ralph_orchestrator.orchestration.discovery import (
            get_skills_for_subagent,
            SkillInfo,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Skill for validator
            validator_dir = Path(tmpdir) / "validator-skill"
            validator_dir.mkdir()
            (validator_dir / "SKILL.md").write_text(
                """---
name: validator-skill
description: For validators
subagent_types:
  - validator
---
"""
            )

            # Skill for implementer
            impl_dir = Path(tmpdir) / "implementer-skill"
            impl_dir.mkdir()
            (impl_dir / "SKILL.md").write_text(
                """---
name: implementer-skill
description: For implementers
subagent_types:
  - implementer
---
"""
            )

            result = get_skills_for_subagent("validator", skills_dir=Path(tmpdir))

            assert "validator-skill" in result
            assert "implementer-skill" not in result

    def test_get_skills_for_subagent_includes_shared_skills(self):
        """get_skills_for_subagent() includes skills available to multiple types."""
        from ralph_orchestrator.orchestration.discovery import get_skills_for_subagent

        with tempfile.TemporaryDirectory() as tmpdir:
            # Skill for multiple subagents
            shared_dir = Path(tmpdir) / "shared-skill"
            shared_dir.mkdir()
            (shared_dir / "SKILL.md").write_text(
                """---
name: shared-skill
description: Shared across types
subagent_types:
  - validator
  - implementer
  - analyst
---
"""
            )

            validator_result = get_skills_for_subagent(
                "validator", skills_dir=Path(tmpdir)
            )
            implementer_result = get_skills_for_subagent(
                "implementer", skills_dir=Path(tmpdir)
            )
            researcher_result = get_skills_for_subagent(
                "researcher", skills_dir=Path(tmpdir)
            )

            assert "shared-skill" in validator_result
            assert "shared-skill" in implementer_result
            assert "shared-skill" not in researcher_result

    def test_get_skills_for_subagent_returns_all_when_no_types_specified(self):
        """Skills without subagent_types are available to all subagents."""
        from ralph_orchestrator.orchestration.discovery import get_skills_for_subagent

        with tempfile.TemporaryDirectory() as tmpdir:
            # Skill with no subagent_types (universal)
            universal_dir = Path(tmpdir) / "universal-skill"
            universal_dir.mkdir()
            (universal_dir / "SKILL.md").write_text(
                """---
name: universal-skill
description: Universal skill
---
"""
            )

            for subagent_type in ["validator", "researcher", "implementer", "analyst"]:
                result = get_skills_for_subagent(subagent_type, skills_dir=Path(tmpdir))
                assert "universal-skill" in result


class TestSkillMapping:
    """Test skill-to-subagent mapping from profile configuration."""

    def test_map_skills_from_profiles(self):
        """Skills can be mapped from profile required_tools."""
        from ralph_orchestrator.orchestration.config import SUBAGENT_PROFILES
        from ralph_orchestrator.orchestration.discovery import (
            get_required_skills_for_subagent,
        )

        # Validator requires playwright-skill and systematic-debugging
        required = get_required_skills_for_subagent("validator")
        assert "playwright-skill" in required
        assert "systematic-debugging" in required

    def test_get_required_skills_returns_list(self):
        """get_required_skills_for_subagent() returns a list."""
        from ralph_orchestrator.orchestration.discovery import (
            get_required_skills_for_subagent,
        )

        result = get_required_skills_for_subagent("implementer")
        assert isinstance(result, list)
        assert "test-driven-development" in result

    def test_get_required_skills_unknown_subagent(self):
        """get_required_skills_for_subagent() returns empty list for unknown type."""
        from ralph_orchestrator.orchestration.discovery import (
            get_required_skills_for_subagent,
        )

        result = get_required_skills_for_subagent("unknown-type")
        assert result == []
