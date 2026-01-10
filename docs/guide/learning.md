# ACE Learning Guide

Ralph Orchestrator integrates with [ACE (Agentic Context Engineering)](https://github.com/kayba-ai/agentic-context-engine) to enable self-improving agent loops. This guide covers how ACE learning works, configuration options, and best practices.

## What is ACE Learning?

ACE is a Stanford/SambaNova framework that enables agents to learn from their execution history. Instead of static prompts, ACE maintains an evolving "skillbook" of learned strategies that improve agent performance over time.

### The Learning Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                      Ralph + ACE Learning Loop                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INJECT: Before each iteration                               │
│     └─ Skillbook strategies added to agent prompt               │
│     └─ Agent sees: "Based on past experience, prefer X over Y"  │
│                                                                  │
│  2. EXECUTE: Normal Ralph iteration                             │
│     └─ Agent runs with enhanced context                         │
│     └─ Execution tracked: success/failure, outputs, tokens      │
│                                                                  │
│  3. LEARN: After iteration completes (async, non-blocking)      │
│     ├─ Reflector: "What worked? What failed? What patterns?"    │
│     └─ SkillManager: Updates skillbook with new skills          │
│                                                                  │
│  [Repeat for next iteration...]                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits

- **Continuous Improvement**: Each iteration makes the agent smarter
- **Cross-Session Memory**: Skillbook persists between runs
- **Reduced Errors**: Agents learn to avoid past mistakes
- **Faster Convergence**: Tasks complete in fewer iterations over time

## Getting Started

### Installation

ACE learning requires the optional `learning` dependency:

```bash
# With pip
pip install ralph-orchestrator[learning]

# With uv (recommended)
uv pip install ralph-orchestrator[learning]

# Verify installation
python -c "from ralph_orchestrator.learning import ACE_AVAILABLE; print(f'ACE: {ACE_AVAILABLE}')"
```

### Quick Start

```bash
# Enable learning with a simple flag
ralph run --learning "Create a Python CLI that generates random passwords"

# Learning is now active - watch the logs for:
# [INFO] ACE learning initialized | model=claude-sonnet-4-5-20250929 | skills=0
# [INFO] Skillbook injected | skills=0 | added_chars=0
# ... (iteration runs) ...
# [INFO] ACE learning complete | skills=1 (Δ+1) | reflect=XXms | skill_mgr=XXms
```

## Configuration

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--learning` | `false` | Enable ACE learning loop |
| `--learning-model` | `claude-sonnet-4-5-20250929` | Model for reflection and skill management |
| `--skillbook-path` | `.agent/skillbook/skillbook.json` | Path to persist the skillbook |

### Configuration File (ralph.yml)

```yaml
# Full learning configuration
learning:
  enabled: true                              # Master switch for learning
  model: claude-sonnet-4-5-20250929          # Model used for reflection
  skillbook_path: .agent/skillbook/skillbook.json  # Where to store skills
  async_learning: true                       # Run learning in background
  max_skills: 100                            # Maximum skills before pruning

# Learning can be combined with other settings
execution:
  max_iterations: 100
  max_cost: 50.0

adapters:
  claude:
    model: claude-sonnet-4-5-20250929
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `RALPH_LEARNING_ENABLED` | Override `learning.enabled` |
| `RALPH_LEARNING_MODEL` | Override `learning.model` |
| `RALPH_SKILLBOOK_PATH` | Override `learning.skillbook_path` |
| `ANTHROPIC_API_KEY` | Required for Claude-based learning |

## The Skillbook

### What is a Skillbook?

The skillbook is a JSON file that stores learned strategies. Each "skill" is a pattern the agent learned from past execution:

```json
{
  "skills": [
    {
      "id": "skill_001",
      "name": "prefer-pytest-over-unittest",
      "description": "When writing Python tests, prefer pytest fixtures over unittest.TestCase",
      "context": "python_testing",
      "confidence": 0.85,
      "created_at": "2024-01-15T10:30:00Z",
      "usage_count": 12
    },
    {
      "id": "skill_002",
      "name": "check-imports-first",
      "description": "Before writing code, verify all required imports are available",
      "context": "python_development",
      "confidence": 0.92,
      "created_at": "2024-01-15T11:45:00Z",
      "usage_count": 8
    }
  ],
  "metadata": {
    "version": "1.0",
    "total_skills": 2,
    "last_updated": "2024-01-15T12:00:00Z"
  }
}
```

### Skillbook Lifecycle

1. **Creation**: First `--learning` run creates an empty skillbook
2. **Growth**: Each iteration adds new skills from successful patterns
3. **Injection**: Skills are formatted and added to agent prompts
4. **Pruning**: When `max_skills` is exceeded, oldest/lowest-confidence skills are removed
5. **Persistence**: Skillbook is saved after each learning cycle and on checkpoints

### Sharing Skillbooks

Skillbooks can be shared across environments:

```bash
# Commit skillbook to version control
git add .agent/skillbook/skillbook.json
git commit -m "Add learned skills from task X"

# Team members get the learned skills automatically
git pull
ralph run --learning "New task"  # Benefits from team's learnings
```

### Project-Specific vs Global Skills

```yaml
# Project-specific skillbook (default)
learning:
  skillbook_path: .agent/skillbook/skillbook.json

# Global skillbook (shared across projects)
learning:
  skillbook_path: ~/.ralph/global-skillbook.json

# Task-specific skillbook
learning:
  skillbook_path: .agent/skillbooks/api-development.json
```

## How Learning Works Internally

### 1. Injection Phase

Before each iteration, the `ACELearningAdapter.inject_context()` method:

- Loads the current skillbook
- Formats skills as natural language guidance
- Prepends to the agent's prompt

```python
# What the agent sees (simplified):
"""
## Learned Strategies (from previous executions)

Based on past experience:
- When writing Python tests, prefer pytest fixtures over unittest.TestCase
- Before writing code, verify all required imports are available

## Original Task

Create a Python CLI that generates random passwords...
"""
```

### 2. Execution Phase

Normal Ralph iteration with the enhanced prompt. The adapter tracks:

- Execution success/failure
- Output content
- Token usage
- Duration

### 3. Learning Phase (Async)

After iteration completes, `ACELearningAdapter.learn_from_execution()`:

1. **Reflector**: Analyzes the execution
   - What was the task?
   - What approach was taken?
   - What worked well?
   - What could be improved?

2. **SkillManager**: Updates the skillbook
   - Extracts actionable skills from reflection
   - Assigns confidence scores
   - Deduplicates against existing skills
   - Prunes if over capacity

This happens asynchronously so it doesn't block the next iteration.

## Best Practices

### When to Enable Learning

**Enable learning for:**
- Long-running tasks (10+ iterations)
- Recurring task types (API development, testing, refactoring)
- Complex domains where patterns emerge
- Team projects where learnings should be shared

**Skip learning for:**
- One-off quick tasks
- Highly unique/novel tasks
- Cost-sensitive single runs

### Choosing a Learning Model

| Model | Use Case | Cost |
|-------|----------|------|
| `claude-sonnet-4-5-20250929` | Default, good balance | Medium |
| `claude-haiku-3-5` | Budget-conscious, quick tasks | Low |
| `claude-opus-4` | Maximum quality reflection | High |

```bash
# Development: fast, cheap learning
ralph run --learning --learning-model claude-haiku-3-5 "Quick task"

# Production: thorough learning
ralph run --learning --learning-model claude-sonnet-4-5-20250929 "Complex task"
```

### Managing Skillbook Size

```yaml
learning:
  max_skills: 100  # Default: reasonable for most projects

# For focused projects
learning:
  max_skills: 50   # Smaller, more curated skillbook

# For comprehensive learning
learning:
  max_skills: 200  # Larger skillbook, more context per prompt
```

### Monitoring Learning

Watch the logs for learning metrics:

```
[INFO] ACE learning initialized | model=claude-sonnet-4-5-20250929 | skills=12
[INFO] Skillbook injected | skills=12 | added_chars=1456
[INFO] ACE learning complete | skills=13 (Δ+1) | reflect=234ms | skill_mgr=156ms
```

Check learning stats in the summary:

```
[INFO] Learning Summary:
  ├─ Initial Skills: 12
  ├─ Final Skills: 15
  ├─ Skills Added: 3
  ├─ Total Reflect Time: 1.2s
  └─ Total Skill Mgr Time: 0.8s
```

## Troubleshooting

### Learning Not Initializing

```bash
# Check if ACE is installed
python -c "from ralph_orchestrator.learning import ACE_AVAILABLE; print(ACE_AVAILABLE)"

# If False, install the learning extra
pip install ralph-orchestrator[learning]
```

### Authentication Errors

```bash
# Ensure ANTHROPIC_API_KEY is set
export ANTHROPIC_API_KEY="your-key-here"

# Or use a different model provider (if supported)
ralph run --learning --learning-model "gpt-4" "Task"
```

### Skillbook Not Updating

1. Check the skillbook path is writable
2. Verify async_learning isn't causing race conditions
3. Check logs for learning errors:
   ```
   [WARNING] ACE learning error: ...
   ```

### High Learning Costs

```yaml
# Use a cheaper model
learning:
  model: claude-haiku-3-5

# Or disable async for more control
learning:
  async_learning: false
```

## API Reference

### ACELearningAdapter

```python
from ralph_orchestrator.learning import ACELearningAdapter, LearningConfig

# Initialize
config = LearningConfig(
    model="claude-sonnet-4-5-20250929",
    skillbook_path=".agent/skillbook/skillbook.json",
    max_skills=100,
    async_learning=True
)
adapter = ACELearningAdapter(config)

# Inject context before execution
enhanced_prompt = adapter.inject_context(original_prompt)

# Learn after execution
adapter.learn_from_execution(
    task="Original task",
    output="Execution output",
    success=True,
    metrics={"tokens": 1000, "duration": 5.2}
)

# Save skillbook
adapter.save_skillbook()

# Get learning stats
stats = adapter.get_stats()
print(f"Skills: {stats['skill_count']}, Events: {stats['events']}")
```

### LearningConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | str | `claude-sonnet-4-5-20250929` | LLM for reflection |
| `skillbook_path` | str | `.agent/skillbook/skillbook.json` | Skillbook location |
| `max_skills` | int | `100` | Maximum skills to retain |
| `async_learning` | bool | `True` | Run learning asynchronously |

## Next Steps

- [Configuration Guide](configuration.md) - Full configuration reference
- [Cost Management](cost-management.md) - Control learning costs
- [Checkpointing](checkpointing.md) - Recovery with learning state
- [Agents Guide](agents.md) - Agent-specific learning behavior
