#!/bin/bash
# DuilioCode Studio - Startup Script

cd "$(dirname "$0")"

echo "🚀 DuilioCode Studio"
echo "===================="
echo ""

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found!"
    echo "   Install with: brew install ollama"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Starting..."
    ollama serve &
    sleep 3
fi

# Check model
echo "📦 Checking Qwen2.5-Coder model..."
if ! ollama list | grep -q "qwen2.5-coder:14b"; then
    echo "⏳ Model not found. To download:"
    echo "   ollama pull qwen2.5-coder:14b"
    echo ""
    echo "   Or use the 7B model (faster):"
    echo "   ollama pull qwen2.5-coder:7b"
    echo ""
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install fastapi uvicorn httpx pydantic pydantic-settings python-multipart pygments
fi

echo ""
echo "🌐 Interface: http://127.0.0.1:8080"
echo "📖 API Docs:  http://127.0.0.1:8080/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server from src directory (Clean Architecture)
cd src
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8080 --reload
