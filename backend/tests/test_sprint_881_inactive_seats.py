"""Sprint 881 — an inactive subscription leaves the firm one seat (AZ-08).

The seat check used ``sub.total_seats`` whatever the subscription's status, so a cancelled
or past-due firm kept its paid allocation. CEO decision 2026-11-16: an inactive
subscription leaves the Free allowance of 1 seat. Existing members are not removed, but no
invitation can be sent or accepted.
"""

import pytest
from fastapi import HTTPException

from organization_model import OrganizationMember
from subscription_model import SubscriptionStatus
from tests.test_sprint_881_seats import (
    PRO_MONTHLY,
    PRO_SEAT_MONTHLY,
    _add_members,
    _hard,
    _org_for,
    _pending_invite,
    _price_ids,  # noqa: F401 — autouse fixture: seat price IDs in the environment
    _sync,
    stripe_subscription,
)


class TestInactiveSubscriptionSeats:
    @pytest.mark.parametrize("stripe_status", ["canceled", "past_due", "unpaid", "incomplete_expired", "paused"])
    def test_owner_only_firm_cannot_reserve_a_seat(self, db_session, make_user, stripe_status):
        from shared.entitlement_checks import check_seat_limit_for_org

        prefix = f"az08_{stripe_status}_"
        owner = make_user(email=f"{prefix}owner@example.com")
        sub = _sync(
            db_session, owner, "professional", stripe_subscription(PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 2)
        )
        org = _org_for(db_session, owner, sub, prefix.rstrip("_").replace("_", "-"))
        with _hard():
            check_seat_limit_for_org(db_session, org.id)  # active: 1/9 used

        _sync(
            db_session,
            owner,
            "professional",
            stripe_subscription(PRO_MONTHLY, 50000, PRO_SEAT_MONTHLY, 6500, 2, status=stripe_status),
        )
        with _hard(), pytest.raises(HTTPException) as exc:
            check_seat_limit_for_org(db_session, org.id)
        assert exc.value.status_code == 403
        assert "(1/1)" in exc.value.detail["message"]

    @pytest.mark.parametrize("stripe_status", ["canceled", "past_due"])
    def test_owner_only_firm_cannot_accept_existing_invite(self, db_session, make_user, stripe_status):
        """An invite sent while active cannot be accepted once the subscription lapses."""
        from shared.entitlement_checks import check_seat_limit_for_org

        prefix = f"az08acc_{stripe_status}_"
        owner = make_user(email=f"{prefix}owner@example.com")
        sub = _sync(db_session, owner, "professional", stripe_subscription(PRO_MONTHLY, 50000, None, 0, 0))
        org = _org_for(db_session, owner, sub, prefix.rstrip("_").replace("_", "-"))
        invite = _pending_invite(db_session, org, f"{prefix}invitee@example.com", owner)
        with _hard():
            check_seat_limit_for_org(db_session, org.id, exclude_invite_id=invite.id)  # active: accept fits

        _sync(
            db_session,
            owner,
            "professional",
            stripe_subscription(PRO_MONTHLY, 50000, None, 0, 0, status=stripe_status),
        )
        with _hard(), pytest.raises(HTTPException) as exc:
            check_seat_limit_for_org(db_session, org.id, exclude_invite_id=invite.id)
        assert exc.value.status_code == 403

    def test_existing_members_are_not_removed(self, db_session, make_user):
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(email="az08keep_owner@example.com")
        sub = _sync(db_session, owner, "professional", stripe_subscription(PRO_MONTHLY, 50000, None, 0, 0))
        org = _org_for(db_session, owner, sub, "az08-keep")
        _add_members(db_session, make_user, org, 3, "az08keep_m")
        _sync(db_session, owner, "professional", stripe_subscription(PRO_MONTHLY, 50000, None, 0, 0, status="canceled"))
        with _hard(), pytest.raises(HTTPException):
            check_seat_limit_for_org(db_session, org.id)
        assert db_session.query(OrganizationMember).filter(OrganizationMember.organization_id == org.id).count() == 4

    def test_trialing_keeps_paid_allowance(self, db_session, make_user):
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(email="az08trial_owner@example.com")
        sub = _sync(
            db_session,
            owner,
            "professional",
            stripe_subscription(PRO_MONTHLY, 50000, None, 0, 0, status="trialing"),
        )
        assert sub.status == SubscriptionStatus.TRIALING
        org = _org_for(db_session, owner, sub, "az08-trial")
        _add_members(db_session, make_user, org, 5, "az08trial_m")
        with _hard():
            check_seat_limit_for_org(db_session, org.id)  # 6/7 used
