# ACE Monitoring Suite Implementation

```yaml
type: do
topic: ace-monitoring
version: 1
created: 2026-01-10T02:46:00-05:00
references:
  - plans/260110-ace-monitoring-comprehensive-implementation.md
dependencies:
  - Component 1 (ACE API Key Fix) - COMPLETED
output_location: .prompts/005-ace-monitoring-do/ace-monitoring-do.md
validation_approach: end-to-end functional testing only (NO pytest/unit tests)
extended_thinking: required
```

---

<objective>
Implement Components 2-5 of the Ralph Orchestrator ACE Monitoring Suite with production-quality code, following the exact specifications in the implementation plan. This creates a fully observable orchestration system with real-time log streaming, tool call tracking, context visualization, and a tmux-based dashboard.

**Critical constraint**: Do NOT write any pytest or unit tests. Only validate from the end user or end system perspective using the provided bash validation scripts.

**Implementation philosophy**: Thoroughly analyze each component before writing code. Deeply consider integration points. Systematically verify each phase before proceeding to the next.
</objective>

<context>
## Reference Documents

@plans/260110-ace-monitoring-comprehensive-implementation.md - Complete implementation specifications with code snippets

## Current State

- **Branch**: feat/ace-learning-loop
- **Component 1**: ACE Learning API Key Fix - COMPLETED
- **Existing infrastructure**:
  - `src/ralph_orchestrator/logging/stream_logger.py` - StreamLogger class (partially implemented)
  - `src/ralph_orchestrator/logging/__init__.py` - Module exports
  - `scripts/validate-log-streaming.sh` - Validation script for Component 2

## Ralph Architecture Understanding

Ralph Orchestrator is a production-ready AI orchestration system that:
1. Runs AI agents in a continuous loop until task completion
2. Supports multiple adapters: Claude, ACP, Kiro (formerly Q Chat), Gemini
3. Uses `.agent/` directory for state: logs, metrics, skillbook, checkpoints
4. Has VerboseLogger for detailed logging and CostTracker for usage metrics
5. CLI entry point: `python -m ralph_orchestrator run [options]`

## Key Files to Understand

Before implementing, deeply analyze:
- `src/ralph_orchestrator/orchestrator.py` - Main orchestration loop
- `src/ralph_orchestrator/main.py` - CLI configuration and entry point
- `src/ralph_orchestrator/__main__.py` - Module entry point
- `src/ralph_orchestrator/verbose_logger.py` - Existing logging infrastructure
- `src/ralph_orchestrator/adapters/base.py` - Base adapter with prompt enhancement
</context>

<requirements>
## PHASE 1: Complete Log Streaming (Component 2)

### Objective
Enable real-time visibility into ALL log levels (DEBUG, INFO, WARNING, ERROR) via console, JSONL file, and FIFO pipe.

### Required Changes

#### 1.1 Verify/Fix StreamLogger Integration

The StreamLogger class exists at `src/ralph_orchestrator/logging/stream_logger.py`. Verify it:
- Exports `StreamLogger`, `LogLevel`, `StructuredLogEntry`, `create_stream_logger`
- Has proper FIFO pipe handling with non-blocking writes
- Includes Rich console output with color coding
- Supports callback registration

#### 1.2 Add CLI Flags to main.py

Add these CLI arguments to the argument parser:

```python
# Log streaming options
parser.add_argument(
    "--log-level",
    type=str,
    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    default="INFO",
    help="Minimum log level to output (default: INFO)"
)
parser.add_argument(
    "--stream-logs",
    action="store_true",
    help="Enable real-time log streaming to console and FIFO pipe"
)
```

#### 1.3 Integrate StreamLogger into Orchestrator

In `orchestrator.py`, initialize and use StreamLogger:
- Create StreamLogger instance when `stream_logs=True` in config
- Pass logger to adapters and other components
- Log key orchestration events at appropriate levels

#### 1.4 Validation Gate

Run `scripts/validate-log-streaming.sh` and verify:
- [ ] `--log-level` flag exists in CLI help
- [ ] `--stream-logs` flag exists in CLI help
- [ ] JSONL file created at `.agent/logs/ralph-*.jsonl`
- [ ] Logs contain structured JSON with timestamp, level, component, message

**STOP HERE if validation fails. Debug before proceeding.**

---

## PHASE 2: Tool Call Streaming (Component 3)

### Objective
Make tool calls visible with START/END events, timing, and success/failure status.

### Required Changes

#### 2.1 Create ToolCallTracker

Add to `src/ralph_orchestrator/logging/tool_tracker.py`:

```python
"""
Tool call tracking with timing and streaming.
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ToolCallEvent:
    """Represents a single tool call with timing."""
    tool_name: str
    arguments: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    parent_call_id: Optional[str] = None
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    def to_log_entry(self) -> dict:
        return {
            "type": "tool_call",
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments_preview": str(self.arguments)[:200],
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "result_preview": str(self.result)[:200] if self.result else None
        }

class ToolCallTracker:
    """Track and stream tool calls with timing."""

    def __init__(self, stream_logger=None):
        self.stream_logger = stream_logger
        self._call_stack: List[ToolCallEvent] = []
        self._all_calls: List[ToolCallEvent] = []

    def start_call(self, tool_name: str, arguments: dict) -> ToolCallEvent:
        """Record start of a tool call."""
        parent_id = self._call_stack[-1].call_id if self._call_stack else None
        event = ToolCallEvent(
            tool_name=tool_name,
            arguments=arguments,
            start_time=datetime.now(),
            parent_call_id=parent_id
        )
        self._call_stack.append(event)
        self._all_calls.append(event)

        if self.stream_logger:
            self.stream_logger.info(
                "ToolCall",
                f"START {tool_name}",
                tool_name=tool_name,
                call_id=event.call_id,
                args_preview=str(arguments)[:100]
            )
        return event

    def end_call(self, event: ToolCallEvent, result: str = None, success: bool = True, error: str = None):
        """Record end of a tool call."""
        event.end_time = datetime.now()
        event.result = result
        event.success = success
        event.error = error

        if self._call_stack and self._call_stack[-1].call_id == event.call_id:
            self._call_stack.pop()

        if self.stream_logger:
            status = "SUCCESS" if success else "FAILED"
            self.stream_logger.info(
                "ToolCall",
                f"END {event.tool_name} [{status}] ({event.duration_ms:.0f}ms)",
                tool_name=event.tool_name,
                call_id=event.call_id,
                duration_ms=event.duration_ms,
                success=success,
                error=error
            )

    def get_summary(self) -> dict:
        """Get summary of all tool calls."""
        return {
            "total_calls": len(self._all_calls),
            "successful": sum(1 for c in self._all_calls if c.success),
            "failed": sum(1 for c in self._all_calls if not c.success),
            "total_duration_ms": sum(c.duration_ms or 0 for c in self._all_calls),
            "by_tool": self._group_by_tool()
        }

    def _group_by_tool(self) -> dict:
        groups = {}
        for call in self._all_calls:
            if call.tool_name not in groups:
                groups[call.tool_name] = {"count": 0, "total_ms": 0}
            groups[call.tool_name]["count"] += 1
            groups[call.tool_name]["total_ms"] += call.duration_ms or 0
        return groups
```

#### 2.2 Update Logging Module Exports

Add to `src/ralph_orchestrator/logging/__init__.py`:
```python
from .tool_tracker import ToolCallTracker, ToolCallEvent
```

#### 2.3 Integrate with VerboseLogger

Enhance `verbose_logger.py` to use ToolCallTracker when stream logging is enabled.

#### 2.4 Validation Gate

Create and run `scripts/validate-tool-streaming.sh`:
- [ ] Tool calls show START event with tool name
- [ ] Tool calls show END event with duration in ms
- [ ] JSONL contains `"type":"tool_call"` entries

**STOP HERE if validation fails. Debug before proceeding.**

---

## PHASE 3: Context Visualization Timeline (Component 4)

### Objective
Track and visualize context window usage throughout orchestration with accurate token counting.

### Required Changes

#### 3.1 Create Monitoring Module

Create `src/ralph_orchestrator/monitoring/__init__.py`:
```python
"""Monitoring and observability for Ralph Orchestrator."""
from .context_tracker import ContextTracker, ContextMeasurement, MeasurePoint

__all__ = ["ContextTracker", "ContextMeasurement", "MeasurePoint"]
```

#### 3.2 Create ContextTracker

Create `src/ralph_orchestrator/monitoring/context_tracker.py` with the full implementation from the plan (lines 691-920). Key features:
- tiktoken-based token counting (with fallback)
- MeasurePoint enum for measurement types
- ContextMeasurement dataclass for storing measurements
- ASCII timeline visualization
- JSON timeline export to `.agent/metrics/`

#### 3.3 Add tiktoken Dependency

Add to `pyproject.toml` dependencies:
```toml
"tiktoken>=0.5.0",
```

#### 3.4 Integrate with Orchestrator

Add measurement points in `orchestrator.py`:
- `ITERATION_START` - beginning of each iteration
- `AFTER_PROMPT_INJECT` - after prompt enhancement
- `AFTER_TOOL_CALL` - after each tool execution
- `ITERATION_END` - end of iteration

#### 3.5 Validation Gate

Create and run `scripts/validate-context-tracking.sh`:
- [ ] Context measurements logged with token counts
- [ ] Timeline JSON file created at `.agent/metrics/context-timeline-*.json`
- [ ] Measurements include percentage_used field
- [ ] ASCII visualization generates correctly

**STOP HERE if validation fails. Debug before proceeding.**

---

## PHASE 4: Monitor Dashboard (Component 5)

### Objective
Create a real-time tmux-based dashboard for monitoring Ralph orchestration.

### Required Changes

#### 4.1 Create monitor.sh

Create `scripts/monitor.sh` with the full implementation from the plan (lines 1055-1323). Key features:
- Dependency checking (tmux, jq)
- FIFO pipe setup
- 4-pane tmux layout:
  - Main: Live log stream
  - Status: Iteration, context %, elapsed time
  - Tools: Recent tool calls with timing
  - Context: ASCII timeline visualization
- Real-time updates every 2 seconds

#### 4.2 Create Helper Script

Create `scripts/ralph-with-monitor.sh`:
```bash
#!/bin/bash
# Run Ralph with full monitoring enabled
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RALPH_DIR="$(dirname "$SCRIPT_DIR")"

# Start monitor in background
echo "Starting monitor dashboard..."
tmux new-session -d -s ralph-monitor "$SCRIPT_DIR/monitor.sh"

# Run Ralph with all monitoring flags
echo "Running Ralph with monitoring..."
cd "$RALPH_DIR"
python -m ralph_orchestrator run \
    --log-level DEBUG \
    --stream-logs \
    --learning \
    "$@"

echo ""
echo "Ralph complete. Monitor still running in tmux session 'ralph-monitor'"
echo "Attach with: tmux attach -t ralph-monitor"
```

#### 4.3 Make Scripts Executable

```bash
chmod +x scripts/monitor.sh scripts/ralph-with-monitor.sh
```

#### 4.4 Validation Gate

Create and run `scripts/validate-monitor-dashboard.sh`:
- [ ] scripts/monitor.sh is executable
- [ ] Dependencies (tmux, jq) detected
- [ ] tmux session creates successfully
- [ ] FIFO pipe operational

**STOP HERE if validation fails. Debug before proceeding.**

---

## PHASE 5: Master Validation

Run the complete end-to-end validation to verify all components work together.

### Master Validation Script

Create `scripts/validate-ace-monitoring-suite.sh`:
```bash
#!/bin/bash
# Master validation - ALL components together
set -e
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     RALPH MONITORING SUITE - MASTER VALIDATION                ║"
echo "║     Date: $(date -Iseconds)                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd /Users/nick/Desktop/ralph-orchestrator

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY must be set"
    exit 1
fi

RESULTS=""

# Component 2: Log Streaming
echo "Testing Component 2: Log Streaming..."
if python -m ralph_orchestrator run --help 2>&1 | grep -q "log-level"; then
    echo "  ✓ --log-level flag present"
    RESULTS+="C2-LogLevel:PASS\n"
else
    echo "  ✗ --log-level flag missing"
    RESULTS+="C2-LogLevel:FAIL\n"
fi

if python -m ralph_orchestrator run --help 2>&1 | grep -q "stream-logs"; then
    echo "  ✓ --stream-logs flag present"
    RESULTS+="C2-StreamLogs:PASS\n"
else
    echo "  ✗ --stream-logs flag missing"
    RESULTS+="C2-StreamLogs:FAIL\n"
fi

# Component 3: Tool Call Streaming
echo ""
echo "Testing Component 3: Tool Call Streaming..."
if python -c "from ralph_orchestrator.logging import ToolCallTracker" 2>/dev/null; then
    echo "  ✓ ToolCallTracker importable"
    RESULTS+="C3-ToolTracker:PASS\n"
else
    echo "  ✗ ToolCallTracker import failed"
    RESULTS+="C3-ToolTracker:FAIL\n"
fi

# Component 4: Context Tracking
echo ""
echo "Testing Component 4: Context Tracking..."
if python -c "from ralph_orchestrator.monitoring import ContextTracker" 2>/dev/null; then
    echo "  ✓ ContextTracker importable"
    RESULTS+="C4-ContextTracker:PASS\n"
else
    echo "  ✗ ContextTracker import failed"
    RESULTS+="C4-ContextTracker:FAIL\n"
fi

# Component 5: Monitor Dashboard
echo ""
echo "Testing Component 5: Monitor Dashboard..."
if [ -x "scripts/monitor.sh" ]; then
    echo "  ✓ monitor.sh is executable"
    RESULTS+="C5-MonitorScript:PASS\n"
else
    echo "  ✗ monitor.sh not executable"
    RESULTS+="C5-MonitorScript:FAIL\n"
fi

if bash -n scripts/monitor.sh 2>/dev/null; then
    echo "  ✓ monitor.sh syntax valid"
    RESULTS+="C5-MonitorSyntax:PASS\n"
else
    echo "  ✗ monitor.sh syntax error"
    RESULTS+="C5-MonitorSyntax:FAIL\n"
fi

# Integration test: dry run with all features
echo ""
echo "Integration Test: Running ralph with all monitoring features..."
mkdir -p .agent/logs .agent/metrics

python -m ralph_orchestrator run \
    --dry-run \
    --stream-logs \
    --log-level DEBUG \
    -p "echo hello" \
    2>&1 | tee /tmp/ralph-master-test.log | head -30

# Check outputs
echo ""
echo "Checking outputs..."
if ls .agent/logs/ralph-*.jsonl 1>/dev/null 2>&1; then
    JSONL_FILE=$(ls -t .agent/logs/ralph-*.jsonl | head -1)
    LINES=$(wc -l < "$JSONL_FILE" | tr -d ' ')
    echo "  ✓ JSONL log created: $JSONL_FILE ($LINES lines)"
    RESULTS+="Integration-JSONL:PASS\n"
else
    echo "  ✗ No JSONL log file created"
    RESULTS+="Integration-JSONL:FAIL\n"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "VALIDATION SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo -e "$RESULTS"

# Count results
PASS_COUNT=$(echo -e "$RESULTS" | grep -c "PASS" || true)
FAIL_COUNT=$(echo -e "$RESULTS" | grep -c "FAIL" || true)
echo ""
echo "PASSED: $PASS_COUNT"
echo "FAILED: $FAIL_COUNT"

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo ""
    echo "🎉 ALL VALIDATIONS PASSED"
    exit 0
else
    echo ""
    echo "⚠️  Some validations failed - review above"
    exit 1
fi
```

### Success Criteria

ALL of the following must pass:
- [ ] C2: `--log-level` and `--stream-logs` CLI flags work
- [ ] C2: JSONL log files created with structured entries
- [ ] C3: ToolCallTracker importable and functional
- [ ] C3: Tool calls logged with START/END and timing
- [ ] C4: ContextTracker importable and functional
- [ ] C4: Timeline JSON files generated
- [ ] C5: monitor.sh executable and syntax-valid
- [ ] C5: tmux dashboard creates successfully
- [ ] Integration: All components work together in dry-run
</requirements>

<implementation>
## Execution Strategy

This is a **phased implementation** with validation gates. Do NOT proceed to the next phase until the current phase's validation passes.

### Execution Order

```
Phase 1 (Log Streaming) → Validate → Phase 2 (Tool Tracking) → Validate →
Phase 3 (Context) → Validate → Phase 4 (Dashboard) → Validate → Master Validation
```

### Extended Thinking Triggers

Before each phase, perform these analyses:
1. **Thoroughly analyze** existing code at integration points
2. **Deeply consider** how new code interacts with existing infrastructure
3. **Systematically verify** imports and dependencies before writing code
4. **Carefully examine** any error messages during validation

### Code Quality Standards

- Follow existing Ralph code patterns and style
- Use type hints consistently
- Include docstrings for all public functions/classes
- Handle errors gracefully (don't break orchestration on logging failures)
- Use thread-safe constructs where appropriate
- Preserve backward compatibility (existing functionality must not break)

### File Management

Create new files:
- `src/ralph_orchestrator/logging/tool_tracker.py`
- `src/ralph_orchestrator/monitoring/__init__.py`
- `src/ralph_orchestrator/monitoring/context_tracker.py`
- `scripts/monitor.sh`
- `scripts/ralph-with-monitor.sh`
- `scripts/validate-tool-streaming.sh`
- `scripts/validate-context-tracking.sh`
- `scripts/validate-monitor-dashboard.sh`
- `scripts/validate-ace-monitoring-suite.sh`

Modify existing files:
- `src/ralph_orchestrator/main.py` - Add CLI flags
- `src/ralph_orchestrator/__main__.py` - Wire CLI flags if needed
- `src/ralph_orchestrator/orchestrator.py` - Integrate new logging/tracking
- `src/ralph_orchestrator/logging/__init__.py` - Export new classes
- `src/ralph_orchestrator/verbose_logger.py` - Integration with StreamLogger
- `pyproject.toml` - Add tiktoken dependency
</implementation>

<verification>
## Per-Phase Validation

After implementing each phase, run the corresponding validation script and verify ALL checkboxes pass before proceeding.

### Validation Script Locations

| Phase | Script | Purpose |
|-------|--------|---------|
| 1 | `scripts/validate-log-streaming.sh` | Verify CLI flags and JSONL output |
| 2 | `scripts/validate-tool-streaming.sh` | Verify tool call START/END events |
| 3 | `scripts/validate-context-tracking.sh` | Verify token counting and timeline |
| 4 | `scripts/validate-monitor-dashboard.sh` | Verify tmux dashboard creation |
| 5 | `scripts/validate-ace-monitoring-suite.sh` | Full integration test |

### Debugging Protocol

If a validation fails:
1. Read the full error output carefully
2. Check the specific validation step that failed
3. Examine the relevant code for the issue
4. Fix the specific issue (don't rewrite working code)
5. Re-run the validation script
6. Only proceed when ALL checks pass
</verification>

<summary_requirements>
After completing all phases, create SUMMARY.md in the output folder with:

## Required Sections

### One-liner
A substantive description of what was accomplished (NOT generic like "Implementation complete").

Example: "Added real-time log streaming, tool call tracking, context visualization, and tmux dashboard to Ralph Orchestrator"

### Version
v1

### Key Findings
- List 3-5 key technical findings or decisions made during implementation
- Include any unexpected challenges and how they were resolved

### Files Created
- List all new files created with brief descriptions

### Files Modified
- List all modified files with summary of changes

### Decisions Needed
- List any decisions that need user input before next steps

### Blockers
- List any external impediments (should be "None" if successful)

### Next Step
- Concrete action for what to do next
- Usually: "Run production test with real task" or "Commit changes"
</summary_requirements>

<success_criteria>
## Implementation Complete When

1. **All Validation Scripts Pass**
   - `scripts/validate-log-streaming.sh` - PASS
   - `scripts/validate-tool-streaming.sh` - PASS
   - `scripts/validate-context-tracking.sh` - PASS
   - `scripts/validate-monitor-dashboard.sh` - PASS
   - `scripts/validate-ace-monitoring-suite.sh` - PASS

2. **All Imports Work**
   ```python
   from ralph_orchestrator.logging import StreamLogger, ToolCallTracker
   from ralph_orchestrator.monitoring import ContextTracker
   ```

3. **CLI Flags Functional**
   ```bash
   python -m ralph_orchestrator run --help | grep "log-level"
   python -m ralph_orchestrator run --help | grep "stream-logs"
   ```

4. **Integration Test Passes**
   ```bash
   python -m ralph_orchestrator run --dry-run --stream-logs --log-level DEBUG -p "test"
   ```
   - Creates `.agent/logs/ralph-*.jsonl`
   - Creates `.agent/metrics/context-timeline-*.json`
   - Shows colored console output

5. **Dashboard Operational**
   ```bash
   ./scripts/monitor.sh
   ```
   - Creates tmux session with 4 panes
   - Reads from FIFO pipe
   - Shows real-time updates

6. **SUMMARY.md Created**
   - Located at `.prompts/005-ace-monitoring-do/SUMMARY.md`
   - Contains all required sections
   - One-liner is substantive (not generic)
</success_criteria>
