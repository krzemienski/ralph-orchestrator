#!/bin/bash
# ABOUTME: Convenience script to run Ralph with full monitoring enabled
# ABOUTME: Starts monitor dashboard in background and runs Ralph with all flags
#
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
