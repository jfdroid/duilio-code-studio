# DuilioCode Studio

AI-powered code assistant with direct file system access, full CRUD operations, and comprehensive observability.

## 🚀 Features

### Core Features
- **Agent Mode**: Full CRUD operations on files, directories, and projects
- **Chat Mode**: Simple conversation with centered layout (Gemini/DeepSeek style)
- **Intelligent Context**: Automatic codebase analysis and context injection
- **Linguistic Analysis**: Advanced NLP for intent detection (verbs, connectors, patterns)
- **System Information**: Access to local machine data (OS, CPU, Memory, User, Hostname)

### File Operations
- **Create**: Files, directories, complete projects
- **Read**: File content with intelligent context
- **Update**: Modify existing files with full content
- **Delete**: Files and directories
- **List**: Accurate file and folder counting with tree structure

### Advanced Capabilities
- **Project Scaffolding**: Complete project generation (React, Android, Node.js, Python, etc.)
- **Code Analysis**: Intelligent codebase understanding
- **Dependency Graph**: File dependency tracking
- **Action Processing**: Automatic execution of AI-generated actions
- **Prompt Engineering**: Operation-specific, clean prompts (no verbosity)

## 📋 Requirements

- Python 3.9+
- Ollama (local LLM server)
- Qwen2.5-Coder model (14b or 7b)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd duilio-code-studio
```

### 2. Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com
```

### 3. Pull Model
```bash
ollama pull qwen2.5-coder:14b
# Or use 7b for faster responses:
ollama pull qwen2.5-coder:7b
```

### 4. Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Start Server
```bash
./start.sh
# Or manually:
cd src
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8080 --reload
```

### 6. Access Interface
- **Web UI**: http://127.0.0.1:8080
- **API Docs**: http://127.0.0.1:8080/docs
- **Health Check**: http://127.0.0.1:8080/health

## 🏗️ Architecture

### Clean Architecture + MVI Pattern
- **Separation of Concerns**: Routes, Handlers, Services, Core
- **Dependency Injection**: Centralized container (`core/container.py`)
- **Error Handling**: Centralized error handler (`core/error_handler.py`)
- **Validation**: Centralized validators (`core/validators.py`)

### Project Structure
```
duilio-code-studio/
├── src/
│   ├── api/
│   │   ├── main.py                    # FastAPI app entry point
│   │   └── routes/
│   │       ├── chat/
│   │       │   ├── chat_router.py     # Chat endpoints router
│   │       │   ├── chat_handler.py    # Main chat logic (Agent mode)
│   │       │   ├── generate_handler.py # Code generation handler
│   │       │   ├── context_builder.py  # Codebase context builder
│   │       │   └── codebase_endpoints.py # Codebase analysis endpoints
│   │       ├── chat_simple.py         # Simple chat (Chat mode)
│   │       ├── files.py               # File operations
│   │       ├── workspace.py           # Workspace management
│   │       ├── models.py              # Model management
│   │       ├── tools.py               # Git, Execute, Refactor, etc.
│   │       ├── health.py              # Health checks
│   │       ├── metrics.py             # Performance metrics
│   │       └── observability.py       # Tracing, Prometheus
│   ├── core/
│   │   ├── config.py                  # Settings (Pydantic)
│   │   ├── container.py               # Dependency Injection
│   │   ├── database.py                # SQLAlchemy setup
│   │   ├── models.py                  # Database models
│   │   ├── error_handler.py           # Centralized error handling
│   │   ├── validators.py              # Input validation
│   │   ├── logger.py                  # Structured logging
│   │   ├── metrics.py                 # Performance metrics
│   │   ├── observability.py           # Tracing, Prometheus
│   │   ├── security.py                 # Input sanitization
│   │   ├── secrets.py                 # Secrets management
│   │   └── exceptions.py              # Custom exceptions
│   ├── services/
│   │   ├── ollama_service.py         # Ollama API integration
│   │   ├── prompt_builder.py          # Clean prompt construction
│   │   ├── action_processor.py        # Process create-file, modify-file, etc.
│   │   ├── linguistic_analyzer.py     # NLP intent detection
│   │   ├── intent_detector.py         # CRUD intent detection
│   │   ├── system_info.py             # System information
│   │   ├── workspace_service.py       # Workspace operations
│   │   ├── file_service.py            # File operations
│   │   ├── cache_service.py           # Cache (diskcache)
│   │   ├── database_service.py        # Database operations
│   │   └── ... (30+ services)
│   └── middleware/
│       └── rate_limiter.py            # Rate limiting
├── web/
│   ├── templates/
│   │   └── index.html                 # Main UI
│   └── static/
│       ├── js/                         # Frontend modules (22 files)
│       └── css/                        # Styles
├── tests/
│   ├── unit/                           # Unit tests (32 tests)
│   ├── integration/                    # Integration tests
│   └── e2e/                            # End-to-end tests
├── data/
│   └── linguistic/                     # NLP data (verbs, connectors, patterns)
├── alembic/                             # Database migrations
├── .github/
│   └── workflows/
│       └── ci.yml                      # CI/CD pipeline
├── requirements.txt                     # Python dependencies
└── start.sh                             # Startup script
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:14b

# Database
DATABASE_URL=sqlite:///./data/duiliocode.db

# Server
HOST=127.0.0.1
PORT=8080
DEBUG=false

# Cache
CACHE_DIR=.cache/duiliocode
CACHE_DEFAULT_TTL=3600
CACHE_SIZE_LIMIT_MB=500

# Security
CORS_ORIGINS=*
```

### Settings
All settings can be configured via:
- Environment variables
- `.env` file
- `src/core/config.py` (Pydantic Settings)

## 📊 Database

### SQLite Database
- **Location**: `data/duiliocode.db` (or `DATABASE_URL`)
- **Models**:
  - `UserPreference`: User preferences (key-value)
  - `ConversationHistory`: Chat history persistence
  - `SystemMetric`: System metrics for analytics

### Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Service
```python
from services.database_service import get_database_service

db = get_database_service()

# Preferences
db.set_preference('user_id', 'theme', 'dark')
theme = db.get_preference('user_id', 'theme')

# Conversation history
db.save_message('user_id', 'session_id', 'user', 'Hello')
history = db.get_conversation_history('user_id', 'session_id')

# Metrics
db.save_metric('chat_completion', 1234.5, success=True)
```

## 🔒 Security

### Input Sanitization
- **Path Traversal Prevention**: Validates and sanitizes file paths
- **XSS Prevention**: HTML escaping for text inputs
- **SQL Injection Prevention**: Input sanitization for SQL queries
- **Model Name Validation**: Validates model names format

### Secrets Management
- Environment variables support
- `.env` file support
- Secret masking for logging
- Secure storage of API keys

### Rate Limiting
- Granular limits per endpoint
- Configurable via `src/middleware/rate_limiter.py`
- Default: 30/min for chat, 20/min for generate

## 📈 Observability

### Performance Metrics
- **MetricsCollector**: Tracks operation performance
- **Decorator**: `@track_performance("operation_name")`
- **Endpoint**: `/api/metrics/stats`

### Distributed Tracing
- **Tracer**: Tracks request spans
- **Decorator**: `@trace_operation("operation_name")`
- **Endpoint**: `/api/observability/trace`

### Prometheus Metrics
- **Exporter**: Prometheus-compatible metrics
- **Endpoint**: `/api/observability/metrics/prometheus`
- **Health**: `/health/prometheus`

### Health Checks
- `/health` - Basic health check
- `/health/ollama` - Ollama status
- `/health/full` - Full system status
- `/api/observability/health/detailed` - Detailed health with metrics

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests
pytest tests/ -v
```

### Test Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## 🚢 CI/CD

### GitHub Actions
- **Tests**: Python 3.9, 3.10, 3.11
- **Linting**: flake8, black, mypy
- **Security**: bandit, safety
- **Coverage**: Codecov integration

### Pipeline
Located in `.github/workflows/ci.yml`

## 📝 API Endpoints

### Chat
- `POST /api/chat` - Agent mode (full features)
- `POST /api/chat/simple` - Chat mode (simple conversation)
- `POST /api/generate` - Code generation
- `POST /api/generate/stream` - Streaming generation

### Files
- `GET /api/files/list` - List files
- `POST /api/files/read` - Read file
- `POST /api/files/write` - Write file
- `POST /api/files/create` - Create file/directory
- `DELETE /api/files/delete` - Delete file/directory

### Workspace
- `GET /api/workspace/tree` - File tree
- `POST /api/workspace/analyze` - Analyze codebase

### Observability
- `GET /api/metrics/stats` - Performance metrics
- `GET /api/observability/trace` - Trace information
- `GET /api/observability/metrics/prometheus` - Prometheus metrics
- `GET /api/observability/health/detailed` - Detailed health

## 🎯 Usage Examples

### Agent Mode - Create Directory
```
User: "crie o diretorio teste-chat-ai"
AI: ```create-directory:teste-chat-ai```
```

### Agent Mode - Create File
```
User: "crie um arquivo teste.txt com 'Hello World'"
AI: ```create-file:teste.txt
Hello World
```
```

### Agent Mode - List Files
```
User: "quais arquivos você vê?"
AI: [Lists files from FILE LISTING context]
```

### Chat Mode - Simple Question
```
User: "O que é Python?"
AI: [Simple explanation without file operations]
```

## 🔍 Key Improvements Implemented

### Critical (4/4)
1. ✅ Refactored `chat.py` (1,663 → 5 modules)
2. ✅ Organized tests (32 unit tests)
3. ✅ Thread-safe cache (diskcache)
4. ✅ Centralized validation

### Important (4/4)
5. ✅ Dependency Injection (container.py)
6. ✅ Type hints complete
7. ✅ Centralized error handling
8. ✅ Expanded configuration

### Enhancements (7/7)
9. ✅ OpenAPI documentation
10. ✅ Performance monitoring
11. ✅ Frontend modularized
12. ✅ Data persistence (SQLite)
13. ✅ CI/CD pipeline
14. ✅ Security (sanitization, secrets)
15. ✅ Observability (tracing, Prometheus)

## 🛡️ Best Practices

### Prompt Engineering
- Operation-specific prompts (CREATE, READ, UPDATE, DELETE, LIST)
- Direct imperative language
- Minimal verbosity
- Clear context structure
- File listing prioritized

### Code Quality
- Clean Architecture
- SOLID principles
- Type hints
- Comprehensive error handling
- Structured logging

### Security
- Input sanitization
- Path traversal prevention
- SQL injection prevention
- Rate limiting
- Secrets management

## 📚 Dependencies

See `requirements.txt` for complete list. Key dependencies:
- FastAPI 0.115.0+
- SQLAlchemy 2.0.0+
- Alembic 1.13.0+
- Pydantic 2.9.0+
- diskcache 5.6.0+

## 🤝 Contributing

1. Follow Clean Architecture principles
2. Add type hints to all public methods
3. Write tests for new features
4. Update documentation
5. Follow existing code style

## 📄 License

[Add your license here]

## 🆘 Troubleshooting

### Ollama Not Running
```bash
ollama serve
```

### Model Not Found
```bash
ollama pull qwen2.5-coder:14b
```

### Database Issues
```bash
# Reset database
rm data/duiliocode.db
# Restart server (will recreate)
```

### Port Already in Use
```bash
# Change port in .env or config.py
PORT=8081
```

## 🎉 Status

**All 15 improvements implemented and validated!**

- ✅ 32 unit tests passing
- ✅ All integrations working
- ✅ Database functional
- ✅ Security implemented
- ✅ Observability complete
- ✅ CI/CD configured

**Ready for production use!**
