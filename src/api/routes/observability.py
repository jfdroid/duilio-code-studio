"""
Observability Routes
====================
Endpoints for tracing, metrics, and health monitoring.
"""

import sys
from pathlib import Path
from fastapi import APIRouter
from typing import Dict, Any

# Add parent directory to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.observability import get_tracer, get_prometheus_metrics
from core.metrics import get_metrics_collector
from fastapi.responses import Response

router = APIRouter(prefix="/api/observability", tags=["Observability"])


@router.get("/trace")
async def get_trace() -> Dict[str, Any]:
    """
    Get current trace information.
    
    Returns:
        Dictionary with trace spans and metadata
    """
    tracer = get_tracer()
    return tracer.get_trace()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics_endpoint() -> Response:
    """
    Get metrics in Prometheus format.
    
    Returns:
        Prometheus metrics text
    """
    prometheus = get_prometheus_metrics()
    metrics_text = prometheus.get_metrics()
    return Response(content=metrics_text, media_type="text/plain")


@router.get("/health/detailed")
async def detailed_health() -> Dict[str, Any]:
    """
    Detailed health check with metrics and tracing.
    
    Returns:
        Comprehensive health status
    """
    from services.ollama_service import get_ollama_service
    ollama = get_ollama_service()
    ollama_status = await ollama.health_check()
    
    metrics = get_metrics_collector()
    metrics_stats = metrics.get_stats()
    
    tracer = get_tracer()
    trace_info = tracer.get_trace()
    
    return {
        "status": "ok",
        "service": "DuilioCode Studio",
        "version": "2.0.0",
        "ollama": ollama_status,
        "metrics": {
            "operations": len(metrics_stats),
            "total_operations": sum(s.get("count", 0) for s in metrics_stats.values()),
            "stats": metrics_stats
        },
        "tracing": trace_info,
        "features": {
            "code_generation": ollama_status.get("status") == "running",
            "file_operations": True,
            "workspace_management": True,
            "observability": True
        }
    }
