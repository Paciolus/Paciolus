#!/usr/bin/env python3
"""Sprint 780 — Stripe price-parity preflight.

Asserts that the amount Stripe will actually charge equals the amount the product
intends and the pricing page displays.

**Why this exists.** `backend/billing/price_config.py` holds the canonical amounts and
`tests/test_pricing_launch_validation.py` carries ~20 assertions over them — but those
assertions only check the table *against itself*. Nothing had ever fetched a Stripe Price
object. And the mismatch is not hypothetical: `tasks/pricing-launch-readiness.md` records
that Stripe **test mode is still at the v2 price list** (Solo $50 against code and page
$100) and is treated as abandoned. So displayed and charged price already disagree in the
only environment where billing has ever run, and live mode is to be built fresh — meaning
without this check, the first real card is also the first end-to-end test of current
pricing.

**What it checks**, for every price ID present in the environment:

1. The Price object exists and is retrievable with the configured secret key.
2. `unit_amount` equals the canonical cents value.
3. `currency` is `usd`.
4. `recurring.interval` matches the env var's interval (month / year) — a $100 price on
   the wrong cadence bills correctly once and then wrongly forever.
5. The price is `active`.
6. Live/test mode agrees with the secret key's mode, so a test price can never be wired
   into a live deployment.

Coupons named by `STRIPE_COUPON_MONTHLY_20` / `STRIPE_COUPON_ANNUAL_10` are checked, when
set, for existence, percent-off value **and duration**. Duration is not cosmetic: a
"20% off first 3 months" coupon created as plain `repeating` with no month cap discounts
every renewal for the life of the subscription. A missing `percent_off` means an
amount-off coupon that would apply a fixed discount rather than the advertised
percentage. Both are mismatches, not skips.

**Coverage is all ten price objects**: six base (3 tiers x 2 intervals) and four seat
add-ons (Professional and Enterprise x 2 intervals). Mapping only the base table would
silently skip the seat add-ons.

Usage
-----
    # from the repo root, with the target environment's Stripe key exported
    $ STRIPE_SECRET_KEY=sk_live_... python scripts/stripe_price_parity_preflight.py

    # or let it read backend/.env
    $ python scripts/stripe_price_parity_preflight.py

    # fail if any of the ten price IDs is unset (use before a live cutover)
    $ python scripts/stripe_price_parity_preflight.py --require-all

Exit codes
----------
    0 — every configured price matches
    1 — at least one mismatch, missing price, or Stripe error
    2 — misconfiguration (no secret key, or --require-all with unset price IDs)
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

# Canonical amounts live in the backend package; import rather than restate them.
from billing.price_config import (  # noqa: E402
    ENTERPRISE_SEAT_PRICE,
    PRICE_TABLE,
    PROFESSIONAL_SEAT_PRICE,
)

_INTERVAL_TO_STRIPE = {"monthly": "month", "annual": "year"}

PAID_TIERS = ("solo", "professional", "enterprise")
INTERVALS = ("monthly", "annual")


@dataclass(frozen=True)
class ExpectedPrice:
    """One price object we expect to find in Stripe."""

    env_var: str
    label: str
    expected_cents: int
    interval: str  # "monthly" | "annual"

    @property
    def stripe_interval(self) -> str:
        return _INTERVAL_TO_STRIPE[self.interval]


def build_expectations() -> list[ExpectedPrice]:
    """All ten price objects: six base plans plus four seat add-ons."""
    expected: list[ExpectedPrice] = []

    for tier in PAID_TIERS:
        for interval in INTERVALS:
            expected.append(
                ExpectedPrice(
                    env_var=f"STRIPE_PRICE_{tier.upper()}_{interval.upper()}",
                    label=f"{tier} {interval} base plan",
                    expected_cents=PRICE_TABLE[tier][interval],
                    interval=interval,
                )
            )

    seat_tables = (
        ("PRO", "professional", PROFESSIONAL_SEAT_PRICE),
        ("ENT", "enterprise", ENTERPRISE_SEAT_PRICE),
    )
    for env_abbr, tier_label, table in seat_tables:
        for interval in INTERVALS:
            expected.append(
                ExpectedPrice(
                    env_var=f"STRIPE_SEAT_PRICE_{env_abbr}_{interval.upper()}",
                    label=f"{tier_label} {interval} seat add-on",
                    expected_cents=table[interval],
                    interval=interval,
                )
            )

    return expected


@dataclass(frozen=True)
class ExpectedCoupon:
    """One promotional coupon, including how long it is supposed to last.

    Duration is not a detail. A "20% off first 3 months" coupon created as plain
    `repeating` with no month cap discounts every renewal for the life of the
    subscription: correct on the first invoice, wrong on every one after it.
    """

    env_var: str
    label: str
    percent_off: int
    duration: str  # Stripe: "once" | "repeating" | "forever"
    duration_in_months: int | None = None


COUPON_EXPECTATIONS: tuple[ExpectedCoupon, ...] = (
    ExpectedCoupon(
        env_var="STRIPE_COUPON_MONTHLY_20",
        label="monthly 20% off first 3 months",
        percent_off=20,
        duration="repeating",
        duration_in_months=3,
    ),
    ExpectedCoupon(
        env_var="STRIPE_COUPON_ANNUAL_10",
        label="annual 10% off first invoice",
        percent_off=10,
        duration="once",
    ),
)


def _dollars(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def check_price(stripe_module, expected: ExpectedPrice, price_id: str, key_is_live: bool) -> list[str]:
    """Retrieve one Price and return a list of problem descriptions (empty = pass)."""
    try:
        price = stripe_module.Price.retrieve(price_id)
    except Exception as exc:  # noqa: BLE001 — any Stripe error is a preflight failure
        return [f"{expected.label}: could not retrieve {price_id} — {type(exc).__name__}: {exc}"]

    problems: list[str] = []

    actual_cents = price.get("unit_amount")
    if actual_cents != expected.expected_cents:
        problems.append(
            f"{expected.label}: Stripe charges {_dollars(actual_cents) if actual_cents is not None else 'None'} "
            f"but the product intends {_dollars(expected.expected_cents)} "
            f"({price_id}, unit_amount={actual_cents} vs {expected.expected_cents})"
        )

    currency = (price.get("currency") or "").lower()
    if currency != "usd":
        problems.append(f"{expected.label}: currency is {currency!r}, expected 'usd' ({price_id})")

    recurring = price.get("recurring") or {}
    actual_interval = recurring.get("interval")
    if actual_interval != expected.stripe_interval:
        problems.append(
            f"{expected.label}: billing interval is {actual_interval!r}, expected "
            f"{expected.stripe_interval!r} ({price_id}) — this bills correctly once, then wrongly forever"
        )

    if price.get("active") is False:
        problems.append(f"{expected.label}: price is archived/inactive ({price_id})")

    price_is_live = price.get("livemode")
    if price_is_live is not None and price_is_live != key_is_live:
        problems.append(
            f"{expected.label}: price livemode={price_is_live} but the secret key is "
            f"{'live' if key_is_live else 'test'} mode ({price_id})"
        )

    return problems


def check_coupon(stripe_module, expected: ExpectedCoupon, coupon_id: str) -> list[str]:
    """Retrieve one Coupon and return problem descriptions (empty = pass)."""
    label = expected.label
    try:
        coupon = stripe_module.Coupon.retrieve(coupon_id)
    except Exception as exc:  # noqa: BLE001
        return [f"coupon {label}: could not retrieve {coupon_id} — {type(exc).__name__}: {exc}"]

    problems: list[str] = []

    # A missing percent_off means an amount-off coupon. Treat it as a mismatch, never
    # as "nothing to compare": checkout would apply a fixed discount instead of the
    # advertised percentage.
    percent = coupon.get("percent_off")
    if percent is None:
        problems.append(
            f"coupon {label}: has no percent_off (amount_off={coupon.get('amount_off')}), but the product "
            f"advertises {expected.percent_off}% — checkout would apply a fixed discount ({coupon_id})"
        )
    elif int(percent) != expected.percent_off:
        problems.append(f"coupon {label}: percent_off is {percent}, expected {expected.percent_off} ({coupon_id})")

    # Duration decides whether the discount ever stops.
    duration = coupon.get("duration")
    if duration != expected.duration:
        suffix = (
            " — this discounts every renewal, forever"
            if duration in {"repeating", "forever"} and expected.duration == "once"
            else ""
        )
        problems.append(
            f"coupon {label}: duration is {duration!r}, expected {expected.duration!r} ({coupon_id}){suffix}"
        )

    if expected.duration == "repeating":
        months = coupon.get("duration_in_months")
        if months != expected.duration_in_months:
            problems.append(
                f"coupon {label}: duration_in_months is {months}, expected {expected.duration_in_months} "
                f"({coupon_id}) — the discount would apply for the wrong number of billing periods"
            )

    if coupon.get("valid") is False:
        problems.append(f"coupon {label}: coupon is no longer valid ({coupon_id})")

    return problems


def run(require_all: bool, stripe_module=None, env: dict[str, str] | None = None) -> tuple[int, list[str]]:
    """Run the preflight. Returns (exit_code, report_lines)."""
    env = dict(os.environ) if env is None else env
    report: list[str] = []

    secret_key = env.get("STRIPE_SECRET_KEY", "").strip()
    if not secret_key:
        return 2, ["STRIPE_SECRET_KEY is not set. Export the key for the environment you are checking."]

    key_is_live = secret_key.startswith("sk_live_")
    mode = "LIVE" if key_is_live else "TEST"

    if stripe_module is None:
        try:
            import stripe as stripe_module  # type: ignore[no-redef]
        except ImportError:
            return 2, ["the `stripe` package is not installed in this interpreter"]
        stripe_module.api_key = secret_key

    report.append(f"Stripe price-parity preflight — {mode} mode")
    report.append("")

    expectations = build_expectations()
    unset: list[ExpectedPrice] = []
    problems: list[str] = []
    checked = 0

    for expected in expectations:
        price_id = env.get(expected.env_var, "").strip()
        if not price_id:
            unset.append(expected)
            continue
        checked += 1
        found = check_price(stripe_module, expected, price_id, key_is_live)
        if found:
            problems.extend(found)
        else:
            report.append(
                f"  PASS  {expected.label:<40} {_dollars(expected.expected_cents):>12} / "
                f"{expected.stripe_interval:<5} {price_id}"
            )

    for expected_coupon in COUPON_EXPECTATIONS:
        coupon_id = env.get(expected_coupon.env_var, "").strip()
        if not coupon_id:
            continue
        found = check_coupon(stripe_module, expected_coupon, coupon_id)
        if found:
            problems.extend(found)
        else:
            span = (
                f"{expected_coupon.duration_in_months} months"
                if expected_coupon.duration == "repeating"
                else expected_coupon.duration
            )
            report.append(
                f"  PASS  coupon {expected_coupon.label:<33} {expected_coupon.percent_off}% / {span:<10} {coupon_id}"
            )

    report.append("")
    report.append(f"Checked {checked} of {len(expectations)} price objects.")

    if unset:
        report.append("")
        report.append(f"{len(unset)} price ID(s) not set in this environment:")
        for expected in unset:
            report.append(f"  - {expected.env_var:<40} ({expected.label})")

    exit_code = 0

    if problems:
        report.append("")
        report.append(f"MISMATCH — {len(problems)} problem(s):")
        for problem in problems:
            report.append(f"  ! {problem}")
        report.append("")
        report.append(
            "Do not proceed with a cutover. Either correct the Stripe Price objects or correct "
            "backend/billing/price_config.py — but the pricing page reads the same table, so the "
            "table is almost certainly right and Stripe is wrong."
        )
        exit_code = 1

    if unset and require_all:
        report.append("")
        report.append("--require-all was passed and some price IDs are unset: treating as failure.")
        exit_code = max(exit_code, 2)

    if exit_code == 0:
        report.append("")
        report.append(
            "ALL CHECKED PRICES MATCH."
            if not unset
            else "All configured prices match. Unset IDs above were skipped — rerun with --require-all before cutover."
        )

    return exit_code, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="fail if any of the ten price IDs is unset (use before a live cutover)",
    )
    args = parser.parse_args(argv)

    # Load backend/.env if present, so local runs behave like the app does.
    env_file = BACKEND / ".env"
    if env_file.exists() and not os.environ.get("STRIPE_SECRET_KEY"):
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
        except ImportError:
            pass

    exit_code, report = run(require_all=args.require_all)
    print("\n".join(report))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
