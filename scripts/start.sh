#!/bin/bash
# Local AI Studio - Quick Start Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🤖 Starting Ollama service..."
    ollama serve &>/dev/null &
    sleep 2
fi

# Start server
echo "🚀 Starting Local AI Studio..."
echo "   Web UI: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""

python -m src.api.main
