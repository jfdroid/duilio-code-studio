# Arquitetura do Sistema

## Visão Geral

DuilioCode Studio segue **Clean Architecture** com padrão **MVI (Model-View-Intent)** e princípios **SOLID**.

## Camadas da Arquitetura

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

## Estrutura de Camadas

### 1. Presentation Layer (Frontend)

**Localização**: `web/`

**Responsabilidades**:
- Interface do usuário
- Comunicação com API
- Gerenciamento de estado
- Renderização de mensagens

**Tecnologias**:
- HTML5
- Vanilla JavaScript (sem frameworks)
- CSS3

### 2. API Layer (Rotas)

**Localização**: `src/api/routes/`

**Responsabilidades**:
- Receber requisições HTTP
- Validar dados de entrada
- Chamar serviços apropriados
- Retornar respostas formatadas

**Estrutura**:
```
routes/
├── chat/              # Endpoints de chat
│   ├── chat_router.py
│   ├── chat_handler.py
│   └── generate_handler.py
├── files.py           # Operações de arquivo
├── workspace.py       # Workspace
└── health.py         # Health checks
```

### 3. Service Layer (Lógica de Negócio)

**Localização**: `src/services/`

**Responsabilidades**:
- Lógica de negócio
- Processamento de dados
- Integração com serviços externos
- Orquestração de operações

**Serviços Principais**:
- `ollama_service.py` - Integração com Ollama
- `action_processor.py` - Execução de ações
- `linguistic_analyzer.py` - Análise linguística
- `codebase_analyzer.py` - Análise de código
- `workspace_service.py` - Gerenciamento de workspace

### 4. Core Layer (Infraestrutura)

**Localização**: `src/core/`

**Responsabilidades**:
- Configuração
- Logging
- Database
- Segurança
- Validação
- Error handling

**Componentes**:
- `config.py` - Configurações
- `database.py` - Database setup
- `logger.py` - Logging
- `error_handler.py` - Error handling
- `validators.py` - Validação
- `security.py` - Segurança

## Fluxo de Dados

### Exemplo: Criar Arquivo

```
1. Frontend (chat.js)
   └─> POST /api/chat
       {message: "crie teste.txt"}

2. API Layer (chat_router.py)
   └─> Valida request
   └─> Chama chat_handler.handle()

3. Service Layer (chat_handler.py)
   └─> Detecta intenção (create)
   └─> Analisa contexto
   └─> Chama ollama_service.generate()

4. Ollama Service
   └─> Envia para Ollama
   └─> Recebe resposta: "```create-file:teste.txt\n...```"

5. Action Processor
   └─> Extrai ação
   └─> Executa: cria arquivo

6. Response
   └─> Retorna para API
   └─> API retorna para Frontend
   └─> Frontend exibe resultado
```

## Dependency Injection

### Container

**Localização**: `src/core/container.py`

**Função**: Centraliza criação de dependências

```python
def get_ollama_service() -> OllamaService:
    return OllamaService(settings.OLLAMA_HOST)

def get_chat_handler() -> ChatHandler:
    return ChatHandler(
        ollama=get_ollama_service(),
        workspace=get_workspace_service()
    )
```

### Uso nas Rotas

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    handler: ChatHandler = Depends(get_chat_handler)
):
    return await handler.handle(request)
```

## Princípios SOLID

### S - Single Responsibility
Cada classe tem **uma responsabilidade**:
- `OllamaService` → Apenas comunicação com Ollama
- `ActionProcessor` → Apenas execução de ações
- `LinguisticAnalyzer` → Apenas análise linguística

### O - Open/Closed
Aberto para **extensão**, fechado para **modificação**:
- Novos serviços podem ser adicionados sem modificar existentes
- Novos tipos de ação podem ser adicionados ao ActionProcessor

### L - Liskov Substitution
Subclasses podem **substituir** classes base:
- Diferentes implementações de cache podem ser trocadas

### I - Interface Segregation
Interfaces **específicas** ao invés de genéricas:
- `FileService` tem métodos específicos para arquivos
- `WorkspaceService` tem métodos específicos para workspace

### D - Dependency Inversion
Depender de **abstrações**, não implementações:
- Rotas dependem de interfaces, não implementações concretas

## Padrões de Design

### 1. Factory Pattern
**Uso**: Criação de serviços no container

```python
def get_ollama_service() -> OllamaService:
    return OllamaService(...)
```

### 2. Strategy Pattern
**Uso**: Diferentes estratégias de prompt por operação

```python
if operation == OperationType.CREATE:
    prompt = build_create_prompt(context)
elif operation == OperationType.READ:
    prompt = build_read_prompt(context)
```

### 3. Observer Pattern
**Uso**: Eventos de sistema (métricas, logs)

```python
metrics_collector.record("chat_completion", duration)
logger.info("Chat completed", extra={"duration": duration})
```

## Separação de Responsabilidades

### Routes → Handlers
- Routes: Validação, roteamento
- Handlers: Lógica de negócio

### Handlers → Services
- Handlers: Orquestração
- Services: Operações específicas

### Services → Core
- Services: Lógica de negócio
- Core: Infraestrutura

## Testabilidade

### Como Testar

**Unit Tests**: Testam serviços isoladamente
```python
def test_ollama_service():
    service = OllamaService()
    result = await service.generate("test", "model")
    assert result is not None
```

**Integration Tests**: Testam fluxo completo
```python
def test_chat_flow():
    response = await client.post("/api/chat", json={...})
    assert response.status_code == 200
```

## Escalabilidade

### Horizontal Scaling
- Stateless: Cada requisição é independente
- Database: SQLite pode ser migrado para PostgreSQL

### Vertical Scaling
- Async: Suporta múltiplas requisições simultâneas
- Cache: Reduz carga no sistema

## Próximos Passos

- [Estrutura de Pastas](05-estrutura.md)
- [Padrões e Princípios](06-padroes.md)
