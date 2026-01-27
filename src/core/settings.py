"""
Settings
========
Comprehensive application settings.
Centralizes all configuration in one place.
"""

import os
from typing import Optional, List
from pathlib import Path
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings.
    
    Loads from environment variables with sensible defaults.
    """
    
    # === Server Configuration ===
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # === Ollama Configuration ===
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_timeout: int = Field(default=300, description="Ollama request timeout (seconds)")
    ollama_default_model: str = Field(
        default="qwen2.5-coder:14b",
        description="Default Ollama model"
    )
    
    # === Cache Configuration ===
    cache_dir: str = Field(
        default=".cache/duiliocode",
        description="Cache directory"
    )
    cache_default_ttl: int = Field(
        default=3600,
        description="Default cache TTL (seconds)"
    )
    cache_size_limit_mb: int = Field(
        default=500,
        description="Cache size limit (MB)"
    )
    
    # === Workspace Configuration ===
    workspace_max_depth: int = Field(
        default=15,
        description="Maximum workspace traversal depth"
    )
    workspace_max_files: int = Field(
        default=50000,
        description="Maximum files to scan in workspace"
    )
    
    # === Codebase Analysis Configuration ===
    codebase_max_files: int = Field(
        default=100,
        description="Maximum files to analyze in codebase"
    )
    codebase_max_context_length: int = Field(
        default=8000,
        description="Maximum context length for codebase analysis"
    )
    
    # === Rate Limiting Configuration ===
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_chat: str = Field(
        default="30/minute",
        description="Chat endpoint rate limit"
    )
    rate_limit_generate: str = Field(
        default="20/minute",
        description="Generate endpoint rate limit"
    )
    
    # === LLM Configuration ===
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for LLM"
    )
    default_max_tokens: int = Field(
        default=4096,
        ge=1,
        le=32768,
        description="Default max tokens for LLM"
    )
    file_listing_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Temperature for file listing operations"
    )
    
    # === File Operations Configuration ===
    file_operations_enabled: bool = Field(
        default=True,
        description="Enable file operations (create, modify, delete)"
    )
    file_max_size_mb: int = Field(
        default=10,
        description="Maximum file size for operations (MB)"
    )
    
    # === Logging Configuration ===
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )
    
    # === Security Configuration ===
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials"
    )
    
    # === Performance Configuration ===
    max_concurrent_requests: int = Field(
        default=100,
        description="Maximum concurrent requests"
    )
    request_timeout: int = Field(
        default=300,
        description="Request timeout (seconds)"
    )
    
    # === Path Configuration ===
    project_root: Path = Field(
        default=Path(__file__).parent.parent.parent,
        description="Project root directory"
    )
    
    @validator("project_root", pre=True)
    def validate_project_root(cls, v):
        """Ensure project_root is a Path object."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
