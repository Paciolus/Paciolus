"""
Paciolus — Parser Observability Metrics (Prometheus)

Sprint 435: Dedicated CollectorRegistry for parser metrics.
Instrumentation helpers for parse_uploaded_file_by_format().

Metrics:
- paciolus_parse_total: Counter by format/stage
- paciolus_parse_errors_total: Counter by format/stage/error_code
- paciolus_parse_duration_seconds: Histogram by format/stage
- paciolus_active_parses: Gauge by format

Uses a dedicated registry so /metrics only exposes parser metrics,
not the default process/GC collectors.
"""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Dedicated registry — avoids polluting default registry
PARSER_REGISTRY = CollectorRegistry()

parse_total = Counter(
    "paciolus_parse_total",
    "Total parse operations",
    ["format", "stage"],
    registry=PARSER_REGISTRY,
)

parse_errors_total = Counter(
    "paciolus_parse_errors_total",
    "Total parse errors",
    ["format", "stage", "error_code"],
    registry=PARSER_REGISTRY,
)

parse_duration_seconds = Histogram(
    "paciolus_parse_duration_seconds",
    "Parse duration in seconds",
    ["format", "stage"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=PARSER_REGISTRY,
)

active_parses = Gauge(
    "paciolus_active_parses",
    "Currently active parse operations",
    ["format"],
    registry=PARSER_REGISTRY,
)
