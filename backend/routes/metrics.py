"""
Paciolus API — Prometheus Metrics Endpoint

Sprint 435: Exposes parser metrics at /metrics for Prometheus scraping.
Unauthenticated (standard Prometheus pattern), excluded from OpenAPI schema.

SECURITY NOTE: In production, restrict access to this endpoint via
reverse proxy rules (e.g. Render internal network, nginx allow/deny)
to prevent operational data leakage to unauthenticated users.
"""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from shared.parser_metrics import PARSER_REGISTRY

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
def get_metrics(request: Request):
    """Prometheus metrics endpoint. Returns text/plain with parser metrics.

    Unauthenticated by design (Prometheus standard). Restrict at infrastructure level.
    """
    return PlainTextResponse(
        content=generate_latest(PARSER_REGISTRY).decode("utf-8"),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
