#!/bin/bash
# Launch Aria Assistant (Hybrid Mode: llama.cpp + OpenClaw)
# This script starts the full Aria stack:
#   1. Verifies the llama.cpp Docker container (LLM on GPU)
#   2. Starts the OpenClaw Gateway (agent layer)
#   3. Launches the Aria pipeline (STT/TTS/Vision/Web UI)

cd /home/filippos/reachy-mini-jetson-assistant

# ── Load Node.js 24 via nvm (required for OpenClaw) ─────────────
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 24 --silent 2>/dev/null || true

echo "=========================================="
echo "🤖 Starting Aria Hybrid Assistant..."
echo "=========================================="

# ── Step 1: Verify llama.cpp LLM server ─────────────────────────
echo "🧠 Checking llama.cpp server (port 8080)..."
if curl -s --max-time 2 http://127.0.0.1:8080/health > /dev/null 2>&1; then
    echo "   ✅ LLM server is running on port 8080."
elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^assistant-llm$"; then
    echo "   ✅ LLM container 'assistant-llm' is running (warming up)."
else
    echo "   ⚠️  LLM server not detected on port 8080."
    echo "   ➡️  Start it with: ./run_llama_cpp.sh ./models/Cosmos-Reason2-2B-Q4_K_M.gguf"
    echo "   Continuing without confirming LLM is ready..."
fi

# ── Step 2: Start OpenClaw Gateway ──────────────────────────────
echo ""
echo "🦅 Starting OpenClaw Gateway (port 19000)..."
pkill -f "openclaw gateway run" 2>/dev/null || true
sleep 1
nohup openclaw gateway run > /tmp/openclaw-gateway.log 2>&1 &
OC_PID=$!
sleep 3

if kill -0 "$OC_PID" 2>/dev/null; then
    echo "   ✅ OpenClaw Gateway started (PID: $OC_PID)"
    echo "   📋 Logs: tail -f /tmp/openclaw-gateway.log"
else
    echo "   ⚠️  OpenClaw Gateway failed to start. Check: cat /tmp/openclaw-gateway.log"
fi

echo ""
echo "🚀 Starting Aria Assistant Pipeline..."
echo "   Web UI: http://0.0.0.0:8090"
echo "   OpenClaw: http://0.0.0.0:19000"
echo "   Press Ctrl+C to stop."
echo "=========================================="
./start.sh
