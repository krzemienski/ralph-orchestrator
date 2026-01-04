#!/usr/bin/env python3
# ABOUTME: OrchestrationManager for subagent coordination and prompt generation
# ABOUTME: Implements Phase O5 - Integration & Subagent Spawning

from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .config import SUBAGENT_PROFILES
from .coordinator import CoordinationManager
from .discovery import (
    discover_skills,
    get_required_skills_for_subagent,
    discover_mcps,
    get_required_mcps_for_subagent,
)

if TYPE_CHECKING:
    from ralph_orchestrator.main import RalphConfig


class OrchestrationManager:
    """Manages subagent orchestration workflow.

    Coordinates skill discovery, MCP profiling, prompt generation, and
    result aggregation for subagent-based task execution.

    Attributes:
        config: RalphConfig instance with orchestration settings
        coordinator: CoordinationManager for file-based coordination
    """

    def __init__(
        self,
        config: "RalphConfig",
        base_dir: Optional[Path] = None,
    ):
        """Initialize OrchestrationManager.

        Args:
            config: RalphConfig instance
            base_dir: Base directory for coordination files (defaults to cwd)
        """
        self.config = config
        self.base_dir = base_dir if base_dir is not None else Path.cwd()
        self.coordinator = CoordinationManager(self.base_dir)

    def generate_subagent_prompt(
        self,
        subagent_type: str,
        phase: str,
        criteria: List[str],
        subagent_id: str = "001",
    ) -> str:
        """Generate a prompt for a specific subagent type.

        Creates a prompt including:
        - Skill loading instructions
        - MCP tool availability
        - Coordination file paths
        - Task description from criteria

        Args:
            subagent_type: Type of subagent (validator, researcher, implementer, analyst)
            phase: Current phase name
            criteria: List of acceptance criteria to validate
            subagent_id: Unique ID for this subagent instance (default: "001")

        Returns:
            Complete prompt string for the subagent
        """
        profile = SUBAGENT_PROFILES.get(subagent_type)
        if not profile:
            raise ValueError(f"Unknown subagent type: {subagent_type}")

        # Generate skill instructions
        skill_instructions = self._generate_skill_instructions(subagent_type)

        # Generate MCP list
        mcp_list = self._generate_mcp_list(subagent_type)

        # Generate task description from criteria
        task_description = self._generate_task_description(phase, criteria)

        # Use profile template with substitutions
        prompt = profile.prompt_template.format(
            skill_instructions=skill_instructions,
            mcp_list=mcp_list,
            task_description=task_description,
            id=subagent_id,
        )

        return prompt

    def _generate_skill_instructions(self, subagent_type: str) -> str:
        """Generate skill loading instructions for a subagent.

        Args:
            subagent_type: Type of subagent

        Returns:
            Formatted skill loading instructions
        """
        required_skills = get_required_skills_for_subagent(subagent_type)
        available_skills = discover_skills()

        lines = []

        # Add required skills
        if required_skills:
            lines.append("**Required Skills (MUST load):**")
            for skill_name in required_skills:
                if skill_name in available_skills:
                    skill_info = available_skills[skill_name]
                    lines.append(f"- `Skill({skill_name})` - {skill_info.description}")
                else:
                    lines.append(f"- `Skill({skill_name})` - (not found, but required)")

        # Add note about skill loading
        if lines:
            lines.append("")
            lines.append("Load these skills BEFORE starting work using the Skill tool.")

        return "\n".join(lines) if lines else "No specific skills required."

    def _generate_mcp_list(self, subagent_type: str) -> str:
        """Generate MCP tool list for a subagent.

        Args:
            subagent_type: Type of subagent

        Returns:
            Formatted MCP tool list
        """
        required_mcps = get_required_mcps_for_subagent(subagent_type)
        profile = SUBAGENT_PROFILES.get(subagent_type)
        optional_mcps = profile.optional_mcps if profile else []

        available_mcps = discover_mcps()

        lines = []

        # Add required MCPs
        if required_mcps:
            lines.append("**Required MCP Servers:**")
            for mcp_name in required_mcps:
                if mcp_name in available_mcps:
                    mcp_info = available_mcps[mcp_name]
                    status = "enabled" if mcp_info.enabled else "disabled"
                    lines.append(f"- `{mcp_name}` ({status})")
                else:
                    lines.append(f"- `{mcp_name}` (not configured)")

        # Add optional MCPs
        if optional_mcps:
            lines.append("")
            lines.append("**Optional MCP Servers (if available):**")
            for mcp_name in optional_mcps:
                if mcp_name in available_mcps:
                    mcp_info = available_mcps[mcp_name]
                    if mcp_info.enabled:
                        lines.append(f"- `{mcp_name}` (available)")
                else:
                    lines.append(f"- `{mcp_name}` (not configured)")

        return "\n".join(lines) if lines else "Standard tools only."

    def _generate_task_description(
        self, phase: str, criteria: List[str]
    ) -> str:
        """Generate task description from phase and criteria.

        Args:
            phase: Current phase name
            criteria: List of acceptance criteria

        Returns:
            Formatted task description
        """
        lines = [
            f"**Phase:** {phase}",
            "",
            "**Acceptance Criteria:**",
        ]

        for i, criterion in enumerate(criteria, 1):
            lines.append(f"{i}. {criterion}")

        lines.append("")
        lines.append("Validate each criterion through REAL execution and collect evidence.")

        return "\n".join(lines)

    def aggregate_results(self) -> Dict[str, Any]:
        """Aggregate results from all subagents.

        Collects results from coordination files and determines overall verdict.
        Verdict is PASS only if all subagents with verdicts pass.

        Returns:
            Dict with aggregated results:
            - verdict: "PASS" | "FAIL" | "NO_RESULTS"
            - subagent_results: List of individual results
            - summary: Human-readable summary
        """
        results = self.coordinator.collect_results()

        if not results:
            return {
                "verdict": "NO_RESULTS",
                "subagent_results": [],
                "summary": "No subagent results found.",
            }

        # Check for any FAIL verdict
        verdicts = [r.get("verdict") for r in results if "verdict" in r]
        has_fail = any(v == "FAIL" for v in verdicts)
        all_pass = all(v == "PASS" for v in verdicts) if verdicts else False

        if has_fail:
            overall_verdict = "FAIL"
        elif all_pass:
            overall_verdict = "PASS"
        else:
            overall_verdict = "INCONCLUSIVE"

        # Generate summary
        pass_count = sum(1 for v in verdicts if v == "PASS")
        fail_count = sum(1 for v in verdicts if v == "FAIL")
        summary = f"{pass_count} passed, {fail_count} failed out of {len(results)} subagent(s)"

        return {
            "verdict": overall_verdict,
            "subagent_results": results,
            "summary": summary,
        }
