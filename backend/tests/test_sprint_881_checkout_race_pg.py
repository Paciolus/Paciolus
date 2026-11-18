"""Sprint 881 (AZ-09) — two concurrent first purchases cannot both complete. PostgreSQL only.

Two checkouts for one new account run at the same time, each in its own committed
session, against a fake Stripe whose ``Customer.create`` and ``Session.create`` each take
0.3 s, like real network calls (so the requests overlap). Purchase admission locks the user row, so the second waits for the first's
attempt row and then either refuses (the first is still opening its session) or
expires the first session before opening its own. Either way, of every session
created, exactly one can be paid.

Without the row lock both requests see an empty account, both open a session, and
both sessions can be paid — this test then fails (checked by hand with
``billing.purchase_admission.lock_purchaser`` patched to a no-op; see Sprint 881 in
tasks/todo.md).

SQLite has no row locks, so this module is skipped there; CI's
``backend-tests-postgres`` job runs it.
"""

import threading
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.orm import sessionmaker

from billing.checkout_orchestrator import CheckoutConflictError, orchestrate_checkout
from models import User, UserTier
from subscription_model import CheckoutAttempt
from tests.conftest import _is_test_sqlite
from tests.helpers.fake_stripe import FakeStripe, FakeStripeError

pytestmark = pytest.mark.skipif(_is_test_sqlite, reason="row locks need PostgreSQL")

SOLO_MONTHLY = "price_1QpSoloMonthly000000000a"


@pytest.fixture
def committed(db_engine):
    """A session factory whose writes really commit; rows created here are deleted after."""
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    created_user_ids: list[int] = []
    yield factory, created_user_ids
    with factory() as s:
        for uid in created_user_ids:
            s.query(CheckoutAttempt).filter(CheckoutAttempt.user_id == uid).delete()
            s.query(User).filter(User.id == uid).delete()
        s.commit()


@pytest.fixture
def fake_stripe():
    fake = FakeStripe(price_intervals={SOLO_MONTHLY: "month"})
    fake.customer_create_delay = 0.3
    fake.session_create_delay = 0.3
    with (
        patch("billing.price_config._load_stripe_price_ids", return_value={"solo": {"monthly": SOLO_MONTHLY}}),
        patch("billing.stripe_client.is_stripe_enabled", return_value=True),
        patch("billing.stripe_client.get_stripe", return_value=fake),
        patch("billing.checkout.get_stripe", return_value=fake),
        patch("config.FRONTEND_URL", "https://app.example.test"),
    ):
        yield fake


def test_two_concurrent_first_purchases_cannot_both_complete(committed, fake_stripe):
    factory, created = committed
    with factory() as s:
        user = User(
            email=f"az09_race_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="x",
            tier=UserTier.FREE,
            is_active=True,
            is_verified=True,
        )
        s.add(user)
        s.commit()
        user_id, email = user.id, user.email
    created.append(user_id)

    start = threading.Barrier(2)
    outcomes: list[object] = []

    def purchase():
        with factory() as db:
            start.wait()
            try:
                outcomes.append(
                    orchestrate_checkout(
                        tier="solo",
                        interval="monthly",
                        seat_count=0,
                        promo_code=None,
                        dpa_accepted=False,
                        user_id=user_id,
                        user_email=email,
                        db=db,
                    )
                )
            except CheckoutConflictError as exc:
                outcomes.append(exc)

    threads = [threading.Thread(target=purchase) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not any(t.is_alive() for t in threads)
    assert len(outcomes) == 2

    paid = 0
    for session_id in list(fake_stripe.created_sessions):
        try:
            fake_stripe.complete_session(session_id, SOLO_MONTHLY)
            paid += 1
        except FakeStripeError:
            pass
    assert paid == 1, f"{paid} sessions could be paid; outcomes={outcomes}"
    assert any(isinstance(o, str) for o in outcomes)
