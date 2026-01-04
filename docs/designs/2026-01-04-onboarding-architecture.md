# Ralph Orchestrator: Onboarding Architecture Design

**Date:** 2026-01-04
**Branch:** feat/onboarding
**Status:** Draft

---

## 1. Problem Statement

Ralph Orchestrator currently has two critical gaps:

1. **No codebase understanding** - When given a prompt for an existing codebase, Ralph starts working without understanding the codebase structure, patterns, or conventions.

2. **Context bloat** - Loading all user skills (100+) adds 50-100K tokens, causing "prompt is too long" errors and inefficient token usage.

3. **No tool optimization** - Skills and MCPs are either all loaded or manually specified, with no intelligent matching to the task at hand.

---

## 2. Solution: Two-Phase Architecture

Inspired by Anthropic's autonomous-coding demo, Ralph will use a **two-phase pattern**:

### Phase 1: Onboarding (runs ONCE per codebase/prompt)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ONBOARDING PHASE                            │
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
│    └─► Create .agent/task-list.json (like feature_list.json)    │
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
│    └─► Mark task "status": "completed" in task-list.json        │
│    └─► NEVER remove or edit task descriptions                   │
│                                                                 │
│ Step 6: COMMIT                                                  │
│    └─► Descriptive commit message                               │
│    └─► Reference task ID                                        │
│                                                                 │
│ Step 7: UPDATE PROGRESS                                         │
│    └─► Append to .agent/progress.md                             │
│    └─► What was done, what's next                               │
│                                                                 │
│ Step 8: CLEAN EXIT                                              │
│    └─► No uncommitted changes                                   │
│    └─► Working state                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Skills vs MCPs (Critical Distinction)

### Skills = Knowledge (loaded into context)
- Behavioral instructions
- High context cost (~1-5K tokens each)
- Teach HOW to do things
- Loaded via `Skill(name)` tool

### MCPs = Tools (invoked for actions)
- APIs and capabilities
- Low context cost (~100-500 tokens each)
- DO things
- Called as `mcp__server__tool()`

### Project Skills (in `.claude/skills/` of ralph-orchestrator)

| Skill | Purpose | ~Lines | Invoked By |
|-------|---------|--------|------------|
| `ralph-onboarding` | How to understand a codebase | <100 | Python before orchestration |
| `ralph-iteration-protocol` | 10-step iteration process | <100 | Each iteration start |
| `ralph-prompt-optimization` | How to write/optimize Ralph prompts | <100 | Prompt generation command |

### MCP Categories

**For Onboarding:**
| MCP | Purpose | Status |
|-----|---------|--------|
| Serena | Semantic code analysis via LSP | NOT INSTALLED - recommend |
| repomix | Codebase summarization | Available |
| claude-mem | Past work on codebase | Available |

**For Validation:**
| MCP | Purpose | Status |
|-----|---------|--------|
| playwright | Browser screenshots | Available |
| sequential-thinking | Structured reasoning | Available |

**For Research:**
| MCP | Purpose | Status |
|-----|---------|--------|
| tavily | Web search | Available |
| Context7 | Library documentation | Available |

---

## 4. File Structure

### Project Skills
```
.claude/skills/
├── ralph-onboarding/
│   ├── SKILL.md                 (<100 lines)
│   └── references/
│       └── codebase-analysis.md
├── ralph-iteration-protocol/
│   ├── SKILL.md                 (<100 lines)
│   └── references/
│       └── 10-step-protocol.md
└── ralph-prompt-optimization/
    ├── SKILL.md                 (<100 lines)
    └── references/
        └── prompt-structure.md
```

### Runtime Artifacts
```
.agent/
├── codebase-context.md          # Cached codebase understanding
├── tool-profile.json            # Approved skills + MCPs for this run
├── task-list.json               # Tasks with status (like feature_list.json)
├── progress.md                  # Session-by-session progress log
└── runs/
    └── {run-id}/
        ├── manifest.json
        └── iteration-{n}.log
```

---

## 5. Tool Profile Schema

```json
{
  "prompt_hash": "sha256:abc123...",
  "created_at": "2026-01-04T15:00:00Z",
  "approved_by_user": true,
  "skills": {
    "required": [
      "ralph-onboarding",
      "ralph-iteration-protocol"
    ],
    "task_specific": [
      "ios-swift-expert",
      "test-driven-development"
    ]
  },
  "mcps": {
    "onboarding": ["serena", "repomix", "claude-mem"],
    "validation": ["playwright", "sequential-thinking"],
    "research": ["tavily", "Context7"]
  },
  "codebase": {
    "type": "existing",
    "languages": ["python", "typescript"],
    "frameworks": ["fastapi", "react"],
    "context_file": ".agent/codebase-context.md"
  }
}
```

---

## 6. Task List Schema

Modeled after autonomous-coding's `feature_list.json`:

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
      "acceptance_criteria": [
        "Tables created",
        "Migrations work"
      ],
      "status": "completed",
      "completed_at": "2026-01-04T14:30:00Z",
      "evidence": ["validation-evidence/01-db-schema.png"]
    },
    {
      "id": "task-002",
      "phase": "Phase 01",
      "description": "Implement user authentication",
      "acceptance_criteria": [
        "Login works",
        "JWT tokens generated"
      ],
      "status": "pending",
      "completed_at": null,
      "evidence": []
    }
  ]
}
```

**Critical Rule:** Tasks can ONLY be marked as completed. NEVER remove or edit task descriptions.

---

## 7. Python Implementation Changes

### New Module: `src/ralph_orchestrator/onboarding/`

```
onboarding/
├── __init__.py
├── codebase_analyzer.py     # Uses Serena/repomix MCPs
├── prompt_analyzer.py       # Parses prompt content
├── tool_matcher.py          # Matches tools to requirements
├── profile_generator.py     # Creates tool-profile.json
└── task_generator.py        # Creates task-list.json
```

### Modified: `src/ralph_orchestrator/orchestrator.py`

```python
async def run(self):
    # PHASE 1: ONBOARDING (new)
    if not self._has_onboarding_completed():
        await self._run_onboarding_phase()

    # PHASE 2: ITERATION (existing, but improved)
    while not self._all_tasks_complete():
        await self._run_iteration()
```

### New CLI Command: `ralph onboard`

```bash
# Explicitly run onboarding without starting iterations
ralph onboard --prompt PROMPT.md

# Run with onboarding (default behavior)
ralph run --prompt PROMPT.md

# Skip onboarding (use existing profile)
ralph run --prompt PROMPT.md --skip-onboard
```

---

## 8. Skill Content (Draft)

### ralph-onboarding/SKILL.md

```markdown
---
name: ralph-onboarding
description: Onboard to a codebase before Ralph orchestration. Invoked automatically by Ralph Python code.
---

# Ralph Codebase Onboarding

## Purpose

Build deep understanding of codebase BEFORE starting implementation work.

## When Invoked

Automatically by Ralph orchestrator when:
- First run on a new prompt
- Codebase has changed significantly
- User requests re-onboarding

## Process

1. **Identify Codebase Type**
   - Fresh build (no existing code) → Skip to prompt analysis
   - Existing code → Continue with analysis

2. **Analyze Codebase** (existing code only)
   - Use Serena MCP for semantic understanding (if available)
   - Use repomix for structure summarization
   - Identify: languages, frameworks, patterns, conventions
   - Search claude-mem for past work on this codebase

3. **Cache Understanding**
   - Write to .agent/codebase-context.md
   - Include: structure, patterns, key files, conventions

4. **Analyze Prompt**
   - Parse PROMPT.md for task type
   - Extract technologies mentioned
   - List acceptance criteria

5. **Match Tools**
   - Discover available skills and MCPs
   - Match to prompt requirements
   - Flag missing recommended tools

6. **Generate Profile**
   - Create .agent/tool-profile.json
   - Present to user for approval

## Output Files

- `.agent/codebase-context.md`
- `.agent/tool-profile.json`
- `.agent/task-list.json`
```

---

## 9. Implementation Plan

### Phase 1: Foundation (This PR)
- [ ] Create `.claude/skills/` directory structure
- [ ] Write `ralph-onboarding` skill
- [ ] Write `ralph-iteration-protocol` skill
- [ ] Add Serena MCP installation instructions

### Phase 2: Python Integration
- [ ] Create `onboarding/` module
- [ ] Implement codebase analyzer
- [ ] Implement prompt analyzer
- [ ] Implement tool matcher
- [ ] Modify orchestrator to call onboarding

### Phase 3: CLI & UX
- [ ] Add `ralph onboard` command
- [ ] Add `--skip-onboard` flag
- [ ] User approval flow for tool profile

### Phase 4: Testing & Validation
- [ ] Test with fresh codebase
- [ ] Test with existing codebase
- [ ] Test tool matching accuracy

---

## 10. Open Questions

1. **Serena MCP Installation** - Should Ralph auto-install missing MCPs, or just recommend?

2. **Profile Caching** - How long should tool-profile.json be valid? Per-session? Per-prompt-hash?

3. **Task Granularity** - How fine should task-list.json tasks be? Per-phase? Per-acceptance-criterion?

4. **Codebase Change Detection** - How to detect when codebase-context.md needs refresh?

---

## References

- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude Quickstarts: Autonomous Coding Demo](https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding)
- [Serena MCP](https://github.com/oraios/serena)
