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
    
    Features:
    - Intelligent model selection
    - Automatic codebase analysis
    - Smart prompt classification
    - Few-shot learning from examples
    - User preference learning
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
    Chat completion endpoint with intelligent context.
    
    Features:
    - Automatic codebase analysis
    - Conversation history handling
    - Smart model selection
    - Streaming support
    - CRUD operation detection
    - Linguistic analysis
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
    """Stream code generation token by token."""
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
    Uses intelligent classification to suggest the best model.
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
    
    Returns:
    - File tree structure
    - Language distribution
    - Dependencies
    - Entry points
    - AI-ready context
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
    Uses caching for performance.
    """
    endpoints = get_codebase_endpoints()
    return await endpoints.get_codebase_context(path=path, refresh=refresh, ollama=ollama)
