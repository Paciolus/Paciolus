"""
Tests for shared.alert_checker — Parser Alert Threshold Checker — Sprint 437.

Covers:
- TOML loading
- Default fallback
- Per-format override
- Health check violations
- Severity escalation
"""

from pathlib import Path

from shared.alert_checker import (
    check_format_health,
    load_alert_thresholds,
)


class TestLoadAlertThresholds:
    """TOML loading and threshold construction."""

    def test_loads_from_default_path(self):
        thresholds = load_alert_thresholds()
        assert "csv" in thresholds
        assert "ods" in thresholds
        assert "pdf" in thresholds

    def test_csv_has_custom_error_rate(self):
        thresholds = load_alert_thresholds()
        assert thresholds["csv"].error_rate_percent == 5.0

    def test_ods_has_higher_tolerance(self):
        thresholds = load_alert_thresholds()
        assert thresholds["ods"].error_rate_percent == 15.0

    def test_pdf_has_high_latency_threshold(self):
        thresholds = load_alert_thresholds()
        assert thresholds["pdf"].latency_p95_seconds == 15.0

    def test_missing_file_returns_empty(self):
        thresholds = load_alert_thresholds(toml_path=Path("/nonexistent/path.toml"))
        assert thresholds == {}

    def test_all_formats_have_active_parses_max(self):
        thresholds = load_alert_thresholds()
        for fmt, t in thresholds.items():
            assert t.active_parses_max == 50, f"{fmt} missing active_parses_max default"


class TestCheckFormatHealth:
    """Health check evaluation."""

    def test_healthy_when_under_thresholds(self):
        result = check_format_health("csv", error_rate=1.0, latency_p95=0.5)
        assert result.healthy is True
        assert len(result.alerts) == 0

    def test_unhealthy_when_error_rate_exceeded(self):
        result = check_format_health("csv", error_rate=10.0, latency_p95=0.5)
        assert result.healthy is False
        assert any(a.metric == "error_rate_percent" for a in result.alerts)

    def test_unhealthy_when_latency_exceeded(self):
        result = check_format_health("csv", error_rate=1.0, latency_p95=5.0)
        assert result.healthy is False
        assert any(a.metric == "latency_p95_seconds" for a in result.alerts)

    def test_severity_warning_for_moderate_breach(self):
        result = check_format_health("csv", error_rate=7.0)
        # 7% > 5% threshold but < 10% (2x threshold)
        violation = next(a for a in result.alerts if a.metric == "error_rate_percent")
        assert violation.severity == "warning"

    def test_severity_critical_for_severe_breach(self):
        result = check_format_health("csv", error_rate=15.0)
        # 15% > 10% (2x the 5% threshold)
        violation = next(a for a in result.alerts if a.metric == "error_rate_percent")
        assert violation.severity == "critical"

    def test_unknown_format_is_healthy(self):
        result = check_format_health("unknown_format", error_rate=99.0)
        assert result.healthy is True

    def test_active_parses_violation(self):
        result = check_format_health("csv", active_parses=60)
        assert result.healthy is False
        assert any(a.metric == "active_parses_max" for a in result.alerts)
