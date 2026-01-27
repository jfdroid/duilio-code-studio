"""
Observability
=============
Tracing, metrics, and health monitoring for the application.
"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime
from core.metrics import MetricsCollector, get_metrics_collector
from core.logger import get_logger


@dataclass
class TraceSpan:
    """Single trace span."""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Tracer:
    """
    Distributed tracing for request tracking.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self._spans: list[TraceSpan] = []
    
    def start_span(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> TraceSpan:
        """
        Start a new trace span.
        
        Args:
            operation: Operation name
            metadata: Optional metadata
            
        Returns:
            TraceSpan instance
        """
        span = TraceSpan(
            operation=operation,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self._spans.append(span)
        return span
    
    def end_span(self, span: TraceSpan, error: Optional[str] = None):
        """
        End a trace span.
        
        Args:
            span: Span to end
            error: Optional error message
        """
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        span.error = error
        
        # Log if slow or error
        if span.duration_ms > 5000:
            self.logger.warning(
                f"Slow operation: {span.operation}",
                duration_ms=span.duration_ms,
                metadata=span.metadata
            )
        elif error:
            self.logger.error(
                f"Operation failed: {span.operation}",
                error=error,
                duration_ms=span.duration_ms,
                metadata=span.metadata
            )
    
    def get_trace(self) -> Dict[str, Any]:
        """
        Get current trace information.
        
        Returns:
            Dictionary with trace data
        """
        return {
            "spans": [
                {
                    "operation": span.operation,
                    "duration_ms": span.duration_ms,
                    "metadata": span.metadata,
                    "error": span.error
                }
                for span in self._spans
            ],
            "total_spans": len(self._spans),
            "total_duration_ms": sum(s.duration_ms or 0 for s in self._spans)
        }


# Singleton tracer
_tracer: Optional[Tracer] = None


def get_tracer() -> Tracer:
    """Get or create Tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def trace_operation(operation_name: str):
    """
    Decorator to trace an operation.
    
    Usage:
        @trace_operation("chat_completion")
        async def chat(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span = tracer.start_span(operation_name, metadata={"function": func.__name__})
            try:
                result = await func(*args, **kwargs)
                tracer.end_span(span)
                return result
            except Exception as e:
                tracer.end_span(span, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span = tracer.start_span(operation_name, metadata={"function": func.__name__})
            try:
                result = func(*args, **kwargs)
                tracer.end_span(span)
                return result
            except Exception as e:
                tracer.end_span(span, error=str(e))
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class PrometheusMetrics:
    """
    Prometheus-compatible metrics exporter.
    """
    
    def __init__(self):
        self.metrics_collector = get_metrics_collector()
        self.logger = get_logger()
    
    def get_metrics(self) -> str:
        """
        Get metrics in Prometheus format.
        
        Returns:
            Prometheus metrics string
        """
        stats = self.metrics_collector.get_stats()
        
        lines = []
        lines.append("# HELP duiliocode_operations_total Total number of operations")
        lines.append("# TYPE duiliocode_operations_total counter")
        
        for operation, data in stats.items():
            # Counter
            lines.append(f'duiliocode_operations_total{{operation="{operation}"}} {data["count"]}')
            
            # Histogram (duration)
            lines.append(f'# HELP duiliocode_operation_duration_ms Operation duration in milliseconds')
            lines.append(f'# TYPE duiliocode_operation_duration_ms histogram')
            lines.append(f'duiliocode_operation_duration_ms_bucket{{operation="{operation}",le="100"}} {1 if data.get("avg_duration_ms", 0) <= 100 else 0}')
            lines.append(f'duiliocode_operation_duration_ms_bucket{{operation="{operation}",le="500"}} {1 if data.get("avg_duration_ms", 0) <= 500 else 0}')
            lines.append(f'duiliocode_operation_duration_ms_bucket{{operation="{operation}",le="1000"}} {1 if data.get("avg_duration_ms", 0) <= 1000 else 0}')
            lines.append(f'duiliocode_operation_duration_ms_bucket{{operation="{operation}",le="5000"}} {1 if data.get("avg_duration_ms", 0) <= 5000 else 0}')
            lines.append(f'duiliocode_operation_duration_ms_bucket{{operation="{operation}",le="+Inf"}} {data["count"]}')
            lines.append(f'duiliocode_operation_duration_ms_sum{{operation="{operation}"}} {data.get("avg_duration_ms", 0) * data["count"]}')
            lines.append(f'duiliocode_operation_duration_ms_count{{operation="{operation}"}} {data["count"]}')
            
            # Error rate
            lines.append(f'# HELP duiliocode_operation_errors_total Total number of operation errors')
            lines.append(f'# TYPE duiliocode_operation_errors_total counter')
            lines.append(f'duiliocode_operation_errors_total{{operation="{operation}"}} {int(data.get("error_rate", 0) * data["count"])}')
        
        return "\n".join(lines)


# Singleton Prometheus metrics
_prometheus_metrics: Optional[PrometheusMetrics] = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """Get or create PrometheusMetrics instance."""
    global _prometheus_metrics
    if _prometheus_metrics is None:
        _prometheus_metrics = PrometheusMetrics()
    return _prometheus_metrics
