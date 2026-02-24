"""
Paciolus — Parser Alert Threshold Checker

Sprint 437: Reads alert thresholds from guards/parser_alerts.toml,
provides functions to compare current metric values against thresholds.

Usage:
    thresholds = load_alert_thresholds()
    result = check_format_health("csv", error_rate=12.0, latency_p95=1.5)
    # result.alerts = [AlertViolation(metric="error_rate_percent", ...)]
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Python 3.11+ has tomllib in stdlib; use tomli as fallback
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

_TOML_PATH = Path(__file__).parent.parent / "guards" / "parser_alerts.toml"


@dataclass(frozen=True)
class FormatThresholds:
    """Alert thresholds for a specific format."""

    format_name: str
    error_rate_percent: float
    latency_p95_seconds: float
    active_parses_max: int


@dataclass(frozen=True)
class AlertViolation:
    """A single threshold violation."""

    format_name: str
    metric: str
    current_value: float
    threshold: float
    severity: str  # "warning" or "critical"


@dataclass
class HealthCheckResult:
    """Result of checking a format's metric health."""

    format_name: str
    healthy: bool
    alerts: list[AlertViolation] = field(default_factory=list)


def load_alert_thresholds(toml_path: Path | None = None) -> dict[str, FormatThresholds]:
    """Load alert thresholds from TOML config.

    Returns a dict mapping format name -> FormatThresholds.
    Missing per-format keys fall back to [alert_defaults].
    """
    path = toml_path or _TOML_PATH

    if not path.exists():
        logger.warning("Alert thresholds file not found: %s", path)
        return {}

    with open(path, "rb") as f:
        config = tomllib.load(f)

    defaults = config.get("alert_defaults", {})
    default_error_rate = defaults.get("error_rate_percent", 10.0)
    default_latency = defaults.get("latency_p95_seconds", 5.0)
    default_active = defaults.get("active_parses_max", 50)

    alerts_section = config.get("alerts", {})
    thresholds: dict[str, FormatThresholds] = {}

    for fmt_name, fmt_config in alerts_section.items():
        thresholds[fmt_name] = FormatThresholds(
            format_name=fmt_name,
            error_rate_percent=fmt_config.get("error_rate_percent", default_error_rate),
            latency_p95_seconds=fmt_config.get("latency_p95_seconds", default_latency),
            active_parses_max=fmt_config.get("active_parses_max", default_active),
        )

    return thresholds


def check_format_health(
    format_name: str,
    error_rate: float = 0.0,
    latency_p95: float = 0.0,
    active_parses: int = 0,
    thresholds: dict[str, FormatThresholds] | None = None,
) -> HealthCheckResult:
    """Check current metrics against alert thresholds for a format.

    Args:
        format_name: The file format to check (e.g., "csv", "ods").
        error_rate: Current error rate percentage.
        latency_p95: Current p95 latency in seconds.
        active_parses: Current number of active parse operations.
        thresholds: Pre-loaded thresholds (loads from TOML if not provided).

    Returns:
        HealthCheckResult with any threshold violations.
    """
    if thresholds is None:
        thresholds = load_alert_thresholds()

    fmt_thresholds = thresholds.get(format_name)
    if fmt_thresholds is None:
        # No thresholds configured — assume healthy
        return HealthCheckResult(format_name=format_name, healthy=True)

    alerts: list[AlertViolation] = []

    if error_rate > fmt_thresholds.error_rate_percent:
        alerts.append(
            AlertViolation(
                format_name=format_name,
                metric="error_rate_percent",
                current_value=error_rate,
                threshold=fmt_thresholds.error_rate_percent,
                severity="critical" if error_rate > fmt_thresholds.error_rate_percent * 2 else "warning",
            )
        )

    if latency_p95 > fmt_thresholds.latency_p95_seconds:
        alerts.append(
            AlertViolation(
                format_name=format_name,
                metric="latency_p95_seconds",
                current_value=latency_p95,
                threshold=fmt_thresholds.latency_p95_seconds,
                severity="critical" if latency_p95 > fmt_thresholds.latency_p95_seconds * 2 else "warning",
            )
        )

    if active_parses > fmt_thresholds.active_parses_max:
        alerts.append(
            AlertViolation(
                format_name=format_name,
                metric="active_parses_max",
                current_value=float(active_parses),
                threshold=float(fmt_thresholds.active_parses_max),
                severity="critical" if active_parses > fmt_thresholds.active_parses_max * 2 else "warning",
            )
        )

    return HealthCheckResult(
        format_name=format_name,
        healthy=len(alerts) == 0,
        alerts=alerts,
    )
