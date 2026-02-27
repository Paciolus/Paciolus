"""
Phase LXII: Unit tests for shared/entitlement_checks.py.

Tests all 6 entitlement dependency functions:
- check_diagnostic_limit  — DB-backed monthly ActivityLog count
- check_client_limit      — DB-backed active Client count
- check_tool_access       — factory: tier-based tool access gate
- check_format_access     — factory: tier-based format access gate
- check_workspace_access  — tier gate (TEAM+ only)
- check_seat_limit        — subscription-backed seat validation

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
    def test_team_tier_unlimited_always_passes(self, make_user, db_session):
        """TEAM tier has diagnostics_per_month=0 (unlimited)."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.TEAM, email="team_diag@example.com")
        result = check_diagnostic_limit(user=user, db=db_session)
        assert result is user

    def test_enterprise_tier_unlimited_always_passes(self, make_user, db_session):
        """ENTERPRISE tier is also unlimited."""
        from shared.entitlement_checks import check_diagnostic_limit

        user = make_user(tier=UserTier.ENTERPRISE, email="ent_diag@example.com")
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
        assert detail["resource"] == "diagnostics"
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
    def test_team_tier_unlimited_always_passes(self, make_user, db_session):
        """TEAM tier has max_clients=0 (unlimited)."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.TEAM, email="team_client@example.com")
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

    def test_solo_tier_at_nine_clients_passes(self, make_user, make_client, db_session):
        """SOLO tier: max_clients=10; 9 clients should pass."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.SOLO, email="solo_cl_9@example.com")
        for i in range(9):
            make_client(user=user, name=f"Solo Client {i}")

        result = check_client_limit(user=user, db=db_session)
        assert result is user

    def test_solo_tier_at_limit_raises_403(self, make_user, make_client, db_session):
        """SOLO tier: 10 clients (at limit) raises 403."""
        from shared.entitlement_checks import check_client_limit

        user = make_user(tier=UserTier.SOLO, email="solo_cl_10@example.com")
        for i in range(10):
            make_client(user=user, name=f"Solo Client {i}")

        with pytest.raises(HTTPException) as exc_info:
            check_client_limit(user=user, db=db_session)

        assert exc_info.value.status_code == 403

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
    def test_team_tier_can_access_any_tool(self, make_user):
        """TEAM tier has empty tools_allowed → all tools permitted."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.TEAM)
        dep = check_tool_access("fixed_asset_testing")
        result = dep(user=user)
        assert result is user

    def test_enterprise_tier_can_access_any_tool(self, make_user):
        """ENTERPRISE tier has empty tools_allowed → all tools permitted."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.ENTERPRISE)
        dep = check_tool_access("inventory_testing")
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

    def test_solo_tier_blocked_from_inventory_testing(self, make_user):
        """SOLO tier cannot access inventory_testing (requires TEAM+)."""
        from shared.entitlement_checks import check_tool_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_tool_access("inventory_testing")

        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)

        assert exc_info.value.status_code == 403

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
    def test_team_tier_can_access_any_format(self, make_user):
        """TEAM tier has empty formats_allowed → all formats permitted."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.TEAM)
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

    def test_solo_tier_blocked_from_ods(self, make_user):
        """SOLO tier cannot access ods (not in _SOLO_FORMATS)."""
        from shared.entitlement_checks import check_format_access

        user = make_user(tier=UserTier.SOLO)
        dep = check_format_access("ods")

        with pytest.raises(HTTPException) as exc_info:
            dep(user=user)

        assert exc_info.value.status_code == 403

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
    def test_team_tier_has_workspace(self, make_user):
        """TEAM tier has workspace=True — passes."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.TEAM)
        result = check_workspace_access(user=user)
        assert result is user

    def test_enterprise_tier_has_workspace(self, make_user):
        """ENTERPRISE tier has workspace=True — passes."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.ENTERPRISE)
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

    def test_solo_tier_blocked_from_workspace(self, make_user):
        """SOLO tier has workspace=False — raises 403."""
        from shared.entitlement_checks import check_workspace_access

        user = make_user(tier=UserTier.SOLO)

        with pytest.raises(HTTPException) as exc_info:
            check_workspace_access(user=user)

        assert exc_info.value.status_code == 403

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

    def test_team_no_subscription_skipped(self, make_user, db_session):
        """TEAM with no Subscription row — check skipped (no sub = nothing to validate)."""
        from shared.entitlement_checks import check_seat_limit

        user = make_user(tier=UserTier.TEAM, email="seat_team_nosub@example.com")
        result = check_seat_limit(user=user, db=db_session)
        assert result is user

    def test_team_valid_subscription_passes(self, make_user, db_session):
        """TEAM with valid subscription (additional_seats=0) — passes."""
        from shared.entitlement_checks import check_seat_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.TEAM, email="seat_team_valid@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="team",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=4,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        result = check_seat_limit(user=user, db=db_session)
        assert result is user

    def test_team_negative_additional_seats_soft_mode_does_not_raise(self, make_user, db_session):
        """Team with negative additional_seats in soft mode — logs warning, no raise."""
        from shared.entitlement_checks import check_seat_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.TEAM, email="seat_neg_soft@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="team",
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

    def test_team_negative_additional_seats_hard_mode_raises_403(self, make_user, db_session):
        """Team with negative additional_seats in hard mode — raises 403."""
        from shared.entitlement_checks import check_seat_limit
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user = make_user(tier=UserTier.TEAM, email="seat_neg_hard@example.com")
        sub = Subscription(
            user_id=user.id,
            tier="team",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            seat_count=4,
            additional_seats=-1,
        )
        db_session.add(sub)
        db_session.flush()

        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            with pytest.raises(HTTPException) as exc_info:
                check_seat_limit(user=user, db=db_session)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "TIER_LIMIT_EXCEEDED"
        assert exc_info.value.detail["resource"] == "seats"
