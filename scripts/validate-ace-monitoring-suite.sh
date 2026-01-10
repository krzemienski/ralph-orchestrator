#!/bin/bash
# ABOUTME: Master validation script for the complete ACE Monitoring Suite
# ABOUTME: Tests all components (Log Streaming, Tool Tracking, Context, Dashboard) together
#
# Master validation - ALL components together
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     RALPH MONITORING SUITE - MASTER VALIDATION                ║"
echo "║     Date: $(date -Iseconds)                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

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
    echo "ERROR: Cannot find Python with ralph_orchestrator installed"
    exit 1
fi

echo "Using Python: $($PYTHON --version) at $PYTHON"
echo ""

RESULTS=""

# Component 2: Log Streaming
echo "Testing Component 2: Log Streaming..."
if $PYTHON -m ralph_orchestrator run --help 2>&1 | grep -q "log-level"; then
    echo "  ✓ --log-level flag present"
    RESULTS+="C2-LogLevel:PASS\n"
else
    echo "  ✗ --log-level flag missing"
    RESULTS+="C2-LogLevel:FAIL\n"
fi

if $PYTHON -m ralph_orchestrator run --help 2>&1 | grep -q "stream-logs"; then
    echo "  ✓ --stream-logs flag present"
    RESULTS+="C2-StreamLogs:PASS\n"
else
    echo "  ✗ --stream-logs flag missing"
    RESULTS+="C2-StreamLogs:FAIL\n"
fi

# Component 3: Tool Call Streaming
echo ""
echo "Testing Component 3: Tool Call Streaming..."
if $PYTHON -c "from ralph_orchestrator.logging import ToolCallTracker" 2>/dev/null; then
    echo "  ✓ ToolCallTracker importable"
    RESULTS+="C3-ToolTracker:PASS\n"
else
    echo "  ✗ ToolCallTracker import failed"
    RESULTS+="C3-ToolTracker:FAIL\n"
fi

# Component 4: Context Tracking
echo ""
echo "Testing Component 4: Context Tracking..."
if $PYTHON -c "from ralph_orchestrator.monitoring import ContextTracker" 2>/dev/null; then
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

# Dry run with stream-logs - capture output for inspection
$PYTHON -m ralph_orchestrator run \
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
