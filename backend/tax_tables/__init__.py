"""Annual tax tables — Sprint 860 (CEO directive 2026-11-14).

One module per tax year (``ty<year>.py``: a module name cannot start with a
digit) holds every statutory figure the W-2 and 1099 tools apply for that year,
each with its citation, source URL and the sentence it was read from, plus a
practitioner sign-off per tool. The engines read their tables from here.

Adding a year: copy the latest module, update every figure from its source,
add it to ``TABLES`` below, and run ``tests/test_sprint860_tax_tables.py`` — the
invariants (rates × bases, catch-up floors, year-over-year moves, citations)
check the arithmetic. The tool refuses the year until the sign-off is recorded
(``tax_figures_status.enforce_tax_year_signed_off``). The yearly calendar is in
``docs/runbooks/annual-tax-tables.md``.
"""

from __future__ import annotations

from tax_tables import ty2025, ty2026
from tax_tables._schema import Figure, SignOff, TaxYearTable, ThresholdFigure, W2Figures

TABLES: dict[int, TaxYearTable] = {
    2025: ty2025.TABLE,
    2026: ty2026.TABLE,
}

TOOLS: tuple[str, ...] = ("w2_reconciliation", "form_1099")


def w2_years() -> list[int]:
    return sorted(year for year, table in TABLES.items() if table.w2 is not None)


def form_1099_years() -> list[int]:
    return sorted(year for year, table in TABLES.items() if table.form_1099 is not None)


def years_for(tool: str) -> list[int]:
    if tool == "w2_reconciliation":
        return w2_years()
    if tool == "form_1099":
        return form_1099_years()
    raise KeyError(tool)


def is_signed_off(tool: str, year: int) -> bool:
    table = TABLES.get(year)
    return table is not None and year in years_for(tool) and table.sign_off(tool).is_signed


def signed_off_years(tool: str) -> list[int]:
    return [year for year in years_for(tool) if is_signed_off(tool, year)]


__all__ = [
    "TABLES",
    "TOOLS",
    "Figure",
    "SignOff",
    "TaxYearTable",
    "ThresholdFigure",
    "W2Figures",
    "form_1099_years",
    "is_signed_off",
    "signed_off_years",
    "w2_years",
    "years_for",
]
