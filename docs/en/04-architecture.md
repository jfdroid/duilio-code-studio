# System Architecture

## Overview

DuilioCode Studio follows **Clean Architecture** with **MVI (Model-View-Intent)** pattern and **SOLID** principles.

## Architecture Layers

```
┌─────────────────────────────────────┐
│         Presentation Layer           │
│  (Frontend - HTML/JS/CSS)            │
└──────────────┬──────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────┐
│         API Layer                    │
│  (FastAPI Routes)                    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Service Layer                │
│  (Business Logic)                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Core Layer                   │
│  (Infrastructure)                     │
└──────────────────────────────────────┘
```

## Layer Structure

### 1. Presentation Layer (Frontend)

**Location**: `web/`

**Responsibilities**:
- User interface
- API communication
- State management
- Message rendering

**Technologies**:
- HTML5
- Vanilla JavaScript (no frameworks)
- CSS3

### 2. API Layer (Routes)

**Location**: `src/api/routes/`

**Responsibilities**:
- Receive HTTP requests
- Validate input data
- Call appropriate services
- Return formatted responses

**Structure**:
```
routes/
├── chat/              # Chat endpoints
│   ├── chat_router.py
│   ├── chat_handler.py
│   └── generate_handler.py
├── files.py           # File operations
├── workspace.py       # Workspace
└── health.py         # Health checks
```

### 3. Service Layer (Business Logic)

**Location**: `src/services/`

**Responsibilities**:
- Business logic
- Data processing
- External service integration
- Operation orchestration

**Main Services**:
- `ollama_service.py` - Ollama integration
- `action_processor.py` - Action execution
- `linguistic_analyzer.py` - Linguistic analysis
- `codebase_analyzer.py` - Code analysis
- `workspace_service.py` - Workspace management

### 4. Core Layer (Infrastructure)

**Location**: `src/core/`

**Responsibilities**:
- Configuration
- Logging
- Database
- Security
- Validation
- Error handling

**Components**:
- `config.py` - Settings
- `database.py` - Database setup
- `logger.py` - Logging
- `error_handler.py` - Error handling
- `validators.py` - Validation
- `security.py` - Security

## Data Flow

### Example: Create File

```
1. Frontend (chat.js)
   └─> POST /api/chat
       {message: "create teste.txt"}

2. API Layer (chat_router.py)
   └─> Validates request
   └─> Calls chat_handler.handle()

3. Service Layer (chat_handler.py)
   └─> Detects intention (create)
   └─> Analyzes context
   └─> Calls ollama_service.generate()

4. Ollama Service
   └─> Sends to Ollama
   └─> Receives response: "```create-file:teste.txt\n...```"

5. Action Processor
   └─> Extracts action
   └─> Executes: creates file

6. Response
   └─> Returns to API
   └─> API returns to Frontend
   └─> Frontend displays result
```

## Dependency Injection

### Container

**Location**: `src/core/container.py`

**Function**: Centralizes dependency creation

```python
def get_ollama_service() -> OllamaService:
    return OllamaService(settings.OLLAMA_HOST)

def get_chat_handler() -> ChatHandler:
    return ChatHandler(
        ollama=get_ollama_service(),
        workspace=get_workspace_service()
    )
```

### Usage in Routes

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    handler: ChatHandler = Depends(get_chat_handler)
):
    return await handler.handle(request)
```

## SOLID Principles

### S - Single Responsibility
Each class has **one responsibility**:
- `OllamaService` → Only Ollama communication
- `ActionProcessor` → Only action execution
- `LinguisticAnalyzer` → Only linguistic analysis

### O - Open/Closed
Open for **extension**, closed for **modification**:
- New services can be added without modifying existing ones
- New action types can be added to ActionProcessor

### L - Liskov Substitution
Subclasses can **replace** base classes:
- Different cache implementations can be swapped

### I - Interface Segregation
**Specific** interfaces instead of generic:
- `FileService` has specific methods for files
- `WorkspaceService` has specific methods for workspace

### D - Dependency Inversion
Depend on **abstractions**, not implementations:
- Routes depend on interfaces, not concrete implementations

## Design Patterns

### 1. Factory Pattern
**Usage**: Service creation in container

```python
def get_ollama_service() -> OllamaService:
    return OllamaService(...)
```

### 2. Strategy Pattern
**Usage**: Different prompt strategies per operation

```python
if operation == OperationType.CREATE:
    prompt = build_create_prompt(context)
elif operation == OperationType.READ:
    prompt = build_read_prompt(context)
```

### 3. Observer Pattern
**Usage**: System events (metrics, logs)

```python
metrics_collector.record("chat_completion", duration)
logger.info("Chat completed", extra={"duration": duration})
```

## Separation of Responsibilities

### Routes → Handlers
- Routes: Validation, routing
- Handlers: Business logic

### Handlers → Services
- Handlers: Orchestration
- Services: Specific operations

### Services → Core
- Services: Business logic
- Core: Infrastructure

## Testability

### How to Test

**Unit Tests**: Test services in isolation
```python
def test_ollama_service():
    service = OllamaService()
    result = await service.generate("test", "model")
    assert result is not None
```

**Integration Tests**: Test complete flow
```python
def test_chat_flow():
    response = await client.post("/api/chat", json={...})
    assert response.status_code == 200
```

## Scalability

### Horizontal Scaling
- Stateless: Each request is independent
- Database: SQLite can be migrated to PostgreSQL

### Vertical Scaling
- Async: Supports multiple simultaneous requests
- Cache: Reduces system load

## Next Steps

- [Folder Structure](05-structure.md)
- [Patterns and Principles](06-patterns.md)
