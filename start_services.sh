#!/bin/bash

# Get the absolute path to the project root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"

# File to store PIDs
PID_FILE="$ROOT_DIR/service_pids.txt"

# Ensure the PID file is empty
> "$PID_FILE"

# Function to start a service in the background
start_service() {
    local name="$1"
    local dir="$2"
    local cmd="$3"
    echo "Starting $name..."
    (
        cd "$dir" || exit
        # Redirect both stdout and stderr to log files
        mkdir -p "$ROOT_DIR/logs"
        eval "$cmd" &> "$ROOT_DIR/logs/$name.log" &
        PID=$!
        echo "$name:$PID" >> "$PID_FILE"
        echo "$name started with PID $PID"
    )
}

# Start Frontend and Backend services
start_service "Frontend" "$FRONTEND_DIR" "npm run dev"
start_service "Backend" "$BACKEND_DIR" "uvicorn src.main:app --reload"

echo "All services started."
