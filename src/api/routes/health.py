"""
Health Routes
=============
Server health check and status endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from services.ollama_service import OllamaService, get_ollama_service


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check."""
    return {"status": "ok", "service": "DuilioCode Studio"}


@router.get("/ollama")
async def ollama_status(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """Check Ollama server status."""
    return await ollama.health_check()


@router.get("/full")
async def full_status(
    ollama: OllamaService = Depends(get_ollama_service)
) -> Dict[str, Any]:
    """Full system status check."""
    ollama_status = await ollama.health_check()
    
    # Get metrics
    try:
        from core.metrics import get_metrics_collector
        metrics = get_metrics_collector()
        metrics_stats = metrics.get_stats()
    except Exception:
        metrics_stats = {}
    
    # Get trace info
    try:
        from core.observability import get_tracer
        tracer = get_tracer()
        trace_info = tracer.get_trace()
    except Exception:
        trace_info = {}
    
    return {
        "status": "ok",
        "service": "DuilioCode Studio",
        "version": "2.0.0",
        "ollama": ollama_status,
        "features": {
            "code_generation": ollama_status.get("status") == "running",
            "file_operations": True,
            "workspace_management": True
        },
        "metrics": {
            "operations": len(metrics_stats),
            "total_operations": sum(s.get("count", 0) for s in metrics_stats.values())
        },
        "tracing": {
            "spans": trace_info.get("total_spans", 0),
            "total_duration_ms": trace_info.get("total_duration_ms", 0)
        }
    }


@router.get("/prometheus")
async def prometheus_metrics() -> str:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for scraping.
    """
    from core.observability import get_prometheus_metrics
    from fastapi.responses import Response
    
    prometheus = get_prometheus_metrics()
    metrics_text = prometheus.get_metrics()
    
    return Response(content=metrics_text, media_type="text/plain")
