"""Sprint 846 — fixed-asset loose ends from the Sprint 823 register (A4, A5, A8).

Dates are built relative to a period end one year back, so nothing here ages.
"""

from datetime import date, timedelta

from fixed_asset_testing_engine import (
    FixedAssetTestingConfig,
    detect_fa_columns,
    parse_fa_entries,
    run_fixed_asset_testing,
)
from shared.parsing_helpers import infer_day_first, parse_date

_PERIOD_END = date(date.today().year - 1, 12, 31)
_Y = _PERIOD_END.year

_COLUMNS = [
    "Asset ID",
    "Description",
    "Cost",
    "Accumulated Depreciation",
    "Acquisition Date",
    "Useful Life",
    "Depreciation Method",
    "Residual Value",
]


def _run(rows: list[dict], columns: list[str] = _COLUMNS, reference_date: date = _PERIOD_END) -> dict:
    config = FixedAssetTestingConfig(reference_date=reference_date, reference_date_source="as_of_date")
    return run_fixed_asset_testing(rows=rows, column_names=columns, config=config).to_dict()


def _test(result: dict, key: str) -> dict:
    return next(t for t in result["test_results"] if t["test_key"] == key)


def _asset(n, cost, accum, acquired, life, method="Straight-Line", residual=0.0, life_header="Useful Life"):
    return {
        "Asset ID": f"FA{n}",
        "Description": f"Equipment {n}",
        "Cost": cost,
        "Accumulated Depreciation": accum,
        "Acquisition Date": acquired,
        life_header: life,
        "Depreciation Method": method,
        "Residual Value": residual,
    }


def _sl_accum(cost: float, life: float, acquired: date, as_of: date = _PERIOD_END) -> float:
    return round(cost / life * (as_of - acquired).days / 365.25, 2)


# --- A4: DD/MM/YYYY registers --------------------------------------------------


def test_infer_day_first_from_unambiguous_values():
    assert infer_day_first(["01/12/2020", "25/03/2021"]) is True
    assert infer_day_first(["12/01/2020", "03/25/2021"]) is False
    # No unambiguous value either way — keep the month-first default.
    assert infer_day_first(["01/02/2020", "03/04/2021"]) is False
    # Contradictory evidence — not a day-first column.
    assert infer_day_first(["25/03/2021", "03/25/2021"]) is False
    assert infer_day_first(["2021-03-25", None, "", 42]) is False


def test_parse_date_day_first_is_opt_in():
    assert parse_date("01/12/2020") == date(2020, 1, 12)
    assert parse_date("01/12/2020", day_first=True) == date(2020, 12, 1)
    assert parse_date("01-12-2020", day_first=True) == date(2020, 12, 1)
    # Unambiguous forms are unaffected by the flag.
    assert parse_date("2020-01-12", day_first=True) == date(2020, 1, 12)
    assert parse_date("25/03/2021", day_first=True) == date(2021, 3, 25)


def test_day_first_register_is_not_read_month_first():
    """A4: '01/12/Y' in a DD/MM register was read as 12 January — 11 months off, flagged HIGH."""
    dec_1 = date(_Y - 2, 12, 1)
    mar_25 = date(_Y - 3, 3, 25)
    rows = [
        _asset(1, 100_000.0, _sl_accum(100_000, 10, dec_1), dec_1.strftime("%d/%m/%Y"), 10),
        _asset(2, 50_000.0, _sl_accum(50_000, 10, mar_25), mar_25.strftime("%d/%m/%Y"), 10),
    ]
    assert _test(_run(rows), "depreciation_recalc")["entries_flagged"] == 0


def test_month_first_register_is_unchanged():
    dec_1 = date(_Y - 2, 12, 1)
    mar_25 = date(_Y - 3, 3, 25)
    rows = [
        _asset(1, 100_000.0, _sl_accum(100_000, 10, dec_1), dec_1.strftime("%m/%d/%Y"), 10),
        _asset(2, 50_000.0, _sl_accum(50_000, 10, mar_25), mar_25.strftime("%m/%d/%Y"), 10),
    ]
    assert _test(_run(rows), "depreciation_recalc")["entries_flagged"] == 0


def test_day_first_register_still_catches_under_depreciation():
    dec_1 = date(_Y - 2, 12, 1)
    mar_25 = date(_Y - 3, 3, 25)
    rows = [
        _asset(1, 100_000.0, round(_sl_accum(100_000, 10, dec_1) * 0.5, 2), dec_1.strftime("%d/%m/%Y"), 10),
        _asset(2, 50_000.0, _sl_accum(50_000, 10, mar_25), mar_25.strftime("%d/%m/%Y"), 10),
    ]
    assert _test(_run(rows), "depreciation_recalc")["entries_flagged"] == 1


# --- A5: half-year convention -------------------------------------------------


def test_half_year_convention_register_is_not_flagged():
    """A5: half-year registers were flagged although the docstring said 5% absorbed the convention.

    An asset bought 1 November two years before period end carries 2.5 years under the
    half-year convention; exact-day proration expects ~2.17 years — a 15% "variance".
    """
    nov_1 = date(_Y - 2, 11, 1)
    in_year = date(_Y, 11, 1)
    early = date(_Y - 3, 2, 1)
    rows = [
        _asset(1, 100_000.0, 100_000 / 5 * 2.5, nov_1.isoformat(), 5),
        _asset(2, 60_000.0, 60_000 / 5 * 0.5, in_year.isoformat(), 5),
        _asset(3, 40_000.0, 40_000 / 10 * 3.5, early.isoformat(), 10),
    ]
    assert _test(_run(rows), "depreciation_recalc")["entries_flagged"] == 0


def test_half_year_declining_balance_register_is_not_flagged():
    # Bought in the final year: half a year of DDB (22%) vs two months by actual days (8%).
    nov_1 = date(_Y, 11, 1)
    rate = 2 / 5
    accum = round(100_000 * (1 - (1 - rate) ** 0.5), 2)
    rows = [_asset(1, 100_000.0, accum, nov_1.isoformat(), 5, method="Double-Declining Balance")]
    assert _test(_run(rows), "depreciation_recalc")["entries_flagged"] == 0


def test_half_year_follows_a_non_calendar_fiscal_year():
    """Period end 30 June: the half-year midpoint is 31 December of the acquiring fiscal year."""
    period_end = date(_Y, 6, 30)
    acquired = date(_Y - 2, 5, 1)  # FY ending 30 June Y-2 → 0.5 + 2 full years = 2.5 years
    rows = [_asset(1, 100_000.0, 100_000 / 10 * 2.5, acquired.isoformat(), 10)]
    result = _test(_run(rows, reference_date=period_end), "depreciation_recalc")
    assert result["entries_flagged"] == 0


def test_misstatement_outside_both_conventions_is_still_flagged():
    nov_1 = date(_Y - 2, 11, 1)
    # 3.0 years booked: 20% over half-year (2.5y), 38% over exact-day (2.17y).
    rows = [_asset(1, 100_000.0, 100_000 / 5 * 3.0, nov_1.isoformat(), 5)]
    flagged = _test(_run(rows), "depreciation_recalc")["flagged_entries"]
    assert len(flagged) == 1
    assert flagged[0]["details"]["convention"] == "half-year"


def test_exact_day_register_still_matches():
    acquired = _PERIOD_END - timedelta(days=800)
    rows = [_asset(1, 100_000.0, _sl_accum(100_000, 7, acquired), acquired.isoformat(), 7)]
    assert _test(_run(rows), "depreciation_recalc")["entries_flagged"] == 0


# --- A8: useful life in months ------------------------------------------------


def test_useful_life_months_column_is_converted_to_years():
    """A8: 'Useful Life (Months)' = 60 was read as 60 years — an FA-05 outlier and a wrong FA-T11."""
    header = "Useful Life (Months)"
    columns = [header if c == "Useful Life" else c for c in _COLUMNS]
    acquired = date(_Y - 2, 1, 1)
    rows = [_asset(1, 100_000.0, _sl_accum(100_000, 5, acquired), acquired.isoformat(), 60, life_header=header)]

    detection = detect_fa_columns(columns)
    assert detection.useful_life_column == header
    assert parse_fa_entries(rows, detection)[0].useful_life == 5.0

    result = _run(rows, columns=columns)
    assert _test(result, "useful_life_outliers")["entries_flagged"] == 0
    assert _test(result, "depreciation_recalc")["entries_flagged"] == 0
    assert any("months" in note.lower() for note in result["column_detection"]["detection_notes"])


def test_useful_life_months_header_variants_are_detected():
    for header in ("Life (Months)", "Useful Life Months", "Life in Months", "Useful Life (mos)"):
        detection = detect_fa_columns(["Asset ID", "Cost", header])
        assert detection.useful_life_column == header, header
        rows = [{"Asset ID": "A", "Cost": 1, header: 36}]
        assert parse_fa_entries(rows, detection)[0].useful_life == 3.0, header


def test_useful_life_years_column_is_unchanged():
    detection = detect_fa_columns(["Asset ID", "Cost", "Useful Life Years"])
    rows = [{"Asset ID": "A", "Cost": 1, "Useful Life Years": 7}]
    assert parse_fa_entries(rows, detection)[0].useful_life == 7.0


def test_manually_mapped_months_column_is_converted():
    header = "Mos"
    columns = ["Asset ID", "Cost", header]
    rows = [{"Asset ID": "A", "Cost": 1000, header: 24}]
    config = FixedAssetTestingConfig(reference_date=_PERIOD_END, reference_date_source="as_of_date")
    result = run_fixed_asset_testing(
        rows=rows, column_names=columns, config=config, column_mapping={"useful_life_column": header}
    )
    # "Mos" is a months abbreviation — still converted when mapped by hand.
    assert result.test_results is not None
    detection = result.column_detection
    assert parse_fa_entries(rows, detection)[0].useful_life == 2.0
