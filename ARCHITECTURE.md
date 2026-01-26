# DuilioCode Studio - Architecture Documentation

## Overview

DuilioCode Studio is an AI-powered coding assistant that provides intelligent code generation, analysis, and file management capabilities. It uses a FastAPI backend with a web-based UI, connecting to Ollama/Qwen for AI-powered features.

## Architecture Pattern

**Type**: REST API (not MCP/RIG)
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript + HTML/CSS
- **AI Engine**: Ollama with Qwen models
- **Communication**: HTTP REST API

## Core Components

### 1. API Layer (`src/api/`)
- **main.py**: FastAPI application setup, middleware, routing
- **routes/chat.py**: Chat and code generation endpoints
- **routes/files.py**: File operations (read, write, delete)
- **routes/workspace.py**: Workspace management
- **routes/tools.py**: Additional tools (git, execute, scaffold, refactor, docs, security, agent)

### 2. Services Layer (`src/services/`)

#### AI Services
- **ollama_service.py**: Communication with Ollama API
- **intent_detector.py**: AI-powered intent classification (read, create, modify, delete)
- **project_detector.py**: AI-powered project intention detection

#### Analysis Services
- **codebase_analyzer.py**: Intelligent codebase analysis with caching
- **language_detector.py**: Dynamic language detection using AI
- **file_intelligence.py**: AI-powered file classification
- **relevance_scorer.py**: Relevance scoring with caching

#### File Operations
- **file_service.py**: File read/write operations
- **workspace_service.py**: Workspace management
- **action_processor.py**: Process AI-generated actions (create-file, modify-file, delete-file, run-command)
- **path_intelligence.py**: Intelligent path resolution
- **path_security.py**: Security validation for paths (path traversal prevention)

#### Infrastructure
- **cache_service.py**: Disk-based caching using diskcache
- **code_executor.py**: Safe command execution
- **dependency_graph.py**: File dependency tracking
- **directory_tree.py**: Efficient directory structure representation

### 3. Core Layer (`src/core/`)
- **config.py**: Application configuration (Pydantic Settings)
- **logger.py**: Structured logging with JSON output
- **exceptions.py**: Custom exception classes

## Data Flow

### Chat/Generation Flow
1. User sends prompt via `/api/chat` or `/api/generate`
2. **IntentDetector** classifies user intent (read, create, modify, delete)
3. **ProjectDetector** determines if new project directory is needed
4. **CodebaseAnalyzer** analyzes workspace (with cache)
5. System prompt is constructed with context
6. **OllamaService** generates response using Qwen
7. **ActionProcessor** extracts and executes actions from response
8. **PathSecurity** validates all paths for security
9. Results are returned to frontend

### File Creation Flow
1. AI generates `create-file:path` action
2. **ActionProcessor** extracts action
3. **PathSecurity** validates path (prevents traversal attacks)
4. **PathIntelligence** normalizes path
5. **FileService** creates file
6. **Logger** logs action with context
7. Frontend refreshes explorer

## Security Features

### Path Security (`path_security.py`)
- Prevents path traversal attacks (`../`, `..\\`)
- Detects null byte injection
- Validates symlinks
- Ensures paths stay within workspace (configurable)

### Command Execution (`code_executor.py`, `action_processor.py`)
- AI-powered command safety checking
- Timeout protection
- Working directory validation
- Shell injection prevention

## Performance Optimizations

### Caching
- **Codebase Analysis**: Cached for 1 hour (TTL)
- **Relevance Scoring**: LRU cache (10,000 entries)
- **File Intelligence**: Pattern-based (fast)
- **Cache Service**: Disk-based using diskcache (500MB limit)

### Efficient Data Structures
- **DirectoryTree**: Trie-based structure for fast path lookups
- **DependencyGraph**: Graph structure for dependency tracking
- **LRU Caches**: In-memory caches for frequently accessed data

## Logging

### Structured Logging (`core/logger.py`)
- JSON-formatted logs
- Context-aware (workspace_path, file_path, etc.)
- Performance metrics
- Security event tracking
- Configurable log levels and file output

## AI Integration

### Ollama/Qwen Usage
- **Intent Detection**: Classifies user prompts
- **Project Detection**: Determines project creation needs
- **Code Generation**: Generates code, files, and actions
- **Language Detection**: Dynamically detects languages
- **File Classification**: Intelligent file type detection

### System Prompts
- Context-aware prompts with codebase analysis
- Few-shot examples for action format
- Dynamic instructions based on detected intent
- Project creation instructions when needed

## Configuration

### Settings (`core/config.py`)
- Environment variable support
- `.env` file support
- Default values for all settings
- Type-safe with Pydantic

### Key Settings
- `OLLAMA_HOST`: Ollama API endpoint
- `DEFAULT_MODEL`: Default AI model (qwen2.5-coder:14b)
- `MAX_FILE_SIZE`: Maximum file size for analysis (10MB)
- `LOG_LEVEL`: Logging level (INFO)
- `LOG_JSON`: Use structured JSON logging (True)

## Testing

### Test Structure
- **test_critical_scenarios.py**: Comprehensive test suite
- **test_chat_scenarios.md**: Original 15 chat scenarios
- **critical_test_results.json**: Test execution results

### Test Isolation
- Each test creates isolated project directory
- Prevents test interference
- Clean workspace for each scenario

## Future Improvements

1. **Async Optimization**: Parallel processing for file operations
2. **Type Hints**: Complete type annotations
3. **Integration Tests**: End-to-end flow validation
4. **UI Analysis**: Performance, accessibility, UX improvements
5. **Dependencies**: Security and compatibility updates

## Dependencies

### Core
- FastAPI: Web framework
- Pydantic: Data validation
- diskcache: Disk-based caching

### AI
- httpx: HTTP client for Ollama
- ollama: Ollama Python client (optional)

### Utilities
- pathlib: Path operations
- typing: Type hints
- logging: Logging (enhanced with structured logger)

## File Structure

```
duilio-code-studio/
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── files.py
│   │       ├── workspace.py
│   │       └── tools.py
│   ├── services/
│   │   ├── ollama_service.py
│   │   ├── intent_detector.py
│   │   ├── project_detector.py
│   │   ├── codebase_analyzer.py
│   │   ├── action_processor.py
│   │   ├── path_security.py
│   │   └── ...
│   └── core/
│       ├── config.py
│       ├── logger.py
│       └── exceptions.py
├── web/
│   ├── static/
│   │   ├── js/
│   │   └── css/
│   └── templates/
├── test_critical_scenarios.py
└── requirements.txt
```

## Design Decisions

1. **REST API over MCP/RIG**: Simpler, more flexible, easier to debug
2. **AI-Powered Detection**: Dynamic detection instead of hardcoded lists
3. **Security First**: Path validation, command safety, input sanitization
4. **Performance**: Caching, efficient data structures, async where possible
5. **Structured Logging**: JSON logs for better observability
6. **Test Isolation**: Each test creates its own directory

## Contributing

When adding new features:
1. Use AI-powered detection instead of hardcoded patterns
2. Add security validation for file operations
3. Use structured logging
4. Add caching for expensive operations
5. Write tests with isolated directories
6. Document architecture decisions
