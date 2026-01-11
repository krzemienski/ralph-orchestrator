# ABOUTME: ACE Learning Adapter for Ralph Orchestrator
# ABOUTME: Wraps ACE Framework components to provide learning capabilities

"""ACE Learning Adapter for Ralph Orchestrator.

Wraps ACE Framework components to provide learning capabilities
for the orchestration loop. ACE (Agentic Context Engineering) enables
agents to improve through in-context learning instead of fine-tuning.

The adapter provides:
- inject_context(): Add skillbook strategies to prompts
- learn_from_execution(): Update skillbook based on results (async or sync)
- save/load skillbook persistence
- shutdown(): Graceful shutdown with skillbook persistence

ACE Framework is an optional dependency. If not installed, the adapter
gracefully disables learning without affecting other functionality.

Reference: https://github.com/kayba-ai/agentic-context-engine
"""

import atexit
import logging
import os
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger('ralph-orchestrator.learning')

# Telemetry event types for learning operations
LEARNING_EVENTS = {
    'INIT': 'learning_init',
    'INJECT': 'skillbook_inject',
    'REFLECT': 'reflector_run',
    'SKILL_UPDATE': 'skill_manager_update',
    'PRUNE': 'skillbook_prune',
    'SAVE': 'skillbook_save',
    'ERROR': 'learning_error',
}


@dataclass
class LearningEvent:
    """Structured learning telemetry event."""
    event_type: str
    timestamp: str
    duration_ms: float
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'details': self.details,
            'error': self.error,
        }

    def __str__(self) -> str:
        status = '✓' if self.success else '✗'
        return f"[{self.event_type}] {status} {self.duration_ms:.1f}ms | {self.details}"


# Graceful import of ACE Framework (optional dependency)
# ACE has a langchain integration that can conflict with newer pydantic versions
# We mock langchain modules if needed to avoid import errors
ACE_AVAILABLE = False
try:
    # Try direct import first
    from ace import Skillbook
    from ace.llm_providers import LiteLLMClient
    from ace.roles import Reflector, SkillManager, AgentOutput
    from ace.prompts_v2_1 import PromptManager
    from ace.integrations.base import wrap_skillbook_context
    ACE_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    # If langchain conflict, try with mocked langchain
    if 'langchain' in str(e).lower() or 'pydantic' in str(e).lower():
        try:
            import sys
            from unittest.mock import MagicMock
            # Mock langchain to avoid pydantic v1/v2 conflicts
            for mod in ['langchain', 'langchain.agents', 'langchain.chains', 'langchain.llms']:
                if mod not in sys.modules:
                    sys.modules[mod] = MagicMock()
            # Now retry imports
            from ace.skillbook import Skillbook
            from ace.llm_providers import LiteLLMClient
            from ace.roles import Reflector, SkillManager, AgentOutput
            from ace.prompts_v2_1 import PromptManager
            from ace.integrations.base import wrap_skillbook_context
            ACE_AVAILABLE = True
            logger.debug("ACE imported with langchain mocked (pydantic conflict workaround)")
        except ImportError:
            pass
    if not ACE_AVAILABLE:
        logger.debug("ace-framework not installed. Install with: pip install ralph-orchestrator[learning]")

if not ACE_AVAILABLE:
    # Define placeholder types for type hints when ACE not available
    Skillbook = None  # type: ignore
    LiteLLMClient = None  # type: ignore
    Reflector = None  # type: ignore
    SkillManager = None  # type: ignore
    AgentOutput = None  # type: ignore
    wrap_skillbook_context = None  # type: ignore


@dataclass
class LearningTask:
    """A learning task to be processed by the async worker.

    Attributes:
        task: The prompt/task that was executed
        output: Agent output text
        success: Whether iteration succeeded
        error: Error message if failed
        execution_trace: Execution trace for analysis
        iteration: The iteration number this task came from
        created_at: When this task was created
    """
    task: str
    output: str
    success: bool
    error: Optional[str] = None
    execution_trace: str = ""
    iteration: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')


@dataclass
class LearningConfig:
    """Configuration for ACE learning.

    Attributes:
        enabled: Whether learning is enabled
        model: Model to use for Reflector/SkillManager (defaults to gpt-4o-mini for efficiency)
        skillbook_path: Path to persist skillbook JSON
        async_learning: Whether to run learning in background (not blocking iterations)
        max_skills: Maximum number of skills to keep in skillbook
        max_tokens: Max tokens for ACE LLM calls
        prune_threshold: Effectiveness score below which to prune skills
        deduplication_enabled: Enable embedding-based skill deduplication
        similarity_threshold: Cosine similarity threshold for deduplication
        worker_timeout: Timeout in seconds for async worker to complete
    """
    enabled: bool = False
    model: str = "gpt-4o-mini"  # Efficient model for ACE operations
    skillbook_path: str = ".agent/skillbook/skillbook.json"
    async_learning: bool = True
    max_skills: int = 100
    max_tokens: int = 2048
    prune_threshold: float = -0.3  # Prune skills with negative effectiveness
    deduplication_enabled: bool = True
    similarity_threshold: float = 0.85
    worker_timeout: float = 30.0  # Max seconds to wait for worker on shutdown
    top_k_skills: int = 0  # 0 = inject all skills, >0 = inject top K by score (Phase 5)


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
        init_start = time.time()
        self.config = config
        self._skillbook_lock = threading.Lock()

        # Async learning worker components
        self._learning_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._worker_running = False

        # Telemetry tracking
        self._events: List[LearningEvent] = []
        self._stats = {
            'reflections_count': 0,
            'skills_added': 0,
            'skills_updated': 0,
            'skills_pruned': 0,
            'skills_deduplicated': 0,
            'inject_count': 0,
            'errors_count': 0,
            'total_learning_time_ms': 0.0,
            'async_tasks_queued': 0,
            'async_tasks_processed': 0,
            'rollback_learnings': 0,
        }

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
        # CRITICAL: Explicitly read API key from environment at initialization time
        # LiteLLM's auto-detection can fail in subprocess/thread contexts
        try:
            # Determine which API key to use based on model
            api_key = None
            api_key_env_var = None

            if 'claude' in config.model.lower() or 'anthropic' in config.model.lower():
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                api_key_env_var = 'ANTHROPIC_API_KEY'
            elif 'gpt' in config.model.lower() or 'openai' in config.model.lower():
                api_key = os.environ.get('OPENAI_API_KEY')
                api_key_env_var = 'OPENAI_API_KEY'
            elif 'gemini' in config.model.lower() or 'google' in config.model.lower():
                api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
                api_key_env_var = 'GOOGLE_API_KEY or GEMINI_API_KEY'
            else:
                # Try common API keys
                api_key = (
                    os.environ.get('ANTHROPIC_API_KEY') or
                    os.environ.get('OPENAI_API_KEY') or
                    os.environ.get('GOOGLE_API_KEY')
                )
                api_key_env_var = 'ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY'

            if not api_key:
                logger.error(
                    f"ACE learning requires {api_key_env_var} environment variable for model '{config.model}'. "
                    "Please set the appropriate API key in your environment."
                )
                self._learning_enabled = False
                return

            logger.debug(f"ACE learning using API key from {api_key_env_var} ({len(api_key)} chars)")

            self.llm = LiteLLMClient(
                model=config.model,
                max_tokens=config.max_tokens,
                api_key=api_key  # Explicit pass-through to avoid environment detection issues
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

        # Start async learning worker if enabled
        if config.async_learning:
            self._start_worker()

        # Register shutdown handler to save skillbook on exit
        atexit.register(self._atexit_handler)

        # Log successful initialization
        init_duration = (time.time() - init_start) * 1000
        skill_count = len(list(self.skillbook.skills()))
        self._record_event(
            LEARNING_EVENTS['INIT'],
            init_duration,
            success=True,
            details={
                'model': config.model,
                'skillbook_path': config.skillbook_path,
                'initial_skills': skill_count,
                'max_skills': config.max_skills,
                'async_learning': config.async_learning,
                'deduplication_enabled': config.deduplication_enabled,
            }
        )
        logger.info(
            f"ACE learning initialized | model={config.model} | "
            f"skills={skill_count} | path={config.skillbook_path} | "
            f"async={config.async_learning}"
        )

    def _record_event(
        self,
        event_type: str,
        duration_ms: float,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> LearningEvent:
        """Record a telemetry event for learning operations."""
        event = LearningEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            duration_ms=duration_ms,
            success=success,
            details=details or {},
            error=error,
        )
        self._events.append(event)

        # Update aggregate stats
        if not success:
            self._stats['errors_count'] += 1

        # Log the event
        if success:
            logger.debug(f"Learning event: {event}")
        else:
            logger.warning(f"Learning event (failed): {event}")

        return event

    def _start_worker(self) -> None:
        """Start the async learning worker thread.

        The worker processes learning tasks from a queue in the background,
        preventing learning operations from blocking the main orchestration loop.
        """
        if self._worker_running:
            return

        self._shutdown_event.clear()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="ACELearningWorker",
            daemon=True  # Allow clean exit even if worker is running
        )
        self._worker_running = True
        self._worker_thread.start()
        logger.debug("ACE learning worker thread started")

    def _worker_loop(self) -> None:
        """Main loop for the async learning worker.

        Processes learning tasks from the queue until shutdown is signaled.
        Each task is processed with full error handling to prevent worker crashes.
        """
        while not self._shutdown_event.is_set():
            try:
                # Wait for a task with timeout (allows checking shutdown event)
                try:
                    learning_task: LearningTask = self._learning_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Process the learning task
                self._process_learning_task(learning_task)
                self._stats['async_tasks_processed'] += 1
                self._learning_queue.task_done()

            except Exception as e:
                logger.warning(f"ACE learning worker error (non-fatal): {e}")
                self._stats['errors_count'] += 1

        logger.debug("ACE learning worker thread exiting")
        self._worker_running = False

    def _process_learning_task(self, task: LearningTask) -> None:
        """Process a single learning task (runs in worker thread).

        This is the core learning logic extracted from learn_from_execution
        to run in the background worker thread.

        Args:
            task: The learning task to process
        """
        learn_start = time.time()
        skills_before = 0

        with self._skillbook_lock:
            try:
                skills_before = len(list(self.skillbook.skills()))

                # Build rich execution trace for better reflection
                execution_trace = self._build_rich_execution_trace(task)

                # Create AgentOutput for Reflector interface
                agent_output = AgentOutput(
                    reasoning=execution_trace,
                    final_answer=task.output[:2000] if task.output else "",
                    skill_ids=[],  # External adapter, no pre-selected skills
                    raw={
                        "success": task.success,
                        "has_error": task.error is not None,
                        "iteration": task.iteration,
                        "task_preview": task.task[:200] if task.task else "",
                    }
                )

                # Build feedback string
                status = "succeeded" if task.success else "failed"
                feedback = f"Iteration {task.iteration} {status}"
                if task.error:
                    feedback += f"\nError: {task.error[:500]}"

                # Run Reflector with timing
                reflect_start = time.time()
                reflection = self.reflector.reflect(
                    question=task.task[:1000],
                    agent_output=agent_output,
                    skillbook=self.skillbook,
                    ground_truth=None,
                    feedback=feedback
                )
                reflect_duration = (time.time() - reflect_start) * 1000

                # Record reflection event
                self._stats['reflections_count'] += 1
                self._record_event(
                    LEARNING_EVENTS['REFLECT'],
                    reflect_duration,
                    success=True,
                    details={
                        'task_success': task.success,
                        'task_len': len(task.task),
                        'output_len': len(task.output) if task.output else 0,
                        'iteration': task.iteration,
                        'has_execution_trace': bool(task.execution_trace),
                        'reflection_summary': str(reflection)[:200] if reflection else None,
                    }
                )

                # Run SkillManager with timing
                skill_mgr_start = time.time()
                skill_manager_output = self.skill_manager.update_skills(
                    reflection=reflection,
                    skillbook=self.skillbook,
                    question_context=f"task: {task.task[:500]}",
                    progress=f"Iteration {task.iteration}: {task.task[:200]}"
                )
                skill_mgr_duration = (time.time() - skill_mgr_start) * 1000

                # Apply skill updates with deduplication
                self._apply_skill_update_with_deduplication(skill_manager_output.update)

                # Calculate skill changes
                skills_after = len(list(self.skillbook.skills()))
                skills_delta = skills_after - skills_before

                # Record skill update event
                if skills_delta > 0:
                    self._stats['skills_added'] += skills_delta
                elif skills_delta < 0:
                    self._stats['skills_pruned'] += abs(skills_delta)
                else:
                    self._stats['skills_updated'] += 1  # Assume update if no net change

                self._record_event(
                    LEARNING_EVENTS['SKILL_UPDATE'],
                    skill_mgr_duration,
                    success=True,
                    details={
                        'skills_before': skills_before,
                        'skills_after': skills_after,
                        'skills_delta': skills_delta,
                        'update_type': getattr(skill_manager_output.update, 'type', 'unknown'),
                        'iteration': task.iteration,
                    }
                )

                # Enforce max_skills limit
                self._prune_skills_if_needed()

                # Calculate total learning time
                total_duration = (time.time() - learn_start) * 1000
                self._stats['total_learning_time_ms'] += total_duration

                # Log comprehensive learning summary
                logger.info(
                    f"ACE learning complete | iteration={task.iteration} | "
                    f"skills={skills_after} (Δ{skills_delta:+d}) | "
                    f"reflect={reflect_duration:.1f}ms | skill_mgr={skill_mgr_duration:.1f}ms | "
                    f"total={total_duration:.1f}ms | task_success={task.success}"
                )

            except Exception as e:
                learn_duration = (time.time() - learn_start) * 1000
                self._record_event(
                    LEARNING_EVENTS['ERROR'],
                    learn_duration,
                    success=False,
                    error=str(e),
                    details={
                        'phase': 'process_learning_task',
                        'task_success': task.success,
                        'skills_before': skills_before,
                        'iteration': task.iteration,
                    }
                )
                logger.warning(f"ACE learning error (non-fatal): {e}")

    def _build_rich_execution_trace(self, task: LearningTask) -> str:
        """Build a rich execution trace for the Reflector.

        Creates a structured trace that includes all relevant context
        for the Reflector to analyze and extract skills from.

        Args:
            task: The learning task containing execution data

        Returns:
            Formatted execution trace string
        """
        trace_parts = []

        # Task context
        trace_parts.append(f"## Task\n{task.task[:1000]}")

        # Execution metadata
        trace_parts.append(f"\n## Execution Metadata")
        trace_parts.append(f"- Iteration: {task.iteration}")
        trace_parts.append(f"- Success: {task.success}")
        trace_parts.append(f"- Timestamp: {task.created_at}")

        # Error information if present
        if task.error:
            trace_parts.append(f"\n## Error\n{task.error[:500]}")

        # Original execution trace if provided
        if task.execution_trace:
            trace_parts.append(f"\n## Execution Details\n{task.execution_trace[:1000]}")

        # Output summary
        if task.output:
            output_preview = task.output[:1000] if len(task.output) > 1000 else task.output
            trace_parts.append(f"\n## Output Summary\n{output_preview}")

        return "\n".join(trace_parts)

    def _apply_skill_update_with_deduplication(self, update) -> None:
        """Apply skill update with deduplication check.

        Before adding new skills, checks for similar existing skills
        to prevent duplication. Uses simple content matching for now,
        with option to extend to embedding-based similarity.

        Args:
            update: The skill update from SkillManager
        """
        if not self.config.deduplication_enabled:
            self.skillbook.apply_update(update)
            return

        # Get the update type and new skills
        update_type = getattr(update, 'type', None)

        # Only deduplicate for add operations
        if update_type not in ('add', 'ADD', None):
            self.skillbook.apply_update(update)
            return

        # Get existing skill contents for deduplication
        existing_contents = set()
        for skill in self.skillbook.skills():
            content = getattr(skill, 'content', '').strip().lower()
            if content:
                existing_contents.add(content)

        # Check if new skill is duplicate (simple content matching)
        new_content = getattr(update, 'content', '')
        if new_content:
            new_content_normalized = new_content.strip().lower()

            # Check for exact or very similar match
            is_duplicate = False
            for existing in existing_contents:
                # Exact match
                if new_content_normalized == existing:
                    is_duplicate = True
                    break
                # High overlap (>85% of words match)
                new_words = set(new_content_normalized.split())
                existing_words = set(existing.split())
                if new_words and existing_words:
                    overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
                    if overlap >= self.config.similarity_threshold:
                        is_duplicate = True
                        break

            if is_duplicate:
                self._stats['skills_deduplicated'] += 1
                logger.debug(f"Skipped duplicate skill: {new_content[:50]}...")
                return

        # Not a duplicate, apply the update
        self.skillbook.apply_update(update)

    def _atexit_handler(self) -> None:
        """Atexit handler to ensure skillbook is saved on process exit.

        This handler is registered via atexit.register() to ensure the
        skillbook is persisted even if the process exits unexpectedly.
        """
        try:
            self.shutdown()
        except Exception as e:
            # Don't let exceptions escape during process exit
            logger.debug(f"Error in atexit handler: {e}")

    def shutdown(self) -> None:
        """Gracefully shutdown the learning adapter.

        Stops the async worker, waits for pending tasks to complete,
        and saves the skillbook to disk. Should be called before
        process exit for clean shutdown.
        """
        if not self.enabled:
            return

        logger.debug("Shutting down ACE learning adapter...")

        # Signal worker to stop
        self._shutdown_event.set()

        # Wait for worker thread to finish with timeout
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=self.config.worker_timeout)
            if self._worker_thread.is_alive():
                logger.warning("ACE learning worker did not stop cleanly")

        # Save skillbook before exit
        self.save_skillbook()

        logger.info("ACE learning adapter shutdown complete")

    @property
    def enabled(self) -> bool:
        """Check if learning is enabled."""
        return self._learning_enabled

    def inject_context(self, prompt: str) -> str:
        """Add skillbook strategies to prompt.

        Thread-safe: Uses lock to prevent race conditions.
        Phase 5: Supports TOP-K skill injection by score (helpful - harmful).

        Args:
            prompt: Original prompt text

        Returns:
            Enhanced prompt with skillbook context appended,
            or original prompt if no skills or learning disabled.
        """
        if not self.enabled:
            return prompt

        inject_start = time.time()
        with self._skillbook_lock:
            try:
                skills = list(self.skillbook.skills())
                if not skills:
                    logger.debug("No skills in skillbook, returning original prompt")
                    return prompt

                # Phase 5: TOP-K skill injection by score
                top_k = self.config.top_k_skills if hasattr(self.config, 'top_k_skills') else 0
                total_skills = len(skills)

                if top_k > 0 and len(skills) > top_k:
                    # Sort by effectiveness score (helpful - harmful), highest first
                    skills_with_scores = [
                        (s, getattr(s, 'helpful', 0) - getattr(s, 'harmful', 0))
                        for s in skills
                    ]
                    skills_with_scores.sort(key=lambda x: x[1], reverse=True)
                    skills = [s for s, _ in skills_with_scores[:top_k]]
                    logger.debug(f"TOP-K filter: {top_k}/{total_skills} skills by score")

                    # Format TOP-K skills manually since we can't use wrap_skillbook_context with filtered skills
                    skill_lines = []
                    for skill in skills:
                        content = getattr(skill, 'content', str(skill))
                        section = getattr(skill, 'section', 'general')
                        helpful = getattr(skill, 'helpful', 0)
                        harmful = getattr(skill, 'harmful', 0)
                        skill_lines.append(f"- [{section}] {content} (score: {helpful - harmful})")

                    skillbook_context = "## Learned Strategies (TOP-K)\n" + "\n".join(skill_lines)
                else:
                    # Use ACE's wrap_skillbook_context for consistent formatting (all skills)
                    skillbook_context = wrap_skillbook_context(self.skillbook)

                enhanced = f"{prompt}\n\n{skillbook_context}"

                # Record telemetry
                inject_duration = (time.time() - inject_start) * 1000
                self._stats['inject_count'] += 1
                self._record_event(
                    LEARNING_EVENTS['INJECT'],
                    inject_duration,
                    success=True,
                    details={
                        'skills_injected': len(skills),
                        'total_skills': total_skills,
                        'top_k_enabled': top_k > 0,
                        'original_prompt_len': len(prompt),
                        'enhanced_prompt_len': len(enhanced),
                        'context_added_chars': len(skillbook_context),
                    }
                )

                logger.info(
                    f"Skillbook injected | skills={len(skills)}/{total_skills} | "
                    f"top_k={top_k if top_k > 0 else 'all'} | "
                    f"added_chars={len(skillbook_context)} | duration={inject_duration:.1f}ms"
                )
                return enhanced

            except Exception as e:
                inject_duration = (time.time() - inject_start) * 1000
                self._record_event(
                    LEARNING_EVENTS['INJECT'],
                    inject_duration,
                    success=False,
                    error=str(e)
                )
                logger.warning(f"Error injecting skillbook context: {e}")
                return prompt

    def learn_from_execution(
        self,
        task: str,
        output: str,
        success: bool,
        error: Optional[str] = None,
        execution_trace: str = "",
        iteration: int = 0
    ) -> None:
        """Learn from iteration execution.

        Non-blocking: If async_learning is enabled, queues the learning task
        for background processing. Otherwise processes synchronously.
        Thread-safe: Uses lock to prevent race conditions.

        Args:
            task: The prompt/task that was executed
            output: Agent output text
            success: Whether iteration succeeded
            error: Error message if failed
            execution_trace: Optional execution trace for analysis
            iteration: The iteration number (for telemetry)
        """
        if not self.enabled:
            return

        # Create learning task
        learning_task = LearningTask(
            task=task,
            output=output,
            success=success,
            error=error,
            execution_trace=execution_trace,
            iteration=iteration,
        )

        # If async learning is enabled and worker is running, queue the task
        if self.config.async_learning and self._worker_running:
            try:
                self._learning_queue.put_nowait(learning_task)
                self._stats['async_tasks_queued'] += 1
                logger.debug(
                    f"Queued learning task | iteration={iteration} | "
                    f"queue_size={self._learning_queue.qsize()}"
                )
            except queue.Full:
                logger.warning("Learning queue full, processing synchronously")
                self._process_learning_task(learning_task)
        else:
            # Process synchronously (blocking)
            self._process_learning_task(learning_task)

    def learn_from_rollback(
        self,
        failed_iterations: int,
        rollback_target: str,
        reason: str = ""
    ) -> None:
        """Learn from a checkpoint rollback event.

        Records the rollback as a learning opportunity to avoid
        repeating patterns that lead to failure.

        Args:
            failed_iterations: Number of failed iterations before rollback
            rollback_target: The target commit/checkpoint rolled back to
            reason: Why the rollback occurred
        """
        if not self.enabled:
            return

        self._stats['rollback_learnings'] += 1

        # Create a special learning task for rollback analysis
        rollback_context = f"""
## Rollback Event
A rollback was triggered after {failed_iterations} failed iterations.
Target: {rollback_target}
Reason: {reason}

## Analysis
This indicates a pattern that led to repeated failures. The agent should:
1. Identify what went wrong in the failed iterations
2. Avoid similar approaches in future attempts
3. Consider alternative strategies
"""

        learning_task = LearningTask(
            task="Analyze rollback event and extract failure patterns",
            output=rollback_context,
            success=False,
            error=reason,
            execution_trace=f"Rollback after {failed_iterations} failures to {rollback_target}",
            iteration=-1,  # Special marker for rollback learning
        )

        # Always process rollback learning synchronously (important insight)
        self._process_learning_task(learning_task)
        logger.info(
            f"Learned from rollback | failed_iterations={failed_iterations} | "
            f"target={rollback_target}"
        )

    def _prune_skills_if_needed(self) -> None:
        """Prune lowest-scoring skills if over max_skills limit.

        Called after learning to enforce the max_skills configuration.
        Removes skills with the lowest (helpful - harmful) score.
        """
        prune_start = time.time()
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
            pruned_ids = []
            for skill, score in skills_with_scores[:excess]:
                skill_id = getattr(skill, 'id', None) or getattr(skill, 'skill_id', None)
                if skill_id:
                    # Try to remove skill - method depends on ACE version
                    if hasattr(self.skillbook, 'remove_skill'):
                        self.skillbook.remove_skill(skill_id)
                        pruned_ids.append({'id': skill_id, 'score': score})
                    logger.debug(f"Pruned low-scoring skill: {skill_id} (score: {score})")

            # Record prune event
            prune_duration = (time.time() - prune_start) * 1000
            self._stats['skills_pruned'] += len(pruned_ids)
            self._record_event(
                LEARNING_EVENTS['PRUNE'],
                prune_duration,
                success=True,
                details={
                    'skills_before': len(skills),
                    'skills_pruned': len(pruned_ids),
                    'max_skills': self.config.max_skills,
                    'lowest_scores': [p['score'] for p in pruned_ids[:5]],  # First 5 scores
                }
            )
            logger.info(f"Pruned {excess} low-scoring skills to enforce max_skills={self.config.max_skills}")

        except Exception as e:
            prune_duration = (time.time() - prune_start) * 1000
            self._record_event(
                LEARNING_EVENTS['PRUNE'],
                prune_duration,
                success=False,
                error=str(e)
            )
            logger.debug(f"Skill pruning failed (non-critical): {e}")

    def save_skillbook(self) -> None:
        """Save skillbook to disk.

        Thread-safe: Uses lock to prevent race conditions.
        Called automatically on checkpoint and graceful shutdown.
        """
        if not self.enabled:
            return

        save_start = time.time()
        with self._skillbook_lock:
            try:
                path = Path(self.config.skillbook_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                self.skillbook.save_to_file(str(path))

                # Get file size for telemetry
                file_size = path.stat().st_size if path.exists() else 0
                skill_count = len(list(self.skillbook.skills()))

                save_duration = (time.time() - save_start) * 1000
                self._record_event(
                    LEARNING_EVENTS['SAVE'],
                    save_duration,
                    success=True,
                    details={
                        'path': str(path),
                        'skill_count': skill_count,
                        'file_size_bytes': file_size,
                    }
                )
                logger.debug(f"Saved skillbook to {path} | skills={skill_count} | size={file_size}B")

            except Exception as e:
                save_duration = (time.time() - save_start) * 1000
                self._record_event(
                    LEARNING_EVENTS['SAVE'],
                    save_duration,
                    success=False,
                    error=str(e)
                )
                logger.warning(f"Failed to save skillbook: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics including telemetry data.

        Returns:
            Dictionary with learning status, skillbook stats, and telemetry.
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
                    # Async worker status
                    "async_worker_running": self._worker_running,
                    "async_queue_size": self._learning_queue.qsize(),
                    # Telemetry stats
                    "telemetry": {
                        "reflections_count": self._stats['reflections_count'],
                        "skills_added": self._stats['skills_added'],
                        "skills_updated": self._stats['skills_updated'],
                        "skills_pruned": self._stats['skills_pruned'],
                        "skills_deduplicated": self._stats['skills_deduplicated'],
                        "inject_count": self._stats['inject_count'],
                        "errors_count": self._stats['errors_count'],
                        "total_learning_time_ms": self._stats['total_learning_time_ms'],
                        "events_recorded": len(self._events),
                        "async_tasks_queued": self._stats['async_tasks_queued'],
                        "async_tasks_processed": self._stats['async_tasks_processed'],
                        "rollback_learnings": self._stats['rollback_learnings'],
                    },
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

    def get_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent telemetry events.

        Args:
            limit: Maximum number of events to return (most recent first)

        Returns:
            List of event dictionaries, most recent first.
        """
        return [e.to_dict() for e in self._events[-limit:][::-1]]

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get a comprehensive telemetry summary.

        Returns:
            Dictionary with aggregated telemetry data suitable for monitoring.
        """
        if not self.enabled:
            return {"enabled": False}

        # Calculate event type counts
        event_counts: Dict[str, int] = {}
        for event in self._events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

        # Calculate success rate
        total_events = len(self._events)
        successful_events = sum(1 for e in self._events if e.success)
        success_rate = (successful_events / total_events * 100) if total_events > 0 else 0.0

        # Calculate average durations by event type
        duration_by_type: Dict[str, List[float]] = {}
        for event in self._events:
            if event.event_type not in duration_by_type:
                duration_by_type[event.event_type] = []
            duration_by_type[event.event_type].append(event.duration_ms)

        avg_durations = {
            event_type: sum(durations) / len(durations)
            for event_type, durations in duration_by_type.items()
        }

        return {
            "enabled": True,
            "summary": {
                "total_events": total_events,
                "successful_events": successful_events,
                "failed_events": total_events - successful_events,
                "success_rate_pct": round(success_rate, 2),
            },
            "event_counts": event_counts,
            "avg_duration_ms": avg_durations,
            "stats": self._stats.copy(),
        }


# Export ACE_AVAILABLE for external checks
__all__ = [
    "ACELearningAdapter",
    "LearningConfig",
    "LearningTask",
    "LearningEvent",
    "LEARNING_EVENTS",
    "ACE_AVAILABLE",
]
