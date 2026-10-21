"""Sprint 780 — tests for the Stripe price-parity preflight.

The preflight is the gate that stops a silent mispricing reaching a customer, so it
needs to be trustworthy itself. Every test here drives a fake `stripe` module: no
network, no keys, and the fake returns exactly the shapes the real API returns.

Covered:
- the happy path across all ten price objects
- each failure mode independently (amount, currency, interval, archived, livemode)
- coupon checks
- unset price IDs, with and without --require-all
- misconfiguration (no secret key)
- agreement between the preflight's expectations and price_config's canonical tables
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "stripe_price_parity_preflight.py"


def _load_preflight():
    """Import the preflight script by path (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location("stripe_price_parity_preflight", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


preflight = _load_preflight()


# ---------------------------------------------------------------------------
# Fake Stripe
# ---------------------------------------------------------------------------


class _FakeStripe:
    """Minimal stand-in for the stripe module's Price/Coupon retrieve calls."""

    def __init__(self, prices: dict[str, dict[str, Any]], coupons: dict[str, dict[str, Any]] | None = None):
        self._prices = prices
        self._coupons = coupons or {}
        outer = self

        class Price:
            @staticmethod
            def retrieve(price_id: str) -> dict[str, Any]:
                if price_id not in outer._prices:
                    raise ValueError(f"No such price: {price_id}")
                return outer._prices[price_id]

        class Coupon:
            @staticmethod
            def retrieve(coupon_id: str) -> dict[str, Any]:
                if coupon_id not in outer._coupons:
                    raise ValueError(f"No such coupon: {coupon_id}")
                return outer._coupons[coupon_id]

        self.Price = Price
        self.Coupon = Coupon


def _price(
    cents: int,
    interval: str = "month",
    currency: str = "usd",
    active: bool = True,
    livemode: bool = False,
    interval_count: int | None = None,
):
    recurring: dict[str, Any] = {"interval": interval}
    # Stripe omits interval_count when it is 1, so default to omitting it here too.
    if interval_count is not None:
        recurring["interval_count"] = interval_count
    return {
        "unit_amount": cents,
        "currency": currency,
        "recurring": recurring,
        "active": active,
        "livemode": livemode,
    }


def _coupon(
    percent: float | None = 20,
    duration: str = "repeating",
    months: int | None = 3,
    valid: bool = True,
    amount_off: int | None = None,
) -> dict[str, Any]:
    return {
        "percent_off": percent,
        "amount_off": amount_off,
        "duration": duration,
        "duration_in_months": months,
        "valid": valid,
    }


def _good_coupons() -> dict[str, dict[str, Any]]:
    """Coupons matching both COUPON_EXPECTATIONS entries."""
    return {
        "cpn_m": _coupon(20, "repeating", 3),
        "cpn_a": _coupon(10, "once", None),
    }


def _coupon_env() -> dict[str, str]:
    return _full_env() | {"STRIPE_COUPON_MONTHLY_20": "cpn_m", "STRIPE_COUPON_ANNUAL_10": "cpn_a"}


def _full_env() -> dict[str, str]:
    """A test-mode environment with all ten price IDs set."""
    env = {"STRIPE_SECRET_KEY": "sk_test_abc"}
    for expected in preflight.build_expectations():
        env[expected.env_var] = f"price_{expected.env_var.lower()}"
    return env


def _matching_prices() -> dict[str, dict[str, Any]]:
    """Stripe-side objects that agree with every canonical amount."""
    return {
        f"price_{e.env_var.lower()}": _price(e.expected_cents, interval=e.stripe_interval)
        for e in preflight.build_expectations()
    }


# ---------------------------------------------------------------------------
# Expectations are derived from price_config, not restated
# ---------------------------------------------------------------------------


def test_expectations_cover_all_ten_price_objects():
    """Six base plans plus four seat add-ons. Mapping only the base table would
    silently skip the seat prices, which is the exact gap Sprint 780 was filed over."""
    expectations = preflight.build_expectations()
    assert len(expectations) == 10
    env_vars = {e.env_var for e in expectations}
    assert env_vars == {
        "STRIPE_PRICE_SOLO_MONTHLY",
        "STRIPE_PRICE_SOLO_ANNUAL",
        "STRIPE_PRICE_PROFESSIONAL_MONTHLY",
        "STRIPE_PRICE_PROFESSIONAL_ANNUAL",
        "STRIPE_PRICE_ENTERPRISE_MONTHLY",
        "STRIPE_PRICE_ENTERPRISE_ANNUAL",
        "STRIPE_SEAT_PRICE_PRO_MONTHLY",
        "STRIPE_SEAT_PRICE_PRO_ANNUAL",
        "STRIPE_SEAT_PRICE_ENT_MONTHLY",
        "STRIPE_SEAT_PRICE_ENT_ANNUAL",
    }


def test_expected_amounts_match_price_config():
    """The preflight must read the canonical tables, never a second copy of the numbers."""
    from billing.price_config import ENTERPRISE_SEAT_PRICE, PRICE_TABLE, PROFESSIONAL_SEAT_PRICE

    by_var = {e.env_var: e.expected_cents for e in preflight.build_expectations()}
    assert by_var["STRIPE_PRICE_SOLO_MONTHLY"] == PRICE_TABLE["solo"]["monthly"]
    assert by_var["STRIPE_PRICE_PROFESSIONAL_ANNUAL"] == PRICE_TABLE["professional"]["annual"]
    assert by_var["STRIPE_PRICE_ENTERPRISE_MONTHLY"] == PRICE_TABLE["enterprise"]["monthly"]
    assert by_var["STRIPE_SEAT_PRICE_PRO_MONTHLY"] == PROFESSIONAL_SEAT_PRICE["monthly"]
    assert by_var["STRIPE_SEAT_PRICE_ENT_ANNUAL"] == ENTERPRISE_SEAT_PRICE["annual"]


def test_annual_expectations_use_year_interval():
    for expected in preflight.build_expectations():
        assert expected.stripe_interval == ("year" if expected.interval == "annual" else "month")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_all_prices_matching_exits_zero():
    code, report = preflight.run(require_all=True, stripe_module=_FakeStripe(_matching_prices()), env=_full_env())
    text = "\n".join(report)
    assert code == 0, text
    assert "ALL CHECKED PRICES MATCH" in text
    assert "Checked 10 of 10 price objects." in text


def test_report_names_mode_from_key_prefix():
    _, report = preflight.run(require_all=False, stripe_module=_FakeStripe(_matching_prices()), env=_full_env())
    assert "TEST mode" in report[0]

    live_env = _full_env() | {"STRIPE_SECRET_KEY": "sk_live_abc"}
    live_prices = {pid: {**p, "livemode": True} for pid, p in _matching_prices().items()}
    _, live_report = preflight.run(require_all=False, stripe_module=_FakeStripe(live_prices), env=live_env)
    assert "LIVE mode" in live_report[0]


# ---------------------------------------------------------------------------
# Failure modes, one at a time
# ---------------------------------------------------------------------------


def test_wrong_amount_is_reported_in_dollars():
    """The v2-vs-v3 case that motivated this script: Solo at $50 against a $100 table."""
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(5000)
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    text = "\n".join(report)
    assert code == 1
    assert "solo monthly base plan" in text
    assert "$50.00" in text and "$100.00" in text
    assert "unit_amount=5000 vs 10000" in text


def test_seat_price_mismatch_is_caught():
    """Seat add-ons are checked, not just base plans."""
    prices = _matching_prices()
    prices["price_stripe_seat_price_ent_monthly"] = _price(6500)  # Pro's rate on Enterprise
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    assert code == 1
    assert "enterprise monthly seat add-on" in "\n".join(report)


def test_wrong_currency_is_caught():
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(10000, currency="eur")
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    assert code == 1
    assert "currency is 'eur'" in "\n".join(report)


def test_wrong_interval_is_caught():
    """A correct amount on the wrong cadence bills right once and wrong forever."""
    prices = _matching_prices()
    prices["price_stripe_price_solo_annual"] = _price(100000, interval="month")
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    text = "\n".join(report)
    assert code == 1
    assert "billing interval is 'month'" in text
    assert "wrongly forever" in text


def test_quarterly_interval_count_is_caught():
    """interval="month" with interval_count=3 bills quarterly.

    PR #179 review: the cadence check validated the unit and ignored the multiplier, so a
    quarterly price charging the monthly amount passed — the same defect the interval check
    was added to prevent.
    """
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(10000, interval="month", interval_count=3)
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    text = "\n".join(report)
    assert code == 1
    assert "interval_count is 3" in text
    assert "every 3 months" in text


def test_biennial_annual_price_is_caught():
    prices = _matching_prices()
    prices["price_stripe_price_enterprise_annual"] = _price(1000000, interval="year", interval_count=2)
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    assert code == 1
    assert "interval_count is 2" in "\n".join(report)


def test_omitted_interval_count_is_treated_as_one():
    """Stripe omits interval_count when it is 1; that must not read as a mismatch."""
    prices = _matching_prices()
    assert "interval_count" not in prices["price_stripe_price_solo_monthly"]["recurring"]
    code, _ = preflight.run(require_all=True, stripe_module=_FakeStripe(prices), env=_full_env())
    assert code == 0


def test_explicit_interval_count_of_one_passes():
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(10000, interval="month", interval_count=1)
    code, _ = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    assert code == 0


def test_archived_price_is_caught():
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(10000, active=False)
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    assert code == 1
    assert "archived/inactive" in "\n".join(report)


def test_test_mode_price_under_live_key_is_caught():
    """The cutover accident this prevents: a live deployment wired to test prices."""
    env = _full_env() | {"STRIPE_SECRET_KEY": "sk_live_abc"}
    prices = {pid: {**p, "livemode": True} for pid, p in _matching_prices().items()}
    prices["price_stripe_price_solo_monthly"]["livemode"] = False
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=env)
    text = "\n".join(report)
    assert code == 1
    assert "livemode=False" in text and "live mode" in text


def test_unretrievable_price_is_reported_not_raised():
    """An expired or wrong key must produce a report, not a traceback."""
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe({}), env=_full_env())
    text = "\n".join(report)
    assert code == 1
    assert "could not retrieve" in text
    assert "ValueError" in text


def test_every_mismatch_is_listed_not_just_the_first():
    """Three wrong amounts, each otherwise well-formed, must all be named.

    Intervals are kept correct here on purpose: one price object can produce several
    problems at once (wrong amount *and* wrong cadence), so the problem count equals
    the number of prices only when each has exactly one defect.
    """
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(5000, interval="month")
    prices["price_stripe_price_enterprise_annual"] = _price(123, interval="year")
    prices["price_stripe_seat_price_pro_annual"] = _price(1, interval="year")
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    text = "\n".join(report)
    assert code == 1
    assert "3 problem(s)" in text
    for label in ("solo monthly base plan", "enterprise annual base plan", "professional annual seat add-on"):
        assert label in text


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------


def test_matching_coupons_pass():
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), _good_coupons()), env=_coupon_env()
    )
    assert code == 0, "\n".join(report)


def test_fractional_coupon_percent_is_not_truncated():
    """percent_off is a float in Stripe. int() made 20.5 compare equal to 20, passing while
    checkout granted a larger discount than advertised (PR #179 review)."""
    coupons = _good_coupons()
    coupons["cpn_m"] = _coupon(20.5, "repeating", 3)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    text = "\n".join(report)
    assert code == 1
    assert "percent_off is 20.5, expected 20" in text


def test_integer_valued_float_percent_still_passes():
    """20.0 is the advertised 20% — it must not be reported as a mismatch."""
    coupons = _good_coupons()
    coupons["cpn_m"] = _coupon(20.0, "repeating", 3)
    code, _ = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    assert code == 0


def test_coupon_percent_mismatch_is_caught():
    coupons = _good_coupons()
    coupons["cpn_m"] = _coupon(25, "repeating", 3)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    assert code == 1
    assert "percent_off is 25, expected 20" in "\n".join(report)


def test_amount_off_coupon_is_a_mismatch_not_a_skip():
    """percent_off=None means an amount-off coupon. Checkout would apply a fixed
    discount instead of the advertised percentage, so it must fail rather than
    be treated as nothing to compare."""
    coupons = _good_coupons()
    coupons["cpn_a"] = _coupon(None, "once", None, amount_off=500)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    text = "\n".join(report)
    assert code == 1
    assert "has no percent_off" in text
    assert "amount_off=500" in text
    assert "fixed discount" in text


def test_repeating_coupon_without_month_cap_is_caught():
    """The expensive one: 20% off that never stops. duration_in_months=None on a
    repeating coupon discounts every renewal for the life of the subscription."""
    coupons = _good_coupons()
    coupons["cpn_m"] = _coupon(20, "repeating", None)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    text = "\n".join(report)
    assert code == 1
    assert "duration_in_months is None, expected 3" in text


def test_repeating_coupon_with_wrong_month_count_is_caught():
    coupons = _good_coupons()
    coupons["cpn_m"] = _coupon(20, "repeating", 12)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    assert code == 1
    assert "duration_in_months is 12, expected 3" in "\n".join(report)


def test_forever_coupon_where_once_expected_is_caught():
    """ANNUAL10 is "first invoice only"; forever would discount every annual renewal."""
    coupons = _good_coupons()
    coupons["cpn_a"] = _coupon(10, "forever", None)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    text = "\n".join(report)
    assert code == 1
    assert "duration is 'forever', expected 'once'" in text
    assert "every renewal, forever" in text


def test_once_coupon_where_repeating_expected_is_caught():
    coupons = _good_coupons()
    coupons["cpn_m"] = _coupon(20, "once", None)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    assert code == 1
    assert "duration is 'once', expected 'repeating'" in "\n".join(report)


def test_invalid_coupon_is_caught():
    coupons = _good_coupons()
    coupons["cpn_a"] = _coupon(10, "once", None, valid=False)
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), coupons), env=_coupon_env()
    )
    assert code == 1
    assert "no longer valid" in "\n".join(report)


def test_unretrievable_coupon_is_reported():
    code, report = preflight.run(
        require_all=False, stripe_module=_FakeStripe(_matching_prices(), {}), env=_coupon_env()
    )
    assert code == 1
    assert "could not retrieve" in "\n".join(report)


def test_coupons_are_optional():
    code, _ = preflight.run(require_all=True, stripe_module=_FakeStripe(_matching_prices()), env=_full_env())
    assert code == 0


def test_coupon_expectations_match_the_documented_promotions():
    """The promo copy says 20% off the first 3 months and 10% off the first annual
    invoice. Those two promises are the whole reason duration is checked."""
    by_var = {c.env_var: c for c in preflight.COUPON_EXPECTATIONS}
    monthly = by_var["STRIPE_COUPON_MONTHLY_20"]
    assert (monthly.percent_off, monthly.duration, monthly.duration_in_months) == (20, "repeating", 3)
    annual = by_var["STRIPE_COUPON_ANNUAL_10"]
    assert (annual.percent_off, annual.duration) == (10, "once")


# ---------------------------------------------------------------------------
# Unset IDs and misconfiguration
# ---------------------------------------------------------------------------


def test_unset_price_ids_are_skipped_without_require_all():
    env = _full_env()
    del env["STRIPE_SEAT_PRICE_ENT_ANNUAL"]
    del env["STRIPE_PRICE_PROFESSIONAL_MONTHLY"]
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(_matching_prices()), env=env)
    text = "\n".join(report)
    assert code == 0
    assert "Checked 8 of 10 price objects." in text
    assert "2 price ID(s) not set" in text
    assert "rerun with --require-all before cutover" in text


def test_unset_price_ids_fail_under_require_all():
    env = _full_env()
    del env["STRIPE_SEAT_PRICE_ENT_ANNUAL"]
    code, report = preflight.run(require_all=True, stripe_module=_FakeStripe(_matching_prices()), env=env)
    assert code == 2
    assert "--require-all was passed" in "\n".join(report)


def test_missing_secret_key_is_exit_two():
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe({}), env={})
    assert code == 2
    assert "STRIPE_SECRET_KEY is not set" in report[0]


def test_mismatch_outranks_unset_in_exit_code():
    """A real mismatch must not be masked by the unset-ID path."""
    env = _full_env()
    del env["STRIPE_SEAT_PRICE_ENT_ANNUAL"]
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(5000)
    code, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=env)
    assert code == 1
    assert "MISMATCH" in "\n".join(report)


# ---------------------------------------------------------------------------
# Guidance in the failure output
# ---------------------------------------------------------------------------


def test_failure_output_tells_the_operator_what_to_do():
    prices = _matching_prices()
    prices["price_stripe_price_solo_monthly"] = _price(5000)
    _, report = preflight.run(require_all=False, stripe_module=_FakeStripe(prices), env=_full_env())
    text = "\n".join(report)
    assert "Do not proceed with a cutover" in text
    assert "the pricing page reads the same table" in text


@pytest.mark.parametrize(
    ("cents", "rendered"),
    [(0, "$0.00"), (10000, "$100.00"), (1000000, "$10,000.00"), (6500, "$65.00")],
)
def test_dollar_rendering(cents: int, rendered: str):
    assert preflight._dollars(cents) == rendered
