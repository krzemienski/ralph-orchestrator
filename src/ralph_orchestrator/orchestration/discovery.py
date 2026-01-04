#!/usr/bin/env python3
# ABOUTME: Skill and MCP discovery for Ralph orchestrator subagents
# ABOUTME: Scans skill directories and maps skills to subagent types

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .config import SUBAGENT_PROFILES


@dataclass
class SkillInfo:
    """Information about a discovered skill.

    Attributes:
        name: Skill name (from SKILL.md frontmatter)
        path: Path to the skill directory
        description: Human-readable description
        subagent_types: List of subagent types this skill is relevant to
    """

    name: str
    path: Path
    description: str
    subagent_types: List[str] = field(default_factory=list)


# Default skills directory
DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _parse_skill_frontmatter(content: str) -> Optional[Dict]:
    """Parse YAML frontmatter from SKILL.md content.

    Args:
        content: Full content of SKILL.md file

    Returns:
        Parsed frontmatter dict or None if invalid
    """
    # Match YAML frontmatter between --- markers
    pattern = r"^---\s*\n(.*?)\n---"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def discover_skills(
    skills_dir: Optional[Path] = None,
) -> Dict[str, SkillInfo]:
    """Discover available skills from the skills directory.

    Scans the skills directory for subdirectories containing SKILL.md files.
    Parses each SKILL.md to extract name, description, and subagent mappings.

    Args:
        skills_dir: Path to skills directory (defaults to ~/.claude/skills/)

    Returns:
        Dict mapping skill names to SkillInfo objects
    """
    if skills_dir is None:
        skills_dir = DEFAULT_SKILLS_DIR

    if not skills_dir.exists():
        return {}

    skills: Dict[str, SkillInfo] = {}

    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text()
            frontmatter = _parse_skill_frontmatter(content)

            if not frontmatter:
                continue

            # Extract required fields
            name = frontmatter.get("name")
            description = frontmatter.get("description", "")

            if not name:
                continue

            # Extract optional subagent_types
            subagent_types = frontmatter.get("subagent_types", [])
            if isinstance(subagent_types, str):
                subagent_types = [subagent_types]

            skills[name] = SkillInfo(
                name=name,
                path=skill_path,
                description=description,
                subagent_types=subagent_types,
            )
        except Exception:
            # Skip skills with errors
            continue

    return skills


def get_skills_for_subagent(
    subagent_type: str,
    skills_dir: Optional[Path] = None,
) -> Dict[str, SkillInfo]:
    """Get skills relevant for a specific subagent type.

    Filters discovered skills to those that:
    1. Have the subagent_type in their subagent_types list, OR
    2. Have no subagent_types specified (universal skills)

    Args:
        subagent_type: Type of subagent (validator, researcher, implementer, analyst)
        skills_dir: Path to skills directory (defaults to ~/.claude/skills/)

    Returns:
        Dict mapping skill names to SkillInfo objects for relevant skills
    """
    all_skills = discover_skills(skills_dir)
    relevant: Dict[str, SkillInfo] = {}

    for name, skill in all_skills.items():
        # Include if no types specified (universal) or if type matches
        if not skill.subagent_types or subagent_type in skill.subagent_types:
            relevant[name] = skill

    return relevant


def get_required_skills_for_subagent(subagent_type: str) -> List[str]:
    """Get the list of required skill names for a subagent type.

    This returns the skills defined in the subagent profile's required_tools.

    Args:
        subagent_type: Type of subagent (validator, researcher, implementer, analyst)

    Returns:
        List of skill names required by this subagent type
    """
    profile = SUBAGENT_PROFILES.get(subagent_type)
    if not profile:
        return []

    return list(profile.required_tools)
