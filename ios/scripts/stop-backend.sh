#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PID_FILE="${SRCROOT:-.}/.ralph-backend-pid"

echo -e "${YELLOW}🛑 Stopping Ralph Backend${NC}"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Killing backend (PID: $PID)${NC}"
        kill -9 "$PID" 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${YELLOW}⚠ Backend not running (stale PID)${NC}"
    fi
    rm -f "$PID_FILE"
else
    echo -e "${YELLOW}⚠ No PID file found${NC}"
fi

# Also kill any process on port 8080
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Killing process on port 8080${NC}"
    PID=$(lsof -ti:8080)
    kill -9 $PID 2>/dev/null || true
fi

echo -e "${GREEN}✓ Cleanup complete${NC}"
