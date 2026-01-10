# feat: ACE Framework Learning Loop Integration

## Overview

Integrate the Agentic Context Engine (ACE) framework into Ralph Orchestrator to enable **self-improving agent loops**. After each iteration, ACE analyzes what worked and what failed, then injects those learnings into the next iteration. This creates a continuous learning loop where Ralph gets smarter over time.

**Reference Implementation:** [kayba-ai/agentic-context-engine](https://github.com/kayba-ai/agentic-context-engine) - specifically the [claude-code-loop example](https://github.com/kayba-ai/agentic-context-engine/tree/main/examples/claude-code-loop).

---

## Problem Statement / Motivation

**Current State:** Ralph executes iterations in a loop but doesn't learn from execution history. Each iteration starts fresh without knowledge of what strategies worked or failed in previous iterations.

**With ACE Integration:**
- Ralph accumulates a "skillbook" of proven strategies
- Failed approaches are marked as harmful and deprioritized
- Successful patterns are reinforced across iterations
- The agent improves over time through execution feedback

**Business Value:**
- 17%+ improvement in task completion rates (per ACE research)
- Reduced token costs from avoiding repeated failures
- Better long-running task performance (4+ hour sessions)
- Institutional memory that persists across sessions

---

## Proposed Solution

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Ralph Orchestration Loop                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐    ┌──────────────────┐    ┌──────────────┐   │
│   │   Prompt    │───▶│  ACE Learning    │───▶│   Adapter    │   │
│   │   Manager   │    │  (inject skills) │    │  (execute)   │   │
│   └─────────────┘    └──────────────────┘    └──────┬───────┘   │
│                                                      │           │
│                                                      ▼           │
│   ┌─────────────┐    ┌──────────────────┐    ┌──────────────┐   │
│   │  Skillbook  │◀───│  ACE Learning    │◀───│   Response   │   │
│   │  (persist)  │    │  (reflect/learn) │    │   (output)   │   │
│   └─────────────┘    └──────────────────┘    └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Learning Cycle (per iteration)

1. **INJECT**: Add skillbook strategies to the prompt
2. **EXECUTE**: Adapter runs the enhanced prompt
3. **REFLECT**: Reflector analyzes execution outcome
4. **LEARN**: SkillManager updates skillbook
5. **PERSIST**: Save skillbook for next iteration

---

## Technical Approach

### Phase 1: Infrastructure Setup

**1.1 Create new branch from main**
```bash
git checkout main
git pull origin main
git checkout -b feat/ace-learning-loop
```

**1.2 Install ACE Framework dependency**
```bash
# Add to pyproject.toml under [project.dependencies]
pip install ace-framework
```

**1.3 Create learning module structure**
```
src/ralph_orchestrator/learning/
├── __init__.py           # Module exports
├── ace_adapter.py        # ACELearningAdapter class
└── config.py             # Learning-specific config dataclass
```

### Phase 2: Configuration

**2.1 Add to RalphConfig (main.py:198)**

```python
@dataclass
class RalphConfig:
    # ... existing fields ...

    # Learning configuration (ACE Framework)
    learning_enabled: bool = False
    learning_model: str = "claude-sonnet-4-5-20250929"  # Model for Reflector/SkillManager
    learning_skillbook_path: str = ".agent/skillbook/skillbook.json"
    learning_async: bool = True  # Run learning in background thread
    learning_max_skills: int = 100  # Maximum skills in skillbook
```

**2.2 Add to ralph.yml**

```yaml
# Learning configuration (ACE Framework)
# Enables self-improving agent loops that learn from execution feedback
learning:
  enabled: false                                    # Enable ACE learning
  model: claude-sonnet-4-5-20250929                # Model for reflection
  skillbook_path: .agent/skillbook/skillbook.json  # Skillbook storage
  async: true                                       # Background learning
  max_skills: 100                                   # Maximum skills
```

**2.3 Add CLI arguments**

```python
parser.add_argument(
    "--learning",
    action="store_true",
    help="Enable ACE learning loop (agent learns from each iteration)"
)

parser.add_argument(
    "--learning-model",
    type=str,
    default="claude-sonnet-4-5-20250929",
    help="Model for ACE learning (Reflector/SkillManager)"
)

parser.add_argument(
    "--skillbook-path",
    type=str,
    default=".agent/skillbook/skillbook.json",
    help="Path to skillbook file"
)
```

### Phase 3: ACE Learning Adapter

**File: `src/ralph_orchestrator/learning/ace_adapter.py`**

```python
"""ACE Learning Adapter for Ralph Orchestrator.

Wraps ACE Framework components to provide learning capabilities
for the orchestration loop.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ace import Skillbook, LiteLLMClient
from ace.roles import Reflector, SkillManager, AgentOutput
from ace.prompts_v2_1 import PromptManager
from ace.integrations.base import wrap_skillbook_context

logger = logging.getLogger('ralph-orchestrator.learning')


@dataclass
class LearningConfig:
    """Configuration for ACE learning."""
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

    Example:
        adapter = ACELearningAdapter(config)

        # Before iteration
        enhanced_prompt = adapter.inject_context(prompt)

        # Execute iteration...

        # After iteration
        adapter.learn_from_execution(prompt, response)
    """

    def __init__(self, config: LearningConfig):
        """Initialize ACE learning components.

        Args:
            config: Learning configuration
        """
        self.config = config
        self._learning_enabled = config.enabled

        if not config.enabled:
            logger.info("ACE learning disabled")
            return

        # Ensure skillbook directory exists
        skillbook_path = Path(config.skillbook_path)
        skillbook_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or create skillbook
        if skillbook_path.exists():
            self.skillbook = Skillbook.load_from_file(str(skillbook_path))
            logger.info(f"Loaded skillbook with {len(list(self.skillbook.skills()))} skills")
        else:
            self.skillbook = Skillbook()
            logger.info("Created new skillbook")

        # Initialize LLM client for ACE (separate from main adapter)
        self.llm = LiteLLMClient(
            model=config.model,
            max_tokens=config.max_tokens
        )

        # Initialize ACE components with v2.1 prompts
        prompt_mgr = PromptManager()
        self.reflector = Reflector(
            self.llm,
            prompt_template=prompt_mgr.get_reflector_prompt()
        )
        self.skill_manager = SkillManager(
            self.llm,
            prompt_template=prompt_mgr.get_skill_manager_prompt()
        )

        logger.info(f"ACE learning initialized with model: {config.model}")

    @property
    def enabled(self) -> bool:
        """Check if learning is enabled."""
        return self._learning_enabled

    def inject_context(self, prompt: str) -> str:
        """Add skillbook strategies to prompt.

        Args:
            prompt: Original prompt text

        Returns:
            Enhanced prompt with skillbook context
        """
        if not self.enabled:
            return prompt

        if not self.skillbook.skills():
            logger.debug("No skills in skillbook, returning original prompt")
            return prompt

        # Use ACE's wrap_skillbook_context for consistent formatting
        skillbook_context = wrap_skillbook_context(self.skillbook)
        enhanced = f"{prompt}\n\n{skillbook_context}"

        skill_count = len(list(self.skillbook.skills()))
        logger.debug(f"Injected {skill_count} skills into prompt")

        return enhanced

    def learn_from_execution(
        self,
        task: str,
        output: str,
        success: bool,
        error: Optional[str] = None,
        execution_trace: str = ""
    ) -> None:
        """Learn from iteration execution.

        Args:
            task: The prompt/task that was executed
            output: Agent output text
            success: Whether iteration succeeded
            error: Error message if failed
            execution_trace: Optional execution trace for analysis
        """
        if not self.enabled:
            return

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

            # Log learning
            skill_count = len(list(self.skillbook.skills()))
            logger.info(f"ACE learning complete. Skillbook now has {skill_count} skills")

        except Exception as e:
            logger.warning(f"ACE learning error (non-fatal): {e}")

    def save_skillbook(self) -> None:
        """Save skillbook to disk."""
        if not self.enabled:
            return

        try:
            path = Path(self.config.skillbook_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self.skillbook.save_to_file(str(path))
            logger.debug(f"Saved skillbook to {path}")
        except Exception as e:
            logger.warning(f"Failed to save skillbook: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        if not self.enabled:
            return {"enabled": False}

        skills = list(self.skillbook.skills())
        return {
            "enabled": True,
            "model": self.config.model,
            "skillbook_path": self.config.skillbook_path,
            "skill_count": len(skills),
            "top_skills": [
                {
                    "content": s.content[:100],
                    "helpful": s.helpful,
                    "harmful": s.harmful
                }
                for s in sorted(
                    skills,
                    key=lambda x: x.helpful - x.harmful,
                    reverse=True
                )[:5]
            ]
        }
```

**File: `src/ralph_orchestrator/learning/__init__.py`**

```python
"""ACE Learning module for Ralph Orchestrator."""

from .ace_adapter import ACELearningAdapter, LearningConfig

__all__ = ["ACELearningAdapter", "LearningConfig"]
```

### Phase 4: Orchestrator Integration

**Modify `orchestrator.py`**

**4.1 Add imports (after line 25)**

```python
# Learning (ACE Framework)
from .learning import ACELearningAdapter, LearningConfig
```

**4.2 Initialize learning in `__init__` (after line 158)**

```python
        # Initialize ACE learning if enabled
        self.learning_adapter = None
        if hasattr(prompt_file_or_config, 'learning_enabled') and prompt_file_or_config.learning_enabled:
            learning_config = LearningConfig(
                enabled=True,
                model=getattr(prompt_file_or_config, 'learning_model', 'claude-sonnet-4-5-20250929'),
                skillbook_path=getattr(prompt_file_or_config, 'learning_skillbook_path', '.agent/skillbook/skillbook.json'),
                async_learning=getattr(prompt_file_or_config, 'learning_async', True),
            )
            self.learning_adapter = ACELearningAdapter(learning_config)
            logger.info("ACE learning loop enabled")
```

**4.3 Modify `_aexecute_iteration` (around line 593)**

```python
    async def _aexecute_iteration(self) -> bool:
        """Execute a single iteration asynchronously."""
        # Get the current prompt
        prompt = self.context_manager.get_prompt()

        # INJECT: Add skillbook context if learning enabled
        if self.learning_adapter and self.learning_adapter.enabled:
            prompt = self.learning_adapter.inject_context(prompt)

        # Extract tasks from prompt if task queue is empty
        if not self.task_queue and not self.current_task:
            self._extract_tasks_from_prompt(prompt)

        # Update current task status
        self._update_current_task('in_progress')

        # Try primary adapter with prompt file path
        response = await self.current_adapter.aexecute(
            prompt,
            prompt_file=str(self.prompt_file),
            verbose=self.verbose
        )

        # ... existing fallback logic ...

        # Store and log the response output
        if response.success and response.output:
            self.last_response_output = response.output
            # ... existing logging ...

        # LEARN: Update skillbook based on execution
        if self.learning_adapter and self.learning_adapter.enabled:
            self.learning_adapter.learn_from_execution(
                task=self.context_manager.get_prompt()[:1000],
                output=response.output or "",
                success=response.success,
                error=None if response.success else "Iteration failed",
                execution_trace=""
            )

        # ... rest of existing method ...

        return response.success
```

**4.4 Save skillbook on checkpoint (around line 720)**

```python
    async def _create_checkpoint(self):
        """Create a git checkpoint asynchronously."""
        # Save skillbook before checkpoint
        if self.learning_adapter:
            self.learning_adapter.save_skillbook()

        # ... existing checkpoint logic ...
```

**4.5 Add learning stats to summary (around line 826)**

```python
            # Learning stats (if enabled)
            "learning": self.learning_adapter.get_stats() if self.learning_adapter else {"enabled": False},
```

### Phase 5: Testing & Validation

**5.1 Unit Tests**

**File: `tests/test_learning.py`**

```python
"""Tests for ACE learning integration."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from ralph_orchestrator.learning import ACELearningAdapter, LearningConfig


class TestACELearningAdapter:
    """Test ACE learning adapter."""

    def test_disabled_by_default(self):
        """Learning should be disabled by default."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)
        assert not adapter.enabled

    def test_inject_context_when_disabled(self):
        """Should return original prompt when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        prompt = "Test prompt"
        result = adapter.inject_context(prompt)
        assert result == prompt

    @patch('ralph_orchestrator.learning.ace_adapter.LiteLLMClient')
    @patch('ralph_orchestrator.learning.ace_adapter.Skillbook')
    def test_inject_context_with_skills(self, mock_skillbook_class, mock_llm_class):
        """Should inject skillbook context when enabled with skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock skillbook with skills
            mock_skillbook = Mock()
            mock_skill = Mock()
            mock_skill.content = "Test strategy"
            mock_skill.helpful = 5
            mock_skill.harmful = 0
            mock_skillbook.skills.return_value = [mock_skill]
            mock_skillbook_class.return_value = mock_skillbook

            config = LearningConfig(
                enabled=True,
                skillbook_path=f"{tmpdir}/skillbook.json"
            )

            with patch('ralph_orchestrator.learning.ace_adapter.wrap_skillbook_context') as mock_wrap:
                mock_wrap.return_value = "## Learned Strategies\n- Test strategy"
                adapter = ACELearningAdapter(config)
                adapter.skillbook = mock_skillbook

                prompt = "Test prompt"
                result = adapter.inject_context(prompt)

                assert "Test prompt" in result
                assert "Learned Strategies" in result

    def test_get_stats_when_disabled(self):
        """Should return minimal stats when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        stats = adapter.get_stats()
        assert stats == {"enabled": False}
```

**5.2 Integration Test**

```python
"""Integration test for learning loop."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import tempfile

from ralph_orchestrator.orchestrator import RalphOrchestrator
from ralph_orchestrator.main import RalphConfig


@pytest.mark.asyncio
async def test_learning_loop_integration():
    """Test full learning loop with mock adapter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test prompt
        prompt_file = f"{tmpdir}/PROMPT.md"
        with open(prompt_file, "w") as f:
            f.write("Test task: Add a function")

        # Create config with learning enabled
        config = RalphConfig(
            prompt_file=prompt_file,
            max_iterations=2,
            learning_enabled=True,
            learning_skillbook_path=f"{tmpdir}/skillbook.json"
        )

        with patch('ralph_orchestrator.orchestrator.ClaudeAdapter') as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter.available = True
            mock_adapter.name = "claude"
            mock_adapter.aexecute = AsyncMock(return_value=Mock(
                success=True,
                output="Function added successfully",
                tokens_used=100
            ))
            mock_adapter_class.return_value = mock_adapter

            orchestrator = RalphOrchestrator(config)

            # Verify learning adapter initialized
            assert orchestrator.learning_adapter is not None
            assert orchestrator.learning_adapter.enabled

            # Run one iteration
            orchestrator.max_iterations = 1
            # Would run: await orchestrator.arun()
```

---

## Acceptance Criteria

### Functional Requirements
- [ ] Learning can be enabled via CLI `--learning` flag
- [ ] Learning can be enabled via ralph.yml `learning.enabled: true`
- [ ] Skillbook persists to `.agent/skillbook/skillbook.json`
- [ ] Skillbook context injected into prompts when skills exist
- [ ] Reflector analyzes iteration success/failure
- [ ] SkillManager updates skillbook after each iteration
- [ ] Learning stats included in final summary
- [ ] Skillbook saved on checkpoint

### Non-Functional Requirements
- [ ] Learning doesn't block iteration execution (async mode)
- [ ] Learning failure doesn't crash orchestrator (graceful degradation)
- [ ] All existing tests still pass
- [ ] No breaking changes to CLI or config

### Quality Gates
- [ ] Unit tests for ACELearningAdapter
- [ ] Integration test with mock adapter
- [ ] Manual validation with real Claude execution
- [ ] Documentation updated (README, ralph.yml)

---

## Dependencies & Prerequisites

**Required:**
- Python 3.11+
- ace-framework package (pip install)
- ANTHROPIC_API_KEY or OPENAI_API_KEY for learning model

**Related:**
- [ACE Framework](https://github.com/kayba-ai/agentic-context-engine) - v0.3.0+
- [LiteLLM](https://github.com/BerriAI/litellm) - for model abstraction

---

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ACE API changes | Low | Medium | Pin ace-framework version |
| LLM costs increase | Medium | Low | Use cheaper model for learning (sonnet) |
| Skillbook corruption | Low | High | Backup skillbook on checkpoint |
| Learning slows iteration | Medium | Medium | Use async learning by default |

---

## Future Considerations

1. **Skill Deduplication**: Add embedding-based deduplication when skillbook grows large
2. **Multi-Project Skills**: Share skillbooks across projects
3. **Skill Categories**: Organize skills by domain (coding, testing, debugging)
4. **Learning Analytics**: Dashboard for viewing skill evolution over time
5. **Custom Reflectors**: Domain-specific reflection prompts

---

## References & Research

### Internal References
- `src/ralph_orchestrator/orchestrator.py:593` - _aexecute_iteration method
- `src/ralph_orchestrator/main.py:198` - RalphConfig dataclass
- `ralph.yml` - Configuration file structure

### External References
- [ACE Framework Documentation](https://github.com/kayba-ai/agentic-context-engine/blob/main/docs/COMPLETE_GUIDE_TO_ACE.md)
- [Claude Code Loop Example](https://github.com/kayba-ai/agentic-context-engine/tree/main/examples/claude-code-loop)
- [ACE Research Paper (arXiv)](https://arxiv.org/abs/2510.04618)

### Related Work
- ACE's ACEClaudeCode integration: `ace/integrations/claude_code.py`
- Example loop implementation: `examples/claude-code-loop/ace_loop.py`

---

## Implementation Phases Summary

| Phase | Description | Estimated Effort | Files Changed |
|-------|-------------|-----------------|---------------|
| 1 | Infrastructure Setup | 30 min | pyproject.toml, new module |
| 2 | Configuration | 1 hour | main.py, ralph.yml |
| 3 | ACE Adapter | 2 hours | learning/ace_adapter.py |
| 4 | Orchestrator Integration | 1 hour | orchestrator.py |
| 5 | Testing & Validation | 2 hours | tests/test_learning.py |

**Total Estimated Effort:** ~6 hours

---

## SpecFlow Analysis - Gaps & Edge Cases

### Critical Issues (Must Address Before Implementation)

**1. Async Learning Race Conditions**
- The spec shows `learning_async: bool = True` but provides no implementation
- Concurrent skillbook access could corrupt data
- **Resolution**: Use `threading.Lock()` around skillbook operations
- **Code Addition**:
```python
self._skillbook_lock = threading.Lock()

def learn_from_execution(self, ...):
    with self._skillbook_lock:
        # ... learning logic ...
```

**2. ACE Framework Import Failure**
- If `ace-framework` not installed, imports will raise `ImportError`
- **Resolution**: Make ACE an optional dependency with graceful degradation
- **Code Addition** (at top of ace_adapter.py):
```python
try:
    from ace import Skillbook, LiteLLMClient
    from ace.roles import Reflector, SkillManager, AgentOutput
    ACE_AVAILABLE = True
except ImportError:
    ACE_AVAILABLE = False
    logger.warning("ace-framework not installed. Learning disabled.")
```

**3. Configuration Precedence**
- CLI vs YAML vs defaults not specified
- **Resolution**: CLI > YAML > Defaults (standard pattern)
- Add to documentation and validate in code

**4. Graceful Shutdown Skillbook Save**
- Ctrl+C may lose recent learnings if only checkpoint saves skillbook
- **Resolution**: Add `save_skillbook()` to `_emergency_cleanup()`
- **Code Addition** (in orchestrator.py):
```python
async def _emergency_cleanup(self) -> None:
    if self.learning_adapter:
        self.learning_adapter.save_skillbook()
    # ... existing cleanup ...
```

**5. Learning Model API Errors**
- Rate limits, timeouts, 500 errors need defined behavior
- **Resolution**: Log warning, skip learning for this iteration, continue
- Already handled in try/except, but add retry logic for rate limits

### Important Issues (Address During Implementation)

**6. Config Field Naming**
- YAML uses `async: true` but Python reserved word
- **Resolution**: Rename to `async_learning` in YAML
```yaml
learning:
  async_learning: true  # Not 'async'
```

**7. Learning Cost Tracking**
- Learning uses separate API calls not tracked in `max_cost`
- **Resolution**: Track learning costs separately and include in summary
- Add `learning_tokens_used` and `learning_cost` to metrics

**8. max_skills Enforcement**
- `learning_max_skills: int = 100` defined but not implemented
- **Resolution**: Add skill pruning when limit reached
- Prune skills with lowest `helpful - harmful` score

**9. Execution Trace Content**
- Currently passing empty string `""`
- **Resolution**: Pass actual execution trace from adapter output
```python
execution_trace=response.output[:2000] if hasattr(response, 'output') else ""
```

**10. Skillbook Location & Git**
- `.agent/skillbook/` may be gitignored
- **Resolution**: Document in README that skillbooks are personal by default
- Add option for shared skillbook path outside .agent/

### Edge Case Handling

| Edge Case | Behavior |
|-----------|----------|
| Empty skillbook | Return original prompt unchanged |
| Corrupted skillbook.json | Log error, create new skillbook, backup corrupted file |
| Learning model unavailable | Log warning, disable learning for session |
| Iteration timeout | Treat as failure, include timeout in feedback |
| max_skills reached | Prune lowest-scoring skill before adding new one |
| Concurrent skillbook access | Use threading.Lock() for all operations |
| Prompt too long with skills | Skills injected at end may be truncated; document limitation |

### Testing Requirements (Updated)

- [ ] Test empty skillbook initialization
- [ ] Test corrupted skillbook recovery
- [ ] Test API failure graceful degradation
- [ ] Test async learning thread safety
- [ ] Test CLI > YAML > defaults precedence
- [ ] Test graceful shutdown skillbook save
- [ ] Test max_skills pruning behavior
- [ ] Test learning cost tracking

---

*Created: 2026-01-09*
*Updated: 2026-01-09 (SpecFlow analysis integrated)*
*Status: Ready for Implementation*
*Branch: feat/ace-learning-loop*
