# Modo Chat vs Modo Agent

## Visão Geral

DuilioCode tem **dois modos de operação** completamente diferentes, cada um otimizado para um tipo de uso.

## 🗣️ Modo Chat (Simples)

### Quando Usar?
- Perguntas gerais sobre programação
- Explicações de conceitos
- Conversas simples sem operações em arquivos
- Quando você só quer conversar, não fazer ações

### Características
- **Interface focada**: Layout centralizado, esconde elementos do IDE
- **Resposta direta**: Sem processamento complexo
- **Sem contexto de arquivos**: Não analisa o projeto
- **Rápido**: Resposta imediata

### Como Funciona?

```
Usuário → Chat Mode → Ollama (direto) → Resposta
```

**Código**: `src/api/routes/chat_simple.py`

```python
@router.post("/chat/simple")
async def chat_simple(request: SimpleChatRequest):
    # Envia direto para Ollama, sem processamento
    response = await ollama.generate(
        prompt=request.messages[-1]["content"],
        model=request.model
    )
    return {"response": response}
```

### Exemplo de Uso

**Pergunta:**
```
"O que é Python?"
```

**Resposta:**
```
"Python é uma linguagem de programação de alto nível..."
```

**Sem ações**, apenas explicação.

## 🤖 Modo Agent (Avançado)

### Quando Usar?
- Criar, modificar, deletar arquivos
- Operações no sistema de arquivos
- Análise de código
- Trabalhar com projetos completos
- Quando você quer que o DuilioCode **faça coisas**, não apenas explique

### Características
- **CRUD completo**: Create, Read, Update, Delete
- **Contexto completo**: Analisa o projeto inteiro
- **Ações automáticas**: Executa o que você pedir
- **Sistema de arquivos**: Acesso direto aos arquivos

### Como Funciona?

```
Usuário → Agent Mode → Análise de Intenção → Contexto do Projeto → 
Ollama (com contexto) → Action Processor → Executa Ações → Resposta
```

**Código**: `src/api/routes/chat/chat_handler.py`

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    # 1. Detecta intenção (CRUD)
    crud_intent = detect_crud_intent(message)
    
    # 2. Analisa codebase
    context = build_codebase_context(workspace_path)
    
    # 3. Gera resposta com contexto
    response = await ollama.generate(
        prompt=message,
        system_prompt=build_system_prompt(crud_intent, context),
        model=request.model
    )
    
    # 4. Processa ações (create-file, etc.)
    actions = process_actions(response)
    
    return {"response": response, "actions": actions}
```

### Exemplo de Uso

**Pergunta:**
```
"crie um arquivo teste.txt com 'Hello World'"
```

**Processamento:**
1. Detecta: `create_intent = True`
2. Analisa: workspace atual
3. Gera: ````create-file:teste.txt\nHello World\n````
4. Executa: Action Processor cria o arquivo
5. Responde: "Arquivo teste.txt criado com sucesso!"

## Comparação Visual

### Modo Chat
```
┌─────────────────────────────────┐
│         Chat Centrado           │
│                                 │
│  Você: O que é Python?         │
│                                 │
│  AI: Python é uma linguagem...  │
│                                 │
│  [Input]                        │
└─────────────────────────────────┘
```

### Modo Agent
```
┌──────────┬──────────────────┬─────┐
│ Explorer │   Chat Panel     │ ... │
│          │                  │     │
│ src/     │  Você: crie...   │     │
│  app.js  │                  │     │
│          │  AI: [cria]     │     │
│          │                  │     │
│          │  [Input]         │     │
└──────────┴──────────────────┴─────┘
```

## Detecção de Modo

### Frontend

**Código**: `web/static/js/chat.js`

```javascript
// Detecta modo inicial
initMode() {
    const agentBtn = document.querySelector('#mode-agent');
    this.mode = agentBtn?.classList.contains('active') ? 'agent' : 'chat';
}

// Envia para endpoint correto
send() {
    if (this.mode === 'chat') {
        endpoint = '/api/chat/simple';
    } else {
        endpoint = '/api/chat';
    }
}
```

### Backend

O backend **não precisa detectar** - cada modo tem seu próprio endpoint:
- `/api/chat/simple` → Sempre modo chat
- `/api/chat` → Sempre modo agent

## Quando Usar Cada Modo?

### Use Chat Mode quando:
- ✅ Quer apenas conversar
- ✅ Precisa de explicações
- ✅ Não vai fazer operações em arquivos
- ✅ Quer resposta rápida

### Use Agent Mode quando:
- ✅ Vai criar/modificar arquivos
- ✅ Precisa trabalhar com o projeto
- ✅ Quer que DuilioCode execute ações
- ✅ Precisa de contexto do codebase

## Mudando de Modo

### Na Interface
- Clique no botão "Chat" ou "Agent"
- Interface muda automaticamente
- Próxima mensagem usa o modo selecionado

### Programaticamente
```javascript
// Mudar para Agent
Chat.setMode('agent');

// Mudar para Chat
Chat.setMode('chat');
```

## Diferenças Técnicas

| Aspecto | Chat Mode | Agent Mode |
|---------|-----------|------------|
| **Endpoint** | `/api/chat/simple` | `/api/chat` |
| **Contexto** | Nenhum | Codebase completo |
| **Processamento** | Direto | Análise + Contexto |
| **Ações** | Não executa | Executa automaticamente |
| **Velocidade** | Muito rápido | Mais lento (com contexto) |
| **Temperatura** | 0.7 (padrão) | Ajustável (0.2-0.9) |

## Próximos Passos

- [Como Funciona o Chat](11-chat-funcionamento.md)
- [CRUD - Operações de Arquivos](13-crud.md)
