# 🎨 DuilioAI Studio

**100% Local AI** for image editing, chat and code generation - optimized for Apple Silicon.

## Features

- **🖼️ Image Generation** - Generate images from text (txt2img)
- **✏️ Image Editing** - Edit entire images with prompts (img2img)
- **🖌️ Inpainting** - Edit specific areas using mask
- **💬 Chat** - Conversational AI with Ollama models
- **💻 Code** - Code generation with Qwen2.5-Coder

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4) or NVIDIA GPU
- Python 3.9+
- [Ollama](https://ollama.ai) for chat/code
- 8GB+ RAM recommended

## Quick Start

```bash
# 1. Clone and enter directory
cd duilio-ai-studio

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Ollama models
ollama pull llama3.2
ollama pull qwen2.5-coder:7b

# 5. Start server
python -m src.api.main
```

Then open http://localhost:8000

## Technical Details

### Apple Silicon Optimization

DuilioAI is specifically optimized for Apple Silicon:

- **MPS (Metal Performance Shaders)** - Uses GPU acceleration
- **float32 for stability** - Avoids black image issues with float16
- **Attention slicing** - Reduces memory usage
- **VAE slicing** - Processes VAE in chunks
- **CPU generator** - Proper seed handling for MPS

### Architecture (SOLID)

```
duilio-ai-studio/
├── config/
│   └── settings.py          # Configuration
├── src/
│   ├── api/
│   │   └── main.py          # FastAPI server
│   ├── chat/
│   │   └── ollama_client.py # Chat with Ollama
│   └── image_gen/
│       └── sd_client.py     # Image generation (SOLID)
└── web/
    ├── templates/           # HTML
    └── static/              # CSS/JS
```

### Models Used

| Feature | Model |
|---------|-------|
| Text-to-Image | stable-diffusion-v1-5 |
| Image-to-Image | stable-diffusion-v1-5 |
| Inpainting | runwayml/stable-diffusion-inpainting |
| Chat | llama3.2 |
| Code | qwen2.5-coder:7b |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Chat with LLM |
| `/api/code` | POST | Generate code |
| `/api/image/generate` | POST | Generate image |
| `/api/image/edit` | POST | Edit image |
| `/api/image/inpaint` | POST | Inpaint image |
| `/health` | GET | Health check |
| `/docs` | GET | API documentation |

## Troubleshooting

### Black images on Apple Silicon

This is fixed in DuilioAI by:
1. Using `float32` instead of `float16`
2. Creating generator on CPU instead of MPS
3. Disabling callbacks that cause issues

### Out of memory

- Reduce image size to 384x384
- Use "Quick Mode" for previews
- Restart server to clear cache

### Models not loading

```bash
# Check Ollama is running
ollama list

# Pull required models
ollama pull llama3.2
ollama pull qwen2.5-coder:7b
```

## License

MIT - Use freely for any purpose.
