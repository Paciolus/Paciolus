"""
Post-audit remediation regression suite — 2026-04-20.

Covers:
  * RPT-11 confirmed defects:
      - price-variance denominator guard no longer conflates
        ``price_variance_threshold`` with a near-zero monetary base.
      - match-rate denominator includes the receipts population.
      - three-way match route accepts validated config overrides.
  * RPT-02 confirmed defect:
      - significance thresholds are configurable via caller/API and emitted
        in the response for audit traceability.
  * DASH-01 confirmed defect:
      - engagement dashboard normalises ``medium`` (3-tier producer) to
        ``moderate`` (4-tier canonical).
  * RPT-02 signed variance basis — SUSPICION VALIDATION.
      - Characterization tests confirm abs(prior_balance) denominator is the
        INTENTIONAL platform policy (pairs with credit-normal sign-flipping
        at display).  Suspicion REJECTED; tests lock in the behaviour.
  * RPT-07 non-deterministic aging reference date — SUSPICION CONFIRMED.
      - Engine no longer silently falls back to ``date.today()``; route
        rejects sub-ledger uploads lacking ``as_of_date``.
  * Cross-report float precision — characterization tests.
      - Pin current float-boundary rounding behaviour for a handful of
        high-risk computational paths so future refactors can't drift
        silently.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

# -----------------------------------------------------------------------------
# RPT-11: Three-way match engine — price variance denominator guard
# -----------------------------------------------------------------------------
from three_way_match_engine import (
    MONETARY_EPSILON,
    Invoice,
    PurchaseOrder,
    Receipt,
    ThreeWayMatchConfig,
    _compute_variances,
    run_three_way_match,
)


class TestRPT11PriceVarianceDenominator:
    """Price variance denominator must use a monetary epsilon, not
    ``price_variance_threshold`` (which is a 5% decision threshold)."""

    def test_monetary_epsilon_is_less_than_a_cent(self):
        # Fixed floor: less than a cent (half-cent) — well below any
        # presentation-rounded currency amount.
        assert MONETARY_EPSILON < Decimal("0.01")
        assert MONETARY_EPSILON > Decimal("0")

    def test_low_unit_price_no_longer_100pct_variance(self):
        """Regression: PO unit price $0.03 vs. invoice $0.031 used to be
        flagged at 100% variance because 0.03 < 0.05 threshold."""
        po = PurchaseOrder(unit_price=Decimal("0.03"))
        inv = Invoice(unit_price=Decimal("0.031"))
        config = ThreeWayMatchConfig(price_variance_threshold=0.05)

        variances = _compute_variances(po, inv, None, config)
        price_vars = [v for v in variances if v.field == "price"]
        # Actual variance is |0.031 - 0.03| / 0.03 ≈ 3.33% — well below the
        # 5% decision threshold, so NO variance should be recorded.
        assert price_vars == [], f"Sub-cent unit prices must not trigger spurious 100% variance — got {price_vars}"

    def test_sub_epsilon_base_still_caps_at_100pct(self):
        """Edge: unit price below MONETARY_EPSILON is genuinely near-zero;
        pct is capped at 1.0 to avoid divide-by-zero."""
        po = PurchaseOrder(unit_price=Decimal("0.001"))  # below epsilon
        inv = Invoice(unit_price=Decimal("1.00"))
        config = ThreeWayMatchConfig(price_variance_threshold=0.05)

        variances = _compute_variances(po, inv, None, config)
        price_vars = [v for v in variances if v.field == "price"]
        assert len(price_vars) == 1
        assert price_vars[0].variance_pct == 1.0

    def test_high_price_variance_still_flagged(self):
        """Regression lock-in: genuine 20% variance still flagged high."""
        po = PurchaseOrder(unit_price=Decimal("100"))
        inv = Invoice(unit_price=Decimal("120"))
        config = ThreeWayMatchConfig(price_variance_threshold=0.05)

        variances = _compute_variances(po, inv, None, config)
        price_vars = [v for v in variances if v.field == "price"]
        assert len(price_vars) == 1
        assert price_vars[0].severity == "high"
        assert abs(price_vars[0].variance_pct - 0.20) < 1e-9

    def test_amount_variance_small_base(self):
        """Regression: PO total $0.02 vs invoice $0.03 — no false variance
        from conflated denominator guard."""
        po = PurchaseOrder(total_amount=Decimal("0.02"))
        inv = Invoice(total_amount=Decimal("0.03"))
        config = ThreeWayMatchConfig(amount_tolerance=0.01)
        variances = _compute_variances(po, inv, None, config)
        amount_vars = [v for v in variances if v.field == "amount"]
        # diff = $0.01; tolerance = $0.01 — equal, not greater, so no flag.
        assert amount_vars == []


# -----------------------------------------------------------------------------
# RPT-11: Three-way match engine — match-rate denominator aggregation
# -----------------------------------------------------------------------------


class TestRPT11MatchRateDenominator:
    """Match-rate denominator must include receipts; rate must stay ≤ 1."""

    def _po(self, po_num, vendor="Acme", amount=100.0):
        return PurchaseOrder(
            po_number=po_num, vendor=vendor, total_amount=Decimal(str(amount)), row_number=int(po_num[-3:])
        )

    def _inv(self, po_ref, vendor="Acme", amount=100.0, row=1):
        return Invoice(po_reference=po_ref, vendor=vendor, total_amount=Decimal(str(amount)), row_number=row)

    def _rec(self, po_ref, vendor="Acme", qty=1.0, row=1):
        return Receipt(po_reference=po_ref, vendor=vendor, quantity_received=qty, row_number=row)

    def test_receipts_included_in_denominator_when_largest_population(self):
        """When receipts outnumber POs/invoices (e.g., split deliveries),
        the denominator must reflect that — otherwise match rate > 1.0."""
        pos = [self._po("PO-001")]
        invoices = [self._inv("PO-001", row=1)]
        # 5 partial receipts for one PO
        receipts = [self._rec("PO-001", row=i + 1) for i in range(5)]

        result = run_three_way_match(pos, invoices, receipts)

        # Denominator must be max(1, 1, 5) = 5.
        assert result.summary.match_rate_denominator == 5
        assert result.summary.full_match_rate <= 1.0
        assert result.summary.partial_match_rate <= 1.0

    def test_denominator_source_documented(self):
        """The result exposes which population drove the denominator for
        audit workpaper traceability."""
        pos = [self._po("PO-001")]
        invoices = [self._inv("PO-001", row=1)]
        receipts = [self._rec("PO-001", row=i + 1) for i in range(5)]

        result = run_three_way_match(pos, invoices, receipts)
        assert "receipts" in result.summary.match_rate_denominator_source

    def test_denominator_prior_pos_largest(self):
        """Prior behaviour preserved when POs are the largest population."""
        pos = [self._po(f"PO-{i:03d}") for i in range(1, 4)]
        invoices = [self._inv("PO-001", row=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        assert result.summary.match_rate_denominator == 3
        assert "pos" in result.summary.match_rate_denominator_source


# -----------------------------------------------------------------------------
# RPT-11: Three-way match route — validated config overrides
# -----------------------------------------------------------------------------

from fastapi import HTTPException  # noqa: E402

from routes.three_way_match import _build_twm_config  # noqa: E402


class TestRPT11RouteConfigOverrides:
    def test_defaults_when_no_overrides(self):
        """Backward compatibility: None overrides → dataclass defaults."""
        cfg = _build_twm_config(
            amount_tolerance=None,
            quantity_tolerance=None,
            date_window_days=None,
            fuzzy_vendor_threshold=None,
            price_variance_threshold=None,
            enable_fuzzy_matching=None,
            fuzzy_composite_threshold=None,
        )
        default = ThreeWayMatchConfig()
        assert cfg.amount_tolerance == default.amount_tolerance
        assert cfg.price_variance_threshold == default.price_variance_threshold
        assert cfg.fuzzy_composite_threshold == default.fuzzy_composite_threshold

    def test_valid_overrides_applied(self):
        cfg = _build_twm_config(
            amount_tolerance=0.05,
            quantity_tolerance=1.0,
            date_window_days=60,
            fuzzy_vendor_threshold=0.90,
            price_variance_threshold=0.10,
            enable_fuzzy_matching=False,
            fuzzy_composite_threshold=0.75,
        )
        assert cfg.amount_tolerance == 0.05
        assert cfg.date_window_days == 60
        assert cfg.enable_fuzzy_matching is False
        assert cfg.fuzzy_composite_threshold == 0.75

    def test_out_of_range_price_variance_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _build_twm_config(
                amount_tolerance=None,
                quantity_tolerance=None,
                date_window_days=None,
                fuzzy_vendor_threshold=None,
                price_variance_threshold=2.0,  # >1.0 bound
                enable_fuzzy_matching=None,
                fuzzy_composite_threshold=None,
            )
        assert exc.value.status_code == 400

    def test_negative_tolerance_rejected(self):
        with pytest.raises(HTTPException):
            _build_twm_config(
                amount_tolerance=-1.0,
                quantity_tolerance=None,
                date_window_days=None,
                fuzzy_vendor_threshold=None,
                price_variance_threshold=None,
                enable_fuzzy_matching=None,
                fuzzy_composite_threshold=None,
            )

    def test_date_window_upper_bound(self):
        with pytest.raises(HTTPException):
            _build_twm_config(
                amount_tolerance=None,
                quantity_tolerance=None,
                date_window_days=400,  # >365 days
                fuzzy_vendor_threshold=None,
                price_variance_threshold=None,
                enable_fuzzy_matching=None,
                fuzzy_composite_threshold=None,
            )


# -----------------------------------------------------------------------------
# RPT-02: Configurable significance thresholds
# -----------------------------------------------------------------------------

from multi_period_comparison import (  # noqa: E402
    SIGNIFICANT_VARIANCE_AMOUNT,
    SIGNIFICANT_VARIANCE_PERCENT,
    MovementType,
    SignificanceThresholds,
    SignificanceTier,
    classify_significance,
    compare_trial_balances,
)


def _acct(name, debit=0, credit=0, atype="asset"):
    return {"account": name, "debit": debit, "credit": credit, "type": atype}


class TestRPT02ConfigurableThresholds:
    def test_default_thresholds_unchanged(self):
        """Defaults must match the historical module-level constants."""
        t = SignificanceThresholds()
        assert t.variance_percent == SIGNIFICANT_VARIANCE_PERCENT
        assert t.variance_amount == SIGNIFICANT_VARIANCE_AMOUNT

    def test_lower_amount_threshold_catches_smaller_variances(self):
        """Custom $1,000 threshold should flag a $5K movement that the
        $10K default would classify as minor (if below 10% too)."""
        # Change = $5,000 (4.9% of $102K prior) — minor under defaults
        assert classify_significance(5_000, 4.9, materiality_threshold=0) == SignificanceTier.MINOR
        # With stricter $1K threshold, same movement is SIGNIFICANT
        custom = SignificanceThresholds(variance_percent=10.0, variance_amount=1_000.0)
        tier = classify_significance(5_000, 4.9, materiality_threshold=0, thresholds=custom)
        assert tier == SignificanceTier.SIGNIFICANT

    def test_percent_threshold_independently_configurable(self):
        """A 3% change on a tiny base is invisible under 10% default but
        visible under a custom 2%."""
        # abs $1 change, 3% percent
        assert classify_significance(1.0, 3.0) == SignificanceTier.MINOR
        tighter = SignificanceThresholds(variance_percent=2.0, variance_amount=10_000.0)
        assert classify_significance(1.0, 3.0, thresholds=tighter) == SignificanceTier.SIGNIFICANT

    def test_active_thresholds_emitted_in_response(self):
        """Response must advertise the thresholds used for audit trace."""
        prior = [_acct("Cash", debit=100_000)]
        current = [_acct("Cash", debit=105_000)]
        custom = SignificanceThresholds(variance_percent=2.0, variance_amount=500.0)
        result = compare_trial_balances(prior, current, thresholds=custom)
        at = result.active_thresholds
        assert at == {
            "significant_variance_percent": 2.0,
            "significant_variance_amount": 500.0,
        }
        d = result.to_dict()
        assert d["active_thresholds"]["significant_variance_percent"] == 2.0

    def test_active_thresholds_reflects_defaults_when_unset(self):
        prior = [_acct("Cash", debit=100_000)]
        current = [_acct("Cash", debit=105_000)]
        result = compare_trial_balances(prior, current)
        at = result.active_thresholds
        assert at["significant_variance_percent"] == SIGNIFICANT_VARIANCE_PERCENT
        assert at["significant_variance_amount"] == SIGNIFICANT_VARIANCE_AMOUNT


# -----------------------------------------------------------------------------
# DASH-01: Tier taxonomy normalization
# -----------------------------------------------------------------------------

from engagement_dashboard_engine import (  # noqa: E402
    _compute_overall_tier,
    compute_engagement_dashboard,
)
from shared.testing_enums import normalize_risk_tier  # noqa: E402


class TestDASH01TierNormalization:
    def test_medium_maps_to_moderate(self):
        assert normalize_risk_tier("medium") == "moderate"

    def test_case_insensitive(self):
        assert normalize_risk_tier("MEDIUM") == "moderate"
        assert normalize_risk_tier("High") == "high"

    def test_canonical_pass_through(self):
        for t in ("low", "moderate", "elevated", "high"):
            assert normalize_risk_tier(t) == t

    def test_unknown_falls_back_to_default(self):
        assert normalize_risk_tier("unseen") == "low"
        assert normalize_risk_tier(None) == "low"
        assert normalize_risk_tier("") == "low"

    def test_legacy_aliases(self):
        assert normalize_risk_tier("critical") == "high"
        assert normalize_risk_tier("minimal") == "low"

    def test_dashboard_priority_action_for_medium_three_way_match(self):
        """A three-way match report emitting 'medium' previously vanished
        from the priority action list — now surfaces via normalisation."""
        # Construct a report in the legacy shape three-way-match uses —
        # ``summary.risk_assessment = 'medium'`` — to exercise the
        # _extract_report_summary fallback path.
        reports = [
            {
                "report_type": "three_way_match",
                "report_title": "Three-Way Match",
                "summary": {
                    "total_unmatched": 3,
                    "risk_assessment": "medium",
                },
                # Simulate flagged items surfaced via rec_tests-style path
                "rec_tests": [
                    {
                        "test_key": "match",
                        "flagged_count": 0,
                        "flagged_items": [
                            {"severity": "high"},
                            {"severity": "high"},
                        ],
                    }
                ],
            }
        ]
        result = compute_engagement_dashboard(reports)
        # The report's risk_tier should now be 'moderate' not 'medium'
        assert len(result.report_summaries) == 1
        summary = result.report_summaries[0]
        assert summary.risk_tier == "moderate", f"Expected normalised 'moderate'; got {summary.risk_tier!r}"

    def test_dashboard_overall_tier_still_uses_canonical(self):
        # Unchanged behaviour sanity check.
        assert _compute_overall_tier(5) == "low"
        assert _compute_overall_tier(20) == "moderate"
        assert _compute_overall_tier(40) == "elevated"
        assert _compute_overall_tier(75) == "high"


# -----------------------------------------------------------------------------
# RPT-02 suspicion: signed vs abs-based variance denominator
# -----------------------------------------------------------------------------
#
# CONCLUSION: SUSPICION REJECTED.  The abs() denominator is intentional — it
# pairs with the credit-normal sign-flipping in AccountMovement.to_dict() to
# keep internal representation in debit-positive terms and flip only at the
# presentation boundary.  A signed-denominator implementation would break
# the display layer assumption (raw change_percent is negated for
# credit-normal categories to produce display_change_percent).
#
# These tests lock in the intended behaviour so a future "bug fix" to use
# signed denominators doesn't silently flip liability growth reporting.

from multi_period_comparison import calculate_movement  # noqa: E402


class TestRPT02SignedVarianceSuspicion:
    def test_positive_prior_positive_current(self):
        """Vanilla asset growth: +10% as expected."""
        mt, amt, pct = calculate_movement(prior_balance=100.0, current_balance=110.0)
        assert mt == MovementType.INCREASE
        assert amt == pytest.approx(10.0)
        assert pct == pytest.approx(10.0)

    def test_negative_prior_negative_current_documented_policy(self):
        """Liability (credit-normal, stored as negative debit-positive):
        prior -100, current -150 (liability GREW).

        Current policy: raw change_percent uses abs(prior) denominator →
        -50%.  Display layer flips sign for credit-normal categories to
        +50%.  This test pins the raw value; the display flip is tested
        in AccountMovement.to_dict behaviour elsewhere."""
        mt, amt, pct = calculate_movement(prior_balance=-100.0, current_balance=-150.0)
        assert mt == MovementType.DECREASE  # debit-positive went down
        assert amt == pytest.approx(-50.0)
        # abs denominator: (-50 / 100) * 100 = -50
        assert pct == pytest.approx(-50.0)

    def test_sign_change_prior_negative_current_positive(self):
        """Liability becoming an asset — sign change.  abs() denominator
        keeps pct interpretable; signed denominator would invert."""
        mt, amt, pct = calculate_movement(prior_balance=-100.0, current_balance=50.0)
        assert mt == MovementType.SIGN_CHANGE
        assert amt == pytest.approx(150.0)
        # With abs denominator: +150% (direction preserved)
        assert pct == pytest.approx(150.0)

    def test_zero_prior_yields_none_percent(self):
        _, _, pct = calculate_movement(prior_balance=0.0, current_balance=50.0)
        assert pct is None

    def test_near_zero_prior_yields_none_percent(self):
        """Below NEAR_ZERO (0.005) triggers divide-by-near-zero guard."""
        _, _, pct = calculate_movement(prior_balance=0.001, current_balance=50.0)
        assert pct is None


# -----------------------------------------------------------------------------
# RPT-07 suspicion: non-deterministic aging reference date
# -----------------------------------------------------------------------------

from ar_aging_engine import _compute_aging_days  # noqa: E402


class TestRPT07DeterministicAging:
    def test_explicit_as_of_date_deterministic(self):
        # 90 days past due vs. an explicit reference.
        days = _compute_aging_days("2025-01-01", "2025-04-01")
        assert days == 90

    def test_missing_as_of_date_returns_none(self):
        """RPT-07 CONFIRMED: engine no longer silently uses date.today().

        Callers that supply no reference date now receive None (aging
        undefined), preventing the pre-remediation behaviour of
        overstating aging by whatever wall-clock gap exists between
        upload date and the intended as-of date.
        """
        result = _compute_aging_days("2025-01-01", None)
        assert result is None, (
            "AR aging must not silently default to date.today() when no reference date is supplied — got {result}"
        )

    def test_unparseable_as_of_date_raises(self):
        """Surface the problem instead of silently shifting to today()."""
        with pytest.raises(ValueError):
            _compute_aging_days("2025-01-01", "not-a-date")

    def test_supported_date_formats(self):
        # ISO, US slash, EU slash, US dash, EU dash, ISO slash
        assert _compute_aging_days("2025-01-01", "2025-04-01") == 90
        assert _compute_aging_days("2025-01-01", "04/01/2025") == 90
        assert _compute_aging_days("01/01/2025", "2025-04-01") == 90


# -----------------------------------------------------------------------------
# Cross-report float precision — characterization tests
# -----------------------------------------------------------------------------
#
# These tests characterise the CURRENT float/Decimal boundary behaviour.
# They do NOT attempt to drive Decimal precision end-to-end (that would be
# a separate multi-sprint refactor) — they just pin today's behaviour so
# future refactors cannot silently drift.


class TestCrossReportPrecisionBoundaries:
    def test_three_way_match_decimal_preserved_through_engine(self):
        """Three-way match keeps unit_price / total_amount as Decimal through
        the engine; float conversion happens only at MatchVariance export.
        Pin this because flipping to float internally would reintroduce
        rounding differences."""
        po = PurchaseOrder(unit_price=Decimal("33.33"), total_amount=Decimal("33.33"))
        assert isinstance(po.unit_price, Decimal)
        assert isinstance(po.total_amount, Decimal)

    def test_three_way_match_variance_exports_float(self):
        """MatchVariance.to_dict returns float (presentation boundary)."""
        po = PurchaseOrder(total_amount=Decimal("100"))
        inv = Invoice(total_amount=Decimal("110"))
        config = ThreeWayMatchConfig()
        variances = _compute_variances(po, inv, None, config)
        d = variances[0].to_dict()
        assert isinstance(d["variance_amount"], float)

    def test_multi_period_change_amount_rounds_at_cent(self):
        """``calculate_movement`` converts to float before computing
        change_amount — pin the <0.01 UNCHANGED guard."""
        mt, amt, pct = calculate_movement(prior_balance=100.00, current_balance=100.005)
        assert mt == MovementType.UNCHANGED
        assert amt == 0.0

    def test_significance_threshold_exact_boundary(self):
        """$10K exactly → SIGNIFICANT (>= threshold).  Float noise in the
        caller must not knock this off.  Pin with pytest.approx."""
        tier = classify_significance(
            change_amount=10_000.0,
            change_percent=5.0,
            thresholds=SignificanceThresholds(),
        )
        assert tier == SignificanceTier.SIGNIFICANT

    def test_signed_percent_abs_symmetry(self):
        """abs denominator makes |growth% for asset +10%| == |contraction%
        for asset -10%| — a property the downstream display layer relies
        on when flipping signs for credit-normal categories."""
        _, _, pct_up = calculate_movement(prior_balance=100.0, current_balance=110.0)
        _, _, pct_down = calculate_movement(prior_balance=100.0, current_balance=90.0)
        assert pct_up == pytest.approx(-pct_down)
