# Chat Mode vs Agent Mode

## Overview

DuilioCode has **two completely different operation modes**, each optimized for a type of use.

## 🗣️ Chat Mode (Simple)

### When to Use?
- General programming questions
- Concept explanations
- Simple conversations without file operations
- When you just want to chat, not perform actions

### Characteristics
- **Focused interface**: Centered layout, hides IDE elements
- **Direct response**: No complex processing
- **No file context**: Doesn't analyze the project
- **Fast**: Immediate response

### How Does It Work?

```
User → Chat Mode → Ollama (direct) → Response
```

**Code**: `src/api/routes/chat_simple.py`

```python
@router.post("/chat/simple")
async def chat_simple(request: SimpleChatRequest):
    # Sends directly to Ollama, no processing
    response = await ollama.generate(
        prompt=request.messages[-1]["content"],
        model=request.model
    )
    return {"response": response}
```

### Usage Example

**Question:**
```
"What is Python?"
```

**Response:**
```
"Python is a high-level programming language..."
```

**No actions**, just explanation.

## 🤖 Agent Mode (Advanced)

### When to Use?
- Create, modify, delete files
- File system operations
- Code analysis
- Work with complete projects
- When you want DuilioCode to **do things**, not just explain

### Characteristics
- **Full CRUD**: Create, Read, Update, Delete
- **Full context**: Analyzes entire project
- **Automatic actions**: Executes what you ask
- **File system**: Direct access to files

### How Does It Work?

```
User → Agent Mode → Intention Analysis → Project Context → 
Ollama (with context) → Action Processor → Executes Actions → Response
```

**Code**: `src/api/routes/chat/chat_handler.py`

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    # 1. Detects intention (CRUD)
    crud_intent = detect_crud_intent(message)
    
    # 2. Analyzes codebase
    context = build_codebase_context(workspace_path)
    
    # 3. Generates response with context
    response = await ollama.generate(
        prompt=message,
        system_prompt=build_system_prompt(crud_intent, context),
        model=request.model
    )
    
    # 4. Processes actions (create-file, etc.)
    actions = process_actions(response)
    
    return {"response": response, "actions": actions}
```

### Usage Example

**Question:**
```
"create a file teste.txt with 'Hello World'"
```

**Processing:**
1. Detects: `create_intent = True`
2. Analyzes: current workspace
3. Generates: ````create-file:teste.txt\nHello World\n````
4. Executes: Action Processor creates the file
5. Responds: "File teste.txt created successfully!"

## Visual Comparison

### Chat Mode
```
┌─────────────────────────────────┐
│         Centered Chat           │
│                                 │
│  You: What is Python?          │
│                                 │
│  AI: Python is a language...   │
│                                 │
│  [Input]                        │
└─────────────────────────────────┘
```

### Agent Mode
```
┌──────────┬──────────────────┬─────┐
│ Explorer │   Chat Panel     │ ... │
│          │                  │     │
│ src/     │  You: create...  │     │
│  app.js  │                  │     │
│          │  AI: [creates]   │     │
│          │                  │     │
│          │  [Input]         │     │
└──────────┴──────────────────┴─────┘
```

## Mode Detection

### Frontend

**Code**: `web/static/js/chat.js`

```javascript
// Detects initial mode
initMode() {
    const agentBtn = document.querySelector('#mode-agent');
    this.mode = agentBtn?.classList.contains('active') ? 'agent' : 'chat';
}

// Sends to correct endpoint
send() {
    if (this.mode === 'chat') {
        endpoint = '/api/chat/simple';
    } else {
        endpoint = '/api/chat';
    }
}
```

### Backend

The backend **doesn't need to detect** - each mode has its own endpoint:
- `/api/chat/simple` → Always chat mode
- `/api/chat` → Always agent mode

## When to Use Each Mode?

### Use Chat Mode when:
- ✅ Just want to chat
- ✅ Need explanations
- ✅ Won't do file operations
- ✅ Want fast response

### Use Agent Mode when:
- ✅ Will create/modify files
- ✅ Need to work with project
- ✅ Want DuilioCode to execute actions
- ✅ Need codebase context

## Changing Modes

### In Interface
- Click "Chat" or "Agent" button
- Interface changes automatically
- Next message uses selected mode

### Programmatically
```javascript
// Change to Agent
Chat.setMode('agent');

// Change to Chat
Chat.setMode('chat');
```

## Technical Differences

| Aspect | Chat Mode | Agent Mode |
|--------|-----------|------------|
| **Endpoint** | `/api/chat/simple` | `/api/chat` |
| **Context** | None | Complete codebase |
| **Processing** | Direct | Analysis + Context |
| **Actions** | Doesn't execute | Executes automatically |
| **Speed** | Very fast | Slower (with context) |
| **Temperature** | 0.7 (default) | Adjustable (0.2-0.9) |

## Next Steps

- [How Chat Works](11-chat-functionality.md)
- [CRUD - File Operations](13-crud.md)
