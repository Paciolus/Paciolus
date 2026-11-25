"""
Sprint 860: the annual tax tables do their own arithmetic.

A reviewer skims each year's table; these tests check what can be checked
without a person: every figure cites a source, a fetched figure quotes the
sentence that states it, indexed amounts never fall, a move over 10% has been
acknowledged, the age 60-63 catch-ups respect their statutory floor, and the
engines apply exactly what the tables hold.

The season check reads the real date on purpose: from Nov 1 of a year it warns
when that year's table is missing or unsigned; from Jan 1 it fails.
"""

from __future__ import annotations

import warnings
from datetime import date
from decimal import Decimal

import pytest

import tax_figures_status as tfs
import tax_tables
from form_1099_engine import THRESHOLDS_BY_TABLE_YEAR
from w2_reconciliation_engine import STATUTORY_LIMITS_BY_YEAR

# Figures fetched with their excerpt from this year on (2025 was carried over).
FIRST_EXCERPTED_YEAR = 2026
LARGE_MOVE = Decimal("0.10")


def _w2_figures(year: int) -> dict[str, tax_tables.Figure]:
    w2 = tax_tables.TABLES[year].w2
    return w2.figures() if w2 is not None else {}


def _1099_figures(year: int) -> dict[str, tax_tables.Figure]:
    items = tax_tables.TABLES[year].form_1099 or ()
    return {item.key: item.amount for item in items}


def _all_figures(year: int) -> dict[str, tax_tables.Figure]:
    return {**_w2_figures(year), **_1099_figures(year)}


def _as_written(value: Decimal) -> str:
    """How a source writes the figure: 6.2%, $184,500."""
    if value < 1:
        return f"{(value * 100).normalize():f}%"
    return f"${value:,.0f}"


YEARS = sorted(tax_tables.TABLES)
CONSECUTIVE = list(zip(YEARS, YEARS[1:]))


@pytest.mark.parametrize("year", YEARS)
def test_every_figure_cites_a_source(year):
    for name, figure in _all_figures(year).items():
        assert figure.citation.strip(), f"{year} {name}: no citation"
        assert figure.source_url.startswith("https://"), f"{year} {name}: no source URL"


@pytest.mark.parametrize("year", [y for y in YEARS if y >= FIRST_EXCERPTED_YEAR])
def test_every_fetched_figure_quotes_the_sentence_that_states_it(year):
    for name, figure in _all_figures(year).items():
        assert figure.excerpt.strip(), f"{year} {name}: no excerpt"
        assert _as_written(figure.value) in figure.excerpt, (
            f"{year} {name}: the excerpt does not state {_as_written(figure.value)}: {figure.excerpt!r}"
        )


@pytest.mark.parametrize("prior, year", CONSECUTIVE)
def test_no_figure_falls_year_over_year(prior, year):
    before, after = _all_figures(prior), _all_figures(year)
    for name in before.keys() & after.keys():
        assert after[name].value >= before[name].value, f"{name} fell from {prior} to {year}"


@pytest.mark.parametrize("prior, year", CONSECUTIVE)
def test_a_move_over_ten_percent_is_acknowledged(prior, year):
    before, after = _all_figures(prior), _all_figures(year)
    acknowledged = tax_tables.TABLES[year].acknowledged_large_moves
    large = {
        name
        for name in before.keys() & after.keys()
        if before[name].value and abs(after[name].value / before[name].value - 1) > LARGE_MOVE
    }
    assert large <= set(acknowledged), f"{year}: moves over 10% not acknowledged: {sorted(large - set(acknowledged))}"
    assert set(acknowledged) <= large, f"{year}: acknowledged but not over 10%: {sorted(set(acknowledged) - large)}"


@pytest.mark.parametrize("year", YEARS)
def test_age_60_63_catch_ups_respect_their_statutory_floor(year):
    """IRC §414(v)(2)(E) (SECURE 2.0 §109): the greater of a floor ($10,000, or
    $5,000 for SIMPLE) and 150% of the 2025 regular catch-up — then indexed, so
    never below that. (It is *not* 150% of the same year's regular catch-up:
    2026's 401(k) figure stays $11,250 while the regular one rose to $8,000.)"""
    w2 = tax_tables.TABLES[year].w2
    base = tax_tables.TABLES[2025].w2
    assert w2 is not None and base is not None
    floor_401k = max(Decimal("10000"), base.limit_401k_catchup_50.value * Decimal("1.5"))
    assert w2.limit_401k_catchup_60_63.value >= floor_401k
    if w2.limit_simple_catchup_60_63 is not None and base.limit_simple_catchup_50 is not None:
        floor_simple = max(Decimal("5000"), base.limit_simple_catchup_50.value * Decimal("1.5"))
        assert w2.limit_simple_catchup_60_63.value >= floor_simple
    if year == 2025:
        assert w2.limit_401k_catchup_60_63.value == floor_401k


@pytest.mark.parametrize(
    "year, max_tax",
    [(2025, Decimal("10918.20")), (2026, Decimal("11439.00"))],
)
def test_social_security_maximum_tax_is_wage_base_times_rate(year, max_tax):
    limits = STATUTORY_LIMITS_BY_YEAR[year]
    assert (limits.ss_wage_base * limits.ss_rate).quantize(Decimal("0.01")) == max_tax


@pytest.mark.parametrize("year", YEARS)
def test_engines_apply_exactly_what_the_tables_hold(year):
    limits = STATUTORY_LIMITS_BY_YEAR[year]
    for name, figure in _w2_figures(year).items():
        assert getattr(limits, name) == figure.value, name
    applied = {f"{i.form_type.value} box {i.box}": i.amount for i in THRESHOLDS_BY_TABLE_YEAR[year]}
    assert applied == {k: f.value for k, f in _1099_figures(year).items()}


@pytest.mark.parametrize("year", YEARS)
def test_every_table_in_use_has_a_sign_off_record_per_tool(year):
    table = tax_tables.TABLES[year]
    for tool in tax_tables.TOOLS:
        if year in tax_tables.years_for(tool):
            assert tool in table.sign_offs, f"{year}: no sign-off record for {tool}"


class TestSeason:
    @pytest.mark.parametrize(
        "today, expected",
        [
            (date(2026, 10, 31), (2025, "fail")),
            (date(2026, 11, 1), (2026, "warn")),
            (date(2026, 12, 31), (2026, "warn")),
            (date(2027, 1, 1), (2026, "fail")),
        ],
    )
    def test_season_year_and_mode(self, today, expected):
        assert tfs.season_tax_year(today) == expected

    def test_gaps_name_missing_and_unsigned_tables(self, monkeypatch):
        monkeypatch.setattr(tax_tables, "is_signed_off", lambda tool, year: tool == "form_1099")
        assert tfs.season_table_gaps(date(2026, 11, 2)) == ["w2_reconciliation: 2026 table not signed off"]
        assert tfs.season_table_gaps(date(2027, 11, 2)) == [
            "w2_reconciliation: no 2027 table",
            "form_1099: no 2027 table",
        ]


def test_this_seasons_tables_are_ready():
    """Reads the real date. Warns from Nov 1; fails from Jan 1 (runbook: docs/runbooks/annual-tax-tables.md)."""
    today = date.today()
    year, mode = tfs.season_tax_year(today)
    gaps = tfs.season_table_gaps(today)
    if not gaps:
        return
    message = (
        f"Tax year {year} tables are not ready: {'; '.join(gaps)}. Add backend/tax_tables/ty{year}.py from "
        "the sources and record the practitioner sign-off (docs/runbooks/annual-tax-tables.md)."
    )
    if mode == "fail":
        pytest.fail(message)
    warnings.warn(message, stacklevel=1)
