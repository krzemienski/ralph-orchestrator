#!/usr/bin/env bash
# ABOUTME: Phase 2 validation script for Tool Call Streaming
# ABOUTME: Validates ToolCallTracker integration with VerboseLogger

set -uo pipefail
# Note: Not using set -e because we capture exit codes explicitly

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Phase 2 Validation: Tool Call Streaming"
echo "=============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Find the correct Python interpreter (handles virtualenv path issues)
PYTHON=""

# First check project venv locations
for venv_path in "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/.venv/bin/python3"; do
    if [ -x "$venv_path" ]; then
        if "$venv_path" -c "import ralph_orchestrator" 2>/dev/null; then
            PYTHON="$venv_path"
            break
        fi
    fi
done

# Fallback to system Python
if [ -z "$PYTHON" ]; then
    for candidate in python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if command -v "$candidate" &>/dev/null || [ -x "$candidate" ]; then
            if "$candidate" -c "import ralph_orchestrator" 2>/dev/null; then
                PYTHON="$candidate"
                break
            fi
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    echo -e "${RED}FAIL: Cannot find Python with ralph_orchestrator installed${NC}"
    echo "Tried: .venv/bin/python, venv/bin/python, python3, /opt/homebrew/bin/python3"
    exit 1
fi

echo "Using Python: $($PYTHON --version) at $(which $PYTHON)"

# Track results
PASSED=0
FAILED=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $desc"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $desc"
        ((FAILED++))
    fi
}

echo ""
echo "--- Check 1: ToolCallTracker module exists ---"
$PYTHON -c "from ralph_orchestrator.logging.tool_tracker import ToolCallTracker, ToolCallEvent" 2>/dev/null
check "ToolCallTracker and ToolCallEvent can be imported" $?

echo ""
echo "--- Check 2: ToolCallTracker has required methods ---"
$PYTHON -c "
from ralph_orchestrator.logging.tool_tracker import ToolCallTracker
tracker = ToolCallTracker()
assert hasattr(tracker, 'start_call'), 'Missing start_call method'
assert hasattr(tracker, 'end_call'), 'Missing end_call method'
assert hasattr(tracker, 'get_summary'), 'Missing get_summary method'
print('All required methods present')
" 2>/dev/null
check "ToolCallTracker has start_call, end_call, get_summary methods" $?

echo ""
echo "--- Check 3: ToolCallEvent has duration_ms property ---"
$PYTHON -c "
from ralph_orchestrator.logging.tool_tracker import ToolCallEvent
from datetime import datetime
import time

event = ToolCallEvent(
    tool_name='TestTool',
    arguments={'test': 'value'},
    start_time=datetime.now()
)
time.sleep(0.01)  # 10ms
event.end_time = datetime.now()

assert event.duration_ms is not None, 'duration_ms should not be None'
assert event.duration_ms >= 10, f'Duration should be >= 10ms, got {event.duration_ms}'
print(f'Duration calculated: {event.duration_ms:.0f}ms')
" 2>/dev/null
check "ToolCallEvent calculates duration_ms correctly" $?

echo ""
echo "--- Check 4: VerboseLogger accepts stream_logger parameter ---"
$PYTHON -c "
import inspect
from ralph_orchestrator.verbose_logger import VerboseLogger
sig = inspect.signature(VerboseLogger.__init__)
params = list(sig.parameters.keys())
assert 'stream_logger' in params, f'stream_logger not in params: {params}'
print('stream_logger parameter found')
" 2>/dev/null
check "VerboseLogger.__init__ accepts stream_logger parameter" $?

echo ""
echo "--- Check 5: VerboseLogger creates ToolCallTracker when stream_logger provided ---"
$PYTHON -c "
from ralph_orchestrator.verbose_logger import VerboseLogger
from ralph_orchestrator.logging.stream_logger import create_stream_logger
import tempfile
import os

# Create a temp directory for logs
with tempfile.TemporaryDirectory() as tmpdir:
    # Create stream logger
    stream_logger = create_stream_logger(
        log_level='DEBUG',
        enable_console=False,  # No console output during test
        enable_file=True,
        enable_fifo=False,
        log_dir=tmpdir
    )

    # Create verbose logger with stream logger
    verbose_logger = VerboseLogger(log_dir=tmpdir, stream_logger=stream_logger)

    assert verbose_logger.stream_logger is not None, 'stream_logger not stored'
    assert verbose_logger.tool_tracker is not None, 'tool_tracker not created'
    print('ToolCallTracker created successfully')

    stream_logger.cleanup()
" 2>/dev/null
check "VerboseLogger creates ToolCallTracker when stream_logger provided" $?

echo ""
echo "--- Check 6: ToolCallTracker emits START/END events through StreamLogger ---"
$PYTHON -c "
from ralph_orchestrator.logging.tool_tracker import ToolCallTracker
from ralph_orchestrator.logging.stream_logger import create_stream_logger
import tempfile
import json
import os

with tempfile.TemporaryDirectory() as tmpdir:
    # Create stream logger with file output
    stream_logger = create_stream_logger(
        log_level='DEBUG',
        enable_console=False,
        enable_file=True,
        enable_fifo=False,
        log_dir=tmpdir
    )

    # Create tracker with stream logger
    tracker = ToolCallTracker(stream_logger=stream_logger)

    # Simulate a tool call
    event = tracker.start_call('Read', {'file_path': '/test/file.py'})
    tracker.end_call(event, result='file content here', success=True)

    # Cleanup to flush
    stream_logger.cleanup()

    # Read the log file
    log_file = stream_logger.log_file_path
    if log_file and os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Check for START and END events
        start_found = False
        end_found = False
        for line in lines:
            data = json.loads(line)
            if 'START' in data.get('message', ''):
                start_found = True
                print(f'START event: {data[\"message\"]}')
            if 'END' in data.get('message', ''):
                end_found = True
                print(f'END event: {data[\"message\"]}')

        assert start_found, 'START event not found in logs'
        assert end_found, 'END event not found in logs'
        print('Both START and END events emitted')
    else:
        raise AssertionError('Log file not created')
" 2>/dev/null
check "ToolCallTracker emits START/END events to JSONL" $?

echo ""
echo "--- Check 7: JSONL contains tool_name in events ---"
$PYTHON -c "
from ralph_orchestrator.logging.tool_tracker import ToolCallTracker
from ralph_orchestrator.logging.stream_logger import create_stream_logger
import tempfile
import json
import os

with tempfile.TemporaryDirectory() as tmpdir:
    stream_logger = create_stream_logger(
        log_level='DEBUG',
        enable_console=False,
        enable_file=True,
        enable_fifo=False,
        log_dir=tmpdir
    )

    tracker = ToolCallTracker(stream_logger=stream_logger)
    event = tracker.start_call('Bash', {'command': 'echo hello'})
    tracker.end_call(event, result='hello', success=True)
    stream_logger.cleanup()

    log_file = stream_logger.log_file_path
    with open(log_file, 'r') as f:
        lines = f.readlines()

    tool_name_found = False
    for line in lines:
        data = json.loads(line)
        # tool_name is in metadata dict
        metadata = data.get('metadata', {})
        if metadata.get('tool_name') == 'Bash':
            tool_name_found = True
            print(f'Found tool_name in metadata: {metadata.get(\"tool_name\")}')
            break

    assert tool_name_found, 'tool_name not found in JSONL entries'
" 2>/dev/null
check "JSONL contains tool_name field in metadata" $?

echo ""
echo "--- Check 8: END event includes duration_ms ---"
$PYTHON -c "
from ralph_orchestrator.logging.tool_tracker import ToolCallTracker
from ralph_orchestrator.logging.stream_logger import create_stream_logger
import tempfile
import json
import os
import time

with tempfile.TemporaryDirectory() as tmpdir:
    stream_logger = create_stream_logger(
        log_level='DEBUG',
        enable_console=False,
        enable_file=True,
        enable_fifo=False,
        log_dir=tmpdir
    )

    tracker = ToolCallTracker(stream_logger=stream_logger)
    event = tracker.start_call('Glob', {'pattern': '*.py'})
    time.sleep(0.05)  # 50ms
    tracker.end_call(event, result='10 files', success=True)
    stream_logger.cleanup()

    log_file = stream_logger.log_file_path
    with open(log_file, 'r') as f:
        lines = f.readlines()

    duration_found = False
    for line in lines:
        data = json.loads(line)
        metadata = data.get('metadata', {})
        if 'END' in data.get('message', '') and metadata.get('duration_ms') is not None:
            duration_found = True
            print(f'Duration in END event metadata: {metadata.get(\"duration_ms\")}ms')
            assert metadata.get('duration_ms') >= 50, f'Duration should be >= 50ms'
            break

    assert duration_found, 'duration_ms not found in END event metadata'
" 2>/dev/null
check "END event includes duration_ms in JSONL metadata" $?

echo ""
echo "=============================================="
echo "Phase 2 Validation Results"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo -e "${RED}VALIDATION FAILED - Fix issues before proceeding to Phase 3${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}ALL CHECKS PASSED - Ready for Phase 3${NC}"
    exit 0
fi
