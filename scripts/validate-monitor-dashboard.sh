#!/usr/bin/env bash
# ABOUTME: Phase 4 validation script for Monitor Dashboard
# ABOUTME: Validates monitor.sh structure and dependencies

set -uo pipefail
# Note: Not using set -e because we capture exit codes explicitly

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Phase 4 Validation: Monitor Dashboard"
echo "=============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

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
echo "--- Check 1: monitor.sh exists and is executable ---"
[ -x "$SCRIPT_DIR/monitor.sh" ]
check "monitor.sh exists and is executable" $?

echo ""
echo "--- Check 2: ralph-with-monitor.sh exists and is executable ---"
[ -x "$SCRIPT_DIR/ralph-with-monitor.sh" ]
check "ralph-with-monitor.sh exists and is executable" $?

echo ""
echo "--- Check 3: tmux is installed ---"
command -v tmux >/dev/null 2>&1
check "tmux is installed" $?

echo ""
echo "--- Check 4: jq is installed ---"
command -v jq >/dev/null 2>&1
check "jq is installed" $?

echo ""
echo "--- Check 5: monitor.sh has required functions ---"
grep -q "generate_status()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "generate_tools()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "generate_context_timeline()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "stream_logs()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "create_dashboard()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null
check "monitor.sh has all required functions (generate_status, generate_tools, generate_context_timeline, stream_logs, create_dashboard)" $?

echo ""
echo "--- Check 6: monitor.sh checks dependencies ---"
grep -q "check_deps()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null
check "monitor.sh has dependency check function" $?

echo ""
echo "--- Check 7: monitor.sh creates FIFO pipe ---"
grep -q "mkfifo" "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "setup_fifo()" "$SCRIPT_DIR/monitor.sh" 2>/dev/null
check "monitor.sh sets up FIFO pipe" $?

echo ""
echo "--- Check 8: monitor.sh uses tmux for dashboard ---"
grep -q "tmux new-session" "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "tmux split-window" "$SCRIPT_DIR/monitor.sh" 2>/dev/null
check "monitor.sh uses tmux for dashboard layout" $?

echo ""
echo "--- Check 9: monitor.sh reads context timeline JSON ---"
grep -q "context-timeline-" "$SCRIPT_DIR/monitor.sh" 2>/dev/null
check "monitor.sh reads context timeline JSON files" $?

echo ""
echo "--- Check 10: monitor.sh parses JSONL logs ---"
grep -q '\.jsonl' "$SCRIPT_DIR/monitor.sh" 2>/dev/null && \
grep -q "jq" "$SCRIPT_DIR/monitor.sh" 2>/dev/null
check "monitor.sh parses JSONL log files with jq" $?

echo ""
echo "--- Check 11: ralph-with-monitor.sh starts monitor in tmux ---"
grep -q "tmux new-session -d -s ralph-monitor" "$SCRIPT_DIR/ralph-with-monitor.sh" 2>/dev/null
check "ralph-with-monitor.sh starts monitor in tmux background session" $?

echo ""
echo "--- Check 12: ralph-with-monitor.sh uses --stream-logs flag ---"
grep -q "\-\-stream-logs" "$SCRIPT_DIR/ralph-with-monitor.sh" 2>/dev/null
check "ralph-with-monitor.sh passes --stream-logs to ralph" $?

echo ""
echo "=============================================="
echo "Phase 4 Validation Results"
echo "=============================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo -e "${RED}VALIDATION FAILED - Fix issues before proceeding to Phase 5${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}ALL CHECKS PASSED - Ready for Phase 5${NC}"
    exit 0
fi
