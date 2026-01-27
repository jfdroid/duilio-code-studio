"""
Rate Limiting Middleware
========================
Provides rate limiting for API endpoints to prevent abuse.
Uses slowapi (Flask-Limiter compatible) for FastAPI.
"""

from typing import Callable
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import get_settings

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour", "200/minute"],  # Generous defaults
    storage_uri="memory://",  # In-memory storage (can be upgraded to Redis)
    headers_enabled=True
)

# Rate limit configurations per endpoint
RATE_LIMITS = {
    "/api/chat": "30/minute",  # Chat endpoint - moderate limit
    "/api/generate": "20/minute",  # Code generation - lower limit (more expensive)
    "/api/tools/execute": "10/minute",  # Command execution - strict limit
    "/api/tools/refactor": "15/minute",  # Refactoring - moderate limit
    "/api/files": "100/minute",  # File operations - higher limit
    "/api/workspace": "50/minute",  # Workspace operations - moderate limit
    "default": "100/minute"  # Default for other endpoints
}


def get_rate_limit_for_path(path: str) -> str:
    """
    Get rate limit configuration for a given path.
    
    Args:
        path: Request path (e.g., "/api/chat")
    
    Returns:
        Rate limit string (e.g., "30/minute")
    """
    # Check exact matches first
    if path in RATE_LIMITS:
        return RATE_LIMITS[path]
    
    # Check prefix matches
    for endpoint, limit in RATE_LIMITS.items():
        if endpoint != "default" and path.startswith(endpoint):
            return limit
    
    # Return default
    return RATE_LIMITS.get("default", "100/minute")


def setup_rate_limiting(app):
    """
    Setup rate limiting for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add rate limit exception handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return app


def rate_limit_decorator(limit: str = None):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        limit: Rate limit string (e.g., "30/minute"). If None, uses default.
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        if limit:
            return limiter.limit(limit)(func)
        return func
    return decorator
