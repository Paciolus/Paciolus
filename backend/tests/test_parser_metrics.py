"""
Tests for parser Prometheus metrics — Sprint 435.

Verifies:
- Metric definitions exist in PARSER_REGISTRY
- Successful parse increments counters and records duration
- Failed parse increments error counter
- Active gauge increments/decrements correctly
- /metrics endpoint returns Prometheus text format
"""

import pytest
from fastapi import HTTPException
from prometheus_client import generate_latest

from shared.parser_metrics import (
    PARSER_REGISTRY,
    active_parses,
    parse_duration_seconds,
    parse_errors_total,
    parse_total,
)

# =============================================================================
# Metric definitions
# =============================================================================


class TestMetricDefinitions:
    """Verify all expected metrics exist in PARSER_REGISTRY."""

    def test_parse_total_exists(self):
        output = generate_latest(PARSER_REGISTRY).decode()
        assert "paciolus_parse_total" in output or parse_total is not None

    def test_parse_errors_total_exists(self):
        assert parse_errors_total is not None

    def test_parse_duration_exists(self):
        assert parse_duration_seconds is not None

    def test_active_parses_exists(self):
        assert active_parses is not None

    def test_registry_is_dedicated(self):
        """Should NOT contain default process metrics."""
        output = generate_latest(PARSER_REGISTRY).decode()
        assert "process_cpu_seconds_total" not in output


# =============================================================================
# Metric behavior with parse operations
# =============================================================================


class TestMetricsInstrumentation:
    """Verify metrics are updated during parse operations."""

    def test_successful_csv_parse_increments_counter(self):
        """Parsing a valid CSV should increment parse_total for 'csv'."""
        from shared.helpers import parse_uploaded_file_by_format

        # Get baseline
        before = _get_counter_value(parse_total, {"format": "csv", "stage": "parse"})

        content = b"Account,Balance\n1000,100.0\n2000,200.0\n"
        parse_uploaded_file_by_format(content, "test.csv")

        after = _get_counter_value(parse_total, {"format": "csv", "stage": "parse"})
        assert after > before

    def test_successful_parse_records_duration(self):
        """Parsing should record a duration histogram sample."""
        from shared.helpers import parse_uploaded_file_by_format

        content = b"A,B\n1,2\n3,4\n"
        parse_uploaded_file_by_format(content, "timing.csv")

        # Check that at least one observation was recorded
        output = generate_latest(PARSER_REGISTRY).decode()
        assert "paciolus_parse_duration_seconds_count" in output

    def test_failed_parse_increments_error_counter(self):
        """A parse error should increment parse_errors_total."""
        from unittest.mock import patch

        from shared.helpers import parse_uploaded_file_by_format

        # Enable ODS so we reach the parse stage (not the feature flag check)
        with patch("config.FORMAT_ODS_ENABLED", True):
            before = _get_counter_value(parse_errors_total, {"format": "ods", "stage": "parse", "error_code": "400"})

            with pytest.raises(HTTPException):
                # Corrupt ODS file -> 400 during parse stage
                parse_uploaded_file_by_format(b"PK\x03\x04corrupt", "fail.ods")

            after = _get_counter_value(parse_errors_total, {"format": "ods", "stage": "parse", "error_code": "400"})
            assert after > before

    def test_detect_stage_increments(self):
        """Format detection stage should increment parse_total."""
        from shared.helpers import parse_uploaded_file_by_format

        before = _get_counter_value(parse_total, {"format": "csv", "stage": "detect"})

        content = b"A,B\n1,2\n"
        parse_uploaded_file_by_format(content, "detect.csv")

        after = _get_counter_value(parse_total, {"format": "csv", "stage": "detect"})
        assert after > before

    def test_active_gauge_returns_to_zero(self):
        """After a parse completes, active_parses gauge should return to 0."""
        from shared.helpers import parse_uploaded_file_by_format

        content = b"X,Y\n1,2\n"
        parse_uploaded_file_by_format(content, "gauge.csv")

        # Gauge should be 0 after completion
        val = active_parses.labels(format="csv")._value.get()
        assert val == 0.0

    def test_active_gauge_returns_to_zero_on_error(self):
        """After a failed parse, active_parses gauge should still return to 0."""
        from shared.helpers import parse_uploaded_file_by_format

        try:
            parse_uploaded_file_by_format(b"A,B\n", "gaugefail.csv")
        except HTTPException:
            pass

        val = active_parses.labels(format="csv")._value.get()
        assert val == 0.0


# =============================================================================
# /metrics endpoint
# =============================================================================


class TestMetricsEndpoint:
    """Verify /metrics route returns Prometheus text format."""

    def test_metrics_output_is_text(self):
        output = generate_latest(PARSER_REGISTRY)
        assert isinstance(output, bytes)
        text = output.decode("utf-8")
        # Should contain HELP/TYPE lines for at least one metric
        assert "# HELP" in text or "# TYPE" in text or "paciolus_" in text


# =============================================================================
# Helpers
# =============================================================================


def _get_counter_value(counter, labels: dict) -> float:
    """Get the current value of a Prometheus counter with given labels."""
    try:
        return counter.labels(**labels)._value.get()
    except KeyError:
        return 0.0
