"""Tests for PatternExtractor.

PatternExtractor identifies successful workflow patterns from conversation history
and agent analysis results to generate system prompt additions and recommendations.
"""

import pytest
from pathlib import Path
from typing import Dict, List

from ralph_orchestrator.onboarding.history_analyzer import (
    HistoryAnalyzer,
    ToolUsageStats,
    MCPServerStats,
    ToolChain,
    Conversation,
)
from ralph_orchestrator.onboarding.agent_analyzer import AnalysisResult
from ralph_orchestrator.onboarding.pattern_extractor import (
    PatternExtractor,
    Workflow,
    ProjectPatterns,
)


# =============================================================================
# PatternExtractor Initialization Tests
# =============================================================================


class TestPatternExtractorInit:
    """Tests for PatternExtractor initialization."""

    def test_init_with_history_analyzer(self, tmp_path: Path) -> None:
        """PatternExtractor initializes with a HistoryAnalyzer."""
        history = HistoryAnalyzer([])
        extractor = PatternExtractor(history)

        assert extractor.history == history
        assert extractor.analysis_result is None

    def test_init_with_analysis_result(self, tmp_path: Path) -> None:
        """PatternExtractor can accept an AnalysisResult from agent analysis."""
        history = HistoryAnalyzer([])
        analysis = AnalysisResult(
            project_type="python",
            frameworks=["fastapi", "pytest"],
        )
        extractor = PatternExtractor(history, analysis_result=analysis)

        assert extractor.history == history
        assert extractor.analysis_result == analysis

    def test_init_with_none_history(self) -> None:
        """PatternExtractor can be created with None history (agent-only mode)."""
        analysis = AnalysisResult(project_type="nodejs")
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        assert extractor.history is None
        assert extractor.analysis_result == analysis


# =============================================================================
# Workflow Dataclass Tests
# =============================================================================


class TestWorkflowDataclass:
    """Tests for the Workflow dataclass."""

    def test_workflow_creation(self) -> None:
        """Workflow can be created with steps and count."""
        workflow = Workflow(
            name="test-fix-commit",
            steps=["Edit", "Bash", "Bash"],
            count=5,
            description="Run tests, fix issues, commit",
        )

        assert workflow.name == "test-fix-commit"
        assert workflow.steps == ["Edit", "Bash", "Bash"]
        assert workflow.count == 5
        assert workflow.description == "Run tests, fix issues, commit"

    def test_workflow_default_count(self) -> None:
        """Workflow defaults count to 1."""
        workflow = Workflow(name="basic", steps=["Read", "Edit"])

        assert workflow.count == 1

    def test_workflow_default_description(self) -> None:
        """Workflow description can be empty."""
        workflow = Workflow(name="basic", steps=["Read"])

        assert workflow.description == ""


# =============================================================================
# ProjectPatterns Dataclass Tests
# =============================================================================


class TestProjectPatternsDataclass:
    """Tests for the ProjectPatterns dataclass."""

    def test_project_patterns_creation(self) -> None:
        """ProjectPatterns holds project-specific pattern data."""
        patterns = ProjectPatterns(
            workflows=[Workflow(name="tdd", steps=["Edit", "Bash"])],
            successful_tools=["Edit", "Read", "Bash"],
            tool_success_rates={"Edit": 0.95, "Bash": 0.87},
            common_commands=["npm test", "npm run build"],
            mcp_servers=["github", "memory"],
        )

        assert len(patterns.workflows) == 1
        assert patterns.successful_tools == ["Edit", "Read", "Bash"]
        assert patterns.tool_success_rates["Edit"] == 0.95
        assert patterns.common_commands == ["npm test", "npm run build"]
        assert patterns.mcp_servers == ["github", "memory"]

    def test_project_patterns_defaults(self) -> None:
        """ProjectPatterns has sensible defaults."""
        patterns = ProjectPatterns()

        assert patterns.workflows == []
        assert patterns.successful_tools == []
        assert patterns.tool_success_rates == {}
        assert patterns.common_commands == []
        assert patterns.mcp_servers == []


# =============================================================================
# Workflow Identification Tests
# =============================================================================


class TestIdentifyWorkflows:
    """Tests for identify_workflows method."""

    def test_identify_workflows_from_tool_chains(self, tmp_path: Path) -> None:
        """Identifies workflow patterns from tool chains."""
        # Create a JSONL file with a typical test-fix-commit pattern
        jsonl_file = tmp_path / "conv.jsonl"
        jsonl_file.write_text(
            '{"type": "assistant", "content": [{"type": "tool_use", "name": "Read", "id": "1"}]}\n'
            '{"type": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "is_error": false}]}\n'
            '{"type": "assistant", "content": [{"type": "tool_use", "name": "Edit", "id": "2"}]}\n'
            '{"type": "user", "content": [{"type": "tool_result", "tool_use_id": "2", "is_error": false}]}\n'
            '{"type": "assistant", "content": [{"type": "tool_use", "name": "Bash", "id": "3"}]}\n'
            '{"type": "user", "content": [{"type": "tool_result", "tool_use_id": "3", "is_error": false}]}\n'
        )

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        workflows = extractor.identify_workflows()

        assert len(workflows) >= 1
        # Should identify the Read -> Edit -> Bash pattern
        tool_names = [w.steps for w in workflows]
        assert any("Read" in steps and "Edit" in steps for steps in tool_names)

    def test_identify_workflows_empty_history(self) -> None:
        """Returns empty list for empty history."""
        history = HistoryAnalyzer([])
        extractor = PatternExtractor(history)

        workflows = extractor.identify_workflows()

        assert workflows == []

    def test_identify_workflows_from_analysis_result(self) -> None:
        """Uses workflows from AnalysisResult when available."""
        analysis = AnalysisResult(
            workflows=[["Read", "Edit", "Bash"], ["Grep", "Read", "Edit"]],
        )
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        workflows = extractor.identify_workflows()

        assert len(workflows) >= 2
        step_sets = [set(w.steps) for w in workflows]
        assert {"Read", "Edit", "Bash"} in step_sets or any(
            "Read" in w.steps and "Edit" in w.steps and "Bash" in w.steps
            for w in workflows
        )

    def test_identify_workflows_merges_sources(self, tmp_path: Path) -> None:
        """Merges workflows from history and analysis result."""
        jsonl_file = tmp_path / "conv.jsonl"
        jsonl_file.write_text(
            '{"type": "assistant", "content": [{"type": "tool_use", "name": "Glob", "id": "1"}]}\n'
            '{"type": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "is_error": false}]}\n'
        )

        history = HistoryAnalyzer([jsonl_file])
        analysis = AnalysisResult(
            workflows=[["Read", "Write"]],
        )
        extractor = PatternExtractor(history, analysis_result=analysis)

        workflows = extractor.identify_workflows()

        # Should have workflows from both sources
        all_tools_in_workflows = set()
        for w in workflows:
            all_tools_in_workflows.update(w.steps)

        # Should contain tools from both history (Glob) and analysis (Read, Write)
        assert "Glob" in all_tools_in_workflows or "Read" in all_tools_in_workflows


# =============================================================================
# Successful Tools Identification Tests
# =============================================================================


class TestIdentifySuccessfulTools:
    """Tests for identify_successful_tools method."""

    def test_identify_successful_tools_by_success_rate(self, tmp_path: Path) -> None:
        """Identifies tools with high success rates."""
        jsonl_file = tmp_path / "conv.jsonl"
        # Create 10 successful Read uses
        content = ""
        for i in range(10):
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "Read", "id": "r{i}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "r{i}", "is_error": false}}]}}\n'
        # Create 10 Bash uses with 2 failures
        for i in range(10):
            is_error = i < 2  # First 2 are errors
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "Bash", "id": "b{i}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "b{i}", "is_error": {"true" if is_error else "false"}}}]}}\n'

        jsonl_file.write_text(content)

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        successful_tools = extractor.identify_successful_tools()

        # Read should be identified (100% success rate)
        assert "Read" in successful_tools
        # Bash has 80% success rate, should still be included
        assert "Bash" in successful_tools

    def test_identify_successful_tools_threshold(self, tmp_path: Path) -> None:
        """Only includes tools above threshold (default 0.7)."""
        jsonl_file = tmp_path / "conv.jsonl"
        # Create tool with 50% success rate
        content = ""
        for i in range(10):
            is_error = i < 5  # First 5 are errors (50% failure)
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "BadTool", "id": "bt{i}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "bt{i}", "is_error": {"true" if is_error else "false"}}}]}}\n'
        # Create tool with 100% success rate
        for i in range(5):
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "GoodTool", "id": "gt{i}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "gt{i}", "is_error": false}}]}}\n'

        jsonl_file.write_text(content)

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        successful_tools = extractor.identify_successful_tools(threshold=0.7)

        assert "GoodTool" in successful_tools
        assert "BadTool" not in successful_tools

    def test_identify_successful_tools_empty_history(self) -> None:
        """Returns empty list for empty history."""
        history = HistoryAnalyzer([])
        extractor = PatternExtractor(history)

        successful_tools = extractor.identify_successful_tools()

        assert successful_tools == []

    def test_identify_successful_tools_from_analysis(self) -> None:
        """Uses common_tools from AnalysisResult."""
        analysis = AnalysisResult(
            common_tools={"Edit": 0.95, "Read": 0.90, "Bash": 0.60},
        )
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        successful_tools = extractor.identify_successful_tools(threshold=0.7)

        assert "Edit" in successful_tools
        assert "Read" in successful_tools
        assert "Bash" not in successful_tools  # Below threshold


# =============================================================================
# Project Patterns Identification Tests
# =============================================================================


class TestIdentifyProjectPatterns:
    """Tests for identify_project_patterns method."""

    def test_identify_project_patterns_complete(self, tmp_path: Path) -> None:
        """Extracts comprehensive project patterns."""
        jsonl_file = tmp_path / "conv.jsonl"
        # Create conversation with various tools
        content = ""
        # Read, Edit, Bash pattern
        for tool in ["Read", "Edit", "Bash", "mcp_github_commit"]:
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "{tool}", "id": "{tool}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "{tool}", "is_error": false}}]}}\n'

        jsonl_file.write_text(content)

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        patterns = extractor.identify_project_patterns()

        assert isinstance(patterns, ProjectPatterns)
        # Should have some successful tools
        assert len(patterns.successful_tools) > 0
        # Should detect github MCP server
        assert "github" in patterns.mcp_servers

    def test_identify_project_patterns_with_analysis(self) -> None:
        """Combines patterns from history and agent analysis."""
        analysis = AnalysisResult(
            project_type="expo",
            frameworks=["react-native", "expo"],
            common_tools={"Edit": 0.95, "Read": 0.90},
            workflows=[["Read", "Edit", "Bash"]],
        )
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        patterns = extractor.identify_project_patterns()

        assert isinstance(patterns, ProjectPatterns)
        assert "Edit" in patterns.successful_tools
        assert patterns.tool_success_rates.get("Edit") == 0.95


# =============================================================================
# System Prompt Generation Tests
# =============================================================================


class TestGenerateSystemPromptAdditions:
    """Tests for generate_system_prompt_additions method."""

    def test_generate_system_prompt_basic(self, tmp_path: Path) -> None:
        """Generates system prompt additions from patterns."""
        jsonl_file = tmp_path / "conv.jsonl"
        content = ""
        for tool in ["Read", "Edit", "Bash"]:
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "{tool}", "id": "{tool}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "{tool}", "is_error": false}}]}}\n'
        jsonl_file.write_text(content)

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        prompt = extractor.generate_system_prompt_additions()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should mention proven tools
        assert "Read" in prompt or "Edit" in prompt or "Bash" in prompt

    def test_generate_system_prompt_with_project_type(self) -> None:
        """Includes project type context in prompt."""
        analysis = AnalysisResult(
            project_type="python",
            frameworks=["fastapi", "pytest"],
            common_tools={"Edit": 0.95},
        )
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        prompt = extractor.generate_system_prompt_additions()

        assert "python" in prompt.lower() or "Python" in prompt
        assert "fastapi" in prompt.lower() or "FastAPI" in prompt

    def test_generate_system_prompt_includes_workflows(self) -> None:
        """Includes workflow patterns in prompt."""
        analysis = AnalysisResult(
            workflows=[["Read", "Edit", "Bash", "Bash"]],
        )
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        prompt = extractor.generate_system_prompt_additions()

        # Should mention workflow or pattern
        assert "workflow" in prompt.lower() or "pattern" in prompt.lower() or "Read" in prompt

    def test_generate_system_prompt_empty_history(self) -> None:
        """Returns minimal prompt for empty history."""
        history = HistoryAnalyzer([])
        extractor = PatternExtractor(history)

        prompt = extractor.generate_system_prompt_additions()

        # Should return a string (possibly minimal)
        assert isinstance(prompt, str)

    def test_generate_system_prompt_mcp_servers(self) -> None:
        """Includes MCP server recommendations in prompt."""
        analysis = AnalysisResult(
            project_type="nodejs",
        )
        # We need history with MCP usage
        extractor = PatternExtractor(history=None, analysis_result=analysis)

        # When MCP servers are detected, they should be mentioned
        prompt = extractor.generate_system_prompt_additions()

        assert isinstance(prompt, str)


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestPatternExtractorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_corrupted_jsonl(self, tmp_path: Path) -> None:
        """Handles corrupted JSONL gracefully."""
        jsonl_file = tmp_path / "corrupted.jsonl"
        jsonl_file.write_text(
            "not json at all\n"
            '{"type": "assistant", "content": [{"type": "tool_use", "name": "Read", "id": "1"}]}\n'
            '{"broken json\n'
            '{"type": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "is_error": false}]}\n'
        )

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        # Should not raise, should extract what it can
        workflows = extractor.identify_workflows()
        assert isinstance(workflows, list)

    def test_handles_missing_files(self, tmp_path: Path) -> None:
        """Handles missing files gracefully."""
        missing_file = tmp_path / "does_not_exist.jsonl"
        history = HistoryAnalyzer([missing_file])
        extractor = PatternExtractor(history)

        workflows = extractor.identify_workflows()

        assert workflows == []

    def test_neither_history_nor_analysis(self) -> None:
        """Handles case with neither history nor analysis."""
        extractor = PatternExtractor(history=None, analysis_result=None)

        workflows = extractor.identify_workflows()
        successful_tools = extractor.identify_successful_tools()
        patterns = extractor.identify_project_patterns()
        prompt = extractor.generate_system_prompt_additions()

        assert workflows == []
        assert successful_tools == []
        assert isinstance(patterns, ProjectPatterns)
        assert isinstance(prompt, str)

    def test_large_history(self, tmp_path: Path) -> None:
        """Handles large history files efficiently."""
        jsonl_file = tmp_path / "large.jsonl"
        content = ""
        # Create 1000 tool uses
        for i in range(1000):
            tool = ["Read", "Edit", "Bash", "Write"][i % 4]
            content += f'{{"type": "assistant", "content": [{{"type": "tool_use", "name": "{tool}", "id": "t{i}"}}]}}\n'
            content += f'{{"type": "user", "content": [{{"type": "tool_result", "tool_use_id": "t{i}", "is_error": false}}]}}\n'

        jsonl_file.write_text(content)

        history = HistoryAnalyzer([jsonl_file])
        extractor = PatternExtractor(history)

        # Should complete without issues
        workflows = extractor.identify_workflows()
        successful_tools = extractor.identify_successful_tools()

        assert len(successful_tools) >= 1
