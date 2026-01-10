#!/bin/bash
# ABOUTME: Run ACE learning benchmark suite with or without learning enabled
# ABOUTME: Captures metrics per-prompt and generates aggregate report

set -e

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROMPTS_DIR="$SCRIPT_DIR/benchmark-prompts"
OUTPUT_BASE_DIR="$PROJECT_ROOT/docs/benchmarks/runs"

# Default settings
LEARNING_MODE="${1:-disabled}"  # "enabled" or "disabled"
MAX_ITERATIONS="${MAX_ITERATIONS:-15}"
MODEL="${MODEL:-claude-sonnet-4-5-20250929}"
LEARNING_MODEL="${LEARNING_MODEL:-gpt-4o-mini}"
SKILLBOOK_PATH="${SKILLBOOK_PATH:-.agent/skillbook/skillbook.json}"
CLEAR_SKILLBOOK="${CLEAR_SKILLBOOK:-false}"
DRY_RUN="${DRY_RUN:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# Functions
# =============================================================================

usage() {
    cat << EOF
Usage: $0 [enabled|disabled] [OPTIONS]

Run the ACE learning benchmark suite.

Arguments:
  enabled     Run with ACE learning enabled
  disabled    Run with ACE learning disabled (baseline)

Environment Variables:
  MAX_ITERATIONS      Maximum iterations per prompt (default: 15)
  MODEL               Main agent model (default: claude-sonnet-4-5-20250929)
  LEARNING_MODEL      ACE learning model (default: gpt-4o-mini)
  SKILLBOOK_PATH      Path to skillbook (default: .agent/skillbook/skillbook.json)
  CLEAR_SKILLBOOK     Clear skillbook before run (default: false)
  DRY_RUN             Show what would be run without executing (default: false)

Examples:
  # Run baseline (no learning)
  $0 disabled

  # Run with learning, clear skillbook first
  CLEAR_SKILLBOOK=true $0 enabled

  # Dry run to see prompts
  DRY_RUN=true $0 enabled

  # Run with custom model
  MODEL=claude-opus-4 $0 enabled
EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

check_dependencies() {
    local missing=()

    command -v ralph >/dev/null 2>&1 || missing+=("ralph")
    command -v jq >/dev/null 2>&1 || missing+=("jq")

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_error "Install ralph with: pip install ralph-orchestrator"
        log_error "Install jq with: brew install jq"
        exit 1
    fi
}

setup_output_dir() {
    local timestamp=$(date +%Y%m%d-%H%M%S)
    OUTPUT_DIR="$OUTPUT_BASE_DIR/$LEARNING_MODE-$timestamp"
    mkdir -p "$OUTPUT_DIR"
    log_info "Output directory: $OUTPUT_DIR"
}

clear_skillbook() {
    if [ "$CLEAR_SKILLBOOK" = "true" ]; then
        local skillbook_full_path="$PROJECT_ROOT/$SKILLBOOK_PATH"
        if [ -f "$skillbook_full_path" ]; then
            local backup_path="${skillbook_full_path}.backup.$(date +%Y%m%d-%H%M%S)"
            cp "$skillbook_full_path" "$backup_path"
            log_info "Backed up skillbook to: $backup_path"
            rm "$skillbook_full_path"
            log_info "Cleared skillbook"
        fi
    fi
}

count_skills() {
    local skillbook_full_path="$PROJECT_ROOT/$SKILLBOOK_PATH"
    if [ -f "$skillbook_full_path" ]; then
        jq '.skills | length' "$skillbook_full_path" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

run_prompt() {
    local prompt_file="$1"
    local prompt_name=$(basename "$prompt_file" .txt)
    local result_file="$OUTPUT_DIR/$prompt_name.json"

    log_info "Running: $prompt_name"

    # Read the prompt
    local prompt_content=$(cat "$prompt_file")

    # Build ralph command
    local ralph_cmd="ralph run"
    ralph_cmd+=" --max-iterations $MAX_ITERATIONS"
    ralph_cmd+=" --model $MODEL"
    ralph_cmd+=" --metrics"
    ralph_cmd+=" --no-interactive"

    if [ "$LEARNING_MODE" = "enabled" ]; then
        ralph_cmd+=" --learning"
        ralph_cmd+=" --learning-model $LEARNING_MODEL"
        ralph_cmd+=" --skillbook-path $SKILLBOOK_PATH"
    fi

    # Add prompt
    ralph_cmd+=" -p \"$(echo "$prompt_content" | head -1)\""

    if [ "$DRY_RUN" = "true" ]; then
        echo "  Would run: $ralph_cmd"
        return 0
    fi

    # Capture start time
    local start_time=$(date +%s.%N)
    local skills_before=$(count_skills)

    # Run ralph and capture output
    local ralph_output
    local exit_code=0

    cd "$PROJECT_ROOT"

    # Execute with timeout and capture output
    set +e
    ralph_output=$(timeout 600 ralph run \
        --max-iterations "$MAX_ITERATIONS" \
        --model "$MODEL" \
        --metrics \
        --no-interactive \
        $([ "$LEARNING_MODE" = "enabled" ] && echo "--learning --learning-model $LEARNING_MODEL --skillbook-path $SKILLBOOK_PATH") \
        -p "$prompt_content" 2>&1)
    exit_code=$?
    set -e

    # Capture end time
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    local skills_after=$(count_skills)

    # Parse metrics from output
    local iterations=$(echo "$ralph_output" | grep -oP 'iterations:\s*\K\d+' | tail -1 || echo "0")
    local tokens=$(echo "$ralph_output" | grep -oP 'tokens:\s*\K\d+' | tail -1 || echo "0")
    local cost=$(echo "$ralph_output" | grep -oP 'cost:\s*\$?\K[\d.]+' | tail -1 || echo "0")
    local success="false"

    if [ $exit_code -eq 0 ]; then
        if echo "$ralph_output" | grep -qE "(completed|success|done)"; then
            success="true"
        fi
    fi

    # Create result JSON
    cat > "$result_file" << EOF
{
  "prompt_name": "$prompt_name",
  "prompt_file": "$prompt_file",
  "learning_mode": "$LEARNING_MODE",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "configuration": {
    "model": "$MODEL",
    "learning_model": "$LEARNING_MODEL",
    "max_iterations": $MAX_ITERATIONS
  },
  "results": {
    "success": $success,
    "exit_code": $exit_code,
    "iterations": $iterations,
    "tokens": $tokens,
    "cost_usd": $cost,
    "duration_seconds": $duration,
    "skills_before": $skills_before,
    "skills_after": $skills_after,
    "skills_learned": $((skills_after - skills_before))
  },
  "output_excerpt": $(echo "$ralph_output" | tail -50 | jq -Rs .)
}
EOF

    if [ "$success" = "true" ]; then
        log_success "$prompt_name completed | iterations=$iterations | tokens=$tokens | duration=${duration}s"
    else
        log_warning "$prompt_name failed | exit_code=$exit_code | iterations=$iterations"
    fi
}

generate_aggregate_report() {
    log_header "Generating Aggregate Report"

    local report_file="$OUTPUT_DIR/REPORT.md"
    local summary_file="$OUTPUT_DIR/summary.json"

    # Count results
    local total_prompts=$(ls "$OUTPUT_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')

    if [ "$total_prompts" -eq 0 ]; then
        log_warning "No results to aggregate"
        return
    fi

    # Aggregate metrics
    local total_iterations=0
    local total_tokens=0
    local total_cost=0
    local total_duration=0
    local successful=0
    local total_skills_learned=0

    for result_file in "$OUTPUT_DIR"/*.json; do
        iterations=$(jq '.results.iterations' "$result_file" 2>/dev/null || echo 0)
        tokens=$(jq '.results.tokens' "$result_file" 2>/dev/null || echo 0)
        cost=$(jq '.results.cost_usd' "$result_file" 2>/dev/null || echo 0)
        duration=$(jq '.results.duration_seconds' "$result_file" 2>/dev/null || echo 0)
        success=$(jq '.results.success' "$result_file" 2>/dev/null || echo false)
        skills_learned=$(jq '.results.skills_learned' "$result_file" 2>/dev/null || echo 0)

        total_iterations=$((total_iterations + iterations))
        total_tokens=$((total_tokens + tokens))
        total_cost=$(echo "$total_cost + $cost" | bc)
        total_duration=$(echo "$total_duration + $duration" | bc)
        total_skills_learned=$((total_skills_learned + skills_learned))

        if [ "$success" = "true" ]; then
            successful=$((successful + 1))
        fi
    done

    # Calculate averages
    local avg_iterations=$(echo "scale=2; $total_iterations / $total_prompts" | bc)
    local avg_tokens=$(echo "scale=0; $total_tokens / $total_prompts" | bc)
    local avg_cost=$(echo "scale=4; $total_cost / $total_prompts" | bc)
    local avg_duration=$(echo "scale=2; $total_duration / $total_prompts" | bc)
    local success_rate=$(echo "scale=2; $successful * 100 / $total_prompts" | bc)

    # Create summary JSON
    cat > "$summary_file" << EOF
{
  "benchmark_run": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "learning_mode": "$LEARNING_MODE",
    "model": "$MODEL",
    "learning_model": "$LEARNING_MODEL",
    "prompts_run": $total_prompts
  },
  "aggregate_metrics": {
    "total_iterations": $total_iterations,
    "avg_iterations": $avg_iterations,
    "total_tokens": $total_tokens,
    "avg_tokens": $avg_tokens,
    "total_cost_usd": $total_cost,
    "avg_cost_usd": $avg_cost,
    "total_duration_seconds": $total_duration,
    "avg_duration_seconds": $avg_duration,
    "successful_prompts": $successful,
    "success_rate_percent": $success_rate,
    "skills_learned": $total_skills_learned
  }
}
EOF

    # Generate markdown report
    cat > "$report_file" << EOF
# ACE Learning Benchmark Report

**Run Date:** $(date)
**Learning Mode:** $LEARNING_MODE
**Model:** $MODEL
$([ "$LEARNING_MODE" = "enabled" ] && echo "**Learning Model:** $LEARNING_MODEL")

## Summary

| Metric | Value |
|--------|-------|
| Prompts Run | $total_prompts |
| Successful | $successful ($success_rate%) |
| Total Iterations | $total_iterations |
| Avg Iterations | $avg_iterations |
| Total Tokens | $total_tokens |
| Avg Tokens | $avg_tokens |
| Total Cost | \$$total_cost |
| Avg Cost | \$$avg_cost |
| Total Duration | ${total_duration}s |
| Avg Duration | ${avg_duration}s |
$([ "$LEARNING_MODE" = "enabled" ] && echo "| Skills Learned | $total_skills_learned |")

## Per-Prompt Results

| Prompt | Success | Iterations | Tokens | Duration | Skills Learned |
|--------|---------|------------|--------|----------|----------------|
EOF

    # Add per-prompt rows
    for result_file in "$OUTPUT_DIR"/*.json; do
        if [ "$(basename "$result_file")" = "summary.json" ]; then
            continue
        fi

        name=$(jq -r '.prompt_name' "$result_file")
        success=$(jq -r '.results.success' "$result_file")
        iters=$(jq -r '.results.iterations' "$result_file")
        toks=$(jq -r '.results.tokens' "$result_file")
        dur=$(jq -r '.results.duration_seconds' "$result_file")
        skills=$(jq -r '.results.skills_learned' "$result_file")

        success_icon=$([ "$success" = "true" ] && echo "Y" || echo "X")

        echo "| $name | $success_icon | $iters | $toks | ${dur}s | $skills |" >> "$report_file"
    done

    # Add configuration section
    cat >> "$report_file" << EOF

## Configuration

\`\`\`
MAX_ITERATIONS=$MAX_ITERATIONS
MODEL=$MODEL
LEARNING_MODEL=$LEARNING_MODEL
SKILLBOOK_PATH=$SKILLBOOK_PATH
CLEAR_SKILLBOOK=$CLEAR_SKILLBOOK
\`\`\`

## Output Files

- Summary JSON: \`$summary_file\`
- Individual results: \`$OUTPUT_DIR/*.json\`
EOF

    log_success "Report generated: $report_file"
    log_success "Summary JSON: $summary_file"
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_header "ACE Learning Benchmark Suite"

    # Validate arguments
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage
        exit 0
    fi

    if [ "$LEARNING_MODE" != "enabled" ] && [ "$LEARNING_MODE" != "disabled" ]; then
        log_error "Invalid mode: $LEARNING_MODE. Use 'enabled' or 'disabled'"
        usage
        exit 1
    fi

    log_info "Mode: $LEARNING_MODE"
    log_info "Model: $MODEL"
    [ "$LEARNING_MODE" = "enabled" ] && log_info "Learning Model: $LEARNING_MODEL"
    log_info "Max Iterations: $MAX_ITERATIONS"

    # Check dependencies
    check_dependencies

    # Setup
    setup_output_dir

    # Clear skillbook if requested
    if [ "$LEARNING_MODE" = "enabled" ]; then
        clear_skillbook
        log_info "Initial skills: $(count_skills)"
    fi

    # Get list of prompts
    local prompts=($(ls "$PROMPTS_DIR"/*.txt 2>/dev/null | sort))

    if [ ${#prompts[@]} -eq 0 ]; then
        log_error "No prompt files found in $PROMPTS_DIR"
        log_error "Create prompts as .txt files in that directory"
        exit 1
    fi

    log_info "Found ${#prompts[@]} benchmark prompts"
    echo ""

    # Run each prompt
    for prompt_file in "${prompts[@]}"; do
        run_prompt "$prompt_file"

        # Small delay between prompts to avoid rate limiting
        [ "$DRY_RUN" != "true" ] && sleep 2
    done

    # Generate aggregate report
    [ "$DRY_RUN" != "true" ] && generate_aggregate_report

    log_header "Benchmark Complete"
    log_info "Results in: $OUTPUT_DIR"

    if [ "$LEARNING_MODE" = "enabled" ]; then
        log_info "Final skills: $(count_skills)"
    fi

    # Hint for comparison
    if [ "$LEARNING_MODE" = "disabled" ]; then
        echo ""
        log_info "To run with learning enabled:"
        echo "  $0 enabled"
        echo ""
        log_info "To compare results:"
        echo "  # After running both, compare the summary.json files"
    else
        echo ""
        log_info "To run baseline (no learning):"
        echo "  CLEAR_SKILLBOOK=true $0 disabled"
    fi
}

main "$@"
