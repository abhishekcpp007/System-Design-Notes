"""
Metrics API — Prometheus metrics endpoint.
"""
from fastapi import APIRouter, Response

from app.services.observability import metrics

router = APIRouter()


@router.get(
    "/",
    summary="Prometheus Metrics",
    description="""
    Exposes application metrics in Prometheus text format.

    **Available metrics:**
    - `http_requests_total` — Counter of total HTTP requests by method/endpoint/status
    - `http_request_duration_seconds` — Histogram of request durations
    - `http_requests_in_progress` — Gauge of currently processing requests
    - `app_info` — Application version and environment info
    """,
    response_class=Response,
)
async def get_metrics():
    """Get Prometheus metrics in text exposition format."""
    content = metrics.get_metrics_response()
    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
