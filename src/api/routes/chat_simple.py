"""
Simple Chat Route - Clean Ollama/Qwen Connection
=================================================
Direct connection: Web → Ollama → Qwen → Response
No complex logic, no AI-powered detection, just pure prompt → response
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from services.ollama_service import OllamaService, get_ollama_service
from core.logger import get_logger

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# === Request Models ===

class SimpleChatRequest(BaseModel):
    """Simple chat request - just messages."""
    messages: List[Dict[str, str]] = Field(..., description="Conversation messages")
    model: str = Field(..., description="Model to use (required)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for generation")
    stream: bool = Field(default=False, description="Stream response")


# === Simple System Prompt ===

SIMPLE_SYSTEM_PROMPT = """You are DuilioCode, a helpful AI coding assistant.

You help users with:
- Writing and explaining code
- Debugging issues
- Creating files and projects
- Answering questions about programming

Be concise, clear, and helpful. Answer in the same language the user uses."""


# === Endpoints ===

@router.post("/simple")
async def chat_simple(
    request: SimpleChatRequest,
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Simple chat endpoint - direct connection to Ollama/Qwen.
    
    No complex logic, no AI-powered detection, just:
    - Take user message
    - Send to Ollama
    - Return response
    
    This is the CLEAN version that works like Ollama/Qwen in their pure state.
    """
    logger = get_logger()
    
    try:
        # Build prompt from messages
        prompt_parts = []
        system_prompt = SIMPLE_SYSTEM_PROMPT
        
        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Simple prompt: just join the conversation
        full_prompt = "\n".join(prompt_parts) + "\nAssistant:"
        
        # Model is required (validated by Pydantic)
        model = request.model
        
        # Stream if requested
        if request.stream:
            from fastapi.responses import StreamingResponse
            
            async def stream_generator():
                async for token in ollama.generate_stream(
                    prompt=full_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=request.temperature
                ):
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        
        # Generate response - SIMPLE, DIRECT
        result = await ollama.generate(
            prompt=full_prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=request.temperature,
            auto_select_model=False
        )
        
        # Get response content
        if not result or not hasattr(result, 'response') or not result.response:
            response_content = "I apologize, but I encountered an error generating a response. Please try again."
        else:
            response_content = result.response
        
        # Return simple response
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_content
                }
            }],
            "model": model,
            "usage": result.usage if hasattr(result, 'usage') else {}
        }
        
    except Exception as e:
        logger.error(f"Error in simple chat: {e}", context={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
