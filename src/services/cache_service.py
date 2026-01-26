"""
Cache Service
=============
Sistema de cache usando diskcache para otimização de performance.

BigO:
- Get: O(1) com hash lookup
- Set: O(1) com hash insert
- Delete: O(1) com hash delete
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Optional, Dict
from functools import wraps
import diskcache as dc


class CacheService:
    """
    Serviço de cache usando diskcache.
    
    Funcionalidades:
    - Cache persistente em disco
    - TTL (Time To Live) automático
    - Limpeza automática de entradas expiradas
    - Serialização automática de objetos Python
    """
    
    def __init__(self, cache_dir: str = ".cache/duiliocode", default_ttl: int = 3600):
        """
        Inicializa serviço de cache.
        
        Args:
            cache_dir: Diretório para cache em disco
            default_ttl: TTL padrão em segundos (1 hora)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        
        # Criar cache diskcache
        self.cache = dc.Cache(str(self.cache_dir), size_limit=500 * 1024 * 1024)  # 500MB
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Cria chave de cache a partir de argumentos.
        
        Args:
            prefix: Prefixo da chave
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            Chave hash única
        """
        # Serializar argumentos
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        
        # Gerar hash
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Stored value or None if not found/expired
        """
        try:
            return self.cache.get(key, default=None)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (None = use default)
            
        Returns:
            True if stored successfully
        """
        try:
            ttl = ttl or self.default_ttl
            self.cache.set(key, value, expire=ttl)
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """
        Remove entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if removed successfully
        """
        try:
            return self.cache.delete(key)
        except Exception:
            return False
    
    def clear(self, prefix: str = None) -> int:
        """
        Clear cache.
        
        Args:
            prefix: If provided, clear only keys with prefix
            
        Returns:
            Number of entries removed
        """
        if prefix:
            # Limpar apenas chaves com prefixo
            count = 0
            for key in list(self.cache.iterkeys()):
                if key.startswith(prefix):
                    self.cache.delete(key)
                    count += 1
            return count
        else:
            # Limpar tudo
            count = len(self.cache)
            self.cache.clear()
            return count
    
    def get_or_set(self, key: str, factory: callable, ttl: int = None) -> Any:
        """
        Get value from cache or execute factory and store.
        
        Args:
            key: Cache key
            factory: Function that returns value if not found
            ttl: Time to live in seconds
            
        Returns:
            Cache value or factory result
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Executar factory e armazenar
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def stats(self) -> Dict[str, Any]:
        """
        Return cache statistics.
        
        Returns:
            Dict with statistics
        """
        try:
            volume = self.cache.volume()
            return {
                'cache_dir': str(self.cache_dir),
                'volume_bytes': volume,
                'volume_mb': volume / (1024 * 1024),
                'count': len(self.cache),
                'default_ttl': self.default_ttl
            }
        except Exception:
            return {
                'cache_dir': str(self.cache_dir),
                'error': 'Could not get stats'
            }


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create CacheService instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(prefix: str = "cache", ttl: int = None):
    """
    Decorator to cache function result.
    
    Args:
        prefix: Prefix for cache key
        ttl: Time to live in seconds
        
    Example:
        @cached(prefix="codebase_analysis", ttl=3600)
        def analyze_codebase(path: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()
            key = cache._make_key(prefix, *args, **kwargs)
            
            # Tentar obter do cache
            value = cache.get(key)
            if value is not None:
                return value
            
            # Executar função e cachear
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator
