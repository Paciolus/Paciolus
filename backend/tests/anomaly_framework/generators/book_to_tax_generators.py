"""Book-to-tax reconciliation generators (Sprint 823 item 3) — 5 generators.

Book-to-tax is a calculator, not a detector: there is no "flag" to raise. Each
generator therefore injects one adjustment whose effect can be worked by hand
and checks the engine lands on exactly that number — the known-answer form of
the same baseline/inject/detect contract. Baseline: $1,000,000 pre-tax book
income, 21% rate, $20,000 meals disallowance, $4M total assets.
"""

from decimal import Decimal

from book_to_tax_engine import (
    M3_THRESHOLD_TOTAL_ASSETS,
    AdjustmentDirection,
    AdjustmentEntry,
    BookToTaxInputError,
    DifferenceType,
    calculate_book_to_tax,
)
from tests.anomaly_framework.fixtures.base_config_tools import (
    BTT_PRETAX_INCOME,
    BTT_RATE,
    book_to_tax_baseline,
)
from tests.anomaly_framework.generators.config_tool_base import ConfigGenerator, ToolHarness

_BASE_TAXABLE = BTT_PRETAX_INCOME + Decimal("20000")  # the meals add-back


def _run(config) -> dict:
    try:
        return calculate_book_to_tax(config).to_dict()
    except BookToTaxInputError as exc:
        return {"input_error": str(exc)}


BOOK_TO_TAX_HARNESS = ToolHarness(
    tool="book_to_tax",
    engine="book_to_tax_engine.calculate_book_to_tax",
    baseline=book_to_tax_baseline,
    run=_run,
)


def _taxable(result: dict) -> Decimal | None:
    return Decimal(result["tax_provision"]["taxable_income"]) if "tax_provision" in result else None


class BookToTaxM3ThresholdGenerator(ConfigGenerator):
    """At the M-3 asset threshold the entity is reported as large (Schedule M-3)."""

    name = "btt_m3_threshold"
    target = "entity_size"
    injected_at = "total assets raised to M3_THRESHOLD_TOTAL_ASSETS"

    def mutate(self, config):
        config.total_assets = M3_THRESHOLD_TOTAL_ASSETS

    def detected(self, result):
        return result.get("entity_size") == "large"


class BookToTaxTemporaryDifferenceGenerator(ConfigGenerator):
    """Tax depreciation $100,000 over book: taxable income down, a DTL of 21%."""

    name = "btt_temporary_depreciation"
    target = "deferred_tax.ending_dtl"
    injected_at = "temporary subtraction of $100,000 (depreciation_timing)"

    def mutate(self, config):
        config.adjustments.append(
            AdjustmentEntry(
                "Depreciation timing (book vs MACRS)",
                Decimal("100000"),
                DifferenceType.TEMPORARY,
                AdjustmentDirection.SUBTRACT,
                code="depreciation_timing",
            )
        )

    def detected(self, result):
        if "deferred_tax" not in result:
            return False
        expected_dtl = Decimal("100000") * BTT_RATE
        return (
            _taxable(result) == _BASE_TAXABLE - Decimal("100000")
            and Decimal(result["deferred_tax"]["ending_dtl"]) == expected_dtl
            and Decimal(result["tax_provision"]["deferred_tax_expense"]) == expected_dtl
        )


class BookToTaxPermanentAddGenerator(ConfigGenerator):
    """Fines are a permanent add-back: taxable income up, no deferred tax."""

    name = "btt_permanent_fines"
    target = "tax_provision.taxable_income"
    injected_at = "permanent addition of $10,000 (fines_penalties)"

    def mutate(self, config):
        config.adjustments.append(
            AdjustmentEntry(
                "Fines and penalties",
                Decimal("10000"),
                DifferenceType.PERMANENT,
                AdjustmentDirection.ADD,
                code="fines_penalties",
            )
        )

    def detected(self, result):
        return (
            _taxable(result) == _BASE_TAXABLE + Decimal("10000")
            and Decimal(result["tax_provision"]["deferred_tax_expense"]) == 0
        )


class BookToTaxPermanentSubtractGenerator(ConfigGenerator):
    """Tax-exempt interest: taxable income down, listed as an M-3 income item."""

    name = "btt_tax_exempt_interest"
    target = "schedule_m3.income_items"
    injected_at = "permanent subtraction of $50,000 (tax_exempt_interest)"

    def mutate(self, config):
        config.adjustments.append(
            AdjustmentEntry(
                "Tax-exempt interest income",
                Decimal("50000"),
                DifferenceType.PERMANENT,
                AdjustmentDirection.SUBTRACT,
                code="tax_exempt_interest",
            )
        )

    def detected(self, result):
        if "schedule_m3" not in result:
            return False
        return _taxable(result) == _BASE_TAXABLE - Decimal("50000") and any(
            item["code"] == "tax_exempt_interest" for item in result["schedule_m3"]["income_items"]
        )


class BookToTaxMiscodedAdjustmentGenerator(ConfigGenerator):
    """B5 (Sprint 826): a coded permanent item entered as temporary is refused.

    ``fines_penalties`` entered as temporary/subtract reduced taxable income
    and created a DTL.
    """

    name = "btt_miscoded_adjustment"
    target = "input_error"
    injected_at = "fines_penalties entered as a temporary subtraction"

    def mutate(self, config):
        config.adjustments.append(
            AdjustmentEntry(
                "Fines and penalties",
                Decimal("10000"),
                DifferenceType.TEMPORARY,
                AdjustmentDirection.SUBTRACT,
                code="fines_penalties",
            )
        )

    def detected(self, result):
        return "fines_penalties" in result.get("input_error", "")


BOOK_TO_TAX_REGISTRY = [
    BookToTaxM3ThresholdGenerator(),
    BookToTaxTemporaryDifferenceGenerator(),
    BookToTaxPermanentAddGenerator(),
    BookToTaxPermanentSubtractGenerator(),
    BookToTaxMiscodedAdjustmentGenerator(),
]
