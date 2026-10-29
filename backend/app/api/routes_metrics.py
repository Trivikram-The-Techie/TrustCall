"""
Prometheus Metrics Route: GET /v1/metrics
Exposes real-time latency histograms, active sessions, and stage-2 escalation rates.
"""

from fastapi import APIRouter, Response
from app.monitoring.metrics import get_prometheus_metrics

router = APIRouter(prefix="/v1", tags=["Metrics"])


@router.get("/metrics")
async def prometheus_metrics():
    """
    Exposes Prometheus text exposition format metrics for Prometheus server scraping.
    Includes voice_clone_total_latency_seconds, active sessions, and stage-2 rate.
    """
    payload, content_type = get_prometheus_metrics()
    return Response(content=payload, media_type=content_type)
