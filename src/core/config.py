"""
Configuration Settings
======================
Comprehensive centralized configuration using Pydantic Settings.
Supports environment variables and .env files.

Expanded from original config.py to include all application settings.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, validator

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Comprehensive application settings with environment variable support.
    
    All settings can be overridden via environment variables
    or a .env file in the project root.
    """
    
    # === Application ===
    APP_NAME: str = "DuilioCode Studio"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Local AI coding assistant with full file system access"
    DEBUG: bool = False
    
    # === Server ===
    HOST: str = Field(default="127.0.0.1", description="Server host")
    PORT: int = Field(default=8080, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")
    
    # === Paths ===
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    WEB_DIR: Optional[Path] = None
    TEMPLATES_DIR: Optional[Path] = None
    WORKSPACE_FILE: Optional[Path] = None
    DATA_DIR: Optional[Path] = None  # For user preferences, conversation history, etc.
    
    # === Ollama ===
    OLLAMA_HOST: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    OLLAMA_TIMEOUT: float = Field(default=300.0, description="Ollama request timeout (seconds)")
    DEFAULT_MODEL: str = Field(default="qwen2.5-coder:14b", description="Default Ollama model")
    FALLBACK_MODEL: str = Field(default="qwen2.5-coder:7b", description="Fallback Ollama model")
    
    # === AI Generation ===
    MAX_TOKENS: int = Field(default=4096, ge=1, le=32768, description="Maximum tokens for generation")
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="Default temperature")
    FILE_LISTING_TEMPERATURE: float = Field(default=0.2, ge=0.0, le=2.0, description="Temperature for file listing")
    
    # === File Operations ===
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size (bytes)")
    CREATE_BACKUPS: bool = Field(default=True, description="Create backups before file operations")
    FILE_OPERATIONS_ENABLED: bool = Field(default=True, description="Enable file operations")
    
    # === Cache Configuration ===
    CACHE_DIR: str = Field(default=".cache/duiliocode", description="Cache directory")
    CACHE_DEFAULT_TTL: int = Field(default=3600, description="Default cache TTL (seconds)")
    CACHE_SIZE_LIMIT_MB: int = Field(default=500, description="Cache size limit (MB)")
    
    # === Workspace Configuration ===
    WORKSPACE_MAX_DEPTH: int = Field(default=15, description="Maximum workspace traversal depth")
    WORKSPACE_MAX_FILES: int = Field(default=50000, description="Maximum files to scan")
    
    # === Codebase Analysis ===
    CODEBASE_MAX_FILES: int = Field(default=100, description="Maximum files to analyze")
    CODEBASE_MAX_CONTEXT_LENGTH: int = Field(default=8000, description="Maximum context length")
    
    # === Rate Limiting ===
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_CHAT: str = Field(default="30/minute", description="Chat endpoint rate limit")
    RATE_LIMIT_GENERATE: str = Field(default="20/minute", description="Generate endpoint rate limit")
    
    # === Logging ===
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: Optional[Path] = Field(default=None, description="Log file path (None = console only)")
    LOG_JSON: bool = Field(default=True, description="Use structured JSON logging")
    
    # === Security ===
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS allowed origins")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow CORS credentials")
    
    # === Performance ===
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, description="Maximum concurrent requests")
    REQUEST_TIMEOUT: int = Field(default=300, description="Request timeout (seconds)")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set derived paths
        self.WEB_DIR = self.BASE_DIR / "web"
        self.TEMPLATES_DIR = self.WEB_DIR / "templates"
        self.WORKSPACE_FILE = self.BASE_DIR / ".duilio_workspace.json"
        self.DATA_DIR = Path.home() / ".duilio" / "data"
        # Ensure data directory exists
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache for performance - settings are loaded once.
    """
    return Settings()
