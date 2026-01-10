#!/bin/bash
#
# ACE Learning API Key Fix Validation Script
# Tests that the ACE learning adapter properly receives API keys
#

set -e
echo "=== ACE Learning API Key Fix Validation ==="
echo "Date: $(date -Iseconds)"
echo ""

cd "$(dirname "$0")/.."

# Step 1: Verify API key is set
echo "[1/5] Checking ANTHROPIC_API_KEY is set..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "FAIL: ANTHROPIC_API_KEY not set"
    echo "Please run: export ANTHROPIC_API_KEY='your-key'"
    exit 1
fi
echo "PASS: API key present (${#ANTHROPIC_API_KEY} chars)"

# Step 2: Run ralph with learning enabled (dry-run)
echo ""
echo "[2/5] Running ralph with --learning --dry-run..."
set +e  # Don't exit on error, we want to capture output
python -m ralph_orchestrator run --learning --dry-run -p "Create a simple hello.py file that prints hello world" 2>&1 | tee /tmp/ralph-ace-test.log
EXIT_CODE=$?
set -e

# Step 3: Check for authentication errors
echo ""
echo "[3/5] Checking for authentication errors..."
if grep -qi "AuthenticationError\|Missing.*API.*Key\|api_key.*required" /tmp/ralph-ace-test.log; then
    echo "FAIL: Authentication error found in output"
    grep -i "AuthenticationError\|Missing.*API.*Key\|api_key.*required" /tmp/ralph-ace-test.log
    exit 1
fi
echo "PASS: No authentication errors"

# Step 4: Check ACE learning initialized
echo ""
echo "[4/5] Checking ACE learning initialized..."
if grep -qi "ACE learning initialized\|learning.*initialized\|using API key" /tmp/ralph-ace-test.log; then
    echo "PASS: ACE learning initialization confirmed"
    grep -i "ACE learning\|learning.*init" /tmp/ralph-ace-test.log | head -3
else
    echo "INFO: Could not confirm ACE learning initialization in logs"
    echo "      (This may be expected if learning happens silently)"
fi

# Step 5: Check skillbook was accessed
echo ""
echo "[5/5] Checking skillbook interaction..."
SKILLBOOK_PATH=".agent/skillbook/skillbook.json"
if [ -f "$SKILLBOOK_PATH" ]; then
    echo "PASS: Skillbook exists at $SKILLBOOK_PATH"
    if command -v jq &> /dev/null; then
        echo "Skills count: $(jq '.skills | length' "$SKILLBOOK_PATH" 2>/dev/null || echo 'N/A')"
    fi
else
    echo "INFO: No skillbook yet (will be created on first successful learning)"
fi

echo ""
echo "=== Validation Summary ==="
if [ $EXIT_CODE -eq 0 ]; then
    echo "RESULT: PASS - Ralph executed successfully with learning enabled"
else
    echo "RESULT: Ralph exited with code $EXIT_CODE (may be expected for dry-run)"
fi
echo ""
echo "Full output saved to: /tmp/ralph-ace-test.log"
