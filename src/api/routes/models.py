"""
Models Routes
=============
AI model management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from services.ollama_service import OllamaService, get_ollama_service
from core.exceptions import OllamaConnectionError


from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
router = APIRouter(prefix="/api/models", tags=["Models"])


# Recommended models for code
RECOMMENDED_MODELS = [
    {
        "name": "qwen2.5-coder:14b",
        "display_name": "Qwen2.5-Coder 14B",
        "description": "Recommended - Best cost-benefit",
        "size": "9GB"
    },
    {
        "name": "qwen2.5-coder:7b",
        "display_name": "Qwen2.5-Coder 7B",
        "description": "Fast - Good for simple tasks",
        "size": "4.7GB"
    },
    {
        "name": "qwen2.5-coder:32b",
        "display_name": "Qwen2.5-Coder 32B",
        "description": "Advanced - Maximum quality",
        "size": "19GB"
    },
    {
        "name": "codellama:13b",
        "display_name": "CodeLlama 13B",
        "description": "Meta AI - Good for code completion",
        "size": "7GB"
    },
    {
        "name": "deepseek-coder:6.7b",
        "display_name": "DeepSeek Coder 6.7B",
        "description": "Lightweight - Specialized in code",
        "size": "4GB"
    },
]


@router.get("")
@router.get("/")
async def list_models(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    List all installed models.
    
    Returns installed models with metadata.
    """
    try:
        models = await ollama.list_models()
        
        return {
            "models": models,
            "default": "qwen2.5-coder:14b",
            "total": len(models)
        }
        
    except OllamaConnectionError as e:
        raise HTTPException(status_code=503, detail=e.detail)


@router.get("/recommended")
async def get_recommended_models(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Get recommended models for coding.
    
    Returns list with installation status.
    """
    try:
        installed = await ollama.list_models()
        installed_names = {m["name"] for m in installed}
        
        result = []
        for model in RECOMMENDED_MODELS:
            result.append({
                **model,
                "installed": model["name"] in installed_names
            })
        
        return {
            "recommended": result,
            "installed_count": sum(1 for m in result if m["installed"])
        }
        
    except OllamaConnectionError:
        # Return list without installation status
        return {
            "recommended": RECOMMENDED_MODELS,
            "installed_count": 0,
            "ollama_offline": True
        }


@router.get("/status")
async def get_model_status(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """
    Get Ollama and model status.
    
    Useful for checking if AI features are available.
    """
    status = await ollama.health_check()
    
    return {
        "ollama_running": status.get("status") == "running",
        "models_available": status.get("models_count", 0),
        "default_model_ready": status.get("default_model_available", False),
        "status": status
    }
