"""
Chat Routes
===========
AI code generation and chat endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from services.ollama_service import OllamaService, get_ollama_service
from services.workspace_service import WorkspaceService, get_workspace_service


router = APIRouter(prefix="/api", tags=["Chat"])


# === Request Models ===

class GenerateRequest(BaseModel):
    """Request for code/text generation."""
    prompt: str = Field(..., description="The prompt")
    model: Optional[str] = Field(default=None, description="Model to use (None for auto-selection)")
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32768)


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: list = Field(..., description="Message history")
    model: str = Field(default="qwen2.5-coder:14b")
    temperature: float = Field(default=0.7)
    stream: bool = Field(default=False)


# === Endpoints ===

@router.post("/generate")
async def generate(
    request: GenerateRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    workspace: WorkspaceService = Depends(get_workspace_service)
) -> Dict[str, Any]:
    """
    Generate code or text response.
    
    Uses the specified model (or default) to generate a response.
    Includes workspace context when available.
    """
    try:
        # Get project context
        project_context = workspace.get_project_context()
        context = request.context
        
        if project_context.get("has_workspace"):
            context_addition = f"\nCurrent project: {project_context.get('root_path', '')}"
            if project_context.get("languages"):
                context_addition += f"\nLanguages: {', '.join(project_context['languages'])}"
            context = f"{context or ''}{context_addition}"
        
        result = await ollama.generate(
            prompt=request.prompt,
            model=request.model,
            system_prompt=request.system_prompt,
            context=context,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "response": result.response,
            "model": result.model,
            "done": result.done,
            "total_duration": result.total_duration,
            "eval_count": result.eval_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(
    request: ChatRequest,
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Chat completion endpoint.
    
    Supports streaming responses when stream=true.
    """
    try:
        # Convert messages to prompt
        messages = request.messages
        prompt_parts = []
        system_prompt = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt = "\n".join(prompt_parts) + "\nAssistant:"
        
        if request.stream:
            async def stream_generator():
                async for token in ollama.generate_stream(
                    prompt=prompt,
                    model=request.model,
                    system_prompt=system_prompt,
                    temperature=request.temperature
                ):
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        
        result = await ollama.generate(
            prompt=prompt,
            model=request.model,
            system_prompt=system_prompt,
            temperature=request.temperature
        )
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": result.response
                }
            }],
            "model": result.model
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stream")
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
    Analyzes the prompt and suggests the best model.
    """
    try:
        models = await ollama.list_models()
        model, is_code, reason = OllamaService.get_recommended_model(prompt, models)
        
        return {
            "recommended_model": model,
            "is_code_related": is_code,
            "reason": reason,
            "prompt_type": "code" if is_code else "general"
        }
    except Exception as e:
        return {
            "recommended_model": "qwen2.5-coder:14b",
            "is_code_related": True,
            "reason": f"Error: {str(e)}, using default",
            "prompt_type": "code"
        }
