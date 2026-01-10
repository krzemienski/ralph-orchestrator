# ACE Framework Documentation Research

**ACE provides a three-agent learning architecture (Agent, Reflector, SkillManager) with persistent Skillbook storage that integrates via INJECT->EXECUTE->LEARN cycle, requiring explicit API key passing to fix current RALPH integration failures.**

## Version
v1 - Initial comprehensive research

## Key Findings

### Architecture
- **Three-agent system**: Your agent executes, Reflector analyzes, SkillManager curates skills
- **Skillbook**: JSON storage with skills categorized by section, tracked by helpful/harmful/neutral counts
- **TOON encoding**: Tab-delimited format reduces token usage for skillbook injection
- **Async pipeline**: Parallel Reflectors + serialized SkillManager prevents race conditions

### Integration Pattern
```
INJECT: skillbook.as_prompt() -> Add to agent system prompt
EXECUTE: Agent runs task normally
LEARN: Reflector.reflect() -> SkillManager.update_skills() -> Save skillbook
```

### Critical Fix Identified
The current ace_adapter.py fails because LiteLLMClient doesn't receive the API key:
```python
# BROKEN: Relies on environment auto-detection
self.client = LiteLLMClient(model=model)

# FIXED: Explicit key passing
api_key = os.environ.get("ANTHROPIC_API_KEY")
self.client = LiteLLMClient(model=model, api_key=api_key)
```

### Performance Data
- +17.1% improvement on AppWorld benchmark
- +8.6% improvement on FiNER benchmark
- v2.1 prompts show +17% success rate over v1.0
- 86.9% lower adaptation latency vs fine-tuning

### Configuration Defaults
| Component | Model | Purpose |
|-----------|-------|---------|
| Agent | claude-opus-4-5-20251101 | Main task execution |
| Reflector | gpt-4o-mini | Analyze execution (cheaper) |
| SkillManager | gpt-4o-mini | Update skills (cheaper) |

### Skillbook Location
Recommended: `.agent/skillbook/skillbook.json` (aligns with existing RALPH patterns)

## Files Created
- `/Users/nick/Desktop/ralph-orchestrator/.prompts/006-ace-docs-research/ace-docs-research.md` - Full research with code examples

## Decisions Needed
1. **Skillbook scope**: Project-specific (per-repo) vs global (user-level)?
2. **Skill pruning**: Auto-prune skills with negative effectiveness?
3. **Git tracking**: Commit skillbook to version control?

## Blockers
None - research complete, ready for implementation

## Next Step
Re-implement `src/ralph_orchestrator/learning/ace_adapter.py` following the integration pattern documented in ace-docs-research.md, with explicit API key passing.
