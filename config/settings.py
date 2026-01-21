"""
DuilioCode - Configuration Settings
====================================
Centralized configuration for all components.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # === Project Info ===
    PROJECT_NAME: str = "DuilioCode"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Local AI for code generation, chat and file editing"
    
    # === Server ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False  # Disable auto-reload to prevent interruptions during model loading
    
    # === Paths ===
    BASE_DIR: Path = Path(__file__).parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    DATA_DIR: Path = BASE_DIR / "data"
    
    # === Ollama (Chat/Code) ===
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "llava"
    OLLAMA_CODE_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_TIMEOUT: int = 120
    
    # === Generation Settings ===
    DEFAULT_STEPS: int = 20
    QUICK_STEPS: int = 12
    MAX_SIZE: int = 512
    MIN_SIZE: int = 256
    GUIDANCE_SCALE: float = 7.5
    
    # === Memory Optimization ===
    ENABLE_ATTENTION_SLICING: bool = True
    ENABLE_VAE_SLICING: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Singleton instance for easy import
settings = get_settings()
