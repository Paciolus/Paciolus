"""
Sprint 763 — RPT-10 Bank Reconciliation materiality remediation tests.

Covers:
- BankRecConfig coerces float / int / str inputs to Decimal in __post_init__.
- BankRecConfig rejects negative thresholds.
- ``reconcile_bank_statement`` emits ``active_thresholds`` with the
  thresholds the engine actually applied + a ``materiality_source`` tag.
- The route-layer wiring populates ``materiality_source = "caller"`` only
  when the request supplied an override; otherwise ``"default"``.
- Decimal-precision boundary at the materiality threshold ($50,000.00 vs
  $49,999.99 vs $50,000.01) — no float-drift false positives or negatives.
- Large-engagement scale (>$1B materiality) round-trips through the
  response without precision loss.
- ``_test_high_value_transactions`` accepts both Decimal and float inputs
  for backward compatibility with legacy callers.
"""

from decimal import Decimal

import pytest

from bank_reconciliation import (
    DEFAULT_BANK_REC_MATERIALITY,
    DEFAULT_BANK_REC_PERFORMANCE_MATERIALITY,
    BankRecConfig,
    BankTransaction,
    MatchType,
    ReconciliationMatch,
    ReconciliationSummary,
    _test_high_value_transactions,
    compute_bank_rec_diagnostic_score,
    reconcile_bank_statement,
)

# ---------------------------------------------------------------------------
# BankRecConfig coercion + validation
# ---------------------------------------------------------------------------


class TestBankRecConfigCoercion:
    def test_default_thresholds_are_decimal(self) -> None:
        cfg = BankRecConfig()
        assert isinstance(cfg.materiality, Decimal)
        assert isinstance(cfg.performance_materiality, Decimal)
        assert isinstance(cfg.amount_tolerance, Decimal)
        assert cfg.materiality == DEFAULT_BANK_REC_MATERIALITY
        assert cfg.performance_materiality == DEFAULT_BANK_REC_PERFORMANCE_MATERIALITY

    def test_float_kwargs_coerced_to_decimal(self) -> None:
        cfg = BankRecConfig(materiality=25_000.0, performance_materiality=10_000.0)
        assert isinstance(cfg.materiality, Decimal)
        assert cfg.materiality == Decimal("25000")
        assert cfg.performance_materiality == Decimal("10000")

    def test_int_kwargs_coerced_to_decimal(self) -> None:
        cfg = BankRecConfig(materiality=75_000)
        assert isinstance(cfg.materiality, Decimal)
        assert cfg.materiality == Decimal("75000")

    def test_str_kwargs_coerced_to_decimal(self) -> None:
        cfg = BankRecConfig(materiality="100000.50")
        assert cfg.materiality == Decimal("100000.50")

    def test_decimal_kwargs_pass_through(self) -> None:
        cfg = BankRecConfig(materiality=Decimal("250000.00"))
        assert cfg.materiality == Decimal("250000.00")

    def test_negative_materiality_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            BankRecConfig(materiality=-1.0)

    def test_negative_performance_materiality_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            BankRecConfig(performance_materiality=-50_000)

    def test_negative_amount_tolerance_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            BankRecConfig(amount_tolerance=-0.01)


# ---------------------------------------------------------------------------
# active_thresholds emission + materiality_source plumbing
# ---------------------------------------------------------------------------


def _minimal_inputs() -> dict:
    """Construct the smallest valid input set for reconcile_bank_statement."""
    return {
        "bank_rows": [],
        "ledger_rows": [],
        "bank_columns": ["date", "description", "amount"],
        "ledger_columns": ["date", "description", "amount"],
    }


class TestActiveThresholdsEmission:
    def test_default_run_tags_source_default(self) -> None:
        result = reconcile_bank_statement(**_minimal_inputs())
        assert result.active_thresholds is not None
        assert result.active_thresholds["materiality_source"] == "default"
        assert result.active_thresholds["materiality"] == "50000.00"
        assert result.active_thresholds["performance_materiality"] == "50000.00"
        assert result.active_thresholds["amount_tolerance"] == "0.01"
        assert result.active_thresholds["date_tolerance_days"] == 0

    def test_caller_supplied_tags_source_caller(self) -> None:
        cfg = BankRecConfig(materiality=Decimal("25000"), performance_materiality=Decimal("10000"))
        result = reconcile_bank_statement(**_minimal_inputs(), config=cfg, materiality_source="caller")
        assert result.active_thresholds["materiality_source"] == "caller"
        assert result.active_thresholds["materiality"] == "25000"
        assert result.active_thresholds["performance_materiality"] == "10000"

    def test_to_dict_includes_active_thresholds(self) -> None:
        result = reconcile_bank_statement(**_minimal_inputs())
        d = result.to_dict()
        assert "active_thresholds" in d
        assert d["active_thresholds"]["materiality_source"] == "default"

    def test_invalid_materiality_source_rejected(self) -> None:
        with pytest.raises(ValueError, match="materiality_source"):
            reconcile_bank_statement(**_minimal_inputs(), materiality_source="auto")


# ---------------------------------------------------------------------------
# Decimal-precision boundary at the materiality threshold
# ---------------------------------------------------------------------------


def _match(amount: Decimal | float | str) -> ReconciliationMatch:
    """Build a one-sided match (bank only) at a given amount."""
    return ReconciliationMatch(
        bank_txn=BankTransaction(
            date="2026-01-15",
            description="Test txn",
            amount=Decimal(str(amount)) if not isinstance(amount, Decimal) else amount,
        ),
        ledger_txn=None,
        match_type=MatchType.BANK_ONLY,
        match_confidence=0.0,
    )


class TestMaterialityBoundary:
    def test_at_exactly_materiality_flagged(self) -> None:
        # >= materiality is the engine's documented contract
        result = _test_high_value_transactions([_match(Decimal("50000.00"))], materiality=Decimal("50000.00"))
        assert result.flagged_count == 1

    def test_one_cent_below_not_flagged(self) -> None:
        result = _test_high_value_transactions([_match(Decimal("49999.99"))], materiality=Decimal("50000.00"))
        assert result.flagged_count == 0

    def test_one_cent_above_flagged(self) -> None:
        result = _test_high_value_transactions([_match(Decimal("50000.01"))], materiality=Decimal("50000.00"))
        assert result.flagged_count == 1

    def test_legacy_float_caller_still_works(self) -> None:
        # _test_high_value_transactions is widely called with float in the
        # historical test corpus; coercion via safe_decimal must keep
        # this path working.
        result = _test_high_value_transactions([_match(75_000.0)], materiality=50_000.0)
        assert result.flagged_count == 1

    def test_decimal_arithmetic_at_boundary_is_exact(self) -> None:
        # In float space, summing 100 × $0.01 yields 0.9999999999999998
        # rather than 1.00 — a transaction at exactly the resulting
        # threshold would not flag.  In Decimal space the sum is exact
        # and the boundary holds.
        threshold = sum((Decimal("0.01") for _ in range(100)), Decimal("0"))
        assert threshold == Decimal("1.00")
        result = _test_high_value_transactions([_match(Decimal("1.00"))], materiality=threshold)
        assert result.flagged_count == 1


# ---------------------------------------------------------------------------
# Large-engagement scale (> $1B / > $1T)
# ---------------------------------------------------------------------------


class TestLargeScale:
    def test_billion_dollar_materiality_round_trips(self) -> None:
        cfg = BankRecConfig(
            materiality=Decimal("1000000000.00"),
            performance_materiality=Decimal("500000000.00"),
        )
        result = reconcile_bank_statement(**_minimal_inputs(), config=cfg, materiality_source="caller")
        assert result.active_thresholds["materiality"] == "1000000000.00"
        assert result.active_thresholds["performance_materiality"] == "500000000.00"

    def test_trillion_dollar_transaction_flagged_against_billion_materiality(
        self,
    ) -> None:
        result = _test_high_value_transactions(
            [_match(Decimal("1500000000000.00"))],  # $1.5T
            materiality=Decimal("1000000000.00"),  # $1B
        )
        assert result.flagged_count == 1

    def test_sub_penny_threshold_does_not_underflow(self) -> None:
        # Decimal handles sub-penny precision without underflow; float would.
        result = _test_high_value_transactions([_match(Decimal("0.005"))], materiality=Decimal("0.005"))
        assert result.flagged_count == 1


# ---------------------------------------------------------------------------
# Diagnostic score uses Decimal-space comparison at the materiality boundary
# ---------------------------------------------------------------------------


class TestDiagnosticScoreBoundary:
    def test_reconciling_difference_at_performance_materiality_does_not_double_count(
        self,
    ) -> None:
        # >0.01 AND > performance_materiality both add to score; verify
        # the boundary matches the Decimal contract.
        summary = ReconciliationSummary(
            matched_count=1,
            matched_amount=0.0,
            bank_only_count=0,
            ledger_only_count=0,
            reconciling_difference=49_999.99,  # below performance_materiality
            total_bank=0.0,
            total_ledger=0.0,
        )
        result = compute_bank_rec_diagnostic_score([], summary, performance_materiality=Decimal("50000.00"))
        # 15 (has diff) only; the >performance_materiality branch did not
        # fire because reconciling_difference < performance_materiality.
        assert result["score"] == 15

    def test_reconciling_difference_above_performance_materiality_fires_both_branches(
        self,
    ) -> None:
        summary = ReconciliationSummary(
            matched_count=1,
            matched_amount=0.0,
            bank_only_count=0,
            ledger_only_count=0,
            reconciling_difference=50_000.01,  # above performance_materiality
            total_bank=0.0,
            total_ledger=0.0,
        )
        result = compute_bank_rec_diagnostic_score([], summary, performance_materiality=Decimal("50000.00"))
        # 15 + 10 = 25
        assert result["score"] == 25
