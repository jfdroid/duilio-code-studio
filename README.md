# 🚀 DuilioCode Studio

Local and offline programming assistant, powered by **Qwen2.5-Coder**.

## ✨ Features

- 💻 **100% Local** - Works without internet
- 🔒 **Private** - Your code never leaves your computer
- ⚡ **Fast** - Optimized for Apple Silicon
- 🎨 **Modern Interface** - VS Code/Cursor-style UI
- 📁 **File Editing** - Read and write files directly

## 🏃 Quick Start

```bash
cd /Users/jeffersonsilva/Desen/duilio-code-studio
./start.sh
```

Access: **http://127.0.0.1:8080**

## 📦 Available Models

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| qwen2.5-coder:7b | 4.7GB | ⭐⭐⭐ | ⚡⚡⚡⚡ |
| qwen2.5-coder:14b | 9GB | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| qwen2.5-coder:32b | 19GB | ⭐⭐⭐⭐⭐ | ⚡⚡ |

### Install Model

```bash
# Recommended (best cost-benefit)
ollama pull qwen2.5-coder:14b

# Fast (for simple tasks)
ollama pull qwen2.5-coder:7b

# Advanced (maximum quality)
ollama pull qwen2.5-coder:32b
```

## 🎯 What it does well

- ✅ Generate code in multiple languages
- ✅ Explain programming concepts
- ✅ Code review and suggestions
- ✅ Debug and error fixing
- ✅ Code refactoring
- ✅ Automatic documentation
- ✅ Unit tests
- ✅ Architecture and design patterns

## ⚠️ Limitations (vs Claude 4.5 Opus)

| Aspect | DuilioCode Local | Claude 4.5 Opus |
|--------|------------------|-----------------|
| Complex reasoning | Medium | Excellent |
| Long context | ~8K tokens | ~200K tokens |
| Current knowledge | Up to training date | More recent |
| Speed | Hardware dependent | Fast |
| Cost | 💚 FREE | 💰 Per token |
| Privacy | 💚 100% Local | ☁️ Cloud-based |

## 📁 Structure

```
duilio-code-studio/
├── src/
│   └── api/
│       └── main.py      # FastAPI API
├── web/
│   └── templates/
│       └── index.html   # Interface
├── start.sh             # Startup script
└── requirements.txt     # Dependencies
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/health` | GET | Server status |
| `/api/code` | POST | Generate code |
| `/api/chat` | POST | Chat with history |
| `/api/models` | GET | List models |
| `/api/files` | GET | List files |
| `/api/files/read` | GET | Read file |
| `/api/files/write` | POST | Save file |

## 💡 Usage Tips

### Effective prompts:

```
# Generate function
"Create a Python function that validates CPF"

# Explain code
"Explain this code line by line: [paste code]"

# Code review
"Review this code and suggest improvements: [paste code]"

# Architecture
"How to implement Repository Pattern in Kotlin with Clean Architecture?"
```

## 🆚 Comparison with Other Tools

| Tool | Type | Cost | Offline |
|------|------|------|---------|
| **DuilioCode** | Local | Free | ✅ |
| Cursor AI | Cloud IDE | Paid | ❌ |
| GitHub Copilot | Extension | Paid | ❌ |
| ChatGPT | Web | Paid | ❌ |
| Claude | Web | Paid | ❌ |

---

**DuilioCode Studio** - Your offline Cursor! 🚀
