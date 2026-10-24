"""
Sprint 831 — CEO methodology decisions 2–4 (2026-10-24), journal entry testing.

Decision 2: the composite may never rate lower than its HIGH-severity flags
support, and a Benford failure may never lower the score.
Decision 3: Columbus Day and Veterans Day postings are flagged LOW; the auditor
can exclude holidays the client works and add closure days.
Decision 4: month-end clustering compares each month with the client's own
months; the fixed threshold stays, at LOW.

Each test below fails on the pre-Sprint-831 code.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

import je_testing_engine as je  # noqa: E402  (module import: its test_* functions must not be collected)
from je_testing_engine import (  # noqa: E402
    JETestingConfig,
    JournalEntry,
    TestResult,
    calculate_composite_score,
)
from routes.je_testing import _parse_holiday_calendar  # noqa: E402
from shared.holiday_calendar import us_federal_holiday_names  # noqa: E402
from shared.testing_enums import RiskTier, Severity, TestTier  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _entry(
    row: int, day: str, amount: float = 100.0, account: str = "Cash", entry_id: str | None = None
) -> JournalEntry:
    return JournalEntry(
        entry_id=entry_id or f"JE{row}", account=account, posting_date=day, debit=amount, row_number=row
    )


# ─── Decision 2: composite score ─────────────────────────────────────────


def _result(key: str, severity: Severity, flagged: list = (), total: int = 1000) -> TestResult:
    return TestResult(
        test_name=key,
        test_key=key,
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total,
        severity=severity,
        description="",
        flagged_entries=list(flagged),
    )


class TestCompositeScore:
    def test_benford_failure_without_flags_never_lowers_the_score(self):
        from je_testing_engine import FlaggedEntry

        flags = [
            FlaggedEntry(
                entry=_entry(i, "2025-01-02"),
                test_name="weekend",
                test_key="weekend_postings",
                test_tier=TestTier.STATISTICAL,
                severity=Severity.MEDIUM,
                issue="",
            )
            for i in range(1, 301)
        ]
        others = [_result("weekend_postings", Severity.MEDIUM, flags), _result("round_amounts", Severity.LOW)]
        passed = calculate_composite_score([*others, _result("benford_law", Severity.LOW)], 1000)
        failed = calculate_composite_score([*others, _result("benford_law", Severity.HIGH)], 1000)
        assert failed.score >= passed.score
        assert failed.risk_tier != RiskTier.LOW

    def test_benford_failure_alone_is_moderate_and_explained(self):
        score = calculate_composite_score(
            [_result("benford_law", Severity.HIGH), _result("round_amounts", Severity.LOW)], 1000
        )
        assert score.risk_tier == RiskTier.MODERATE
        assert any("Benford" in reason for reason in score.score_basis)
        assert score.to_dict()["score_basis"] == score.score_basis

    def test_split_of_two_material_pieces_is_high(self):
        entries = [_entry(1, "2025-03-04", 4_900), _entry(2, "2025-03-04", 4_800)]
        result = je.test_just_below_threshold(entries, JETestingConfig())
        splits = [f for f in result.flagged_entries if "split" in f.issue]
        assert splits and all(f.severity == Severity.HIGH for f in splits)

    def test_busy_account_routine_volume_is_medium_not_high(self):
        entries = [_entry(i, "2025-03-04", 100 + i * 100) for i in range(1, 15)]
        result = je.test_just_below_threshold(entries, JETestingConfig())
        splits = [f for f in result.flagged_entries if "split" in f.issue]
        assert splits, "detection unchanged — routine volume is still flagged"
        assert all(f.severity == Severity.MEDIUM for f in splits)


# ─── Decision 3: holidays ────────────────────────────────────────────────


class TestHolidays:
    def test_columbus_day_large_posting_is_low(self):
        # Columbus Day 2025 = Monday Oct 13; Christmas = Thursday Dec 25.
        entries = [_entry(1, "2025-10-13", 50_000), _entry(2, "2025-12-25", 50_000)]
        result = je.test_holiday_postings(entries, JETestingConfig())
        by_row = {f.entry.row_number: f for f in result.flagged_entries}
        assert by_row[1].severity == Severity.LOW
        assert "open on this holiday" in by_row[1].issue
        assert by_row[2].severity == Severity.HIGH

    def test_veterans_day_is_still_flagged(self):
        result = je.test_holiday_postings([_entry(1, "2025-11-11", 50_000)], JETestingConfig())
        assert result.entries_flagged == 1

    def test_auditor_calendar_excludes_and_adds_days(self):
        config = JETestingConfig(
            holiday_excluded_names=("Christmas Day",), holiday_additional_dates=(date(2025, 12, 24),)
        )
        entries = [_entry(1, "2025-12-25", 50_000), _entry(2, "2025-12-24", 50_000)]
        result = je.test_holiday_postings(entries, config)
        assert [f.entry.row_number for f in result.flagged_entries] == [2]
        assert result.flagged_entries[0].details["holiday"] == "Client closure day"
        assert "Excluded by the auditor: Christmas Day" in result.description

    def test_route_parses_a_calendar(self):
        config = _parse_holiday_calendar(json.dumps({"exclude": ["Columbus Day"], "closed_dates": ["2025-12-24"]}))
        assert config.holiday_excluded_names == ("Columbus Day",)
        assert config.holiday_additional_dates == (date(2025, 12, 24),)
        assert _parse_holiday_calendar(None) is None

    @pytest.mark.parametrize(
        "raw",
        [
            "not json",
            json.dumps(["Columbus Day"]),
            json.dumps({"exclude": ["Halloween"]}),
            json.dumps({"closed_dates": ["12/24/2025"]}),
            json.dumps({"closed_dates": ["2025-01-01"] * 61}),
            json.dumps({"exclude": [], "extra": 1}),
        ],
    )
    def test_route_refuses_a_malformed_calendar(self, raw):
        with pytest.raises(HTTPException) as exc:
            _parse_holiday_calendar(raw)
        assert exc.value.status_code == 400

    def test_frontend_holiday_list_matches_backend(self):
        ts = (REPO_ROOT / "frontend/src/types/jeTesting.ts").read_text(encoding="utf-8")
        block = ts[ts.index("export const US_FEDERAL_HOLIDAYS") :]
        block = block[: block.index("] as const")]
        names = [a or b for a, b in re.findall(r"\"([^\"]+)\"|'([^']+)'", block)]
        assert names == us_federal_holiday_names()


# ─── Decision 4: month-end clustering ────────────────────────────────────


def _month(year: int, month: int, total: int, month_end: int, start_row: int) -> list[JournalEntry]:
    """`total` entries in a month, `month_end` of them in the last 3 days (day 1 vs day 28+)."""
    from calendar import monthrange

    last = monthrange(year, month)[1]
    rows = []
    for i in range(total):
        day = last - (i % 3) if i < month_end else 1 + (i % 20)
        rows.append(_entry(start_row + i, f"{year}-{month:02d}-{day:02d}"))
    return rows


class TestMonthEnd:
    def test_normal_close_every_month_is_low_only(self):
        # About 30% of entries in the last 3 days every month: the fixed
        # threshold trips every month, but no month is unusual for the client.
        entries: list[JournalEntry] = []
        for m in range(1, 13):
            entries += _month(2025, m, 100, 30, m * 1000)
        result = je.test_month_end_clustering(entries, JETestingConfig())
        assert result.entries_flagged > 0, "fixed-threshold detection is unchanged"
        assert {f.severity for f in result.flagged_entries} == {Severity.LOW}
        assert result.severity == Severity.LOW
        assert "0 unusual" in result.description

    def test_a_spike_month_is_medium(self):
        entries: list[JournalEntry] = []
        for m in range(1, 13):
            entries += _month(2025, m, 100, 60 if m == 12 else 30, m * 1000)
        result = je.test_month_end_clustering(entries, JETestingConfig())
        december = [f for f in result.flagged_entries if f.details["month"] == "2025-12"]
        others = [f for f in result.flagged_entries if f.details["month"] != "2025-12"]
        assert december and all(f.severity in (Severity.MEDIUM, Severity.HIGH) for f in december)
        assert all(f.details["client_baseline_outlier"] for f in december)
        assert all(f.severity == Severity.LOW for f in others)
        assert result.severity == Severity.MEDIUM

    def test_too_few_months_says_the_comparison_did_not_run(self):
        entries = _month(2025, 1, 100, 30, 1000) + _month(2025, 2, 100, 30, 2000)
        result = je.test_month_end_clustering(entries, JETestingConfig())
        assert "Client-baseline comparison not run" in result.description
