"""
Context Builder
===============
Builds codebase context with proper caching.
Replaces global _codebase_cache with CacheService.
"""

import sys
from typing import Optional
from pathlib import Path

# Add parent directories to path for imports
src_path = Path(__file__).parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from services.codebase_analyzer import CodebaseAnalyzer
from services.cache_service import get_cache_service
from core.logger import get_logger


def get_codebase_context(
    path: str, 
    force_refresh: bool = False, 
    query: str = "", 
    ollama_service=None
) -> str:
    """
    Get or generate codebase context with caching.
    
    Uses CacheService instead of global dict for:
    - Thread safety
    - TTL support
    - Size limits
    - Persistence
    
    Args:
        path: Codebase path
        force_refresh: Force refresh cache
        query: Query for relevance scoring
        ollama_service: Optional Ollama service for AI-powered analysis
        
    Returns:
        Codebase context string
    """
    logger = get_logger()
    cache = get_cache_service()
    
    cache_key = f"codebase_context:{path}:{query}"
    
    # Check cache (unless force refresh)
    if not force_refresh:
        cached_context = cache.get(cache_key)
        if cached_context is not None:
            logger.debug(f"Cache hit for codebase context: {path}")
            return cached_context
    
    try:
        analyzer = CodebaseAnalyzer(path, ollama_service=ollama_service)
        # IMPORTANT:
        # - Chat needs fresh context so the model can accurately MODIFY recently created/edited files.
        # - Passing `query` into analysis enables relevance scoring.
        analysis = analyzer.analyze(max_files=100, query=query, use_cache=not force_refresh)
        context = analyzer.get_context_for_ai(analysis, max_length=8000, query=query)
        
        # Cache with TTL (1 hour)
        cache.set(cache_key, context, ttl=3600)
        
        logger.info(f"Cached codebase context: {path} ({len(context)} chars)")
        return context
    except Exception as e:
        error_msg = f"[Error analyzing codebase: {str(e)}]"
        logger.error(f"Error building codebase context: {e}", exc_info=True)
        return error_msg
