# FastAPI - Framework Web

## O que é FastAPI?

FastAPI é um framework **moderno e rápido** para criar APIs em Python. É perfeito para conectar o frontend (interface web) com o backend (lógica do DuilioCode).

## Por que FastAPI?

### ✅ Vantagens
- **Rápido**: Uma das frameworks mais rápidas em Python
- **Type Safety**: Validação automática com type hints
- **Documentação Automática**: Gera docs OpenAPI/Swagger
- **Async/Await**: Suporta operações assíncronas
- **Fácil de Usar**: Sintaxe simples e clara

## Como Funciona no DuilioCode?

### Estrutura Básica

```
Frontend (JavaScript) 
    ↓ HTTP Request
FastAPI (Python)
    ↓ Processa
Services (Ollama, File, etc.)
    ↓ Retorna
FastAPI
    ↓ HTTP Response
Frontend
```

### Arquivo Principal: `src/api/main.py`

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Processa requisição
    return {"response": "..."}
```

## Rotas (Endpoints)

### O que são Rotas?

Rotas são **pontos de entrada** na API. Cada rota faz uma coisa específica:

```
POST /api/chat          → Chat com IA (Agent mode)
POST /api/chat/simple   → Chat simples (Chat mode)
POST /api/generate      → Geração de código
GET  /api/files/list    → Listar arquivos
POST /api/files/create  → Criar arquivo
```

### Como Criamos Rotas

```python
# src/api/routes/chat/chat_router.py
router = APIRouter(prefix="/api", tags=["Chat"])

@router.post("/chat")
async def chat(request: ChatRequest):
    handler = get_chat_handler()
    return await handler.handle(request, ollama, workspace)
```

## Request/Response

### Request (Requisição)

Quando o frontend envia dados:

```python
class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str
    workspace_path: Optional[str] = None
    temperature: float = 0.7
```

### Response (Resposta)

O que o backend retorna:

```python
{
    "response": "Texto da resposta",
    "model": "qwen2.5-coder:14b",
    "tokens": 150,
    "actions": [...]
}
```

## Dependency Injection

### O que é?

Dependency Injection (DI) é um padrão onde **dependências são injetadas** ao invés de criadas dentro da função.

### Sem DI (Ruim)
```python
def chat():
    ollama = OllamaService()  # Cria dentro
    return ollama.generate(...)
```

### Com DI (Bom)
```python
def chat(ollama: OllamaService = Depends(get_ollama_service)):
    return ollama.generate(...)  # Recebe já criado
```

### Vantagens
- **Testável**: Fácil mockar dependências
- **Reutilizável**: Mesma instância compartilhada
- **Organizado**: Centralizado no container

## Async/Await

### Por que Async?

Operações de IA podem demorar. Async permite que o servidor **atenda outras requisições** enquanto espera:

```python
# Síncrono (bloqueia)
def chat():
    response = ollama.generate(...)  # Espera aqui
    return response

# Assíncrono (não bloqueia)
async def chat():
    response = await ollama.generate(...)  # Libera para outras requisições
    return response
```

## Middleware

### O que são?

Middleware são **funções que executam antes/depois** das rotas:

```
Request → Middleware 1 → Middleware 2 → Route → Response
```

### Exemplos no DuilioCode

1. **CORS**: Permite requisições do frontend
2. **Rate Limiting**: Limita requisições por minuto
3. **Error Handling**: Captura erros e formata respostas

```python
# src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True
)
```

## Lifespan (Ciclo de Vida)

### Startup
```python
@app.on_event("startup")
async def startup():
    init_database()  # Inicializa banco
    check_ollama()    # Verifica Ollama
```

### Shutdown
```python
@app.on_event("shutdown")
async def shutdown():
    await ollama.close()  # Fecha conexões
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

## Validação Automática

### Pydantic Models

FastAPI usa Pydantic para **validar automaticamente** os dados:

```python
class ChatRequest(BaseModel):
    model: str
    temperature: float = Field(ge=0.0, le=2.0)  # Entre 0 e 2

# Se enviar temperature=3.0 → Erro automático!
```

## Documentação Automática

### Swagger UI
- **URL**: `http://localhost:8080/docs`
- **Interface visual** para testar API
- **Gerada automaticamente** dos type hints

### ReDoc
- **URL**: `http://localhost:8080/redoc`
- **Documentação alternativa** mais limpa

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

### Centralizado

No DuilioCode, usamos `core/error_handler.py` para centralizar:

```python
error_handler = get_error_handler()

@app.exception_handler(Exception)
async def handler(request, exc):
    http_exc = error_handler.handle_generic_error(exc)
    return JSONResponse(status_code=http_exc.status_code, ...)
```

## Performance

### Uvicorn

FastAPI roda sobre **Uvicorn** (servidor ASGI):

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8080
```

### Otimizações
- **Async**: Múltiplas requisições simultâneas
- **Type Hints**: Validação rápida
- **Pydantic**: Serialização otimizada

## Estrutura de Rotas no DuilioCode

```
src/api/
├── main.py              # App principal
└── routes/
    ├── chat/
    │   ├── chat_router.py      # Router principal
    │   ├── chat_handler.py     # Lógica do chat
    │   └── generate_handler.py  # Lógica de geração
    ├── files.py         # Operações de arquivo
    ├── workspace.py     # Workspace
    ├── health.py        # Health checks
    ├── metrics.py       # Métricas
    └── observability.py # Observabilidade
```

## Próximos Passos

- [Modo Chat vs Modo Agent](10-chat-modes.md)
- [Como Funciona o Chat](11-chat-funcionamento.md)
