# FastAPI - Web Framework

## What is FastAPI?

FastAPI is a **modern and fast** framework for creating APIs in Python. It's perfect for connecting the frontend (web interface) with the backend (DuilioCode logic).

## Why FastAPI?

### ✅ Advantages
- **Fast**: One of the fastest frameworks in Python
- **Type Safety**: Automatic validation with type hints
- **Automatic Documentation**: Generates OpenAPI/Swagger docs
- **Async/Await**: Supports asynchronous operations
- **Easy to Use**: Simple and clear syntax

## How Does It Work in DuilioCode?

### Basic Structure

```
Frontend (JavaScript) 
    ↓ HTTP Request
FastAPI (Python)
    ↓ Processes
Services (Ollama, File, etc.)
    ↓ Returns
FastAPI
    ↓ HTTP Response
Frontend
```

### Main File: `src/api/main.py`

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Process request
    return {"response": "..."}
```

## Routes (Endpoints)

### What Are Routes?

Routes are **entry points** in the API. Each route does a specific thing:

```
POST /api/chat          → Chat with AI (Agent mode)
POST /api/chat/simple   → Simple chat (Chat mode)
POST /api/generate      → Code generation
GET  /api/files/list    → List files
POST /api/files/create  → Create file
```

### How We Create Routes

```python
# src/api/routes/chat/chat_router.py
router = APIRouter(prefix="/api", tags=["Chat"])

@router.post("/chat")
async def chat(request: ChatRequest):
    handler = get_chat_handler()
    return await handler.handle(request, ollama, workspace)
```

## Request/Response

### Request

When frontend sends data:

```python
class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str
    workspace_path: Optional[str] = None
    temperature: float = 0.7
```

### Response

What backend returns:

```python
{
    "response": "Response text",
    "model": "qwen2.5-coder:14b",
    "tokens": 150,
    "actions": [...]
}
```

## Dependency Injection

### What Is It?

Dependency Injection (DI) is a pattern where **dependencies are injected** instead of created inside the function.

### Without DI (Bad)
```python
def chat():
    ollama = OllamaService()  # Creates inside
    return ollama.generate(...)
```

### With DI (Good)
```python
def chat(ollama: OllamaService = Depends(get_ollama_service)):
    return ollama.generate(...)  # Receives already created
```

### Advantages
- **Testable**: Easy to mock dependencies
- **Reusable**: Same instance shared
- **Organized**: Centralized in container

## Async/Await

### Why Async?

AI operations can take time. Async allows the server to **handle other requests** while waiting:

```python
# Synchronous (blocks)
def chat():
    response = ollama.generate(...)  # Waits here
    return response

# Asynchronous (doesn't block)
async def chat():
    response = await ollama.generate(...)  # Releases for other requests
    return response
```

## Middleware

### What Are They?

Middleware are **functions that execute before/after** routes:

```
Request → Middleware 1 → Middleware 2 → Route → Response
```

### Examples in DuilioCode

1. **CORS**: Allows frontend requests
2. **Rate Limiting**: Limits requests per minute
3. **Error Handling**: Captures errors and formats responses

```python
# src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True
)
```

## Lifespan (Lifecycle)

### Startup
```python
@app.on_event("startup")
async def startup():
    init_database()  # Initialize database
    check_ollama()    # Check Ollama
```

### Shutdown
```python
@app.on_event("shutdown")
async def shutdown():
    await ollama.close()  # Close connections
```

### FastAPI 0.115+ (Lifespan)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    yield
    # Shutdown
    await ollama.close()
```

## Automatic Validation

### Pydantic Models

FastAPI uses Pydantic to **automatically validate** data:

```python
class ChatRequest(BaseModel):
    model: str
    temperature: float = Field(ge=0.0, le=2.0)  # Between 0 and 2

# If you send temperature=3.0 → Automatic error!
```

## Automatic Documentation

### Swagger UI
- **URL**: `http://localhost:8080/api-docs`
- **Visual interface** to test API
- **Automatically generated** from type hints

### ReDoc
- **URL**: `http://localhost:8080/redoc`
- **Alternative documentation** cleaner

## Error Handling

### Exception Handlers

```python
@app.exception_handler(ValidationError)
async def validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": str(exc)}
    )
```

### Centralized

In DuilioCode, we use `core/error_handler.py` to centralize:

```python
error_handler = get_error_handler()

@app.exception_handler(Exception)
async def handler(request, exc):
    http_exc = error_handler.handle_generic_error(exc)
    return JSONResponse(status_code=http_exc.status_code, ...)
```

## Performance

### Uvicorn

FastAPI runs on **Uvicorn** (ASGI server):

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8080
```

### Optimizations
- **Async**: Multiple simultaneous requests
- **Type Hints**: Fast validation
- **Pydantic**: Optimized serialization

## Route Structure in DuilioCode

```
src/api/
├── main.py              # Main app
└── routes/
    ├── chat/
    │   ├── chat_router.py      # Main router
    │   ├── chat_handler.py     # Chat logic
    │   └── generate_handler.py  # Generation logic
    ├── files.py         # File operations
    ├── workspace.py     # Workspace
    ├── health.py        # Health checks
    ├── metrics.py       # Metrics
    └── observability.py # Observability
```

## Next Steps

- [Chat Mode vs Agent Mode](10-chat-modes.md)
- [How Chat Works](11-chat-functionality.md)
