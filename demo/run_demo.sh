#!/bin/bash
# Full demo pipeline — produces demo/assets/demo_final.mp4
# Run from the project root: bash demo/run_demo.sh

set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "=================================================="
echo " GenAI Document Assistant — Demo Recording"
echo "=================================================="
echo ""
echo "Prerequisites:"
echo "  • Ollama running with llama3.2 + nomic-embed-text"
echo "    open /Applications/Ollama.app"
echo ""
read -p "Press ENTER when Ollama is running..."

# Step 0: Stop any running servers + clean data BEFORE API starts
echo ""
echo "Stopping any running servers..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true
sleep 2

echo "Cleaning data directories..."
rm -rf data/chroma_db data/uploads
mkdir -p data/chroma_db data/uploads
echo "  ✓ ChromaDB and uploads cleared"

# Step 1: Start API (clean state)
echo ""
echo "Starting FastAPI..."
python main.py &>/tmp/demo_api.log &
sleep 4
if ! curl -s http://localhost:8000/health | grep -q '"status"'; then
  echo "❌ API failed to start. Check /tmp/demo_api.log"
  exit 1
fi
echo "  ✓ API ready"

# Step 2: Start Streamlit
echo "Starting Streamlit..."
streamlit run ui/streamlit_app.py --server.headless true &>/tmp/demo_ui.log &
sleep 6
echo "  ✓ Streamlit ready"

# Step 3: Generate narration audio
echo ""
echo "Step 1/3: Generating narration (Edge TTS)..."
python demo/narration.py

# Step 4: Record browser demo
echo ""
echo "Step 2/3: Recording browser demo (Playwright)..."
echo "  (A browser window will open — do not interact with it)"
python demo/playwright_demo.py

# Step 5: Combine video + audio
echo ""
echo "Step 3/3: Combining video + narration (ffmpeg)..."
python demo/combine_demo.py

# Stop servers
pkill -f "python main.py" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true

echo ""
echo "=================================================="
echo " Done! → demo/assets/demo_final.mp4"
echo "=================================================="
