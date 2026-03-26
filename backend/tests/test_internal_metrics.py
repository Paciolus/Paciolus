"""
Tests for Internal Metrics API — Sprint 589: Founder Ops dashboard.

Tests cover:
- Revenue metrics: MRR/ARR calculation, by-plan breakdown, 30-day movements
- Churn metrics: logo churn, revenue churn, involuntary churn
- Trial funnel: signups, conversions, median conversion time
- Revenue history: daily/weekly/monthly granularity
- Authorization: owner-only access (403 for non-owners, 401 for unauthenticated)
- Edge cases: empty state, annual plans, mixed intervals
"""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_verified_user
from database import get_db
from main import app
from models import ActivityLog, User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from subscription_model import (
    BillingEvent,
    BillingEventType,
    BillingInterval,
    Subscription,
    SubscriptionStatus,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def owner_user(db_session):
    """Create an org owner with Professional subscription."""
    user = User(
        email="metrics_owner@example.com",
        name="Metrics Owner",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    sub = Subscription(
        user_id=user.id,
        tier="professional",
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        seat_count=7,
        additional_seats=0,
    )
    db_session.add(sub)
    db_session.flush()

    org = Organization(
        name="Metrics Firm",
        slug="metrics-firm",
        owner_user_id=user.id,
        subscription_id=sub.id,
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db_session.add(member)
    db_session.flush()

    user.organization_id = org.id
    db_session.flush()

    return user


@pytest.fixture
def member_user(db_session, owner_user):
    """Create a regular MEMBER in the same org."""
    user = User(
        email="metrics_member@example.com",
        name="Metrics Member",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    member = OrganizationMember(
        organization_id=owner_user.organization_id,
        user_id=user.id,
        role=OrgRole.MEMBER,
    )
    db_session.add(member)
    db_session.flush()

    user.organization_id = owner_user.organization_id
    db_session.flush()

    return user


@pytest.fixture
def solo_owner(db_session):
    """Create a solo user with active subscription (no org)."""
    user = User(
        email="metrics_solo@example.com",
        name="Solo Owner",
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
        seat_count=1,
        additional_seats=0,
    )
    db_session.add(sub)
    db_session.flush()

    return user


@pytest.fixture
def free_user(db_session):
    """Create a free user with no subscription."""
    user = User(
        email="metrics_free@example.com",
        name="Free User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.FREE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_owner(db_session, owner_user):
    """Override auth for org owner."""
    app.dependency_overrides[require_verified_user] = lambda: owner_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield owner_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_member(db_session, member_user):
    """Override auth for org member."""
    app.dependency_overrides[require_verified_user] = lambda: member_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield member_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_solo(db_session, solo_owner):
    """Override auth for solo owner."""
    app.dependency_overrides[require_verified_user] = lambda: solo_owner
    app.dependency_overrides[get_db] = lambda: db_session
    yield solo_owner
    app.dependency_overrides.clear()


@pytest.fixture
def override_free(db_session, free_user):
    """Override auth for free user."""
    app.dependency_overrides[require_verified_user] = lambda: free_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield free_user
    app.dependency_overrides.clear()


def _create_subscription(db, user_id, tier, status, interval, additional_seats=0):
    """Helper to create a subscription."""
    sub = Subscription(
        user_id=user_id,
        tier=tier,
        status=status,
        billing_interval=interval,
        seat_count=1 if tier == "solo" else 7 if tier == "professional" else 20,
        additional_seats=additional_seats,
    )
    db.add(sub)
    db.flush()
    return sub


def _create_billing_event(db, event_type, user_id=None, tier=None, interval=None, metadata=None, days_ago=0):
    """Helper to create a billing event at a specific time offset."""
    created = datetime.now(UTC) - timedelta(days=days_ago)
    event = BillingEvent(
        user_id=user_id,
        event_type=event_type,
        tier=tier,
        interval=interval,
        metadata_json=json.dumps(metadata) if metadata else None,
        created_at=created,
    )
    db.add(event)
    db.flush()
    return event


# =============================================================================
# Route Registration
# =============================================================================


class TestInternalMetricsRouteRegistration:
    """Verify internal metrics routes are registered."""

    def test_revenue_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/internal/metrics/revenue" in paths

    def test_churn_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/internal/metrics/churn" in paths

    def test_trial_funnel_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/internal/metrics/trial-funnel" in paths

    def test_revenue_history_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/internal/metrics/revenue/history" in paths


# =============================================================================
# Authorization Tests
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAuthorization:
    """Test access control for all internal metrics endpoints."""

    ENDPOINTS = [
        "/internal/metrics/revenue",
        "/internal/metrics/churn",
        "/internal/metrics/trial-funnel",
        "/internal/metrics/revenue/history",
    ]

    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self):
        """Unauthenticated requests get 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for endpoint in self.ENDPOINTS:
                response = await client.get(endpoint)
                assert response.status_code == 401, f"Expected 401 for {endpoint}"

    @pytest.mark.asyncio
    async def test_owner_access_allowed(self, override_owner):
        """Org owner gets 200."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for endpoint in self.ENDPOINTS:
                response = await client.get(endpoint)
                assert response.status_code == 200, f"Expected 200 for {endpoint}, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_member_access_denied(self, override_member):
        """Non-owner org member gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for endpoint in self.ENDPOINTS:
                response = await client.get(endpoint)
                assert response.status_code == 403, f"Expected 403 for {endpoint}"

    @pytest.mark.asyncio
    async def test_solo_owner_allowed(self, override_solo):
        """Solo subscriber with active subscription gets 200."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for endpoint in self.ENDPOINTS:
                response = await client.get(endpoint)
                assert response.status_code == 200, f"Expected 200 for {endpoint}"

    @pytest.mark.asyncio
    async def test_free_user_denied(self, override_free):
        """Free user with no subscription gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for endpoint in self.ENDPOINTS:
                response = await client.get(endpoint)
                assert response.status_code == 403, f"Expected 403 for {endpoint}"


# =============================================================================
# Revenue Metrics — Unit Tests
# =============================================================================


class TestRevenueMetricsComputation:
    """Unit tests for MRR/ARR calculation logic."""

    def test_empty_state_returns_zeroes(self, db_session):
        """No subscriptions returns zeroed metrics."""
        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["total"] == 0.0
        assert result["arr"] == 0.0
        assert result["subscribers"]["total_active"] == 0
        assert result["subscribers"]["trialing"] == 0
        assert result["subscribers"]["past_due"] == 0

    def test_single_solo_monthly(self, db_session):
        """One Solo monthly → $100 MRR."""
        user = User(
            email="rev_solo@test.com", hashed_password="x", tier=UserTier.SOLO, is_active=True, is_verified=True
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(db_session, user.id, "solo", SubscriptionStatus.ACTIVE, BillingInterval.MONTHLY)

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["total"] == 100.0
        assert result["arr"] == 1200.0
        assert result["mrr"]["by_plan"]["solo"]["count"] == 1
        assert result["mrr"]["by_plan"]["solo"]["mrr"] == 100.0
        assert result["subscribers"]["total_active"] == 1

    def test_annual_plan_normalized_to_monthly(self, db_session):
        """Enterprise annual ($10,000/yr) → $833.33/mo MRR."""
        user = User(
            email="rev_ent@test.com", hashed_password="x", tier=UserTier.ENTERPRISE, is_active=True, is_verified=True
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(db_session, user.id, "enterprise", SubscriptionStatus.ACTIVE, BillingInterval.ANNUAL)

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        # $1,000,000 cents / 12 / 100 = $833.33
        assert result["mrr"]["total"] == pytest.approx(833.33, abs=0.01)
        assert result["arr"] == pytest.approx(10000.0, abs=0.15)

    def test_multiple_plans_aggregated(self, db_session):
        """Multiple plans summed correctly."""
        for i, (tier, ut) in enumerate(
            [("solo", UserTier.SOLO), ("professional", UserTier.PROFESSIONAL), ("enterprise", UserTier.ENTERPRISE)]
        ):
            user = User(
                email=f"rev_multi_{i}@test.com",
                hashed_password="x",
                tier=ut,
                is_active=True,
                is_verified=True,
            )
            db_session.add(user)
            db_session.flush()
            _create_subscription(db_session, user.id, tier, SubscriptionStatus.ACTIVE, BillingInterval.MONTHLY)

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        # Solo $100 + Pro $500 + Enterprise $1000 = $1600
        assert result["mrr"]["total"] == 1600.0
        assert result["subscribers"]["total_active"] == 3
        assert len(result["mrr"]["by_plan"]) == 3

    def test_trialing_counts_in_mrr(self, db_session):
        """Trialing subscriptions count toward MRR and trialing count."""
        user = User(
            email="rev_trial@test.com", hashed_password="x", tier=UserTier.SOLO, is_active=True, is_verified=True
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(db_session, user.id, "solo", SubscriptionStatus.TRIALING, BillingInterval.MONTHLY)

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["total"] == 100.0
        assert result["subscribers"]["trialing"] == 1
        assert result["subscribers"]["total_active"] == 1

    def test_canceled_excluded_from_mrr(self, db_session):
        """Canceled subscriptions do not contribute to MRR."""
        user = User(
            email="rev_cancel@test.com", hashed_password="x", tier=UserTier.SOLO, is_active=True, is_verified=True
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(db_session, user.id, "solo", SubscriptionStatus.CANCELED, BillingInterval.MONTHLY)

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["total"] == 0.0
        assert result["subscribers"]["total_active"] == 0

    def test_past_due_counted_separately(self, db_session):
        """Past-due subscriptions counted in past_due, not in active MRR."""
        user = User(
            email="rev_pastdue@test.com", hashed_password="x", tier=UserTier.SOLO, is_active=True, is_verified=True
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(db_session, user.id, "solo", SubscriptionStatus.PAST_DUE, BillingInterval.MONTHLY)

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["total"] == 0.0
        assert result["subscribers"]["past_due"] == 1
        assert result["subscribers"]["total_active"] == 0

    def test_seat_addon_revenue(self, db_session):
        """Professional with 3 additional seats → base + seat revenue."""
        user = User(
            email="rev_seats@test.com",
            hashed_password="x",
            tier=UserTier.PROFESSIONAL,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(
            db_session, user.id, "professional", SubscriptionStatus.ACTIVE, BillingInterval.MONTHLY, additional_seats=3
        )

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        # $500 base + 3 × $65 seat = $500 + $195 = $695
        assert result["mrr"]["total"] == 695.0

    def test_net_new_mrr_from_events(self, db_session):
        """Net new MRR computed from subscription_created events."""
        _create_billing_event(
            db_session, BillingEventType.SUBSCRIPTION_CREATED, tier="solo", interval="monthly", days_ago=5
        )
        _create_billing_event(
            db_session, BillingEventType.TRIAL_CONVERTED, tier="professional", interval="monthly", days_ago=10
        )

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        # Solo $100 + Pro $500 = $600
        assert result["mrr"]["net_new_mrr_30d"] == 600.0

    def test_expansion_mrr_from_upgrades(self, db_session):
        """Expansion MRR from upgrade events."""
        _create_billing_event(
            db_session,
            BillingEventType.SUBSCRIPTION_UPGRADED,
            tier="professional",
            interval="monthly",
            metadata={"old_tier": "solo"},
            days_ago=5,
        )

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        # Pro $500 - Solo $100 = $400 expansion
        assert result["mrr"]["expansion_mrr_30d"] == 400.0

    def test_churned_mrr_from_cancellations(self, db_session):
        """Churned MRR from cancellation events."""
        _create_billing_event(
            db_session, BillingEventType.SUBSCRIPTION_CANCELED, tier="solo", interval="monthly", days_ago=3
        )

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["churned_mrr_30d"] == -100.0

    def test_contraction_mrr_from_downgrades(self, db_session):
        """Contraction MRR from downgrade events."""
        _create_billing_event(
            db_session,
            BillingEventType.SUBSCRIPTION_DOWNGRADED,
            tier="solo",
            interval="monthly",
            metadata={"old_tier": "professional"},
            days_ago=5,
        )

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        # Solo $100 - Pro $500 = -$400 contraction
        assert result["mrr"]["contraction_mrr_30d"] == -400.0

    def test_events_outside_30d_excluded(self, db_session):
        """Events older than 30 days are not counted in 30-day movements."""
        _create_billing_event(
            db_session, BillingEventType.SUBSCRIPTION_CREATED, tier="solo", interval="monthly", days_ago=45
        )

        from billing.internal_metrics import compute_revenue_metrics

        result = compute_revenue_metrics(db_session)

        assert result["mrr"]["net_new_mrr_30d"] == 0.0


# =============================================================================
# Churn Metrics — Unit Tests
# =============================================================================


class TestChurnMetricsComputation:
    """Unit tests for churn rate calculations."""

    def test_empty_state_returns_zeroes(self, db_session):
        """No subscriptions returns zeroed churn."""
        from billing.internal_metrics import compute_churn_metrics

        result = compute_churn_metrics(db_session)

        assert result["logo_churn"]["rate"] == 0.0
        assert result["logo_churn"]["count"] == 0
        assert result["revenue_churn"]["gross_rate"] == 0.0
        assert result["revenue_churn"]["net_rate"] == 0.0
        assert result["involuntary_churn"]["past_due_count"] == 0
        assert result["involuntary_churn"]["failed_payments_30d"] == 0

    def test_logo_churn_rate(self, db_session):
        """2 cancellations with 10 active → 2/(10+2) starting = 0.1667."""
        for i in range(10):
            user = User(
                email=f"churn_active_{i}@test.com",
                hashed_password="x",
                tier=UserTier.SOLO,
                is_active=True,
                is_verified=True,
            )
            db_session.add(user)
            db_session.flush()
            _create_subscription(db_session, user.id, "solo", SubscriptionStatus.ACTIVE, BillingInterval.MONTHLY)

        # 2 cancellation events
        _create_billing_event(
            db_session, BillingEventType.SUBSCRIPTION_CANCELED, tier="solo", interval="monthly", days_ago=5
        )
        _create_billing_event(
            db_session, BillingEventType.SUBSCRIPTION_CANCELED, tier="solo", interval="monthly", days_ago=10
        )

        from billing.internal_metrics import compute_churn_metrics

        result = compute_churn_metrics(db_session)

        assert result["logo_churn"]["count"] == 2
        assert result["logo_churn"]["starting_count"] == 12  # 10 active + 2 canceled
        assert result["logo_churn"]["rate"] == pytest.approx(2 / 12, abs=0.001)

    def test_involuntary_churn_tracking(self, db_session):
        """Past-due subs and failed payments tracked."""
        user = User(
            email="churn_pastdue@test.com",
            hashed_password="x",
            tier=UserTier.SOLO,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()

        _create_subscription(db_session, user.id, "solo", SubscriptionStatus.PAST_DUE, BillingInterval.MONTHLY)

        _create_billing_event(db_session, BillingEventType.PAYMENT_FAILED, days_ago=2)
        _create_billing_event(db_session, BillingEventType.PAYMENT_FAILED, days_ago=5)

        from billing.internal_metrics import compute_churn_metrics

        result = compute_churn_metrics(db_session)

        assert result["involuntary_churn"]["past_due_count"] == 1
        assert result["involuntary_churn"]["past_due_mrr"] == 100.0
        assert result["involuntary_churn"]["failed_payments_30d"] == 2


# =============================================================================
# Trial Funnel — Unit Tests
# =============================================================================


class TestTrialFunnelComputation:
    """Unit tests for trial funnel metrics."""

    def test_empty_state_returns_zeroes(self, db_session):
        """No activity returns zeroed funnel."""
        from billing.internal_metrics import compute_trial_funnel

        result = compute_trial_funnel(db_session)

        assert result["signups"] == 0
        assert result["trials_started"] == 0
        assert result["first_upload"] == 0
        assert result["first_report_generated"] == 0
        assert result["converted_to_paid"] == 0
        assert result["conversion_rate"] == 0.0
        assert result["median_time_to_conversion_days"] is None

    def test_trial_conversion_rate(self, db_session):
        """10 trials, 4 conversions → 0.4 rate."""
        # Create real users to satisfy FK constraints
        trial_users = []
        for i in range(10):
            u = User(
                email=f"trial_rate_{i}@test.com",
                hashed_password="x",
                tier=UserTier.FREE,
                is_active=True,
                is_verified=True,
            )
            db_session.add(u)
            db_session.flush()
            trial_users.append(u)

        for i in range(10):
            _create_billing_event(
                db_session, BillingEventType.TRIAL_STARTED, user_id=trial_users[i].id, tier="solo", days_ago=20
            )

        for i in range(4):
            _create_billing_event(
                db_session, BillingEventType.TRIAL_CONVERTED, user_id=trial_users[i].id, tier="solo", days_ago=15
            )

        from billing.internal_metrics import compute_trial_funnel

        result = compute_trial_funnel(db_session)

        assert result["trials_started"] == 10
        assert result["converted_to_paid"] == 4
        assert result["conversion_rate"] == 0.4

    def test_median_conversion_time(self, db_session):
        """Median conversion time computed from trial_started → trial_converted pairs."""
        # Create real users for FK constraints
        median_users = []
        for i in range(3):
            u = User(
                email=f"median_conv_{i}@test.com",
                hashed_password="x",
                tier=UserTier.FREE,
                is_active=True,
                is_verified=True,
            )
            db_session.add(u)
            db_session.flush()
            median_users.append(u)

        # User A: trial day 20 ago, convert day 15 ago → 5 days
        _create_billing_event(
            db_session, BillingEventType.TRIAL_STARTED, user_id=median_users[0].id, tier="solo", days_ago=20
        )
        _create_billing_event(
            db_session, BillingEventType.TRIAL_CONVERTED, user_id=median_users[0].id, tier="solo", days_ago=15
        )

        # User B: trial day 10 ago, convert day 7 ago → 3 days
        _create_billing_event(
            db_session, BillingEventType.TRIAL_STARTED, user_id=median_users[1].id, tier="solo", days_ago=10
        )
        _create_billing_event(
            db_session, BillingEventType.TRIAL_CONVERTED, user_id=median_users[1].id, tier="solo", days_ago=7
        )

        # User C: trial day 25 ago, convert day 18 ago → 7 days
        _create_billing_event(
            db_session, BillingEventType.TRIAL_STARTED, user_id=median_users[2].id, tier="solo", days_ago=25
        )
        _create_billing_event(
            db_session, BillingEventType.TRIAL_CONVERTED, user_id=median_users[2].id, tier="solo", days_ago=18
        )

        from billing.internal_metrics import compute_trial_funnel

        result = compute_trial_funnel(db_session)

        # Sorted days: [3, 5, 7] → median = 5
        assert result["median_time_to_conversion_days"] == pytest.approx(5.0, abs=0.2)

    def test_signups_counted(self, db_session):
        """Users created in the period are counted as signups."""
        for i in range(5):
            user = User(
                email=f"funnel_signup_{i}@test.com",
                hashed_password="x",
                tier=UserTier.FREE,
                is_active=True,
                is_verified=True,
                created_at=datetime.now(UTC) - timedelta(days=5),
            )
            db_session.add(user)
        db_session.flush()

        from billing.internal_metrics import compute_trial_funnel

        result = compute_trial_funnel(db_session)

        assert result["signups"] >= 5

    def test_first_upload_tracked(self, db_session):
        """Activity log entries in period counted as first uploads."""
        user = User(
            email="funnel_upload@test.com",
            hashed_password="x",
            tier=UserTier.FREE,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()

        log = ActivityLog(
            user_id=user.id,
            filename_hash="a" * 64,
            record_count=10,
            total_debits=1000,
            total_credits=1000,
            materiality_threshold=50,
            was_balanced=True,
            timestamp=datetime.now(UTC) - timedelta(days=5),
        )
        db_session.add(log)
        db_session.flush()

        from billing.internal_metrics import compute_trial_funnel

        result = compute_trial_funnel(db_session)

        assert result["first_upload"] >= 1


# =============================================================================
# Revenue History — Unit Tests
# =============================================================================


class TestRevenueHistoryComputation:
    """Unit tests for historical revenue snapshots."""

    def test_empty_state_returns_points(self, db_session):
        """Empty DB still returns date points with zero values."""
        from billing.internal_metrics import compute_revenue_history

        result = compute_revenue_history(db_session, granularity="weekly")

        assert len(result) > 0
        for point in result:
            assert point["mrr"] == 0.0
            assert point["arr"] == 0.0
            assert point["active_subscribers"] == 0

    def test_daily_granularity(self, db_session):
        """Daily granularity produces ~90 points for 90-day range."""
        from billing.internal_metrics import compute_revenue_history

        result = compute_revenue_history(db_session, granularity="daily")

        # Should have approximately 91 points (90 days + end date)
        assert len(result) >= 85

    def test_monthly_granularity(self, db_session):
        """Monthly granularity produces ~3-4 points for 90-day range."""
        from billing.internal_metrics import compute_revenue_history

        result = compute_revenue_history(db_session, granularity="monthly")

        assert 2 <= len(result) <= 5

    def test_history_reflects_subscriptions(self, db_session):
        """Snapshot includes subscriptions created before the point date."""
        user = User(
            email="history_sub@test.com",
            hashed_password="x",
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
            seat_count=1,
            additional_seats=0,
            created_at=datetime.now(UTC) - timedelta(days=60),
        )
        db_session.add(sub)
        db_session.flush()

        from billing.internal_metrics import compute_revenue_history

        result = compute_revenue_history(db_session, granularity="monthly")

        # At least some points should have non-zero MRR
        has_nonzero = any(p["mrr"] > 0 for p in result)
        assert has_nonzero


# =============================================================================
# API Integration Tests
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestRevenueEndpoint:
    """Integration tests for GET /internal/metrics/revenue."""

    @pytest.mark.asyncio
    async def test_revenue_response_shape(self, override_owner):
        """Response matches RevenueMetricsResponse schema."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/metrics/revenue")
            assert response.status_code == 200
            data = response.json()

            assert "as_of" in data
            assert "mrr" in data
            assert "arr" in data
            assert "subscribers" in data
            assert "total" in data["mrr"]
            assert "by_plan" in data["mrr"]
            assert "total_active" in data["subscribers"]


@pytest.mark.usefixtures("bypass_csrf")
class TestChurnEndpoint:
    """Integration tests for GET /internal/metrics/churn."""

    @pytest.mark.asyncio
    async def test_churn_response_shape(self, override_owner):
        """Response matches ChurnMetricsResponse schema."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/metrics/churn")
            assert response.status_code == 200
            data = response.json()

            assert data["period"] == "trailing_30d"
            assert "logo_churn" in data
            assert "revenue_churn" in data
            assert "involuntary_churn" in data


@pytest.mark.usefixtures("bypass_csrf")
class TestTrialFunnelEndpoint:
    """Integration tests for GET /internal/metrics/trial-funnel."""

    @pytest.mark.asyncio
    async def test_trial_funnel_response_shape(self, override_owner):
        """Response matches TrialFunnelResponse schema."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/metrics/trial-funnel")
            assert response.status_code == 200
            data = response.json()

            assert data["period"] == "trailing_30d"
            assert "signups" in data
            assert "trials_started" in data
            assert "conversion_rate" in data


@pytest.mark.usefixtures("bypass_csrf")
class TestRevenueHistoryEndpoint:
    """Integration tests for GET /internal/metrics/revenue/history."""

    @pytest.mark.asyncio
    async def test_history_response_shape(self, override_owner):
        """Response is a list of RevenueHistoryPoint objects."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/metrics/revenue/history?granularity=weekly")
            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            assert len(data) > 0
            point = data[0]
            assert "date" in point
            assert "mrr" in point
            assert "arr" in point
            assert "active_subscribers" in point

    @pytest.mark.asyncio
    async def test_history_invalid_granularity(self, override_owner):
        """Invalid granularity returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/metrics/revenue/history?granularity=hourly")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_history_with_date_range(self, override_owner):
        """Custom date range filters results."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/internal/metrics/revenue/history?granularity=daily&start_date=2026-03-01&end_date=2026-03-10"
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 12  # ~10 days + possible end cap

    @pytest.mark.asyncio
    async def test_history_bad_date_format(self, override_owner):
        """Malformed date returns 400."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/metrics/revenue/history?start_date=not-a-date")
            assert response.status_code == 400
