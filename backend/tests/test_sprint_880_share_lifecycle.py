"""Sprint 880: shared-link retention, cleanup and file provenance.

5A (DH-08) — a link stops working at expiry and its stored file is gone within
one hour after that: the purge runs every 10 minutes, opening an expired link
deletes its file there and then, a file that outlives its link by more than an
hour raises a warning, and a link dies with its creator's place in the firm or
their account. A downgrade does not revoke links.

Real Bearer auth throughout (only ``get_db`` is overridden), so these tests run
the same dependency path production does.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import Session

from auth import create_access_token
from database import get_db
from export_share_model import ExportShare
from main import app
from models import User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from shared import export_share_storage
from shared.parser_metrics import PARSER_REGISTRY
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

pytestmark = pytest.mark.usefixtures("bypass_csrf")

PDF_BYTES = b"%PDF-1.4 sprint880 share lifecycle"
_OVERDUE_GAUGE = "paciolus_export_share_oldest_undeleted_seconds"


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


class _FakeR2:
    """Dict-backed bucket with switchable delete failure."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.modified: dict[str, datetime] = {}
        self.delete_calls: list[str] = []
        self.fail_deletes = 0  # number of upcoming deletes that fail; -1 = all
        self.after_upload: Any = None  # hook run once an upload has landed

    def upload(self, share_token_hash: str, data: bytes, content_type: str) -> str:
        key = f"shares/{share_token_hash}"
        self.objects[key] = data
        self.modified[key] = datetime.now(UTC)
        if self.after_upload is not None:
            self.after_upload()
        return key

    def put(self, key: str, data: bytes, age: timedelta) -> None:
        """Place an object directly, as if uploaded ``age`` ago."""
        self.objects[key] = data
        self.modified[key] = datetime.now(UTC) - age

    def list_objects(self, prefix: str = "shares/") -> list[tuple[str, datetime]]:
        return [(k, self.modified.get(k, datetime.now(UTC))) for k in self.objects if k.startswith(prefix)]

    def download(self, object_key: str) -> bytes | None:
        return self.objects.get(object_key)

    def delete(self, object_key: str) -> bool:
        self.delete_calls.append(object_key)
        if self.fail_deletes:
            if self.fail_deletes > 0:
                self.fail_deletes -= 1
            return False
        self.objects.pop(object_key, None)
        return True


@pytest.fixture
def fake_r2(monkeypatch: pytest.MonkeyPatch) -> _FakeR2:
    fake = _FakeR2()
    monkeypatch.setattr(export_share_storage, "is_configured", lambda: True)
    monkeypatch.setattr(export_share_storage, "upload", fake.upload)
    monkeypatch.setattr(export_share_storage, "download", fake.download)
    monkeypatch.setattr(export_share_storage, "delete", fake.delete)
    monkeypatch.setattr(export_share_storage, "list_objects", fake.list_objects, raising=False)
    return fake


@pytest.fixture
def api(db_session: Session) -> Iterator[httpx.AsyncClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    finally:
        app.dependency_overrides.clear()


def _auth(user: User) -> dict[str, str]:
    token, _ = create_access_token(user.id, user.email, user.password_changed_at)
    return {"Authorization": f"Bearer {token}"}


async def _create_share(api: httpx.AsyncClient, user: User, data: bytes = PDF_BYTES, fmt: str = "pdf") -> str:
    r = await api.post(
        "/export-sharing/create",
        json={
            "tool_name": "trial_balance",
            "export_format": fmt,
            "export_data_b64": base64.b64encode(data).decode(),
        },
        headers=_auth(user),
    )
    assert r.status_code == 200, r.text
    return str(r.json()["share_token"])


def _row(db: Session, token: str) -> ExportShare | None:
    db.expire_all()
    return db.query(ExportShare).filter_by(share_token_hash=hashlib.sha256(token.encode()).hexdigest()).one_or_none()


def _expire(db: Session, token: str, ago: timedelta = timedelta(seconds=1)) -> ExportShare:
    share = _row(db, token)
    assert share is not None
    share.expires_at = datetime.now(UTC) - ago
    db.commit()
    return share


def _key(token: str) -> str:
    return f"shares/{hashlib.sha256(token.encode()).hexdigest()}"


def _firm_with_member(db: Session, make_user: Any) -> tuple[User, User, OrganizationMember]:
    owner = make_user(email="s880_owner@example.com", tier=UserTier.PROFESSIONAL)
    member = make_user(email="s880_member@example.com", tier=UserTier.PROFESSIONAL)
    sub = Subscription(
        user_id=owner.id,
        tier="professional",
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        seat_count=7,
        additional_seats=0,
    )
    db.add(sub)
    db.flush()
    org = Organization(name="S880 Firm", slug="s880-firm", owner_user_id=owner.id, subscription_id=sub.id)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    membership = OrganizationMember(organization_id=org.id, user_id=member.id, role=OrgRole.MEMBER)
    db.add(membership)
    owner.organization_id = org.id
    member.organization_id = org.id
    db.commit()
    return owner, member, membership


# ---------------------------------------------------------------------------
# 5A — cadence
# ---------------------------------------------------------------------------


class TestPurgeCadence:
    def test_share_purge_job_runs_every_ten_minutes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import apscheduler.schedulers.background as bg

        import cleanup_scheduler

        jobs: dict[str, dict[str, Any]] = {}

        class _Recorder:
            def __init__(self, *a: Any, **kw: Any) -> None:
                pass

            def add_job(self, func: Any, trigger: str, **kw: Any) -> None:
                jobs[kw["id"]] = kw

            def start(self) -> None:
                pass

        monkeypatch.setattr(bg, "BackgroundScheduler", _Recorder)
        monkeypatch.setattr(cleanup_scheduler, "CLEANUP_SCHEDULER_ENABLED", True)
        try:
            cleanup_scheduler.init_scheduler()
        finally:
            cleanup_scheduler._scheduler = None

        purge = jobs["expired_export_shares"]
        assert purge.get("minutes") == 10 and "hours" not in purge
        assert cleanup_scheduler._EXPECTED_INTERVALS["expired_export_shares"] == timedelta(minutes=10)


# ---------------------------------------------------------------------------
# 5A — expiry deletes the file
# ---------------------------------------------------------------------------


class TestExpiryDeletesTheFile:
    @pytest.mark.asyncio
    async def test_share_made_just_after_a_pass_link_and_file_both_end(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="s880_cadence@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        assert purge_expired_export_shares(db_session) == 0  # the pass that just ran

        # Before expiry: link works, file stored.
        assert (await api.get(f"/export-sharing/{token}")).status_code == 200
        assert _key(token) in fake_r2.objects

        # Across expiry, never opened: the next pass (≤10 min later) removes both.
        _expire(db_session, token)
        assert purge_expired_export_shares(db_session) == 1
        assert _key(token) not in fake_r2.objects
        assert _row(db_session, token) is None
        assert (await api.get(f"/export-sharing/{token}")).status_code == 404

    @pytest.mark.asyncio
    async def test_opening_an_expired_link_deletes_its_file_then(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        user = make_user(email="s880_open@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        _expire(db_session, token)

        r = await api.get(f"/export-sharing/{token}")
        assert r.status_code == 410
        assert _key(token) not in fake_r2.objects  # no cleanup pass ran
        assert _row(db_session, token) is None

    @pytest.mark.asyncio
    async def test_expired_open_with_failing_delete_keeps_the_row_for_the_purge(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="s880_open_fail@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        _expire(db_session, token)
        fake_r2.fail_deletes = 1

        assert (await api.post(f"/export-sharing/{token}/download", json={})).status_code == 410
        assert _key(token) in fake_r2.objects
        assert _row(db_session, token) is not None  # still tracked

        assert purge_expired_export_shares(db_session) == 1
        assert _key(token) not in fake_r2.objects


# ---------------------------------------------------------------------------
# 5A — failed deletes: retried, measured, warned
# ---------------------------------------------------------------------------


class TestOverdueFiles:
    @pytest.mark.asyncio
    async def test_failing_deletes_are_retried_and_warn_past_one_hour(
        self,
        api: httpx.AsyncClient,
        db_session: Session,
        make_user: Any,
        fake_r2: _FakeR2,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="s880_overdue@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        _expire(db_session, token, ago=timedelta(minutes=61))
        fake_r2.fail_deletes = -1

        with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
            assert purge_expired_export_shares(db_session) == 0
            assert purge_expired_export_shares(db_session) == 0  # retried
        assert fake_r2.delete_calls.count(_key(token)) == 2
        assert (PARSER_REGISTRY.get_sample_value(_OVERDUE_GAUGE) or 0) >= 61 * 60
        assert any("export_share_file_overdue" in r.getMessage() for r in caplog.records)

        fake_r2.fail_deletes = 0
        assert purge_expired_export_shares(db_session) == 1
        assert _key(token) not in fake_r2.objects
        assert PARSER_REGISTRY.get_sample_value(_OVERDUE_GAUGE) == 0

    @pytest.mark.asyncio
    async def test_no_warning_inside_the_hour(
        self,
        api: httpx.AsyncClient,
        db_session: Session,
        make_user: Any,
        fake_r2: _FakeR2,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="s880_recent@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        _expire(db_session, token, ago=timedelta(minutes=5))
        fake_r2.fail_deletes = -1

        with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
            purge_expired_export_shares(db_session)
        age = PARSER_REGISTRY.get_sample_value(_OVERDUE_GAUGE) or 0
        assert 5 * 60 <= age < 60 * 60
        assert not any("export_share_file_overdue" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# 5A — revocation decision
# ---------------------------------------------------------------------------


class TestRevocation:
    @pytest.mark.asyncio
    async def test_member_removal_revokes_the_link_and_deletes_the_file(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        owner, member, membership = _firm_with_member(db_session, make_user)
        token = await _create_share(api, member)
        assert _row(db_session, token).organization_id == owner.organization_id  # type: ignore[union-attr]

        r = await api.delete(f"/organization/members/{membership.id}", headers=_auth(owner))
        assert r.status_code == 200, r.text

        assert (await api.get(f"/export-sharing/{token}")).status_code == 404
        assert _key(token) not in fake_r2.objects  # deleted at removal, not at the next pass

    @pytest.mark.asyncio
    async def test_download_rechecks_the_creator_is_still_in_the_firm(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        """A membership that ends by any path (not only the remove route) ends the link."""
        _owner, member, membership = _firm_with_member(db_session, make_user)
        token = await _create_share(api, member)
        db_session.delete(membership)
        db_session.commit()

        assert (await api.get(f"/export-sharing/{token}")).status_code == 404
        assert _key(token) not in fake_r2.objects
        assert _row(db_session, token) is None  # file confirmed gone, so the row went too

    @pytest.mark.asyncio
    async def test_recheck_with_failing_delete_revokes_and_leaves_the_row_for_the_purge(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        _owner, member, membership = _firm_with_member(db_session, make_user)
        token = await _create_share(api, member)
        db_session.delete(membership)
        db_session.commit()
        fake_r2.fail_deletes = 1

        assert (await api.get(f"/export-sharing/{token}")).status_code == 404
        share = _row(db_session, token)
        assert share is not None and share.revoked_at is not None
        assert (await api.get(f"/export-sharing/{token}")).status_code == 404  # stays dead

    @pytest.mark.asyncio
    async def test_account_closure_removes_links_and_files(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        from services.account_erasure import erase_account

        user = make_user(email="s880_close@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        erase_account(db_session, user)

        assert _key(token) not in fake_r2.objects
        assert _row(db_session, token) is None
        assert (await api.get(f"/export-sharing/{token}")).status_code == 404

    @pytest.mark.asyncio
    async def test_downgrade_does_not_revoke(
        self, api: httpx.AsyncClient, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        user = make_user(email="s880_downgrade@example.com", tier=UserTier.PROFESSIONAL)
        token = await _create_share(api, user)
        user.tier = UserTier.FREE
        db_session.commit()

        r = await api.get(f"/export-sharing/{token}")
        assert r.status_code == 200
        assert r.content == PDF_BYTES


# ---------------------------------------------------------------------------
# 5B — no stored file without a durable record
# ---------------------------------------------------------------------------


def _patch_bucket(monkeypatch: pytest.MonkeyPatch, fake: _FakeR2) -> None:
    monkeypatch.setattr(export_share_storage, "is_configured", lambda: True)
    monkeypatch.setattr(export_share_storage, "upload", fake.upload)
    monkeypatch.setattr(export_share_storage, "download", fake.download)
    monkeypatch.setattr(export_share_storage, "delete", fake.delete)
    monkeypatch.setattr(export_share_storage, "list_objects", fake.list_objects, raising=False)


def _fail_next_commit(db: Session) -> None:
    """Make the session's next commit raise once (as a dropped DB connection would)."""
    real_commit = db.commit

    def commit() -> None:
        db.commit = real_commit  # type: ignore[method-assign]
        db.rollback()
        raise RuntimeError("simulated commit failure")

    db.commit = commit  # type: ignore[method-assign]


async def _create_expecting_500(db: Session, user: User) -> None:
    app.dependency_overrides[get_db] = lambda: db
    try:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/export-sharing/create",
                json={
                    "tool_name": "trial_balance",
                    "export_format": "pdf",
                    "export_data_b64": base64.b64encode(PDF_BYTES).decode(),
                },
                headers=_auth(user),
            )
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 500, r.text


class TestFailedCreateLeavesNoUntrackedFile:
    @pytest.mark.asyncio
    async def test_commit_fails_after_upload_and_first_delete_fails_record_survives_restart(
        self, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="s880_orphan@example.com", tier=UserTier.PROFESSIONAL)
        fake_r2.fail_deletes = 1  # the create handler's own clean-up delete fails
        fake_r2.after_upload = lambda: _fail_next_commit(db_session)

        await _create_expecting_500(db_session, user)
        assert len(fake_r2.objects) == 1  # the upload landed and the delete failed
        (key,) = fake_r2.objects

        # "Restart": nothing in memory survives — only what was committed.
        db_session.expire_all()
        pending = db_session.query(ExportShare).filter_by(object_key=key).one()
        assert pending.upload_pending is True  # never became a live link

        # The pending record is not a working link and is not listed.
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                assert (await client.get("/export-sharing/", headers=_auth(user))).json() == []
        finally:
            app.dependency_overrides.clear()

        # Once the grace period has passed, the purge removes the file, then the record.
        pending.created_at = datetime.now(UTC) - timedelta(minutes=30)
        db_session.commit()
        assert purge_expired_export_shares(db_session) == 1
        assert key not in fake_r2.objects
        db_session.expire_all()
        assert db_session.query(ExportShare).filter_by(object_key=key).one_or_none() is None

    @pytest.mark.asyncio
    async def test_commit_fails_after_upload_and_delete_works_nothing_is_left(
        self, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        user = make_user(email="s880_orphan_ok@example.com", tier=UserTier.PROFESSIONAL)
        fake_r2.after_upload = lambda: _fail_next_commit(db_session)

        await _create_expecting_500(db_session, user)
        assert fake_r2.objects == {}
        db_session.expire_all()
        assert db_session.query(ExportShare).filter_by(user_id=user.id).count() == 0

    def test_a_pending_record_inside_its_grace_period_is_left_alone(
        self, db_session: Session, make_user: Any, fake_r2: _FakeR2
    ) -> None:
        """An upload in flight must not be deleted under the request that is making it."""
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="s880_inflight@example.com", tier=UserTier.PROFESSIONAL)
        key = "shares/" + "c" * 64
        fake_r2.put(key, PDF_BYTES, age=timedelta(seconds=5))
        db_session.add(
            ExportShare(
                user_id=user.id,
                share_token_hash="c" * 64,
                tool_name="trial_balance",
                export_format="pdf",
                object_key=key,
                upload_pending=True,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        db_session.commit()
        assert purge_expired_export_shares(db_session) == 0
        assert key in fake_r2.objects


class TestReconciliation:
    def test_objects_with_no_record_are_deleted_tracked_and_recent_ones_kept(
        self, db_session: Session, make_user: Any, fake_r2: _FakeR2, caplog: pytest.LogCaptureFixture
    ) -> None:
        from cleanup_scheduler import reconcile_export_share_objects

        user = make_user(email="s880_reconcile@example.com", tier=UserTier.PROFESSIONAL)
        tracked = "shares/" + "d" * 64
        orphan = "shares/" + "e" * 64
        recent_orphan = "shares/" + "f" * 64
        fake_r2.put(tracked, PDF_BYTES, age=timedelta(hours=2))
        fake_r2.put(orphan, PDF_BYTES, age=timedelta(hours=2))
        fake_r2.put(recent_orphan, PDF_BYTES, age=timedelta(seconds=30))
        db_session.add(
            ExportShare(
                user_id=user.id,
                share_token_hash="d" * 64,
                tool_name="trial_balance",
                export_format="pdf",
                object_key=tracked,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        db_session.commit()

        with caplog.at_level(logging.WARNING, logger="cleanup_scheduler"):
            assert reconcile_export_share_objects(db_session) == 1
        assert orphan not in fake_r2.objects
        assert tracked in fake_r2.objects
        assert recent_orphan in fake_r2.objects  # may belong to a create still in flight
        assert any("export_share_untracked_objects" in r.getMessage() for r in caplog.records)

    def test_reconciliation_is_scheduled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import apscheduler.schedulers.background as bg

        import cleanup_scheduler

        ids: list[str] = []

        class _Recorder:
            def __init__(self, *a: Any, **kw: Any) -> None:
                pass

            def add_job(self, func: Any, trigger: str, **kw: Any) -> None:
                ids.append(kw["id"])

            def start(self) -> None:
                pass

        monkeypatch.setattr(bg, "BackgroundScheduler", _Recorder)
        monkeypatch.setattr(cleanup_scheduler, "CLEANUP_SCHEDULER_ENABLED", True)
        try:
            cleanup_scheduler.init_scheduler()
        finally:
            cleanup_scheduler._scheduler = None
        assert "reconcile_export_share_objects" in ids
