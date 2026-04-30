"""
Sprint 766 — bank_reconciliation.py Decimal port tests.

Covers:
- ``ReconciliationSummary``, ``RecFlaggedItem``, ``OutstandingItemsAging``,
  ``SuggestedJE`` monetary fields are stored as ``Decimal``.
- ``__post_init__`` coerces float / int / str inputs for backward
  compatibility with route layers that still pass float (e.g., the
  CSV-export route that rebuilds the summary from a JSON request body).
- ``calculate_summary`` keeps Decimal aggregates end-to-end (no
  float-roundtrip eroding precision before storage).
- ``to_dict`` quantizes 2dp HALF_UP at the wire boundary (was Python's
  default HALF_EVEN under ``round(x, 2)``).
- ``three_way_match_engine.MONETARY_EPSILON`` is the same object as
  ``shared.monetary.MONETARY_NEAR_ZERO``.
"""

from decimal import Decimal

from bank_reconciliation import (
    BankTransaction,
    LedgerTransaction,
    MatchType,
    OutstandingItemsAging,
    RecFlaggedItem,
    ReconciliationMatch,
    ReconciliationSummary,
    SuggestedJE,
    SuggestedJEKind,
    calculate_summary,
)

# ---------------------------------------------------------------------------
# Dataclass field types and coercion
# ---------------------------------------------------------------------------


class TestReconciliationSummaryDecimal:
    def test_default_fields_are_decimal(self) -> None:
        s = ReconciliationSummary()
        assert isinstance(s.matched_amount, Decimal)
        assert isinstance(s.bank_only_amount, Decimal)
        assert isinstance(s.ledger_only_amount, Decimal)
        assert isinstance(s.reconciling_difference, Decimal)
        assert isinstance(s.total_bank, Decimal)
        assert isinstance(s.total_ledger, Decimal)

    def test_float_kwargs_coerced_to_decimal(self) -> None:
        # Legacy CSV-export route rebuilds summary from JSON body with
        # float values — coercion must keep this path working.
        s = ReconciliationSummary(
            matched_amount=12345.67,
            reconciling_difference=89.01,
            total_bank=1000.0,
        )
        assert isinstance(s.matched_amount, Decimal)
        assert s.matched_amount == Decimal("12345.67")
        assert s.reconciling_difference == Decimal("89.01")
        assert s.total_bank == Decimal("1000")

    def test_str_kwargs_coerced_to_decimal(self) -> None:
        s = ReconciliationSummary(matched_amount="999.99")
        assert s.matched_amount == Decimal("999.99")

    def test_to_dict_quantizes_half_up(self) -> None:
        # 1234.005 → HALF_UP rounds to 1234.01.  Python's default
        # round(x, 2) is HALF_EVEN and would round to 1234.00.
        s = ReconciliationSummary(matched_amount=Decimal("1234.005"))
        d = s.to_dict()
        assert d["matched_amount"] == 1234.01

    def test_to_dict_returns_floats_for_wire_compat(self) -> None:
        s = ReconciliationSummary(matched_amount=Decimal("100.00"))
        d = s.to_dict()
        # Wire format remains float for JSON compatibility.
        assert isinstance(d["matched_amount"], float)


class TestRecFlaggedItemDecimal:
    def test_amount_field_is_decimal(self) -> None:
        item = RecFlaggedItem(test_name="t", description="d")
        assert isinstance(item.amount, Decimal)

    def test_float_amount_coerced(self) -> None:
        item = RecFlaggedItem(test_name="t", description="d", amount=42.5)
        assert isinstance(item.amount, Decimal)
        assert item.amount == Decimal("42.5")

    def test_to_dict_emits_quantized_float(self) -> None:
        item = RecFlaggedItem(test_name="t", description="d", amount=Decimal("100.005"))
        d = item.to_dict()
        assert d["amount"] == 100.01  # HALF_UP


class TestOutstandingItemsAgingDecimal:
    def test_oldest_item_amount_field_is_decimal(self) -> None:
        a = OutstandingItemsAging(category="bank_only")
        assert isinstance(a.oldest_item_amount, Decimal)

    def test_float_amount_coerced(self) -> None:
        a = OutstandingItemsAging(category="bank_only", oldest_item_amount=99.99)
        assert a.oldest_item_amount == Decimal("99.99")


class TestSuggestedJEDecimal:
    def test_amount_field_is_decimal(self) -> None:
        bt = BankTransaction(amount=Decimal("25.00"))
        je = SuggestedJE(
            bank_txn=bt,
            kind=SuggestedJEKind.BANK_FEE,
            debit_account="Bank Service Fees",
            credit_account="Cash",
            amount=Decimal("25.00"),
            description="Bank fee",
            confidence=0.9,
        )
        assert isinstance(je.amount, Decimal)

    def test_float_amount_coerced(self) -> None:
        bt = BankTransaction(amount=Decimal("25.00"))
        je = SuggestedJE(
            bank_txn=bt,
            kind=SuggestedJEKind.BANK_FEE,
            debit_account="Bank Service Fees",
            credit_account="Cash",
            amount=25.0,
            description="Bank fee",
            confidence=0.9,
        )
        assert isinstance(je.amount, Decimal)
        assert je.amount == Decimal("25")


# ---------------------------------------------------------------------------
# calculate_summary keeps Decimal end-to-end (no float roundtrip)
# ---------------------------------------------------------------------------


def _bank(amount: str) -> BankTransaction:
    return BankTransaction(date="2026-01-15", description="b", amount=Decimal(amount))


def _ledger(amount: str) -> LedgerTransaction:
    return LedgerTransaction(date="2026-01-15", description="l", amount=Decimal(amount))


class TestCalculateSummaryEndToEnd:
    def test_aggregates_remain_decimal(self) -> None:
        matches = [
            ReconciliationMatch(
                bank_txn=_bank("0.01"),
                ledger_txn=_ledger("0.01"),
                match_type=MatchType.MATCHED,
            ),
        ]
        summary = calculate_summary(matches)
        assert isinstance(summary.matched_amount, Decimal)
        assert isinstance(summary.total_bank, Decimal)
        assert isinstance(summary.reconciling_difference, Decimal)

    def test_summing_pennies_is_exact(self) -> None:
        # 100 × $0.01 should equal exactly $1.00 in Decimal.  In float
        # this would be 0.9999999999999998.  The pre-Sprint-766 code path
        # would float-roundtrip the aggregate, eroding precision.
        matches = [
            ReconciliationMatch(
                bank_txn=_bank("0.01"),
                ledger_txn=_ledger("0.01"),
                match_type=MatchType.MATCHED,
            )
            for _ in range(100)
        ]
        summary = calculate_summary(matches)
        assert summary.matched_amount == Decimal("1.00")
        assert summary.total_bank == Decimal("1.00")
        assert summary.total_ledger == Decimal("1.00")
        assert summary.reconciling_difference == Decimal("0.00")

    def test_to_dict_at_boundary_quantizes_half_up(self) -> None:
        # Reconciling difference of $1234.005 → HALF_UP rounds to 1234.01.
        matches = [
            ReconciliationMatch(
                bank_txn=_bank("1234.005"),
                ledger_txn=None,
                match_type=MatchType.BANK_ONLY,
            ),
        ]
        summary = calculate_summary(matches)
        d = summary.to_dict()
        assert d["bank_only_amount"] == 1234.01


# ---------------------------------------------------------------------------
# Helper consolidation: three_way_match_engine.MONETARY_EPSILON
# ---------------------------------------------------------------------------


class TestMonetaryNearZeroConsolidation:
    def test_three_way_epsilon_aliases_shared_constant(self) -> None:
        from shared.monetary import MONETARY_NEAR_ZERO
        from three_way_match_engine import MONETARY_EPSILON

        # Sprint 766: same object — three_way_match_engine no longer
        # owns its own ``Decimal("0.005")``.
        assert MONETARY_EPSILON is MONETARY_NEAR_ZERO
        assert MONETARY_EPSILON == Decimal("0.005")

    def test_balance_tolerance_distinct_from_near_zero(self) -> None:
        # These are semantically different and must not be conflated.
        from shared.monetary import BALANCE_TOLERANCE, MONETARY_NEAR_ZERO

        assert BALANCE_TOLERANCE == Decimal("0.01")  # equality tolerance
        assert MONETARY_NEAR_ZERO == Decimal("0.005")  # denominator guard
        assert BALANCE_TOLERANCE != MONETARY_NEAR_ZERO
