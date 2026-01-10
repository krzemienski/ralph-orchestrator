#!/bin/bash
# ABOUTME: Real-time tmux dashboard for monitoring Ralph orchestration
# ABOUTME: Shows live logs, status, tool calls, and context timeline
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
