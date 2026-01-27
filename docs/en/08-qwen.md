# Qwen2.5-Coder - Language Model

## What is Qwen2.5-Coder?

Qwen2.5-Coder is a language model **specialized in code**. It was trained specifically to understand, generate, and work with code in various programming languages.

## Why Qwen2.5-Coder?

### ✅ Code Specialized
- Understands syntax of multiple languages
- Generates functional and correct code
- Understands project context

### ✅ Multilingual
- Works well in Portuguese and English
- Responds in the same language you write

### ✅ Available Sizes
- **14B**: Smarter, needs more RAM (16GB+)
- **7B**: Faster, needs less RAM (8GB+)

## How Does It Work?

### Prompt Processing

```
Your prompt → Qwen processes → Generates response based on:
  - Provided context
  - System prompt instructions
  - Conversation history
  - Pre-trained knowledge
```

### Practical Example

**Input:**
```
System Prompt: "You are DuilioCode. You can create files using ```create-file:path"
User: "create a file teste.txt with 'Hello World'"
```

**Output:**
```
```create-file:teste.txt
Hello World
```
```

## System Prompts

### What Are They?

System prompts are **instructions** that tell the model how to behave. In DuilioCode, we use system prompts to:

1. **Define identity**: "You are DuilioCode"
2. **Capabilities**: "You can create files using create-file:"
3. **Format**: "Use ```create-file:path format"
4. **Rules**: "NEVER say you cannot create files"

### Example System Prompt

```python
CODE_SYSTEM_PROMPT = """You are DuilioCode. You have DIRECT ACCESS to files.

CRITICAL RULES:
- When user asks to create, use ```create-file:path format
- DO NOT say "I cannot create files" - YOU CAN!
- Start response IMMEDIATELY with create-file blocks
"""
```

## Temperature

### What Is It?

Temperature controls the **creativity** of the response:
- **0.0-0.3**: Very deterministic (best for code)
- **0.7**: Balanced (default)
- **1.0-2.0**: Very creative (may generate incorrect code)

### In DuilioCode

```python
# For file listing (precision)
temperature = 0.2

# For code generation (controlled creativity)
temperature = 0.7

# For explanations (more natural)
temperature = 0.9
```

## Context Window

### What Is It?

Context window is the **maximum size** of text the model can process at once.

### Qwen2.5-Coder
- **14B**: ~32,000 tokens
- **7B**: ~32,000 tokens

### How We Use It

1. **File Listing**: List of project files
2. **Codebase Context**: Code analysis
3. **Conversation History**: Previous messages
4. **System Info**: System information

All of this is sent together in the prompt!

## Tokens

### What Are They?

Tokens are **pieces of text** the model processes. They're not exactly words:

- "Hello" = 1 token
- "Hello World" = 2 tokens
- "create a file" = 4 tokens (in English)

### Limits

- **Input**: Maximum tokens in prompt
- **Output**: Maximum tokens in response
- **Total**: Sum of input + output

### In DuilioCode

```python
MAX_TOKENS = 4096  # Maximum tokens in response
```

## Streaming

### What Is It?

Streaming allows the response to appear **word by word** in real time, instead of waiting for everything to be ready.

### How It Works

```
Without Streaming:
  [Wait 10 seconds] → Complete response appears

With Streaming:
  "Hello" → "Hello, how" → "Hello, how can" → ... (appears in real time)
```

### Implementation

```python
async def generate_stream(self, prompt, model):
    async for chunk in ollama.stream(prompt, model):
        yield chunk["response"]  # Sends each piece
```

## Fine-tuning and Adaptation

### How Do We Adapt the Model?

We don't modify the model itself, but **adapt the prompts**:

1. **Specific System Prompts**: For each operation type
2. **Few-shot Learning**: Examples in prompt
3. **Context Injection**: Relevant information
4. **Temperature Adjustment**: Adjust by task type

### Adaptation Example

```python
# For file creation
system_prompt = """
CRITICAL FORMAT:
```create-file:path/to/file.ext
[content]
```
"""

# For listing
system_prompt = """
Use FILE LISTING in context.
Answer: "I see X files and Y folders"
"""
```

## Performance

### Factors That Affect Speed

1. **Model Size**: 7B is faster than 14B
2. **Prompt Size**: Larger prompts = slower
3. **Hardware**: CPU/GPU, available RAM
4. **Temperature**: Lower values are faster

### Optimizations in DuilioCode

- **Context Cache**: Avoids re-analyzing codebase
- **Streaming**: Responses appear faster
- **Simplified Prompt**: Fewer tokens = faster

## Troubleshooting

### Incorrect Responses
- Adjust temperature
- Improve system prompt
- Add more context

### Too Slow
- Use 7B model instead of 14B
- Reduce context size
- Check system resources

### Memory Errors
- Close other applications
- Use smaller model (7B)
- Reduce MAX_TOKENS

## Next Steps

- [FastAPI - Web Framework](09-fastapi.md)
- [How Chat Works](11-chat-functionality.md)
