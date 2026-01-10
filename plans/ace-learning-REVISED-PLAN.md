# ACE Learning Integration - REVISED Implementation Plan

**Created**: 2026-01-10
**Status**: Implementation Complete - Ready for Validation
**Branch**: feat/mobile-orchestration-prompt

## Executive Summary

After thoroughly reading every line of the ACE claude-code-loop example and all ACE documentation, I've confirmed that the **current implementation is architecturally correct**. The concern about "separate API key" was based on a misunderstanding of the authentication patterns between Claude Code CLI (subscription auth) and Claude Agent SDK (API key auth).

## Key Discovery: Authentication Pattern

### Claude Code CLI (how ACE's claude-code-loop example works)
```python
# Claude Code CLI uses SUBSCRIPTION auth (no API key)
# ACE filters out ANTHROPIC_API_KEY so CLI uses subscription
env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
subprocess.run(["claude", ...], env=env)

# ACE learning uses API key via LiteLLMClient
self.ace_llm = LiteLLMClient(model=ace_model)  # Gets ANTHROPIC_API_KEY from env
```

### Ralph Orchestrator (how our integration works)
```python
# Ralph execution uses ANTHROPIC_API_KEY via Claude Agent SDK
# (Already configured in adapters)

# ACE learning uses SAME ANTHROPIC_API_KEY via LiteLLMClient
# LiteLLMClient auto-detects API key from environment:
#   - ANTHROPIC_API_KEY for claude-* models
#   - OPENAI_API_KEY for gpt-* models
self.llm = LiteLLMClient(model=config.model)
```

**Result**: Both Ralph execution AND ACE learning use the SAME `ANTHROPIC_API_KEY` environment variable. No separate key needed. No conflict.

## Current Implementation Status

### ✅ Completed Components

1. **ACE Learning Adapter** (`src/ralph_orchestrator/learning/ace_adapter.py`)
   - LiteLLMClient correctly initialized for learning
   - Reflector and SkillManager properly configured
   - Thread-safe skillbook operations
   - Comprehensive telemetry tracking
   - Skill pruning with max_skills limit

2. **Orchestrator Integration** (`src/ralph_orchestrator/orchestrator.py`)
   - Learning adapter initialized in constructor
   - `inject_context()` called before iteration execution
   - `learn_from_execution()` called after iteration
   - Skillbook saved on checkpoints
   - Learning stats included in telemetry

3. **Configuration** (`src/ralph_orchestrator/main.py`)
   - `--learning` flag to enable
   - `--learning-model` to specify model
   - `--skillbook-path` for skillbook location
   - Config file support for learning settings

### ✅ Three-Step Pattern Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                      Ralph Iteration Loop                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INJECT (before execution)                                   │
│     └─ adapter.inject_context(prompt)                           │
│        └─ wrap_skillbook_context(skillbook) → enhanced prompt   │
│                                                                  │
│  2. EXECUTE (Ralph's existing adapters)                         │
│     └─ ClaudeAdapter.aexecute(enhanced_prompt)                  │
│        └─ Uses ANTHROPIC_API_KEY via Claude Agent SDK           │
│                                                                  │
│  3. LEARN (after execution)                                     │
│     └─ adapter.learn_from_execution(task, output, success)      │
│        ├─ Reflector.reflect() → analysis                        │
│        └─ SkillManager.update_skills() → skillbook updates      │
│        └─ Uses ANTHROPIC_API_KEY via LiteLLMClient              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Validation Plan

### Functional Test (Manual - NOT pytest)

Run Ralph with learning enabled and verify:

```bash
# 1. Ensure ANTHROPIC_API_KEY is set
export ANTHROPIC_API_KEY="your-key"

# 2. Run Ralph with learning
cd /Users/nick/Desktop/ralph-orchestrator
ralph --learning --dry-run "Create a hello world Python script"

# 3. Check that:
#    - ACE learning initializes (check logs)
#    - Skillbook is created/updated
#    - No authentication errors
```

### Expected Log Output

```
[INFO] ACE learning initialized | model=claude-sonnet-4-5-20250929 | skills=0
[INFO] Skillbook injected | skills=0 | added_chars=0
... (iteration executes) ...
[INFO] ACE learning complete | skills=1 (Δ+1) | reflect=XXms | skill_mgr=XXms
```

### Validation Criteria

- [ ] Learning initializes without API key errors
- [ ] LiteLLMClient picks up ANTHROPIC_API_KEY automatically
- [ ] Reflector runs successfully after iteration
- [ ] SkillManager updates skillbook
- [ ] Skillbook file is created at configured path
- [ ] Skills are injected into subsequent iterations

## Files Modified

| File | Changes |
|------|---------|
| `src/ralph_orchestrator/learning/__init__.py` | Module exports |
| `src/ralph_orchestrator/learning/ace_adapter.py` | Complete ACE adapter with telemetry |
| `src/ralph_orchestrator/orchestrator.py` | Learning integration |
| `src/ralph_orchestrator/main.py` | CLI flags and config |
| `src/ralph_orchestrator/metrics.py` | TriggerReason enum for telemetry |

## Running with Learning Enabled

### Command Line
```bash
# Basic usage
ralph --learning "Your task here"

# With custom model
ralph --learning --learning-model "claude-sonnet-4-5-20250929" "Your task"

# With custom skillbook path
ralph --learning --skillbook-path ".agent/my-skillbook.json" "Your task"
```

### Config File
```yaml
learning:
  enabled: true
  model: claude-sonnet-4-5-20250929
  skillbook_path: .agent/skillbook/skillbook.json
  async_learning: true
  max_skills: 100
```

## Conclusion

The ACE learning integration is **complete and architecturally correct**. The key insight is that:

1. **Claude Code CLI** filters out `ANTHROPIC_API_KEY` to use subscription auth
2. **Ralph uses Claude Agent SDK** which requires `ANTHROPIC_API_KEY`
3. **ACE learning (LiteLLMClient)** auto-detects `ANTHROPIC_API_KEY` from environment
4. **Both Ralph and ACE learning use the SAME key** - no conflict

The remaining step is functional validation by running Ralph with `--learning` flag and confirming the learning loop works end-to-end.
