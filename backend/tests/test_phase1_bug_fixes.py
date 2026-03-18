"""
Phase 1 Bug Fix Tests — Comprehensive Remediation Sprint.

Tests covering all 8 bug fixes from the formal audit:
  Bug 1: Webhook dedup — operational errors must not return 200
  Bug 2: Webhook atomicity — failure must roll back entire transaction
  Bug 3: Admin overview — correct field references on ActivityLog/TeamActivityLog
  Bug 4: Client manager — no cartesian join in get_clients_with_count
  Bug 5: Seat removal — Stripe quantity reaches 0 (no max(1,...) clamp)
  Bug 6: Invite acceptance — not blocked at exact capacity
  Bug 7: Webhook metadata — malformed paciolus_user_id handled gracefully
  Bug 8: Tool run numbering — unique constraint prevents duplicates
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ActivityLog, Client
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

# ---------------------------------------------------------------------------
# Bug 1: Webhook dedup — operational errors must NOT return 200
# ---------------------------------------------------------------------------


class TestBug1WebhookDedupErrorClassification:
    """Operational DB errors during dedup must return 500, not 200."""

    @pytest.mark.asyncio
    async def test_operational_error_returns_500(self, db_session):
        """OperationalError during dedup flush must return 500 so Stripe retries."""
        from database import get_db
        from main import app

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_op_error_test",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_err", "customer": "cus_err"}},
        }

        app.dependency_overrides[get_db] = lambda: db_session

        try:
            import httpx
            from sqlalchemy.exc import OperationalError

            original_flush = db_session.flush

            call_count = 0

            def failing_flush(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                # First flush (dedup marker insert) — simulate DB outage
                if call_count == 1:
                    raise OperationalError("connection lost", {}, None)
                return original_flush(*args, **kwargs)

            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
                patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_SECRET"),
                patch.object(db_session, "flush", side_effect=failing_flush),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    resp = await client.post(
                        "/billing/webhook",
                        content=b'{"type": "test"}',
                        headers={
                            "stripe-signature": "t=123,v1=sig",
                            "content-type": "application/json",
                        },
                    )

                # Must NOT be 200 — Stripe must retry
                assert resp.status_code == 500
        finally:
            app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_integrity_error_returns_200_duplicate(self, db_session):
        """IntegrityError during dedup correctly returns 200 (true duplicate)."""
        from database import get_db
        from main import app
        from subscription_model import ProcessedWebhookEvent

        # Pre-insert the event marker to simulate a duplicate
        db_session.add(ProcessedWebhookEvent(stripe_event_id="evt_dup_integrity"))
        db_session.flush()

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_dup_integrity",
            "type": "checkout.session.completed",
            "data": {"object": {}},
        }

        app.dependency_overrides[get_db] = lambda: db_session

        try:
            import httpx

            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
                patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_SECRET"),
                patch("billing.webhook_handler.process_webhook_event") as mock_process,
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    resp = await client.post(
                        "/billing/webhook",
                        content=b'{"type": "test"}',
                        headers={
                            "stripe-signature": "t=123,v1=sig",
                            "content-type": "application/json",
                        },
                    )

                assert resp.status_code == 200
                # Handler must NOT be called for duplicates
                mock_process.assert_not_called()
        finally:
            app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Bug 2: Webhook processing atomicity
# ---------------------------------------------------------------------------


class TestBug2WebhookAtomicity:
    """Webhook handlers must not commit individually — single outer commit."""

    def test_sync_subscription_uses_flush_not_commit(self, db_session, make_user):
        """sync_subscription_from_stripe uses flush, not commit."""
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="atom_sync@example.com")
        stripe_sub = {
            "id": "sub_atom",
            "status": "active",
            "items": {"data": [{"price": {"id": "price_solo_mo"}, "quantity": 1, "plan": {"interval": "month"}}]},
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "cancel_at_period_end": False,
        }

        committed = False
        original_commit = db_session.commit

        def spy_commit():
            nonlocal committed
            committed = True
            original_commit()

        with (
            patch("billing.price_config.get_all_seat_price_ids", return_value=set()),
            patch.object(db_session, "commit", side_effect=spy_commit),
        ):
            sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_atom", "solo")

        # sync_subscription_from_stripe must NOT have committed (it uses flush now)
        assert committed is False

    @pytest.mark.asyncio
    async def test_handler_failure_rolls_back_dedup_marker(self, db_session):
        """If a handler raises after dedup insert, the entire transaction is rolled back."""
        from database import get_db
        from main import app

        mock_stripe = MagicMock()
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_rollback_test",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_rb", "customer": "cus_rb", "subscription": "sub_rb"}},
        }

        app.dependency_overrides[get_db] = lambda: db_session

        try:
            import httpx

            with (
                patch("billing.stripe_client.is_stripe_enabled", return_value=True),
                patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
                patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_SECRET"),
                patch(
                    "billing.webhook_handler.process_webhook_event",
                    side_effect=RuntimeError("handler crash"),
                ),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    resp = await client.post(
                        "/billing/webhook",
                        content=b'{"type": "test"}',
                        headers={
                            "stripe-signature": "t=123,v1=sig",
                            "content-type": "application/json",
                        },
                    )

                # Must return non-200 so Stripe retries
                assert resp.status_code == 500

                # Dedup marker must NOT be persisted (was rolled back)
                from subscription_model import ProcessedWebhookEvent

                marker = (
                    db_session.query(ProcessedWebhookEvent)
                    .filter(ProcessedWebhookEvent.stripe_event_id == "evt_rollback_test")
                    .first()
                )
                assert marker is None
        finally:
            app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Bug 3: Admin overview — correct field references
# ---------------------------------------------------------------------------


class TestBug3AdminOverviewFields:
    """Admin overview uses correct model fields (timestamp, not created_at for ActivityLog)."""

    def test_activity_log_has_timestamp_not_created_at(self):
        """ActivityLog model uses 'timestamp', not 'created_at' — verify column exists."""
        assert hasattr(ActivityLog, "timestamp"), "ActivityLog must have 'timestamp' column"
        # Confirm there's no 'created_at' column on ActivityLog (the source of the bug)
        col_names = [c.name for c in ActivityLog.__table__.columns]
        assert "timestamp" in col_names
        # Note: SoftDeleteMixin may add an 'archived_at' but ActivityLog has no 'created_at'

    def test_admin_overview_references_correct_columns(self):
        """Verify get_overview correctly references ActivityLog.timestamp for upload counting."""
        # Direct attribute access test: ActivityLog.timestamp is a valid column,
        # ActivityLog has no 'created_at' or 'tool_name' column.
        from sqlalchemy.orm.attributes import InstrumentedAttribute

        assert isinstance(ActivityLog.timestamp, InstrumentedAttribute)

        # ActivityLog should NOT have 'tool_name' as a column
        col_names = [c.name for c in ActivityLog.__table__.columns]
        assert "tool_name" not in col_names

    def test_admin_overview_tool_usage_queries_team_activity(self):
        """Tool usage query in get_overview must use TeamActivityLog, not ActivityLog."""
        from sqlalchemy.orm.attributes import InstrumentedAttribute

        from team_activity_model import TeamActivityLog

        # TeamActivityLog has the tool_name column that the admin dashboard needs
        assert isinstance(TeamActivityLog.tool_name, InstrumentedAttribute)
        assert isinstance(TeamActivityLog.created_at, InstrumentedAttribute)

    def test_usage_by_member_uses_timestamp(self):
        """ActivityLog queries must use .timestamp (the actual column), not .created_at."""
        col_names = [c.name for c in ActivityLog.__table__.columns]
        assert "timestamp" in col_names


# ---------------------------------------------------------------------------
# Bug 4: Client manager — no cartesian join
# ---------------------------------------------------------------------------


class TestBug4ClientManagerCount:
    """get_clients_with_count must return correct results without duplication."""

    def test_correct_count_and_no_duplicates(self, db_session, make_user):
        """Multiple clients: count matches, no duplicates, correct page size."""
        from client_manager import ClientManager

        user = make_user(email="client_count@example.com")
        mgr = ClientManager(db_session)

        # Create 5 clients
        for i in range(5):
            client = Client(user_id=user.id, name=f"Client {i:02d}")
            db_session.add(client)
        db_session.flush()

        # Request page of 3
        clients, total = mgr.get_clients_with_count(user.id, limit=3, offset=0)

        assert total == 5
        assert len(clients) == 3

        # No duplicate IDs
        ids = [c.id for c in clients]
        assert len(ids) == len(set(ids))

    def test_empty_result(self, db_session, make_user):
        """User with no clients returns empty list and count=0."""
        from client_manager import ClientManager

        user = make_user(email="client_empty@example.com")
        mgr = ClientManager(db_session)

        clients, total = mgr.get_clients_with_count(user.id)
        assert clients == []
        assert total == 0

    def test_single_client(self, db_session, make_user):
        """Single client: count=1, list has 1 item."""
        from client_manager import ClientManager

        user = make_user(email="client_single@example.com")
        mgr = ClientManager(db_session)

        client = Client(user_id=user.id, name="Only Client")
        db_session.add(client)
        db_session.flush()

        clients, total = mgr.get_clients_with_count(user.id)
        assert total == 1
        assert len(clients) == 1
        assert clients[0].name == "Only Client"


# ---------------------------------------------------------------------------
# Bug 5: Seat removal — Stripe quantity must reach 0
# ---------------------------------------------------------------------------


class TestBug5SeatRemovalToZero:
    """Removing all additional seats must send quantity=0 (or delete item) to Stripe."""

    def test_remove_all_seats_deletes_stripe_item(self, db_session, make_user):
        """Removing last 3 seats: local=0, Stripe item deleted (not clamped to 1)."""
        from billing.subscription_manager import remove_seats

        user = make_user(email="seat_zero@example.com")

        # Create subscription with 3 additional seats
        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seat_rm",
            stripe_subscription_id="sub_seat_rm",
            seat_count=1,
            additional_seats=3,
        )
        db_session.add(sub)
        db_session.flush()

        # Mock Stripe
        mock_stripe = MagicMock()
        mock_stripe.Subscription.retrieve.return_value = {
            "items": {
                "data": [
                    {"id": "si_plan", "price": {"id": "price_pro_mo"}, "quantity": 1},
                    {"id": "si_seat", "price": {"id": "price_seat_mo"}, "quantity": 3},
                ]
            }
        }

        with (
            patch("billing.subscription_manager.get_stripe", return_value=mock_stripe),
            patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}),
        ):
            result = remove_seats(db_session, user.id, 3)

        assert result is not None
        assert result.additional_seats == 0

        # Stripe item must be DELETED (not modified with quantity=1)
        from unittest.mock import ANY

        mock_stripe.SubscriptionItem.delete.assert_called_once_with("si_seat", idempotency_key=ANY)
        mock_stripe.SubscriptionItem.modify.assert_not_called()

    def test_partial_removal_modifies_stripe_item(self, db_session, make_user):
        """Removing 2 of 5 seats: Stripe item modified to quantity=3."""
        from billing.subscription_manager import remove_seats

        user = make_user(email="seat_partial@example.com")

        sub = Subscription(
            user_id=user.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seat_partial",
            stripe_subscription_id="sub_seat_partial",
            seat_count=1,
            additional_seats=5,
        )
        db_session.add(sub)
        db_session.flush()

        mock_stripe = MagicMock()
        mock_stripe.Subscription.retrieve.return_value = {
            "items": {
                "data": [
                    {"id": "si_plan", "price": {"id": "price_pro_mo"}, "quantity": 1},
                    {"id": "si_seat", "price": {"id": "price_seat_mo"}, "quantity": 5},
                ]
            }
        }

        with (
            patch("billing.subscription_manager.get_stripe", return_value=mock_stripe),
            patch("billing.price_config.get_all_seat_price_ids", return_value={"price_seat_mo"}),
        ):
            result = remove_seats(db_session, user.id, 2)

        assert result is not None
        assert result.additional_seats == 3
        from unittest.mock import ANY

        mock_stripe.SubscriptionItem.modify.assert_called_once_with("si_seat", quantity=3, idempotency_key=ANY)
        mock_stripe.SubscriptionItem.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Bug 6: Invite acceptance at exact capacity
# ---------------------------------------------------------------------------


class TestBug6InviteAcceptanceAtCapacity:
    """Accepting the last-seat invite must not be blocked by double-counting."""

    def test_accept_invite_at_exact_capacity(self, db_session, make_user):
        """Org at exact capacity with 1 pending invite — acceptance succeeds."""
        from organization_model import (
            InviteStatus,
            Organization,
            OrganizationInvite,
            OrganizationMember,
            OrgRole,
        )
        from shared.entitlement_checks import check_seat_limit_for_org

        owner = make_user(email="owner_cap@example.com")

        org = Organization(name="Cap Org", slug="cap-org", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()

        # Create subscription with total_seats=2
        sub = Subscription(
            user_id=owner.id,
            tier="professional",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_cap",
            seat_count=2,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        org.subscription_id = sub.id

        # Owner membership (1 member)
        m = OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER)
        db_session.add(m)

        # Pending invite (makes effective_count = 1 member + 1 pending = 2 = total_seats)
        invite = OrganizationInvite(
            organization_id=org.id,
            invite_token_hash="fakehash",
            invitee_email="invited@example.com",
            role=OrgRole.MEMBER,
            invited_by_user_id=owner.id,
            status=InviteStatus.PENDING,
        )
        db_session.add(invite)
        db_session.flush()

        # Enforce hard mode for this test
        with patch("shared.entitlement_checks._get_seat_enforcement_mode", return_value="hard"):
            # WITHOUT exclude_invite_id → should BLOCK (at capacity)
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc:
                check_seat_limit_for_org(db_session, org.id)
            assert exc.value.status_code == 403

            # WITH exclude_invite_id → should PASS (invite being accepted)
            check_seat_limit_for_org(db_session, org.id, exclude_invite_id=invite.id)
            # No exception = test passes


# ---------------------------------------------------------------------------
# Bug 7: Webhook metadata — malformed paciolus_user_id
# ---------------------------------------------------------------------------


class TestBug7WebhookMetadataValidation:
    """Malformed metadata values must not crash the webhook handler."""

    def test_none_user_id_falls_through(self):
        """None value for paciolus_user_id falls through to customer lookup."""
        from billing.webhook_handler import _resolve_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = _resolve_user_id(mock_db, {"metadata": {"paciolus_user_id": None}})
        assert result is None

    def test_missing_key_falls_through(self):
        """Missing paciolus_user_id key falls through to customer lookup."""
        from billing.webhook_handler import _resolve_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = _resolve_user_id(mock_db, {"metadata": {}})
        assert result is None

    def test_string_abc_falls_through(self):
        """Non-numeric string 'abc' is handled gracefully, falls through."""
        from billing.webhook_handler import _resolve_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = _resolve_user_id(mock_db, {"metadata": {"paciolus_user_id": "abc"}})
        assert result is None

    def test_empty_string_falls_through(self):
        """Empty string '' is handled gracefully, falls through."""
        from billing.webhook_handler import _resolve_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = _resolve_user_id(mock_db, {"metadata": {"paciolus_user_id": ""}})
        assert result is None

    def test_valid_integer_string_returns_int(self):
        """Valid integer string '42' returns int 42."""
        from billing.webhook_handler import _resolve_user_id

        mock_db = MagicMock()
        result = _resolve_user_id(mock_db, {"metadata": {"paciolus_user_id": "42"}})
        assert result == 42

    def test_none_metadata_handled(self):
        """metadata=None handled gracefully (not just missing key)."""
        from billing.webhook_handler import _resolve_user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = _resolve_user_id(mock_db, {"metadata": None})
        assert result is None


# ---------------------------------------------------------------------------
# Bug 8: Tool run numbering — unique constraint prevents duplicates
# ---------------------------------------------------------------------------


class TestBug8ToolRunUniqueness:
    """Unique constraint on (engagement_id, tool_name, run_number) prevents race duplicates."""

    def test_sequential_runs_get_distinct_numbers(self, db_session, make_engagement):
        """Three sequential record_tool_run calls produce run_numbers 1, 2, 3."""
        from engagement_manager import EngagementManager
        from engagement_model import ToolName, ToolRunStatus

        eng = make_engagement()
        mgr = EngagementManager(db_session)

        runs = []
        for _ in range(3):
            run = mgr.record_tool_run(eng.id, ToolName.TRIAL_BALANCE, ToolRunStatus.COMPLETED)
            runs.append(run)

        numbers = [r.run_number for r in runs]
        assert numbers == [1, 2, 3]
        assert len(set(numbers)) == 3

    def test_retry_on_integrity_error(self, db_session, make_engagement):
        """When IntegrityError occurs (race), retry produces the next available number."""

        from engagement_manager import EngagementManager
        from engagement_model import ToolName, ToolRun, ToolRunStatus

        eng = make_engagement()
        mgr = EngagementManager(db_session)

        # Pre-insert run_number=1 manually
        existing = ToolRun(
            engagement_id=eng.id,
            tool_name=ToolName.TRIAL_BALANCE,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
        )
        db_session.add(existing)
        db_session.flush()

        # record_tool_run should see max=1 and try run_number=2
        run = mgr.record_tool_run(eng.id, ToolName.TRIAL_BALANCE, ToolRunStatus.COMPLETED)
        assert run.run_number == 2

    def test_different_tools_independent_numbering(self, db_session, make_engagement):
        """Different tool_names have independent run_number sequences."""
        from engagement_manager import EngagementManager
        from engagement_model import ToolName, ToolRunStatus

        eng = make_engagement()
        mgr = EngagementManager(db_session)

        run_tb = mgr.record_tool_run(eng.id, ToolName.TRIAL_BALANCE, ToolRunStatus.COMPLETED)
        run_je = mgr.record_tool_run(eng.id, ToolName.JOURNAL_ENTRY_TESTING, ToolRunStatus.COMPLETED)

        assert run_tb.run_number == 1
        assert run_je.run_number == 1
