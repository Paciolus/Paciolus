"""Tests for the 2026-04-20 refactor pass.

Covers the behaviour-preserving extractions:

* ``shared.helpers`` continues to re-export every symbol it used to expose.
* ``shared.organization_policy.apply_org_subscription_to_user`` backfills
  ``org.subscription_id`` via the owner's personal subscription and copies
  the tier to the joining user.
* ``shared.organization_policy.revert_user_tier_after_removal`` restores
  a personal subscription tier when present, otherwise FREE.
* ``shared.billing_access.require_billing_analytics_access`` enforces the
  owner/admin + solo-subscription rule.
"""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

# ---------------------------------------------------------------------------
# Helpers (mirror of test_organization_routes fixtures — kept local so these
# tests don't depend on fixture imports).
# ---------------------------------------------------------------------------


def _make_org(db, owner: User, name: str = "Refactor Org") -> Organization:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")[:90]
    org = Organization(name=name, slug=slug, owner_user_id=owner.id)
    db.add(org)
    db.flush()
    membership = OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER)
    db.add(membership)
    owner.organization_id = org.id
    db.flush()
    return org


def _make_sub(db, user: User, tier: str = "professional") -> Subscription:
    sub = Subscription(
        user_id=user.id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        seat_count=3,
        additional_seats=0,
    )
    db.add(sub)
    db.flush()
    return sub


# ---------------------------------------------------------------------------
# helpers.py compatibility shim
# ---------------------------------------------------------------------------


class TestHelpersReExports:
    """Every previously-public symbol is still importable from shared.helpers."""

    def test_upload_pipeline_symbols(self) -> None:
        from shared.helpers import (
            _XLS_MAGIC,
            _XLSX_MAGIC,
            MAX_CELL_LENGTH,
            MAX_COL_COUNT,
            MAX_FILE_SIZE_MB,
            MAX_ROW_COUNT,
            _validate_and_convert_df,
            memory_cleanup,
            parse_uploaded_file,
            parse_uploaded_file_by_format,
            validate_file_size,
        )

        assert MAX_FILE_SIZE_MB == 100
        assert MAX_ROW_COUNT == 500_000
        # Memory cleanup is an @contextmanager — confirm it yields without error.
        with memory_cleanup():
            pass
        for sym in (
            validate_file_size,
            parse_uploaded_file,
            parse_uploaded_file_by_format,
            _validate_and_convert_df,
        ):
            assert callable(sym)
        assert _XLSX_MAGIC
        assert _XLS_MAGIC
        assert MAX_CELL_LENGTH > 0
        assert MAX_COL_COUNT > 0

    def test_filename_and_sanitizer_symbols(self) -> None:
        from shared.helpers import (
            escape_like_wildcards,
            get_filename_display,
            hash_filename,
            safe_download_filename,
            sanitize_csv_value,
        )

        assert sanitize_csv_value("=cmd") == "'=cmd"
        assert escape_like_wildcards("100%_of") == "100\\%\\_of"
        assert len(hash_filename("x.csv")) == 64
        assert get_filename_display("long_name.xlsx") == "long_name..."
        assert ".csv" in safe_download_filename("Client", "TB", "csv")

    def test_background_email_and_tool_recorder_symbols(self) -> None:
        from shared.helpers import (
            _log_tool_activity,
            maybe_record_tool_run,
            safe_background_email,
        )

        assert callable(safe_background_email)
        assert callable(maybe_record_tool_run)
        assert callable(_log_tool_activity)

    def test_json_form_and_client_access_symbols(self) -> None:
        from shared.helpers import (
            get_accessible_client,
            is_authorized_for_client,
            parse_json_list,
            parse_json_mapping,
            require_client,
            try_parse_risk,
            try_parse_risk_band,
        )

        assert parse_json_list("[1,2,3]", "nums") == [1, 2, 3]
        assert parse_json_list("not-json", "nums") is None
        assert parse_json_mapping('{"a":"b"}', "m") == {"a": "b"}
        assert parse_json_mapping("not-json", "m") is None
        for sym in (
            is_authorized_for_client,
            get_accessible_client,
            require_client,
            try_parse_risk,
            try_parse_risk_band,
        ):
            assert callable(sym)


# ---------------------------------------------------------------------------
# organization_policy.apply_org_subscription_to_user
# ---------------------------------------------------------------------------


class TestApplyOrgSubscriptionToUser:
    """Tier inheritance on invite acceptance."""

    def test_inherits_tier_from_org_linked_subscription(self, db_session, make_user):
        owner = make_user(email="owner_apply1@example.com")
        org = _make_org(db_session, owner)
        sub = _make_sub(db_session, owner, tier="professional")
        org.subscription_id = sub.id
        db_session.flush()

        joiner = make_user(email="joiner_apply1@example.com", tier=UserTier.FREE)

        from shared.organization_policy import apply_org_subscription_to_user

        apply_org_subscription_to_user(db_session, joiner, org)

        assert joiner.tier == UserTier("professional")

    def test_backfills_org_subscription_from_owner(self, db_session, make_user):
        """When org.subscription_id is null, look up the owner's sub and backfill."""
        owner = make_user(email="owner_apply2@example.com")
        org = _make_org(db_session, owner)
        # Owner has a sub but org.subscription_id is null
        sub = _make_sub(db_session, owner, tier="solo")
        db_session.flush()
        assert org.subscription_id is None

        joiner = make_user(email="joiner_apply2@example.com", tier=UserTier.FREE)

        from shared.organization_policy import apply_org_subscription_to_user

        apply_org_subscription_to_user(db_session, joiner, org)

        assert joiner.tier == UserTier("solo")
        assert org.subscription_id == sub.id  # backfilled

    def test_no_subscription_leaves_tier_untouched(self, db_session, make_user):
        owner = make_user(email="owner_apply3@example.com")
        org = _make_org(db_session, owner)
        joiner = make_user(email="joiner_apply3@example.com", tier=UserTier.FREE)

        from shared.organization_policy import apply_org_subscription_to_user

        apply_org_subscription_to_user(db_session, joiner, org)

        # No ACTIVE/TRIALING sub exists; joiner stays on prior tier.
        assert joiner.tier == UserTier.FREE


# ---------------------------------------------------------------------------
# organization_policy.revert_user_tier_after_removal
# ---------------------------------------------------------------------------


class TestRevertUserTierAfterRemoval:
    def test_restores_personal_subscription_tier(self, db_session, make_user):
        owner = make_user(email="revert1_owner@example.com")
        org = _make_org(db_session, owner, name="Revert1 Org")

        user = make_user(email="revert1@example.com", tier=UserTier("professional"))
        user.organization_id = org.id
        _make_sub(db_session, user, tier="solo")

        from shared.organization_policy import revert_user_tier_after_removal

        revert_user_tier_after_removal(db_session, user)

        assert user.organization_id is None
        assert user.tier == UserTier("solo")

    def test_falls_back_to_free_when_no_personal_subscription(self, db_session, make_user):
        owner = make_user(email="revert2_owner@example.com")
        org = _make_org(db_session, owner, name="Revert2 Org")

        user = make_user(email="revert2@example.com", tier=UserTier("professional"))
        user.organization_id = org.id

        from shared.organization_policy import revert_user_tier_after_removal

        revert_user_tier_after_removal(db_session, user)

        assert user.organization_id is None
        assert user.tier == UserTier.FREE


# ---------------------------------------------------------------------------
# billing_access.require_billing_analytics_access
# ---------------------------------------------------------------------------


class TestBillingAnalyticsAccess:
    def test_org_owner_passes(self, db_session, make_user):
        owner = make_user(email="ba_owner@example.com")
        _make_org(db_session, owner)

        from shared.billing_access import require_billing_analytics_access

        require_billing_analytics_access(db_session, owner)

    def test_org_member_without_admin_is_403(self, db_session, make_user):
        owner = make_user(email="ba_owner2@example.com")
        org = _make_org(db_session, owner)

        member_user = make_user(email="ba_member@example.com")
        member_user.organization_id = org.id
        db_session.add(OrganizationMember(organization_id=org.id, user_id=member_user.id, role=OrgRole.MEMBER))
        db_session.flush()

        from shared.billing_access import require_billing_analytics_access

        with pytest.raises(HTTPException) as exc_info:
            require_billing_analytics_access(db_session, member_user)
        assert exc_info.value.status_code == 403

    def test_solo_without_subscription_is_403(self, db_session, make_user):
        user = make_user(email="ba_solo_nosub@example.com")
        # No organization, no subscription
        from shared.billing_access import require_billing_analytics_access

        with pytest.raises(HTTPException) as exc_info:
            require_billing_analytics_access(db_session, user)
        assert exc_info.value.status_code == 403

    def test_solo_with_active_subscription_passes(self, db_session, make_user):
        user = make_user(email="ba_solo_sub@example.com")
        _make_sub(db_session, user, tier="solo")

        from shared.billing_access import require_billing_analytics_access

        require_billing_analytics_access(db_session, user)
