# DuilioCode Studio

AI-powered code assistant with direct file system access.

## Architecture

- **FastAPI**: Web framework (async, type-safe, perfect for Ollama)
- **Ollama**: Local LLM inference
- **Clean Architecture**: Separated concerns (services, routes, core)

## Key Features

- **Agent Mode**: Full CRUD operations on files
- **Chat Mode**: Simple conversation (centered layout)
- **PromptBuilder**: Clean, operation-specific prompts (no verbosity)

## Project Structure

```
src/
  api/
    routes/
      chat.py          # Main chat endpoint
      chat_simple.py   # Simple chat (no context)
      files.py         # File operations
  services/
    ollama_service.py  # Ollama API integration
    prompt_builder.py  # Clean prompt construction
    action_processor.py # Process create-file, modify-file, etc.
  core/
    config.py          # Settings
    logger.py          # Logging
```

## Best Practices Applied

Based on research (Gemini Code Assist, Cursor):
- Operation-specific prompts (CREATE, READ, UPDATE, DELETE, LIST)
- Direct imperative language
- Minimal verbosity
- Clear context structure
- File listing prioritized in context

## Usage

```bash
./start.sh
```

Access at `http://127.0.0.1:8080`
