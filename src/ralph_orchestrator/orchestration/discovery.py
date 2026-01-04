#!/usr/bin/env python3
# ABOUTME: Skill and MCP discovery for Ralph orchestrator subagents
# ABOUTME: Scans skill directories, MCP configs, and maps to subagent types

import json
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


# ==============================================================================
# MCP DISCOVERY
# ==============================================================================


@dataclass
class MCPInfo:
    """Information about a discovered MCP server.

    Attributes:
        name: MCP server name (from config key)
        command: Command to run the MCP server
        args: Command line arguments
        enabled: Whether the server is enabled (not in disabled list)
        tools: List of known tool names (from autoApprove if available)
    """

    name: str
    command: str
    args: List[str] = field(default_factory=list)
    enabled: bool = True
    tools: List[str] = field(default_factory=list)


# Default MCP config path
DEFAULT_MCP_CONFIG_PATH = Path.home() / ".mcp.json"


def discover_mcps(
    mcp_config_path: Optional[Path] = None,
    disabled_servers: Optional[List[str]] = None,
) -> Dict[str, MCPInfo]:
    """Discover available MCP servers from configuration.

    Reads ~/.mcp.json for available MCP servers. Marks servers as disabled
    if they appear in the disabled_servers list.

    Args:
        mcp_config_path: Path to MCP config file (defaults to ~/.mcp.json)
        disabled_servers: List of server names that are disabled

    Returns:
        Dict mapping server names to MCPInfo objects
    """
    if mcp_config_path is None:
        mcp_config_path = DEFAULT_MCP_CONFIG_PATH

    if disabled_servers is None:
        disabled_servers = []

    if not mcp_config_path.exists():
        return {}

    try:
        content = mcp_config_path.read_text()
        config = json.loads(content)
    except (json.JSONDecodeError, IOError):
        return {}

    mcp_servers = config.get("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        return {}

    result: Dict[str, MCPInfo] = {}

    for name, server_config in mcp_servers.items():
        if not isinstance(server_config, dict):
            continue

        command = server_config.get("command", "")
        if not command:
            continue

        args = server_config.get("args", [])
        if not isinstance(args, list):
            args = []

        # Extract tools from autoApprove if available
        tools = server_config.get("autoApprove", [])
        if not isinstance(tools, list):
            tools = []

        enabled = name not in disabled_servers

        result[name] = MCPInfo(
            name=name,
            command=command,
            args=args,
            enabled=enabled,
            tools=tools,
        )

    return result


def get_mcps_for_subagent(
    subagent_type: str,
    mcp_config_path: Optional[Path] = None,
    disabled_servers: Optional[List[str]] = None,
) -> Dict[str, MCPInfo]:
    """Get MCP servers relevant for a specific subagent type.

    Returns MCPs that are either required or optional for the subagent type,
    filtered to only include those that are enabled and exist in the config.

    Args:
        subagent_type: Type of subagent (validator, researcher, implementer, analyst)
        mcp_config_path: Path to MCP config file (defaults to ~/.mcp.json)
        disabled_servers: List of server names that are disabled

    Returns:
        Dict mapping server names to MCPInfo objects for relevant MCPs
    """
    profile = SUBAGENT_PROFILES.get(subagent_type)
    if not profile:
        return {}

    all_mcps = discover_mcps(mcp_config_path, disabled_servers)

    # Get required and optional MCP names for this subagent type
    relevant_names = set(profile.required_mcps) | set(profile.optional_mcps)

    # Filter to only include enabled MCPs that are in the relevant list
    result: Dict[str, MCPInfo] = {}
    for name, mcp in all_mcps.items():
        if name in relevant_names and mcp.enabled:
            result[name] = mcp

    return result


def get_required_mcps_for_subagent(subagent_type: str) -> List[str]:
    """Get the list of required MCP server names for a subagent type.

    This returns the MCPs defined in the subagent profile's required_mcps.

    Args:
        subagent_type: Type of subagent (validator, researcher, implementer, analyst)

    Returns:
        List of MCP server names required by this subagent type
    """
    profile = SUBAGENT_PROFILES.get(subagent_type)
    if not profile:
        return []

    return list(profile.required_mcps)
