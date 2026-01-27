# Step-by-Step Installation

## Prerequisites

- **Operating System**: macOS, Linux, or Windows
- **Python**: 3.9 or higher
- **RAM**: Minimum 8GB (16GB recommended for 14B model)
- **Disk Space**: ~10GB (for model and dependencies)

## Step 1: Install Ollama

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
1. Download installer from: https://ollama.com
2. Run the installer
3. Follow instructions

### Verify Installation
```bash
ollama --version
```

## Step 2: Start Ollama

### Start Server
```bash
ollama serve
```

The server runs on `http://localhost:11434`

### Verify It's Running
```bash
curl http://localhost:11434/api/tags
```

If it returns JSON, it's working!

## Step 3: Download Qwen2.5-Coder Model

### Option 1: 14B Model (Recommended - Smarter)
```bash
ollama pull qwen2.5-coder:14b
```

**Requirements**: 16GB+ RAM

### Option 2: 7B Model (Faster)
```bash
ollama pull qwen2.5-coder:7b
```

**Requirements**: 8GB+ RAM

### Verify Model
```bash
ollama list
```

Should show `qwen2.5-coder:14b` or `qwen2.5-coder:7b`

## Step 4: Clone Repository

```bash
git clone <repository-url>
cd duilio-code-studio
```

## Step 5: Create Virtual Environment

### Create Virtual Environment
```bash
python3 -m venv venv
```

### Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` at the beginning of the prompt.

## Step 6: Install Dependencies

### Update pip
```bash
pip install --upgrade pip
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- FastAPI
- SQLAlchemy
- Alembic
- diskcache
- And all other dependencies

### Verify Installation
```bash
python3 -c "import fastapi; import sqlalchemy; print('✅ Dependencies OK')"
```

## Step 7: Configure Environment (Optional)

### Create .env file
```bash
cp .env.example .env  # If exists
# Or create manually
```

### Edit .env
```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:14b

# Database
DATABASE_URL=sqlite:///./data/duiliocode.db

# Server
HOST=127.0.0.1
PORT=8080
```

## Step 8: Initialize Database

### Automatic (Recommended)
The database is created automatically on first run.

### Manual (Optional)
```bash
cd src
python3 -c "from core.database import init_database; init_database()"
```

## Step 9: Start Server

### Using Script (Recommended)
```bash
./start.sh
```

### Manually
```bash
cd src
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8080 --reload
```

## Step 10: Verify Functionality

### 1. Open in Browser
```
http://127.0.0.1:8080
```

### 2. Verify Health Check
```bash
curl http://127.0.0.1:8080/health
```

Should return:
```json
{"status": "ok", "service": "DuilioCode Studio"}
```

### 3. Verify Ollama
```bash
curl http://127.0.0.1:8080/health/ollama
```

### 4. Test Chat
1. Open web interface
2. Select a model
3. Type a message
4. Verify you receive a response

## Troubleshooting

### Error: "Ollama not found"
```bash
# Verify installation
which ollama

# Reinstall if necessary
brew install ollama  # macOS
```

### Error: "Model not found"
```bash
# List models
ollama list

# Download model
ollama pull qwen2.5-coder:14b
```

### Error: "Port 8080 already in use"
```bash
# Find process
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Kill process or change port
# Edit .env: PORT=8081
```

### Error: "Module not found"
```bash
# Verify venv is active
which python3  # Should point to venv/bin/python3

# Reinstall dependencies
pip install -r requirements.txt
```

### Error: "Database locked"
```bash
# Close other connections
# Or delete and recreate
rm data/duiliocode.db
# Restart server
```

## Final Verification

### Checklist
- [ ] Ollama installed and running
- [ ] Qwen2.5-Coder model downloaded
- [ ] Python 3.9+ installed
- [ ] Virtual environment created and active
- [ ] Dependencies installed
- [ ] Server started without errors
- [ ] Web interface accessible
- [ ] Health check returns OK
- [ ] Chat works

## Next Steps

- [First Steps](03-first-steps.md)
- [System Architecture](04-architecture.md)
