"""
Paciolus API — Prometheus Metrics Endpoint

Sprint 435: Exposes parser metrics at /metrics for Prometheus scraping.
Unauthenticated (standard Prometheus pattern), excluded from OpenAPI schema.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from shared.parser_metrics import PARSER_REGISTRY

router = APIRouter(tags=["metrics"])


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
def get_metrics():
    """Prometheus metrics endpoint. Returns text/plain with parser metrics."""
    return PlainTextResponse(
        content=generate_latest(PARSER_REGISTRY).decode("utf-8"),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
