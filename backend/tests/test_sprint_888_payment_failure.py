"""Sprint 888 (CEO brief 13A, review AZ-12): what a failed payment does, and what we say it does.

Paid features pause at the **first** failed payment (``invoice.payment_failed`` sets the
subscription PAST_DUE and the user's tier to Free). Cancellation comes later, seven days
after the third failed retry (``process_grace_period_expirations``). Access returns when
payment succeeds. The pricing FAQ and every dunning email must describe that timing.
"""

import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.webhook_handler import process_webhook_event
from models import User, UserTier
from shared.entitlement_checks import get_effective_entitlements
from shared.entitlements import get_entitlements
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

REPO = Path(__file__).resolve().parents[2]
PRICING_TS = REPO / "frontend" / "src" / "domain" / "pricing.ts"

CUSTOMER = "cus_sprint888"


@pytest.fixture
def solo_subscriber(db_session):
    user = User(
        email="sprint888@test.com",
        name="Sprint 888",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.SOLO,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    sub = Subscription(
        user_id=user.id,
        tier="solo",
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        stripe_customer_id=CUSTOMER,
        stripe_subscription_id="sub_sprint888",
        seat_count=1,
        additional_seats=0,
    )
    db_session.add(sub)
    db_session.flush()
    return user, sub


def _subscription_event(status: str) -> dict:
    return {
        "id": "sub_sprint888",
        "customer": CUSTOMER,
        "status": status,
        "metadata": {},
        "items": {"data": [{"price": {"id": "price_solo_monthly", "recurring": {"interval": "month"}}, "quantity": 1}]},
    }


class TestFirstFailedPaymentPausesPaidFeatures:
    @patch("email_service.send_dunning_first_failure")
    def test_first_failure_moves_entitlements_to_free(self, _mail, db_session, solo_subscriber):
        user, sub = solo_subscriber
        assert get_effective_entitlements(user, db_session).uploads_per_month == 100

        handled = process_webhook_event(db_session, "invoice.payment_failed", {"id": "in_1", "customer": CUSTOMER})

        assert handled is True
        db_session.refresh(user)
        db_session.refresh(sub)
        assert sub.status == SubscriptionStatus.PAST_DUE
        assert user.tier == UserTier.FREE
        effective = get_effective_entitlements(user, db_session)
        free = get_entitlements(UserTier.FREE)
        assert effective == free
        # The concrete Free allowance a lapsed Solo subscriber falls back to.
        assert effective.uploads_per_month == 10
        assert effective.max_clients == 3
        # Not canceled yet: cancellation is a later, separate step.
        assert sub.status != SubscriptionStatus.CANCELED

    @patch("email_service.send_dunning_recovered")
    @patch("email_service.send_dunning_first_failure")
    def test_access_returns_when_stripe_reports_the_subscription_active(self, _fail, _ok, db_session, solo_subscriber):
        user, sub = solo_subscriber
        process_webhook_event(db_session, "invoice.payment_failed", {"id": "in_1", "customer": CUSTOMER})

        with patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"):
            process_webhook_event(db_session, "customer.subscription.updated", _subscription_event("active"))

        db_session.refresh(user)
        assert user.tier == UserTier.SOLO
        assert get_effective_entitlements(user, db_session).uploads_per_month == 100

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Sprint 888 finding for the CEO: invoice.paid sets the subscription ACTIVE but leaves "
            "user.tier on Free, and bumps updated_at, so Stripe's customer.subscription.updated for "
            "the same recovery (created in the same second or earlier) is skipped as stale. "
            "The subscriber is charged and stays on Free."
        ),
    )
    @patch("email_service.send_dunning_recovered")
    @patch("email_service.send_dunning_first_failure")
    def test_access_returns_when_invoice_paid_arrives_first(self, _fail, _ok, db_session, solo_subscriber):
        user, sub = solo_subscriber
        process_webhook_event(db_session, "invoice.payment_failed", {"id": "in_1", "customer": CUSTOMER})
        recovery_created = int(datetime.now(UTC).timestamp())

        process_webhook_event(db_session, "invoice.paid", {"id": "in_1", "customer": CUSTOMER})
        with patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"):
            process_webhook_event(
                db_session,
                "customer.subscription.updated",
                _subscription_event("active"),
                event_created=recovery_created,
            )

        db_session.refresh(user)
        assert user.tier == UserTier.SOLO

    @patch("email_service.send_dunning_suspended")
    @patch("email_service.send_dunning_final_notice")
    @patch("email_service.send_dunning_second_failure")
    @patch("email_service.send_dunning_first_failure")
    def test_cancellation_comes_seven_days_after_the_third_failure(self, _1, _2, _3, _4, db_session, solo_subscriber):
        from billing.dunning_engine import process_grace_period_expirations
        from dunning_model import DunningEpisode

        user, sub = solo_subscriber
        for n in range(3):
            process_webhook_event(db_session, "invoice.payment_failed", {"id": "in_1", "customer": CUSTOMER})
        db_session.refresh(sub)
        assert sub.status == SubscriptionStatus.PAST_DUE

        episode = db_session.query(DunningEpisode).filter_by(subscription_id=sub.id).one()
        episode.last_failed_at = datetime.now(UTC) - timedelta(days=6, hours=23)
        db_session.flush()
        assert process_grace_period_expirations(db_session) == 0

        episode.last_failed_at = datetime.now(UTC) - timedelta(days=7, minutes=1)
        db_session.flush()
        assert process_grace_period_expirations(db_session) == 1
        db_session.refresh(sub)
        assert sub.status == SubscriptionStatus.CANCELED


# ---------------------------------------------------------------------------
# Copy check: FAQ and dunning emails describe the same timing
# ---------------------------------------------------------------------------

_FORBIDDEN_TIMING = [
    re.compile(r"grace period", re.I),
    re.compile(r"avoid (service )?interruption", re.I),
    re.compile(r"will be suspended", re.I),
    re.compile(r"retained for 30 days", re.I),
]


def _faq_answer(question: str) -> str:
    text = PRICING_TS.read_text(encoding="utf-8")
    m = re.search(re.escape(question) + r"',\s*answer:\s*'((?:[^'\\]|\\.)*)'", text)
    assert m, f"FAQ question not found: {question}"
    return m.group(1).replace("\\'", "'")


def _captured_emails() -> dict[str, str]:
    import email_service

    sent: dict[str, str] = {}

    def capture(to_email, subject, html_body, plain_body):
        sent[subject] = f"{subject}\n{html_body}\n{plain_body}"
        return email_service.EmailResult(success=True, message="captured")

    with patch.object(email_service, "_send_dunning_email", side_effect=capture):
        email_service.send_dunning_first_failure("a@b.c", "$100.00", "Paciolus Solo (monthly)", "https://x/billing")
        email_service.send_dunning_second_failure("a@b.c", "$100.00", "https://x/billing")
        email_service.send_dunning_final_notice("a@b.c", "December 1, 2026", "https://x/billing")
        email_service.send_dunning_suspended("a@b.c", "https://x/pricing")
        email_service.send_dunning_recovered("a@b.c", "$100.00")
    assert len(sent) == 5
    return sent


class TestPaymentFailureCopy:
    def test_faq_says_paid_features_pause_at_the_first_failed_payment(self):
        answer = _faq_answer("What happens if a payment fails?")
        assert re.search(r"paid features pause", answer, re.I)
        assert re.search(r"first failed payment", answer, re.I)
        assert re.search(r"canceled", answer, re.I)
        assert re.search(r"7 days after the (third|final) (failed )?(retry|attempt)", answer, re.I)
        assert re.search(r"(access|paid features) (return|come back)", answer, re.I)
        assert re.search(r"remain readable", answer, re.I)
        for pattern in _FORBIDDEN_TIMING:
            assert not pattern.search(answer), pattern.pattern

    def test_trial_answer_does_not_promise_a_grace_period(self):
        answer = _faq_answer("What happens when my trial expires?")
        for pattern in _FORBIDDEN_TIMING:
            assert not pattern.search(answer), pattern.pattern

    def test_failure_emails_say_paid_features_are_paused_now(self):
        emails = _captured_emails()
        failure_emails = [body for subject, body in emails.items() if "received" not in subject.lower()]
        assert len(failure_emails) == 4
        for body in failure_emails:
            for pattern in _FORBIDDEN_TIMING:
                assert not pattern.search(body), (pattern.pattern, body[:120])
            assert re.search(r"remain readable", body, re.I), body[:120]
        first, second, final = failure_emails[0], failure_emails[1], failure_emails[2]
        for body in (first, second, final):
            assert re.search(r"paid features are paused", body, re.I), body[:120]
        assert re.search(r"will be canceled on December 1, 2026", final)

    def test_recovered_email_says_paid_features_are_back(self):
        emails = _captured_emails()
        (body,) = [b for s, b in emails.items() if "received" in s.lower()]
        assert re.search(r"paid features are available again", body, re.I)
