"""
API Routes Module
=================
FastAPI router modules for each domain.
"""

from .health import router as health_router
try:
    from .chat.chat_router import router as chat_router
except ImportError:
    # Fallback to old chat.py if new structure not ready
    from .chat import router as chat_router
from .files import router as files_router
from .workspace import router as workspace_router
from .models import router as models_router

__all__ = [
    "health_router",
    "chat_router",
    "files_router",
    "workspace_router",
    "models_router",
]
