<research>
<summary>
# ACE Framework Documentation Research

## Executive Summary

The Agentic Context Engineering (ACE) Framework is a three-agent architecture for enabling AI agents to learn from their execution experiences and improve over time. It implements a learning loop pattern: INJECT → EXECUTE → LEARN (Reflect + Update). The framework stores learned strategies in a Skillbook—a persistent JSON structure containing categorized skills with effectiveness metrics.

## Key Integration Points for RALPH

1. **Skillbook Context Injection**: Use `skillbook.as_prompt()` to generate TOON-encoded context for LLM prompts
2. **Learning Trigger**: After each iteration, call Reflector.reflect() with execution results
3. **Skill Updates**: SkillManager processes reflections into ADD/UPDATE/TAG/REMOVE operations
4. **Async Learning**: Use AsyncLearningPipeline for non-blocking learning (parallel Reflectors, serialized SkillManager)
5. **API Key Handling**: LiteLLMClient uses environment variables (ANTHROPIC_API_KEY, OPENAI_API_KEY) - must be explicitly passed to subprocesses

## Performance Results

- +17.1% improvement on AppWorld benchmark
- +8.6% improvement on FiNER benchmark
- 86.9% lower adaptation latency vs fine-tuning
- v2.1 prompts show +17% success rate over v1.0
</summary>

<findings>

## 1. Core Architecture

### Three-Agent System

The ACE Framework implements a separation of concerns across three specialized agents:

#### 1.1 Agent (Your Existing Agent)
- The primary task executor (e.g., RALPH's ClaudeAdapter or ACPAdapter)
- Receives skillbook context as part of its system prompt
- Executes tasks and produces outputs that become learning material

#### 1.2 Reflector
- Analyzes agent execution after task completion
- Performs structured reflection including:
  - Error identification
  - Root cause analysis
  - Correct approach determination
  - Key insight extraction
  - Skill tagging (marks existing skills as helpful/harmful/neutral)
- Outputs `ReflectorOutput` with extracted learnings

```python
@dataclass
class ReflectorOutput:
    reasoning: str
    error_identification: str
    root_cause_analysis: str
    correct_approach: str
    key_insight: str
    extracted_learnings: List[ExtractedLearning]
    skill_tags: List[SkillTag]
```

#### 1.3 SkillManager
- Processes Reflector output into skillbook updates
- Performs four update operations:
  - **ADD**: Create new skill with unique ID
  - **UPDATE**: Modify existing skill content
  - **TAG**: Increment helpful/harmful/neutral counters
  - **REMOVE**: Soft-delete or hard-delete skills
- Handles skill deduplication via embeddings

```python
@dataclass
class UpdateOperation:
    operation: Literal["ADD", "UPDATE", "TAG", "REMOVE"]
    skill_id: Optional[str]  # Required for UPDATE, TAG, REMOVE
    section: Optional[str]   # Required for ADD
    content: Optional[str]   # Required for ADD, UPDATE
    tag: Optional[Literal["helpful", "harmful", "neutral"]]  # For TAG
```

### Learning Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                     INJECT PHASE                            │
│  1. Load skillbook from persistent storage                  │
│  2. Generate TOON-encoded context via skillbook.as_prompt() │
│  3. Inject into agent's system prompt                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     EXECUTE PHASE                           │
│  4. Agent executes task with skillbook context              │
│  5. Capture AgentOutput (reasoning, final_answer, skills)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      LEARN PHASE                            │
│  6. Reflector.reflect() analyzes execution                  │
│  7. SkillManager.update_skills() modifies skillbook         │
│  8. Save skillbook to persistent storage                    │
└─────────────────────────────────────────────────────────────┘
```

## 2. Skillbook System

### Skill Data Structure

```python
@dataclass
class Skill:
    id: str                                    # Unique identifier (UUID or custom)
    section: str                               # Category/grouping
    content: str                               # The actual strategy/knowledge
    helpful: int = 0                           # Times marked helpful
    harmful: int = 0                           # Times marked harmful
    neutral: int = 0                           # Times marked neutral
    embedding: Optional[List[float]] = None   # For deduplication
    status: Literal["active", "invalid"] = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Skillbook JSON Structure

```json
{
  "version": "1.0",
  "skills": [
    {
      "id": "skill_abc123",
      "section": "error_handling",
      "content": "When encountering rate limits, implement exponential backoff starting at 1 second",
      "helpful": 5,
      "harmful": 0,
      "neutral": 2,
      "status": "active"
    }
  ],
  "metadata": {
    "created_at": "2024-01-15T10:30:00Z",
    "last_updated": "2024-01-16T14:45:00Z",
    "total_skills": 42
  }
}
```

### TOON Encoding Format

Skills are encoded in a tab-delimited format for token efficiency:

```
# SKILLBOOK - LEARNED STRATEGIES

## Section: error_handling
ID	Content	Helpful	Harmful	Neutral
skill_001	When encountering rate limits...	5	0	2
skill_002	Always validate API responses...	8	1	0

## Section: code_patterns
ID	Content	Helpful	Harmful	Neutral
skill_003	Use async/await for I/O bound...	12	0	3
```

### Skill Effectiveness Calculation

```python
def effectiveness_score(skill: Skill) -> float:
    total = skill.helpful + skill.harmful + skill.neutral
    if total == 0:
        return 0.0
    return (skill.helpful - skill.harmful) / total
```

Skills with negative effectiveness scores are candidates for removal.

## 3. Async Learning Pipeline

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AsyncLearningPipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Task Queue      │───▶│ Reflector Pool  │                │
│  │ (Thread-safe)   │    │ (Parallel)      │                │
│  └─────────────────┘    └────────┬────────┘                │
│                                  │                          │
│                                  ▼                          │
│                         ┌─────────────────┐                │
│                         │ Reflection Queue│                │
│                         └────────┬────────┘                │
│                                  │                          │
│                                  ▼                          │
│                         ┌─────────────────┐                │
│                         │ SkillManager    │                │
│                         │ (Serialized)    │                │
│                         └────────┬────────┘                │
│                                  │                          │
│                                  ▼                          │
│                         ┌─────────────────┐                │
│                         │ ThreadSafe      │                │
│                         │ Skillbook       │                │
│                         └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Thread Safety

```python
class ThreadSafeSkillbook:
    """Lock-free reads, locked writes using RLock"""

    def __init__(self, skillbook: Skillbook):
        self._skillbook = skillbook
        self._lock = threading.RLock()

    # Read operations - no lock needed
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self._skillbook.get_skill(skill_id)

    def as_prompt(self) -> str:
        return self._skillbook.as_prompt()

    # Write operations - require lock
    def apply_update(self, update: UpdateBatch) -> None:
        with self._lock:
            self._skillbook.apply_update(update)
```

### Pipeline Configuration

```python
pipeline = AsyncLearningPipeline(
    skillbook=skillbook,
    reflector=reflector,
    skill_manager=skill_manager,
    max_reflector_workers=3,      # Parallel reflection threads
    reflection_queue_size=100,    # Buffer for reflections
    learning_timeout=30.0,        # Seconds before timeout
)
```

## 4. LiteLLM Integration

### Client Configuration

```python
from ace.llm import LiteLLMClient

client = LiteLLMClient(
    model="claude-opus-4-5-20251101",  # Or any LiteLLM-supported model
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # Explicit key passing
    temperature=0.7,
    max_tokens=4096,
)
```

### Supported Providers

LiteLLM supports 100+ providers including:
- OpenAI (gpt-4o, gpt-4o-mini)
- Anthropic (claude-opus-4-5-20251101, claude-sonnet-4-20250514)
- Azure OpenAI
- Google Gemini
- AWS Bedrock
- Local models via Ollama

### API Key Environment Variables

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
OPENAI_API_KEY=sk-...

# Azure
AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
```

**CRITICAL FOR RALPH**: Environment variables must be explicitly passed to subprocesses. The current ace_adapter.py bug stems from not passing these variables through the process hierarchy.

## 5. Integration Patterns

### Pattern 1: Direct Integration (Recommended for RALPH)

```python
class ACELearningWrapper:
    """Wraps existing agent with ACE learning capabilities"""

    def __init__(
        self,
        skillbook_path: str,
        reflector_model: str = "gpt-4o-mini",
        skill_manager_model: str = "gpt-4o-mini",
        async_learning: bool = True,
    ):
        self.skillbook = Skillbook.load_from_file(skillbook_path)
        self.reflector = Reflector(LiteLLMClient(model=reflector_model))
        self.skill_manager = SkillManager(LiteLLMClient(model=skill_manager_model))

        if async_learning:
            self.pipeline = AsyncLearningPipeline(
                skillbook=ThreadSafeSkillbook(self.skillbook),
                reflector=self.reflector,
                skill_manager=self.skill_manager,
            )
            self.pipeline.start()

    def inject_context(self, base_prompt: str) -> str:
        """Add skillbook context to agent prompt"""
        skillbook_context = self.skillbook.as_prompt()
        return f"{base_prompt}\n\n{skillbook_context}"

    def learn_from_execution(
        self,
        question: str,
        agent_output: AgentOutput,
        ground_truth: Optional[str] = None,
    ) -> None:
        """Trigger learning after execution"""
        if self.pipeline:
            task = LearningTask(
                question=question,
                agent_output=agent_output,
                ground_truth=ground_truth,
            )
            self.pipeline.submit(task)
        else:
            # Synchronous learning
            reflection = self.reflector.reflect(
                question=question,
                agent_output=agent_output,
                skillbook=self.skillbook,
                ground_truth=ground_truth,
            )
            self.skill_manager.update_skills(
                reflection=reflection,
                skillbook=self.skillbook,
                question_context=question,
            )

    def save(self, path: str) -> None:
        """Persist skillbook to disk"""
        if self.pipeline:
            self.pipeline.wait_for_completion()
        self.skillbook.save_to_file(path)
```

### Pattern 2: Claude Code Integration (Reference Implementation)

```python
from ace.integrations.claude_code import ACEClaudeCode

ace = ACEClaudeCode(
    working_dir="/path/to/project",
    ace_model="gpt-4o-mini",
    skillbook_path=".agent/skillbook.json",
    is_learning=True,
    async_learning=True,
    timeout=600,
)

# Execute task with learning
result = ace.run(
    task="Implement user authentication",
    context="Using JWT tokens with refresh rotation",
)

# Save learned skills
ace.save_skillbook(".agent/skillbook.json")
```

### Pattern 3: REST API Integration

```python
from ace import ACEServer

server = ACEServer(
    skillbook_path="skillbook.json",
    reflector_model="gpt-4o-mini",
)

# POST /inject - Get skillbook context
# POST /learn - Submit execution for learning
# GET /skills - List all skills
# POST /skills - Add manual skill
```

## 6. Skill Deduplication

### Configuration

```python
from ace.skillbook import DeduplicationConfig

config = DeduplicationConfig(
    enabled=True,
    similarity_threshold=0.85,      # Skills above this similarity are merged
    embedding_model="text-embedding-3-small",
    batch_size=100,                 # Process embeddings in batches
)

skillbook = Skillbook(deduplication_config=config)
```

### Deduplication Process

1. When adding a new skill, compute its embedding
2. Compare against existing skill embeddings using cosine similarity
3. If similarity > threshold:
   - Merge skills (combine effectiveness counts)
   - Keep the more comprehensive content
4. Store embedding for future comparisons

### Embedding Storage

```json
{
  "id": "skill_abc123",
  "content": "Always validate API responses...",
  "embedding": [0.023, -0.156, 0.089, ...],  // 1536 dimensions
  "helpful": 8,
  "harmful": 1
}
```

## 7. Insight Levels

ACE supports three insight granularities:

### Micro (Single Interaction)
- Learn from individual tool calls or responses
- Fine-grained skill extraction
- Use for: Detailed error recovery patterns

### Meso (Full Agent Run)
- Learn from complete task execution
- Holistic strategy extraction
- Use for: Overall approach patterns (recommended for RALPH)

### Macro (Cross-Run Patterns)
- Learn from multiple runs over time
- Meta-strategy extraction
- Use for: Project-wide conventions

## 8. v2.1 Prompt Improvements

The v2.1 prompts provide significant improvements:

### Reflector v2.1 Changes
- More structured error analysis
- Better root cause identification
- Clearer learning extraction format
- +17% success rate vs v1.0

### SkillManager v2.1 Changes
- Smarter deduplication decisions
- Better section categorization
- More conservative removal thresholds
- Improved UPDATE vs ADD decisions

### Prompt Selection

```python
from ace.prompts import REFLECTOR_PROMPT_V2_1, SKILL_MANAGER_PROMPT_V2_1

reflector = Reflector(
    client=client,
    system_prompt=REFLECTOR_PROMPT_V2_1,
)
```

</findings>

<configuration_reference>

## Configuration Options Reference

### Skillbook Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `version` | str | "1.0" | Skillbook format version |
| `max_skills` | int | 1000 | Maximum skills before pruning |
| `prune_threshold` | float | -0.3 | Effectiveness score below which to prune |
| `deduplication_enabled` | bool | True | Enable embedding-based dedup |
| `similarity_threshold` | float | 0.85 | Cosine similarity for dedup |

### Reflector Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | str | "gpt-4o-mini" | LLM model for reflection |
| `temperature` | float | 0.7 | Sampling temperature |
| `max_tokens` | int | 4096 | Maximum response tokens |
| `include_ground_truth` | bool | True | Include expected output in reflection |
| `timeout` | float | 30.0 | Seconds before timeout |

### SkillManager Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | str | "gpt-4o-mini" | LLM model for skill management |
| `conservative_removal` | bool | True | Require high harmful count to remove |
| `auto_section` | bool | True | Automatically categorize new skills |
| `merge_duplicates` | bool | True | Merge instead of reject duplicates |

### AsyncLearningPipeline Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_reflector_workers` | int | 3 | Parallel reflection threads |
| `reflection_queue_size` | int | 100 | Pending reflection buffer |
| `learning_timeout` | float | 30.0 | Per-task timeout |
| `error_handler` | Callable | None | Custom error handling |
| `on_skill_update` | Callable | None | Callback after updates |

### LiteLLMClient Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | str | Required | LiteLLM model identifier |
| `api_key` | str | None | Explicit API key (recommended) |
| `api_base` | str | None | Custom API endpoint |
| `temperature` | float | 0.7 | Sampling temperature |
| `max_tokens` | int | 4096 | Maximum response tokens |
| `timeout` | float | 60.0 | Request timeout |
| `num_retries` | int | 3 | Retry count on failure |

### Claude Code Integration Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `working_dir` | str | Required | Project directory |
| `ace_model` | str | "gpt-4o-mini" | Model for ACE operations |
| `skillbook_path` | str | ".agent/skillbook.json" | Skillbook location |
| `is_learning` | bool | True | Enable learning |
| `async_learning` | bool | False | Use async pipeline |
| `timeout` | int | 600 | Execution timeout (seconds) |
| `max_turns` | int | None | Maximum conversation turns |

</configuration_reference>

<code_examples>

## Implementation Examples

### Example 1: Basic RALPH Integration

```python
# src/ralph_orchestrator/learning/ace_adapter.py

import os
from typing import Optional, Dict, Any
from ace.skillbook import Skillbook
from ace.roles import Reflector, SkillManager, AgentOutput
from ace.llm import LiteLLMClient
from ace.async_learning import AsyncLearningPipeline, ThreadSafeSkillbook, LearningTask

class ACELearningAdapter:
    """ACE Framework integration for RALPH orchestrator"""

    def __init__(
        self,
        skillbook_path: str = ".agent/skillbook/skillbook.json",
        ace_model: str = "gpt-4o-mini",
        async_learning: bool = True,
        api_key: Optional[str] = None,
    ):
        self.skillbook_path = skillbook_path
        self.async_learning = async_learning

        # CRITICAL: Explicitly pass API key
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key required for ACE learning")

        # Initialize LLM client with explicit key
        self.client = LiteLLMClient(
            model=ace_model,
            api_key=api_key,
        )

        # Load or create skillbook
        if os.path.exists(skillbook_path):
            self.skillbook = Skillbook.load_from_file(skillbook_path)
        else:
            self.skillbook = Skillbook()

        # Initialize reflection components
        self.reflector = Reflector(client=self.client)
        self.skill_manager = SkillManager(client=self.client)

        # Setup async pipeline if enabled
        self.pipeline = None
        if async_learning:
            self.pipeline = AsyncLearningPipeline(
                skillbook=ThreadSafeSkillbook(self.skillbook),
                reflector=self.reflector,
                skill_manager=self.skill_manager,
                max_reflector_workers=3,
            )
            self.pipeline.start()

    def inject_context(self, base_prompt: str) -> str:
        """Inject skillbook context into agent prompt"""
        if not self.skillbook.skills:
            return base_prompt

        skillbook_context = self.skillbook.as_prompt()
        return f"""{base_prompt}

<learned_strategies>
The following strategies have been learned from previous executions.
Use them to guide your approach when applicable.

{skillbook_context}
</learned_strategies>"""

    def learn_from_execution(
        self,
        task: str,
        output: str,
        tool_calls: list,
        success: bool,
        feedback: Optional[str] = None,
    ) -> None:
        """Learn from completed iteration"""
        # Build AgentOutput structure
        agent_output = AgentOutput(
            reasoning=output,
            final_answer=output,
            skill_ids=[],  # Skills used (if tracked)
            raw={"tool_calls": tool_calls, "success": success},
        )

        if self.pipeline:
            # Async learning
            learning_task = LearningTask(
                question=task,
                agent_output=agent_output,
                feedback=feedback if not success else None,
            )
            self.pipeline.submit(learning_task)
        else:
            # Synchronous learning
            reflection = self.reflector.reflect(
                question=task,
                agent_output=agent_output,
                skillbook=self.skillbook,
                feedback=feedback if not success else None,
            )
            self.skill_manager.update_skills(
                reflection=reflection,
                skillbook=self.skillbook,
                question_context=task,
            )

    def save(self) -> None:
        """Persist skillbook to disk"""
        if self.pipeline:
            self.pipeline.wait_for_completion(timeout=30.0)

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.skillbook_path), exist_ok=True)
        self.skillbook.save_to_file(self.skillbook_path)

    def shutdown(self) -> None:
        """Clean shutdown of async pipeline"""
        if self.pipeline:
            self.pipeline.stop(wait=True, timeout=30.0)
        self.save()
```

### Example 2: Integration with RALPH Orchestrator

```python
# In src/ralph_orchestrator/orchestrator.py

class RalphOrchestrator:
    def __init__(self, config: OrchestratorConfig):
        # ... existing initialization ...

        # Initialize ACE learning if enabled
        self.ace_adapter = None
        if config.ace_enabled:
            from .learning.ace_adapter import ACELearningAdapter
            self.ace_adapter = ACELearningAdapter(
                skillbook_path=config.skillbook_path,
                ace_model=config.ace_model,
                async_learning=config.ace_async,
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
            )

    def _enhance_prompt_with_instructions(self, prompt: str) -> str:
        """Enhanced to include ACE skillbook context"""
        enhanced = super()._enhance_prompt_with_instructions(prompt)

        if self.ace_adapter:
            enhanced = self.ace_adapter.inject_context(enhanced)

        return enhanced

    async def _aexecute_iteration(self, iteration: int) -> IterationResult:
        """Execute with learning trigger"""
        result = await super()._aexecute_iteration(iteration)

        # Trigger learning after iteration
        if self.ace_adapter and self.config.ace_learning_enabled:
            self.ace_adapter.learn_from_execution(
                task=self.current_task,
                output=result.output,
                tool_calls=result.tool_calls,
                success=result.success,
                feedback=result.error_message if not result.success else None,
            )

        return result

    async def _afinalize(self) -> None:
        """Clean shutdown including ACE"""
        await super()._afinalize()

        if self.ace_adapter:
            self.ace_adapter.shutdown()
```

### Example 3: Claude Code Loop Pattern

```python
# Reference: examples/claude-code-loop/ace_loop.py

from ace.integrations.claude_code import ACEClaudeCode

def run_learning_loop(
    task: str,
    working_dir: str,
    max_iterations: int = 10,
    stall_threshold: int = 4,
):
    """Run task with ACE learning loop"""

    ace = ACEClaudeCode(
        working_dir=working_dir,
        ace_model="gpt-4o-mini",
        skillbook_path=".agent/skillbook.json",
        is_learning=True,
        async_learning=True,
    )

    iterations_without_progress = 0
    last_commit_count = get_commit_count()

    for iteration in range(max_iterations):
        # Execute with injected skillbook
        result = ace.run(task=task)

        # Check for progress (commits as indicator)
        current_commits = get_commit_count()
        if current_commits > last_commit_count:
            iterations_without_progress = 0
            last_commit_count = current_commits
        else:
            iterations_without_progress += 1

        # Stall detection
        if iterations_without_progress >= stall_threshold:
            print(f"Stalled after {iteration + 1} iterations")
            break

        # Check for completion
        if result.completed:
            print(f"Completed in {iteration + 1} iterations")
            break

    # Save learned skills
    ace.save_skillbook(".agent/skillbook.json")
```

### Example 4: Manual Skill Management

```python
from ace.skillbook import Skillbook, Skill

# Load skillbook
skillbook = Skillbook.load_from_file(".agent/skillbook.json")

# Add a manual skill
skillbook.add_skill(
    section="error_handling",
    content="When API returns 429, implement exponential backoff starting at 1s",
    skill_id="manual_rate_limit_001",
    metadata={"source": "manual", "added_by": "developer"},
)

# Tag existing skill
skillbook.tag_skill(
    skill_id="skill_abc123",
    tag="helpful",
    increment=1,
)

# Remove ineffective skill
skillbook.remove_skill(
    skill_id="skill_harmful_001",
    soft=True,  # Set status to "invalid" instead of deleting
)

# Get skills by section
error_skills = skillbook.get_skills_by_section("error_handling")

# Get most effective skills
top_skills = sorted(
    skillbook.skills,
    key=lambda s: (s.helpful - s.harmful) / max(1, s.helpful + s.harmful + s.neutral),
    reverse=True,
)[:10]

# Save changes
skillbook.save_to_file(".agent/skillbook.json")
```

</code_examples>

<recommendations>

## Integration Recommendations for RALPH

### 1. Fix API Key Passing (CRITICAL)

The current ace_adapter.py fails because LiteLLMClient cannot find API keys. Fix by explicitly passing:

```python
# Current (broken)
self.client = LiteLLMClient(model=model)

# Fixed
api_key = os.environ.get("ANTHROPIC_API_KEY")
self.client = LiteLLMClient(model=model, api_key=api_key)
```

### 2. Use Meso-Level Learning

For RALPH's iteration-based execution, learn at the iteration level (Meso), not individual tool calls (Micro):

```python
# After each iteration completes
ace_adapter.learn_from_execution(
    task=current_task,
    output=iteration_result.output,
    tool_calls=iteration_result.tool_calls,
    success=iteration_result.success,
)
```

### 3. Enable Async Learning

Use async learning pipeline to avoid blocking execution:

```python
ace_adapter = ACELearningAdapter(
    async_learning=True,  # Non-blocking learning
    skillbook_path=".agent/skillbook/skillbook.json",
)
```

### 4. Use Efficient Models for ACE Operations

Since Reflector and SkillManager are internal operations, use cheaper/faster models:

```python
ace_model="gpt-4o-mini"  # Good balance of quality/cost
# Or for lower cost:
ace_model="gpt-3.5-turbo"
```

### 5. Skillbook Location

Store skillbook in `.agent/` to align with RALPH's existing patterns:

```
.agent/
├── scratchpad.md          # Existing cross-iteration state
├── skillbook/
│   └── skillbook.json     # Learned strategies
└── metrics/
    └── session.json       # Existing metrics
```

### 6. Add Skill Pruning

Periodically prune ineffective skills to prevent context bloat:

```python
def prune_skills(skillbook: Skillbook, threshold: float = -0.3):
    """Remove skills with negative effectiveness"""
    for skill in skillbook.skills[:]:  # Copy to avoid mutation during iteration
        effectiveness = (skill.helpful - skill.harmful) / max(1, skill.helpful + skill.harmful + skill.neutral)
        if effectiveness < threshold and skill.harmful >= 3:
            skillbook.remove_skill(skill.id, soft=True)
```

### 7. Implement Graceful Degradation

If ACE learning fails, continue without blocking orchestration:

```python
try:
    self.ace_adapter.learn_from_execution(...)
except Exception as e:
    self.logger.warning(f"ACE learning failed: {e}")
    # Continue without learning - don't block main execution
```

### 8. Track Learning Metrics

Add metrics for ACE operations:

```python
class ACEMetrics:
    reflections_completed: int = 0
    skills_added: int = 0
    skills_updated: int = 0
    skills_removed: int = 0
    learning_failures: int = 0
    average_reflection_time: float = 0.0
```

### 9. Version Skillbook with Project

Consider committing skillbook to git for project-specific learning persistence:

```bash
# .gitignore
.agent/
!.agent/skillbook/  # Include skillbook in version control
```

### 10. Use v2.1 Prompts

Ensure you're using the latest prompts for better learning quality:

```python
from ace.prompts import REFLECTOR_PROMPT_V2_1, SKILL_MANAGER_PROMPT_V2_1

reflector = Reflector(
    client=client,
    system_prompt=REFLECTOR_PROMPT_V2_1,
)
```

</recommendations>

<metadata>
<confidence>0.92</confidence>
<confidence_justification>
High confidence based on comprehensive source code analysis of the ACE repository. All major components (Skillbook, Reflector, SkillManager, AsyncLearningPipeline, LiteLLMClient, Claude Code integration) were examined directly. The integration patterns are well-documented and the claude-code-loop example provides a concrete reference implementation. Minor uncertainty around edge cases in async pipeline error handling and some undocumented configuration options.
</confidence_justification>

<sources_consulted>
- https://github.com/kayba-ai/agentic-context-engine (full repository via repomix)
- docs/COMPLETE_GUIDE_TO_ACE.md - Core framework documentation
- docs/INTEGRATION_GUIDE.md - Integration patterns documentation
- ace/skillbook.py - Skillbook class implementation
- ace/roles.py - Reflector and SkillManager classes
- ace/async_learning.py - Async learning pipeline
- ace/llm.py - LiteLLM client wrapper
- ace/integrations/claude_code.py - Claude Code integration
- examples/claude-code-loop/ace_loop.py - Reference implementation
- examples/claude-code-loop/README.md - Example documentation
</sources_consulted>

<verification_checklist>
- [x] Core architecture documented (Reflector, Skillbook, SkillManager)
- [x] Learning loop mechanics explained (Inject → Execute → Learn)
- [x] Skill extraction algorithm documented (ReflectorOutput → UpdateOperations)
- [x] Skill curation algorithm documented (SkillManager update logic)
- [x] Configuration options catalogued (all major configs)
- [x] Claude Code integration pattern analyzed
- [x] Best practices for skill granularity provided
- [x] Learning trigger patterns documented
- [x] Skillbook maintenance recommendations included
- [x] Code examples for RALPH integration provided
- [x] API key handling solution provided
- [x] Async learning architecture explained
</verification_checklist>

<dependencies>
- ace package (agentic-context-engine)
- litellm (for LLM provider abstraction)
- instructor (for structured outputs)
- openai or anthropic SDK (depending on chosen model)
</dependencies>

<open_questions>
1. Should RALPH use project-specific skillbooks (per-repo) or global skillbooks (user-level)?
2. What's the optimal skill count before performance degrades?
3. How should skillbook conflicts be handled in multi-agent scenarios?
4. Should there be skill expiration/decay for old skills?
</open_questions>

<assumptions>
1. RALPH will use Anthropic models (claude-opus-4-5-20251101 or claude-sonnet-4-20250514) for main execution
2. ACE operations (Reflector, SkillManager) will use cheaper models (gpt-4o-mini)
3. Skillbook will be stored in .agent/ directory following existing patterns
4. Async learning is preferred to avoid blocking iteration execution
5. The current ace_adapter.py implementation needs complete rewrite
</assumptions>
</metadata>

</research>
