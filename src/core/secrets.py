"""
Secrets Management
=================
Secure handling of API keys, tokens, and sensitive configuration.
"""

import os
from typing import Optional
from pathlib import Path
from functools import lru_cache


class SecretsManager:
    """
    Manages secrets and sensitive configuration.
    
    Priority order:
    1. Environment variables
    2. .env file (if exists)
    3. Default values (if safe)
    """
    
    @staticmethod
    @lru_cache()
    def get_secret(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """
        Get secret value from environment or .env file.
        
        Args:
            key: Secret key name
            default: Default value if not found (only if not required)
            required: If True, raise error if secret not found
            
        Returns:
            Secret value or default
            
        Raises:
            ValueError: If required secret is not found
        """
        # Try environment variable first
        value = os.getenv(key)
        
        if value:
            return value
        
        # Try .env file
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        env_key, env_value = line.split("=", 1)
                        env_key = env_key.strip()
                        env_value = env_value.strip().strip('"').strip("'")
                        if env_key == key:
                            return env_value
        
        # Check if required
        if required:
            raise ValueError(f"Required secret '{key}' not found in environment or .env file")
        
        return default
    
    @staticmethod
    def get_ollama_api_key() -> Optional[str]:
        """Get Ollama API key if configured."""
        return SecretsManager.get_secret("OLLAMA_API_KEY", required=False)
    
    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """Get OpenAI API key if configured."""
        return SecretsManager.get_secret("OPENAI_API_KEY", required=False)
    
    @staticmethod
    def get_database_url() -> Optional[str]:
        """Get database connection URL if configured."""
        return SecretsManager.get_secret("DATABASE_URL", required=False)
    
    @staticmethod
    def get_redis_url() -> Optional[str]:
        """Get Redis connection URL if configured."""
        return SecretsManager.get_secret("REDIS_URL", required=False)
    
    @staticmethod
    def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
        """
        Mask secret value for logging.
        
        Args:
            value: Secret value to mask
            visible_chars: Number of characters to show at start
            
        Returns:
            Masked string (e.g., "sk-...xxxx")
        """
        if not value:
            return "***"
        
        if len(value) <= visible_chars:
            return "***"
        
        return value[:visible_chars] + "..." + "*" * min(8, len(value) - visible_chars)
