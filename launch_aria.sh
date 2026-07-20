#!/bin/bash
# Launch Aria Assistant
cd /home/filippos/reachy-mini-jetson-assistant

echo "=========================================="
echo "🤖 Starting Aria Assistant Backend..."
echo "=========================================="

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -Eq "^assistant-llm$"; then
    echo "LLM Container not found! Creating it..."
    NGL=999 CTX=1024 ./run_llama_cpp.sh models/Cosmos-Reason2-2B-Q4_K_M.gguf
else
    # Start LLM container if it is stopped
    if [ "$(docker inspect -f '{{.State.Running}}' assistant-llm 2>/dev/null)" != "true" ]; then
        echo "Starting existing LLM container..."
        docker start assistant-llm
    else
        echo "LLM container is already running."
    fi
fi

echo ""
echo "🚀 Starting Aria Assistant Pipeline..."
echo "Press Ctrl+C to stop."
echo "=========================================="
./start.sh
