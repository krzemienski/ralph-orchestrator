# ACE + RALPH Implementation

<objective>
Execute the implementation plan phases 1-2: Fix critical bugs and implement proper ACE integration.

Purpose: Get ACE learning working correctly in RALPH
Output: Working ACE integration with skillbook injection and learning triggers
</objective>

<context>
ACE Research: @.prompts/006-ace-docs-research/ace-docs-research.md
RALPH Research: @.prompts/007-ralph-integration-research/ralph-integration-research.md
Implementation Plan: @.prompts/008-ace-ralph-plan/ace-ralph-plan.md

Follow the plan exactly for phases 1 and 2.
</context>

<requirements>
**Phase 1 - Fix Critical Bugs:**
- Fix ANTHROPIC_API_KEY propagation to LiteLLMClient
- Fix any import or initialization errors
- Ensure ace_adapter.py follows ACE official patterns
- Add proper error handling for missing API keys

**Phase 2 - Proper Integration:**
- Implement skillbook injection in `_enhance_prompt_with_instructions()`
- Implement learning trigger after `_aexecute_iteration()` success
- Map RALPH iteration data to ACE reflection format
- Implement async learning queue for non-blocking operation
- Ensure skillbook persists to `.agent/skillbook/skillbook.json`

**Quality Requirements:**
- No breaking changes to non-learning mode
- Graceful degradation if learning fails
- Proper logging for debugging
- Thread-safe operations
</requirements>

<implementation>
**Follow ACE Official Patterns:**
Use patterns from the ACE research output. Key patterns:
- Initialize LiteLLMClient with explicit api_key parameter
- Use ACE's inject → execute → learn cycle
- Map output to AgentOutput format for reflection
- Use threading.Lock for skillbook access

**Specific Changes (from RALPH research):**
Reference the integration points identified in ralph-integration-research.md:
- Skillbook injection location: {from research}
- Learning trigger location: {from research}
- Data mapping: {from research}

**Error Handling:**
- If API key missing: log warning, continue without learning
- If reflection fails: log error, don't crash orchestration
- If skillbook corrupt: reinitialize with empty skillbook

**Environment Variables:**
Ensure these propagate correctly:
- ANTHROPIC_API_KEY
- OPENAI_API_KEY (fallback)
- Any ACE-specific configs
</implementation>

<output>
Modify files:
- `src/ralph_orchestrator/learning/ace_adapter.py` - Complete rewrite following ACE patterns
- `src/ralph_orchestrator/orchestrator.py` - Add learning integration hooks
- `src/ralph_orchestrator/adapters/base.py` - Add skillbook injection method

Create/modify:
- `.agent/skillbook/` directory structure
- Any new helper modules needed
</output>

<verification>
**Phase 1 Validation:**
```bash
# Must complete without API key errors
ralph run --learning --dry-run -p "echo test"

# Check logs for successful ACE initialization
# Should see: "ACE learning adapter initialized" or similar
```

**Phase 2 Validation:**
```bash
# Run a real task with learning
ralph run --learning -p "Create a simple Python hello world script"

# Verify skillbook was updated
cat .agent/skillbook/skillbook.json | jq .

# Should see skills extracted from the task
```

**Integration Check:**
```bash
# Run monitoring dashboard while executing
./scripts/ralph-with-monitor.sh "Add a comment to README"

# Verify metrics capture and no errors
```
</verification>

<summary_requirements>
Create `.prompts/009-ace-ralph-implement/SUMMARY.md`

Must include:
- **One-liner**: What was implemented and working status
- **Files Created/Modified**: List with descriptions
- **Bug Fixes**: What was broken, how fixed
- **Integration Points**: Where ACE connects to RALPH
- **Validation Results**: Output of verification commands
- **Decisions Made**: Any implementation choices
- **Blockers Encountered**: Issues during implementation
- **Next Step**: "Execute Phase 3: Benchmark infrastructure"
</summary_requirements>

<success_criteria>
- `ralph run --learning` completes without API key errors
- Skillbook injection visible in enhanced prompts
- Learning triggers after successful iterations
- Skillbook.json updated with extracted skills
- Non-learning mode still works (`ralph run` without --learning)
- No regressions in existing functionality
- SUMMARY.md documents implementation details
</success_criteria>

<constraints>
**CRITICAL:**
- Do NOT write pytest or unit tests
- Validate ONLY through end-to-end execution
- Use monitoring dashboard for validation
- Use real ralph commands for testing
</constraints>
