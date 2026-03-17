"""
Phase LXII: Unit tests for shared/entitlement_checks.py.

Tests all entitlement dependency functions:
- _raise_or_log           — soft vs hard enforcement mode
- check_upload_limit      — DB-backed monthly ActivityLog count + subscription path
- check_client_limit      — DB-backed active Client count
- check_tool_access       — factory: tier-based tool access gate
- check_format_access     — factory: tier-based format access gate
- check_workspace_access  — tier gate (Solo+ only)
- check_export_access     — tier gate (Solo+ only)
- check_export_sharing_access — tier gate (Professional+ only)
- check_admin_dashboard_access — tier gate (Professional+ only)
- check_activity_log_access — tier gate (Professional+ only)
- check_bulk_upload_access — tier gate (Enterprise only)
- check_custom_branding_access — tier gate (Enterprise only)
- check_seat_limit        — subscription-backed seat validation
- check_seat_limit_for_org — org-level seat enforcement
- _resolve_org_subscription — org subscription resolution with fallback
- increment_upload_count  — subscription upload counter increment

Functions are called directly as Python (bypassing FastAPI DI).
Enforcement mode is "hard" by default (raises HTTPException 403).
Soft mode is tested via monkeypatching _get_enforcement_mode.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException

# Import subscription_model at module level so Base.metadata includes the
# subscriptions table before the session-scoped db_engine fixture calls create_all().
import subscription_model  # noqa: F401 — side-effect import to register ORM model
from models import ActivityLog, UserTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_activity_log(user_id, db_session, timestamp=None):
    """Insert one ActivityLog row for the given user_id."""
    ts = timestamp or datetime.now(UTC)
    log = ActivityLog(
        user_id=user_id,
        filename_hash="a" * 64,
        filename_display="test.csv",
        timestamp=ts,
        record_count=10,
        total_debits=1000.00,
        total_credits=1000.00,
        materiality_threshold=500.00,
        was_balanced=True,
    )
    db_session.add(log)
    db_session.flush()
    return log


# ---------------------------------------------------------------------------
# check_diagnostic_limit
# ---------------------------------------------------------------------------


class TestCheckDiagnosticLimit:
    def test_professional_tier_unlimited_always_passes(self, make_user, db_session):
        """PROFESSIONAL tier has diagnostics_per_month=0 (unlimited)."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.PROFESSIONAL, email="professional_diag@example.com")
        result = check_diagnostic_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_zero_logs_passes(self, make_user, db_session):
        """FREE tier with no usage passes."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.FREE, email="free_diag_0@example.com")
        result = check_diagnostic_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_under_limit_passes(self, make_user, db_session):
        """FREE tier: 5 logs (limit=10) should pass."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.FREE, email="free_diag_5@example.com")
        for _ in range(5):
            _make_activity_log(user.id, db_session)

        result = check_diagnostic_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_at_limit_raises_403(self, make_user, db_session):
        """FREE tier: exactly 10 logs this month raises 403."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.FREE, email="free_diag_10@example.com")
        for _ in range(10):
            _make_activity_log(user.id, db_session)

        with pytest.raises(HTTPException) as exc_info:
            check_diagnostic_limit(user=user, db=db_session)

        assert exc_info.value.status_code == 403
        detail = exc_info.value.detail
        assert detail["code"] == "TIER_LIMIT_EXCEEDED"
        assert detail["resource"] == "uploads"
        assert "/pricing" in detail["upgrade_url"]

    def test_free_tier_over_limit_raises_403(self, make_user, db_session):
        """FREE tier: 12 logs (over limit of 10) raises 403."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.FREE, email="free_diag_12@example.com")
        for _ in range(12):
            _make_activity_log(user.id, db_session)

        with pytest.raises(HTTPException) as exc_info:
            check_diagnostic_limit(user=user, db=db_session)

        assert exc_info.value.status_code == 403

    def test_soft_mode_at_limit_does_not_raise(self, make_user, db_session):
        """Soft enforcement: limit exceeded is logged but no exception raised."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.FREE, email="free_diag_soft@example.com")
        for _ in range(11):
            _make_activity_log(user.id, db_session)

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            result = check_diagnostic_limit(user=user, db=db_session)

        assert result is user

    def test_only_current_month_logs_counted(self, make_user, db_session):
        """Logs from a previous month should not count toward the limit."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.SOLO, email="solo_diag_month@example.com")
        # SOLO limit=20; add 20 logs from January 2024 (in the past)
        old_ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        for _ in range(20):
            _make_activity_log(user.id, db_session, timestamp=old_ts)

        # Should pass because all logs are from a different month
        result = check_diagnostic_limit(user=user, db=db_session)
        assert result is user

    def test_only_current_user_logs_counted(self, make_user, db_session):
        """Another user's logs should not affect this user's limit."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.FREE, email="free_diag_me@example.com")
        other = make_user(tier=UserTier.FREE, email="free_diag_other@example.com")

        # Add 10 logs for other user (at their limit), 0 for user
        for _ in range(10):
            _make_activity_log(other.id, db_session)

        # user should still pass
        result = check_diagnostic_limit(user=user, db=db_session)
        assert result is user


# ---------------------------------------------------------------------------
# check_client_limit
# ---------------------------------------------------------------------------


class TestCheckClientLimit:
    def test_professional_tier_unlimited_always_passes(self, make_user, db_session):
        """PROFESSIONAL tier has max_clients=0 (unlimited)."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.PROFESSIONAL, email="professional_client@example.com")
        result = check_client_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_zero_clients_passes(self, make_user, db_session):
        """FREE tier with no clients passes."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.FREE, email="free_cl_0@example.com")
        result = check_client_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_under_limit_passes(self, make_user, make_client, db_session):
        """FREE tier max_clients=3; 2 clients should pass."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.FREE, email="free_cl_2@example.com")
        make_client(user=user, name="Client A")
        make_client(user=user, name="Client B")

        result = check_client_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_at_limit_raises_403(self, make_user, make_client, db_session):
        """FREE tier: 3 clients (at limit) raises 403."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.FREE, email="free_cl_3@example.com")
        for i in range(3):
            make_client(user=user, name=f"Client {i}")

        with pytest.raises(HTTPException) as exc_info:
            check_client_limit(user=user, db=db_session)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TIER_LIMIT_EXCEEDED"
        assert exc_info.value.detail["resource"] == "clients"

    def test_solo_tier_unlimited_clients_passes(self, make_user, make_client, db_session):
        """SOLO tier: max_clients=0 (unlimited); many clients should pass."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.SOLO, email="solo_cl_many@example.com")
        for i in range(10):
            make_client(user=user, name=f"Solo Client {i}")

        result = check_client_limit(user=user, db=db_session)
        assert result is user

    def test_soft_mode_at_limit_does_not_raise(self, make_user, make_client, db_session):
        """Soft enforcement: client limit exceeded is logged, not raised."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.FREE, email="free_cl_soft@example.com")
        for i in range(3):
            make_client(user=user, name=f"Soft Client {i}")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            result = check_client_limit(user=user, db=db_session)

        assert result is user


# ---------------------------------------------------------------------------
# check_tool_access (factory)
# ---------------------------------------------------------------------------


class TestCheckToolAccess:
    def test_professional_tier_can_access_any_tool(self, make_user):
        """PROFESSIONAL tier has empty tools_allowed → all tools permitted."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.PROFESSIONAL)
        dep = check_tool_access("fixed_asset_testing")
        result = dep(user=user)
        assert result is user

    def test_free_tier_can_access_trial_balance(self, make_user):
        """FREE tier can access trial_balance (in _BASIC_TOOLS)."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.FREE)
        dep = check_tool_access("trial_balance")
        result = dep(user=user)
        assert result is user

    def test_free_tier_can_access_flux_analysis(self, make_user):
        """FREE tier can access flux_analysis (in _BASIC_TOOLS)."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.FREE)
        dep = check_tool_access("flux_analysis")
        result = dep(user=user)
        assert result is user

    def test_free_tier_blocked_from_fixed_asset_testing(self, make_user):
        """FREE tier cannot access fixed_asset_testing — raises 403."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.FREE)
        dep = check_tool_access("fixed_asset_testing")

        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TIER_LIMIT_EXCEEDED"
        assert exc_info.value.detail["resource"] == "tool_access"

    def test_free_tier_blocked_from_journal_entry_testing(self, make_user):
        """FREE tier cannot access journal_entry_testing (in _SOLO_TOOLS but not _BASIC_TOOLS)."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.FREE)
        dep = check_tool_access("journal_entry_testing")

        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)

        assert exc_info.value.status_code == 403

    def test_solo_tier_can_access_journal_entry_testing(self, make_user):
        """SOLO tier can access journal_entry_testing (in _SOLO_TOOLS)."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_tool_access("journal_entry_testing")
        result = dep(user=user)
        assert result is user

    def test_solo_tier_can_access_inventory_testing(self, make_user):
        """SOLO tier has all tools (empty tools_allowed) — inventory_testing passes."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_tool_access("inventory_testing")
        result = dep(user=user)
        assert result is user

    def test_soft_mode_blocked_tool_does_not_raise(self, make_user):
        """Soft enforcement: blocked tool access is logged but not raised."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.FREE)
        dep = check_tool_access("fixed_asset_testing")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            result = dep(user=user)

        assert result is user


# ---------------------------------------------------------------------------
# check_format_access (factory)
# ---------------------------------------------------------------------------


class TestCheckFormatAccess:
    def test_professional_tier_can_access_any_format(self, make_user):
        """PROFESSIONAL tier has empty formats_allowed → all formats permitted."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.PROFESSIONAL)
        dep = check_format_access("ods")
        result = dep(user=user)
        assert result is user

    def test_free_tier_can_access_csv(self, make_user):
        """FREE tier can access csv (in _BASIC_FORMATS)."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.FREE)
        dep = check_format_access("csv")
        result = dep(user=user)
        assert result is user

    def test_free_tier_can_access_xlsx(self, make_user):
        """FREE tier can access xlsx (in _BASIC_FORMATS)."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.FREE)
        dep = check_format_access("xlsx")
        result = dep(user=user)
        assert result is user

    def test_free_tier_blocked_from_ods(self, make_user):
        """FREE tier cannot access ods — raises 403."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.FREE)
        dep = check_format_access("ods")

        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TIER_LIMIT_EXCEEDED"
        assert exc_info.value.detail["resource"] == "format_access"

    def test_solo_tier_can_access_pdf(self, make_user):
        """SOLO tier can access pdf (in _SOLO_FORMATS)."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_format_access("pdf")
        result = dep(user=user)
        assert result is user

    def test_solo_tier_can_access_iif(self, make_user):
        """SOLO tier can access iif (in _SOLO_FORMATS)."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_format_access("iif")
        result = dep(user=user)
        assert result is user

    def test_solo_tier_can_access_ods(self, make_user):
        """SOLO tier has all formats (empty formats_allowed) — ods passes."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_format_access("ods")
        result = dep(user=user)
        assert result is user

    def test_soft_mode_blocked_format_does_not_raise(self, make_user):
        """Soft enforcement: blocked format access is logged but not raised."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.FREE)
        dep = check_format_access("ods")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            result = dep(user=user)

        assert result is user


# ---------------------------------------------------------------------------
# check_workspace_access
# ---------------------------------------------------------------------------


class TestCheckWorkspaceAccess:
    def test_professional_tier_has_workspace(self, make_user):
        """PROFESSIONAL tier has workspace=True — passes."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.PROFESSIONAL)
        result = check_workspace_access(user=user)
        assert result is user

    def test_free_tier_blocked_from_workspace(self, make_user):
        """FREE tier has workspace=False — raises 403."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.FREE)

        with pytest.raises(HTTPException) as exc_info:
            check_workspace_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TIER_LIMIT_EXCEEDED"
        assert exc_info.value.detail["resource"] == "workspace"

    def test_solo_tier_has_workspace(self, make_user):
        """SOLO tier has workspace=True — passes."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.SOLO)
        result = check_workspace_access(user=user)
        assert result is user

    def test_soft_mode_workspace_block_does_not_raise(self, make_user):
        """Soft enforcement: workspace access denied is logged but not raised."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.FREE)

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            result = check_workspace_access(user=user)

        assert result is user


# ---------------------------------------------------------------------------
# check_seat_limit
# ---------------------------------------------------------------------------


class TestCheckSeatLimit:
    def test_solo_tier_skipped(self, make_user, db_session):
        """SOLO tier has seats_included=1 — seat check is skipped entirely."""
        from shared.entitlement_checks import check_seat_limit

        user = make_user(tier=UserTier.SOLO, email="seat_solo@example.com")
        result = check_seat_limit(user=user, db=db_session)
        assert result is user

    def test_free_tier_skipped(self, make_user, db_session):
        """FREE tier has seats_included=1 — seat check is skipped."""
        from shared.entitlement_checks import check_seat_limit

        user = make_user(tier=UserTier.FREE, email="seat_free@example.com")
        result = check_seat_limit(user=user, db=db_session)
        assert result is user

    def test_professional_no_subscription_skipped(self, make_user, db_session):
        """TEAM with no Subscription row — check skipped (no sub = nothing to validate)."""
        from shared.entitlement_checks import check_seat_limit

        user = make_user(tier=UserTier.PROFESSIONAL, email="seat_professional_nosub@example.com")
        result = check_seat_limit(user=user, db=db_session)
        assert result is user

    def test_professional_valid_subscription_passes(self, make_user, db_session):
        """TEAM with valid subscription (additional_seats=0) — passes."""
        from shared.entitlement_checks import check_seat_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.PROFESSIONAL, email="seat_professional_valid@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=4,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        result = check_seat_limit(user=user, db=db_session)
        assert result is user

    def test_professional_negative_additional_seats_soft_mode_does_not_raise(self, make_user, db_session):
        """Professional with negative additional_seats in soft mode — logs warning, no raise."""
        from shared.entitlement_checks import check_seat_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.PROFESSIONAL, email="seat_prof_neg_soft@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=4,
            additional_seats=-1,
        )
        db_session.add(sub)
        db_session.flush()

        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="soft"):
            result = check_seat_limit(user=user, db=db_session)

        assert result is user

    def test_professional_no_org_skips_seat_check(self, make_user, db_session):
        """Professional without organization_id — seat check is skipped."""
        from shared.entitlement_checks import check_seat_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.PROFESSIONAL, email="seat_prof_noorg@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=4,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        # User has no organization_id, so seat check is skipped
        result = check_seat_limit(user=user, db=db_session)
        assert result is user


# ---------------------------------------------------------------------------
# _raise_or_log (direct tests)
# ---------------------------------------------------------------------------


class TestRaiseOrLog:
    """Direct tests for the _raise_or_log helper."""

    def test_hard_mode_raises_403(self, make_user):
        """Hard enforcement mode raises HTTPException 403."""
        from shared.entitlement_checks import _raise_or_log

        user = make_user(tier=UserTier.FREE, email="raise_hard@example.com")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                _raise_or_log(user, "test_resource", "Test limit exceeded")

            assert exc_info.value.status_code == 403
            detail = exc_info.value.detail
            assert detail["code"] == "TIER_LIMIT_EXCEEDED"
            assert detail["message"] == "Test limit exceeded"
            assert detail["resource"] == "test_resource"
            assert detail["current_tier"] == "free"
            assert detail["upgrade_url"] == "/pricing"

    def test_soft_mode_logs_but_does_not_raise(self, make_user):
        """Soft enforcement mode logs a warning but does not raise."""
        from shared.entitlement_checks import _raise_or_log

        user = make_user(tier=UserTier.FREE, email="raise_soft@example.com")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            # Should not raise
            result = _raise_or_log(user, "test_resource", "Test limit exceeded")
            assert result is None  # Returns None in soft mode

    def test_hard_mode_includes_correct_tier(self, make_user):
        """HTTPException detail includes the user's actual tier."""
        from shared.entitlement_checks import _raise_or_log

        user = make_user(tier=UserTier.SOLO, email="raise_tier@example.com")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                _raise_or_log(user, "uploads", "Monthly upload limit reached")

            assert exc_info.value.detail["current_tier"] == "solo"


# ---------------------------------------------------------------------------
# check_upload_limit — subscription-based counting path
# ---------------------------------------------------------------------------


class TestCheckUploadLimitSubscriptionPath:
    """Test the subscription-based upload counting path (Subscription.uploads_used_current_period)."""

    def test_subscription_path_under_limit_passes(self, make_user, db_session):
        """SOLO tier with subscription counter under limit passes."""
        from shared.entitlement_checks import check_upload_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.SOLO, email="sub_upload_ok@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            uploads_used_current_period=50,
        )
        db_session.add(sub)
        db_session.flush()

        result = check_upload_limit(user=user, db=db_session)
        assert result is user

    def test_subscription_path_at_limit_raises_403(self, make_user, db_session):
        """SOLO tier with subscription counter at limit raises 403."""
        from shared.entitlement_checks import check_upload_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.SOLO, email="sub_upload_limit@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            uploads_used_current_period=100,  # SOLO limit is 100
        )
        db_session.add(sub)
        db_session.flush()

        with pytest.raises(HTTPException) as exc_info:
            check_upload_limit(user=user, db=db_session)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "uploads"

    def test_enterprise_tier_unlimited_always_passes(self, make_user, db_session):
        """ENTERPRISE tier has uploads_per_month=0 (unlimited)."""
        from shared.entitlement_checks import check_upload_limit

        user = make_user(tier=UserTier.ENTERPRISE, email="ent_upload@example.com")
        result = check_upload_limit(user=user, db=db_session)
        assert result is user


# ---------------------------------------------------------------------------
# increment_upload_count
# ---------------------------------------------------------------------------


class TestIncrementUploadCount:
    def test_increments_subscription_counter(self, make_user, db_session):
        """Increments uploads_used_current_period on subscription."""
        from shared.entitlement_checks import increment_upload_count
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.SOLO, email="incr_upload@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            uploads_used_current_period=5,
        )
        db_session.add(sub)
        db_session.flush()

        increment_upload_count(db_session, user.id)

        db_session.refresh(sub)
        assert sub.uploads_used_current_period == 6

    def test_no_op_without_subscription(self, make_user, db_session):
        """No subscription = no-op (free tier uses ActivityLog counting)."""
        from shared.entitlement_checks import increment_upload_count

        user = make_user(tier=UserTier.FREE, email="incr_free@example.com")
        # Should not raise
        increment_upload_count(db_session, user.id)

    def test_handles_none_initial_value(self, make_user, db_session):
        """If uploads_used_current_period is None, starts from 0."""
        from shared.entitlement_checks import increment_upload_count
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.SOLO, email="incr_none@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            uploads_used_current_period=None,
        )
        db_session.add(sub)
        db_session.flush()

        increment_upload_count(db_session, user.id)

        db_session.refresh(sub)
        assert sub.uploads_used_current_period == 1


# ---------------------------------------------------------------------------
# check_export_access
# ---------------------------------------------------------------------------


class TestCheckExportAccess:
    def test_solo_tier_has_export(self, make_user):
        """SOLO tier has pdf_export, excel_export, csv_export — passes."""
        from shared.entitlement_checks import check_export_access

        user = make_user(tier=UserTier.SOLO, email="export_solo@example.com")
        result = check_export_access(user=user)
        assert result is user

    def test_free_tier_blocked_from_export(self, make_user):
        """FREE tier has no export — raises 403."""
        from shared.entitlement_checks import check_export_access

        user = make_user(tier=UserTier.FREE, email="export_free@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_export_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "export"

    def test_professional_tier_has_export(self, make_user):
        """PROFESSIONAL tier has all exports — passes."""
        from shared.entitlement_checks import check_export_access

        user = make_user(tier=UserTier.PROFESSIONAL, email="export_prof@example.com")
        result = check_export_access(user=user)
        assert result is user

    def test_soft_mode_export_block_does_not_raise(self, make_user):
        """Soft enforcement: export access denied is logged, not raised."""
        from shared.entitlement_checks import check_export_access

        user = make_user(tier=UserTier.FREE, email="export_soft@example.com")

        with patch("shared.entitlement_checks._get_enforcement_mode", return_value="soft"):
            result = check_export_access(user=user)

        assert result is user


# ---------------------------------------------------------------------------
# check_export_sharing_access
# ---------------------------------------------------------------------------


class TestCheckExportSharingAccess:
    def test_professional_tier_has_export_sharing(self, make_user):
        """PROFESSIONAL tier has export_sharing=True — passes."""
        from shared.entitlement_checks import check_export_sharing_access

        user = make_user(tier=UserTier.PROFESSIONAL, email="sharing_prof@example.com")
        result = check_export_sharing_access(user=user)
        assert result is user

    def test_solo_tier_blocked(self, make_user):
        """SOLO tier has export_sharing=False — raises 403."""
        from shared.entitlement_checks import check_export_sharing_access

        user = make_user(tier=UserTier.SOLO, email="sharing_solo@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_export_sharing_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "export_sharing"

    def test_free_tier_blocked(self, make_user):
        """FREE tier has export_sharing=False — raises 403."""
        from shared.entitlement_checks import check_export_sharing_access

        user = make_user(tier=UserTier.FREE, email="sharing_free@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_export_sharing_access(user=user)

        assert exc_info.value.status_code == 403

    def test_enterprise_tier_has_export_sharing(self, make_user):
        """ENTERPRISE tier has export_sharing=True — passes."""
        from shared.entitlement_checks import check_export_sharing_access

        user = make_user(tier=UserTier.ENTERPRISE, email="sharing_ent@example.com")
        result = check_export_sharing_access(user=user)
        assert result is user


# ---------------------------------------------------------------------------
# check_admin_dashboard_access
# ---------------------------------------------------------------------------


class TestCheckAdminDashboardAccess:
    def test_professional_tier_has_admin_dashboard(self, make_user):
        """PROFESSIONAL tier has admin_dashboard=True — passes."""
        from shared.entitlement_checks import check_admin_dashboard_access

        user = make_user(tier=UserTier.PROFESSIONAL, email="admin_prof@example.com")
        result = check_admin_dashboard_access(user=user)
        assert result is user

    def test_solo_tier_blocked(self, make_user):
        """SOLO tier has admin_dashboard=False — raises 403."""
        from shared.entitlement_checks import check_admin_dashboard_access

        user = make_user(tier=UserTier.SOLO, email="admin_solo@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_admin_dashboard_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "admin_dashboard"

    def test_free_tier_blocked(self, make_user):
        """FREE tier has admin_dashboard=False — raises 403."""
        from shared.entitlement_checks import check_admin_dashboard_access

        user = make_user(tier=UserTier.FREE, email="admin_free@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_admin_dashboard_access(user=user)

        assert exc_info.value.status_code == 403

    def test_enterprise_tier_has_admin_dashboard(self, make_user):
        """ENTERPRISE tier has admin_dashboard=True — passes."""
        from shared.entitlement_checks import check_admin_dashboard_access

        user = make_user(tier=UserTier.ENTERPRISE, email="admin_ent@example.com")
        result = check_admin_dashboard_access(user=user)
        assert result is user


# ---------------------------------------------------------------------------
# check_activity_log_access
# ---------------------------------------------------------------------------


class TestCheckActivityLogAccess:
    def test_professional_tier_has_activity_logs(self, make_user):
        """PROFESSIONAL tier has activity_logs=True — passes."""
        from shared.entitlement_checks import check_activity_log_access

        user = make_user(tier=UserTier.PROFESSIONAL, email="actlog_prof@example.com")
        result = check_activity_log_access(user=user)
        assert result is user

    def test_solo_tier_blocked(self, make_user):
        """SOLO tier has activity_logs=False — raises 403."""
        from shared.entitlement_checks import check_activity_log_access

        user = make_user(tier=UserTier.SOLO, email="actlog_solo@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_activity_log_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "activity_logs"

    def test_free_tier_blocked(self, make_user):
        """FREE tier has activity_logs=False — raises 403."""
        from shared.entitlement_checks import check_activity_log_access

        user = make_user(tier=UserTier.FREE, email="actlog_free@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_activity_log_access(user=user)

        assert exc_info.value.status_code == 403

    def test_enterprise_tier_has_activity_logs(self, make_user):
        """ENTERPRISE tier has activity_logs=True — passes."""
        from shared.entitlement_checks import check_activity_log_access

        user = make_user(tier=UserTier.ENTERPRISE, email="actlog_ent@example.com")
        result = check_activity_log_access(user=user)
        assert result is user


# ---------------------------------------------------------------------------
# check_bulk_upload_access
# ---------------------------------------------------------------------------


class TestCheckBulkUploadAccess:
    def test_enterprise_tier_has_bulk_upload(self, make_user):
        """ENTERPRISE tier has bulk_upload=True — passes."""
        from shared.entitlement_checks import check_bulk_upload_access

        user = make_user(tier=UserTier.ENTERPRISE, email="bulk_ent@example.com")
        result = check_bulk_upload_access(user=user)
        assert result is user

    def test_professional_tier_blocked(self, make_user):
        """PROFESSIONAL tier has bulk_upload=False — raises 403."""
        from shared.entitlement_checks import check_bulk_upload_access

        user = make_user(tier=UserTier.PROFESSIONAL, email="bulk_prof@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_bulk_upload_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "bulk_upload"

    def test_solo_tier_blocked(self, make_user):
        """SOLO tier has bulk_upload=False — raises 403."""
        from shared.entitlement_checks import check_bulk_upload_access

        user = make_user(tier=UserTier.SOLO, email="bulk_solo@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_bulk_upload_access(user=user)

        assert exc_info.value.status_code == 403

    def test_free_tier_blocked(self, make_user):
        """FREE tier has bulk_upload=False — raises 403."""
        from shared.entitlement_checks import check_bulk_upload_access

        user = make_user(tier=UserTier.FREE, email="bulk_free@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_bulk_upload_access(user=user)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# check_custom_branding_access
# ---------------------------------------------------------------------------


class TestCheckCustomBrandingAccess:
    def test_enterprise_tier_has_custom_branding(self, make_user):
        """ENTERPRISE tier has custom_branding=True — passes."""
        from shared.entitlement_checks import check_custom_branding_access

        user = make_user(tier=UserTier.ENTERPRISE, email="brand_ent@example.com")
        result = check_custom_branding_access(user=user)
        assert result is user

    def test_professional_tier_blocked(self, make_user):
        """PROFESSIONAL tier has custom_branding=False — raises 403."""
        from shared.entitlement_checks import check_custom_branding_access

        user = make_user(tier=UserTier.PROFESSIONAL, email="brand_prof@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_custom_branding_access(user=user)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["resource"] == "custom_branding"

    def test_solo_tier_blocked(self, make_user):
        """SOLO tier has custom_branding=False — raises 403."""
        from shared.entitlement_checks import check_custom_branding_access

        user = make_user(tier=UserTier.SOLO, email="brand_solo@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_custom_branding_access(user=user)

        assert exc_info.value.status_code == 403

    def test_free_tier_blocked(self, make_user):
        """FREE tier has custom_branding=False — raises 403."""
        from shared.entitlement_checks import check_custom_branding_access

        user = make_user(tier=UserTier.FREE, email="brand_free@example.com")

        with pytest.raises(HTTPException) as exc_info:
            check_custom_branding_access(user=user)

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# _resolve_org_subscription
# ---------------------------------------------------------------------------


class TestResolveOrgSubscription:
    """Test the _resolve_org_subscription helper function."""

    def test_direct_subscription_via_org(self, make_user, db_session):
        """org.subscription_id set — resolves directly."""
        from organization_model import Organization
        from shared.entitlement_checks import _resolve_org_subscription
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="resolve_direct_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=7,
            additional_seats=3,
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Direct Org",
            slug="direct-org-resolve",
            owner_user_id=owner.id,
            subscription_id=sub.id,
        )
        db_session.add(org)
        db_session.flush()

        resolved_sub, entitlements = _resolve_org_subscription(db_session, org.id)
        assert resolved_sub is not None
        assert resolved_sub.id == sub.id
        assert entitlements.uploads_per_month == 500  # Professional

    def test_fallback_via_owner_subscription(self, make_user, db_session):
        """org.subscription_id is None — falls back to owner's active subscription."""
        from organization_model import Organization
        from shared.entitlement_checks import _resolve_org_subscription
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="resolve_fallback_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=7,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Fallback Org",
            slug="fallback-org-resolve",
            owner_user_id=owner.id,
            subscription_id=None,  # No direct link
        )
        db_session.add(org)
        db_session.flush()

        resolved_sub, entitlements = _resolve_org_subscription(db_session, org.id)
        assert resolved_sub is not None
        assert resolved_sub.id == sub.id
        # Backfill linkage should have been applied
        db_session.refresh(org)
        assert org.subscription_id == sub.id

    def test_no_org_found(self, db_session):
        """Non-existent org_id returns None + FREE entitlements."""
        from shared.entitlement_checks import _resolve_org_subscription

        sub, entitlements = _resolve_org_subscription(db_session, 999999)
        assert sub is None
        assert entitlements.uploads_per_month == 10  # FREE

    def test_no_subscription_at_all(self, make_user, db_session):
        """Org exists but no subscription (direct or owner) returns None + FREE."""
        from organization_model import Organization
        from shared.entitlement_checks import _resolve_org_subscription

        owner = make_user(tier=UserTier.FREE, email="resolve_nosub_owner@example.com")
        org = Organization(
            name="No Sub Org",
            slug="nosub-org-resolve",
            owner_user_id=owner.id,
            subscription_id=None,
        )
        db_session.add(org)
        db_session.flush()

        sub, entitlements = _resolve_org_subscription(db_session, org.id)
        assert sub is None
        assert entitlements.uploads_per_month == 10  # FREE

    def test_fallback_finds_trialing_subscription(self, make_user, db_session):
        """Owner's trialing subscription is found via fallback."""
        from organization_model import Organization
        from shared.entitlement_checks import _resolve_org_subscription
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="resolve_trial_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.TRIALING,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=7,
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Trial Org",
            slug="trial-org-resolve",
            owner_user_id=owner.id,
            subscription_id=None,
        )
        db_session.add(org)
        db_session.flush()

        resolved_sub, entitlements = _resolve_org_subscription(db_session, org.id)
        assert resolved_sub is not None
        assert resolved_sub.status == SubscriptionStatus.TRIALING


# ---------------------------------------------------------------------------
# check_seat_limit_for_org
# ---------------------------------------------------------------------------


class TestCheckSeatLimitForOrg:
    """Test org-level seat enforcement with member + invite counting."""

    def test_under_limit_passes(self, make_user, db_session):
        """Org with members under seat limit passes."""
        from organization_model import Organization, OrganizationMember, OrgRole
        from shared.entitlement_checks import check_seat_limit_for_org
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="seat_org_under_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=7,
            additional_seats=3,  # total_seats = 10
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Seat Under Org",
            slug="seat-under-org",
            owner_user_id=owner.id,
            subscription_id=sub.id,
        )
        db_session.add(org)
        db_session.flush()

        # Add 5 members (under 10 seat limit)
        for i in range(5):
            member_user = make_user(email=f"seat_org_m{i}@example.com")
            db_session.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=member_user.id,
                    role=OrgRole.MEMBER,
                )
            )
        db_session.flush()

        # Should not raise
        check_seat_limit_for_org(db_session, org.id)

    def test_at_limit_raises_403(self, make_user, db_session):
        """Org with members at seat limit raises 403 in hard mode."""
        from organization_model import Organization, OrganizationMember, OrgRole
        from shared.entitlement_checks import check_seat_limit_for_org
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="seat_org_at_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=2,
            additional_seats=0,  # total_seats = 2
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Seat At Org",
            slug="seat-at-org",
            owner_user_id=owner.id,
            subscription_id=sub.id,
        )
        db_session.add(org)
        db_session.flush()

        # Add exactly 2 members (at limit)
        for i in range(2):
            member_user = make_user(email=f"seat_org_at_m{i}@example.com")
            db_session.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=member_user.id,
                    role=OrgRole.MEMBER,
                )
            )
        db_session.flush()

        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                check_seat_limit_for_org(db_session, org.id)

            assert exc_info.value.status_code == 403
            assert exc_info.value.detail["code"] == "TIER_LIMIT_EXCEEDED"
            assert exc_info.value.detail["resource"] == "seats"

    def test_pending_invites_counted(self, make_user, db_session):
        """Pending invites count toward the seat limit."""
        from organization_model import (
            InviteStatus,
            Organization,
            OrganizationInvite,
            OrganizationMember,
            OrgRole,
        )
        from shared.entitlement_checks import check_seat_limit_for_org
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="seat_invite_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=3,
            additional_seats=0,  # total_seats = 3
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Invite Org",
            slug="invite-org-seat",
            owner_user_id=owner.id,
            subscription_id=sub.id,
        )
        db_session.add(org)
        db_session.flush()

        # 2 members
        for i in range(2):
            member_user = make_user(email=f"seat_inv_m{i}@example.com")
            db_session.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=member_user.id,
                    role=OrgRole.MEMBER,
                )
            )
        db_session.flush()

        # 1 pending invite (2 members + 1 invite = 3 = at limit)
        invite = OrganizationInvite(
            organization_id=org.id,
            invite_token_hash="a" * 64,
            invitee_email="pending@example.com",
            role=OrgRole.MEMBER,
            status=InviteStatus.PENDING,
        )
        db_session.add(invite)
        db_session.flush()

        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                check_seat_limit_for_org(db_session, org.id)

            assert exc_info.value.status_code == 403

    def test_exclude_invite_id_subtracts_from_pending(self, make_user, db_session):
        """exclude_invite_id decrements pending count (for invite acceptance)."""
        from organization_model import (
            InviteStatus,
            Organization,
            OrganizationInvite,
            OrganizationMember,
            OrgRole,
        )
        from shared.entitlement_checks import check_seat_limit_for_org
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="seat_exclude_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=3,
            additional_seats=0,  # total_seats = 3
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Exclude Org",
            slug="exclude-org-seat",
            owner_user_id=owner.id,
            subscription_id=sub.id,
        )
        db_session.add(org)
        db_session.flush()

        # 2 members
        for i in range(2):
            member_user = make_user(email=f"seat_excl_m{i}@example.com")
            db_session.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=member_user.id,
                    role=OrgRole.MEMBER,
                )
            )
        db_session.flush()

        # 1 pending invite
        invite = OrganizationInvite(
            organization_id=org.id,
            invite_token_hash="b" * 64,
            invitee_email="pending_excl@example.com",
            role=OrgRole.MEMBER,
            status=InviteStatus.PENDING,
        )
        db_session.add(invite)
        db_session.flush()

        # Without exclude: 2 members + 1 pending = 3 = at limit → should raise in hard mode
        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException):
                check_seat_limit_for_org(db_session, org.id)

            # With exclude_invite_id: 2 members + 0 pending = 2 < 3 → should pass
            check_seat_limit_for_org(db_session, org.id, exclude_invite_id=invite.id)

    def test_no_subscription_enforces_free_tier_cap(self, make_user, db_session):
        """Org without subscription enforces free-tier seat cap (1)."""
        from organization_model import Organization, OrganizationMember, OrgRole
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(tier=UserTier.FREE, email="seat_free_cap_owner@example.com")
        org = Organization(
            name="Free Cap Org",
            slug="free-cap-org-seat",
            owner_user_id=owner.id,
            subscription_id=None,
        )
        db_session.add(org)
        db_session.flush()

        # 1 member (at free-tier cap of 1)
        member_user = make_user(email="seat_free_cap_m@example.com")
        db_session.add(
            OrganizationMember(
                organization_id=org.id,
                user_id=member_user.id,
                role=OrgRole.MEMBER,
            )
        )
        db_session.flush()

        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                check_seat_limit_for_org(db_session, org.id)

            assert exc_info.value.status_code == 403

    def test_soft_mode_at_limit_does_not_raise(self, make_user, db_session):
        """Soft seat enforcement: limit exceeded is logged but not raised."""
        from organization_model import Organization, OrganizationMember, OrgRole
        from shared.entitlement_checks import check_seat_limit_for_org
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        owner = make_user(tier=UserTier.PROFESSIONAL, email="seat_soft_owner@example.com")
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=1,
            additional_seats=0,  # total_seats = 1
        )
        db_session.add(sub)
        db_session.flush()

        org = Organization(
            name="Soft Seat Org",
            slug="soft-seat-org",
            owner_user_id=owner.id,
            subscription_id=sub.id,
        )
        db_session.add(org)
        db_session.flush()

        # 1 member (at limit)
        member_user = make_user(email="seat_soft_m@example.com")
        db_session.add(
            OrganizationMember(
                organization_id=org.id,
                user_id=member_user.id,
                role=OrgRole.MEMBER,
            )
        )
        db_session.flush()

        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="soft"):
            # Should not raise in soft mode
            check_seat_limit_for_org(db_session, org.id)
