# Ollama - Local AI Engine

## What is Ollama?

Ollama is a server that runs language models (LLMs) **directly on your computer**. It's like having ChatGPT running locally, without needing internet or sending data to external servers.

## Why Do We Use Ollama?

### ✅ Advantages
- **Privacy**: Your code never leaves your computer
- **Speed**: Doesn't depend on internet connection
- **Control**: You choose which model to use
- **Free**: No API costs
- **Offline**: Works without internet

### ❌ Disadvantages
- **Resources**: Needs sufficient RAM (large models)
- **Speed**: May be slower than cloud APIs (depends on hardware)

## How Does It Work?

```
DuilioCode → HTTP Request → Ollama Server → Qwen Model → Response → DuilioCode
```

### Detailed Flow

1. **DuilioCode sends prompt** to Ollama via HTTP
2. **Ollama processes** using installed model (Qwen2.5-Coder)
3. **Model generates response** based on prompt
4. **Ollama returns** response to DuilioCode
5. **DuilioCode processes** response and executes actions if needed

## Installation

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download from: https://ollama.com

## Starting the Server

### Automatic
The `start.sh` script checks and starts automatically.

### Manual
```bash
ollama serve
```

The server runs on `http://localhost:11434`

## Available Models

### Qwen2.5-Coder (Recommended)
```bash
# 14B version (smarter, slower)
ollama pull qwen2.5-coder:14b

# 7B version (faster, less accurate)
ollama pull qwen2.5-coder:7b
```

### Other Models
```bash
# List installed models
ollama list

# Download other models
ollama pull llama2
ollama pull codellama
```

## Integration in DuilioCode

### Code: `src/services/ollama_service.py`

```python
class OllamaService:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def generate(self, prompt, model, system_prompt=None):
        # Sends request to Ollama
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt
            }
        )
        return response.json()
```

### How It's Used

1. **Chat Handler** calls `ollama.generate()`
2. **Ollama Service** makes HTTP request
3. **Ollama Server** processes and returns
4. **Response** is processed and displayed

## Configuration

### Environment Variables
```bash
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:14b
```

### In Code
```python
# src/core/config.py
OLLAMA_HOST: str = "http://localhost:11434"
DEFAULT_MODEL: str = "qwen2.5-coder:14b"
```

## Health Check

DuilioCode checks if Ollama is running:

```python
async def health_check(self):
    try:
        response = await self.client.get(f"{self.base_url}/api/tags")
        return {"status": "running", "models": response.json()}
    except:
        return {"status": "offline"}
```

## Streaming (Real-Time Responses)

Ollama supports streaming - responses appear word by word:

```python
async def generate_stream(self, prompt, model):
    async with self.client.stream(
        "POST",
        f"{self.base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": True}
    ) as response:
        async for line in response.aiter_lines():
            if line:
                yield json.loads(line)
```

## Troubleshooting

### Ollama won't start
```bash
# Verify installation
which ollama

# Check logs
ollama serve
```

### Model not found
```bash
# List models
ollama list

# Download model
ollama pull qwen2.5-coder:14b
```

### Port occupied
```bash
# Check process
lsof -i :11434

# Kill process
kill -9 <PID>
```

## Next Steps

- [Qwen2.5-Coder - Language Model](08-qwen.md)
- [How Chat Works](11-chat-functionality.md)
