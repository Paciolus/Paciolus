"""Sprint 741a — regression tests for the upload-quota reset.

Root cause, from Render production logs on 2026-10-20: `reset_upload_quotas` failed every
hour with `psycopg2.errors.InvalidTextRepresentation` (pgcode 22P02). The job's raw SQL
filtered `WHERE status = 'active'`, but `Subscription.status` is mapped with a bare
`Enum(SubscriptionStatus)` and no `values_callable`, so SQLAlchemy persists the enum
**member name** — the Postgres type's labels are `ACTIVE`, `PAST_DUE`, … and the lowercase
`.value` is not among them.

Why 8,728 passing tests missed it: on SQLite that enum is a VARCHAR with no type
constraint, so the comparison does not error. It simply matches **zero rows**, and the job
logs success with `records_processed: 0`. The defect is invisible to the dev dialect.

So the tests below assert **behaviour, not SQL text**: a subscription that should be reset
is actually reset. That fails on the old implementation under SQLite (zero rows matched)
and passes on the new one, which is what makes it a regression test rather than a
restatement.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from models import User, UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus


@pytest.fixture()
def make_sub(db_session):
    """Create a Subscription with an explicit period end and upload count."""
    counter = {"n": 0}

    def _make(
        *,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        period_end: datetime | None = None,
        uploads_used: int = 5,
        tier: str = "solo",
    ) -> Subscription:
        counter["n"] += 1
        n = counter["n"]
        user = User(
            email=f"quota{n}@example.com",
            name=f"Quota {n}",
            hashed_password="$2b$12$fakehashvalue",
            tier=UserTier.SOLO,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()
        sub = Subscription(
            user_id=user.id,
            tier=tier,
            status=status,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id=f"cus_quota_{n}",
            stripe_subscription_id=f"sub_quota_{n}",
            current_period_end=period_end,
            uploads_used_current_period=uploads_used,
        )
        db_session.add(sub)
        db_session.flush()
        return sub

    return _make


def _run_reset(db_session) -> int:
    """Call the reset directly.

    Sprint 741a extracted this out of the job closure precisely so a test can exercise
    the query without standing up the scheduler's session, DB lock and commit/rollback
    lifecycle — a test that patches all of that is testing the wrapper, not the fix.
    """
    from unittest.mock import patch

    from cleanup_scheduler import reset_upload_quotas

    # commit() would end the fixture's transaction; flush keeps the assertions readable.
    with patch.object(db_session, "commit", db_session.flush):
        return reset_upload_quotas(db_session)


# ---------------------------------------------------------------------------
# The mapping invariant the bug rested on
# ---------------------------------------------------------------------------


def test_status_enum_persists_member_names_not_values():
    """The trap, stated as an assertion.

    `Enum(SubscriptionStatus)` without `values_callable` stores `.name`. Any raw SQL that
    compares this column to a lowercase `.value` is broken on PostgreSQL — which is what
    Sprint 741a fixed. If someone later adds `values_callable=lambda e: [m.value for m in e]`,
    this test fails and points at the call sites that would need rechecking.
    """
    labels = Subscription.__table__.c.status.type.enums
    assert labels == [
        "ACTIVE",
        "PAST_DUE",
        "CANCELED",
        "TRIALING",
        "INCOMPLETE",
        "INCOMPLETE_EXPIRED",
        "UNPAID",
        "PAUSED",
    ]
    assert SubscriptionStatus.ACTIVE.value == "active"
    assert SubscriptionStatus.ACTIVE.value not in labels


def test_reset_quotas_uses_no_raw_status_literal():
    """Guard the specific regression: a lowercase status literal in this job's SQL.

    Narrow by design — it reads the one function, not the whole file, and looks for a
    quoted lowercase enum value rather than any mention of the word.

    The docstring is stripped before matching, because the function's own docstring
    quotes `WHERE status = 'active'` while explaining the bug. The first draft of this
    check flagged it: prose describing a defect is textually identical to the defect, and
    that has now caught me three times in one day (the Sprint 779 boundary scan and the
    Sprint 787 stale-literal check were the other two).
    """
    import ast
    import inspect
    import re
    import textwrap

    import cleanup_scheduler

    source = textwrap.dedent(inspect.getsource(cleanup_scheduler.reset_upload_quotas))
    tree = ast.parse(source)
    func = tree.body[0]
    assert isinstance(func, ast.FunctionDef)

    body = func.body[1:] if ast.get_docstring(func) is not None else func.body
    code = "\n".join(ast.get_source_segment(source, node) or "" for node in body)

    offenders = re.findall(r"status\s*=\s*'(active|trialing|past_due|canceled|unpaid|paused)'", code)
    assert not offenders, (
        f"raw lowercase status literal(s) {offenders} in reset_upload_quotas. "
        f"The Postgres enum labels are member NAMES (ACTIVE, …); bind SubscriptionStatus "
        f"through the ORM instead."
    )


# ---------------------------------------------------------------------------
# Behaviour — these are what fail on the old implementation
# ---------------------------------------------------------------------------


def test_expired_active_subscription_is_reset(db_session, make_sub):
    """The case that had never once worked in production."""
    sub = make_sub(period_end=datetime.now(UTC) - timedelta(days=1), uploads_used=7)

    _run_reset(db_session)

    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 0


def test_reset_is_scoped_to_expired_periods(db_session, make_sub):
    """A subscription still inside its period keeps its counter."""
    sub = make_sub(period_end=datetime.now(UTC) + timedelta(days=5), uploads_used=9)

    _run_reset(db_session)

    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 9


def test_reset_is_scoped_to_active_status(db_session, make_sub):
    """Canceled subscriptions are not reset — their counter is historical."""
    sub = make_sub(
        status=SubscriptionStatus.CANCELED,
        period_end=datetime.now(UTC) - timedelta(days=1),
        uploads_used=4,
    )

    _run_reset(db_session)

    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 4


def test_null_period_end_is_skipped(db_session, make_sub):
    sub = make_sub(period_end=None, uploads_used=3)

    _run_reset(db_session)

    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 3


def test_already_zero_counter_is_untouched(db_session, make_sub):
    """`uploads_used > 0` keeps the UPDATE from touching every row every hour."""
    sub = make_sub(period_end=datetime.now(UTC) - timedelta(days=1), uploads_used=0)

    _run_reset(db_session)

    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 0


def test_resets_many_subscriptions_in_one_pass(db_session, make_sub):
    past = datetime.now(UTC) - timedelta(days=2)
    subs = [make_sub(period_end=past, uploads_used=i + 1) for i in range(4)]
    untouched = make_sub(period_end=datetime.now(UTC) + timedelta(days=2), uploads_used=11)

    _run_reset(db_session)

    for sub in subs:
        db_session.refresh(sub)
        assert sub.uploads_used_current_period == 0
    db_session.refresh(untouched)
    assert untouched.uploads_used_current_period == 11


def test_reset_does_not_null_the_updated_at_column(db_session, make_sub):
    """An ORM `update()` includes columns carrying `onupdate`, unlike the raw SQL it
    replaced — so check the timestamp is refreshed rather than wiped.

    `Subscription.updated_at` has a callable `onupdate`, which SQLAlchemy evaluates at
    execution time. Compiling the statement shows `updated_at=None` in the parameter dict,
    which looks alarming and is only an artefact of compile-time inspection. Asserting the
    runtime value is the way to tell the difference, and a NULL here would be silent data
    damage on every hourly run.
    """
    before = datetime(2020, 1, 1, tzinfo=UTC).replace(tzinfo=None)
    sub = make_sub(period_end=datetime.now(UTC) - timedelta(days=1), uploads_used=5)
    sub.updated_at = before
    db_session.flush()

    _run_reset(db_session)
    db_session.refresh(sub)

    assert sub.uploads_used_current_period == 0
    assert sub.updated_at is not None, "onupdate wrote NULL — the reset would corrupt the row"
    assert sub.updated_at > before


def test_reset_matches_either_enum_label_convention(db_session, make_sub):
    """The predicate must not depend on how the schema was built.

    PR #177 review: production's `subscriptionstatus` holds member names (`ACTIVE`),
    because it was created by `create_all`; the documented Alembic chain creates the same
    type with lowercase labels (`active`). A predicate bound to either representation is
    correct on one database and broken on the other. The job compares
    `lower(status::text)`, which matches both — asserted here by checking the emitted SQL
    folds case rather than binding a literal label.
    """
    import inspect

    from cleanup_scheduler import reset_upload_quotas

    source = inspect.getsource(reset_upload_quotas)
    assert "func.lower" in source and "cast(" in source, (
        "the status predicate no longer case-folds; it will be correct on only one of "
        "production (member-name labels) and a chain-built database (lowercase labels). "
        "See Sprint 741c."
    )

    # And it still works.
    sub = make_sub(period_end=datetime.now(UTC) - timedelta(days=1), uploads_used=2)
    _run_reset(db_session)
    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 0


def test_trialing_subscription_is_not_reset(db_session, make_sub):
    """Documents the current scope: only ACTIVE is reset.

    Whether a trialing subscription past its period end should also reset is a product
    question, not a bug — the job has always filtered on ACTIVE alone. Pinned here so a
    future change to that scope is deliberate.
    """
    sub = make_sub(
        status=SubscriptionStatus.TRIALING,
        period_end=datetime.now(UTC) - timedelta(days=1),
        uploads_used=6,
    )

    _run_reset(db_session)

    db_session.refresh(sub)
    assert sub.uploads_used_current_period == 6
