"""
Metrics Routes
==============
Performance metrics and monitoring endpoints.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional

# Add parent directory to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.container import get_metrics_collector
from core.metrics import MetricsCollector

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("/stats")
async def get_metrics_stats(
    operation: Optional[str] = None,
    metrics: MetricsCollector = Depends(get_metrics_collector)
) -> Dict[str, Any]:
    """
    Get performance metrics statistics.
    
    Returns aggregated performance metrics for all operations or a specific operation.
    
    **Query Parameters**:
    - `operation` (optional): Filter by specific operation name
    
    **Response**:
    ```json
    {
      "chat_completion": {
        "count": 150,
        "avg_duration_ms": 2345.6,
        "min_duration_ms": 500.2,
        "max_duration_ms": 10000.0,
        "error_rate": 0.02,
        "last_execution": "2025-01-27T15:30:00"
      },
      "code_generation": {
        "count": 75,
        "avg_duration_ms": 1800.3,
        ...
      }
    }
    ```
    
    **Example Request**:
    ```
    GET /api/metrics/stats
    GET /api/metrics/stats?operation=chat_completion
    ```
    """
    stats = metrics.get_stats(operation=operation)
    return {
        "stats": stats,
        "total_operations": len(stats) if not operation else 1
    }


@router.post("/clear")
async def clear_metrics(
    metrics: MetricsCollector = Depends(get_metrics_collector)
) -> Dict[str, Any]:
    """
    Clear all performance metrics.
    
    **Response**:
    ```json
    {
      "message": "Metrics cleared successfully"
    }
    ```
    """
    metrics.clear()
    return {"message": "Metrics cleared successfully"}
