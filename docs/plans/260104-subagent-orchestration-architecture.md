# Ralph Subagent Orchestration Architecture

**Date:** 2026-01-04
**Status:** DESIGN PROPOSAL
**Author:** Claude (via brainstorming session)

## Executive Summary

Hub-and-spoke subagent orchestration enabling Ralph to deploy "full force from attempt 1" with parallel specialized subagents. Key innovations:

- **Validation-first with error content detection** - Screenshots checked for ERROR CONTENT, not just existence
- **Parallel subagents by default** - No gradual escalation; full power on first attempt
- **Dynamic MCP discovery** - Adapts to user's installed MCP servers
- **Tool restrictions per subagent** - Prevents context bloat (saves 17k tokens per agent)
- **All subagents use Opus** - Quality over cost per user requirements
- **sequential-thinking REQUIRED** - All subagents use structured reasoning

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RALPH ORCHESTRATOR                        │
│                  (Main Iteration Loop)                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  DISPATCH LAYER                      │    │
│  │   Spawns parallel subagents with restricted tools    │    │
│  └──────────────┬───────────────┬──────────────┬───────┘    │
│                 │               │              │             │
│        ┌────────▼─────┐  ┌──────▼─────┐  ┌────▼──────┐     │
│        │  VALIDATOR   │  │ RESEARCHER │  │IMPLEMENTER│     │
│        │  (Opus)      │  │  (Opus)    │  │  (Opus)   │     │
│        │              │  │            │  │           │     │
│        │ playwright   │  │ tavily     │  │ Read/Write│     │
│        │ Read/Bash    │  │ Context7   │  │ Edit/Bash │     │
│        │ seq-think    │  │ seq-think  │  │ seq-think │     │
│        └──────┬───────┘  └─────┬──────┘  └─────┬─────┘     │
│               │                │               │            │
│        ┌──────▼────────────────▼───────────────▼──────┐    │
│        │          .agent/coordination/                 │    │
│        │   shared-context.md | subagent-results/      │    │
│        │   attempt-journal.md                          │    │
│        └──────────────────────┬────────────────────────┘    │
│                               │                             │
│        ┌──────────────────────▼────────────────────────┐    │
│        │              AGGREGATION LAYER                │    │
│        │   Collects results → Decides PASS/RETRY       │    │
│        └───────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Core Constraints (from Claude Code)

1. **Subagents live in silos** - Cannot communicate directly with each other
2. **Single input/output** - Subagent receives task once, returns result once
3. **Isolated context windows** - Each subagent has own 200k token context
4. **No inter-subagent dependencies** - Must design for parallel, not sequential

### Design Principles

1. **Full force from attempt 1** - Deploy all relevant subagents in parallel immediately
2. **Orchestrator loop IS escalation** - No separate "debugger" agent; iteration provides escalation
3. **Shared files for coordination** - `.agent/coordination/` is the communication bus
4. **Tool restrictions prevent bloat** - Each subagent gets ONLY their domain tools

---

## Subagent Specifications

### 1. VALIDATOR

**Purpose:** Verify acceptance criteria by checking evidence for ERRORS, not just existence.

**Tools:**
- REQUIRED: `sequential-thinking`, `Read`, `Bash`
- MCP: `playwright` (browser automation)

**Prompt Template:**
```
You are a VALIDATION specialist. Your ONLY job is to verify acceptance criteria.

CRITICAL: Check evidence for ERRORS, not just existence.

For screenshots:
1. Use playwright to capture fresh screenshot if needed
2. Use sequential-thinking to analyze screenshot content
3. Look for: error messages, red text, warning icons, "failed" text, "Network request failed"
4. Look for: success indicators, expected UI elements, correct state
5. Report: PASS (with evidence) or FAIL (with specific error found)

For test output:
1. Read test output files completely
2. Search for: "Error:", "FAILED", "Exception", assertion failures, non-zero exit codes
3. Search for: "PASSED", "SUCCESS", expected output patterns
4. Report specific line numbers where errors found

For logs:
1. Read log files from validation-evidence directory
2. Search for ERROR, WARN, FATAL, stack traces, "connection refused"
3. Extract relevant context around errors (5 lines before/after)
4. Report timestamp + error type + message

OUTPUT FORMAT (JSON):
{
  "verdict": "PASS" | "FAIL",
  "phase": "phase-XX",
  "evidence_analyzed": ["file1.png", "output.txt"],
  "errors_found": [
    {"file": "dashboard.png", "error": "Network request failed visible in screenshot"},
    {"file": "test-output.txt", "line": 47, "error": "AssertionError: expected 200, got 500"}
  ],
  "success_indicators": ["Login button rendered", "API returned 200"],
  "confidence": 0.95,
  "recommendation": "Fix network connectivity before re-running validation"
}
```

**Token Budget:** ~15,000 tokens (minimal tools)

---

### 2. RESEARCHER

**Purpose:** Investigate unknowns, gather external knowledge, find solutions.

**Tools:**
- REQUIRED: `sequential-thinking`, `Read`, `Grep`, `Glob`
- MCP: `tavily` (web search), `Context7` (library docs), `WebSearch`

**Prompt Template:**
```
You are a RESEARCH specialist. Your job is to find solutions and gather knowledge.

Use sequential-thinking to structure your research approach.

RESEARCH WORKFLOW:
1. Understand the question/problem clearly
2. Search for relevant documentation (Context7 for libraries)
3. Search web for solutions (tavily for current best practices)
4. Read relevant files in codebase for context
5. Synthesize findings into actionable recommendations

OUTPUT FORMAT (JSON):
{
  "question": "How to fix iOS code signing for CI/CD",
  "sources_consulted": [
    {"type": "Context7", "library": "fastlane", "topic": "match"},
    {"type": "tavily", "query": "iOS code signing 2026 best practices"},
    {"type": "file", "path": "fastlane/Fastfile"}
  ],
  "findings": [
    {"source": "fastlane docs", "insight": "Use match for CI signing"},
    {"source": "web", "insight": "Apple requires notarization for macOS"}
  ],
  "recommendation": "Implement fastlane match with readonly mode in CI",
  "confidence": 0.85,
  "uncertainties": ["Team ID configuration unclear"]
}
```

**Token Budget:** ~18,000 tokens

---

### 3. IMPLEMENTER

**Purpose:** Write and modify code, execute builds, run tests.

**Tools:**
- REQUIRED: `sequential-thinking`, `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`
- OPTIONAL MCP: `xc-mcp` (if iOS), `repomix` (code context)

**Prompt Template:**
```
You are an IMPLEMENTATION specialist. Your job is to write and modify code.

Use sequential-thinking to plan your implementation approach BEFORE writing code.

IMPLEMENTATION WORKFLOW:
1. Read existing code to understand patterns and conventions
2. Plan the implementation (files to create/modify, order of changes)
3. Make changes incrementally (one file at a time)
4. Run tests/builds after each significant change
5. Report results with specific file paths and line numbers

CONSTRAINTS:
- Follow existing code style and patterns
- Don't over-engineer (YAGNI)
- Write minimal code to satisfy requirements
- Run verification commands after changes

OUTPUT FORMAT (JSON):
{
  "task": "Add validation evidence freshness check",
  "files_modified": [
    {"path": "src/orchestrator.py", "changes": "Added _check_evidence_freshness method"}
  ],
  "files_created": [],
  "tests_run": "pytest tests/test_validation.py",
  "test_result": "PASSED (5/5)",
  "build_result": "SUCCESS",
  "summary": "Added freshness check comparing file mtime to run_start_time"
}
```

**Token Budget:** ~20,000 tokens

---

### 4. MEMORY_AGENT

**Purpose:** Query and store cross-session knowledge via claude-mem.

**Tools:**
- REQUIRED: `sequential-thinking`
- MCP: `claude-mem` (search, timeline, get_observations)

**Prompt Template:**
```
You are a MEMORY specialist. Your job is to retrieve relevant past work and decisions.

MEMORY WORKFLOW:
1. Search for relevant past observations using semantic queries
2. Get timeline context around important findings
3. Fetch full details for the most relevant IDs
4. Synthesize into actionable context for current task

QUERY PATTERNS:
- "How did we solve X before?" → search(query="X solution")
- "What decisions were made about Y?" → search(type="decision", query="Y")
- "What happened last time we tried Z?" → timeline(query="Z failed")

OUTPUT FORMAT (JSON):
{
  "query": "validation evidence checking patterns",
  "observations_found": 5,
  "relevant_ids": [10612, 10474],
  "key_findings": [
    {"id": 10474, "insight": "Phase 01 validation used real script output with PIDs"},
    {"id": 10612, "insight": "Token budgets: 17k savings per agent with restrictions"}
  ],
  "recommendations": [
    "Reuse the validation evidence directory structure from Phase 01",
    "Apply same freshness checking pattern"
  ],
  "past_mistakes_to_avoid": [
    "Don't check file existence only - check content for errors"
  ]
}
```

**Token Budget:** ~12,000 tokens (minimal tools)

---

### 5. ANALYST

**Purpose:** Examine logs, errors, system state for root cause analysis.

**Tools:**
- REQUIRED: `sequential-thinking`, `Read`, `Grep`, `Bash`

**Prompt Template:**
```
You are an ANALYSIS specialist. Your job is to diagnose errors and identify root causes.

Use sequential-thinking for systematic root cause analysis.

ANALYSIS WORKFLOW:
1. Read error logs/output completely
2. Identify the FIRST error (root cause often earliest)
3. Trace the error to its source
4. Search for patterns across multiple files
5. Formulate hypothesis and verify

ERROR PATTERNS TO CHECK:
- Stack traces: Find the topmost application code frame
- Exit codes: Non-zero indicates failure
- Timestamps: Identify when failure started
- Environment: Missing variables, wrong paths
- Dependencies: Version mismatches, missing packages

OUTPUT FORMAT (JSON):
{
  "symptom": "Mobile app shows 'Network request failed'",
  "logs_analyzed": ["metro.log", "api-server.log"],
  "error_chain": [
    {"timestamp": "06:52:01", "source": "metro", "error": "Bundle ready"},
    {"timestamp": "07:01:15", "source": "app", "error": "fetch() rejected - ECONNREFUSED"}
  ],
  "root_cause": "Backend server not running during mobile app test",
  "evidence": "No process listening on port 8085 at test time",
  "fix_recommendation": "Start backend server before mobile validation",
  "confidence": 0.92
}
```

**Token Budget:** ~15,000 tokens

---

## Token Budget Mathematics

### Main Orchestrator (Ralph Iteration Loop)

| Component | Tokens |
|-----------|--------|
| System prompt | 10,000 |
| Task prompt + acceptance criteria | 30,000 |
| Attempt journals (5 attempts) | 5,000 |
| Full tool definitions (~80 tools) | 20,000 |
| Working space for responses | 100,000 |
| **TOTAL** | **165,000** |

Fits within Opus 200k context window with 35k headroom.

### Per Subagent (with tool restrictions)

| Component | Tokens |
|-----------|--------|
| Focused system prompt | 5,000 |
| Task context (from parent) | 10,000 |
| Restricted tools (5-10 tools) | 3,000 |
| sequential-thinking MCP | 500 |
| Domain MCP tools | 5,000 |
| Working space | 45,000 |
| Output buffer | 5,000 |
| **TOTAL** | **73,500** |

### Savings from Tool Restriction

| Scenario | Tools | Tokens |
|----------|-------|--------|
| Full tool inheritance | ~80 tools | 20,000 |
| Restricted tools | 5-10 tools | 3,000 |
| **SAVINGS** | | **17,000** |

With 5 parallel subagents: **85,000 tokens saved total**

### Parallel Execution Cost (Opus)

| Metric | Value |
|--------|-------|
| Main orchestrator | 165,000 tokens |
| 5 parallel subagents | 5 × 73,500 = 367,500 tokens |
| **Total per iteration** | ~530,000 tokens across all contexts |

**Cost at Opus rates ($15/M input, $75/M output):**
- Input: 530,000 × $15/M = ~$8/iteration
- Output: ~100,000 × $75/M = ~$7.50/iteration
- **Per iteration: ~$15.50**
- **10 iterations: ~$155**

User explicitly required Opus for quality; this is the cost.

---

## MCP Discovery & Configuration

### Discovery Algorithm

```python
def discover_mcps() -> Dict[str, MCPServer]:
    """Read user's ~/.claude.json and extract available MCPs."""
    claude_json = Path.home() / ".claude.json"
    config = json.loads(claude_json.read_text())

    all_mcps = config.get("mcpServers", {})
    disabled = set()

    # Check project-specific disabled list
    project_settings = config.get("projects", {}).get(str(Path.cwd()), {})
    disabled = set(project_settings.get("disabledMcpServers", []))

    # Return enabled MCPs
    return {
        name: server
        for name, server in all_mcps.items()
        if name not in disabled
    }
```

### Domain Detection

```python
def detect_project_domain() -> Set[str]:
    """Detect project domain to select appropriate MCPs."""
    domains = set()

    # iOS detection
    if list(Path.cwd().glob("*.xcodeproj")) or (Path.cwd() / "Package.swift").exists():
        domains.add("ios")

    # Web frontend detection
    if (Path.cwd() / "package.json").exists():
        pkg = json.loads((Path.cwd() / "package.json").read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "react" in deps or "vue" in deps or "svelte" in deps:
            domains.add("web-frontend")

    # Python backend detection
    if (Path.cwd() / "requirements.txt").exists() or (Path.cwd() / "pyproject.toml").exists():
        domains.add("python-backend")

    return domains
```

### MCP-to-Subagent Mapping

| Subagent Type | Required MCPs | Optional MCPs (by domain) |
|---------------|---------------|--------------------------|
| VALIDATOR | sequential-thinking | playwright, chrome-devtools |
| RESEARCHER | sequential-thinking | tavily, Context7, firecrawl-mcp |
| IMPLEMENTER | sequential-thinking | xc-mcp (iOS), repomix, serena |
| MEMORY_AGENT | sequential-thinking, memory | - |
| ANALYST | sequential-thinking | - |

### Configuration Dataclass

```python
@dataclass
class OrchestrationConfig:
    """Configuration for subagent orchestration."""

    # Model settings (user required Opus)
    subagent_model: str = "opus"

    # MCP requirements
    required_mcps: List[str] = field(default_factory=lambda: [
        "sequential-thinking",  # REQUIRED for all
    ])
    optional_mcps: List[str] = field(default_factory=lambda: [
        "playwright", "tavily", "Context7", "repomix",
        "xc-mcp", "tuist", "chrome-devtools", "serena",
        "memory", "firecrawl-mcp"
    ])

    # Subagent profiles
    subagent_profiles: Dict[str, SubagentProfile] = field(default_factory=dict)

    # Token budgets
    max_subagent_context: int = 73500
    max_parallel_subagents: int = 5

    # Coordination
    coordination_dir: str = ".agent/coordination"

    # Behavior
    always_parallel: bool = True  # Full force from attempt 1


@dataclass
class SubagentProfile:
    """Profile defining a subagent type's capabilities."""
    name: str
    description: str
    required_tools: List[str]  # Base Claude Code tools
    required_mcps: List[str]   # MCP servers required
    optional_mcps: List[str]   # MCP servers used if available
    prompt_template: str       # System prompt for this type
    max_tokens: int = 73500    # Context budget
```

---

## Coordination Protocol

### Shared File Structure

```
.agent/
└── coordination/
    ├── current-attempt.json      # Metadata for current attempt
    ├── shared-context.md         # Common context all subagents read
    ├── attempt-journal.md        # Full history of all attempts
    └── subagent-results/
        ├── validator-001.json    # Validator findings
        ├── researcher-001.json   # Research results
        ├── implementer-001.json  # Implementation status
        ├── memory-001.json       # Memory query results
        └── analyst-001.json      # Analysis findings
```

### current-attempt.json Schema

```json
{
  "attempt_number": 3,
  "started_at": "2026-01-04T11:45:00Z",
  "phase": "phase-04",
  "acceptance_criteria": "Mobile app shows orchestrator list",
  "subagents_dispatched": ["validator", "researcher", "implementer"],
  "status": "in_progress",
  "previous_attempt_summary": "Failed - Network request failed in screenshot"
}
```

### attempt-journal.md Format

```markdown
# Attempt Journal

## Attempt 1 (2026-01-04T10:30:00Z)
**Phase:** phase-04
**Subagents:** validator, implementer

### Validator Results
- **Verdict:** FAIL
- **Evidence:** dashboard.png shows "Network request failed"
- **Root Cause:** Backend server not running

### Implementer Results
- **Status:** BLOCKED
- **Reason:** Waiting for validator to pass

### Attempt Outcome
**Result:** FAIL
**Reason:** Backend server offline during mobile testing
**Next Action:** Start backend server, retry validation

---

## Attempt 2 (2026-01-04T10:45:00Z)
...
```

### Coordination Flow

```
1. DISPATCH (Main Orchestrator)
   ├── Write current-attempt.json
   ├── Write shared-context.md (task context)
   └── Spawn N parallel subagents with restricted tools

2. EXECUTE (Each Subagent, in parallel)
   ├── Read shared-context.md
   ├── Use sequential-thinking for structured work
   ├── Perform domain-specific task
   └── Write results to subagent-results/{type}-{id}.json

3. AGGREGATE (Main Orchestrator)
   ├── Wait for all subagents to complete
   ├── Read all subagent-results/*.json
   ├── Merge into attempt-journal.md
   └── Decide: SUCCESS (exit) or NEXT_ATTEMPT (loop)

4. ITERATE (if NEXT_ATTEMPT)
   ├── Update shared-context.md with learnings
   ├── Increment attempt_number
   └── Return to step 1
```

---

## Implementation Plan

### Phase 1: Core Data Structures

**Files to create/modify:**
- `src/ralph_orchestrator/orchestration/__init__.py`
- `src/ralph_orchestrator/orchestration/config.py` - OrchestrationConfig, SubagentProfile
- `src/ralph_orchestrator/orchestration/mcp_discovery.py` - MCP discovery functions

**Acceptance Criteria:**
- [ ] OrchestrationConfig dataclass with all fields
- [ ] SubagentProfile dataclass with prompt templates
- [ ] Default profiles for all 5 subagent types
- [ ] Unit tests for config validation

### Phase 2: MCP Discovery

**Files to create/modify:**
- `src/ralph_orchestrator/orchestration/mcp_discovery.py`

**Acceptance Criteria:**
- [ ] `discover_mcps()` reads ~/.claude.json
- [ ] `detect_project_domain()` identifies iOS/web/python
- [ ] `get_subagent_tools()` returns appropriate tools for subagent type
- [ ] Handles missing/disabled MCPs gracefully

### Phase 3: Subagent Spawning

**Files to create/modify:**
- `src/ralph_orchestrator/orchestration/subagent.py`
- `src/ralph_orchestrator/orchestration/dispatcher.py`

**Acceptance Criteria:**
- [ ] `spawn_subagent()` creates Task with restricted tools
- [ ] `dispatch_parallel()` spawns N subagents concurrently
- [ ] Tool restrictions enforced via AgentDefinition.tools
- [ ] sequential-thinking included in all subagents

### Phase 4: Coordination Files

**Files to create/modify:**
- `src/ralph_orchestrator/orchestration/coordination.py`

**Acceptance Criteria:**
- [ ] `init_coordination_dir()` creates .agent/coordination/
- [ ] `write_current_attempt()` updates current-attempt.json
- [ ] `write_shared_context()` generates shared-context.md
- [ ] `collect_results()` reads subagent-results/*.json
- [ ] `update_journal()` appends to attempt-journal.md

### Phase 5: Integration with Ralph Loop

**Files to modify:**
- `src/ralph_orchestrator/orchestrator.py`
- `src/ralph_orchestrator/__main__.py`

**Acceptance Criteria:**
- [ ] `enable_orchestration` parameter added to RalphOrchestrator
- [ ] When enabled, uses subagent dispatch instead of single-agent execution
- [ ] Attempt journal passed between iterations
- [ ] SUCCESS/FAIL decided based on aggregated subagent results

---

## Risk Assessment

### Technical Risks

| Risk | Mitigation |
|------|------------|
| MCP not installed | Graceful degradation; warn user, suggest alternatives |
| Subagent timeout | Configurable timeout per subagent type |
| Context overflow | Token budget math validated; restricted tools |
| Coordination file conflicts | Use atomic writes, file locking |

### Cost Risks

| Risk | Mitigation |
|------|------------|
| Opus cost per iteration | Feature is opt-in (enable_orchestration=False by default) |
| Runaway iterations | Existing max_iterations limit applies |
| Parallel subagent cost | Configurable max_parallel_subagents |

### Quality Risks

| Risk | Mitigation |
|------|------------|
| Subagent returns wrong format | Validate output against schema |
| False positives in validation | Multiple validators cross-check |
| Missed errors in screenshots | Explicit error pattern list in prompt |

---

## Unresolved Questions

1. **Subagent retry policy** - If a subagent fails (timeout, error), should we retry that specific subagent or fail the whole attempt?

2. **Result confidence aggregation** - How to combine multiple subagent confidence scores into overall pass/fail decision?

3. **MCP permission model** - Should user pre-approve MCP usage per subagent type, or allow any available?

4. **Journal truncation** - How to handle attempt-journal.md growing beyond token limits? Summarization strategy?

5. **Subagent specialization** - Should we allow custom subagent profiles beyond the 5 defaults?

---

## References

- [Claude Code Subagent Orchestration Best Practices](claude-mem:#10608)
- [Ralph Subagent Architecture Decision](claude-mem:#10607)
- [Hybrid Orchestration Architecture with Token Budgets](claude-mem:#10612)
- [Claude Agent SDK Documentation](Context7:/anthropic/anthropic-sdk-python)
