#!/bin/bash

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.service_pids"

echo "🛑 Stopping all services..."

# Stop by PID file
if [ -f "$PID_FILE" ]; then
    echo "Stopping services from $PID_FILE..."
    while read pid; do
        if [ -n "$pid" ] && ps -p $pid > /dev/null 2>&1; then
            echo "Killing PID: $pid"
            kill $pid 2>/dev/null
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# Stop by process name
echo "Cleaning up any remaining processes..."
pkill -f "python3 -m http.server" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
pkill -f "llama-server" 2>/dev/null
pkill -f "caddy" 2>/dev/null

echo "✅ All services stopped"