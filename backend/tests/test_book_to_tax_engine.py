"""Sprint 635 — Book-to-Tax Adjustment engine tests."""

from decimal import Decimal

from book_to_tax_engine import (
    M3_THRESHOLD_TOTAL_ASSETS,
    STANDARD_ADJUSTMENTS,
    AdjustmentDirection,
    AdjustmentEntry,
    BookToTaxConfig,
    BookToTaxInputError,
    DeferredTaxRollforwardInput,
    DifferenceType,
    calculate_book_to_tax,
)


def _meals_50pct() -> AdjustmentEntry:
    return AdjustmentEntry(
        label="Meals — 50% disallowance",
        amount=Decimal("5000"),
        difference_type=DifferenceType.PERMANENT,
        direction=AdjustmentDirection.ADD,
        code="meals_50pct",
    )


def _tax_exempt_interest() -> AdjustmentEntry:
    return AdjustmentEntry(
        label="Municipal bond interest",
        amount=Decimal("2000"),
        difference_type=DifferenceType.PERMANENT,
        direction=AdjustmentDirection.SUBTRACT,
        code="tax_exempt_interest",
    )


def _bad_debt_reserve(amount: str = "10000") -> AdjustmentEntry:
    return AdjustmentEntry(
        label="Bad debt reserve increase",
        amount=Decimal(amount),
        difference_type=DifferenceType.TEMPORARY,
        direction=AdjustmentDirection.ADD,
        code="bad_debt_reserve",
    )


def _depreciation_timing(amount: str = "15000") -> AdjustmentEntry:
    return AdjustmentEntry(
        label="Tax depreciation in excess of book",
        amount=Decimal(amount),
        difference_type=DifferenceType.TEMPORARY,
        direction=AdjustmentDirection.SUBTRACT,
        code="depreciation_timing",
    )


def _config(**overrides) -> BookToTaxConfig:
    defaults = dict(
        tax_year=2026,
        book_pretax_income=Decimal("500000"),
        total_assets=Decimal("5000000"),
        federal_tax_rate=Decimal("0.21"),
        adjustments=[
            _meals_50pct(),
            _tax_exempt_interest(),
            _bad_debt_reserve(),
            _depreciation_timing(),
        ],
    )
    defaults.update(overrides)
    return BookToTaxConfig(**defaults)


class TestScheduleM1:
    def test_reconciliation_matches_signed_total(self):
        result = calculate_book_to_tax(_config())
        # 500_000 + 5_000 (meals) - 2_000 (tax-exempt) + 10_000 (bad debt) - 15_000 (depr)
        assert result.schedule_m1.taxable_income == Decimal("498000.00")

    def test_permanent_vs_temporary_partitioned(self):
        result = calculate_book_to_tax(_config())
        m1 = result.schedule_m1
        assert len(m1.permanent_additions) == 1
        assert len(m1.permanent_subtractions) == 1
        assert len(m1.temporary_additions) == 1
        assert len(m1.temporary_subtractions) == 1


class TestScheduleM3:
    def test_entity_size_gates_on_total_assets(self):
        small = calculate_book_to_tax(_config(total_assets=Decimal("5000000")))
        large = calculate_book_to_tax(_config(total_assets=M3_THRESHOLD_TOTAL_ASSETS))
        assert small.entity_size == "small"
        assert large.entity_size == "large"

    def test_m3_income_and_expense_split(self):
        result = calculate_book_to_tax(_config())
        m3 = result.schedule_m3
        # SUBTRACT adjustments → income items (2: tax-exempt + depreciation)
        # ADD adjustments → expense items (2: meals + bad debt)
        assert len(m3.income_items) == 2
        assert len(m3.expense_items) == 2

    def test_m3_sections_separate_permanent_and_temporary(self):
        result = calculate_book_to_tax(_config())
        meals = [s for s in result.schedule_m3.expense_items if s.code == "meals_50pct"][0]
        assert meals.permanent != Decimal("0")
        assert meals.temporary == Decimal("0")


class TestDeferredTaxRollforward:
    def test_positive_net_temporary_builds_dta(self):
        # Only add temporary: +10,000. At 21% → +2,100 DTA.
        cfg = _config(adjustments=[_bad_debt_reserve("10000")])
        result = calculate_book_to_tax(cfg)
        assert result.deferred_tax.current_year_movement == Decimal("2100.00")
        assert result.deferred_tax.ending_dta == Decimal("2100.00")
        assert result.deferred_tax.ending_dtl == Decimal("0.00")

    def test_negative_net_temporary_reduces_dta_then_builds_dtl(self):
        # Temporary net = -15,000 (depreciation only). Movement = -3,150.
        cfg = _config(
            adjustments=[_depreciation_timing("15000")],
            rollforward=DeferredTaxRollforwardInput(
                beginning_dta=Decimal("2000"),
                beginning_dtl=Decimal("0"),
            ),
        )
        result = calculate_book_to_tax(cfg)
        # 2,000 DTA gets fully consumed, 1,150 spills to DTL.
        assert result.deferred_tax.ending_dta == Decimal("0.00")
        assert result.deferred_tax.ending_dtl == Decimal("1150.00")

    def test_rollforward_onto_existing_dta(self):
        cfg = _config(
            adjustments=[_bad_debt_reserve("10000")],
            rollforward=DeferredTaxRollforwardInput(
                beginning_dta=Decimal("500"),
                beginning_dtl=Decimal("0"),
            ),
        )
        result = calculate_book_to_tax(cfg)
        assert result.deferred_tax.beginning_dta == Decimal("500.00")
        assert result.deferred_tax.ending_dta == Decimal("2600.00")


class TestTaxProvision:
    def test_current_federal_tax_uses_taxable_income(self):
        result = calculate_book_to_tax(_config())
        # Taxable income 498,000 × 21% = 104,580.
        assert result.tax_provision.current_federal_tax == Decimal("104580.00")

    def test_total_includes_deferred_expense(self):
        result = calculate_book_to_tax(_config())
        total = (
            result.tax_provision.current_federal_tax
            + result.tax_provision.current_state_tax
            + result.tax_provision.deferred_tax_expense
        )
        assert total == result.tax_provision.total_tax_expense

    def test_effective_rate_computed_on_book_income(self):
        result = calculate_book_to_tax(_config())
        expected = (result.tax_provision.total_tax_expense / Decimal("500000")).quantize(Decimal("0.0001"))
        assert result.tax_provision.effective_rate == expected

    def test_state_tax_applied_on_top(self):
        cfg = _config(state_tax_rate=Decimal("0.05"))
        result = calculate_book_to_tax(cfg)
        assert result.tax_provision.current_state_tax == Decimal("24900.00")


class TestInputValidation:
    def test_negative_amount_rejected(self):
        try:
            AdjustmentEntry(
                label="bad",
                amount=Decimal("-5"),
                difference_type=DifferenceType.PERMANENT,
                direction=AdjustmentDirection.ADD,
            )
        except BookToTaxInputError:
            return
        raise AssertionError("expected BookToTaxInputError")

    def test_tax_rate_out_of_range_rejected(self):
        try:
            calculate_book_to_tax(_config(federal_tax_rate=Decimal("1.5")))
        except BookToTaxInputError:
            return
        raise AssertionError("expected BookToTaxInputError")

    def test_invalid_tax_year_rejected(self):
        try:
            calculate_book_to_tax(_config(tax_year=1999))
        except BookToTaxInputError:
            return
        raise AssertionError("expected BookToTaxInputError")


class TestStandardCatalog:
    def test_standard_catalog_exposes_both_types(self):
        types = {s.difference_type for s in STANDARD_ADJUSTMENTS}
        assert DifferenceType.PERMANENT in types
        assert DifferenceType.TEMPORARY in types

    def test_standard_catalog_has_unique_codes(self):
        codes = [s.code for s in STANDARD_ADJUSTMENTS]
        assert len(codes) == len(set(codes))


class TestSerialisation:
    def test_to_dict_roundtrip(self):
        result = calculate_book_to_tax(_config())
        d = result.to_dict()
        assert d["tax_year"] == 2026
        assert set(d).issuperset({"schedule_m1", "schedule_m3", "deferred_tax", "tax_provision"})
        assert "permanent_additions" in d["schedule_m1"]
