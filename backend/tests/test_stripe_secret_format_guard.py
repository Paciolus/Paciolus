"""Sprint 719 — production startup guard against test-mode Stripe secrets.

Stripe live-mode cutover is preceded by setting `STRIPE_SECRET_KEY`,
`STRIPE_PUBLISHABLE_KEY`, and `STRIPE_WEBHOOK_SECRET` to live values.
The most common cutover failure is pasting test-mode credentials into
the live env-var slot. Symptoms are silent in production:
- Test-mode `sk_test_*` accepts checkouts to a separate Stripe account
  the customer can't see.
- A test-mode `whsec_*test*` rejects every webhook with 400 (signature
  mismatch); customers don't show up in admin dashboard, dispute events
  miss SLA.

Sprint 719 adds the pure-function `_stripe_secret_format_violations`
in `backend/config.py` plus a startup hard-fail that calls it. This
test exercises the function directly (faster + more reliable than a
subprocess of the whole config module).
"""

from __future__ import annotations

import pytest

from config import _stripe_secret_format_violations


def test_test_mode_secret_key_in_production_is_blocked():
    """sk_test_* in ENV_MODE=production must produce a violation."""
    violations = _stripe_secret_format_violations(
        env_mode="production",
        secret_key="sk_test_abcdef0123456789",
        publishable_key="",
        webhook_secret="",
    )
    assert any("sk_test_" in v or "TEST-mode" in v for v in violations), (
        f"Expected sk_test_ violation, got: {violations}"
    )


def test_test_mode_publishable_key_in_production_is_blocked():
    """pk_test_* in ENV_MODE=production must produce a violation."""
    violations = _stripe_secret_format_violations(
        env_mode="production",
        secret_key="",
        publishable_key="pk_test_abcdef0123456789",
        webhook_secret="",
    )
    assert any("pk_test_" in v or "PUBLISHABLE" in v for v in violations), (
        f"Expected pk_test_ violation, got: {violations}"
    )


def test_test_mode_webhook_secret_in_production_is_blocked():
    """whsec_test_* in ENV_MODE=production must produce a violation."""
    violations = _stripe_secret_format_violations(
        env_mode="production",
        secret_key="",
        publishable_key="",
        webhook_secret="whsec_test_doesnotmatchproduction",
    )
    assert any("WEBHOOK_SECRET" in v or "test-mode" in v.lower() for v in violations), (
        f"Expected webhook_secret violation, got: {violations}"
    )


def test_live_mode_secrets_in_production_pass():
    """Live-mode-shaped secrets in production produce no violations."""
    violations = _stripe_secret_format_violations(
        env_mode="production",
        secret_key="sk_live_abcdef0123456789",
        publishable_key="pk_live_abcdef0123456789",
        webhook_secret="whsec_live_signing_secret_value",
    )
    assert violations == [], f"False positive on live secrets: {violations}"


def test_test_mode_secrets_in_development_are_allowed():
    """In ENV_MODE=development, test-mode keys produce no violations."""
    violations = _stripe_secret_format_violations(
        env_mode="development",
        secret_key="sk_test_doesnotmatter",
        publishable_key="pk_test_anywhere",
        webhook_secret="whsec_test_local",
    )
    assert violations == [], f"Dev mode should not flag test-mode secrets: {violations}"


def test_empty_secrets_pass():
    """Empty/missing secrets produce no violations (other guards handle absence)."""
    violations = _stripe_secret_format_violations(
        env_mode="production",
        secret_key="",
        publishable_key="",
        webhook_secret="",
    )
    assert violations == []


def test_multiple_violations_collected():
    """All three violations surface together so operators see the full picture in one log line."""
    violations = _stripe_secret_format_violations(
        env_mode="production",
        secret_key="sk_test_x",
        publishable_key="pk_test_y",
        webhook_secret="whsec_test_z",
    )
    assert len(violations) == 3, f"Expected 3 violations, got {len(violations)}: {violations}"


@pytest.mark.parametrize("env_mode", ["development", "test", "staging", ""])
def test_non_production_env_modes_skip_check(env_mode: str):
    """Only ENV_MODE='production' triggers the format check.

    Staging and other non-prod modes are intentionally permissive — they
    routinely run with test-mode Stripe secrets and the silent-failure
    blast radius is limited.
    """
    violations = _stripe_secret_format_violations(
        env_mode=env_mode,
        secret_key="sk_test_x",
        publishable_key="pk_test_y",
        webhook_secret="whsec_test_z",
    )
    assert violations == []
