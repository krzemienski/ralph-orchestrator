# ABOUTME: ACE Learning module for Ralph Orchestrator
# ABOUTME: Provides self-improving agent loops via Agentic Context Engineering

"""ACE Learning module for Ralph Orchestrator.

This module provides integration with the ACE (Agentic Context Engineering)
framework to enable self-improving agent loops. After each iteration, ACE
analyzes what worked and what failed, then injects those learnings into
the next iteration.

Key Components:
- ACELearningAdapter: Main adapter class that wraps ACE components
- LearningConfig: Configuration dataclass for learning settings
- ACE_AVAILABLE: Boolean indicating if ace-framework is installed

Usage:
    from ralph_orchestrator.learning import ACELearningAdapter, LearningConfig

    config = LearningConfig(
        enabled=True,
        model="claude-sonnet-4-5-20250929",
        skillbook_path=".agent/skillbook/skillbook.json"
    )
    adapter = ACELearningAdapter(config)

    # Before iteration
    enhanced_prompt = adapter.inject_context(prompt)

    # After iteration
    adapter.learn_from_execution(task, output, success)

Installation:
    pip install ralph-orchestrator[learning]

Reference:
    https://github.com/kayba-ai/agentic-context-engine
"""

from .ace_adapter import ACELearningAdapter, LearningConfig, ACE_AVAILABLE

__all__ = ["ACELearningAdapter", "LearningConfig", "ACE_AVAILABLE"]
