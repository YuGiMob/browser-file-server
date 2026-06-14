#!/bin/bash
# Browser File Server - Launch Script
# This script starts the file server in the background

# Configuration
ROOT_DIR="${1:-$HOME}"
PORT="${2:-8080}"
LOG_FILE="${3:-$HOME/fileserver.log}"
PID_FILE="$HOME/.fileserver.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}File server is already running (PID: $PID)${NC}"
        echo "To stop it, run: kill $PID"
        exit 1
    else
        # Remove stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is required but not installed${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo -e "${RED}Error: Python 3.7 or higher is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Check if YAML module is available (optional)
if python3 -c "import yaml" 2>/dev/null; then
    YAML_SUPPORT="yes"
else
    YAML_SUPPORT="no"
    echo -e "${YELLOW}Note: PyYAML not installed. Using simple config parser.${NC}"
    echo "Install with: pip3 install pyyaml"
fi

# Start the server
echo -e "${GREEN}Starting Browser File Server...${NC}"
echo "  Root: $ROOT_DIR"
echo "  Port: $PORT"
echo "  Log:  $LOG_FILE"
echo ""

# Run the server
cd "$SCRIPT_DIR"
nohup python3 -m server "$ROOT_DIR" "$PORT" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo "$SERVER_PID" > "$PID_FILE"

# Wait a moment to check if server started successfully
sleep 1

if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}File server started successfully!${NC}"
    echo "  PID:  $SERVER_PID"
    echo "  URL:  http://localhost:$PORT"
    echo ""
    echo "To stop the server:"
    echo "  kill $SERVER_PID"
    echo ""
    echo "To view logs:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "To run in foreground (for debugging):"
    echo "  cd $SCRIPT_DIR && python3 -m server $ROOT_DIR $PORT"
else
    echo -e "${RED}Error: Failed to start file server${NC}"
    echo "Check the log file for details: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
