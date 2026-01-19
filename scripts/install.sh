#!/bin/bash
# Local AI Studio - Installation Script
# Works on macOS (Apple Silicon) and Linux

set -e

echo "🚀 Local AI Studio - Installation"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_DIR"

# Check Python version
echo "📦 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p data models logs
echo -e "${GREEN}✓ Directories created${NC}"

# Check/Install Ollama
echo ""
echo "🤖 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
else
    echo -e "${YELLOW}⚠ Ollama not found${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing Ollama via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install ollama
            echo -e "${GREEN}✓ Ollama installed${NC}"
        else
            echo -e "${YELLOW}Please install Ollama manually: https://ollama.ai${NC}"
        fi
    else
        echo "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        echo -e "${GREEN}✓ Ollama installed${NC}"
    fi
fi

# Download models
echo ""
echo "🧠 Downloading AI models..."
echo "This may take a while on first run..."

# Start Ollama service if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &>/dev/null &
    sleep 3
fi

# Pull models
echo ""
echo "Pulling llama3.2 (main chat model)..."
ollama pull llama3.2 || echo -e "${YELLOW}⚠ Could not pull llama3.2, you can do this later${NC}"

echo ""
echo "Pulling codellama (code generation)..."
ollama pull codellama || echo -e "${YELLOW}⚠ Could not pull codellama, you can do this later${NC}"

echo ""
echo -e "${YELLOW}💡 Tip: For image analysis, also run: ollama pull llava${NC}"

# Done
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "To start the server:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python -m src.api.main"
echo ""
echo "Then open: http://localhost:8000"
echo ""
echo "Or use the CLI:"
echo "  python -m src.chat.cli"
echo "=========================================="
