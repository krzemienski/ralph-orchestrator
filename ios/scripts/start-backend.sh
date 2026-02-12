#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Add Rust/Cargo to PATH (common locations)
export PATH="$HOME/.cargo/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

# Configuration
BACKEND_DIR="../"
PID_FILE="${SRCROOT}/.ralph-backend-pid"
PORT=8080
MAX_WAIT=10

# Verify cargo is available
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}✗ Cargo not found in PATH${NC}"
    echo -e "${YELLOW}⚠ Install Rust: https://rustup.rs/${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Ralph Backend Auto-Start${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to check if backend is running
check_backend_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend already running (PID: $PID)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Stale PID file found, cleaning up${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to check if port is in use
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to kill existing backend
kill_existing_backend() {
    echo -e "${YELLOW}⚠ Killing existing backend on port $PORT${NC}"
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
}

# Check if backend is already running
if check_backend_running; then
    # Verify it's responsive
    if curl -s -f http://127.0.0.1:$PORT/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Backend not responsive, restarting${NC}"
        PID=$(cat "$PID_FILE")
        kill -9 "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
fi

# Check if port is in use by another process
if check_port; then
    kill_existing_backend
fi

# Navigate to backend directory
cd "$BACKEND_DIR"

echo -e "${GREEN}📦 Building ralph-mobile-server...${NC}"
if ! cargo build --bin ralph-mobile-server --release 2>&1 | tail -5; then
    echo -e "${RED}✗ Failed to build backend${NC}"
    exit 1
fi

echo -e "${GREEN}🔧 Starting ralph-mobile-server...${NC}"

# Start backend in background and capture output
LOG_FILE="${SRCROOT}/.ralph-backend.log"
cargo run --bin ralph-mobile-server --release > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

# Save PID
echo "$BACKEND_PID" > "$PID_FILE"
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
for i in $(seq 1 $MAX_WAIT); do
    if curl -s -f http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}✓ Backend ready at http://127.0.0.1:$PORT${NC}"
        echo -e "${GREEN}✓ Configure iOS app with: http://127.0.0.1:$PORT${NC}"
        exit 0
    fi
    sleep 1
done

echo -e "${RED}✗ Backend failed to start within ${MAX_WAIT}s${NC}"
echo -e "${RED}✗ Check logs at: $LOG_FILE${NC}"
tail -20 "$LOG_FILE"
kill -9 "$BACKEND_PID" 2>/dev/null || true
rm -f "$PID_FILE"
exit 1
