"""
Sprint 816 — elapsed-time tests measure to period end, not to the processing date.

FA-T11 (depreciation recalculation) divided accumulated depreciation — stated
as of period end — by years elapsed to *today*. A register depreciated exactly
on schedule to 2025-12-31 and tested ten months later had 6 of 6 assets
flagged. IN-06 (slow-moving) had the same dependency. Every date here is fixed
or relative to a fixed reference, so nothing depends on the wall clock.
"""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

from fixed_asset_testing_engine import FixedAssetTestingConfig, run_fixed_asset_testing
from inventory_testing_engine import InventoryTestingConfig, run_inventory_testing
from shared.reference_date import resolve_reference_date

PERIOD_END = date(2025, 12, 31)

FA_COLUMNS = [
    "Asset ID",
    "Description",
    "Category",
    "Cost",
    "Accumulated Depreciation",
    "Acquisition Date",
    "Useful Life",
    "Depreciation Method",
    "Residual Value",
]


def _on_schedule_register() -> list[dict]:
    """Six assets depreciated exactly straight-line to PERIOD_END."""
    rows = []
    for n, (acquired, life) in enumerate(
        [
            ("2019-01-01", 10),
            ("2020-01-01", 10),
            ("2021-01-01", 8),
            ("2022-01-01", 7),
            ("2023-01-01", 5),
            ("2024-01-01", 5),
        ],
        start=1,
    ):
        years = (PERIOD_END - date.fromisoformat(acquired)).days / 365.25
        rows.append(
            {
                "Asset ID": f"FA{n}",
                "Description": "Equipment",
                "Category": "Machinery",
                "Cost": 100000.0,
                "Accumulated Depreciation": round(100000 * years / life, 2),
                "Acquisition Date": acquired,
                "Useful Life": life,
                "Depreciation Method": "Straight-Line",
                "Residual Value": 0.0,
            }
        )
    return rows


def _recalc(config: FixedAssetTestingConfig) -> dict:
    result = run_fixed_asset_testing(
        rows=_on_schedule_register(), column_names=FA_COLUMNS, config=config, column_mapping=None
    ).to_dict()
    return next(t for t in result["test_results"] if t["test_key"] == "depreciation_recalc")


def test_on_schedule_register_is_clean_when_measured_to_period_end():
    test = _recalc(FixedAssetTestingConfig(reference_date=PERIOD_END, reference_date_source="engagement_period_end"))
    assert test["entries_flagged"] == 0
    assert "measured to 2025-12-31 (engagement period end)" in test["description"]


def test_measuring_ten_months_late_is_what_flagged_every_asset():
    """The pre-fix behaviour, pinned with a fixed date rather than the clock."""
    test = _recalc(FixedAssetTestingConfig(reference_date=date(2026, 10, 23)))
    assert test["entries_flagged"] == 6


def test_slow_moving_days_are_counted_to_the_reference_date():
    columns = ["Item ID", "Description", "Quantity", "Unit Cost", "Extended Value", "Last Movement Date"]
    rows = [
        {
            "Item ID": "SKU1",
            "Description": "Widget",
            "Quantity": 10,
            "Unit Cost": 5.0,
            "Extended Value": 50.0,
            "Last Movement Date": (PERIOD_END - timedelta(days=30)).isoformat(),
        }
    ]

    def slow_moving(reference: date) -> dict:
        config = InventoryTestingConfig(reference_date=reference, reference_date_source="as_of_date")
        result = run_inventory_testing(rows=rows, column_names=columns, config=config, column_mapping=None).to_dict()
        return next(t for t in result["test_results"] if t["test_key"] == "slow_moving")

    assert slow_moving(PERIOD_END)["entries_flagged"] == 0
    assert slow_moving(PERIOD_END + timedelta(days=300))["entries_flagged"] == 1
    assert "measured to 2025-12-31 (as-of date supplied)" in slow_moving(PERIOD_END)["description"]


class TestResolveReferenceDate:
    @pytest.mark.parametrize("raw", ["2025-12-31", "12/31/2025", "31/12/2025"])
    def test_explicit_as_of_date_wins(self, raw):
        assert resolve_reference_date(raw, None, 1, None) == (PERIOD_END, "as_of_date")

    def test_unparseable_as_of_date_is_rejected_not_ignored(self):
        with pytest.raises(HTTPException) as exc_info:
            resolve_reference_date("next tuesday", None, 1, None)
        assert exc_info.value.status_code == 400

    def test_falls_back_to_the_engagement_period_end(self, db_session, make_user, make_client):
        from engagement_manager import EngagementManager

        user = make_user()
        client = make_client(user=user)
        engagement = EngagementManager(db_session).create_engagement(
            user.id, client.id, datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 12, 31, tzinfo=UTC)
        )

        assert resolve_reference_date(None, engagement.id, user.id, db_session) == (
            PERIOD_END,
            "engagement_period_end",
        )

    def test_without_either_the_engine_uses_the_processing_date(self):
        assert resolve_reference_date(None, None, 1, None) == (None, "processing_date")
