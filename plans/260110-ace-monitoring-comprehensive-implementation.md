# Comprehensive Implementation Plan: ACE Learning Fix + Full Monitoring Suite

**Created**: 2026-01-10 02:20 EST
**Status**: Planning Complete - Ready for Implementation
**Branch**: feat/ace-learning-loop
**Validation Approach**: End-to-end functional testing only (NO unit tests/pytest)

---

## Executive Summary

This plan addresses five interconnected components to create a fully observable, self-improving Ralph orchestrator:

| # | Component | Priority | Est. Effort | Dependencies |
|---|-----------|----------|-------------|--------------|
| 1 | ACE Learning API Key Fix | P0-Critical | 2 hours | None |
| 2 | Full Log Streaming | P1-High | 3 hours | Component 1 |
| 3 | Tool Call Streaming | P1-High | 2 hours | Component 2 |
| 4 | Context Visualization Timeline | P2-Medium | 4 hours | Components 2,3 |
| 5 | monitor.sh Dashboard | P1-High | 3 hours | Components 2,3,4 |

**Total Estimated Effort**: 14 hours
**Validation Date Target**: 2026-01-10 (same day implementation + validation)

---

## Component 1: ACE Learning API Key Fix

### Problem Statement

The ACE learning adapter fails with `litellm.AuthenticationError: Missing Anthropic API Key` despite `ANTHROPIC_API_KEY` being set in the user's shell environment. The root cause is that LiteLLMClient at `ace_adapter.py:235-238` relies on automatic environment variable detection, which fails when:

1. The orchestrator spawns subprocesses that don't inherit environment
2. LiteLLM's environment detection doesn't find the variable in the current process context
3. Async learning threads may have different environment visibility

### Current Broken Code

```python
# src/ralph_orchestrator/learning/ace_adapter.py:235-238
self.llm = LiteLLMClient(
    model=config.model,
    max_tokens=config.max_tokens
)
```

### Solution Design

**Option A (Explicit API Key Pass-through)** - SELECTED
```python
import os

# Read API key at initialization time from current process environment
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable required for ACE learning")

self.llm = LiteLLMClient(
    model=config.model,
    max_tokens=config.max_tokens,
    api_key=api_key  # Explicit pass-through
)
```

**Option B (Environment Propagation Fix)** - Alternative if Option A insufficient
```python
# Ensure environment is propagated to all child contexts
import os
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "")
```

### Implementation Steps

1. **Read current ace_adapter.py** to understand full context around lines 235-238
2. **Identify all LiteLLMClient instantiations** in the codebase
3. **Modify initialization** to explicitly pass `api_key` parameter
4. **Add startup validation** that fails fast if API key is missing
5. **Test environment propagation** in async learning threads

### Files to Modify

| File | Changes |
|------|---------|
| `src/ralph_orchestrator/learning/ace_adapter.py` | Add explicit api_key parameter to LiteLLMClient |
| `src/ralph_orchestrator/orchestrator.py` | Add API key validation at learning adapter init |
| `src/ralph_orchestrator/main.py` | Add early API key check with helpful error message |

### Functional Validation

**Validation Script**: `validate-ace-fix.sh`
```bash
#!/bin/bash
set -e
echo "=== ACE Learning API Key Fix Validation ==="
echo "Date: $(date -Iseconds)"
echo ""

# Step 1: Verify API key is set
echo "[1/5] Checking ANTHROPIC_API_KEY is set..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "FAIL: ANTHROPIC_API_KEY not set"
    exit 1
fi
echo "PASS: API key present (${#ANTHROPIC_API_KEY} chars)"

# Step 2: Run ralph with learning enabled (dry-run)
echo ""
echo "[2/5] Running ralph with --learning --dry-run..."
cd /Users/nick/Desktop/ralph-orchestrator
ralph run --learning --dry-run "Create a simple hello.py file" 2>&1 | tee /tmp/ralph-ace-test.log

# Step 3: Check for authentication errors
echo ""
echo "[3/5] Checking for authentication errors..."
if grep -i "AuthenticationError\|Missing.*API.*Key" /tmp/ralph-ace-test.log; then
    echo "FAIL: Authentication error found"
    exit 1
fi
echo "PASS: No authentication errors"

# Step 4: Check ACE learning initialized
echo ""
echo "[4/5] Checking ACE learning initialized..."
if grep -i "ACE learning initialized\|learning.*initialized" /tmp/ralph-ace-test.log; then
    echo "PASS: ACE learning initialized"
else
    echo "WARN: Could not confirm ACE learning initialization"
fi

# Step 5: Check skillbook was accessed
echo ""
echo "[5/5] Checking skillbook interaction..."
SKILLBOOK_PATH=".agent/skillbook/skillbook.json"
if [ -f "$SKILLBOOK_PATH" ]; then
    echo "PASS: Skillbook exists at $SKILLBOOK_PATH"
    echo "Skills count: $(jq '.skills | length' $SKILLBOOK_PATH 2>/dev/null || echo 'N/A')"
else
    echo "INFO: No skillbook yet (will be created on first successful learning)"
fi

echo ""
echo "=== Validation Complete ==="
```

**Success Criteria**:
- [ ] `ralph run --learning --dry-run "test task"` executes without `AuthenticationError`
- [ ] Logs show "ACE learning initialized" message
- [ ] LiteLLM successfully calls the Anthropic API for reflection
- [ ] Skillbook file is created/updated at `.agent/skillbook/skillbook.json`

---

## Component 2: Full Log Streaming

### Problem Statement

Currently Ralph only streams ERROR-level logs to console. Users need visibility into ALL log levels (DEBUG, INFO, WARNING, ERROR) in real-time to understand orchestration behavior.

### Solution Design

Implement structured JSON logging with configurable streaming to:
1. **Console (stderr)** - Human-readable format with Rich
2. **Log file** - JSON lines format for machine parsing
3. **Named pipe (FIFO)** - For real-time consumption by monitor.sh

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Ralph Orchestrator                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Orchestrator│───▶│ StreamLogger│───▶│ Multiplexer │        │
│  │   Events    │    │  (new)      │    │             │        │
│  └─────────────┘    └─────────────┘    └──────┬──────┘        │
│                                               │                │
│         ┌────────────────┬─────────────┬─────┴─────┐          │
│         ▼                ▼             ▼           ▼          │
│  ┌────────────┐  ┌────────────┐ ┌──────────┐ ┌──────────┐    │
│  │  Console   │  │  Log File  │ │  FIFO    │ │ Callback │    │
│  │  (Rich)    │  │  (JSONL)   │ │  Pipe    │ │ Handlers │    │
│  └────────────┘  └────────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Steps

1. **Create StreamLogger class** in `src/ralph_orchestrator/logging/stream_logger.py`
2. **Add log level configuration** via CLI flag `--log-level` (DEBUG|INFO|WARNING|ERROR)
3. **Implement FIFO pipe output** at `.agent/logs/ralph-stream.fifo`
4. **Add JSON structured format** for machine-parseable logs
5. **Integrate with existing VerboseLogger** without breaking current functionality

### New File: `src/ralph_orchestrator/logging/stream_logger.py`

```python
"""
Real-time structured log streaming for Ralph Orchestrator.
Outputs to console, file, and named pipe simultaneously.
"""
import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40

@dataclass
class StructuredLogEntry:
    timestamp: str
    level: str
    component: str
    message: str
    iteration: Optional[int] = None
    context_tokens: Optional[int] = None
    metadata: Optional[dict] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    def to_rich(self) -> str:
        level_colors = {
            "DEBUG": "[dim]",
            "INFO": "[blue]",
            "WARNING": "[yellow]",
            "ERROR": "[red bold]"
        }
        color = level_colors.get(self.level, "")
        return f"{color}[{self.timestamp}] [{self.level}] {self.component}: {self.message}[/]"

class StreamLogger:
    """Multiplexed log streaming to console, file, and FIFO pipe."""

    def __init__(
        self,
        log_dir: Path = Path(".agent/logs"),
        log_level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_fifo: bool = True
    ):
        self.log_dir = log_dir
        self.log_level = log_level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_fifo = enable_fifo
        self._callbacks: List[Callable[[StructuredLogEntry], None]] = []
        self._fifo_path: Optional[Path] = None
        self._fifo_fd: Optional[int] = None
        self._lock = threading.Lock()

        self._setup()

    def _setup(self):
        """Initialize log outputs."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup JSONL log file
        if self.enable_file:
            self._log_file = self.log_dir / f"ralph-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"

        # Setup FIFO pipe for real-time streaming
        if self.enable_fifo:
            self._fifo_path = self.log_dir / "ralph-stream.fifo"
            if self._fifo_path.exists():
                self._fifo_path.unlink()
            os.mkfifo(self._fifo_path)

    def log(
        self,
        level: LogLevel,
        component: str,
        message: str,
        iteration: Optional[int] = None,
        context_tokens: Optional[int] = None,
        **metadata
    ):
        """Log a structured entry to all outputs."""
        if level.value < self.log_level.value:
            return

        entry = StructuredLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.name,
            component=component,
            message=message,
            iteration=iteration,
            context_tokens=context_tokens,
            metadata=metadata if metadata else None
        )

        with self._lock:
            # Console output (Rich formatted)
            if self.enable_console:
                from rich.console import Console
                console = Console(stderr=True)
                console.print(entry.to_rich())

            # File output (JSONL)
            if self.enable_file:
                with open(self._log_file, "a") as f:
                    f.write(entry.to_json() + "\n")

            # FIFO pipe output (non-blocking)
            if self.enable_fifo and self._fifo_path:
                try:
                    fd = os.open(str(self._fifo_path), os.O_WRONLY | os.O_NONBLOCK)
                    os.write(fd, (entry.to_json() + "\n").encode())
                    os.close(fd)
                except OSError:
                    pass  # No reader on pipe, skip

            # Custom callbacks
            for callback in self._callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass

    def debug(self, component: str, message: str, **kwargs):
        self.log(LogLevel.DEBUG, component, message, **kwargs)

    def info(self, component: str, message: str, **kwargs):
        self.log(LogLevel.INFO, component, message, **kwargs)

    def warning(self, component: str, message: str, **kwargs):
        self.log(LogLevel.WARNING, component, message, **kwargs)

    def error(self, component: str, message: str, **kwargs):
        self.log(LogLevel.ERROR, component, message, **kwargs)

    def add_callback(self, callback: Callable[[StructuredLogEntry], None]):
        """Register a callback for log entries."""
        self._callbacks.append(callback)

    def cleanup(self):
        """Clean up FIFO pipe."""
        if self._fifo_path and self._fifo_path.exists():
            self._fifo_path.unlink()
```

### Files to Modify

| File | Changes |
|------|---------|
| `src/ralph_orchestrator/logging/__init__.py` | Create new module with StreamLogger export |
| `src/ralph_orchestrator/logging/stream_logger.py` | New file (above) |
| `src/ralph_orchestrator/orchestrator.py` | Integrate StreamLogger alongside VerboseLogger |
| `src/ralph_orchestrator/main.py` | Add `--log-level` and `--stream-logs` CLI flags |
| `src/ralph_orchestrator/verbose_logger.py` | Add StreamLogger delegation for all log calls |

### Functional Validation

**Validation Script**: `validate-log-streaming.sh`
```bash
#!/bin/bash
set -e
echo "=== Full Log Streaming Validation ==="
echo "Date: $(date -Iseconds)"
echo ""

cd /Users/nick/Desktop/ralph-orchestrator

# Step 1: Create FIFO reader in background
echo "[1/5] Setting up FIFO pipe reader..."
FIFO_PATH=".agent/logs/ralph-stream.fifo"
rm -f "$FIFO_PATH"
mkfifo "$FIFO_PATH" 2>/dev/null || true

# Start background reader
cat "$FIFO_PATH" > /tmp/fifo-output.log &
READER_PID=$!
echo "FIFO reader started (PID: $READER_PID)"

# Step 2: Run ralph with full logging
echo ""
echo "[2/5] Running ralph with --log-level DEBUG..."
timeout 60 ralph run --log-level DEBUG --dry-run "List files in current directory" 2>&1 | tee /tmp/ralph-log-test.log || true

# Step 3: Kill FIFO reader
kill $READER_PID 2>/dev/null || true

# Step 4: Verify log levels present
echo ""
echo "[3/5] Checking log levels in console output..."
for level in DEBUG INFO WARNING; do
    if grep -q "\[$level\]" /tmp/ralph-log-test.log; then
        echo "PASS: $level level logs present"
    else
        echo "WARN: $level level logs not found"
    fi
done

# Step 5: Verify JSONL file created
echo ""
echo "[4/5] Checking JSONL log file..."
JSONL_FILE=$(ls -t .agent/logs/ralph-*.jsonl 2>/dev/null | head -1)
if [ -n "$JSONL_FILE" ]; then
    echo "PASS: JSONL log file created: $JSONL_FILE"
    echo "Line count: $(wc -l < "$JSONL_FILE")"
    echo "Sample entry:"
    head -1 "$JSONL_FILE" | jq . 2>/dev/null || head -1 "$JSONL_FILE"
else
    echo "FAIL: No JSONL log file found"
fi

# Step 6: Verify FIFO output
echo ""
echo "[5/5] Checking FIFO pipe output..."
if [ -s /tmp/fifo-output.log ]; then
    echo "PASS: FIFO pipe received data"
    echo "Lines received: $(wc -l < /tmp/fifo-output.log)"
else
    echo "WARN: No data received via FIFO (reader may have started too late)"
fi

echo ""
echo "=== Validation Complete ==="
```

**Success Criteria**:
- [ ] Console shows DEBUG, INFO, WARNING, ERROR level logs
- [ ] JSONL log file created at `.agent/logs/ralph-YYYYMMDD-HHMMSS.jsonl`
- [ ] Each log entry is valid JSON with timestamp, level, component, message
- [ ] FIFO pipe at `.agent/logs/ralph-stream.fifo` receives real-time data
- [ ] Log level filtering works (`--log-level WARNING` hides DEBUG/INFO)

---

## Component 3: Tool Call Streaming

### Problem Statement

Tool calls are the primary actions in orchestration but are not visible in logs. Users need to see:
- Tool name being invoked
- Input arguments
- Execution duration
- Output/result summary
- Success/failure status

### Solution Design

Extend the existing `VerboseLogger.log_tool_call()` method to:
1. Stream tool calls to the new StreamLogger
2. Capture timing information with decorators
3. Track tool call hierarchy (nested calls)
4. Include in JSONL output for analysis

### Implementation Steps

1. **Enhance VerboseLogger.log_tool_call()** to use StreamLogger
2. **Add tool call wrapper** that automatically logs start/end
3. **Track tool call stack** for nested invocations
4. **Add tool-specific metadata** (input size, output size, duration)

### Enhanced Tool Call Logging

```python
# Addition to src/ralph_orchestrator/verbose_logger.py

@dataclass
class ToolCallEvent:
    tool_name: str
    arguments: dict
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

    def __init__(self, stream_logger: StreamLogger):
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

        # Stream the start event
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

        # Stream the end event
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

### Files to Modify

| File | Changes |
|------|---------|
| `src/ralph_orchestrator/verbose_logger.py` | Add ToolCallTracker, enhance log_tool_call() |
| `src/ralph_orchestrator/adapters/base.py` | Wrap tool execution with tracker |
| `src/ralph_orchestrator/adapters/claude.py` | Add tool call tracking to Claude adapter |
| `src/ralph_orchestrator/adapters/acp.py` | Add tool call tracking to ACP adapter |

### Functional Validation

**Validation Script**: `validate-tool-streaming.sh`
```bash
#!/bin/bash
set -e
echo "=== Tool Call Streaming Validation ==="
echo "Date: $(date -Iseconds)"
echo ""

cd /Users/nick/Desktop/ralph-orchestrator

# Step 1: Run ralph with a task that will invoke tools
echo "[1/4] Running ralph with tool-invoking task..."
ralph run --log-level DEBUG --dry-run "Read the README.md file and summarize it" 2>&1 | tee /tmp/ralph-tool-test.log

# Step 2: Check for tool call start events
echo ""
echo "[2/4] Checking for tool call START events..."
if grep -E "START.*(Read|Bash|Write|Glob|Grep)" /tmp/ralph-tool-test.log; then
    echo "PASS: Tool call START events found"
else
    echo "WARN: No tool call START events found"
fi

# Step 3: Check for tool call end events with duration
echo ""
echo "[3/4] Checking for tool call END events with duration..."
if grep -E "END.*\[SUCCESS\].*ms\)" /tmp/ralph-tool-test.log; then
    echo "PASS: Tool call END events with duration found"
else
    echo "WARN: No tool call END events found"
fi

# Step 4: Check JSONL for tool_call entries
echo ""
echo "[4/4] Checking JSONL for tool_call type entries..."
JSONL_FILE=$(ls -t .agent/logs/ralph-*.jsonl 2>/dev/null | head -1)
if [ -n "$JSONL_FILE" ]; then
    TOOL_CALLS=$(grep '"type":"tool_call"' "$JSONL_FILE" | wc -l)
    echo "Tool call entries in JSONL: $TOOL_CALLS"
    if [ "$TOOL_CALLS" -gt 0 ]; then
        echo "PASS: Tool calls recorded in JSONL"
        echo "Sample tool call:"
        grep '"type":"tool_call"' "$JSONL_FILE" | head -1 | jq .
    else
        echo "WARN: No tool call entries in JSONL"
    fi
else
    echo "FAIL: No JSONL file found"
fi

echo ""
echo "=== Validation Complete ==="
```

**Success Criteria**:
- [ ] Tool calls show START event with tool name and arguments preview
- [ ] Tool calls show END event with SUCCESS/FAILED and duration in ms
- [ ] Nested tool calls show parent-child relationship
- [ ] JSONL contains tool_call type entries with full metadata
- [ ] Tool call summary shows counts and durations by tool type

---

## Component 4: Context Visualization Timeline

### Problem Statement

Users cannot see how context window is being consumed over time. This makes it impossible to:
- Understand why context limits are hit
- Optimize prompt sizes
- Identify context-hungry operations
- Debug truncation issues

### Solution Design

Create a context tracking system that:
1. Measures tokens at each iteration boundary
2. Tracks individual contributions (prompt, response, tools)
3. Generates real-time visualization data
4. Outputs timeline for post-analysis

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Context Tracker                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                                               │
│  │  tiktoken   │◀─── Token counting engine                     │
│  │  encoder    │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│  ┌──────▼──────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Measure    │───▶│  Timeline   │───▶│  Visualizer │        │
│  │  Points     │    │  Storage    │    │  (ASCII)    │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
│  Measure Points:                                               │
│  • Before iteration (baseline)                                 │
│  • After prompt injection                                      │
│  • After tool results                                          │
│  • After response generation                                   │
│  • End of iteration (total)                                    │
└─────────────────────────────────────────────────────────────────┘
```

### New File: `src/ralph_orchestrator/monitoring/context_tracker.py`

```python
"""
Context window usage tracking and visualization.
Uses tiktoken for accurate token counting.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict, field
from enum import Enum

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

class MeasurePoint(Enum):
    ITERATION_START = "iteration_start"
    AFTER_PROMPT_INJECT = "after_prompt_inject"
    AFTER_SKILLBOOK_INJECT = "after_skillbook_inject"
    AFTER_TOOL_CALL = "after_tool_call"
    AFTER_RESPONSE = "after_response"
    ITERATION_END = "iteration_end"

@dataclass
class ContextMeasurement:
    timestamp: str
    iteration: int
    measure_point: str
    tokens: int
    chars: int
    component: str  # What was added
    delta_tokens: int  # Change from previous measurement
    cumulative_tokens: int  # Total so far in iteration
    context_limit: int
    percentage_used: float

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class IterationContextSummary:
    iteration: int
    start_tokens: int
    end_tokens: int
    peak_tokens: int
    prompt_tokens: int
    response_tokens: int
    tool_tokens: int
    skillbook_tokens: int

class ContextTracker:
    """Track context window usage throughout orchestration."""

    # Context limits by adapter
    CONTEXT_LIMITS = {
        "claude": 200_000,
        "gemini": 32_000,
        "qchat": 8_000,
        "kiro": 8_000,
        "default": 100_000
    }

    def __init__(
        self,
        adapter_type: str = "claude",
        output_dir: Path = Path(".agent/metrics"),
        stream_logger = None
    ):
        self.adapter_type = adapter_type
        self.context_limit = self.CONTEXT_LIMITS.get(adapter_type, self.CONTEXT_LIMITS["default"])
        self.output_dir = output_dir
        self.stream_logger = stream_logger
        self._measurements: List[ContextMeasurement] = []
        self._current_iteration = 0
        self._iteration_baseline = 0

        # Initialize tiktoken encoder
        if TIKTOKEN_AVAILABLE:
            self._encoder = tiktoken.encoding_for_model("gpt-4")  # Compatible with Claude
        else:
            self._encoder = None

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self._encoder:
            return len(self._encoder.encode(text))
        else:
            # Fallback: ~4 chars per token
            return len(text) // 4

    def measure(
        self,
        point: MeasurePoint,
        content: str,
        component: str,
        iteration: Optional[int] = None
    ) -> ContextMeasurement:
        """Record a context measurement."""
        if iteration is not None:
            self._current_iteration = iteration

        tokens = self.count_tokens(content)
        chars = len(content)

        # Calculate delta from previous measurement in same iteration
        prev_in_iteration = [m for m in self._measurements if m.iteration == self._current_iteration]
        if prev_in_iteration:
            delta = tokens - prev_in_iteration[-1].tokens
            cumulative = prev_in_iteration[-1].cumulative_tokens + max(0, delta)
        else:
            delta = tokens
            cumulative = tokens
            self._iteration_baseline = tokens

        measurement = ContextMeasurement(
            timestamp=datetime.now().isoformat(),
            iteration=self._current_iteration,
            measure_point=point.value,
            tokens=tokens,
            chars=chars,
            component=component,
            delta_tokens=delta,
            cumulative_tokens=cumulative,
            context_limit=self.context_limit,
            percentage_used=(cumulative / self.context_limit) * 100
        )

        self._measurements.append(measurement)

        # Stream to logger
        if self.stream_logger:
            emoji = self._get_usage_emoji(measurement.percentage_used)
            self.stream_logger.info(
                "Context",
                f"{emoji} {point.value}: {tokens:,} tokens ({measurement.percentage_used:.1f}% of {self.context_limit:,})",
                iteration=self._current_iteration,
                context_tokens=tokens,
                percentage=measurement.percentage_used,
                component=component
            )

        return measurement

    def _get_usage_emoji(self, percentage: float) -> str:
        """Get emoji indicator for usage level."""
        if percentage < 50:
            return "🟢"
        elif percentage < 80:
            return "🟡"
        elif percentage < 95:
            return "🟠"
        else:
            return "🔴"

    def get_timeline_ascii(self, width: int = 60) -> str:
        """Generate ASCII visualization of context usage over time."""
        if not self._measurements:
            return "No measurements recorded"

        lines = []
        lines.append(f"Context Usage Timeline (limit: {self.context_limit:,} tokens)")
        lines.append("=" * width)

        # Group by iteration
        iterations = {}
        for m in self._measurements:
            if m.iteration not in iterations:
                iterations[m.iteration] = []
            iterations[m.iteration].append(m)

        for iter_num, measurements in sorted(iterations.items()):
            lines.append(f"\nIteration {iter_num}:")
            lines.append("-" * width)

            for m in measurements:
                # Create bar
                bar_width = width - 40
                filled = int((m.percentage_used / 100) * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                emoji = self._get_usage_emoji(m.percentage_used)

                point_name = m.measure_point.replace("_", " ").title()[:15].ljust(15)
                lines.append(f"  {point_name} |{bar}| {m.percentage_used:5.1f}% {emoji}")

        return "\n".join(lines)

    def get_summary(self) -> Dict:
        """Get summary statistics."""
        if not self._measurements:
            return {"error": "No measurements"}

        return {
            "total_measurements": len(self._measurements),
            "iterations_tracked": len(set(m.iteration for m in self._measurements)),
            "peak_usage_percent": max(m.percentage_used for m in self._measurements),
            "peak_tokens": max(m.tokens for m in self._measurements),
            "context_limit": self.context_limit,
            "adapter": self.adapter_type
        }

    def save_timeline(self, filename: str = None) -> Path:
        """Save timeline data to JSON file."""
        if filename is None:
            filename = f"context-timeline-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        filepath = self.output_dir / filename
        data = {
            "metadata": {
                "adapter": self.adapter_type,
                "context_limit": self.context_limit,
                "generated_at": datetime.now().isoformat()
            },
            "summary": self.get_summary(),
            "measurements": [m.to_dict() for m in self._measurements]
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def print_timeline(self):
        """Print ASCII timeline to console."""
        print(self.get_timeline_ascii())
```

### Files to Modify

| File | Changes |
|------|---------|
| `src/ralph_orchestrator/monitoring/__init__.py` | Create module with ContextTracker export |
| `src/ralph_orchestrator/monitoring/context_tracker.py` | New file (above) |
| `src/ralph_orchestrator/orchestrator.py` | Integrate ContextTracker at measure points |
| `src/ralph_orchestrator/adapters/base.py` | Add measurement hooks |
| `pyproject.toml` | Add tiktoken dependency |

### Functional Validation

**Validation Script**: `validate-context-tracking.sh`
```bash
#!/bin/bash
set -e
echo "=== Context Visualization Timeline Validation ==="
echo "Date: $(date -Iseconds)"
echo ""

cd /Users/nick/Desktop/ralph-orchestrator

# Step 1: Run ralph with context tracking
echo "[1/5] Running ralph with context tracking enabled..."
ralph run --log-level DEBUG --dry-run "Create a Python script that reads a file and counts words" 2>&1 | tee /tmp/ralph-context-test.log

# Step 2: Check for context measurement logs
echo ""
echo "[2/5] Checking for context measurement logs..."
if grep -E "Context.*tokens.*%" /tmp/ralph-context-test.log; then
    echo "PASS: Context measurements found in logs"
else
    echo "WARN: No context measurements in logs"
fi

# Step 3: Check for timeline JSON file
echo ""
echo "[3/5] Checking for context timeline JSON..."
TIMELINE_FILE=$(ls -t .agent/metrics/context-timeline-*.json 2>/dev/null | head -1)
if [ -n "$TIMELINE_FILE" ]; then
    echo "PASS: Timeline file created: $TIMELINE_FILE"
    echo "Measurements count: $(jq '.measurements | length' "$TIMELINE_FILE")"
    echo "Peak usage: $(jq '.summary.peak_usage_percent' "$TIMELINE_FILE")%"
else
    echo "FAIL: No timeline file found"
fi

# Step 4: Verify measurement structure
echo ""
echo "[4/5] Verifying measurement structure..."
if [ -n "$TIMELINE_FILE" ]; then
    echo "Sample measurement:"
    jq '.measurements[0]' "$TIMELINE_FILE"

    # Check required fields
    REQUIRED_FIELDS="timestamp iteration measure_point tokens percentage_used"
    for field in $REQUIRED_FIELDS; do
        if jq -e ".measurements[0].$field" "$TIMELINE_FILE" > /dev/null 2>&1; then
            echo "  ✓ $field present"
        else
            echo "  ✗ $field missing"
        fi
    done
fi

# Step 5: Generate ASCII visualization
echo ""
echo "[5/5] ASCII Timeline Visualization:"
if [ -n "$TIMELINE_FILE" ]; then
    # Quick ASCII viz from JSON
    echo ""
    jq -r '.measurements[] | "Iter \(.iteration) | \(.measure_point | .[0:15]) | \(.percentage_used | floor)% | \("█" * ((.percentage_used / 5) | floor))"' "$TIMELINE_FILE" 2>/dev/null || echo "Could not generate visualization"
fi

echo ""
echo "=== Validation Complete ==="
```

**Success Criteria**:
- [ ] Context measurements logged at each measure point
- [ ] JSON timeline file created at `.agent/metrics/context-timeline-*.json`
- [ ] Measurements include tokens, percentage, component, delta
- [ ] ASCII visualization shows usage bars with emoji indicators
- [ ] Peak usage and iteration summaries available
- [ ] tiktoken provides accurate token counts (or fallback works)

---

## Component 5: monitor.sh Dashboard

### Problem Statement

Users need a real-time terminal dashboard to observe orchestration as it runs. This dashboard should show:
- Live log stream
- Current context usage
- Tool call activity
- Iteration progress
- Resource metrics

### Solution Design

Create a tmux-based dashboard with multiple panes:
1. **Main pane**: Live log stream from FIFO pipe
2. **Status pane**: Current iteration, context %, time elapsed
3. **Tools pane**: Recent tool calls with timing
4. **Metrics pane**: Token usage, cost, checkpoint info

### Dashboard Layout

```
┌─────────────────────────────────────────┬─────────────────────┐
│                                         │     STATUS          │
│           LIVE LOG STREAM               │  Iteration: 3/10    │
│                                         │  Context: 45% 🟢    │
│  [2026-01-10T02:30:15] [INFO] Starting  │  Elapsed: 00:03:42  │
│  [2026-01-10T02:30:16] [DEBUG] Tool...  │  Est. remaining: ~5m│
│  [2026-01-10T02:30:17] [INFO] Exec...   │                     │
│                                         ├─────────────────────┤
│                                         │   RECENT TOOLS      │
│                                         │  Read: 3 (245ms)    │
│                                         │  Write: 1 (123ms)   │
│                                         │  Bash: 2 (1.2s)     │
├─────────────────────────────────────────┴─────────────────────┤
│  CONTEXT TIMELINE                                             │
│  ██████████████████░░░░░░░░░░░░░░░░░░░░ 45% (90,000/200,000) │
│  Iter 1: ████████ 40%                                        │
│  Iter 2: ██████████ 52%                                      │
│  Iter 3: █████████ 45% ← current                             │
└───────────────────────────────────────────────────────────────┘
```

### New File: `scripts/monitor.sh`

```bash
#!/bin/bash
#
# Ralph Orchestrator Real-Time Monitor
# Usage: ./scripts/monitor.sh [session_name]
#
# Prerequisites:
#   - tmux installed
#   - jq installed (for JSON parsing)
#   - Ralph orchestrator running with --stream-logs
#
# This script creates a multi-pane tmux dashboard for monitoring
# Ralph orchestration in real-time.

set -e

# Configuration
SESSION_NAME="${1:-ralph-monitor}"
RALPH_DIR="${RALPH_DIR:-$(pwd)}"
LOG_DIR="$RALPH_DIR/.agent/logs"
METRICS_DIR="$RALPH_DIR/.agent/metrics"
FIFO_PATH="$LOG_DIR/ralph-stream.fifo"
REFRESH_INTERVAL=2

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "$LOG_DIR" "$METRICS_DIR"

# Check dependencies
check_deps() {
    local missing=()
    command -v tmux >/dev/null 2>&1 || missing+=("tmux")
    command -v jq >/dev/null 2>&1 || missing+=("jq")

    if [ ${#missing[@]} -ne 0 ]; then
        echo "Missing dependencies: ${missing[*]}"
        echo "Install with: brew install ${missing[*]}"
        exit 1
    fi
}

# Create FIFO if it doesn't exist
setup_fifo() {
    if [ ! -p "$FIFO_PATH" ]; then
        echo "Creating FIFO pipe at $FIFO_PATH"
        mkfifo "$FIFO_PATH"
    fi
}

# Status pane content generator
generate_status() {
    while true; do
        clear
        echo -e "${BLUE}═══════════════════════════════${NC}"
        echo -e "${BLUE}    RALPH ORCHESTRATOR STATUS   ${NC}"
        echo -e "${BLUE}═══════════════════════════════${NC}"
        echo ""

        # Check if Ralph is running
        if pgrep -f "ralph" > /dev/null 2>&1; then
            echo -e "Status: ${GREEN}● RUNNING${NC}"
        else
            echo -e "Status: ${YELLOW}○ IDLE${NC}"
        fi
        echo ""

        # Read latest metrics
        LATEST_METRICS=$(ls -t "$METRICS_DIR"/*.json 2>/dev/null | head -1)
        if [ -n "$LATEST_METRICS" ]; then
            ITERATION=$(jq -r '.iteration // "N/A"' "$LATEST_METRICS" 2>/dev/null || echo "N/A")
            CONTEXT_PCT=$(jq -r '.context_percentage // 0' "$LATEST_METRICS" 2>/dev/null || echo "0")

            echo "Iteration: $ITERATION"

            # Context bar
            PCT_INT=${CONTEXT_PCT%.*}
            if [ "$PCT_INT" -lt 50 ]; then
                COLOR=$GREEN
            elif [ "$PCT_INT" -lt 80 ]; then
                COLOR=$YELLOW
            else
                COLOR=$RED
            fi

            BAR_WIDTH=20
            FILLED=$((PCT_INT * BAR_WIDTH / 100))
            EMPTY=$((BAR_WIDTH - FILLED))
            BAR=$(printf '█%.0s' $(seq 1 $FILLED 2>/dev/null) || true)
            EMPTY_BAR=$(printf '░%.0s' $(seq 1 $EMPTY 2>/dev/null) || true)

            echo -e "Context: ${COLOR}${BAR}${EMPTY_BAR}${NC} ${PCT_INT}%"
        else
            echo "Iteration: Waiting..."
            echo "Context: Waiting..."
        fi

        echo ""
        echo -e "${BLUE}─────────────────────────────────${NC}"
        echo "Updated: $(date '+%H:%M:%S')"

        sleep $REFRESH_INTERVAL
    done
}

# Tool calls pane content generator
generate_tools() {
    while true; do
        clear
        echo -e "${BLUE}═══════════════════════════════${NC}"
        echo -e "${BLUE}      RECENT TOOL CALLS        ${NC}"
        echo -e "${BLUE}═══════════════════════════════${NC}"
        echo ""

        # Parse recent JSONL for tool calls
        LATEST_LOG=$(ls -t "$LOG_DIR"/ralph-*.jsonl 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo "Tool        Count   Avg Time"
            echo "──────────  ─────   ────────"

            # Aggregate tool calls
            grep '"type":"tool_call"' "$LATEST_LOG" 2>/dev/null | \
                jq -r '.tool_name' 2>/dev/null | \
                sort | uniq -c | sort -rn | head -8 | \
                while read count tool; do
                    printf "%-11s %5s   --\n" "$tool" "$count"
                done

            echo ""
            echo "Recent:"
            grep '"type":"tool_call"' "$LATEST_LOG" 2>/dev/null | \
                tail -5 | \
                jq -r '"\(.tool_name): \(.duration_ms // "?")ms"' 2>/dev/null || true
        else
            echo "No tool calls recorded yet"
        fi

        sleep $REFRESH_INTERVAL
    done
}

# Context timeline pane content generator
generate_context_timeline() {
    while true; do
        clear
        echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}                  CONTEXT TIMELINE                       ${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
        echo ""

        TIMELINE_FILE=$(ls -t "$METRICS_DIR"/context-timeline-*.json 2>/dev/null | head -1)
        if [ -n "$TIMELINE_FILE" ]; then
            # Get context limit
            LIMIT=$(jq -r '.metadata.context_limit // 200000' "$TIMELINE_FILE")

            # Show per-iteration summary
            jq -r --arg limit "$LIMIT" '
                .measurements |
                group_by(.iteration) |
                .[] |
                (.[0].iteration) as $iter |
                (map(.tokens) | max) as $peak |
                (($peak / ($limit | tonumber)) * 100) as $pct |
                "Iter \($iter): \("█" * (($pct / 5) | floor))\("░" * (20 - (($pct / 5) | floor))) \($pct | floor)% (\($peak) tokens)"
            ' "$TIMELINE_FILE" 2>/dev/null | tail -10

            echo ""
            PEAK=$(jq -r '.summary.peak_usage_percent // 0' "$TIMELINE_FILE")
            echo "Peak usage: ${PEAK}%"
        else
            echo "Waiting for context measurements..."
        fi

        sleep $REFRESH_INTERVAL
    done
}

# Main log stream reader
stream_logs() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                         LIVE LOG STREAM                            ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Waiting for logs on $FIFO_PATH..."
    echo "(Start Ralph with --stream-logs to see output)"
    echo ""

    # Read from FIFO and colorize
    while true; do
        if [ -p "$FIFO_PATH" ]; then
            cat "$FIFO_PATH" 2>/dev/null | while read -r line; do
                # Parse JSON and colorize
                LEVEL=$(echo "$line" | jq -r '.level // "INFO"' 2>/dev/null || echo "INFO")
                MSG=$(echo "$line" | jq -r '.message // .raw // "?"' 2>/dev/null || echo "$line")
                TS=$(echo "$line" | jq -r '.timestamp // ""' 2>/dev/null | cut -d'T' -f2 | cut -d'.' -f1)
                COMPONENT=$(echo "$line" | jq -r '.component // "Ralph"' 2>/dev/null)

                case "$LEVEL" in
                    DEBUG) COLOR=$BLUE ;;
                    INFO) COLOR=$GREEN ;;
                    WARNING) COLOR=$YELLOW ;;
                    ERROR) COLOR=$RED ;;
                    *) COLOR=$NC ;;
                esac

                echo -e "${COLOR}[$TS] [$LEVEL] $COMPONENT: $MSG${NC}"
            done
        else
            sleep 1
        fi
    done
}

# Create tmux session with panes
create_dashboard() {
    # Kill existing session if present
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

    # Create new session with main pane (log stream)
    tmux new-session -d -s "$SESSION_NAME" -x 120 -y 40

    # Main pane: Log stream (left, 70% width)
    tmux send-keys -t "$SESSION_NAME" "cd '$RALPH_DIR' && $(declare -f stream_logs); stream_logs" Enter

    # Split right side for status (30% width)
    tmux split-window -h -p 30 -t "$SESSION_NAME"
    tmux send-keys -t "$SESSION_NAME" "cd '$RALPH_DIR' && $(declare -f generate_status); generate_status" Enter

    # Split status pane for tools
    tmux split-window -v -p 60 -t "$SESSION_NAME"
    tmux send-keys -t "$SESSION_NAME" "cd '$RALPH_DIR' && $(declare -f generate_tools); generate_tools" Enter

    # Create bottom pane for context timeline
    tmux select-pane -t "$SESSION_NAME":0.0
    tmux split-window -v -p 25 -t "$SESSION_NAME"
    tmux send-keys -t "$SESSION_NAME" "cd '$RALPH_DIR' && $(declare -f generate_context_timeline); generate_context_timeline" Enter

    # Focus on main log pane
    tmux select-pane -t "$SESSION_NAME":0.0

    # Attach to session
    tmux attach-session -t "$SESSION_NAME"
}

# Main
main() {
    echo "Ralph Orchestrator Monitor"
    echo "=========================="
    echo ""

    check_deps
    setup_fifo

    echo "Starting dashboard in tmux session: $SESSION_NAME"
    echo "Press Ctrl+B then D to detach, Ctrl+C to exit"
    echo ""

    create_dashboard
}

# Run main or export functions for sourcing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Additional Helper Scripts

**scripts/ralph-with-monitor.sh** - Run Ralph with monitoring enabled:
```bash
#!/bin/bash
# Run Ralph with full monitoring enabled
# Usage: ./scripts/ralph-with-monitor.sh "Your task here"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RALPH_DIR="$(dirname "$SCRIPT_DIR")"

# Start monitor in background
echo "Starting monitor dashboard..."
tmux new-session -d -s ralph-monitor "$SCRIPT_DIR/monitor.sh"

# Run Ralph with all monitoring flags
echo "Running Ralph with monitoring..."
cd "$RALPH_DIR"
ralph run \
    --log-level DEBUG \
    --stream-logs \
    --learning \
    "$@"

echo ""
echo "Ralph complete. Monitor still running in tmux session 'ralph-monitor'"
echo "Attach with: tmux attach -t ralph-monitor"
```

### Files to Create/Modify

| File | Changes |
|------|---------|
| `scripts/monitor.sh` | New file (above) - main dashboard |
| `scripts/ralph-with-monitor.sh` | New file - convenience wrapper |
| `src/ralph_orchestrator/main.py` | Add `--stream-logs` flag |
| `README.md` | Add monitoring documentation |

### Functional Validation

**Validation Script**: `validate-monitor-dashboard.sh`
```bash
#!/bin/bash
set -e
echo "=== monitor.sh Dashboard Validation ==="
echo "Date: $(date -Iseconds)"
echo ""

cd /Users/nick/Desktop/ralph-orchestrator

# Step 1: Check script exists and is executable
echo "[1/6] Checking monitor.sh exists and is executable..."
if [ -x "scripts/monitor.sh" ]; then
    echo "PASS: scripts/monitor.sh is executable"
else
    echo "FAIL: scripts/monitor.sh not found or not executable"
    exit 1
fi

# Step 2: Check dependencies
echo ""
echo "[2/6] Checking dependencies..."
DEPS_OK=true
for dep in tmux jq; do
    if command -v $dep &> /dev/null; then
        echo "  ✓ $dep installed"
    else
        echo "  ✗ $dep missing"
        DEPS_OK=false
    fi
done

# Step 3: Test FIFO creation
echo ""
echo "[3/6] Testing FIFO pipe creation..."
TEST_FIFO="/tmp/test-ralph-fifo-$$"
mkfifo "$TEST_FIFO"
if [ -p "$TEST_FIFO" ]; then
    echo "PASS: FIFO pipe creation works"
    rm "$TEST_FIFO"
else
    echo "FAIL: Could not create FIFO pipe"
fi

# Step 4: Test tmux session creation (non-interactive)
echo ""
echo "[4/6] Testing tmux session creation..."
TEST_SESSION="ralph-monitor-test-$$"
tmux new-session -d -s "$TEST_SESSION" "echo 'test'" 2>/dev/null
if tmux has-session -t "$TEST_SESSION" 2>/dev/null; then
    echo "PASS: tmux session creation works"
    tmux kill-session -t "$TEST_SESSION" 2>/dev/null
else
    echo "FAIL: Could not create tmux session"
fi

# Step 5: Dry run the monitor script
echo ""
echo "[5/6] Dry-run monitor script syntax check..."
if bash -n scripts/monitor.sh; then
    echo "PASS: monitor.sh syntax is valid"
else
    echo "FAIL: monitor.sh has syntax errors"
fi

# Step 6: Integration test - start monitor, run ralph, check output
echo ""
echo "[6/6] Integration test (10 second timeout)..."
echo "  Starting monitor in background..."

# Start monitor session
tmux new-session -d -s ralph-validate-monitor "cd '$PWD' && scripts/monitor.sh ralph-validate-monitor 2>&1 | head -100"
sleep 2

# Check if session is running
if tmux has-session -t ralph-validate-monitor 2>/dev/null; then
    echo "  PASS: Monitor session started"

    # Run a quick ralph command to generate logs
    echo "  Running ralph dry-run to generate data..."
    timeout 30 ralph run --dry-run --log-level DEBUG "echo hello" 2>&1 | head -20 || true

    sleep 3

    # Check for log files
    if ls .agent/logs/ralph-*.jsonl 1>/dev/null 2>&1; then
        echo "  PASS: Log files generated"
    else
        echo "  WARN: No log files found"
    fi

    # Cleanup
    tmux kill-session -t ralph-validate-monitor 2>/dev/null || true
else
    echo "  FAIL: Monitor session failed to start"
fi

echo ""
echo "=== Validation Complete ==="
echo ""
echo "To manually test the full dashboard:"
echo "  Terminal 1: ./scripts/monitor.sh"
echo "  Terminal 2: ralph run --learning --stream-logs --log-level DEBUG 'Your task'"
```

**Success Criteria**:
- [ ] `scripts/monitor.sh` is executable and passes syntax check
- [ ] Dependencies (tmux, jq) are detected correctly
- [ ] FIFO pipe created at `.agent/logs/ralph-stream.fifo`
- [ ] tmux session with 4 panes created successfully
- [ ] Log stream pane reads from FIFO in real-time
- [ ] Status pane updates every 2 seconds
- [ ] Tools pane shows aggregated tool call stats
- [ ] Context timeline pane shows ASCII visualization
- [ ] Dashboard survives Ralph completion (continues showing final state)

---

## Implementation Order

Based on dependencies and user impact:

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION SEQUENCE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Foundation (Day 1 Morning)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Component 1: ACE Learning API Key Fix                   │    │
│  │ • Fix LiteLLMClient initialization                      │    │
│  │ • Add API key validation                                │    │
│  │ • Run functional validation                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  Phase 2: Logging Infrastructure (Day 1 Afternoon)              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Component 2: Full Log Streaming                         │    │
│  │ • Create StreamLogger class                             │    │
│  │ • Add FIFO pipe output                                  │    │
│  │ • Integrate with orchestrator                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Component 3: Tool Call Streaming                        │    │
│  │ • Enhance VerboseLogger                                 │    │
│  │ • Add ToolCallTracker                                   │    │
│  │ • Integrate with adapters                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  Phase 3: Observability (Day 1 Evening)                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Component 4: Context Visualization Timeline             │    │
│  │ • Create ContextTracker                                 │    │
│  │ • Add measurement points                                │    │
│  │ • Generate timeline output                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  Phase 4: Dashboard (Day 1 Night)                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Component 5: monitor.sh Dashboard                       │    │
│  │ • Create tmux-based dashboard                           │    │
│  │ • Integrate all data sources                            │    │
│  │ • Full end-to-end validation                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Validation Date & Checklist

**Target Validation Date**: 2026-01-10 (same day as implementation)

### End-to-End Validation Procedure

```bash
#!/bin/bash
# Master validation script - validates ALL components together
# Run this AFTER implementing all components

set -e
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     RALPH MONITORING SUITE - MASTER VALIDATION                ║"
echo "║     Date: $(date -Iseconds)                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd /Users/nick/Desktop/ralph-orchestrator

# Ensure API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY must be set"
    exit 1
fi

echo "Starting comprehensive validation..."
echo ""

# 1. Start monitor in background
echo "Step 1: Starting monitor dashboard..."
./scripts/monitor.sh ralph-master-validation &
MONITOR_PID=$!
sleep 3

# 2. Run Ralph with all features enabled
echo ""
echo "Step 2: Running Ralph with full monitoring..."
echo "Command: ralph run --learning --stream-logs --log-level DEBUG"
echo ""

ralph run \
    --learning \
    --stream-logs \
    --log-level DEBUG \
    --dry-run \
    "Create a Python function that calculates fibonacci numbers and write it to fib.py" \
    2>&1 | tee /tmp/ralph-master-validation.log

# 3. Collect results
echo ""
echo "Step 3: Collecting validation results..."
echo ""

RESULTS_FILE="/tmp/validation-results-$(date +%Y%m%d-%H%M%S).txt"

{
    echo "RALPH MONITORING SUITE VALIDATION RESULTS"
    echo "=========================================="
    echo "Date: $(date -Iseconds)"
    echo ""

    echo "1. ACE LEARNING"
    echo "---------------"
    if grep -q "ACE learning initialized" /tmp/ralph-master-validation.log; then
        echo "✓ ACE learning initialized"
    else
        echo "✗ ACE learning NOT initialized"
    fi

    if grep -q "AuthenticationError" /tmp/ralph-master-validation.log; then
        echo "✗ Authentication error occurred"
    else
        echo "✓ No authentication errors"
    fi

    if [ -f ".agent/skillbook/skillbook.json" ]; then
        echo "✓ Skillbook exists"
        echo "  Skills count: $(jq '.skills | length' .agent/skillbook/skillbook.json)"
    else
        echo "○ Skillbook not created (may be first run)"
    fi

    echo ""
    echo "2. LOG STREAMING"
    echo "----------------"
    JSONL_COUNT=$(ls .agent/logs/ralph-*.jsonl 2>/dev/null | wc -l)
    echo "JSONL files: $JSONL_COUNT"

    if [ "$JSONL_COUNT" -gt 0 ]; then
        LATEST_JSONL=$(ls -t .agent/logs/ralph-*.jsonl | head -1)
        echo "Latest: $LATEST_JSONL"
        echo "Lines: $(wc -l < "$LATEST_JSONL")"

        for level in DEBUG INFO WARNING ERROR; do
            COUNT=$(grep "\"level\":\"$level\"" "$LATEST_JSONL" | wc -l)
            echo "  $level: $COUNT entries"
        done
    fi

    echo ""
    echo "3. TOOL CALL STREAMING"
    echo "----------------------"
    if [ -n "$LATEST_JSONL" ]; then
        TOOL_CALLS=$(grep '"type":"tool_call"' "$LATEST_JSONL" 2>/dev/null | wc -l)
        echo "Tool calls recorded: $TOOL_CALLS"

        if [ "$TOOL_CALLS" -gt 0 ]; then
            echo "Tools used:"
            grep '"type":"tool_call"' "$LATEST_JSONL" | jq -r '.tool_name' | sort | uniq -c | sort -rn
        fi
    fi

    echo ""
    echo "4. CONTEXT TRACKING"
    echo "-------------------"
    TIMELINE_FILE=$(ls -t .agent/metrics/context-timeline-*.json 2>/dev/null | head -1)
    if [ -n "$TIMELINE_FILE" ]; then
        echo "✓ Timeline file: $TIMELINE_FILE"
        echo "  Measurements: $(jq '.measurements | length' "$TIMELINE_FILE")"
        echo "  Peak usage: $(jq '.summary.peak_usage_percent' "$TIMELINE_FILE")%"
        echo "  Iterations: $(jq '.summary.iterations_tracked' "$TIMELINE_FILE")"
    else
        echo "✗ No timeline file found"
    fi

    echo ""
    echo "5. MONITOR DASHBOARD"
    echo "--------------------"
    if tmux has-session -t ralph-master-validation 2>/dev/null; then
        echo "✓ Monitor session running"
    else
        echo "○ Monitor session not running (may have been stopped)"
    fi

    echo ""
    echo "=========================================="
    echo "VALIDATION COMPLETE"

} | tee "$RESULTS_FILE"

# Cleanup
kill $MONITOR_PID 2>/dev/null || true
tmux kill-session -t ralph-master-validation 2>/dev/null || true

echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""
echo "To manually explore the dashboard:"
echo "  ./scripts/monitor.sh"
```

### Sign-off Checklist

| # | Validation Item | Status | Validator | Date |
|---|-----------------|--------|-----------|------|
| 1 | ACE learning initializes without API key errors | ☐ | | |
| 2 | Skillbook is created/updated after successful iteration | ☐ | | |
| 3 | DEBUG/INFO/WARNING/ERROR logs visible in console | ☐ | | |
| 4 | JSONL log file created with structured entries | ☐ | | |
| 5 | FIFO pipe receives real-time log data | ☐ | | |
| 6 | Tool calls show START/END with duration | ☐ | | |
| 7 | Tool call aggregation works (count by tool type) | ☐ | | |
| 8 | Context measurements recorded at each iteration | ☐ | | |
| 9 | Context timeline JSON file generated | ☐ | | |
| 10 | ASCII context visualization displays correctly | ☐ | | |
| 11 | monitor.sh creates tmux session with 4 panes | ☐ | | |
| 12 | Dashboard updates in real-time during Ralph run | ☐ | | |
| 13 | End-to-end: Ralph + monitor work together | ☐ | | |

---

## Appendix: Quick Reference

### CLI Flags (After Implementation)

```bash
# Basic run with learning
ralph run --learning "task"

# Full monitoring
ralph run --learning --stream-logs --log-level DEBUG "task"

# Custom skillbook location
ralph run --learning --skillbook-path "./my-skillbook.json" "task"

# With monitor dashboard
./scripts/ralph-with-monitor.sh "task"
```

### File Locations

```
.agent/
├── logs/
│   ├── ralph-YYYYMMDD-HHMMSS.jsonl    # Structured JSON logs
│   └── ralph-stream.fifo              # Real-time FIFO pipe
├── metrics/
│   └── context-timeline-*.json        # Context measurements
├── skillbook/
│   └── skillbook.json                 # ACE learned skills
└── checkpoints/
    └── ...                            # Git checkpoints
```

### Environment Variables

```bash
# Required for ACE learning
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional configuration
export RALPH_LOG_LEVEL="DEBUG"
export RALPH_SKILLBOOK_PATH=".agent/skillbook/skillbook.json"
export RALPH_STREAM_LOGS="true"
```

---

**Plan Author**: Claude (Opus 4.5)
**Plan Version**: 1.0
**Created**: 2026-01-10 02:20 EST
**Target Completion**: 2026-01-10 EOD
