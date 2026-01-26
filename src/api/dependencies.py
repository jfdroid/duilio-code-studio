"""
Dependency Injection
====================
FastAPI dependency providers.
"""

from functools import lru_cache

from services.ollama_service import OllamaService, get_ollama_service
from services.file_service import FileService, get_file_service
from services.workspace_service import WorkspaceService, get_workspace_service
from core.config import Settings, get_settings


# Re-export for convenience
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
__all__ = [
    "get_settings",
    "get_ollama_service",
    "get_file_service",
    "get_workspace_service",
]
