"""
Retry Utility
=============
Provides retry logic with exponential backoff for resilient operations.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import Callable, TypeVar, Optional, List, Any
from functools import wraps

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.logger import get_logger
except ImportError:
    # Fallback if running from different context
    try:
        from core.logger import get_logger
    except ImportError:
        # Minimal logger if all else fails
        import logging
        logging.basicConfig(level=logging.INFO)
        get_logger = lambda: logging.getLogger(__name__)

T = TypeVar('T')
logger = get_logger()


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[List[Exception]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Decorator for async functions with retry logic and exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        retry_on: List of exception types to retry on (None = all exceptions)
        on_retry: Optional callback function called on each retry (attempt_num, exception)
    
    Example:
        @retry_async(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            # Operation that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if retry_on and not any(isinstance(e, exc_type) for exc_type in retry_on):
                        raise
                    
                    # Don't retry on last attempt
                    if attempt >= max_attempts:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    jitter = delay * 0.1 * (time.time() % 1)
                    delay += jitter
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}",
                        context={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "next_retry_delay": delay,
                            "attempt": attempt
                        }
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception:
                            pass  # Don't fail on callback error
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # All attempts failed
            logger.error(
                f"All {max_attempts} attempts failed for {func.__name__}",
                context={
                    "error": str(last_exception),
                    "error_type": type(last_exception).__name__ if last_exception else None
                }
            )
            raise RetryError(
                f"Function {func.__name__} failed after {max_attempts} attempts. "
                f"Last error: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[List[Exception]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Decorator for sync functions with retry logic and exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        retry_on: List of exception types to retry on (None = all exceptions)
        on_retry: Optional callback function called on each retry (attempt_num, exception)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if retry_on and not any(isinstance(e, exc_type) for exc_type in retry_on):
                        raise
                    
                    # Don't retry on last attempt
                    if attempt >= max_attempts:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    jitter = delay * 0.1 * (time.time() % 1)
                    delay += jitter
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}",
                        context={
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "next_retry_delay": delay,
                            "attempt": attempt
                        }
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception:
                            pass  # Don't fail on callback error
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # All attempts failed
            logger.error(
                f"All {max_attempts} attempts failed for {func.__name__}",
                context={
                    "error": str(last_exception),
                    "error_type": type(last_exception).__name__ if last_exception else None
                }
            )
            raise RetryError(
                f"Function {func.__name__} failed after {max_attempts} attempts. "
                f"Last error: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator
