"""
Depreciation Engine (Sprint 626).

Calculates period-by-period depreciation schedules for fixed assets under both
book and tax conventions. Form-input only — zero-storage compliant.

Book methods supported:
- Straight-line (SL)
- Declining balance with optional switch to SL (DB)
- Sum-of-the-years' digits (SYD)
- Units of production (UOP)

Tax (MACRS) methods supported — this list is exhaustive, and every
combination outside it raises ``DepreciationInputError`` rather than falling
back to a different system (Sprint 795):

===========================  ===========  ==================================
System                       Convention   Property classes
===========================  ===========  ==================================
GDS 200% declining balance   half-year    3, 5, 7, 10
GDS 150% declining balance   half-year    15, 20
GDS 200% declining balance   mid-quarter  5 (quarters 1-4)
===========================  ===========  ==================================

MACRS percentages are reproduced from IRS Publication 946 Table A-1 (half-year,
200% and 150% DB) and Tables A-2/A-3/A-4/A-5 (mid-quarter, 5-year property).

**Not available in this release**, and rejected with a named error rather than
approximated: the GDS straight-line election; the 150% DB election for 3/5/7/10-
year property; mid-quarter for classes other than 5; and the mid-month
convention, which applies to 27.5-year residential rental and 39-year
nonresidential real property. Those need practitioner-confirmed tables —
Sprint 795 Step 0.

Before 2026-10-22 this docstring claimed mid-month, 27.5/39-year real property
and "Table A-6" support. None existed: ``validate()`` rejects both classes, and
the mid-month path computed straight line over the asset's *book* life. The
list above is written from the dispatch table rather than from intent.

All monetary math uses Decimal with HALF_UP rounding at the schedule output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Literal, Optional

CENT = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")

# =============================================================================
# Enums and config
# =============================================================================


class BookMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS_DIGITS = "sum_of_years_digits"
    UNITS_OF_PRODUCTION = "units_of_production"


class MacrsConvention(str, Enum):
    HALF_YEAR = "half_year"
    MID_QUARTER = "mid_quarter"
    MID_MONTH = "mid_month"


class MacrsSystem(str, Enum):
    GDS_200 = "gds_200db"  # 200% declining balance
    GDS_150 = "gds_150db"  # 150% declining balance
    GDS_SL = "gds_sl"  # Straight-line GDS


class DepreciationInputError(ValueError):
    """Raised for invalid depreciation parameters."""


# =============================================================================
# MACRS tables (IRS Publication 946)
# =============================================================================

# GDS half-year convention, 200% DB switching to SL
# Source: IRS Pub 946 Table A-1
MACRS_HY_200DB: dict[int, list[Decimal]] = {
    3: [Decimal("33.33"), Decimal("44.45"), Decimal("14.81"), Decimal("7.41")],
    5: [
        Decimal("20.00"),
        Decimal("32.00"),
        Decimal("19.20"),
        Decimal("11.52"),
        Decimal("11.52"),
        Decimal("5.76"),
    ],
    7: [
        Decimal("14.29"),
        Decimal("24.49"),
        Decimal("17.49"),
        Decimal("12.49"),
        Decimal("8.93"),
        Decimal("8.92"),
        Decimal("8.93"),
        Decimal("4.46"),
    ],
    10: [
        Decimal("10.00"),
        Decimal("18.00"),
        Decimal("14.40"),
        Decimal("11.52"),
        Decimal("9.22"),
        Decimal("7.37"),
        Decimal("6.55"),
        Decimal("6.55"),
        Decimal("6.56"),
        Decimal("6.55"),
        Decimal("3.28"),
    ],
}

# GDS half-year convention, 150% DB switching to SL (15- and 20-year property)
# Source: IRS Pub 946 Table A-1 (continued)
MACRS_HY_150DB: dict[int, list[Decimal]] = {
    15: [
        Decimal("5.00"),
        Decimal("9.50"),
        Decimal("8.55"),
        Decimal("7.70"),
        Decimal("6.93"),
        Decimal("6.23"),
        Decimal("5.90"),
        Decimal("5.90"),
        Decimal("5.91"),
        Decimal("5.90"),
        Decimal("5.91"),
        Decimal("5.90"),
        Decimal("5.91"),
        Decimal("5.90"),
        Decimal("5.91"),
        Decimal("2.95"),
    ],
    20: [
        Decimal("3.750"),
        Decimal("7.219"),
        Decimal("6.677"),
        Decimal("6.177"),
        Decimal("5.713"),
        Decimal("5.285"),
        Decimal("4.888"),
        Decimal("4.522"),
        Decimal("4.462"),
        Decimal("4.461"),
        Decimal("4.462"),
        Decimal("4.461"),
        Decimal("4.462"),
        Decimal("4.461"),
        Decimal("4.462"),
        Decimal("4.461"),
        Decimal("4.462"),
        Decimal("4.461"),
        Decimal("4.462"),
        Decimal("4.461"),
        Decimal("2.231"),
    ],
}

# Mid-quarter convention, 200% DB, 5-year property — IRS Pub 946 Table A-2/3/4/5
# Quarter 1 placed in service
MACRS_MQ_5YR_200DB: dict[int, list[Decimal]] = {
    1: [
        Decimal("35.00"),
        Decimal("26.00"),
        Decimal("15.60"),
        Decimal("11.01"),
        Decimal("11.01"),
        Decimal("1.38"),
    ],
    2: [
        Decimal("25.00"),
        Decimal("30.00"),
        Decimal("18.00"),
        Decimal("11.37"),
        Decimal("11.37"),
        Decimal("4.26"),
    ],
    3: [
        Decimal("15.00"),
        Decimal("34.00"),
        Decimal("20.40"),
        Decimal("12.24"),
        Decimal("11.30"),
        Decimal("7.06"),
    ],
    4: [
        Decimal("5.00"),
        Decimal("38.00"),
        Decimal("22.80"),
        Decimal("13.68"),
        Decimal("10.94"),
        Decimal("9.58"),
    ],
}


@dataclass
class AssetConfig:
    """Inputs for a single asset depreciation schedule."""

    asset_name: str
    cost: Decimal
    salvage_value: Decimal = ZERO
    useful_life_years: int = 5
    placed_in_service_year: Optional[int] = None
    placed_in_service_quarter: Literal[1, 2, 3, 4] = 1
    placed_in_service_month: int = 1  # Real property mid-month convention
    book_method: BookMethod = BookMethod.STRAIGHT_LINE
    db_factor: Decimal = Decimal("2")  # 2.0 = DDB, 1.5 = 150% DB
    units_total: Optional[Decimal] = None  # For UOP method
    units_per_year: list[Decimal] = field(default_factory=list)
    # MACRS / tax inputs
    macrs_system: Optional[MacrsSystem] = None  # If None, no tax schedule
    # 3, 5, 7, 10, 15, 20 — enforced by validate(). Real-property classes
    # (27.5 / 39) are NOT supported; the comment here used to list them while
    # the validator three lines below rejected them.
    macrs_property_class: Optional[int] = None
    macrs_convention: MacrsConvention = MacrsConvention.HALF_YEAR
    tax_rate: Decimal = Decimal("0.21")  # Federal corporate

    def validate(self) -> None:
        if self.cost <= 0:
            raise DepreciationInputError("Cost must be positive.")
        if self.salvage_value < 0:
            raise DepreciationInputError("Salvage value cannot be negative.")
        if self.salvage_value >= self.cost:
            raise DepreciationInputError("Salvage value must be less than cost.")
        if self.useful_life_years <= 0:
            raise DepreciationInputError("Useful life must be positive.")
        if self.useful_life_years > 50:
            raise DepreciationInputError("Useful life exceeds 50-year cap.")
        if self.book_method == BookMethod.UNITS_OF_PRODUCTION:
            if self.units_total is None or self.units_total <= 0:
                raise DepreciationInputError("Units of production requires positive units_total.")
            if not self.units_per_year:
                raise DepreciationInputError("Units of production requires units_per_year list.")
            if any(u < 0 for u in self.units_per_year):
                raise DepreciationInputError("Units per year cannot be negative.")
        if self.book_method == BookMethod.DECLINING_BALANCE:
            if self.db_factor <= 0:
                raise DepreciationInputError("Declining balance factor must be positive.")
        if self.macrs_system is not None:
            if self.macrs_property_class is None:
                raise DepreciationInputError("MACRS schedule requires macrs_property_class.")
            if self.macrs_property_class not in (3, 5, 7, 10, 15, 20):
                raise DepreciationInputError("MACRS personal property classes must be one of 3, 5, 7, 10, 15, 20.")
            if not (1 <= self.placed_in_service_quarter <= 4):
                raise DepreciationInputError("Placed-in-service quarter must be 1-4.")


# =============================================================================
# Result dataclasses
# =============================================================================


@dataclass
class YearEntry:
    year_index: int
    calendar_year: Optional[int]
    beginning_book_value: Decimal
    depreciation: Decimal
    accumulated_depreciation: Decimal
    ending_book_value: Decimal

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "year_index": self.year_index,
            "calendar_year": self.calendar_year,
            "beginning_book_value": str(self.beginning_book_value),
            "depreciation": str(self.depreciation),
            "accumulated_depreciation": str(self.accumulated_depreciation),
            "ending_book_value": str(self.ending_book_value),
        }


@dataclass
class BookTaxComparisonEntry:
    year_index: int
    book_depreciation: Decimal
    tax_depreciation: Decimal
    timing_difference: Decimal  # tax - book
    deferred_tax_change: Decimal  # timing_difference * tax_rate
    cumulative_deferred_tax: Decimal

    def to_dict(self) -> dict[str, str | int]:
        return {
            "year_index": self.year_index,
            "book_depreciation": str(self.book_depreciation),
            "tax_depreciation": str(self.tax_depreciation),
            "timing_difference": str(self.timing_difference),
            "deferred_tax_change": str(self.deferred_tax_change),
            "cumulative_deferred_tax": str(self.cumulative_deferred_tax),
        }


@dataclass
class DepreciationResult:
    config: AssetConfig
    book_schedule: list[YearEntry]
    tax_schedule: list[YearEntry]
    book_tax_comparison: list[BookTaxComparisonEntry]
    total_book_depreciation: Decimal
    total_tax_depreciation: Decimal
    cumulative_deferred_tax: Decimal

    def to_dict(self) -> dict[str, object]:
        return {
            "inputs": {
                "asset_name": self.config.asset_name,
                "cost": str(self.config.cost),
                "salvage_value": str(self.config.salvage_value),
                "useful_life_years": self.config.useful_life_years,
                "placed_in_service_year": self.config.placed_in_service_year,
                "placed_in_service_quarter": self.config.placed_in_service_quarter,
                "placed_in_service_month": self.config.placed_in_service_month,
                "book_method": self.config.book_method.value,
                "db_factor": str(self.config.db_factor),
                "macrs_system": self.config.macrs_system.value if self.config.macrs_system else None,
                "macrs_property_class": self.config.macrs_property_class,
                "macrs_convention": self.config.macrs_convention.value,
                "tax_rate": str(self.config.tax_rate),
            },
            "book_schedule": [y.to_dict() for y in self.book_schedule],
            "tax_schedule": [y.to_dict() for y in self.tax_schedule],
            "book_tax_comparison": [c.to_dict() for c in self.book_tax_comparison],
            "total_book_depreciation": str(self.total_book_depreciation),
            "total_tax_depreciation": str(self.total_tax_depreciation),
            "cumulative_deferred_tax": str(self.cumulative_deferred_tax),
        }


# =============================================================================
# Helpers
# =============================================================================


def _q(value: Decimal) -> Decimal:
    """Quantize to cents, HALF_UP."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _calendar_year(start_year: Optional[int], year_index: int) -> Optional[int]:
    return start_year + year_index - 1 if start_year else None


# =============================================================================
# Book methods
# =============================================================================


def _straight_line_schedule(config: AssetConfig) -> list[YearEntry]:
    depreciable_base = config.cost - config.salvage_value
    annual = depreciable_base / Decimal(config.useful_life_years)
    return _emit_year_entries(config, [annual] * config.useful_life_years)


def _declining_balance_schedule(config: AssetConfig) -> list[YearEntry]:
    """DB depreciation that switches to SL when SL would exceed DB.

    Standard book convention — guarantees the asset depreciates to salvage
    value within the useful life.
    """
    rate = config.db_factor / Decimal(config.useful_life_years)
    book_value = config.cost
    annual_charges: list[Decimal] = []
    switched = False
    for year in range(1, config.useful_life_years + 1):
        if not switched:
            db_charge = book_value * rate
            remaining_years = config.useful_life_years - year + 1
            sl_charge = (book_value - config.salvage_value) / Decimal(remaining_years)
            if sl_charge > db_charge:
                charge = sl_charge
                switched = True
            else:
                charge = db_charge
        else:
            remaining_years = config.useful_life_years - year + 1
            charge = (book_value - config.salvage_value) / Decimal(remaining_years)

        # Do not depreciate below salvage value
        if book_value - charge < config.salvage_value:
            charge = book_value - config.salvage_value
        annual_charges.append(charge)
        book_value = book_value - charge
    return _emit_year_entries(config, annual_charges)


def _sum_of_years_digits_schedule(config: AssetConfig) -> list[YearEntry]:
    n = config.useful_life_years
    sum_of_years = Decimal(n * (n + 1)) / Decimal(2)
    depreciable_base = config.cost - config.salvage_value
    annual_charges: list[Decimal] = []
    for year in range(1, n + 1):
        remaining = Decimal(n - year + 1)
        charge = depreciable_base * remaining / sum_of_years
        annual_charges.append(charge)
    return _emit_year_entries(config, annual_charges)


def _units_of_production_schedule(config: AssetConfig) -> list[YearEntry]:
    assert config.units_total is not None
    depreciable_base = config.cost - config.salvage_value
    rate_per_unit = depreciable_base / config.units_total
    annual_charges: list[Decimal] = []
    cumulative_units = ZERO
    for units in config.units_per_year:
        # Cap so we don't depreciate past the total productive life
        usable = min(units, config.units_total - cumulative_units)
        if usable < 0:
            usable = ZERO
        cumulative_units += usable
        annual_charges.append(rate_per_unit * usable)
    return _emit_year_entries(config, annual_charges)


def _emit_year_entries(config: AssetConfig, charges: list[Decimal]) -> list[YearEntry]:
    """Build YearEntry list from a list of annual charges.

    ROUNDING COMPOSITION — the schedule must foot (Sprint 795)
    ----------------------------------------------------------
    The schedule runs on **cent-quantized book values**. Previously the running
    book value was carried at full precision while each column was rounded
    independently at output, so the depreciation column did not sum to the
    depreciable base even though the final book value landed exactly on
    salvage: a $123,456.78 asset reported $123,456.77 of total depreciation
    against an ending book value of 0.00.

    Rounding the charge first and deriving the book value from it makes every
    row foot (``beginning - depreciation == ending``), makes the column
    reconcile down the page, and makes the total equal the base.
    """
    schedule: list[YearEntry] = []
    book_value = _q(config.cost)
    salvage = _q(config.salvage_value)
    accumulated = ZERO
    for idx, raw_charge in enumerate(charges, start=1):
        is_final = idx == len(charges)
        if is_final:
            # Final year absorbs all rounding drift so the asset lands exactly
            # on salvage value.
            charge = book_value - salvage
            if charge < ZERO:
                charge = ZERO
        else:
            charge = _q(raw_charge)
            if book_value - charge < salvage:
                charge = book_value - salvage
            if charge < ZERO:
                charge = ZERO
        beginning_bv = book_value
        book_value = beginning_bv - charge
        accumulated += charge
        schedule.append(
            YearEntry(
                year_index=idx,
                calendar_year=_calendar_year(config.placed_in_service_year, idx),
                beginning_book_value=beginning_bv,
                depreciation=charge,
                accumulated_depreciation=accumulated,
                ending_book_value=book_value,
            )
        )
    return schedule


def _book_schedule(config: AssetConfig) -> list[YearEntry]:
    if config.book_method == BookMethod.STRAIGHT_LINE:
        return _straight_line_schedule(config)
    if config.book_method == BookMethod.DECLINING_BALANCE:
        return _declining_balance_schedule(config)
    if config.book_method == BookMethod.SUM_OF_YEARS_DIGITS:
        return _sum_of_years_digits_schedule(config)
    if config.book_method == BookMethod.UNITS_OF_PRODUCTION:
        return _units_of_production_schedule(config)
    raise DepreciationInputError(f"Unsupported book method: {config.book_method}")


# =============================================================================
# MACRS / tax depreciation
# =============================================================================


# Which (system, convention) pairs this module holds a published table for,
# and which property classes each covers.
#
# THE SELECTED SYSTEM MUST REACH THIS LOOKUP (Sprint 795)
# -------------------------------------------------------
# Until 2026-10-22 ``_macrs_percentages`` dispatched on **convention and class
# only**. ``macrs_system`` was declared on the config, validated for non-null,
# echoed back in the API response, and used to decide whether a tax schedule
# existed at all — and never read by the percentage lookup. So a $100,000
# 5-year asset returned $20,000 of year-one tax depreciation whether the caller
# selected ``gds_200db``, ``gds_150db`` or ``gds_sl``, and the frontend offered
# all three in a dropdown. A practitioner electing straight-line received 200%
# declining-balance figures labelled as their election.
#
# The fix refuses rather than substitutes. Combinations without a published
# table in this module raise a named error saying exactly what is missing. That
# is deliberate: inventing statutory percentages from a code change is how the
# original defect became dangerous, and the tables below are reproduced from
# IRS Pub 946 rather than derived. Adding GDS straight-line and the 150% DB
# election for 3/5/7/10-year property needs practitioner-confirmed figures —
# tracked as Sprint 795 Step 0.


def _macrs_percentages(config: AssetConfig) -> list[Decimal]:
    """Return the year-by-year MACRS depreciation percentages (whole numbers).

    Dispatches on ``(macrs_system, macrs_convention, macrs_property_class)``.
    Every combination this module cannot serve raises
    :class:`DepreciationInputError` naming the gap — it never falls back to a
    different depreciation system.

    Example: a 5-year property, GDS 200% DB, half-year returns
        [20.00, 32.00, 19.20, 11.52, 11.52, 5.76].
    """
    cls = config.macrs_property_class
    system = config.macrs_system
    assert cls is not None
    assert system is not None

    if config.macrs_convention == MacrsConvention.HALF_YEAR:
        if system == MacrsSystem.GDS_200:
            if cls in MACRS_HY_200DB:
                return list(MACRS_HY_200DB[cls])
            if cls in MACRS_HY_150DB:
                raise DepreciationInputError(
                    f"{cls}-year property is depreciated under GDS using the 150% declining-balance "
                    f"method, not 200%. Select 'gds_150db' for this property class."
                )
            raise DepreciationInputError(f"Half-year GDS 200% DB table not available for class {cls}.")

        if system == MacrsSystem.GDS_150:
            if cls in MACRS_HY_150DB:
                return list(MACRS_HY_150DB[cls])
            raise DepreciationInputError(
                f"The GDS 150% declining-balance election for {cls}-year property is not available "
                f"in this release. Published 150% DB tables are provided for 15- and 20-year "
                f"property only. Supply the schedule manually or select 'gds_200db', which is the "
                f"GDS default for {cls}-year property."
            )

        if system == MacrsSystem.GDS_SL:
            raise DepreciationInputError(
                "The GDS straight-line election is not available in this release — no published "
                "straight-line table is provided, and substituting a declining-balance table would "
                "misstate the deduction. Use the book straight-line schedule, or supply the tax "
                "schedule manually."
            )

        raise DepreciationInputError(f"Unsupported MACRS system: {system}")

    if config.macrs_convention == MacrsConvention.MID_QUARTER:
        if system != MacrsSystem.GDS_200:
            raise DepreciationInputError(
                f"Mid-quarter tables in this release cover GDS 200% DB only, not {system.value}."
            )
        if cls != 5:
            raise DepreciationInputError("Mid-quarter MACRS limited to 5-year property in this implementation.")
        return list(MACRS_MQ_5YR_200DB[config.placed_in_service_quarter])

    if config.macrs_convention == MacrsConvention.MID_MONTH:
        # The mid-month convention applies to 27.5-year residential rental and
        # 39-year nonresidential real property. No table for either exists in
        # this module, and ``AssetConfig.validate`` rejects both classes.
        #
        # The previous implementation reached a helper that computed mid-month
        # straight line over the asset's **book** ``useful_life_years`` — a
        # number with no MACRS meaning. For a 5-year asset it returned
        # [19166.67, 20000, 20000, 20000, 20000, 833.33] on $100,000: it summed
        # to cost and looked entirely plausible. Rejecting is the only honest
        # answer until real-property tables are added (Sprint 795 Step 0).
        raise DepreciationInputError(
            "The mid-month convention applies to 27.5-year residential rental and 39-year "
            "nonresidential real property, for which this release provides no MACRS table. "
            "Use the half-year or mid-quarter convention for personal property."
        )

    raise DepreciationInputError(f"Unsupported MACRS convention: {config.macrs_convention}")


def _macrs_schedule(config: AssetConfig) -> list[YearEntry]:
    """Generate tax depreciation schedule using MACRS tables. Salvage value
    is ignored under MACRS — basis is full cost.
    """
    if config.macrs_system is None or config.macrs_property_class is None:
        return []
    pcts = _macrs_percentages(config)
    schedule: list[YearEntry] = []
    # Cent-quantized basis, for the same reason as _emit_year_entries: the
    # depreciation column has to sum to the basis it recovers (Sprint 795).
    basis = _q(config.cost)
    book_value = basis
    accumulated = ZERO
    n = len(pcts)
    for idx, pct in enumerate(pcts, start=1):
        is_final = idx == n
        if is_final:
            # The final year takes whatever remains, so the published table's
            # rounding never leaves a stub of basis undepreciated.
            charge = book_value
        else:
            charge = _q(basis * pct / HUNDRED)
            if charge > book_value:
                charge = book_value
        beginning_bv = book_value
        book_value = beginning_bv - charge
        accumulated += charge
        schedule.append(
            YearEntry(
                year_index=idx,
                calendar_year=_calendar_year(config.placed_in_service_year, idx),
                beginning_book_value=beginning_bv,
                depreciation=charge,
                accumulated_depreciation=accumulated,
                ending_book_value=book_value,
            )
        )
    return schedule


# =============================================================================
# Book vs tax comparison
# =============================================================================


def _book_tax_comparison(
    book: list[YearEntry],
    tax: list[YearEntry],
    tax_rate: Decimal,
) -> list[BookTaxComparisonEntry]:
    if not tax:
        return []
    max_years = max(len(book), len(tax))
    cumulative_deferred = ZERO
    rows: list[BookTaxComparisonEntry] = []
    for idx in range(1, max_years + 1):
        book_dep = book[idx - 1].depreciation if idx <= len(book) else ZERO
        tax_dep = tax[idx - 1].depreciation if idx <= len(tax) else ZERO
        timing = tax_dep - book_dep
        # Accumulate the *rounded* per-year change, so the cumulative column
        # equals the sum of the column printed beside it (Sprint 795).
        #
        # Accumulating at full precision and rounding only for display made the
        # two disagree by a cent: measured at 17 of 48 asset configurations
        # before this change. A practitioner footing the deferred-tax column
        # against its own running total should always get the running total.
        q_deferred_change = _q(timing * tax_rate)
        cumulative_deferred += q_deferred_change
        rows.append(
            BookTaxComparisonEntry(
                year_index=idx,
                book_depreciation=_q(book_dep),
                tax_depreciation=_q(tax_dep),
                timing_difference=_q(timing),
                deferred_tax_change=q_deferred_change,
                cumulative_deferred_tax=cumulative_deferred,
            )
        )
    return rows


# =============================================================================
# Public engine
# =============================================================================


def generate_depreciation_schedule(config: AssetConfig) -> DepreciationResult:
    """Compute book + tax depreciation schedules and the deferred-tax bridge."""
    config.validate()
    book = _book_schedule(config)
    tax = _macrs_schedule(config) if config.macrs_system else []
    comparison = _book_tax_comparison(book, tax, config.tax_rate)
    total_book = sum((y.depreciation for y in book), ZERO)
    total_tax = sum((y.depreciation for y in tax), ZERO)
    cumulative_deferred = comparison[-1].cumulative_deferred_tax if comparison else ZERO
    return DepreciationResult(
        config=config,
        book_schedule=book,
        tax_schedule=tax,
        book_tax_comparison=comparison,
        total_book_depreciation=_q(total_book),
        total_tax_depreciation=_q(total_tax),
        cumulative_deferred_tax=cumulative_deferred,
    )
