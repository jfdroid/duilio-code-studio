"""
Chat Router
===========
Main router for chat endpoints.
Refactored from chat.py to improve maintainability.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional

# Add parent directories to path for imports
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from .chat_handler import ChatHandler
from .generate_handler import GenerateHandler
from .codebase_endpoints import CodebaseEndpoints
from services.ollama_service import OllamaService
from services.workspace_service import WorkspaceService
from services.user_preferences import UserPreferencesService
from services.prompt_examples import PromptExamplesService
from core.container import (
    get_ollama_service,
    get_workspace_service,
    get_user_preferences_service,
    get_prompt_examples_service
)
from core.logger import get_logger

# Rate limiting
try:
    from middleware.rate_limiter import rate_limit_decorator
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    def rate_limit_decorator(limit: str = None):
        def decorator(func):
            return func
        return decorator

router = APIRouter(prefix="/api", tags=["Chat"])

# Initialize handlers
_chat_handler: ChatHandler = None
_generate_handler: GenerateHandler = None
_codebase_endpoints: CodebaseEndpoints = None


def get_chat_handler() -> ChatHandler:
    """Get or create ChatHandler instance."""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler()
    return _chat_handler


def get_generate_handler() -> GenerateHandler:
    """Get or create GenerateHandler instance."""
    global _generate_handler
    if _generate_handler is None:
        _generate_handler = GenerateHandler()
    return _generate_handler


def get_codebase_endpoints() -> CodebaseEndpoints:
    """Get or create CodebaseEndpoints instance."""
    global _codebase_endpoints
    if _codebase_endpoints is None:
        _codebase_endpoints = CodebaseEndpoints()
    return _codebase_endpoints


# === Request Models ===
from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """Request for code/text generation."""
    prompt: str = Field(..., description="The prompt")
    model: str = Field(..., description="Model to use (required)")
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    workspace_path: Optional[str] = Field(default=None, description="Path to analyze for context")
    include_codebase: bool = Field(default=True, description="Include codebase analysis in context")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: list = Field(..., description="Message history")
    model: str = Field(..., description="Model to use (required)")
    workspace_path: Optional[str] = Field(default=None, description="Workspace path for context")
    temperature: float = Field(default=0.7)
    stream: bool = Field(default=False)


class AnalyzeCodebaseRequest(BaseModel):
    """Request to analyze a codebase."""
    path: str = Field(..., description="Path to the codebase")
    max_files: int = Field(default=100, description="Maximum files to analyze")


# === Endpoints ===

@router.post("/generate")
@rate_limit_decorator("20/minute")
async def generate(
    request: GenerateRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    workspace: WorkspaceService = Depends(get_workspace_service),
    user_prefs: UserPreferencesService = Depends(get_user_preferences_service),
    examples: PromptExamplesService = Depends(get_prompt_examples_service)
) -> Dict[str, Any]:
    """
    Generate code or text response with intelligent context.
    
    **Features**:
    - Intelligent model selection based on prompt type
    - Automatic codebase analysis for context
    - Smart prompt classification (code vs general)
    - Few-shot learning from examples
    - User preference learning
    
    **Request Body**:
    - `prompt` (required): The user's prompt/question
    - `model` (required): Model name to use (e.g., "qwen2.5-coder:14b")
    - `system_prompt` (optional): Custom system prompt
    - `context` (optional): Additional context
    - `workspace_path` (optional): Path to workspace for codebase analysis
    - `include_codebase` (default: true): Include codebase analysis in context
    - `temperature` (default: 0.7): Sampling temperature (0.0-2.0)
    - `max_tokens` (default: 4096): Maximum tokens to generate
    
    **Response**:
    ```json
    {
      "response": "Generated code or text",
      "model": "qwen2.5-coder:14b",
      "tokens": 150,
      "duration_ms": 1234.5
    }
    ```
    
    **Example Request**:
    ```json
    {
      "prompt": "Create a React component for a button",
      "model": "qwen2.5-coder:14b",
      "workspace_path": "/path/to/project",
      "temperature": 0.7
    }
    ```
    """
    handler = get_generate_handler()
    return await handler.handle(
        request=request,
        ollama=ollama,
        workspace=workspace,
        user_prefs=user_prefs,
        examples=examples
    )


@router.post("/chat")
@rate_limit_decorator("30/minute")
async def chat(
    request: ChatRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Chat completion endpoint with intelligent context and CRUD capabilities.
    
    **Features**:
    - Automatic codebase analysis for context
    - Conversation history handling
    - Smart model selection
    - Streaming support (when `stream=true`)
    - CRUD operation detection (create, read, update, delete, list)
    - Advanced linguistic analysis (verbs, connectors, intent)
    - File system access and operations
    - System information integration
    
    **Request Body**:
    - `messages` (required): List of conversation messages
      ```json
      [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "List files in current directory"}
      ]
      ```
    - `model` (required): Model name (e.g., "qwen2.5-coder:14b")
    - `workspace_path` (optional): Workspace path for file operations
    - `temperature` (default: 0.7): Response creativity (0.0-2.0)
    - `stream` (default: false): Enable streaming response
    
    **Response**:
    ```json
    {
      "response": "AI-generated response",
      "model": "qwen2.5-coder:14b",
      "tokens": 200,
      "actions": [
        {
          "type": "list_files",
          "path": "/path/to/workspace"
        }
      ],
      "duration_ms": 2345.6
    }
    ```
    
    **Example Request**:
    ```json
    {
      "messages": [
        {"role": "user", "content": "Create a file called test.txt with 'Hello World'"}
      ],
      "model": "qwen2.5-coder:14b",
      "workspace_path": "/path/to/project",
      "temperature": 0.7
    }
    ```
    
    **CRUD Operations Supported**:
    - **Create**: Files, directories, projects
    - **Read**: File content, directory listings
    - **Update**: Modify existing files
    - **Delete**: Files and directories
    - **List**: Files and folders in workspace
    """
    handler = get_chat_handler()
    return await handler.handle(
        request=request,
        ollama=ollama,
        workspace=workspace
    )


@router.post("/generate/stream")
@rate_limit_decorator("20/minute")
async def generate_stream(
    request: GenerateRequest,
    ollama: OllamaService = Depends(get_ollama_service)
) -> StreamingResponse:
    """
    Stream code generation token by token.
    
    Returns Server-Sent Events (SSE) stream with tokens as they are generated.
    Useful for real-time UI updates.
    
    **Request Body**: Same as `/generate` endpoint
    
    **Response**: `text/event-stream` with format:
    ```
    data: token1
    data: token2
    data: [DONE]
    ```
    
    **Example**:
    ```javascript
    const response = await fetch('/api/generate/stream', {
      method: 'POST',
      body: JSON.stringify({
        prompt: "Create a function",
        model: "qwen2.5-coder:14b"
      })
    });
    
    const reader = response.body.getReader();
    // Process stream...
    ```
    """
    async def stream_generator():
        async for token in ollama.generate_stream(
            prompt=request.prompt,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )


@router.post("/recommend-model")
async def recommend_model(
    prompt: str,
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Get recommended model for a given prompt.
    
    Uses intelligent classification to suggest the best model based on:
    - Prompt content analysis
    - Code vs general text detection
    - Available models
    - User preferences
    
    **Request Body**:
    - `prompt` (required): The prompt to analyze
    
    **Response**:
    ```json
    {
      "recommended_model": "qwen2.5-coder:14b",
      "is_code_related": true,
      "category": "code_generation",
      "confidence": 0.95,
      "reason": "Detected code patterns: function, class",
      "keywords_found": ["function", "class", "def"]
    }
    ```
    
    **Example Request**:
    ```json
    {
      "prompt": "Create a Python function to calculate factorial"
    }
    ```
    """
    try:
        from services.prompt_classifier import classify_prompt
        models = await ollama.list_models()
        classification = classify_prompt(prompt, models)
        
        return {
            "recommended_model": classification.recommended_model,
            "is_code_related": classification.is_code_related,
            "category": classification.category.value,
            "confidence": classification.confidence,
            "reason": classification.reasoning,
            "keywords_found": classification.keywords_found
        }
    except Exception as e:
        return {
            "recommended_model": "qwen2.5-coder:14b",
            "is_code_related": True,
            "reason": f"Error: {str(e)}, using default",
            "category": "code_generation"
        }


# === Codebase Analysis Endpoints ===

@router.post("/analyze-codebase")
async def analyze_codebase_endpoint(
    request: AnalyzeCodebaseRequest,
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Analyze a codebase and return structured information.
    
    Performs comprehensive analysis of a codebase including:
    - File tree structure
    - Language distribution
    - Dependencies detection
    - Entry points identification
    - AI-ready context generation
    
    **Request Body**:
    - `path` (required): Path to the codebase directory
    - `max_files` (default: 100): Maximum files to analyze
    
    **Response**:
    ```json
    {
      "file_tree": {...},
      "languages": {
        "python": 45,
        "javascript": 30
      },
      "dependencies": ["react", "fastapi"],
      "entry_points": ["main.py", "index.js"],
      "context": "AI-ready context string..."
    }
    ```
    
    **Example Request**:
    ```json
    {
      "path": "/path/to/project",
      "max_files": 200
    }
    ```
    """
    endpoints = get_codebase_endpoints()
    return await endpoints.analyze_codebase(request=request, ollama=ollama)


@router.get("/codebase-context")
async def get_codebase_context_endpoint(
    path: str,
    refresh: bool = False,
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Get AI-ready context for a codebase.
    
    Returns cached or fresh codebase analysis for use in AI prompts.
    Uses intelligent caching for performance optimization.
    
    **Query Parameters**:
    - `path` (required): Path to the codebase directory
    - `refresh` (default: false): Force refresh, bypass cache
    
    **Response**:
    ```json
    {
      "context": "Structured codebase context...",
      "file_count": 150,
      "languages": ["python", "javascript"],
      "cached": true,
      "cache_age_seconds": 3600
    }
    ```
    
    **Example Request**:
    ```
    GET /api/codebase-context?path=/path/to/project&refresh=false
    ```
    """
    endpoints = get_codebase_endpoints()
    return await endpoints.get_codebase_context(path=path, refresh=refresh, ollama=ollama)
