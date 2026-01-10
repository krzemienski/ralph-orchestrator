# ABOUTME: ACE Learning Adapter for Ralph Orchestrator
# ABOUTME: Wraps ACE Framework components to provide learning capabilities

"""ACE Learning Adapter for Ralph Orchestrator.

Wraps ACE Framework components to provide learning capabilities
for the orchestration loop. ACE (Agentic Context Engineering) enables
agents to improve through in-context learning instead of fine-tuning.

The adapter provides:
- inject_context(): Add skillbook strategies to prompts
- learn_from_execution(): Update skillbook based on results
- save/load skillbook persistence

ACE Framework is an optional dependency. If not installed, the adapter
gracefully disables learning without affecting other functionality.

Reference: https://github.com/kayba-ai/agentic-context-engine
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger('ralph-orchestrator.learning')

# Graceful import of ACE Framework (optional dependency)
try:
    from ace import Skillbook
    from ace.llm_providers import LiteLLMClient
    from ace.roles import Reflector, SkillManager, AgentOutput
    from ace.prompts_v2_1 import PromptManager
    from ace.integrations.base import wrap_skillbook_context
    ACE_AVAILABLE = True
except ImportError:
    ACE_AVAILABLE = False
    logger.debug("ace-framework not installed. Install with: pip install ralph-orchestrator[learning]")
    # Define placeholder types for type hints when ACE not available
    Skillbook = None  # type: ignore
    LiteLLMClient = None  # type: ignore
    Reflector = None  # type: ignore
    SkillManager = None  # type: ignore
    AgentOutput = None  # type: ignore
    wrap_skillbook_context = None  # type: ignore


@dataclass
class LearningConfig:
    """Configuration for ACE learning.

    Attributes:
        enabled: Whether learning is enabled
        model: Model to use for Reflector/SkillManager (e.g., claude-sonnet-4-5-20250929)
        skillbook_path: Path to persist skillbook JSON
        async_learning: Whether to run learning in background (not blocking iterations)
        max_skills: Maximum number of skills to keep in skillbook
        max_tokens: Max tokens for ACE LLM calls
    """
    enabled: bool = False
    model: str = "claude-sonnet-4-5-20250929"
    skillbook_path: str = ".agent/skillbook/skillbook.json"
    async_learning: bool = True
    max_skills: int = 100
    max_tokens: int = 2048


class ACELearningAdapter:
    """Integrates ACE learning into Ralph orchestration loop.

    Provides:
    - inject_context(): Add skillbook strategies to prompt
    - learn_from_execution(): Update skillbook based on results
    - save/load skillbook persistence

    Thread-safe: Uses threading.Lock() for skillbook operations to prevent
    race conditions when async_learning is enabled.

    Example:
        config = LearningConfig(enabled=True, model="claude-sonnet-4-5-20250929")
        adapter = ACELearningAdapter(config)

        # Before iteration
        enhanced_prompt = adapter.inject_context(prompt)

        # Execute iteration via your adapter...

        # After iteration
        adapter.learn_from_execution(
            task="Original prompt",
            output="Agent response",
            success=True
        )

        # Save on checkpoint
        adapter.save_skillbook()
    """

    def __init__(self, config: LearningConfig):
        """Initialize ACE learning components.

        Args:
            config: Learning configuration

        Note:
            If ACE Framework is not installed, learning will be disabled
            automatically with a warning log.
        """
        self.config = config
        self._skillbook_lock = threading.Lock()

        # Check if ACE is available
        if not ACE_AVAILABLE:
            logger.warning(
                "ACE learning requested but ace-framework not installed. "
                "Install with: pip install ralph-orchestrator[learning]"
            )
            self._learning_enabled = False
            return

        # Check if learning is disabled in config
        if not config.enabled:
            logger.info("ACE learning disabled in configuration")
            self._learning_enabled = False
            return

        self._learning_enabled = True

        # Ensure skillbook directory exists
        skillbook_path = Path(config.skillbook_path)
        skillbook_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create skillbook
        try:
            if skillbook_path.exists():
                self.skillbook = Skillbook.load_from_file(str(skillbook_path))
                skill_count = len(list(self.skillbook.skills()))
                logger.info(f"Loaded skillbook with {skill_count} skills from {skillbook_path}")
            else:
                self.skillbook = Skillbook()
                logger.info(f"Created new skillbook at {skillbook_path}")
        except Exception as e:
            logger.warning(f"Failed to load skillbook, creating new: {e}")
            # Backup corrupted file if it exists
            if skillbook_path.exists():
                backup_path = skillbook_path.with_suffix('.json.bak')
                try:
                    skillbook_path.rename(backup_path)
                    logger.info(f"Backed up corrupted skillbook to {backup_path}")
                except Exception:
                    pass
            self.skillbook = Skillbook()

        # Initialize LLM client for ACE (separate from main adapter)
        try:
            self.llm = LiteLLMClient(
                model=config.model,
                max_tokens=config.max_tokens
            )
        except Exception as e:
            logger.warning(f"Failed to initialize learning LLM client: {e}")
            self._learning_enabled = False
            return

        # Initialize ACE components with v2.1 prompts
        try:
            prompt_mgr = PromptManager()
            self.reflector = Reflector(
                self.llm,
                prompt_template=prompt_mgr.get_reflector_prompt()
            )
            self.skill_manager = SkillManager(
                self.llm,
                prompt_template=prompt_mgr.get_skill_manager_prompt()
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ACE components: {e}")
            self._learning_enabled = False
            return

        logger.info(f"ACE learning initialized with model: {config.model}")

    @property
    def enabled(self) -> bool:
        """Check if learning is enabled."""
        return self._learning_enabled

    def inject_context(self, prompt: str) -> str:
        """Add skillbook strategies to prompt.

        Thread-safe: Uses lock to prevent race conditions.

        Args:
            prompt: Original prompt text

        Returns:
            Enhanced prompt with skillbook context appended,
            or original prompt if no skills or learning disabled.
        """
        if not self.enabled:
            return prompt

        with self._skillbook_lock:
            try:
                skills = list(self.skillbook.skills())
                if not skills:
                    logger.debug("No skills in skillbook, returning original prompt")
                    return prompt

                # Use ACE's wrap_skillbook_context for consistent formatting
                skillbook_context = wrap_skillbook_context(self.skillbook)
                enhanced = f"{prompt}\n\n{skillbook_context}"

                logger.debug(f"Injected {len(skills)} skills into prompt")
                return enhanced

            except Exception as e:
                logger.warning(f"Error injecting skillbook context: {e}")
                return prompt

    def learn_from_execution(
        self,
        task: str,
        output: str,
        success: bool,
        error: Optional[str] = None,
        execution_trace: str = ""
    ) -> None:
        """Learn from iteration execution.

        Thread-safe: Uses lock to prevent race conditions.
        Non-blocking: Errors are logged but don't crash the orchestrator.

        Args:
            task: The prompt/task that was executed
            output: Agent output text
            success: Whether iteration succeeded
            error: Error message if failed
            execution_trace: Optional execution trace for analysis
        """
        if not self.enabled:
            return

        with self._skillbook_lock:
            try:
                # Create AgentOutput for Reflector interface
                agent_output = AgentOutput(
                    reasoning=execution_trace or f"Task: {task[:500]}",
                    final_answer=output[:2000] if output else "",
                    skill_ids=[],  # External adapter, no pre-selected skills
                    raw={
                        "success": success,
                        "has_error": error is not None
                    }
                )

                # Build feedback string
                status = "succeeded" if success else "failed"
                feedback = f"Iteration {status}"
                if error:
                    feedback += f"\nError: {error[:500]}"

                # Run Reflector
                reflection = self.reflector.reflect(
                    question=task[:1000],
                    agent_output=agent_output,
                    skillbook=self.skillbook,
                    ground_truth=None,
                    feedback=feedback
                )

                # Run SkillManager
                skill_manager_output = self.skill_manager.update_skills(
                    reflection=reflection,
                    skillbook=self.skillbook,
                    question_context=f"task: {task[:500]}",
                    progress=f"Iteration: {task[:200]}"
                )

                # Update skillbook
                self.skillbook.apply_update(skill_manager_output.update)

                # Enforce max_skills limit
                self._prune_skills_if_needed()

                # Log learning
                skill_count = len(list(self.skillbook.skills()))
                logger.info(f"ACE learning complete. Skillbook now has {skill_count} skills")

            except Exception as e:
                logger.warning(f"ACE learning error (non-fatal): {e}")

    def _prune_skills_if_needed(self) -> None:
        """Prune lowest-scoring skills if over max_skills limit.

        Called after learning to enforce the max_skills configuration.
        Removes skills with the lowest (helpful - harmful) score.
        """
        try:
            skills = list(self.skillbook.skills())
            if len(skills) <= self.config.max_skills:
                return

            # Sort by score (helpful - harmful), ascending
            # We want to remove the lowest-scoring skills
            skills_with_scores = [
                (s, getattr(s, 'helpful', 0) - getattr(s, 'harmful', 0))
                for s in skills
            ]
            skills_with_scores.sort(key=lambda x: x[1])

            # Remove excess skills (lowest scoring first)
            excess = len(skills) - self.config.max_skills
            for skill, score in skills_with_scores[:excess]:
                skill_id = getattr(skill, 'id', None) or getattr(skill, 'skill_id', None)
                if skill_id:
                    # Try to remove skill - method depends on ACE version
                    if hasattr(self.skillbook, 'remove_skill'):
                        self.skillbook.remove_skill(skill_id)
                    logger.debug(f"Pruned low-scoring skill: {skill_id} (score: {score})")

            logger.info(f"Pruned {excess} low-scoring skills to enforce max_skills={self.config.max_skills}")

        except Exception as e:
            logger.debug(f"Skill pruning failed (non-critical): {e}")

    def save_skillbook(self) -> None:
        """Save skillbook to disk.

        Thread-safe: Uses lock to prevent race conditions.
        Called automatically on checkpoint and graceful shutdown.
        """
        if not self.enabled:
            return

        with self._skillbook_lock:
            try:
                path = Path(self.config.skillbook_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                self.skillbook.save_to_file(str(path))
                logger.debug(f"Saved skillbook to {path}")
            except Exception as e:
                logger.warning(f"Failed to save skillbook: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics.

        Returns:
            Dictionary with learning status and skillbook stats.
            Returns {"enabled": False} if learning is disabled.
        """
        if not self.enabled:
            return {"enabled": False}

        with self._skillbook_lock:
            try:
                skills = list(self.skillbook.skills())
                return {
                    "enabled": True,
                    "model": self.config.model,
                    "skillbook_path": self.config.skillbook_path,
                    "skill_count": len(skills),
                    "max_skills": self.config.max_skills,
                    "async_learning": self.config.async_learning,
                    "top_skills": [
                        {
                            "content": getattr(s, 'content', '')[:100],
                            "helpful": getattr(s, 'helpful', 0),
                            "harmful": getattr(s, 'harmful', 0),
                            "score": getattr(s, 'helpful', 0) - getattr(s, 'harmful', 0)
                        }
                        for s in sorted(
                            skills,
                            key=lambda x: getattr(x, 'helpful', 0) - getattr(x, 'harmful', 0),
                            reverse=True
                        )[:5]
                    ]
                }
            except Exception as e:
                logger.warning(f"Error getting learning stats: {e}")
                return {"enabled": True, "error": str(e)}


# Export ACE_AVAILABLE for external checks
__all__ = ["ACELearningAdapter", "LearningConfig", "ACE_AVAILABLE"]
