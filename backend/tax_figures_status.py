"""
Tax-figure status for the tools that apply built-in statutory figures.

Sprint 856 put a banner on each such tool and disabled both on a fixed date
(2026-12-15) unless a practitioner confirmed the 2026 figures. Sprint 860
replaces the one-off date with a per-year rule (CEO directive 2026-11-14):

* Each tax year's figures live in ``backend/tax_tables/ty<year>.py`` with a
  sign-off per tool (who, when, and that the sources are final).
* ``enforce_tax_year_signed_off`` refuses a run whose built-in table is not
  signed off — ``403 TAX_YEAR_NOT_SIGNED_OFF``. Through
  ``UNSIGNED_GRACE_UNTIL`` (the council's 2026-12-15 date) an unsigned table
  still runs behind the banner, so the tools do not go dark the day this lands.
* Form 1099 refuses a tax year after its latest table —
  ``400 TAX_YEAR_NOT_AVAILABLE`` (it used to reuse the latest table with a
  notice). W-2 already refuses a year with no table unless the caller supplies
  the figures (``w2_reconciliation_engine.statutory_limits_for_year``); a caller
  that supplies every required figure uses no built-in table and is not gated.
* ``season_table_gaps`` is the CI early warning: from Nov 1 of a year, that
  year's table must exist and be signed off for each tool (filings are due the
  next January). ``tests/test_sprint860_tax_tables.py`` warns from Nov 1 and
  fails from Jan 1.

Which tools this covers, verified per tool against the engines (Sprint 856):
W-2 / W-3 Reconciliation and Form 1099 Preparation. Not covered, because they
apply no year-indexed figure: Book-to-Tax (rates are the user's inputs; the
$10M Schedule M-3 test is not year-indexed), Depreciation (MACRS tables do not
vary by year; no bonus or §179 limit applied), Loan Amortization.

The banner text below is the single backend source. The frontend copy lives in
``frontend/src/content/tax-figures.ts``; ``tests/test_tax_figures_status.py``
fails if the two drift.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import HTTPException

import tax_tables

# The council's date (2026-10-28, Sprint 856 item 5): unsigned figures may run
# behind the banner through this day, and not after it.
UNSIGNED_GRACE_UNTIL = date(2026, 12, 15)

COVERED_TOOLS: tuple[str, ...] = tax_tables.TOOLS


def _join_years(years: list[int]) -> str:
    words = [str(y) for y in years]
    if not words:
        return "none yet"
    if len(words) == 1:
        return words[0]
    return f"{', '.join(words[:-1])} and {words[-1]}"


def w2_banner() -> str:
    years = tax_tables.w2_years()
    signed = tax_tables.signed_off_years("w2_reconciliation")
    return (
        f"Statutory limits built in for tax year{'s' if len(years) != 1 else ''} {_join_years(years)}; "
        f"signed off by a practitioner: {_join_years(signed)}. Other years are refused unless you supply "
        "the figures. Verify before relying."
    )


def form_1099_banner() -> str:
    years = tax_tables.form_1099_years()
    signed = tax_tables.signed_off_years("form_1099")
    return (
        f"Reporting thresholds built in for tax years through {max(years)} (years before {min(years)} use the "
        f"{min(years)} figures); signed off by a practitioner: {_join_years(signed)}. Later years are refused "
        "until their figures are added. Verify before relying."
    )


W2_TAX_FIGURES_BANNER = w2_banner()
FORM_1099_TAX_FIGURES_BANNER = form_1099_banner()

TAX_FIGURES_BANNERS: dict[str, str] = {
    "w2_reconciliation": W2_TAX_FIGURES_BANNER,
    "form_1099": FORM_1099_TAX_FIGURES_BANNER,
}


def table_year_for(tool: str, tax_year: int) -> int | None:
    """The table a run for ``tax_year`` applies, or None when there is none.

    W-2: the year's own table. Form 1099: the latest table not after the year
    (the 2025 table serves every earlier year); None after the latest table.
    """
    years = tax_tables.years_for(tool)
    if tool == "w2_reconciliation":
        return tax_year if tax_year in years else None
    if tax_year > max(years):
        return None
    eligible = [y for y in years if y <= tax_year]
    return max(eligible) if eligible else min(years)


def _today() -> date:
    """The current UTC date (a seam so tests can move the clock)."""
    return datetime.now(UTC).date()


def enforce_tax_year_signed_off(tool: str, tax_year: int) -> None:
    """Refuse a run on built-in figures that are missing or not signed off.

    Called at the top of each covered tool's analysis and export routes. A W-2
    year with no table passes through here: the engine refuses it (or the caller
    supplied every figure, and no built-in table is used).
    """
    table_year = table_year_for(tool, tax_year)
    if table_year is None:
        if tool == "w2_reconciliation":
            return
        latest = max(tax_tables.years_for(tool))
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TAX_YEAR_NOT_AVAILABLE",
                "message": (
                    f"Tax year {tax_year} is not available: Paciolus has reporting thresholds through tax year "
                    f"{latest}. The {tax_year} figures are added once the IRS publishes them and a "
                    "practitioner signs them off."
                ),
                "resource": "tool_access",
            },
        )
    if tax_tables.is_signed_off(tool, table_year):
        return
    if _today() <= UNSIGNED_GRACE_UNTIL:
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "TAX_YEAR_NOT_SIGNED_OFF",
            "message": (
                f"Tax year {tax_year} is unavailable until a practitioner signs off the built-in {table_year} figures."
            ),
            "resource": "tool_access",
        },
    )


def runnable_years(tool: str) -> list[int]:
    """Built-in years a run can use today: signed off, or unsigned within the grace period."""
    in_grace = _today() <= UNSIGNED_GRACE_UNTIL
    return [y for y in tax_tables.years_for(tool) if in_grace or tax_tables.is_signed_off(tool, y)]


def season_tax_year(today: date) -> tuple[int, str]:
    """The tax year whose table must be ready, and whether a gap warns or fails.

    From Nov 1 of year Y the Y table must be ready (W-2s and 1099s are due the
    next January): a gap warns. From Jan 1 of Y+1 the same gap fails.
    """
    if today.month >= 11:
        return today.year, "warn"
    return today.year - 1, "fail"


def season_table_gaps(today: date) -> list[str]:
    """Covered tools whose table for the season's tax year is missing or unsigned."""
    year, _ = season_tax_year(today)
    gaps = []
    for tool in COVERED_TOOLS:
        if year not in tax_tables.years_for(tool):
            gaps.append(f"{tool}: no {year} table")
        elif not tax_tables.is_signed_off(tool, year):
            gaps.append(f"{tool}: {year} table not signed off")
    return gaps
