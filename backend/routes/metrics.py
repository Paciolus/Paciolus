"""
Paciolus API — Prometheus Metrics Endpoint

Sprint 435: Exposes parser metrics at /metrics for Prometheus scraping.
Excluded from OpenAPI schema.

Security: In production, access is restricted to localhost/internal IPs only.
External Prometheus scrapers should use a reverse proxy or VPN to reach the
backend's internal address.
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from shared.parser_metrics import PARSER_REGISTRY
from shared.rate_limits import RATE_LIMIT_METRICS, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])

# Internal/loopback addresses allowed to scrape metrics in production
_METRICS_ALLOWED_PEERS = frozenset({"127.0.0.1", "::1", "localhost"})


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
@limiter.limit(RATE_LIMIT_METRICS)
def get_metrics(request: Request) -> PlainTextResponse:
    """Prometheus metrics endpoint. Returns text/plain with parser metrics.

    Production: restricted to loopback/internal IPs to prevent operational
    data leakage. Configure your Prometheus scraper to reach the backend's
    internal address (e.g. via Render internal network or Docker bridge).
    """
    from config import ENV_MODE

    if ENV_MODE == "production":
        peer_ip = request.client.host if request.client else ""
        if peer_ip not in _METRICS_ALLOWED_PEERS:
            raise HTTPException(status_code=404, detail="Not found")

    return PlainTextResponse(
        content=generate_latest(PARSER_REGISTRY).decode("utf-8"),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
