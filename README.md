# 🚀 DuilioCode Studio

Your **local and offline** AI coding assistant with full file system access. Like Cursor, but 100% private.

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

## 📁 Project Structure

```
duilio-code-studio/
├── src/
│   └── api/
│       └── main.py      # FastAPI server with file ops
├── web/
│   └── templates/
│       └── index.html   # IDE interface
├── config/
│   └── settings.py      # Configuration
├── start.sh             # Startup script
└── requirements.txt     # Dependencies
```

## 🆚 Comparison

| Feature | DuilioCode | Cursor AI | GitHub Copilot |
|---------|-----------|-----------|----------------|
| **Offline** | ✅ Yes | ❌ No | ❌ No |
| **Privacy** | ✅ 100% Local | ☁️ Cloud | ☁️ Cloud |
| **File Editing** | ✅ Full access | ✅ Full access | ⚠️ Limited |
| **Cost** | 💚 Free | 💰 Paid | 💰 Paid |
| **Project Creation** | ✅ Yes | ✅ Yes | ⚠️ Limited |

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Open issues for bugs or features
- Submit pull requests
- Share your feedback

## 📄 License

MIT License - Use freely!

---

**DuilioCode Studio** - Your offline Cursor! 🚀

Made with ❤️ for developers who value privacy.
