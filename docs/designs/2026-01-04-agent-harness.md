# Ralph Orchestrator: Agent Harness Architecture

**Date:** 2026-01-04
**Branch:** feat/agent-harness
**Status:** Draft
**Reference:** [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

## 1. Problem Statement

Ralph Orchestrator has three critical gaps:

1. **No codebase understanding** - Starts working without understanding existing code structure, patterns, or conventions.

2. **Context bloat** - Loading all user skills (100+) adds 50-100K tokens, causing "prompt is too long" errors.

3. **No tool optimization** - Skills and MCPs either all loaded or manually specified, no intelligent matching.

---

## 2. Solution: Two-Phase Harness Pattern

Inspired by Anthropic's autonomous-coding demo:

### Phase 1: Bootstrap (runs ONCE per codebase/prompt)

```
┌─────────────────────────────────────────────────────────────────┐
│                     BOOTSTRAP PHASE                             │
├─────────────────────────────────────────────────────────────────┤
│ 1. Codebase Analysis (if existing code)                         │
│    └─► Use Serena MCP for semantic understanding                │
│    └─► Use repomix for structure summarization                  │
│    └─► Cache to .agent/codebase-context.md                      │
│                                                                 │
│ 2. Prompt Analysis                                              │
│    └─► Parse prompt to identify task type (iOS, web, backend)   │
│    └─► Identify technologies mentioned                          │
│    └─► Extract acceptance criteria                              │
│                                                                 │
│ 3. Tool Discovery & Matching                                    │
│    └─► Discover available skills (~/.claude/skills/)            │
│    └─► Discover available MCPs (~/.mcp.json)                    │
│    └─► Match tools to task requirements                         │
│    └─► Suggest missing tools (web research)                     │
│                                                                 │
│ 4. User Approval                                                │
│    └─► Present recommended tool profile                         │
│    └─► User approves/modifies                                   │
│    └─► Save to .agent/tool-profile.json                         │
│                                                                 │
│ 5. Task List Generation                                         │
│    └─► Break prompt into trackable tasks                        │
│    └─► Create .agent/task-list.json                             │
│    └─► All tasks start as "status": "pending"                   │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 2: Iteration (runs REPEATEDLY until complete)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ITERATION PHASE                             │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: GET BEARINGS                                            │
│    └─► Read .agent/progress.md                                  │
│    └─► Read .agent/task-list.json                               │
│    └─► Check git log for recent commits                         │
│    └─► Count remaining tasks                                    │
│                                                                 │
│ Step 2: VERIFY EXISTING WORK                                    │
│    └─► Run 1-2 completed tasks to verify still working          │
│    └─► If broken: fix BEFORE new work                           │
│                                                                 │
│ Step 3: CHOOSE ONE TASK                                         │
│    └─► Pick highest-priority pending task                       │
│    └─► Focus on ONE task only                                   │
│                                                                 │
│ Step 4: IMPLEMENT                                               │
│    └─► Use TDD (test first)                                     │
│    └─► Follow codebase conventions from context                 │
│                                                                 │
│ Step 5: UPDATE STATUS                                           │
│    └─► Mark task "status": "completed"                          │
│    └─► NEVER remove or edit task descriptions                   │
│                                                                 │
│ Step 6: COMMIT                                                  │
│    └─► Descriptive commit message                               │
│    └─► Reference task ID                                        │
│                                                                 │
│ Step 7: UPDATE PROGRESS                                         │
│    └─► Append to .agent/progress.md                             │
│                                                                 │
│ Step 8: CLEAN EXIT                                              │
│    └─► No uncommitted changes, working state                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Skills vs MCPs

### Skills = Knowledge (loaded into context)
- Behavioral instructions, teach HOW
- High cost (~1-5K tokens each)
- Loaded via `Skill(name)`

### MCPs = Tools (invoked for actions)
- APIs, DO things
- Low cost (~100-500 tokens each)
- Called as `mcp__server__tool()`

### Project Skills (in `.claude/skills/` of ralph-orchestrator)

| Skill | Purpose | Invoked By |
|-------|---------|------------|
| `ralph-harness-bootstrap` | How to bootstrap codebase understanding | Python before loop |
| `ralph-harness-iteration` | 8-step iteration protocol | Each iteration |
| `ralph-prompt-optimization` | How to write/optimize Ralph prompts | Prompt gen command |

### MCPs by Category

| Category | MCPs | Purpose |
|----------|------|---------|
| **Bootstrap** | Serena*, repomix, claude-mem | Code understanding |
| **Validation** | playwright, sequential-thinking | Screenshots, reasoning |
| **Research** | tavily, Context7 | Web search, docs |

*Serena NOT INSTALLED - recommend installation

---

## 4. File Structure

### Project Skills
```
.claude/skills/
├── ralph-harness-bootstrap/
│   ├── SKILL.md                 (<100 lines)
│   └── references/
│       └── codebase-analysis.md
├── ralph-harness-iteration/
│   ├── SKILL.md                 (<100 lines)
│   └── references/
│       └── 8-step-protocol.md
└── ralph-prompt-optimization/
    ├── SKILL.md                 (<100 lines)
    └── references/
        └── prompt-structure.md
```

### Runtime Artifacts
```
.agent/
├── codebase-context.md          # Cached codebase understanding
├── tool-profile.json            # Approved skills + MCPs
├── task-list.json               # Tasks with status
├── progress.md                  # Session progress log
└── runs/{run-id}/               # Per-run isolation
```

---

## 5. Schemas

### tool-profile.json
```json
{
  "prompt_hash": "sha256:...",
  "created_at": "2026-01-04T15:00:00Z",
  "approved_by_user": true,
  "skills": {
    "required": ["ralph-harness-bootstrap", "ralph-harness-iteration"],
    "task_specific": ["ios-swift-expert", "test-driven-development"]
  },
  "mcps": {
    "bootstrap": ["serena", "repomix", "claude-mem"],
    "validation": ["playwright", "sequential-thinking"],
    "research": ["tavily", "Context7"]
  },
  "codebase": {
    "type": "existing",
    "languages": ["python", "typescript"],
    "context_file": ".agent/codebase-context.md"
  }
}
```

### task-list.json
```json
{
  "prompt_file": "prompts/my-prompt/PROMPT.md",
  "total_tasks": 15,
  "completed_tasks": 3,
  "tasks": [
    {
      "id": "task-001",
      "phase": "Phase 01",
      "description": "Set up database schema",
      "status": "completed",
      "completed_at": "2026-01-04T14:30:00Z"
    }
  ]
}
```

**Critical:** Tasks can ONLY be marked completed. NEVER remove/edit descriptions.

---

## 6. Python Implementation

### New Module: `src/ralph_orchestrator/harness/`
```
harness/
├── __init__.py
├── bootstrap.py           # Bootstrap phase coordinator
├── codebase_analyzer.py   # Uses Serena/repomix MCPs
├── prompt_analyzer.py     # Parses prompt content
├── tool_matcher.py        # Matches tools to requirements
└── task_generator.py      # Creates task-list.json
```

### Modified orchestrator.py
```python
async def run(self):
    # PHASE 1: BOOTSTRAP
    if not self._has_bootstrap_completed():
        await self._run_bootstrap_phase()

    # PHASE 2: ITERATION
    while not self._all_tasks_complete():
        await self._run_iteration()
```

### CLI Commands
```bash
ralph bootstrap --prompt PROMPT.md    # Bootstrap only
ralph run --prompt PROMPT.md          # Bootstrap + iterations
ralph run --skip-bootstrap            # Use existing profile
```

---

## 7. Implementation Plan

### Phase 1: Foundation
- [ ] Create `.claude/skills/` directory structure
- [ ] Write `ralph-harness-bootstrap` skill
- [ ] Write `ralph-harness-iteration` skill
- [ ] Document Serena MCP installation

### Phase 2: Python Integration
- [ ] Create `harness/` module
- [ ] Implement bootstrap phase
- [ ] Modify orchestrator to use harness

### Phase 3: CLI & UX
- [ ] Add `ralph bootstrap` command
- [ ] Add `--skip-bootstrap` flag
- [ ] User approval flow

---

## 8. Open Questions

1. **Serena Installation** - Auto-install missing MCPs or just recommend?

2. **Profile Validity** - How long is tool-profile.json valid?
   - A) Per-session
   - B) Until prompt hash changes
   - C) Until user re-bootstraps

3. **Task Granularity** - How fine should tasks be?
   - A) One per phase
   - B) One per acceptance criterion
   - C) AI decides

---

## References

- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Autonomous Coding Demo](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Serena MCP](https://github.com/oraios/serena)
