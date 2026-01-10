# Ralph Orchestrator

[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://mikeyobrien.github.io/ralph-orchestrator/)
[![Version](https://img.shields.io/badge/version-1.2.2-green)](https://github.com/mikeyobrien/ralph-orchestrator/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

A somewhat functional implementation of the Ralph Wiggum software engineering technique - putting AI agents in a loop until the task is done.

> "Me fail English? That's unpossible!" - Ralph Wiggum

### NOTE: This was a toy project that was itself built with the ralph wiggum technique. Expect bugs, missing functionality, and breaking changes while I clean it up. Mainly tested with Claude Agent SDK path

## 📚 Documentation

**[View Full Documentation](https://mikeyobrien.github.io/ralph-orchestrator/)** | [Quick Start](https://mikeyobrien.github.io/ralph-orchestrator/quick-start/) | [API Reference](https://mikeyobrien.github.io/ralph-orchestrator/api/) | [Examples](https://mikeyobrien.github.io/ralph-orchestrator/examples/)

## Overview

Ralph Orchestrator implements a simple but effective pattern for autonomous task completion using AI agents. It continuously runs an AI agent against a prompt file until the task is marked as complete or limits are reached.

Based on the Ralph Wiggum technique by [Geoffrey Huntley](https://ghuntley.com/ralph/), this implementation provides a robust, tested, and feature-complete orchestration system for AI-driven development.

## ✅ Production Ready - v1.2.2

- **Claude Integration**: ✅ COMPLETE (with Agent SDK)
- **Kiro CLI Integration**: ✅ COMPLETE (Successor to Q Chat)
- **Q Chat Integration**: ✅ COMPLETE (Legacy Support)
- **Gemini Integration**: ✅ COMPLETE
- **ACP Protocol Support**: ✅ COMPLETE (Agent Client Protocol)
- **Core Orchestration**: ✅ OPERATIONAL
- **Test Suite**: ✅ 920+ tests passing
- **Documentation**: ✅ [COMPLETE](https://mikeyobrien.github.io/ralph-orchestrator/)
- **Production Deployment**: ✅ [READY](https://mikeyobrien.github.io/ralph-orchestrator/advanced/production-deployment/)

## Features

- 🤖 **Multiple AI Agent Support**: Works with Claude, Kiro CLI, Q Chat, Gemini CLI, and ACP-compliant agents
- 🔍 **Auto-detection**: Automatically detects which AI agents are available
- 🌐 **WebSearch Support**: Claude can search the web for current information
- 💾 **Checkpointing**: Git-based async checkpointing for recovery and history
- 📚 **Prompt Archiving**: Tracks prompt evolution over iterations
- 🔄 **Error Recovery**: Automatic retry with exponential backoff (non-blocking)
- 📊 **State Persistence**: Saves metrics and state for analysis
- ⏱️ **Configurable Limits**: Set max iterations and runtime limits
- 🧪 **Comprehensive Testing**: 620+ tests with unit, integration, and async coverage
- 🎨 **Rich Terminal Output**: Beautiful formatted output with syntax highlighting
- 🔒 **Security Features**: Automatic masking of API keys et sensitive data in logs
- ⚡ **Async-First Design**: Non-blocking I/O throughout (logging, git operations)
- 📝 **Inline Prompts**: Run with `-p "your task"` without needing a file
- 🧠 **Agent Scratchpad**: All agents persist context across iterations via `.agent/scratchpad.md`

## Installation

### For Users (Recommended)

```bash
# Install with uv tool (easiest way to run Ralph globally)
uv tool install ralph-orchestrator

# Or install with pip
pip install ralph-orchestrator
```

### For Developers

```bash
# Clone the repository
git clone https://github.com/mikeyobrien/ralph-orchestrator.git
cd ralph-orchestrator

# Install with uv (recommended)
uv sync

# Or install with pip (requires pip in virtual environment)
python -m pip install -e .
```

## Prerequisites

At least one AI CLI tool must be installed:

- **[Claude SDK](https://pypi.org/project/claude-code-sdk/)**
  ```bash
  # Automatically installed via dependencies
  # Requires ANTHROPIC_API_KEY environment variable with proper permissions:
  # - Read/Write access to conversations
  # - Model access (Claude 3.5 Sonnet or similar)
  # - Sufficient rate limits for continuous operation
  
  export ANTHROPIC_API_KEY="sk-ant-..."
  ```

- **[Kiro CLI](https://github.com/kiro-cli/kiro)** (formerly Q Chat)
  ```bash
  # Follow installation instructions in repo
  ```

- **[Q Chat](https://github.com/qchat/qchat)** (Legacy)
  ```bash
  # Follow installation instructions in repo
  ```

- **[Gemini CLI](https://github.com/google-gemini/gemini-cli)**
  ```bash
  npm install -g @google/gemini-cli
  ```

- **ACP-Compliant Agents** (Agent Client Protocol)
  ```bash
  # Any ACP-compliant agent can be used via the ACP adapter
  # Example: Gemini CLI with ACP mode
  ralph run -a acp --acp-agent gemini
  ```

## Quick Start

### 1. Initialize a project
```bash
ralph init
```

This creates:
- `PROMPT.md` - Task description template
- `ralph.yml` - Configuration file
- `.agent/` - Workspace directories for prompts, checkpoints, metrics, plans, and memory

### 2. Configure Ralph (optional)
Edit `ralph.yml` to customize settings:
```yaml
# Ralph Orchestrator Configuration
agent: auto                    # Which agent to use: claude, kiro, q, gemini, acp, auto
prompt_file: PROMPT.md         # Path to prompt file
max_iterations: 100            # Maximum iterations before stopping
max_runtime: 14400             # Maximum runtime in seconds (4 hours)
verbose: false                 # Enable verbose output

# Adapter configurations
adapters:
  claude:
    enabled: true
    timeout: 300              # Timeout in seconds
  kiro:
    enabled: true
    timeout: 300
  q:
    enabled: true
    timeout: 300
  gemini:
    enabled: true
    timeout: 300
  acp:                        # Agent Client Protocol adapter
    enabled: true
    timeout: 300
    tool_permissions:
      agent_command: gemini   # Command to run the ACP agent
      agent_args: []          # Additional arguments
      permission_mode: auto_approve  # auto_approve, deny_all, allowlist, interactive
      permission_allowlist: []  # Patterns for allowlist mode
```

### 3. Edit PROMPT.md with your task
```markdown
# Task: Build a Python Calculator

Create a calculator module with:
- Basic operations (add, subtract, multiply, divide)
- Error handling for division by zero
- Unit tests for all functions

<!-- Ralph will continue iterating until limits are reached -->
```

### 4. Run Ralph
```bash
ralph run
# or with config file
ralph -c ralph.yml
```

## Usage

### Basic Commands

```bash
# Run with auto-detected agent
ralph

# Use configuration file
ralph -c ralph.yml

# Use specific agent
ralph run -a claude
ralph run -a kiro
ralph run -a q
ralph run -a gemini
ralph run -a acp               # ACP-compliant agent

# Check status
ralph status

# Clean workspace
ralph clean

# Dry run (test without executing)
ralph run --dry-run
```

### Advanced Options

```bash
ralph [OPTIONS] [COMMAND]

Commands:
  init                            Initialize a new Ralph project
  status                          Show current Ralph status  
  clean                           Clean up agent workspace
  prompt                          Generate structured prompt from rough ideas
  run                             Run the orchestrator (default)

Core Options:
  -c, --config CONFIG             Configuration file (YAML format)
  -a, --agent {claude,kiro,q,gemini,acp,auto}  AI agent to use (default: auto)
  -P, --prompt-file FILE          Prompt file path (default: PROMPT.md)
  -p, --prompt-text TEXT          Inline prompt text (overrides file)
  --completion-promise TEXT       Stop when agent output contains this exact string (default: LOOP_COMPLETE)
  -i, --max-iterations N          Maximum iterations (default: 100)
  -t, --max-runtime SECONDS      Maximum runtime (default: 14400)
  -v, --verbose                   Enable verbose output
  -d, --dry-run                   Test mode without executing agents

ACP Options:
  --acp-agent COMMAND             ACP agent command (default: gemini)
  --acp-permission-mode MODE      Permission handling: auto_approve, deny_all, allowlist, interactive

Advanced Options:
  --max-tokens MAX_TOKENS         Maximum total tokens (default: 1000000)
  --max-cost MAX_COST             Maximum cost in USD (default: 50.0)
  --checkpoint-interval N         Git checkpoint interval (default: 5)
  --retry-delay SECONDS           Retry delay on errors (default: 2)
  --no-git                        Disable git checkpointing
  --no-archive                    Disable prompt archiving
  --no-metrics                    Disable metrics collection
```

## ACP (Agent Client Protocol) Integration

Ralph supports any ACP-compliant agent through its ACP adapter. This enables integration with agents like Gemini CLI that implement the [Agent Client Protocol](https://github.com/anthropics/agent-client-protocol).

### Quick Start with ACP

```bash
# Basic usage with Gemini CLI
ralph run -a acp --acp-agent gemini

# With permission mode
ralph run -a acp --acp-agent gemini --acp-permission-mode auto_approve
```

### Permission Modes

The ACP adapter supports four permission modes for handling agent tool requests:

| Mode | Description | Use Case |
|------|-------------|----------|
| `auto_approve` | Approve all requests automatically | Trusted environments, CI/CD |
| `deny_all` | Deny all permission requests | Testing, sandboxed execution |
| `allowlist` | Only approve matching patterns | Production with specific tools |
| `interactive` | Prompt user for each request | Development, manual oversight |

### Configuration

Configure ACP in `ralph.yml`:

```yaml
adapters:
  acp:
    enabled: true
    timeout: 300
    tool_permissions:
      agent_command: gemini      # Agent CLI command
      agent_args: []             # Additional CLI arguments
      permission_mode: auto_approve
      permission_allowlist:      # For allowlist mode
        - "fs/read_text_file:*.py"
        - "fs/write_text_file:src/*"
        - "terminal/create:pytest*"
```

### Agent Scratchpad

All agents maintain context across iterations via `.agent/scratchpad.md`. This file persists:
- Progress from previous iterations
- Decisions and context
- Current blockers or issues
- Remaining work items

The scratchpad enables agents to continue from where they left off rather than restarting each iteration.

## 🧠 ACE Learning (Self-Improving Agents)

Ralph integrates with the [ACE (Agentic Context Engineering)](https://github.com/kayba-ai/agentic-context-engine) framework to enable self-improving agent loops. After each iteration, ACE analyzes what worked and what failed, then injects those learnings into subsequent iterations.

### Quick Start with Learning

```bash
# Enable learning with default settings
ralph run --learning "Your task here"

# With custom learning model
ralph run --learning --learning-model "claude-sonnet-4-5-20250929" "Your task"

# With custom skillbook path
ralph run --learning --skillbook-path ".agent/my-skillbook.json" "Your task"
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      Ralph + ACE Learning Loop                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INJECT: Skillbook strategies added to prompt                │
│     └─ Learned patterns from previous executions                │
│                                                                  │
│  2. EXECUTE: Agent runs iteration with enhanced context         │
│     └─ Normal Ralph execution via Claude/Kiro/Gemini/etc        │
│                                                                  │
│  3. LEARN: ACE analyzes execution outcomes                      │
│     ├─ Reflector extracts learnings                             │
│     └─ SkillManager updates skillbook                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration

**CLI Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--learning` | `false` | Enable ACE learning loop |
| `--learning-model` | `claude-sonnet-4-5-20250929` | Model for learning (reflection/skill management) |
| `--skillbook-path` | `.agent/skillbook/skillbook.json` | Path to persist learned skills |

**Config File (`ralph.yml`):**

```yaml
# ACE Learning Configuration
learning:
  enabled: true                              # Enable/disable learning
  model: claude-sonnet-4-5-20250929          # Model for reflection
  skillbook_path: .agent/skillbook/skillbook.json  # Skillbook location
  async_learning: true                       # Learn in background (non-blocking)
  max_skills: 100                            # Maximum skills to retain
```

### Installation

ACE learning requires the optional `learning` dependency:

```bash
# Install with learning support
pip install ralph-orchestrator[learning]

# Or with uv
uv pip install ralph-orchestrator[learning]
```

### Skillbook Persistence

The skillbook (`.agent/skillbook/skillbook.json`) persists learned strategies across sessions:
- Automatically created on first learning run
- Updated after each iteration with new learnings
- Injected into prompts to guide future iterations
- Pruned automatically when `max_skills` is exceeded

### Supported Operations

The ACP adapter handles these agent requests:

**File Operations:**
- `fs/read_text_file` - Read file contents (with path security validation)
- `fs/write_text_file` - Write file contents (with path security validation)

**Terminal Operations:**
- `terminal/create` - Create subprocess with command
- `terminal/output` - Read process output
- `terminal/wait_for_exit` - Wait for process completion
- `terminal/kill` - Terminate process
- `terminal/release` - Release terminal resources

## How It Works

### The Ralph Loop

```
┌─────────────────┐
│  Read PROMPT.md │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Execute AI Agent│<──────┐
└────────┬────────┘       │
         │                │
         v                │
┌─────────────────┐       │
│ Check Complete? │───No──┘
└────────┬────────┘
         │Yes
         v
┌─────────────────┐
│      Done!      │
└─────────────────┘
```

### Execution Flow

1. **Initialization**: Creates `.agent/` directories and validates prompt file
2. **Agent Detection**: Auto-detects available AI agents (claude, kiro, q, gemini)
3. **Iteration Loop**: 
   - Executes AI agent with current prompt
   - Monitors for task completion marker
   - Creates checkpoints at intervals
   - Handles errors with retry logic
4. **Completion**: Stops when:
   - Max iterations reached
   - Max runtime exceeded
   - Cost limits reached
   - Too many consecutive errors
   - Completion promise matched (default: LOOP_COMPLETE)

## Project Structure

```
ralph-orchestrator/
├── src/
│   └── ralph_orchestrator/
│       ├── __main__.py      # CLI entry point
│       ├── main.py          # Configuration and types
│       ├── orchestrator.py  # Core orchestration logic (async)
│       ├── adapters/        # AI agent adapters
│       │   ├── base.py      # Base adapter interface
│       │   ├── claude.py    # Claude Agent SDK adapter
│       │   ├── kiro.py      # Kiro CLI adapter
│       │   ├── gemini.py    # Gemini CLI adapter
│       │   ├── qchat.py     # Q Chat adapter
│       │   ├── acp.py       # ACP (Agent Client Protocol) adapter
│       │   ├── acp_protocol.py  # JSON-RPC 2.0 protocol handling
│       │   ├── acp_client.py    # Subprocess manager
│       │   ├── acp_models.py    # Data models
│       │   └── acp_handlers.py  # Permission/file/terminal handlers
│       ├── output/          # Output formatting (NEW)
│       │   ├── base.py      # Base formatter interface
│       │   ├── console.py   # Rich console output
│       │   ├── rich_formatter.py  # Rich text formatting
│       │   └── plain.py     # Plain text fallback
│       ├── async_logger.py  # Thread-safe async logging
│       ├── context.py       # Context management
│       ├── logging_config.py # Centralized logging setup
│       ├── metrics.py       # Metrics tracking
│       ├── security.py      # Security validation & masking
│       └── safety.py        # Safety checks
├── tests/                   # Test suite (620+ tests)
│   ├── test_orchestrator.py
│   ├── test_adapters.py
│   ├── test_async_logger.py
│   ├── test_output_formatters.py
│   ├── test_config.py
│   ├── test_integration.py
│   └── test_acp_*.py        # ACP adapter tests (305+ tests)
├── docs/                    # Documentation
├── PROMPT.md               # Task description (user created)
├── ralph.yml               # Configuration file (created by init)
├── pyproject.toml          # Project configuration
├── .agent/                 # CLI workspace (created by init)
│   ├── prompts/            # Prompt workspace
│   ├── checkpoints/        # Checkpoint markers
│   ├── metrics/            # Metrics data
│   ├── plans/              # Planning documents
│   └── memory/             # Agent memory
├── .ralph/                 # Runtime metrics directory
└── prompts/                # Prompt archive directory
    └── archive/            # Archived prompt history
```

## Testing

### Run Test Suite

```bash
# All tests
uv run pytest -v

# With coverage
uv run pytest --cov=ralph_orchestrator

# Specific test file
uv run pytest tests/test_orchestrator.py -v

# Integration tests only
uv run pytest tests/test_integration.py -v
```

### Test Coverage

- ✅ Unit tests for all core functions
- ✅ Integration tests with mocked agents
- ✅ CLI interface tests
- ✅ Error handling and recovery tests
- ✅ State persistence tests

## Examples

### Inline Prompt (Quick Tasks)

```bash
# Run directly with inline prompt - no file needed
ralph run -p "Write a Python function to check if a number is prime" -a claude --max-iterations 5
```

### Simple Function (File-Based)

```bash
echo "Write a Python function to check if a number is prime" > PROMPT.md
ralph run -a claude --max-iterations 5
```

### Web Application

```bash
cat > PROMPT.md << 'EOF'
Build a Flask web app with:
- User registration and login
- SQLite database
- Basic CRUD operations
- Bootstrap UI
EOF

ralph run --max-iterations 50
```

### Test-Driven Development

```bash
cat > PROMPT.md << 'EOF'
Implement a linked list in Python using TDD:
1. Write tests first
2. Implement methods to pass tests
3. Add insert, delete, search operations
4. Ensure 100% test coverage
EOF

ralph run -a q --verbose
```

## Monitoring

### Check Status
```bash
# One-time status check
ralph status

# Example output:
Ralph Orchestrator Status
=========================
Prompt: PROMPT.md exists
Status: IN PROGRESS
Latest metrics: .ralph/metrics_20250907_154435.json
{
  "iteration_count": 15,
  "runtime": 234.5,
  "errors": 0
}
```

### View Logs
```bash
# If using verbose mode
ralph run --verbose 2>&1 | tee ralph.log

# Check git history
git log --oneline | grep "Ralph checkpoint"
```

## Error Recovery

Ralph handles errors gracefully:

- **Retry Logic**: Failed iterations retry after configurable delay
- **Error Limits**: Stops after 5 consecutive errors
- **Timeout Protection**: 5-minute timeout per iteration
- **State Persistence**: Can analyze failures from saved state
- **Git Recovery**: Can reset to last working checkpoint

### Manual Recovery

```bash
# Check last error
cat .ralph/metrics_*.json | jq '.errors[-1]'

# Reset to last checkpoint
git reset --hard HEAD

# Clean and restart
ralph clean
ralph run
```

## Best Practices

1. **Clear Task Definition**: Write specific, measurable requirements
2. **Incremental Goals**: Break complex tasks into smaller steps
3. **Success Markers**: Define clear completion criteria
4. **Regular Checkpoints**: Use default 5-iteration checkpoints
5. **Monitor Progress**: Use `ralph status` to track iterations
6. **Version Control**: Commit PROMPT.md before starting

## Troubleshooting

### Agent Not Found
```bash
# For Claude, ensure API key is set with proper permissions
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify Claude API key permissions:
# - Should have access to Claude 3.5 Sonnet or similar model
# - Need sufficient rate limits (at least 40,000 tokens/minute)
# - Requires read/write access to the API

# For Q and Gemini, check CLI tools are installed
which kiro-cli
which q
which gemini

# Install missing CLI tools as needed
```

### Task Not Completing
```bash
# Check iteration count and progress
ralph status

# Review agent errors
cat .agent/metrics/state_*.json | jq '.errors'

# Try different agent
ralph run -a gemini
```

### Performance Issues
```bash
# Reduce iteration timeout
ralph run --max-runtime 1800

# Increase checkpoint frequency
ralph run --checkpoint-interval 3
```

## Research & Theory

The Ralph Wiggum technique is based on several key principles:

1. **Simplicity Over Complexity**: Keep orchestration minimal (~400 lines)
2. **Deterministic Failure**: Fail predictably in an unpredictable world
3. **Context Recovery**: Use git and state files for persistence
4. **Human-in-the-Loop**: Allow manual intervention when needed

For detailed research and theoretical foundations, see the [research directory](../README.md).

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`uv run pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **[Geoffrey Huntley](https://ghuntley.com/ralph/)** - Creator of the Ralph Wiggum technique
- **[Harper Reed](https://harper.blog/)** - Spec-driven development methodology
- **Anthropic, Google, Q** - For providing excellent AI CLI tools

## Support

- **Documentation**: [Full Documentation](https://mikeyobrien.github.io/ralph-orchestrator/)
- **Deployment Guide**: [Production Deployment](https://mikeyobrien.github.io/ralph-orchestrator/advanced/production-deployment/)
- **Issues**: [GitHub Issues](https://github.com/mikeyobrien/ralph-orchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mikeyobrien/ralph-orchestrator/discussions)
- **Research**: [Ralph Wiggum Research](../)

## Version History

- **v1.2.2** (2025-12)
  - **ACP (Agent Client Protocol) Support**: Full integration with ACP-compliant agents
    - JSON-RPC 2.0 message protocol
    - Permission handling (auto_approve, deny_all, allowlist, interactive)
    - File operations (read/write with security)
    - Terminal operations (create, output, wait, kill, release)
    - Session management and streaming updates
    - Agent scratchpad mechanism for context persistence across iterations
  - New CLI options: `--acp-agent`, `--acp-permission-mode`
  - Configuration support in ralph.yml
  - 305+ new ACP-specific tests
  - Expanded test suite (920+ tests)

- **v1.1.0** (2025-12)
  - Async-first architecture for non-blocking operations
  - Thread-safe async logging with rotation and security masking
  - Rich terminal output with syntax highlighting
  - Inline prompt support (`-p "your task"`)
  - Claude Agent SDK integration with MCP server support
  - Async git checkpointing (non-blocking)
  - Expanded test suite (620+ tests)
  - Improved error handling with debug logging

- **v1.0.0** (2025-09-07)
  - Initial release with Claude, Q, and Gemini support
  - Comprehensive test suite (17 tests)
  - Production-ready error handling
  - Full documentation
  - Git-based checkpointing
  - State persistence and metrics

---

*"I'm learnding!" - Ralph Wiggum*
