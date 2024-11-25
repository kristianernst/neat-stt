#!/bin/bash

# Get the absolute path to the project root directory
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# File where PIDs are stored
PID_FILE="$ROOT_DIR/service_pids.txt"

if [ ! -f "$PID_FILE" ]; then
    echo "PID file not found. No services to stop."
    exit 1
fi

while IFS=: read -r name pid
do
    if kill -0 "$pid" >/dev/null 2>&1; then
        echo "Stopping $name with PID $pid..."
        kill "$pid"
        echo "$name stopped."
    else
        echo "$name with PID $pid is not running."
    fi
done < "$PID_FILE"

# Remove the PID file
rm "$PID_FILE"
echo "All services stopped."
