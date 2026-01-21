"""
Configuration Settings
======================
Centralized configuration using Pydantic Settings.
Supports environment variables and .env files.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables
    or a .env file in the project root.
    """
    
    # === Application ===
    APP_NAME: str = "DuilioCode Studio"
    APP_VERSION: str = "2.0.0"
    APP_DESCRIPTION: str = "Local AI coding assistant with full file system access"
    DEBUG: bool = False
    
    # === Server ===
    HOST: str = "127.0.0.1"
    PORT: int = 8080
    
    # === Paths ===
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    WEB_DIR: Optional[Path] = None
    TEMPLATES_DIR: Optional[Path] = None
    WORKSPACE_FILE: Optional[Path] = None
    DATA_DIR: Optional[Path] = None  # For user preferences, conversation history, etc.
    
    # === Ollama ===
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: float = 300.0  # 5 minutes for large models
    DEFAULT_MODEL: str = "qwen2.5-coder:14b"
    FALLBACK_MODEL: str = "qwen2.5-coder:7b"
    
    # === AI Generation ===
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # === File Operations ===
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    CREATE_BACKUPS: bool = True
    
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


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache for performance - settings are loaded once.
    """
    return Settings()
