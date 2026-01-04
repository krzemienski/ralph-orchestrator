#!/usr/bin/env python3
# ABOUTME: Orchestration package for Ralph - subagent coordination
# ABOUTME: Provides skill discovery, MCP profiling, and subagent spawning

from ralph_orchestrator.orchestration.config import SubagentProfile, SUBAGENT_PROFILES
from ralph_orchestrator.orchestration.discovery import (
    SkillInfo,
    discover_skills,
    get_skills_for_subagent,
    get_required_skills_for_subagent,
    MCPInfo,
    discover_mcps,
    get_mcps_for_subagent,
    get_required_mcps_for_subagent,
)
from ralph_orchestrator.orchestration.coordinator import CoordinationManager

__all__ = [
    "SubagentProfile",
    "SUBAGENT_PROFILES",
    "SkillInfo",
    "discover_skills",
    "get_skills_for_subagent",
    "get_required_skills_for_subagent",
    "MCPInfo",
    "discover_mcps",
    "get_mcps_for_subagent",
    "get_required_mcps_for_subagent",
    "CoordinationManager",
]
