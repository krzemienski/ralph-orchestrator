#!/usr/bin/env bash
# ABOUTME: Phase 3 validation script for Context Tracking
# ABOUTME: Validates ContextTracker with tiktoken token counting

set -uo pipefail
# Note: Not using set -e because we capture exit codes explicitly

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Phase 3 Validation: Context Tracking"
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
echo "--- Check 1: ContextTracker module exists ---"
$PYTHON -c "from ralph_orchestrator.monitoring import ContextTracker, ContextMeasurement, MeasurePoint" 2>/dev/null
check "ContextTracker, ContextMeasurement, MeasurePoint can be imported" $?

echo ""
echo "--- Check 2: MeasurePoint enum has required values ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import MeasurePoint
assert MeasurePoint.ITERATION_START.value == 'iteration_start', 'Missing ITERATION_START'
assert MeasurePoint.AFTER_PROMPT_INJECT.value == 'after_prompt_inject', 'Missing AFTER_PROMPT_INJECT'
assert MeasurePoint.AFTER_TOOL_CALL.value == 'after_tool_call', 'Missing AFTER_TOOL_CALL'
assert MeasurePoint.ITERATION_END.value == 'iteration_end', 'Missing ITERATION_END'
print('All required MeasurePoint values present')
" 2>/dev/null
check "MeasurePoint enum has ITERATION_START, AFTER_PROMPT_INJECT, AFTER_TOOL_CALL, ITERATION_END" $?

echo ""
echo "--- Check 3: ContextTracker.count_tokens works ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker
tracker = ContextTracker()
tokens = tracker.count_tokens('Hello, world! This is a test message.')
assert tokens > 0, f'Token count should be > 0, got {tokens}'
print(f'Token count: {tokens}')
" 2>/dev/null
check "ContextTracker.count_tokens returns positive count" $?

echo ""
echo "--- Check 4: tiktoken is available (accurate counting) ---"
$PYTHON -c "
import tiktoken
encoder = tiktoken.encoding_for_model('gpt-4')
tokens = len(encoder.encode('Hello world'))
print(f'tiktoken available, test token count: {tokens}')
" 2>/dev/null
check "tiktoken is installed and working" $?

echo ""
echo "--- Check 5: ContextMeasurement has percentage_used field ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker, MeasurePoint
tracker = ContextTracker(adapter_type='claude')
measurement = tracker.measure(MeasurePoint.ITERATION_START, 'Test content', 'test', iteration=1)
assert hasattr(measurement, 'percentage_used'), 'Missing percentage_used'
assert measurement.percentage_used >= 0, f'percentage_used should be >= 0, got {measurement.percentage_used}'
print(f'percentage_used: {measurement.percentage_used}')
" 2>/dev/null
check "ContextMeasurement includes percentage_used field" $?

echo ""
echo "--- Check 6: Context measurements logged with token counts ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker, MeasurePoint

tracker = ContextTracker(adapter_type='claude')

# Measure multiple points
m1 = tracker.measure(MeasurePoint.ITERATION_START, 'Initial prompt text' * 100, 'initial_prompt', iteration=1)
m2 = tracker.measure(MeasurePoint.AFTER_PROMPT_INJECT, 'Initial prompt text' * 100 + 'Enhanced prompt' * 50, 'enhanced_prompt')
m3 = tracker.measure(MeasurePoint.AFTER_TOOL_CALL, 'Initial prompt text' * 100 + 'Enhanced prompt' * 50 + 'Tool result' * 20, 'tool_result')
m4 = tracker.measure(MeasurePoint.ITERATION_END, 'Final context' * 200, 'final', iteration=1)

# Verify token counts
assert m1.tokens > 0, 'First measurement should have tokens'
assert m3.tokens > m2.tokens, 'After tool call should have more tokens'
assert m1.delta_tokens > 0, 'First measurement delta should be positive'

print(f'Measurements recorded: 4')
print(f'Token range: {m1.tokens} to {m4.tokens}')
print(f'Peak percentage: {max(m.percentage_used for m in [m1, m2, m3, m4]):.2f}%')
" 2>/dev/null
check "Context measurements logged with token counts" $?

echo ""
echo "--- Check 7: Timeline JSON file created ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker, MeasurePoint
import tempfile
import os
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    output_dir = Path(tmpdir) / 'metrics'
    tracker = ContextTracker(adapter_type='claude', output_dir=output_dir)

    # Add some measurements
    tracker.measure(MeasurePoint.ITERATION_START, 'Test content', 'test', iteration=1)
    tracker.measure(MeasurePoint.ITERATION_END, 'Test content final', 'final')

    # Save timeline
    filepath = tracker.save_timeline()

    assert filepath.exists(), f'Timeline file not created at {filepath}'
    assert filepath.suffix == '.json', 'Timeline should be JSON'
    assert 'context-timeline-' in filepath.name, 'Filename should contain context-timeline-'

    # Verify content
    import json
    with open(filepath) as f:
        data = json.load(f)

    assert 'metadata' in data, 'Missing metadata'
    assert 'measurements' in data, 'Missing measurements'
    assert len(data['measurements']) == 2, f'Expected 2 measurements, got {len(data[\"measurements\"])}'

    print(f'Timeline file created: {filepath.name}')
    print(f'Measurements in file: {len(data[\"measurements\"])}')
" 2>/dev/null
check "Timeline JSON file created with correct structure" $?

echo ""
echo "--- Check 8: ASCII visualization generates correctly ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker, MeasurePoint

# Use kiro adapter (8k limit) to get visible bar fill with reasonable content
tracker = ContextTracker(adapter_type='kiro')

# Add measurements - with 8k limit, 2k tokens = 25% visible
tracker.measure(MeasurePoint.ITERATION_START, 'A' * 4000, 'start', iteration=1)  # ~1k tokens
tracker.measure(MeasurePoint.AFTER_PROMPT_INJECT, 'A' * 16000, 'prompt', iteration=1)  # ~4k tokens = 50%
tracker.measure(MeasurePoint.ITERATION_END, 'A' * 24000, 'end', iteration=1)  # ~6k tokens = 75%

# Get ASCII timeline
ascii_timeline = tracker.get_timeline_ascii()

assert 'Context Usage Timeline' in ascii_timeline, 'Missing header'
assert 'Iteration 1' in ascii_timeline, 'Missing iteration label'
assert '█' in ascii_timeline, 'Missing progress bar (filled)'
assert '░' in ascii_timeline, 'Missing progress bar (empty)'
assert '%' in ascii_timeline, 'Missing percentage'

print('ASCII timeline sample:')
print(ascii_timeline[:600])
" 2>/dev/null
check "ASCII visualization generates correctly" $?

echo ""
echo "--- Check 9: Summary statistics work ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker, MeasurePoint

tracker = ContextTracker(adapter_type='claude')

tracker.measure(MeasurePoint.ITERATION_START, 'A' * 1000, 'start', iteration=1)
tracker.measure(MeasurePoint.ITERATION_END, 'A' * 5000, 'end', iteration=1)
tracker.measure(MeasurePoint.ITERATION_START, 'B' * 2000, 'start', iteration=2)
tracker.measure(MeasurePoint.ITERATION_END, 'B' * 8000, 'end', iteration=2)

summary = tracker.get_summary()

assert 'total_measurements' in summary, 'Missing total_measurements'
assert 'iterations_tracked' in summary, 'Missing iterations_tracked'
assert 'peak_usage_percent' in summary, 'Missing peak_usage_percent'
assert 'peak_tokens' in summary, 'Missing peak_tokens'
assert 'context_limit' in summary, 'Missing context_limit'

assert summary['total_measurements'] == 4, f'Expected 4 measurements, got {summary[\"total_measurements\"]}'
assert summary['iterations_tracked'] == 2, f'Expected 2 iterations, got {summary[\"iterations_tracked\"]}'

print(f'Summary: {summary}')
" 2>/dev/null
check "Summary statistics work correctly" $?

echo ""
echo "--- Check 10: Different adapters have different context limits ---"
$PYTHON -c "
from ralph_orchestrator.monitoring import ContextTracker

claude_tracker = ContextTracker(adapter_type='claude')
gemini_tracker = ContextTracker(adapter_type='gemini')
kiro_tracker = ContextTracker(adapter_type='kiro')

assert claude_tracker.context_limit == 200_000, f'Claude limit should be 200k, got {claude_tracker.context_limit}'
assert gemini_tracker.context_limit == 32_000, f'Gemini limit should be 32k, got {gemini_tracker.context_limit}'
assert kiro_tracker.context_limit == 8_000, f'Kiro limit should be 8k, got {kiro_tracker.context_limit}'

print(f'Claude limit: {claude_tracker.context_limit:,}')
print(f'Gemini limit: {gemini_tracker.context_limit:,}')
print(f'Kiro limit: {kiro_tracker.context_limit:,}')
" 2>/dev/null
check "Different adapters have correct context limits" $?

echo ""
echo "=============================================="
echo "Phase 3 Validation Results"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo -e "${RED}VALIDATION FAILED - Fix issues before proceeding to Phase 4${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}ALL CHECKS PASSED - Ready for Phase 4${NC}"
    exit 0
fi
