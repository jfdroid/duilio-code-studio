"""
Performance Metrics
===================
Performance monitoring and metrics collection for the application.

Features:
- Operation timing
- Request/response metrics
- Error tracking
- Performance logging
"""

import time
from functools import wraps
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from core.logger import get_logger


@dataclass
class Metric:
    """Single performance metric."""
    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates performance metrics.
    
    Thread-safe metrics collection with automatic aggregation.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self._metrics: list[Metric] = []
        self._aggregated: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_duration": 0.0,
            "min_duration": float('inf'),
            "max_duration": 0.0,
            "errors": 0,
            "last_execution": None
        })
    
    def record(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a performance metric.
        
        Args:
            operation: Operation name (e.g., "chat_completion", "file_read")
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            error: Error message if failed
            metadata: Additional metadata
        """
        metric = Metric(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            metadata=metadata or {}
        )
        
        self._metrics.append(metric)
        
        # Aggregate
        agg = self._aggregated[operation]
        agg["count"] += 1
        agg["total_duration"] += duration_ms
        agg["min_duration"] = min(agg["min_duration"], duration_ms)
        agg["max_duration"] = max(agg["max_duration"], duration_ms)
        agg["last_execution"] = datetime.now()
        
        if not success:
            agg["errors"] += 1
        
        # Log if slow or error
        if duration_ms > 5000:  # > 5 seconds
            self.logger.warning(
                f"Slow operation: {operation} took {duration_ms:.2f}ms",
                operation=operation,
                duration_ms=duration_ms,
                metadata=metadata
            )
        elif not success:
            self.logger.error(
                f"Operation failed: {operation}",
                operation=operation,
                duration_ms=duration_ms,
                error=error,
                metadata=metadata
            )
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregated statistics.
        
        Args:
            operation: Optional operation name to filter
            
        Returns:
            Dictionary with statistics
        """
        if operation:
            if operation not in self._aggregated:
                return {}
            agg = self._aggregated[operation]
            return {
                "operation": operation,
                "count": agg["count"],
                "avg_duration_ms": agg["total_duration"] / agg["count"] if agg["count"] > 0 else 0,
                "min_duration_ms": agg["min_duration"] if agg["min_duration"] != float('inf') else 0,
                "max_duration_ms": agg["max_duration"],
                "error_rate": agg["errors"] / agg["count"] if agg["count"] > 0 else 0,
                "last_execution": agg["last_execution"].isoformat() if agg["last_execution"] else None
            }
        
        # Return all stats
        return {
            op: {
                "count": agg["count"],
                "avg_duration_ms": agg["total_duration"] / agg["count"] if agg["count"] > 0 else 0,
                "min_duration_ms": agg["min_duration"] if agg["min_duration"] != float('inf') else 0,
                "max_duration_ms": agg["max_duration"],
                "error_rate": agg["errors"] / agg["count"] if agg["count"] > 0 else 0,
                "last_execution": agg["last_execution"].isoformat() if agg["last_execution"] else None
            }
            for op, agg in self._aggregated.items()
        }
    
    def clear(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()
        self._aggregated.clear()


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create MetricsCollector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_performance(operation_name: str):
    """
    Decorator to track operation performance.
    
    Usage:
        @track_performance("chat_completion")
        async def chat(...):
            ...
    
    Args:
        operation_name: Name of the operation to track
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start = time.time()
            success = True
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                collector.record(
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                    metadata={"function": func.__name__}
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                collector.record(
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                    metadata={"function": func.__name__}
                )
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
