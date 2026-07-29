#!/usr/bin/env bash
# Launcher script for botyarajump on Linux / macOS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    echo "Starting botyarajump using .venv..."
    "$SCRIPT_DIR/.venv/bin/python" main.py
else
    echo "Starting botyarajump using system python3..."
    python3 main.py
fi
