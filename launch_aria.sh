#!/bin/bash
# Launch Aria Assistant (Hybrid Mode: llama.cpp + OpenClaw)
# This script starts the full Aria stack:
#   1. Verifies the llama.cpp Docker container (LLM on GPU)
#   2. Starts the OpenClaw Gateway (agent layer)
#   3. Launches the Aria pipeline (STT/TTS/Vision/Web UI)

cd "$(dirname "$0")"

export NO_PROXY="localhost,127.0.0.1,0.0.0.0,::1"
export no_proxy="localhost,127.0.0.1,0.0.0.0,::1"

# ── Cleanup Handler on Exit ───────────────────────────────────────
cleanup() {
    echo ""
    echo "🧹 Shutting down Aria Assistant & releasing all memory and ports..."
    pkill -f "openclaw gateway run" 2>/dev/null || true
    fuser -k -9 8090/tcp 2>/dev/null || true
    fuser -k -9 19000/tcp 2>/dev/null || true
    echo "✅ Ports 8090 & 19000 released. All RAM and GPU memory freed!"
}
trap cleanup INT TERM EXIT

# ── Load Node.js 24 via nvm or fnm (required for OpenClaw) ─────────────
export PATH="/run/user/1000/fnm_multishells/12806_1784650791471/bin:$HOME/.local/share/fnm:$PATH"
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
    echo "   ⚠️  LLM server not detected on port 8080. Auto-starting server..."
    CTX=2048 CPU_ONLY=1 ./run_llama_cpp.sh ./models/Cosmos-Reason2-2B-Q4_K_M.gguf
fi

# ── Step 2: Start OpenClaw Gateway ──────────────────────────────
echo ""
echo "🦅 Starting OpenClaw Gateway (port 19000)..."
pkill -f "openclaw gateway run" 2>/dev/null || true
sleep 1
export NODE_COMPILE_CACHE="$HOME/.npm/.cache/nodejs-compile-cache"
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
(sleep 4 && (xdg-open "http://localhost:8090" || google-chrome "http://localhost:8090" || firefox "http://localhost:8090")) >/dev/null 2>&1 &
./start.sh
