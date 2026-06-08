#!/bin/bash
# Full demo pipeline — run this script to produce demo/assets/demo_final.mp4
# Prerequisites: API + Streamlit must be running (see README.md Quick Start)

set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "=================================================="
echo " GenAI Document Assistant — Demo Recording"
echo "=================================================="
echo ""
echo "Prerequisites:"
echo "  1. Ollama running:   open /Applications/Ollama.app"
echo "  2. API running:      python main.py  (in another terminal)"
echo "  3. UI running:       streamlit run ui/streamlit_app.py  (in another terminal)"
echo ""
read -p "Press ENTER when all three are running..."

echo ""
echo "Step 1/3: Generating narration audio (Edge TTS)..."
python demo/narration.py

echo ""
echo "Step 2/3: Recording browser demo (Playwright)..."
echo "  (A browser window will open — do not click anything)"
python demo/playwright_demo.py

echo ""
echo "Step 3/3: Combining video + narration (ffmpeg)..."
python demo/combine_demo.py

echo ""
echo "=================================================="
echo " Demo complete!"
echo " Output: demo/assets/demo_final.mp4"
echo "=================================================="
