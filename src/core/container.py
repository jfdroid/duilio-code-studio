"""
Dependency Injection Container
==============================
Centralized dependency injection using FastAPI Depends.
Provides a clean, testable way to manage service dependencies.

Usage:
    from core.container import get_ollama_service, get_workspace_service
    
    @router.get("/endpoint")
    async def endpoint(
        ollama: OllamaService = Depends(get_ollama_service),
        workspace: WorkspaceService = Depends(get_workspace_service)
    ):
        ...
"""

import sys
from pathlib import Path
from functools import lru_cache
from typing import Optional
from fastapi import Depends

# Add parent directory to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from services.ollama_service import OllamaService, get_ollama_service as _get_ollama_service
from services.workspace_service import WorkspaceService, get_workspace_service as _get_workspace_service
from services.file_service import FileService, get_file_service as _get_file_service
from services.cache_service import CacheService, get_cache_service as _get_cache_service
from services.linguistic_analyzer import LinguisticAnalyzer, get_linguistic_analyzer as _get_linguistic_analyzer
from services.intent_detector import IntentDetector, get_intent_detector as _get_intent_detector
from services.prompt_builder import PromptBuilder
from services.system_info import SystemInfoService, get_system_info_service as _get_system_info_service
from services.action_processor import ActionProcessor, get_action_processor as _get_action_processor
from services.user_preferences import UserPreferencesService, get_user_preferences_service as _get_user_preferences_service
from services.prompt_examples import PromptExamplesService, get_prompt_examples_service as _get_prompt_examples_service
from core.config import Settings, get_settings as _get_settings
from core.logger import get_logger as _get_logger


# === Configuration ===

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (singleton, cached).
    
    Returns:
        Settings instance
    """
    return _get_settings()


# === Core Services ===

def get_ollama_service() -> OllamaService:
    """
    Get Ollama service instance (singleton).
    
    Returns:
        OllamaService instance
    """
    return _get_ollama_service()


def get_workspace_service() -> WorkspaceService:
    """
    Get workspace service instance (singleton).
    
    Returns:
        WorkspaceService instance
    """
    return _get_workspace_service()


def get_file_service(ollama_service: Optional[OllamaService] = None) -> FileService:
    """
    Get file service instance (singleton).
    
    Args:
        ollama_service: Optional Ollama service for AI features
        
    Returns:
        FileService instance
    """
    if ollama_service is None:
        ollama_service = get_ollama_service()
    return _get_file_service(ollama_service=ollama_service)


def get_cache_service() -> CacheService:
    """
    Get cache service instance (singleton).
    
    Returns:
        CacheService instance
    """
    return _get_cache_service()


# === Analysis Services ===

def get_linguistic_analyzer() -> LinguisticAnalyzer:
    """
    Get linguistic analyzer instance (singleton).
    
    Returns:
        LinguisticAnalyzer instance
    """
    return _get_linguistic_analyzer()


def get_intent_detector() -> IntentDetector:
    """
    Get intent detector instance (singleton).
    
    Returns:
        IntentDetector instance
    """
    return _get_intent_detector()


def get_system_info_service() -> SystemInfoService:
    """
    Get system info service instance (singleton).
    
    Returns:
        SystemInfoService instance
    """
    return _get_system_info_service()


# === Action Services ===

def get_action_processor(ollama_service: Optional[OllamaService] = None) -> ActionProcessor:
    """
    Get action processor instance (singleton).
    
    Args:
        ollama_service: Optional Ollama service for AI features
        
    Returns:
        ActionProcessor instance
    """
    if ollama_service is None:
        ollama_service = get_ollama_service()
    return _get_action_processor(ollama_service=ollama_service)


# === User Services ===

def get_user_preferences_service() -> UserPreferencesService:
    """
    Get user preferences service instance (singleton).
    
    Returns:
        UserPreferencesService instance
    """
    return _get_user_preferences_service()


def get_prompt_examples_service() -> PromptExamplesService:
    """
    Get prompt examples service instance (singleton).
    
    Returns:
        PromptExamplesService instance
    """
    return _get_prompt_examples_service()


# === Utility Services ===

def get_logger():
    """
    Get logger instance.
    
    Returns:
        Logger instance
    """
    return _get_logger()


def get_metrics_collector():
    """
    Get metrics collector instance (singleton).
    
    Returns:
        MetricsCollector instance
    """
    from services.metrics import get_metrics_collector as _get_metrics_collector
    try:
        return _get_metrics_collector()
    except ImportError:
        # Fallback to core.metrics if services.metrics doesn't exist
        from core.metrics import get_metrics_collector as _get_metrics_collector
        return _get_metrics_collector()


# === FastAPI Dependency Providers ===
# These can be used directly with Depends() in route handlers

# Example usage in routes:
# @router.get("/endpoint")
# async def endpoint(
#     ollama: OllamaService = Depends(get_ollama_service),
#     workspace: WorkspaceService = Depends(get_workspace_service),
#     cache: CacheService = Depends(get_cache_service)
# ):
#     ...
