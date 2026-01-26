"""
DuilioCode Studio - Main Application
====================================
FastAPI application entry point.

Clean Architecture implementation with:
- Single Responsibility Principle: Each module has one job
- Open/Closed Principle: Easy to extend without modifying
- Dependency Inversion: Services injected via FastAPI Depends

Project Structure:
    src/
    ├── api/
    │   ├── main.py          # This file - Entry point
    │   ├── dependencies.py  # DI providers
    │   └── routes/          # API endpoints
    ├── core/
    │   ├── config.py        # Settings
    │   └── exceptions.py    # Custom exceptions
    ├── services/
    │   ├── ollama_service.py    # AI generation
    │   ├── file_service.py      # File operations
    │   └── workspace_service.py # Project management
    └── schemas/
        ├── requests.py      # Request models
        └── responses.py     # Response models
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Add parent directories to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import routes
from api.routes import (
    health_router,
    chat_router,
    files_router,
    workspace_router,
    models_router,
)
from api.routes.tools import router as tools_router
from api.routes.chat_simple import router as chat_simple_router

# Import services for lifecycle management
from services.ollama_service import get_ollama_service
from core.config import get_settings
from core.exceptions import DuilioException
from core.logger import get_logger

# Rate limiting (optional)
try:
    from middleware.rate_limiter import setup_rate_limiting
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    def setup_rate_limiting(app):
        return app


# === Application Lifecycle ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    
    Startup: Initialize services
    Shutdown: Cleanup resources
    """
    # Startup
    settings = get_settings()
    logger = get_logger()
    
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting")
    logger.info(f"Base directory: {settings.BASE_DIR}")
    
    # Check Ollama
    ollama = get_ollama_service()
    status = await ollama.health_check()
    if status.get("status") == "running":
        models_count = status.get('models_count', 0)
        logger.info(f"Ollama connected: {models_count} models available")
    else:
        logger.warning("Ollama offline - AI features unavailable")
    
    logger.info(f"Server starting on http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API docs available at http://{settings.HOST}:{settings.PORT}/docs")
    
    yield
    
    # Shutdown
    logger = get_logger()
    await ollama.close()
    logger.info("Server shutdown complete")


# === Application Factory ===

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # === CORS ===
    # Production: Restricted origins for security
    # Development: Allow all origins for local testing
    allowed_origins = ["*"] if settings.DEBUG else [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    )
    
    # === Security Headers ===
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # CSP can be added but may break some features
        # response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
    
    # === Exception Handlers ===
    
    @app.exception_handler(DuilioException)
    async def duilio_exception_handler(request: Request, exc: DuilioException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "detail": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )
    
    # === Rate Limiting ===
    if RATE_LIMITING_AVAILABLE:
        try:
            app = setup_rate_limiting(app)
            logger = get_logger()
            logger.info("Rate limiting enabled")
        except Exception as e:
            logger = get_logger()
            logger.warning(f"Rate limiting setup failed: {e}")
    
    # === Routes ===
    app.include_router(health_router)
    app.include_router(chat_router)  # Complex chat with all features
    app.include_router(chat_simple_router)  # Simple clean chat - direct Ollama connection
    app.include_router(files_router)
    app.include_router(workspace_router)
    app.include_router(models_router)
    app.include_router(tools_router)  # Git, Execute, Scaffold, Refactor, Docs, Security, Agent
    
    # === Static Files ===
    web_dir = settings.WEB_DIR
    templates_dir = settings.TEMPLATES_DIR
    
    if web_dir and web_dir.exists():
        # Mount static directories
        static_dir = web_dir / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Serve index.html at root
        @app.get("/", response_class=HTMLResponse)
        async def serve_index():
            """Serve the web interface."""
            index_file = templates_dir / "index.html"
            if index_file.exists():
                return HTMLResponse(content=index_file.read_text())
            return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><title>DuilioCode Studio</title></head>
                <body style="font-family: sans-serif; padding: 40px;">
                    <h1>DuilioCode Studio</h1>
                    <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
                </body>
                </html>
""")
    
    return app


# === Application Instance ===
app = create_app()


# === Direct Run Support ===
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
