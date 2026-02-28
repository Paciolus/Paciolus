#!/usr/bin/env python3
"""
Weekly Security Digest — Sprint 455 (CC4.2 / C1.3)

Queries the Paciolus /metrics endpoint and extracts the security-relevant
Prometheus counters needed for the weekly security event review.

Usage:
    METRICS_URL=https://api.paciolus.com/metrics python scripts/weekly_security_digest.py

    Or against local dev:
    METRICS_URL=http://localhost:8000/metrics python scripts/weekly_security_digest.py

Output:
    A pre-formatted markdown block ready to paste into the weekly review template.
    The script prints to stdout; paste the output into the
    "Script output" section of docs/08-internal/security-review-YYYY-WNN.md.

Auth events (login failures, CSRF, lockouts, rate limits) are NOT in Prometheus —
they live in structured JSON application logs (log_secure_operation events).
Use the grep commands in Section 4 of the review template for those.
"""

import os
import sys
import re
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.error import URLError

METRICS_URL = os.environ.get("METRICS_URL", "http://localhost:8000/metrics")

# Prometheus counter names we care about for security review
SECURITY_METRICS = [
    "paciolus_billing_redirect_injection_attempt_total",
    "paciolus_parse_errors_total",
    "paciolus_billing_events_total",
    "paciolus_pricing_v2_checkouts_total",
    "paciolus_active_trials",
    "paciolus_active_subscriptions",
]

# Descriptive labels for the review table
METRIC_DESCRIPTIONS = {
    "paciolus_billing_redirect_injection_attempt_total": "Billing redirect injection attempts",
    "paciolus_parse_errors_total": "File parse errors (all formats)",
    "paciolus_billing_events_total": "Billing events (all types)",
    "paciolus_pricing_v2_checkouts_total": "Checkout sessions initiated",
    "paciolus_active_trials": "Active trials (gauge)",
    "paciolus_active_subscriptions": "Active subscriptions (gauge)",
}

THRESHOLDS = {
    "paciolus_billing_redirect_injection_attempt_total": ">0 = investigate",
    "paciolus_parse_errors_total": "spike = investigate",
    "paciolus_billing_events_total": "see event_type labels",
    "paciolus_pricing_v2_checkouts_total": "—",
    "paciolus_active_trials": "—",
    "paciolus_active_subscriptions": "—",
}


def fetch_metrics(url: str) -> str:
    """Fetch Prometheus text exposition from the /metrics endpoint."""
    try:
        with urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8")
    except URLError as e:
        print(f"ERROR: Could not reach {url}: {e}", file=sys.stderr)
        print(
            "  Make sure METRICS_URL is set and the service is running.",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_metrics(text: str) -> dict[str, list[tuple[str, str, float]]]:
    """
    Parse Prometheus text format into a dict:
        metric_name -> list of (labels_str, raw_line, value)
    """
    result: dict[str, list[tuple[str, str, float]]] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match: metric_name{labels} value  OR  metric_name value
        match = re.match(
            r'^([a-zA-Z_][a-zA-Z0-9_]*)(\{[^}]*\})?\s+([\d.e+\-]+)$', line
        )
        if not match:
            continue

        name = match.group(1)
        labels = match.group(2) or ""
        try:
            value = float(match.group(3))
        except ValueError:
            continue

        if name not in result:
            result[name] = []
        result[name].append((labels, line, value))

    return result


def summarize_metric(
    name: str,
    entries: list[tuple[str, str, float]],
) -> str:
    """
    Return a human-readable summary string for a metric.
    For counters with a single series: just the value.
    For counters with labels: show per-label breakdown.
    """
    if not entries:
        return "0"

    if len(entries) == 1:
        return str(int(entries[0][2]) if entries[0][2].is_integer() else entries[0][2])

    # Multiple label combinations — show each on its own line
    lines = []
    total = 0.0
    for labels, _, value in sorted(entries, key=lambda e: -e[2]):
        label_str = labels.strip("{}")
        val = int(value) if isinstance(value, float) and value.is_integer() else value
        lines.append(f"  {label_str} = {val}")
        total += value
    total_val = int(total) if total.is_integer() else total
    lines.insert(0, f"TOTAL {total_val}:")
    return "\n".join(lines)


def build_report(parsed: dict[str, list[tuple[str, str, float]]]) -> str:
    """Build the markdown block to paste into the weekly review template."""
    now = datetime.now(timezone.utc)
    lines = [
        f"# weekly_security_digest.py output",
        f"# Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"# Source:    {METRICS_URL}",
        "",
    ]

    # Section 1: Security-critical metrics
    lines.append("## Security Metrics (Prometheus /metrics)")
    lines.append("")
    lines.append(f"{'Metric':<60} {'Value':<30} Threshold")
    lines.append(f"{'-'*60} {'-'*30} {'-'*30}")

    for metric in SECURITY_METRICS:
        entries = parsed.get(metric, [])
        desc = METRIC_DESCRIPTIONS.get(metric, metric)
        threshold = THRESHOLDS.get(metric, "—")

        if not entries:
            summary = "NOT FOUND (metric not yet emitted)"
        elif len(entries) == 1:
            val = entries[0][2]
            summary = str(int(val) if isinstance(val, float) and val.is_integer() else val)
        else:
            # Multiple entries — print total + breakdown below
            total = sum(e[2] for e in entries)
            summary = str(int(total) if isinstance(total, float) and total.is_integer() else total)

        lines.append(f"{metric:<60} {summary:<30} {threshold}")

        # For labeled metrics, show breakdown
        if len(entries) > 1:
            for labels, _, val in sorted(entries, key=lambda e: -e[2]):
                val_str = str(int(val) if isinstance(val, float) and val.is_integer() else val)
                lines.append(f"  {labels:<58} {val_str}")

    lines.append("")

    # Section 2: Injection attempt details
    injection_entries = parsed.get("paciolus_billing_redirect_injection_attempt_total", [])
    if injection_entries and any(e[2] > 0 for e in injection_entries):
        lines.append("## ALERT: Billing Redirect Injection Attempts Detected")
        lines.append("")
        for labels, _, val in injection_entries:
            if val > 0:
                lines.append(f"  {labels}: {int(val)}")
        lines.append("")
        lines.append("  ACTION REQUIRED: Investigate source IPs and request patterns in Render logs.")
        lines.append("  See runbook: docs/08-internal/runbooks/billing-injection-spike.md")
        lines.append("")

    # Section 3: Parse error spike check
    parse_error_entries = parsed.get("paciolus_parse_errors_total", [])
    total_parse_errors = sum(e[2] for e in parse_error_entries)
    if total_parse_errors > 50:
        lines.append(f"## WARNING: Elevated Parse Error Count ({int(total_parse_errors)} total)")
        lines.append("")
        lines.append("  Consider investigating: may indicate malformed file uploads or")
        lines.append("  an attempted file-type exploitation.")
        lines.append("")

    # Section 4: Instructions for log-based events
    lines.append("## Log-Based Events (not in Prometheus — manual grep required)")
    lines.append("")
    lines.append("The following events are in structured JSON application logs.")
    lines.append("Run these queries in Render Dashboard → your service → Logs tab:")
    lines.append("")
    lines.append('  grep \'\"login_failed\"\' <log_stream>               # Failed logins')
    lines.append('  grep \'\"account_locked\"\' <log_stream>             # Lockouts triggered')
    lines.append('  grep \'\"csrf_blocked\"\' <log_stream>               # CSRF origin failures')
    lines.append('  grep \'\"csrf_validation_failed\"\' <log_stream>     # CSRF token invalid')
    lines.append('  grep \'\"refresh_token_reuse_detected\"\' <log_stream>  # Token reuse (P0!)')
    lines.append('  grep \'\"status\":429\' <access_log>                  # Rate limit hits')
    lines.append("")
    lines.append("Paste counts for each event type into Section 4 (Auth Events) and")
    lines.append("Section 5 (Rate Limiting) of the weekly review template.")
    lines.append("")

    lines.append("## End of digest")

    return "\n".join(lines)


def main() -> None:
    print(f"Fetching metrics from {METRICS_URL} ...", file=sys.stderr)
    raw = fetch_metrics(METRICS_URL)
    parsed = parse_metrics(raw)

    missing = [m for m in SECURITY_METRICS if m not in parsed]
    if missing:
        print(
            f"Note: {len(missing)} metric(s) not yet emitted "
            f"(service may not have processed any events yet):",
            file=sys.stderr,
        )
        for m in missing:
            print(f"  {m}", file=sys.stderr)

    report = build_report(parsed)
    print(report)


if __name__ == "__main__":
    main()
