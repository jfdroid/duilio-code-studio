"""
Health Routes
=============
Server health check and status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from services.ollama_service import OllamaService, get_ollama_service


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check."""
    return {"status": "ok", "service": "DuilioCode Studio"}


@router.get("/ollama")
async def ollama_status(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """Check Ollama server status."""
    return await ollama.health_check()


@router.get("/full")
async def full_status(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """Full system status check."""
    ollama_status = await ollama.health_check()
    
    return {
        "status": "ok",
        "service": "DuilioCode Studio",
        "version": "2.0.0",
        "ollama": ollama_status,
        "features": {
            "code_generation": ollama_status.get("status") == "running",
            "file_operations": True,
            "workspace_management": True
        }
    }
