"""
Sprint 765 — Variance basis declaration contract tests.

Asserts that every variance-emitting response surfaces ``variance_basis``
+ ``variance_formula`` and that the declared basis matches the actual
computation in every code path.

The contract:
- ``variance_basis == "absolute_prior"``
- ``variance_formula == "(current - prior) / abs(prior) * 100"``
- For any (current, prior) pair with abs(prior) > NEAR_ZERO, the emitted
  percent_variance / change_percent equals the formula applied to those
  inputs (within float tolerance).

See: ``docs/04-compliance/variance-formula-policy.md``.
"""

import httpx
import pytest

import multi_period_comparison as mpc
import prior_period_comparison as ppc
from auth import require_verified_user
from main import app

# ---------------------------------------------------------------------------
# Module-level constants are aligned across files
# ---------------------------------------------------------------------------


class TestPolicyConstants:
    def test_basis_is_absolute_prior_in_both_modules(self) -> None:
        assert mpc.VARIANCE_BASIS == "absolute_prior"
        assert ppc.VARIANCE_BASIS == "absolute_prior"
        assert mpc.VARIANCE_BASIS == ppc.VARIANCE_BASIS

    def test_formula_string_is_aligned(self) -> None:
        expected = "(current - prior) / abs(prior) * 100"
        assert mpc.VARIANCE_FORMULA == expected
        assert ppc.VARIANCE_FORMULA == expected


# ---------------------------------------------------------------------------
# multi_period_comparison.MovementSummary surfaces the contract
# ---------------------------------------------------------------------------


def _make_acct(name: str, debit: float = 0.0, credit: float = 0.0, type_: str = "asset") -> dict:
    return {"account": name, "debit": debit, "credit": credit, "type": type_}


class TestMultiPeriodResponse:
    def test_two_way_to_dict_includes_basis_fields(self) -> None:
        prior = [_make_acct("Cash", debit=10000.0)]
        current = [_make_acct("Cash", debit=12000.0)]
        result = mpc.compare_trial_balances(prior, current).to_dict()
        assert result["variance_basis"] == "absolute_prior"
        assert result["variance_formula"] == "(current - prior) / abs(prior) * 100"

    def test_three_way_to_dict_includes_basis_fields(self) -> None:
        prior = [_make_acct("Cash", debit=10000.0)]
        current = [_make_acct("Cash", debit=12000.0)]
        budget = [_make_acct("Cash", debit=11000.0)]
        result = mpc.compare_three_periods(prior, current, budget).to_dict()
        assert result["variance_basis"] == "absolute_prior"
        assert result["variance_formula"] == "(current - prior) / abs(prior) * 100"

    def test_change_percent_matches_formula_for_normal_account(self) -> None:
        # Cash $10,000 → $12,000.  abs(prior) = 10000.  Expected: +20.0%
        prior = [_make_acct("Cash", debit=10000.0)]
        current = [_make_acct("Cash", debit=12000.0)]
        result = mpc.compare_trial_balances(prior, current)
        cash = next(m for m in result.all_movements if m.account_name == "Cash")
        # Apply the documented formula directly
        expected = (cash.current_balance - cash.prior_balance) / abs(cash.prior_balance) * 100
        assert cash.change_percent == pytest.approx(expected)
        assert cash.change_percent == pytest.approx(20.0)

    def test_change_percent_matches_formula_for_credit_normal_account(self) -> None:
        # Liability $5,000 → $7,500.  Internally debit-credit-net is
        # negative; abs(prior) = 5000.  Expected: +50.0% in raw terms
        # (sign flip happens only at display layer).
        prior = [_make_acct("AP", credit=5000.0, type_="liability")]
        current = [_make_acct("AP", credit=7500.0, type_="liability")]
        result = mpc.compare_trial_balances(prior, current)
        ap = next(m for m in result.all_movements if m.account_name == "AP")
        expected = (ap.current_balance - ap.prior_balance) / abs(ap.prior_balance) * 100
        assert ap.change_percent == pytest.approx(expected)

    def test_near_zero_prior_yields_null_percent(self) -> None:
        # Prior $0 → Current $1,000.  abs(prior) <= NEAR_ZERO ⇒ None.
        prior = [_make_acct("New Acct", debit=0.0)]
        current = [_make_acct("New Acct", debit=1000.0)]
        result = mpc.compare_trial_balances(prior, current)
        new = next(m for m in result.all_movements if m.account_name == "New Acct")
        assert new.change_percent is None


# ---------------------------------------------------------------------------
# prior_period_comparison.PeriodComparison surfaces the contract
# ---------------------------------------------------------------------------


def _summary(**kwargs: float) -> dict:
    return {
        "period_label": "FY2024",
        "total_assets": 0.0,
        "current_assets": 0.0,
        "inventory": 0.0,
        "total_liabilities": 0.0,
        "current_liabilities": 0.0,
        "total_equity": 0.0,
        "total_revenue": 0.0,
        "cost_of_goods_sold": 0.0,
        "total_expenses": 0.0,
        "operating_expenses": 0.0,
        **kwargs,
    }


class TestPriorPeriodResponse:
    def test_to_dict_includes_basis_fields(self) -> None:
        current = _summary(total_assets=120_000.0)
        prior = _summary(total_assets=100_000.0)
        comp = ppc.compare_periods(current, prior, prior_id=42)
        d = comp.to_dict()
        assert d["variance_basis"] == "absolute_prior"
        assert d["variance_formula"] == "(current - prior) / abs(prior) * 100"

    def test_calculate_variance_matches_formula(self) -> None:
        # current=120, prior=100 → +20.0% under absolute_prior.
        dollar_var, pct_var, _, _ = ppc.calculate_variance(120.0, 100.0)
        assert dollar_var == pytest.approx(20.0)
        assert pct_var == pytest.approx(20.0)
        # Apply the formula directly
        expected = (120.0 - 100.0) / abs(100.0) * 100
        assert pct_var == pytest.approx(expected)

    def test_calculate_variance_negative_prior_uses_absolute_denominator(
        self,
    ) -> None:
        # Liability prior parsed as net debit-credit, sign-negative.
        # Absolute-prior basis: abs(-5000) = 5000 → +20% magnitude.
        # Signed-prior basis would have given -20% — confirms we are NOT
        # using signed-prior denominator.
        dollar_var, pct_var, _, _ = ppc.calculate_variance(-4000.0, -5000.0)
        assert dollar_var == pytest.approx(1000.0)
        assert pct_var == pytest.approx(20.0)
        # The signed-prior alternative would have produced -20.0
        signed_alt = (-4000.0 - -5000.0) / -5000.0 * 100
        assert signed_alt == pytest.approx(-20.0)
        assert pct_var != pytest.approx(signed_alt)

    def test_calculate_variance_near_zero_prior_yields_none(self) -> None:
        # abs(prior) < NEAR_ZERO ⇒ percent_variance is None.
        _, pct_var, _, _ = ppc.calculate_variance(100.0, 0.0)
        assert pct_var is None
        _, pct_var2, _, _ = ppc.calculate_variance(100.0, 0.001)
        assert pct_var2 is None


# ---------------------------------------------------------------------------
# Wire contract: variance_basis must survive FastAPI response_model serialization
# ---------------------------------------------------------------------------


class _MockUser:
    """Minimal verified-user stand-in for protected route tests."""

    def __init__(self) -> None:
        from shared.entitlements import UserTier  # local import: avoid circular

        self.id = 1
        self.email = "wire-contract@test"
        self.is_verified = True
        self.tier = UserTier.PROFESSIONAL


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_compare_periods_route_emits_variance_basis_on_wire() -> None:
    """The Pydantic response model must surface variance_basis on the wire.

    Without this, the response_model would silently strip the field and
    the engine's emission would never reach consumers.  Sprint 765/767
    contract guarantee.
    """
    from auth import require_current_user
    from shared import entitlement_checks

    user = _MockUser()
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[require_current_user] = lambda: user

    # Bypass entitlement check (tool gating not under test here).
    original = entitlement_checks.check_upload_limit  # type: ignore[attr-defined]

    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            payload = {
                "prior_accounts": [
                    {"account": "Cash", "debit": 50000.0, "credit": 0.0, "type": "asset"},
                ],
                "current_accounts": [
                    {"account": "Cash", "debit": 65000.0, "credit": 0.0, "type": "asset"},
                ],
                "prior_label": "FY2024",
                "current_label": "FY2025",
                "materiality_threshold": 0.0,
            }
            response = await client.post("/audit/compare-periods", json=payload)
            assert response.status_code == 200, response.text
            data = response.json()
            # The contract: variance_basis + variance_formula on the wire
            assert data.get("variance_basis") == "absolute_prior"
            assert data.get("variance_formula") == "(current - prior) / abs(prior) * 100"
    finally:
        app.dependency_overrides.clear()
