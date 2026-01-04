"""PatternExtractor - Identifies successful workflow patterns.

This module extracts workflow patterns, successful tool combinations, and
project-specific patterns from conversation history and agent analysis results.
It generates system prompt additions that can be used to optimize RALPH configuration.
"""

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ralph_orchestrator.onboarding.history_analyzer import (
    HistoryAnalyzer,
    ToolUsageStats,
    MCPServerStats,
    ToolChain,
)
from ralph_orchestrator.onboarding.agent_analyzer import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    """A named workflow pattern with its steps and occurrence count.

    Attributes:
        name: Short name for the workflow (e.g., "test-fix-commit")
        steps: List of tool names in order
        count: Number of times this workflow was observed
        description: Human-readable description of the workflow
    """

    name: str
    steps: List[str]
    count: int = 1
    description: str = ""


@dataclass
class ProjectPatterns:
    """Project-specific patterns extracted from analysis.

    Attributes:
        workflows: List of identified workflow patterns
        successful_tools: List of tools with high success rates
        tool_success_rates: Dict mapping tool names to success rates
        common_commands: List of commonly used shell commands
        mcp_servers: List of MCP servers that were used
    """

    workflows: List[Workflow] = field(default_factory=list)
    successful_tools: List[str] = field(default_factory=list)
    tool_success_rates: Dict[str, float] = field(default_factory=dict)
    common_commands: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)


class PatternExtractor:
    """Identifies successful workflow patterns from conversation history.

    PatternExtractor analyzes conversation history and/or agent analysis results
    to extract:
    - Common workflow patterns (sequences of tools used together)
    - Successful tools (high success rate)
    - MCP server usage
    - Project-specific patterns

    It can work with:
    - Just HistoryAnalyzer (static analysis mode)
    - Just AnalysisResult (agent analysis mode)
    - Both (combined analysis)
    - Neither (returns empty/default patterns)

    Attributes:
        history: Optional HistoryAnalyzer for static analysis
        analysis_result: Optional AnalysisResult from agent analysis
    """

    def __init__(
        self,
        history: Optional[HistoryAnalyzer] = None,
        analysis_result: Optional[AnalysisResult] = None,
    ):
        """Initialize PatternExtractor.

        Args:
            history: Optional HistoryAnalyzer for JSONL-based static analysis
            analysis_result: Optional AnalysisResult from agent-based analysis
        """
        self.history = history
        self.analysis_result = analysis_result

    def identify_workflows(self) -> List[Workflow]:
        """Identify common workflow patterns from tool chains.

        Combines workflows from both history analysis (tool chains) and
        agent analysis (AnalysisResult.workflows) if available.

        Returns:
            List of Workflow objects representing common patterns.
        """
        workflows: List[Workflow] = []

        # Extract from history analyzer if available
        if self.history:
            tool_chains = self.history.extract_tool_chains()
            for chain in tool_chains:
                if chain.tools:
                    workflow = Workflow(
                        name=self._generate_workflow_name(chain.tools),
                        steps=chain.tools,
                        count=chain.count,
                        description=self._describe_workflow(chain.tools),
                    )
                    workflows.append(workflow)

        # Extract from analysis result if available
        if self.analysis_result and self.analysis_result.workflows:
            for workflow_steps in self.analysis_result.workflows:
                if workflow_steps:
                    workflow = Workflow(
                        name=self._generate_workflow_name(workflow_steps),
                        steps=workflow_steps,
                        count=1,
                        description=self._describe_workflow(workflow_steps),
                    )
                    workflows.append(workflow)

        return workflows

    def _generate_workflow_name(self, steps: List[str]) -> str:
        """Generate a short name for a workflow.

        Args:
            steps: List of tool names in the workflow

        Returns:
            Short descriptive name like "read-edit-test"
        """
        if not steps:
            return "empty"

        # Take first few unique tools, lowercased
        unique_tools = []
        for tool in steps:
            tool_lower = tool.lower().replace("mcp_", "").split("_")[0]
            if tool_lower not in unique_tools:
                unique_tools.append(tool_lower)
            if len(unique_tools) >= 3:
                break

        return "-".join(unique_tools)

    def _describe_workflow(self, steps: List[str]) -> str:
        """Generate a human-readable description for a workflow.

        Args:
            steps: List of tool names in the workflow

        Returns:
            Description of what the workflow does
        """
        if not steps:
            return ""

        tool_descriptions = {
            "Read": "read files",
            "Edit": "edit code",
            "Write": "write files",
            "Bash": "run commands",
            "Glob": "find files",
            "Grep": "search content",
        }

        descriptions = []
        seen = set()
        for tool in steps:
            if tool in tool_descriptions and tool not in seen:
                descriptions.append(tool_descriptions[tool])
                seen.add(tool)

        if descriptions:
            return ", ".join(descriptions)
        return f"Uses: {', '.join(steps[:3])}"

    def identify_successful_tools(self, threshold: float = 0.7) -> List[str]:
        """Identify tools with high success rates.

        Args:
            threshold: Minimum success rate to include (default 0.7 = 70%)

        Returns:
            List of tool names with success rates >= threshold.
        """
        successful_tools: List[str] = []

        # Extract from history analyzer if available
        if self.history:
            tool_stats = self.history.extract_tool_usage()
            for tool_name, stats in tool_stats.items():
                if stats.success_rate >= threshold:
                    successful_tools.append(tool_name)

        # Extract from analysis result if available
        if self.analysis_result and self.analysis_result.common_tools:
            for tool_name, success_rate in self.analysis_result.common_tools.items():
                if success_rate >= threshold and tool_name not in successful_tools:
                    successful_tools.append(tool_name)

        return successful_tools

    def identify_project_patterns(self) -> ProjectPatterns:
        """Extract comprehensive project-specific patterns.

        Combines all analysis to produce a ProjectPatterns object with:
        - Workflow patterns
        - Successful tools
        - Tool success rates
        - MCP servers used

        Returns:
            ProjectPatterns with all extracted patterns.
        """
        patterns = ProjectPatterns()

        # Get workflows
        patterns.workflows = self.identify_workflows()

        # Get successful tools
        patterns.successful_tools = self.identify_successful_tools()

        # Get tool success rates
        if self.history:
            tool_stats = self.history.extract_tool_usage()
            patterns.tool_success_rates = {
                name: stats.success_rate for name, stats in tool_stats.items()
            }

        if self.analysis_result and self.analysis_result.common_tools:
            # Merge with analysis result (analysis takes precedence)
            patterns.tool_success_rates.update(self.analysis_result.common_tools)

        # Get MCP servers
        if self.history:
            mcp_stats = self.history.extract_mcp_usage()
            patterns.mcp_servers = list(mcp_stats.keys())

        return patterns

    def generate_system_prompt_additions(self) -> str:
        """Generate system prompt text from extracted patterns.

        Creates a markdown-formatted string suitable for inclusion in
        RALPH_INSTRUCTIONS.md or system prompts.

        Returns:
            Formatted string with project context and recommendations.
        """
        lines: List[str] = []
        patterns = self.identify_project_patterns()

        # Add project type if known
        if self.analysis_result:
            if self.analysis_result.project_type != "unknown":
                lines.append(f"## Project Type")
                lines.append(f"This is a {self.analysis_result.project_type} project.")
                lines.append("")

            if self.analysis_result.frameworks:
                lines.append(f"## Frameworks")
                for fw in self.analysis_result.frameworks:
                    lines.append(f"- {fw}")
                lines.append("")

        # Add successful tools
        if patterns.successful_tools:
            lines.append("## Proven Tools")
            lines.append("These tools have high success rates for this project:")
            for tool in patterns.successful_tools[:10]:  # Limit to top 10
                rate = patterns.tool_success_rates.get(tool, 0.0)
                if rate > 0:
                    lines.append(f"- **{tool}** ({rate:.0%} success rate)")
                else:
                    lines.append(f"- **{tool}**")
            lines.append("")

        # Add workflow patterns
        if patterns.workflows:
            lines.append("## Common Workflows")
            for workflow in patterns.workflows[:5]:  # Limit to top 5
                lines.append(f"### {workflow.name}")
                if workflow.description:
                    lines.append(workflow.description)
                lines.append(f"Steps: {' -> '.join(workflow.steps[:5])}")
                lines.append("")

        # Add MCP servers
        if patterns.mcp_servers:
            lines.append("## MCP Servers")
            lines.append("These MCP servers have been used successfully:")
            for server in patterns.mcp_servers:
                lines.append(f"- {server}")
            lines.append("")

        # Return minimal prompt if nothing was extracted
        if not lines:
            return "## Project Patterns\nNo patterns extracted yet. Build up history by using Claude Code."

        return "\n".join(lines)
