<p align="center">
  <img src="assets/logo.png" alt="DuilioCode Studio" width="180">
</p>

<h1 align="center">DuilioCode Studio</h1>

<p align="center">
  <strong>Your local AI coding assistant. 100% offline. 100% private.</strong>
</p>

<p align="center">
  <a href="https://github.com/jfdroid/duilio-code-studio/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
  <a href="https://github.com/jfdroid/duilio-code-studio/stargazers">
    <img src="https://img.shields.io/github/stars/jfdroid/duilio-code-studio?style=social" alt="Stars">
  </a>
  <a href="https://github.com/jfdroid/duilio-code-studio/issues">
    <img src="https://img.shields.io/github/issues/jfdroid/duilio-code-studio" alt="Issues">
  </a>
  <img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/ollama-required-orange.svg" alt="Ollama">
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Docs</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

Like **Cursor AI** or **GitHub Copilot**, but runs entirely on your machine with no cloud dependencies.

## ✨ Features

- 💻 **100% Local & Offline** - No internet required, your code never leaves your machine
- 🔒 **Complete Privacy** - All processing happens locally
- 📁 **Full File System Access** - Create, edit, delete files and folders
- 🗂️ **Workspace Management** - Open projects like VS Code/Cursor
- ⚡ **Fast** - Optimized for Apple Silicon and modern hardware
- 🎨 **Modern IDE Interface** - Familiar VS Code-style layout

## 🏃 Quick Start

```bash
# Clone the repository
git clone https://github.com/jfdroid/duilio-code-studio.git
cd duilio-code-studio

# Install Ollama (if not installed)
brew install ollama

# Pull a code model
ollama pull qwen2.5-coder:7b

# Start DuilioCode
./start.sh
```

Open: **http://127.0.0.1:8080**

## 🖥️ Interface Overview

DuilioCode Studio provides a familiar IDE experience:

```
┌─────────────────────────────────────────────────────────────┐
│ 📁 Explorer │        Editor / Welcome        │   💬 Chat   │
│             │                                │             │
│ 📂 Project  │  // Your code here            │  Ask me to: │
│ ├── src/    │                                │  - Create   │
│ │   └── ... │                                │    files    │
│ ├── tests/  │                                │  - Generate │
│ └── ...     │                                │    projects │
│             │                                │  - Review   │
│             │                                │    code     │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Opening a Workspace

1. Click **"Open Folder"** or press `Ctrl+O`
2. Enter a path:
   - Use `~` for your home folder: `~/projects/myapp`
   - Use absolute paths: `/home/user/projects`
   - Use relative paths: `./my-project`
3. Your project files appear in the Explorer

## 🤖 What DuilioCode Can Do

### File Operations
- ✅ **Create** new files and folders
- ✅ **Edit** existing code with syntax highlighting
- ✅ **Delete** files and folders
- ✅ **Rename** and move files

### AI Assistance
- ✅ Generate entire project structures
- ✅ Write functions, classes, and modules
- ✅ Code review and suggestions
- ✅ Debug and fix errors
- ✅ Explain complex code
- ✅ Refactor and optimize
- ✅ Create tests and documentation

### Example Prompts
```
"Create a Python Flask REST API with user authentication"
"Generate a React component with TypeScript and tests"
"Write a bash script to backup my database daily"
"Explain this code and suggest improvements"
"Create a Dockerfile for this Node.js application"
```

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open folder |
| `Ctrl+S` | Save file |
| `Ctrl+B` | Toggle explorer |
| `Ctrl+Enter` | Send message |

## 📦 Available Models

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| qwen2.5-coder:7b | 4.7GB | ⭐⭐⭐ | ⚡⚡⚡⚡ |
| qwen2.5-coder:14b | 9GB | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| qwen2.5-coder:32b | 19GB | ⭐⭐⭐⭐⭐ | ⚡⚡ |

```bash
# Install recommended model
ollama pull qwen2.5-coder:14b

# Or fast model for quick tasks
ollama pull qwen2.5-coder:7b
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/health` | GET | Server status |
| `/api/workspace` | GET/POST | Manage workspace |
| `/api/files` | GET | List directory |
| `/api/files/read` | GET | Read file |
| `/api/files/write` | POST | Save file |
| `/api/files/create` | POST | Create file/folder |
| `/api/files/delete` | POST | Delete file/folder |
| `/api/files/rename` | POST | Rename/move file |
| `/api/code` | POST | AI code generation |
| `/api/chat` | POST | Chat with history |
| `/api/models` | GET | List models |

## 📁 Project Structure (Clean Architecture)

```
duilio-code-studio/
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── dependencies.py  # Dependency injection
│   │   └── routes/          # API endpoints
│   │       ├── health.py    # Health checks
│   │       ├── chat.py      # AI generation
│   │       ├── files.py     # File operations
│   │       ├── workspace.py # Project management
│   │       └── models.py    # Model management
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── exceptions.py    # Custom exceptions
│   ├── services/
│   │   ├── ollama_service.py    # AI/LLM operations
│   │   ├── file_service.py      # File system operations
│   │   └── workspace_service.py # Workspace management
│   └── schemas/
│       ├── requests.py      # Request models
│       └── responses.py     # Response models
├── web/
│   ├── templates/
│   │   └── index.html       # IDE interface
│   └── static/              # CSS, JS assets
├── start.sh                 # Startup script
└── requirements.txt         # Dependencies
```

### Architecture Principles

- **SOLID Principles** - Clean separation of concerns
- **Single Responsibility** - Each module has one job
- **Dependency Injection** - Services injected via FastAPI
- **Domain-Driven** - Business logic in services layer

## 🆚 Comparison

| Feature | DuilioCode | Cursor AI | GitHub Copilot |
|---------|-----------|-----------|----------------|
| **Offline** | ✅ Yes | ❌ No | ❌ No |
| **Privacy** | ✅ 100% Local | ☁️ Cloud | ☁️ Cloud |
| **File Editing** | ✅ Full access | ✅ Full access | ⚠️ Limited |
| **Cost** | 💚 Free | 💰 Paid | 💰 Paid |
| **Project Creation** | ✅ Yes | ✅ Yes | ⚠️ Limited |

## 🤝 Contributing

We love contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Steps

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## 🔒 Security

For security issues, please see [SECURITY.md](SECURITY.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Qwen2.5-Coder](https://github.com/QwenLM/Qwen2.5-Coder) - Amazing code model
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

## ⭐ Star History

If you find DuilioCode useful, please consider giving it a star!

---

<p align="center">
  <strong>DuilioCode Studio</strong> - Your offline AI coding companion! 🚀
</p>

<p align="center">
  Made with ❤️ for developers who value privacy
</p>

<p align="center">
  <a href="https://github.com/jfdroid/duilio-code-studio">GitHub</a> •
  <a href="https://github.com/jfdroid/duilio-code-studio/issues">Report Bug</a> •
  <a href="https://github.com/jfdroid/duilio-code-studio/issues">Request Feature</a>
</p>
