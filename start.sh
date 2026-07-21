#!/bin/bash
# Wrapper to start any python script inside the venv with proper LD_LIBRARY_PATH

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Error: Virtual environment 'venv' not found."
    exit 1
fi

source venv/bin/activate
export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH
export NO_PROXY="localhost,127.0.0.1,0.0.0.0,::1"
export no_proxy="localhost,127.0.0.1,0.0.0.0,::1"

# Run the provided arguments as a command, default to assistant.py
if [ $# -eq 0 ]; then
    python assistant.py
else
    python "$@"
fi
