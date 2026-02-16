"""
Tests for DB-backed Tool Sessions — Sprint 262

Validates:
- ToolSession model CRUD (load, save, delete, cleanup)
- Upsert behavior (INSERT ON CONFLICT UPDATE)
- TTL expiration (lazy cleanup on read)
- Startup cleanup (cleanup_expired_tool_sessions)
- AdjustmentSet round-trip (to_dict / from_dict) with edge cases
- CurrencyRateTable round-trip (to_storage_dict / from_storage_dict) with edge cases
- Multi-user isolation
- Large payloads (100+ items)
- Special characters in data
"""

import json
import sys
from datetime import datetime, UTC, timedelta, date, timezone
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tool_session_model import (
    ToolSession,
    load_tool_session,
    save_tool_session,
    delete_tool_session,
    cleanup_expired_tool_sessions,
    TOOL_SESSION_TTLS,
    DEFAULT_TTL_SECONDS,
    _is_expired,
    _save_fallback,
)
from adjusting_entries import (
    AdjustmentSet,
    AdjustingEntry,
    AdjustmentLine,
    AdjustmentType,
    AdjustmentStatus,
)
from currency_engine import CurrencyRateTable, ExchangeRate


# =============================================================================
# ToolSession Model CRUD
# =============================================================================


class TestToolSessionSaveAndLoad:
    """Basic save/load round-trip tests."""

    def test_save_and_load(self, db_session, make_user):
        user = make_user(email="session1@test.com")
        data = {"key": "value", "number": 42}
        save_tool_session(db_session, user.id, "adjustments", data)
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == data

    def test_load_nonexistent_returns_none(self, db_session, make_user):
        user = make_user(email="session2@test.com")
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded is None

    def test_save_overwrites_existing(self, db_session, make_user):
        """Upsert: second save should update, not create duplicate."""
        user = make_user(email="session3@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"v": 1})
        save_tool_session(db_session, user.id, "adjustments", {"v": 2})
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"v": 2}
        # Verify only one row exists
        count = db_session.query(ToolSession).filter_by(
            user_id=user.id, tool_name="adjustments"
        ).count()
        assert count == 1

    def test_different_tools_separate(self, db_session, make_user):
        user = make_user(email="session4@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"tool": "adj"})
        save_tool_session(db_session, user.id, "currency_rates", {"tool": "curr"})
        adj = load_tool_session(db_session, user.id, "adjustments")
        curr = load_tool_session(db_session, user.id, "currency_rates")
        assert adj == {"tool": "adj"}
        assert curr == {"tool": "curr"}

    def test_multi_user_isolation(self, db_session, make_user):
        """Different users' sessions must not interfere."""
        u1 = make_user(email="user1@test.com")
        u2 = make_user(email="user2@test.com")
        save_tool_session(db_session, u1.id, "adjustments", {"user": "one"})
        save_tool_session(db_session, u2.id, "adjustments", {"user": "two"})
        assert load_tool_session(db_session, u1.id, "adjustments") == {"user": "one"}
        assert load_tool_session(db_session, u2.id, "adjustments") == {"user": "two"}


class TestToolSessionDelete:
    def test_delete_existing(self, db_session, make_user):
        user = make_user(email="del1@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"x": 1})
        deleted = delete_tool_session(db_session, user.id, "adjustments")
        assert deleted is True
        assert load_tool_session(db_session, user.id, "adjustments") is None

    def test_delete_nonexistent(self, db_session, make_user):
        user = make_user(email="del2@test.com")
        deleted = delete_tool_session(db_session, user.id, "adjustments")
        assert deleted is False


class TestToolSessionTTL:
    """Lazy expiration on read."""

    def test_expired_session_returns_none(self, db_session, make_user):
        user = make_user(email="ttl1@test.com")
        # Insert a session with an old updated_at
        old_time = datetime.now(UTC) - timedelta(seconds=TOOL_SESSION_TTLS["adjustments"] + 60)
        ts = ToolSession(
            user_id=user.id,
            tool_name="adjustments",
            session_data=json.dumps({"expired": True}),
            updated_at=old_time,
        )
        db_session.add(ts)
        db_session.commit()

        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded is None

    def test_fresh_session_not_expired(self, db_session, make_user):
        user = make_user(email="ttl2@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"fresh": True})
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"fresh": True}

    def test_expired_session_deleted_from_db(self, db_session, make_user):
        """Lazy cleanup should remove the expired row."""
        user = make_user(email="ttl3@test.com")
        old_time = datetime.now(UTC) - timedelta(seconds=TOOL_SESSION_TTLS["adjustments"] + 60)
        ts = ToolSession(
            user_id=user.id,
            tool_name="adjustments",
            session_data=json.dumps({"expired": True}),
            updated_at=old_time,
        )
        db_session.add(ts)
        db_session.commit()

        load_tool_session(db_session, user.id, "adjustments")

        count = db_session.query(ToolSession).filter_by(
            user_id=user.id, tool_name="adjustments"
        ).count()
        assert count == 0

    def test_currency_rates_ttl_different(self, db_session, make_user):
        """Currency rates have 2h TTL vs adjustments 1h."""
        user = make_user(email="ttl4@test.com")
        # 90 minutes old — expired for adjustments (1h) but not currency (2h)
        mid_time = datetime.now(UTC) - timedelta(minutes=90)
        for tool in ("adjustments", "currency_rates"):
            ts = ToolSession(
                user_id=user.id,
                tool_name=tool,
                session_data=json.dumps({"tool": tool}),
                updated_at=mid_time,
            )
            db_session.add(ts)
        db_session.commit()

        adj = load_tool_session(db_session, user.id, "adjustments")
        curr = load_tool_session(db_session, user.id, "currency_rates")
        assert adj is None  # 90 min > 60 min TTL
        assert curr is not None  # 90 min < 120 min TTL


class TestToolSessionStartupCleanup:
    def test_cleanup_removes_expired(self, db_session, make_user):
        user = make_user(email="cleanup1@test.com")
        old_time = datetime.now(UTC) - timedelta(seconds=TOOL_SESSION_TTLS["adjustments"] + 60)
        ts = ToolSession(
            user_id=user.id,
            tool_name="adjustments",
            session_data=json.dumps({"stale": True}),
            updated_at=old_time,
        )
        db_session.add(ts)
        db_session.commit()

        count = cleanup_expired_tool_sessions(db_session)
        assert count >= 1

    def test_cleanup_keeps_fresh(self, db_session, make_user):
        user = make_user(email="cleanup2@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"fresh": True})
        cleanup_expired_tool_sessions(db_session)
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"fresh": True}


class TestIsExpired:
    def test_none_updated_at(self):
        assert _is_expired(None, "adjustments") is True

    def test_tz_naive_datetime(self):
        """SQLite returns tz-naive — should still work."""
        recent = datetime.utcnow()
        assert _is_expired(recent, "adjustments") is False

    def test_tz_aware_datetime(self):
        recent = datetime.now(UTC)
        assert _is_expired(recent, "adjustments") is False

    def test_old_datetime(self):
        old = datetime.now(UTC) - timedelta(hours=2)
        assert _is_expired(old, "adjustments") is True


# =============================================================================
# AdjustmentSet Round-Trip (to_dict / from_dict)
# =============================================================================


class TestAdjustmentSetRoundTrip:
    """Verify AdjustmentSet survives JSON serialization round-trip."""

    def _make_entry(
        self, ref="AJE-001", desc="Test", debit_acct="Cash", credit_acct="Revenue", amount="100.00"
    ):
        return AdjustingEntry(
            reference=ref,
            description=desc,
            adjustment_type=AdjustmentType.ACCRUAL,
            lines=[
                AdjustmentLine(account_name=debit_acct, debit=Decimal(amount)),
                AdjustmentLine(account_name=credit_acct, credit=Decimal(amount)),
            ],
        )

    def test_empty_set_round_trip(self):
        """Empty AdjustmentSet should survive round-trip."""
        original = AdjustmentSet()
        restored = AdjustmentSet.from_dict(original.to_dict())
        assert restored.total_adjustments == 0
        assert restored.entries == []

    def test_single_entry_round_trip(self):
        original = AdjustmentSet()
        original.add_entry(self._make_entry())
        restored = AdjustmentSet.from_dict(original.to_dict())
        assert restored.total_adjustments == 1
        assert restored.entries[0].reference == "AJE-001"
        assert restored.entries[0].lines[0].debit == Decimal("100.00")
        assert restored.entries[0].lines[1].credit == Decimal("100.00")

    def test_multiple_entries_round_trip(self):
        original = AdjustmentSet()
        original.add_entry(self._make_entry("AJE-001", "First"))
        original.add_entry(self._make_entry("AJE-002", "Second", "AR", "Revenue", "250.50"))
        restored = AdjustmentSet.from_dict(original.to_dict())
        assert restored.total_adjustments == 2
        assert restored.entries[1].reference == "AJE-002"

    def test_special_characters_in_account_names(self):
        """Account names with special chars must survive JSON round-trip."""
        entry = AdjustingEntry(
            reference="AJE-003",
            description="Special chars test: <script>alert('xss')</script>",
            lines=[
                AdjustmentLine(account_name='Accounts "Receivable" & Co.', debit=Decimal("50.00")),
                AdjustmentLine(account_name="Crédit Agricole — Épargne", credit=Decimal("50.00")),
            ],
        )
        original = AdjustmentSet(entries=[entry])
        data = original.to_dict()
        # Actually serialize to JSON and back (simulates DB storage)
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        restored = AdjustmentSet.from_dict(parsed)
        assert restored.entries[0].lines[0].account_name == 'Accounts "Receivable" & Co.'
        assert restored.entries[0].lines[1].account_name == "Crédit Agricole — Épargne"

    def test_all_statuses_round_trip(self):
        """Entries with different statuses should preserve status."""
        original = AdjustmentSet()
        for i, status in enumerate(AdjustmentStatus):
            entry = self._make_entry(f"AJE-{i:03d}", f"Status: {status.value}")
            entry.status = status
            original.add_entry(entry)

        restored = AdjustmentSet.from_dict(original.to_dict())
        for i, status in enumerate(AdjustmentStatus):
            assert restored.entries[i].status == status

    def test_all_types_round_trip(self):
        """Entries with different adjustment types should preserve type."""
        original = AdjustmentSet()
        for i, adj_type in enumerate(AdjustmentType):
            entry = self._make_entry(f"AJE-{i:03d}", f"Type: {adj_type.value}")
            original.add_entry(entry)
            original.entries[-1].adjustment_type = adj_type

        data = original.to_dict()
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        restored = AdjustmentSet.from_dict(parsed)
        for i, adj_type in enumerate(AdjustmentType):
            assert restored.entries[i].adjustment_type == adj_type

    def test_large_payload_100_entries(self):
        """100+ adjusting entries should round-trip correctly."""
        original = AdjustmentSet()
        for i in range(120):
            original.add_entry(self._make_entry(
                ref=f"AJE-{i:03d}",
                desc=f"Entry number {i}",
                amount=f"{(i + 1) * 10.50:.2f}",
            ))
        data = original.to_dict()
        json_str = json.dumps(data)
        assert len(json_str) > 10_000  # Sanity check: payload is large
        parsed = json.loads(json_str)
        restored = AdjustmentSet.from_dict(parsed)
        assert restored.total_adjustments == 120
        assert restored.entries[99].reference == "AJE-099"

    def test_period_and_client_preserved(self):
        original = AdjustmentSet(
            period_label="FY2025",
            client_name="Acme Corporation",
        )
        original.add_entry(self._make_entry())
        restored = AdjustmentSet.from_dict(original.to_dict())
        assert restored.period_label == "FY2025"
        assert restored.client_name == "Acme Corporation"

    def test_db_round_trip(self, db_session, make_user):
        """Full end-to-end: AdjustmentSet → DB → AdjustmentSet.

        Packet 2: Lines are sanitized on save, so entries survive
        with metadata but without financial line data.
        """
        user = make_user(email="adj_rt@test.com")
        original = AdjustmentSet(period_label="Q4 2025")
        original.add_entry(self._make_entry())

        save_tool_session(db_session, user.id, "adjustments", original.to_dict())
        data = load_tool_session(db_session, user.id, "adjustments")
        restored = AdjustmentSet.from_dict(data)

        assert restored.total_adjustments == 1
        assert restored.period_label == "Q4 2025"
        assert restored.entries[0].reference == "AJE-001"
        # Lines are stripped by Packet 2 sanitization
        assert len(restored.entries[0].lines) == 0


# =============================================================================
# CurrencyRateTable Round-Trip (to_storage_dict / from_storage_dict)
# =============================================================================


class TestCurrencyRateTableRoundTrip:
    """Verify CurrencyRateTable survives JSON serialization round-trip."""

    def _make_table(self, rates=None, currency="USD"):
        if rates is None:
            rates = [
                ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.0523")),
                ExchangeRate(date(2026, 1, 31), "GBP", "USD", Decimal("1.2650")),
            ]
        return CurrencyRateTable(
            rates=rates,
            uploaded_at=datetime(2026, 2, 15, 10, 0, 0, tzinfo=UTC),
            presentation_currency=currency,
        )

    def test_empty_rate_table_round_trip(self):
        """Empty rate table should survive round-trip."""
        original = CurrencyRateTable()
        restored = CurrencyRateTable.from_storage_dict(original.to_storage_dict())
        assert len(restored.rates) == 0
        assert restored.presentation_currency == "USD"

    def test_basic_round_trip(self):
        original = self._make_table()
        data = original.to_storage_dict()
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        restored = CurrencyRateTable.from_storage_dict(parsed)
        assert len(restored.rates) == 2
        assert restored.rates[0].from_currency == "EUR"
        assert restored.rates[0].rate == Decimal("1.0523")
        assert restored.presentation_currency == "USD"
        assert restored.uploaded_at is not None

    def test_zero_rate(self):
        """Rates with zero should fail validation, but 0.0001 should survive."""
        table = CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 1), "JPY", "USD", Decimal("0.0001"))],
            presentation_currency="USD",
        )
        restored = CurrencyRateTable.from_storage_dict(table.to_storage_dict())
        assert restored.rates[0].rate == Decimal("0.0001")

    def test_very_large_rate(self):
        """Very large rates (hyperinflation scenarios) should round-trip."""
        table = CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 1), "VES", "USD", Decimal("9999999.9999"))],
            presentation_currency="USD",
        )
        json_str = json.dumps(table.to_storage_dict())
        parsed = json.loads(json_str)
        restored = CurrencyRateTable.from_storage_dict(parsed)
        assert restored.rates[0].rate == Decimal("9999999.9999")

    def test_many_currency_pairs(self):
        """Table with many pairs should round-trip."""
        pairs = [
            ("EUR", "1.05"), ("GBP", "1.27"), ("JPY", "0.0067"), ("CHF", "1.12"),
            ("CAD", "0.74"), ("AUD", "0.65"), ("NZD", "0.61"), ("CNY", "0.14"),
            ("INR", "0.012"), ("BRL", "0.17"), ("MXN", "0.058"), ("ZAR", "0.055"),
        ]
        rates = [
            ExchangeRate(date(2026, 1, 31), code, "USD", Decimal(rate))
            for code, rate in pairs
        ]
        table = CurrencyRateTable(rates=rates, presentation_currency="USD")
        restored = CurrencyRateTable.from_storage_dict(table.to_storage_dict())
        assert len(restored.rates) == 12
        assert restored.rates[2].from_currency == "JPY"

    def test_100_plus_rates(self):
        """100+ rates should round-trip correctly."""
        rates = [
            ExchangeRate(
                date(2026, 1, i % 28 + 1),
                "EUR",
                "USD",
                Decimal(f"1.{i:04d}"),
            )
            for i in range(120)
        ]
        table = CurrencyRateTable(rates=rates, presentation_currency="USD")
        data = table.to_storage_dict()
        json_str = json.dumps(data)
        assert len(json_str) > 5_000
        restored = CurrencyRateTable.from_storage_dict(json.loads(json_str))
        assert len(restored.rates) == 120

    def test_non_usd_presentation_currency(self):
        table = CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 31), "USD", "EUR", Decimal("0.9502"))],
            presentation_currency="EUR",
        )
        restored = CurrencyRateTable.from_storage_dict(table.to_storage_dict())
        assert restored.presentation_currency == "EUR"

    def test_uploaded_at_none(self):
        """Table without uploaded_at should round-trip with None."""
        table = CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))],
            uploaded_at=None,
        )
        restored = CurrencyRateTable.from_storage_dict(table.to_storage_dict())
        assert restored.uploaded_at is None

    def test_db_round_trip(self, db_session, make_user):
        """Full end-to-end: CurrencyRateTable → DB → CurrencyRateTable."""
        user = make_user(email="curr_rt@test.com")
        original = self._make_table()

        save_tool_session(db_session, user.id, "currency_rates", original.to_storage_dict())
        data = load_tool_session(db_session, user.id, "currency_rates")
        restored = CurrencyRateTable.from_storage_dict(data)

        assert len(restored.rates) == 2
        assert restored.rates[0].rate == Decimal("1.0523")
        assert restored.presentation_currency == "USD"


# =============================================================================
# Dialect-Aware Upsert (Packet 5)
# =============================================================================


class TestDialectAwareUpsert:
    """Verify save_tool_session dispatches correctly per dialect."""

    def test_sqlite_native_upsert(self, db_session, make_user):
        """SQLite dialect (test default) should use native INSERT ON CONFLICT."""
        user = make_user(email="dialect_sq@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"v": 1})
        save_tool_session(db_session, user.id, "adjustments", {"v": 2})
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"v": 2}
        count = db_session.query(ToolSession).filter_by(
            user_id=user.id, tool_name="adjustments"
        ).count()
        assert count == 1

    def test_postgresql_dialect_importable(self):
        """PostgreSQL dialect insert should be importable for the pg path."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        assert pg_insert is not None

    def test_fallback_insert_new_row(self, db_session, make_user):
        """Fallback path should INSERT when no row exists."""
        user = make_user(email="fb_insert@test.com")
        now = datetime.now(UTC)
        _save_fallback(db_session, user.id, "adjustments", json.dumps({"v": 1}), now)
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"v": 1}

    def test_fallback_update_existing_row(self, db_session, make_user):
        """Fallback path should UPDATE when row already exists."""
        user = make_user(email="fb_update@test.com")
        now = datetime.now(UTC)
        _save_fallback(db_session, user.id, "adjustments", json.dumps({"v": 1}), now)
        _save_fallback(db_session, user.id, "adjustments", json.dumps({"v": 2}), now)
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"v": 2}
        count = db_session.query(ToolSession).filter_by(
            user_id=user.id, tool_name="adjustments"
        ).count()
        assert count == 1

    def test_fallback_dispatched_for_unknown_dialect(self, db_session, make_user):
        """Unknown dialect name should route to _save_fallback."""
        from unittest.mock import patch, MagicMock

        user = make_user(email="fb_dispatch@test.com")

        mock_bind = MagicMock()
        mock_bind.dialect.name = "mysql"

        with patch.object(db_session, "bind", mock_bind):
            with patch("tool_session_model._save_fallback") as mock_fb:
                save_tool_session(db_session, user.id, "adjustments", {"v": 1})
                mock_fb.assert_called_once()


# =============================================================================
# Upsert Race Condition Simulation
# =============================================================================


class TestUpsertBehavior:
    """Verify upsert (INSERT ON CONFLICT UPDATE) works correctly."""

    def test_concurrent_saves_last_wins(self, db_session, make_user):
        """Simulate two workers saving: last write wins."""
        user = make_user(email="upsert1@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"worker": "A"})
        save_tool_session(db_session, user.id, "adjustments", {"worker": "B"})
        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert loaded == {"worker": "B"}

    def test_upsert_updates_timestamp(self, db_session, make_user):
        """Upsert should update updated_at."""
        user = make_user(email="upsert2@test.com")
        save_tool_session(db_session, user.id, "adjustments", {"v": 1})
        row1 = db_session.query(ToolSession).filter_by(
            user_id=user.id, tool_name="adjustments"
        ).first()
        ts1 = row1.updated_at

        save_tool_session(db_session, user.id, "adjustments", {"v": 2})
        db_session.expire_all()
        row2 = db_session.query(ToolSession).filter_by(
            user_id=user.id, tool_name="adjustments"
        ).first()
        # updated_at should be >= ts1 (may be equal due to fast execution)
        assert row2.updated_at >= ts1


# =============================================================================
# Route Registration
# =============================================================================


class TestRouteRegistration:
    """Verify routes still registered after refactoring."""

    def test_adjustment_routes_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/adjustments" in paths
        assert "/audit/adjustments/types" in paths
        assert "/audit/adjustments/statuses" in paths
        assert "/audit/adjustments/reference/next" in paths
        assert "/audit/adjustments/apply" in paths

    def test_currency_routes_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/currency-rates" in paths
        assert "/audit/currency-rate" in paths


# =============================================================================
# Financial Data Sanitization (Packet 2)
# =============================================================================


class TestFinancialDataSanitization:
    """Verify financial data is stripped from tool session persistence."""

    def _make_adjustment_data(self):
        """Return a typical AdjustmentSet.to_dict() payload with financial content."""
        return {
            "entries": [{
                "id": "entry-001",
                "reference": "AJE-001",
                "description": "Accrue unbilled revenue",
                "adjustment_type": "accrual",
                "status": "proposed",
                "lines": [
                    {"account_name": "Accounts Receivable", "debit": 5000.0, "credit": 0.0, "description": None},
                    {"account_name": "Revenue", "debit": 0.0, "credit": 5000.0, "description": None},
                ],
                "total_debits": 5000.0,
                "total_credits": 5000.0,
                "entry_total": 5000.0,
                "is_balanced": True,
                "account_count": 2,
                "prepared_by": "auditor@test.com",
                "reviewed_by": None,
                "created_at": "2026-02-16T10:00:00+00:00",
                "updated_at": None,
                "notes": "Q4 year-end",
                "is_reversing": False,
            }],
            "total_adjustments": 1,
            "proposed_count": 1,
            "approved_count": 0,
            "rejected_count": 0,
            "posted_count": 0,
            "total_adjustment_amount": 0.0,
            "period_label": "FY2025",
            "client_name": "Acme Corp",
            "created_at": "2026-02-16T10:00:00+00:00",
        }

    def test_adjustment_lines_stripped_on_save(self, db_session, make_user):
        """Lines array must be stripped from saved adjustment entries."""
        user = make_user(email="sanitize_lines@test.com")
        save_tool_session(db_session, user.id, "adjustments", self._make_adjustment_data())
        loaded = load_tool_session(db_session, user.id, "adjustments")

        entry = loaded["entries"][0]
        assert "lines" not in entry
        assert "total_debits" not in entry
        assert "total_credits" not in entry
        assert "entry_total" not in entry

    def test_adjustment_set_total_stripped(self, db_session, make_user):
        """Top-level total_adjustment_amount must be stripped."""
        user = make_user(email="sanitize_total@test.com")
        data = self._make_adjustment_data()
        data["total_adjustment_amount"] = 5000.0
        save_tool_session(db_session, user.id, "adjustments", data)
        loaded = load_tool_session(db_session, user.id, "adjustments")

        assert "total_adjustment_amount" not in loaded

    def test_adjustment_metadata_preserved(self, db_session, make_user):
        """Non-financial metadata must survive sanitization."""
        user = make_user(email="sanitize_meta@test.com")
        save_tool_session(db_session, user.id, "adjustments", self._make_adjustment_data())
        loaded = load_tool_session(db_session, user.id, "adjustments")

        entry = loaded["entries"][0]
        assert entry["id"] == "entry-001"
        assert entry["reference"] == "AJE-001"
        assert entry["description"] == "Accrue unbilled revenue"
        assert entry["adjustment_type"] == "accrual"
        assert entry["status"] == "proposed"
        assert entry["prepared_by"] == "auditor@test.com"
        assert entry["notes"] == "Q4 year-end"
        assert entry["is_reversing"] is False
        assert entry["is_balanced"] is True
        assert loaded["period_label"] == "FY2025"
        assert loaded["client_name"] == "Acme Corp"

    def test_currency_rates_not_affected(self, db_session, make_user):
        """Currency rate data is reference data and must NOT be stripped."""
        user = make_user(email="sanitize_curr@test.com")
        rate_data = {
            "rates": [
                {"effective_date": "2026-01-31", "from_currency": "EUR",
                 "to_currency": "USD", "rate": "1.0523"},
                {"effective_date": "2026-01-31", "from_currency": "GBP",
                 "to_currency": "USD", "rate": "1.2650"},
            ],
            "uploaded_at": "2026-02-15T10:00:00+00:00",
            "presentation_currency": "USD",
        }
        save_tool_session(db_session, user.id, "currency_rates", rate_data)
        loaded = load_tool_session(db_session, user.id, "currency_rates")

        assert len(loaded["rates"]) == 2
        assert loaded["rates"][0]["rate"] == "1.0523"
        assert loaded["rates"][0]["from_currency"] == "EUR"
        assert loaded["rates"][1]["to_currency"] == "USD"
        assert loaded["presentation_currency"] == "USD"

    def test_forbidden_keys_stripped_defense_in_depth(self, db_session, make_user):
        """Even for unknown tools, forbidden financial keys are caught."""
        user = make_user(email="sanitize_depth@test.com")
        data = {
            "safe_key": "preserved",
            "nested": {
                "account_name": "Should be stripped",
                "debit": 5000.0,
                "credit": 3000.0,
                "amount": 2000.0,
                "safe_nested": "also preserved",
            },
            "list_data": [
                {"account_name": "Gone", "ok": True},
            ],
        }
        save_tool_session(db_session, user.id, "some_future_tool", data)
        loaded = load_tool_session(db_session, user.id, "some_future_tool")

        assert loaded["safe_key"] == "preserved"
        assert "account_name" not in loaded["nested"]
        assert "debit" not in loaded["nested"]
        assert "credit" not in loaded["nested"]
        assert "amount" not in loaded["nested"]
        assert loaded["nested"]["safe_nested"] == "also preserved"
        assert "account_name" not in loaded["list_data"][0]
        assert loaded["list_data"][0]["ok"] is True

    def test_empty_entries_survive(self, db_session, make_user):
        """Empty adjustment set should round-trip cleanly."""
        user = make_user(email="sanitize_empty@test.com")
        adj_data = {"entries": [], "period_label": "FY2025"}
        save_tool_session(db_session, user.id, "adjustments", adj_data)
        loaded = load_tool_session(db_session, user.id, "adjustments")

        assert loaded["entries"] == []
        assert loaded["period_label"] == "FY2025"

    def test_multiple_entries_all_sanitized(self, db_session, make_user):
        """Multiple entries should all have lines stripped."""
        user = make_user(email="sanitize_multi@test.com")
        data = {
            "entries": [
                {"id": f"e-{i}", "reference": f"AJE-{i:03d}", "status": "proposed",
                 "lines": [{"account_name": f"Acct-{i}", "debit": float(i * 100), "credit": 0.0}],
                 "total_debits": float(i * 100), "entry_total": float(i * 100)}
                for i in range(5)
            ],
        }
        save_tool_session(db_session, user.id, "adjustments", data)
        loaded = load_tool_session(db_session, user.id, "adjustments")

        assert len(loaded["entries"]) == 5
        for entry in loaded["entries"]:
            assert "lines" not in entry
            assert "total_debits" not in entry
            assert "entry_total" not in entry
            assert "id" in entry  # metadata kept
            assert "reference" in entry

    def test_adjustment_set_round_trip_via_model(self, db_session, make_user):
        """Full AdjustmentSet → save → load → from_dict: entries have no lines."""
        user = make_user(email="sanitize_model_rt@test.com")
        adj_set = AdjustmentSet(period_label="FY2025")
        adj_set.add_entry(AdjustingEntry(
            reference="AJE-001",
            description="Accrue revenue",
            adjustment_type=AdjustmentType.ACCRUAL,
            lines=[
                AdjustmentLine(account_name="AR", debit=Decimal("1000.00")),
                AdjustmentLine(account_name="Revenue", credit=Decimal("1000.00")),
            ],
        ))

        # Save through the session layer (sanitized)
        save_tool_session(db_session, user.id, "adjustments", adj_set.to_dict())
        data = load_tool_session(db_session, user.id, "adjustments")
        restored = AdjustmentSet.from_dict(data)

        # Entry metadata survives
        assert restored.total_adjustments == 1
        assert restored.entries[0].reference == "AJE-001"
        assert restored.entries[0].description == "Accrue revenue"
        assert restored.entries[0].adjustment_type == AdjustmentType.ACCRUAL
        # Lines are gone
        assert len(restored.entries[0].lines) == 0


# =============================================================================
# Legacy Session Cleanup (Packet 2)
# =============================================================================


class TestLegacySessionCleanup:
    """Verify startup sanitization of pre-Packet-2 tool session rows."""

    def test_sanitizes_legacy_rows_with_financial_data(self, db_session, make_user):
        """Rows with financial content are sanitized at startup."""
        from tool_session_model import sanitize_existing_sessions

        user = make_user(email="legacy_san1@test.com")
        legacy_data = json.dumps({
            "entries": [{
                "id": "old-entry",
                "reference": "AJE-001",
                "status": "proposed",
                "lines": [{"account_name": "Cash", "debit": 1000, "credit": 0}],
                "total_debits": 1000.0,
                "total_credits": 1000.0,
                "entry_total": 1000.0,
            }],
            "total_adjustment_amount": 1000.0,
        })
        ts = ToolSession(
            user_id=user.id,
            tool_name="adjustments",
            session_data=legacy_data,
            updated_at=datetime.now(UTC),
        )
        db_session.add(ts)
        db_session.commit()

        count = sanitize_existing_sessions(db_session)
        assert count == 1

        loaded = load_tool_session(db_session, user.id, "adjustments")
        assert "lines" not in loaded["entries"][0]
        assert "total_debits" not in loaded["entries"][0]
        assert "total_adjustment_amount" not in loaded

    def test_already_clean_rows_not_modified(self, db_session, make_user):
        """Rows without financial data should not be modified."""
        from tool_session_model import sanitize_existing_sessions

        user = make_user(email="legacy_san2@test.com")
        clean_data = json.dumps({
            "entries": [{"id": "clean-entry", "reference": "AJE-001", "status": "proposed"}],
        })
        ts = ToolSession(
            user_id=user.id,
            tool_name="adjustments",
            session_data=clean_data,
            updated_at=datetime.now(UTC),
        )
        db_session.add(ts)
        db_session.commit()

        count = sanitize_existing_sessions(db_session)
        assert count == 0

    def test_returns_accurate_count(self, db_session, make_user):
        """Returns correct count of sanitized rows."""
        from tool_session_model import sanitize_existing_sessions

        u1 = make_user(email="legacy_san3@test.com")
        u2 = make_user(email="legacy_san4@test.com")

        for user in (u1, u2):
            ts = ToolSession(
                user_id=user.id,
                tool_name="adjustments",
                session_data=json.dumps({
                    "entries": [{"lines": [{"account_name": "Cash", "debit": 100}]}],
                }),
                updated_at=datetime.now(UTC),
            )
            db_session.add(ts)

        # One clean row
        ts_clean = ToolSession(
            user_id=u1.id,
            tool_name="currency_rates",
            session_data=json.dumps({"rates": [], "presentation_currency": "USD"}),
            updated_at=datetime.now(UTC),
        )
        db_session.add(ts_clean)
        db_session.commit()

        count = sanitize_existing_sessions(db_session)
        assert count == 2  # Two dirty rows, one clean

    def test_idempotent(self, db_session, make_user):
        """Second sanitization run changes nothing."""
        from tool_session_model import sanitize_existing_sessions

        user = make_user(email="legacy_san5@test.com")
        ts = ToolSession(
            user_id=user.id,
            tool_name="adjustments",
            session_data=json.dumps({
                "entries": [{"lines": [{"account_name": "AR", "debit": 500}]}],
            }),
            updated_at=datetime.now(UTC),
        )
        db_session.add(ts)
        db_session.commit()

        first = sanitize_existing_sessions(db_session)
        assert first == 1
        second = sanitize_existing_sessions(db_session)
        assert second == 0

    def test_main_wires_sanitize_existing_sessions(self):
        """main.py must import and call sanitize_existing_sessions in lifespan."""
        import ast
        from pathlib import Path

        main_path = Path(__file__).parent.parent / "main.py"
        source = main_path.read_text()
        assert "sanitize_existing_sessions" in source

        tree = ast.parse(source)
        found_import = False
        found_call = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "tool_session_model":
                for alias in node.names:
                    if alias.name == "sanitize_existing_sessions":
                        found_import = True
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "sanitize_existing_sessions":
                    found_call = True
        assert found_import, "main.py must import sanitize_existing_sessions"
        assert found_call, "main.py must call sanitize_existing_sessions()"
