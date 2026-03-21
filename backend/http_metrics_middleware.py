"""
Paciolus — HTTP Metrics & Access Log Middleware

Sprint 516 (F-008 + F-017):
- F-008: HTTP RED metrics (Request rate, Error rate, Duration) via Prometheus
- F-017: Per-request structured access log with request_id correlation

Path normalization converts dynamic segments to templates so Prometheus
label cardinality stays bounded (e.g. /clients/42 -> /clients/{id}).

The middleware is intentionally lightweight: one time.perf_counter() call,
one counter increment, one histogram observation, and one log.info() call.
No PII or financial data is logged.
"""

import logging
import re
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logging_config import request_id_var
from shared.parser_metrics import http_request_duration_seconds, http_requests_total

logger = logging.getLogger("paciolus.access")

# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------
# Patterns that match dynamic path segments. Order matters — more specific
# patterns first, then the catch-all numeric/hex ID pattern.

_PATH_NORMALIZERS: list[tuple[re.Pattern[str], str]] = [
    # Export-sharing tokens (hex strings, 16+ chars)
    (re.compile(r"/export-sharing/[a-f0-9]{16,}"), "/export-sharing/{token}"),
    # Bulk upload job IDs (UUID-style or numeric)
    (re.compile(r"/upload/bulk/[a-f0-9\-]{8,}"), "/upload/bulk/{job_id}"),
    # Benchmark industry names (e.g. /benchmarks/manufacturing)
    (re.compile(r"/benchmarks/[a-zA-Z][a-zA-Z0-9_\-]+"), "/benchmarks/{industry}"),
    # Generic numeric IDs in path segments (e.g. /clients/42, /adjustments/7/status)
    (re.compile(r"/(\d+)(?=/|$)"), "/{id}"),
]

# Paths to exclude from metrics entirely (high-frequency internal endpoints
# that would bloat cardinality without providing useful signal)
_EXCLUDED_PATHS = frozenset({"/health", "/metrics"})


def _normalize_path(path: str) -> str:
    """Collapse dynamic path segments into template placeholders.

    This prevents unbounded Prometheus label cardinality from unique IDs,
    tokens, or other variable path components.
    """
    for pattern, replacement in _PATH_NORMALIZERS:
        path = pattern.sub(replacement, path)
    return path


class HttpMetricsMiddleware(BaseHTTPMiddleware):
    """Combined HTTP RED metrics + structured access log middleware.

    Records:
    - paciolus_http_requests_total   (Counter: method, path, status_code)
    - paciolus_http_request_duration_seconds (Histogram: method, path, status_code)
    - INFO-level access log line per request (method, path, status, duration_ms, request_id)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip excluded paths to avoid noise
        if path in _EXCLUDED_PATHS:
            resp: Response = await call_next(request)
            return resp

        method = request.method
        start = time.perf_counter()

        response: Response = await call_next(request)

        duration = time.perf_counter() - start
        status_code = str(response.status_code)
        normalized = _normalize_path(path)

        # F-008: Prometheus RED metrics
        http_requests_total.labels(
            method=method,
            path=normalized,
            status_code=status_code,
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            path=normalized,
            status_code=status_code,
        ).observe(duration)

        # F-017: Structured access log (no PII, no financial data)
        request_id = request_id_var.get("-")
        duration_ms = round(duration * 1000, 1)

        logger.info(
            "%s %s %s %.1fms [%s]",
            method,
            path,
            status_code,
            duration_ms,
            request_id,
        )

        return response
