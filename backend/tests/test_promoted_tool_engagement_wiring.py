"""
Engagement wiring for the six Sprint-689 promoted tools — Sprint 787b.

Sprint 787 made these six tools *representable*: it added their members to
`ToolName` and the Postgres enum, classified them in the convergence taxonomy,
and fixed the "Tools Executed: n of 13" denominator. It did not wire them up,
and the PR #174 review caught that overclaim. None of the six routes called
`maybe_record_tool_run`, and none accepted an `engagement_id`, so a run of any
of them was invisible to the workpaper index, the Anomaly Summary and the
completion gate.

This file is the verification bar from the Sprint 787b filing, stated as a test:
*a run of each tool against an engagement produces a ToolRun row.*

Two deliberate design decisions are pinned here rather than left implicit:

1. **`composite_score` is None for all six.** None of the six engines computes
   one. The sprint filing said explicitly not to invent a score to fill the
   parameter, so a test asserts it stays None — otherwise a later change could
   quietly start writing a fabricated number into a workpaper.
2. **`flagged_accounts` is None for all six.** `shared/account_extractors.py`
   has no extractor for any of them, which is not an oversight — Sprint 787's
   convergence classification established that `CONVERGENCE_TOOLS` is exactly
   the key set of `ACCOUNT_EXTRACTORS`, because a tool can only contribute to
   the Convergence Index if something can pull GL accounts from its result.
   A role-permission matrix and a 90-day cash projection do not produce
   GL-account-level output.

**On the session passed into the background task.** The success path records via
`background_tasks.add_task(maybe_record_tool_run, db, ...)`, handing a
request-scoped `Session` to a callable that runs after the handler returns. That
is the house pattern across all seven previously-wired routes, but it is only
safe if the task runs *before* `get_db`'s `finally: db.close()`. These tests
cannot settle it — `_override` installs `get_db` as `lambda: db_session`, a plain
callable rather than a generator, so no teardown happens at all.

It was settled separately, against the installed FastAPI, and the answer is that
the ordering is favourable: background tasks run **before** `yield`-dependency
teardown, so the session is still open. `TestBackgroundTaskOrderingContract`
below pins that as a contract test rather than leaving it as a verified-once
fact, because **Sprint 786b plans to bump FastAPI 0.136 → 0.150**. If a release
in that range flips the ordering, 13 routes stop recording tool runs on their
success path and every test in this file still passes, since they all override
`get_db` with a non-generator.
"""

import json
import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user, require_verified_user
from database import get_db
from engagement_model import ToolName, ToolRun, ToolRunStatus
from main import app

# ---------------------------------------------------------------------------
# Minimum-viable payloads, lifted from each tool's own route test so these
# exercise the same engine happy paths rather than a second set of fixtures.
# ---------------------------------------------------------------------------


def _sod_payload() -> dict:
    return {
        "user_assignments": [{"user_id": "u1", "user_name": "Alice", "role_codes": ["accountant"]}],
        "role_permissions": [{"role_code": "accountant", "permissions": ["JE_create", "JE_post"]}],
        "extra_rules": [],
    }


def _intercompany_payload() -> dict:
    return {
        "entities": [
            {
                "entity_id": "A",
                "entity_name": "Parent",
                "accounts": [{"account": "Due From B", "debit": "1000.00", "credit": "0", "counterparty_entity": "B"}],
            },
            {
                "entity_id": "B",
                "entity_name": "Sub",
                "accounts": [{"account": "Due To A", "debit": "0", "credit": "1000.00", "counterparty_entity": "A"}],
            },
        ],
        "tolerance": "1.00",
    }


def _w2_payload() -> dict:
    return {
        "tax_year": 2025,
        "employees": [
            {
                "employee_id": "E001",
                "employee_name": "Alice",
                "federal_wages": "80000.00",
                "federal_withholding": "12000.00",
                "ss_wages": "80000.00",
                "ss_tax_withheld": "4960.00",
                "medicare_wages": "80000.00",
                "medicare_tax_withheld": "1160.00",
            }
        ],
        "w2_drafts": [],
        "form_941_quarters": [],
        "tolerance": "1.00",
    }


def _form_1099_payload() -> dict:
    return {
        "tax_year": 2025,
        "vendors": [
            {"vendor_id": "V001", "vendor_name": "ACME Consulting LLC", "tin": "12-3456789", "entity_type": "llc"}
        ],
        "payments": [
            {"vendor_id": "V001", "amount": "750.00", "payment_category": "nonemployee_comp", "payment_method": "check"}
        ],
    }


def _book_to_tax_payload() -> dict:
    return {
        "tax_year": 2025,
        "book_pretax_income": "500000.00",
        "total_assets": "5000000.00",
        "federal_tax_rate": "0.21",
        "state_tax_rate": "0.05",
        "adjustments": [
            {"label": "Meals (50%)", "amount": "10000.00", "difference_type": "permanent", "direction": "add"}
        ],
        "rollforward": {"beginning_dta": "0", "beginning_dtl": "0"},
    }


def _cash_flow_payload() -> dict:
    # Relative to nothing — the engine has no wall-clock dependency (verified:
    # no date.today()/datetime.now() anywhere in cash_flow_projector_engine.py),
    # so these literals cannot become a time bomb the way the Sprint 785-era
    # inventory fixture did.
    return {
        "opening_balance": "100000.00",
        "start_date": "2026-05-01",
        "ar_aging": {
            "current": "50000",
            "days_1_30": "25000",
            "days_31_60": "10000",
            "days_61_90": "0",
            "days_over_90": "0",
        },
        "ap_aging": {
            "current": "20000",
            "days_1_30": "10000",
            "days_31_60": "0",
            "days_61_90": "0",
            "days_over_90": "0",
        },
        "recurring_flows": [
            {"label": "Payroll", "amount": "-30000", "frequency": "biweekly", "first_date": "2026-05-01"}
        ],
        "min_safe_cash": "10000",
    }


# (endpoint, payload factory, ToolName member)
PROMOTED_TOOLS = [
    ("/audit/sod/analyze", _sod_payload, ToolName.SOD_CHECKER),
    ("/audit/intercompany-elimination", _intercompany_payload, ToolName.INTERCOMPANY_ELIMINATION),
    ("/audit/w2-reconciliation", _w2_payload, ToolName.W2_RECONCILIATION),
    ("/audit/form-1099", _form_1099_payload, ToolName.FORM_1099),
    ("/audit/book-to-tax", _book_to_tax_payload, ToolName.BOOK_TO_TAX),
    ("/audit/cash-flow-projector", _cash_flow_payload, ToolName.CASH_FLOW_PROJECTOR),
]

IDS = [t[2].value for t in PROMOTED_TOOLS]


def _override(user, db_session) -> None:
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session


def _tool_runs(db_session, engagement_id: int, tool: ToolName) -> list[ToolRun]:
    return (
        db_session.query(ToolRun)
        .filter(ToolRun.engagement_id == engagement_id, ToolRun.tool_name == tool)
        .order_by(ToolRun.run_number)
        .all()
    )


@pytest.mark.usefixtures("bypass_csrf")
class TestPromotedToolsRecordAgainstEngagement:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_run_against_engagement_creates_tool_run(
        self, db_session, make_user, make_engagement, endpoint, payload_fn, tool
    ):
        """The Sprint 787b verification bar, one case per tool."""
        user = make_user(email=f"wire_{tool.value}@example.com")
        engagement = make_engagement(user=user)
        _override(user, db_session)
        try:
            assert _tool_runs(db_session, engagement.id, tool) == []

            payload = {**payload_fn(), "engagement_id": engagement.id}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(endpoint, json=payload)
            assert response.status_code == 200, response.text

            runs = _tool_runs(db_session, engagement.id, tool)
            assert len(runs) == 1, f"{tool.value} did not record a ToolRun"
            run = runs[0]
            assert run.status == ToolRunStatus.COMPLETED
            assert run.run_number == 1
            # Both None by design — see the module docstring.
            assert run.composite_score is None
            assert run.flagged_accounts is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_run_without_engagement_id_records_nothing(
        self, db_session, make_user, make_engagement, endpoint, payload_fn, tool
    ):
        """`engagement_id` is optional and omitting it must stay a no-op on the
        workpaper trail — the tool still runs, it just is not filed anywhere."""
        user = make_user(email=f"nowire_{tool.value}@example.com")
        engagement = make_engagement(user=user)
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(endpoint, json=payload_fn())
            assert response.status_code == 200, response.text
            assert _tool_runs(db_session, engagement.id, tool) == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_repeat_runs_increment_run_number(
        self, db_session, make_user, make_engagement, endpoint, payload_fn, tool
    ):
        """`record_tool_run` auto-increments run_number per (engagement, tool).
        Asserted per tool because the slug is what keys that counter — a
        copy-paste slug error would land both runs under the wrong tool and
        still produce two rows."""
        user = make_user(email=f"repeat_{tool.value}@example.com")
        engagement = make_engagement(user=user)
        _override(user, db_session)
        try:
            payload = {**payload_fn(), "engagement_id": engagement.id}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                first = await client.post(endpoint, json=payload)
                second = await client.post(endpoint, json=payload)
            assert first.status_code == 200
            assert second.status_code == 200

            runs = _tool_runs(db_session, engagement.id, tool)
            assert [r.run_number for r in runs] == [1, 2]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_foreign_engagement_id_is_ignored_not_recorded(
        self, db_session, make_user, make_engagement, endpoint, payload_fn, tool
    ):
        """An engagement belonging to someone else must not receive a ToolRun.

        `maybe_record_tool_run` resolves the engagement through
        `EngagementManager.get_engagement(user_id, engagement_id)` and skips when
        it does not resolve, so this is an authorization boundary and not merely
        a data-hygiene nicety. Worth a test on all six at once, because the
        wiring passed `payload.engagement_id` straight through from the request
        body — an attacker-chosen integer.
        """
        owner = make_user(email=f"owner_{tool.value}@example.com")
        intruder = make_user(email=f"intruder_{tool.value}@example.com")
        victim_engagement = make_engagement(user=owner)
        _override(intruder, db_session)
        try:
            payload = {**payload_fn(), "engagement_id": victim_engagement.id}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(endpoint, json=payload)
            # The analysis itself is not privileged — only the filing is.
            assert response.status_code == 200, response.text
            assert _tool_runs(db_session, victim_engagement.id, tool) == []
        finally:
            app.dependency_overrides.clear()


class TestEveryPromotedToolIsCovered:
    """Guard against this file going stale.

    Sprint 787 added six members to `ToolName`; Sprint 787b wires exactly those
    six. If a seventh tool is promoted and wired without being added here, the
    sprint's verification bar silently stops covering it — which is the same
    failure mode that let the original six sit unwired for six months behind a
    sprint marked complete.
    """

    def test_all_six_sprint_689_tools_are_exercised(self):
        expected = {
            ToolName.SOD_CHECKER,
            ToolName.INTERCOMPANY_ELIMINATION,
            ToolName.W2_RECONCILIATION,
            ToolName.FORM_1099,
            ToolName.BOOK_TO_TAX,
            ToolName.CASH_FLOW_PROJECTOR,
        }
        assert {t[2] for t in PROMOTED_TOOLS} == expected

    def test_every_route_that_accepts_an_engagement_run_also_records_it(self):
        """A route that accepts an `engagement_id` on a *run* and then records
        nothing is worse than one that never offered the parameter: the caller
        is told the run was filed and it was not. That is precisely the state
        the six promoted tools were in. Checks the implication repo-wide.

        Two refinements over the obvious version of this check, both of which
        its first draft got wrong by flagging nine false positives:

        1. **Only body parameters count.** `engagement_id` arriving as
           `Query(...)` is a filter on a read — `activity.py` scoping the
           activity feed, `trends.py` scoping industry ratios. Nothing should be
           recorded for those. A run arrives as `Form(...)` or in a JSON body.
        2. **Delegation has to be followed, but narrowly.** Most routes never
           call the recorder themselves: the six testing tools go through
           `shared/testing_route.py::run_single_file_testing`, and the
           diagnostics endpoints through
           `services/audit/file_tool_scaffold.py::execute_file_tool`. Both of
           those call `maybe_record_tool_run` and both take `engagement_id`.

        The second refinement had to be made twice. "Imports from a module that
        calls the recorder" is vacuous: `shared/testing_route.py` holds both
        `enforce_tool_access` — which nearly every route imports — and
        `run_single_file_testing`, so module-level resolution marked almost
        every route as delegating and the guard silently stopped testing
        anything. Regression-proving it by stripping the recorder out of
        `routes/form_1099.py` caught that: the guard passed. So the check is on
        the *called function*, from an explicit set, verified below to actually
        record.
        """
        import pathlib
        import re

        backend = pathlib.Path(__file__).resolve().parent.parent

        # Helpers that take engagement_id and record on the caller's behalf.
        # test_recording_helpers_actually_record keeps this honest.
        DELEGATES = ("run_single_file_testing", "execute_file_tool")

        offenders: list[str] = []
        for path in sorted((backend / "routes").glob("*.py")):
            src = path.read_text(encoding="utf-8")

            # (1) does any endpoint take engagement_id from the request body?
            #     Query(...) is a filter on a read, not a run.
            accepts_run_link = re.search(r"\bengagement_id\s*:\s*Optional\[int\]\s*=\s*(Form|Field)\(", src) is not None
            if not accepts_run_link:
                continue

            # (2) records directly, or calls a helper that does?
            if "maybe_record_tool_run" in src:
                continue
            if any(re.search(rf"\b{d}\s*\(", src) for d in DELEGATES):
                continue
            offenders.append(path.name)

        assert offenders == [], (
            "These route modules accept an engagement_id on a run but neither "
            "call maybe_record_tool_run nor delegate to a helper that does, so "
            f"the engagement link is accepted and dropped: {offenders}"
        )

    def test_recording_helpers_actually_record(self):
        """Pins the premise the delegation allowlist rests on.

        If `run_single_file_testing` or `execute_file_tool` stopped recording,
        the guard above would keep passing for every route that delegates to
        them — about half the catalog — while nothing was being filed. Assert
        the property at the source instead of trusting the name.
        """
        import pathlib

        backend = pathlib.Path(__file__).resolve().parent.parent
        for rel, func in (
            ("shared/testing_route.py", "run_single_file_testing"),
            ("services/audit/file_tool_scaffold.py", "execute_file_tool"),
        ):
            src = (backend / rel).read_text(encoding="utf-8")
            assert f"def {func}(" in src, f"{func} no longer lives in {rel}"
            assert "maybe_record_tool_run" in src, (
                f"{rel} no longer calls maybe_record_tool_run, so treating "
                f"{func} as a recording delegate is wrong — every route that "
                "relies on it has silently stopped filing tool runs."
            )


class TestFailurePathRecording:
    """A failed run must be filed as FAILED, not omitted.

    An engagement whose workpaper trail silently drops failures reads as though
    the tool was never run, which is exactly the state Sprint 787b was fixing.
    SoD is the interesting case: unlike 689c–g it had no try/except at all,
    because its engine does not raise on bad input — `_build_extra_rule` does,
    as a 400 for an unrecognised severity.
    """

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_sod_invalid_severity_records_failed_run(self, db_session, make_user, make_engagement):
        user = make_user(email="sod_fail@example.com")
        engagement = make_engagement(user=user)
        _override(user, db_session)
        try:
            payload = {
                **_sod_payload(),
                "engagement_id": engagement.id,
                "extra_rules": [
                    {
                        "code": "X-01",
                        "title": "Bad severity",
                        "severity": "catastrophic",  # not high|medium|low
                        "permissions_required": ["a"],
                        "permissions_alternate": ["b"],
                        "mitigation": "",
                        "rationale": "",
                    }
                ],
            }
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/sod/analyze", json=payload)
            assert response.status_code == 400

            runs = _tool_runs(db_session, engagement.id, ToolName.SOD_CHECKER)
            assert len(runs) == 1
            assert runs[0].status == ToolRunStatus.FAILED
            # record_tool_run drops score and flagged accounts on failure.
            assert runs[0].composite_score is None
            assert runs[0].flagged_accounts is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_intercompany_input_error_records_failed_run(self, db_session, make_user, make_engagement):
        """The 689c–g shape: a domain InputError raised by the engine."""
        user = make_user(email="ic_fail@example.com")
        engagement = make_engagement(user=user)
        _override(user, db_session)
        try:
            payload = _intercompany_payload()
            payload["engagement_id"] = engagement.id
            # Duplicate entity_id — rejected by the engine as an input error.
            payload["entities"][1]["entity_id"] = "A"
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/intercompany-elimination", json=payload)
            assert response.status_code == 400, response.text

            runs = _tool_runs(db_session, engagement.id, ToolName.INTERCOMPANY_ELIMINATION)
            assert len(runs) == 1
            assert runs[0].status == ToolRunStatus.FAILED
        finally:
            app.dependency_overrides.clear()


class TestToolActivityFeed:
    """`maybe_record_tool_run` has two surfaces: the engagement-linked ToolRun
    and the always-written cross-engagement `ToolActivity` feed that powers the
    multi-tool dashboard. Before Sprint 787b these six tools appeared in
    neither, so a customer who ran only promoted tools saw an empty dashboard.

    These cases prove the recorder is *called*, not that the row is durable —
    `_override` reuses one session whose autoflush makes a pending insert
    visible to the follow-up query, so they passed even while every row was
    being discarded at `db.close()`. Durability is covered by
    `TestRecorderDurabilityAndForeignKeys` below, through the real `get_db`.
    """

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_activity_row_written_even_without_engagement(
        self, db_session, make_user, endpoint, payload_fn, tool
    ):
        from models import ToolActivity

        user = make_user(email=f"activity_{tool.value}@example.com")
        _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(endpoint, json=payload_fn())
            assert response.status_code == 200, response.text

            rows = (
                db_session.query(ToolActivity)
                .filter(ToolActivity.user_id == user.id, ToolActivity.tool_name == tool.value)
                .all()
            )
            assert len(rows) == 1
            assert rows[0].engagement_id is None
        finally:
            app.dependency_overrides.clear()


def test_flagged_accounts_is_json_when_present_sanity():
    """Documents the storage shape the None assertions above are measured
    against: `record_tool_run` JSON-encodes a non-empty list and stores None
    otherwise, so `flagged_accounts is None` genuinely means "nothing filed"
    rather than "an empty list was filed"."""
    assert json.dumps(["1000", "2000"]) == '["1000", "2000"]'


class TestRecorderDurabilityAndForeignKeys:
    """Two defects the PR #182 review found in `shared/tool_run_recorder.py`.

    Both were pre-existing and shared by all thirteen wired routes, and both
    made claims elsewhere in this file untrue. Exercised here through the real
    `get_db` generator where durability is the point, so the session actually
    closes.
    """

    def test_activity_row_survives_the_session_closing(self, make_user):
        """Review finding: the pending ToolActivity row was discarded.

        `get_db` ends in a bare `db.close()` and not one of the thirteen callers
        committed, so for a run with no `engagement_id` the row never reached
        the database. Measured at zero rows surviving before the fix.
        """
        from database import SessionLocal, get_db
        from models import ToolActivity, User, UserTier
        from shared.tool_run_recorder import maybe_record_tool_run

        setup = SessionLocal()
        try:
            user = User(
                email="durability_probe@example.com",
                name="Durability Probe",
                hashed_password="$2b$12$fakehashvalue",
                tier=UserTier.PROFESSIONAL,
                is_active=True,
                is_verified=True,
            )
            setup.add(user)
            setup.commit()
            uid = user.id
        finally:
            setup.close()

        try:
            # The exact get_db lifecycle: yield, use, then run its finally block.
            gen = get_db()
            db = next(gen)
            maybe_record_tool_run(db, None, uid, "sod_checker", True, None, None)
            try:
                next(gen)
            except StopIteration:
                pass

            verify = SessionLocal()
            try:
                rows = verify.query(ToolActivity).filter(ToolActivity.user_id == uid).all()
                assert len(rows) == 1, (
                    "The ToolActivity row did not survive get_db's db.close(), so every "
                    "engagement-less tool run across all thirteen wired routes is missing "
                    "from the multi-tool dashboard feed."
                )
                assert rows[0].tool_name == "sod_checker"
                assert rows[0].engagement_id is None
            finally:
                verify.close()
        finally:
            cleanup = SessionLocal()
            try:
                cleanup.query(ToolActivity).filter(ToolActivity.user_id == uid).delete()
                cleanup.query(User).filter(User.id == uid).delete()
                cleanup.commit()
            finally:
                cleanup.close()

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_nonexistent_engagement_id_does_not_500(self, db_session, make_user, endpoint, payload_fn, tool):
        """Review finding: a stale engagement id produced an IntegrityError.

        The recorder wrote `ToolActivity` carrying the caller-supplied id first
        and then queried for the engagement; that query's autoflush pushed the
        insert and violated the foreign key. Confirmed to raise on both the
        success and the failure path of every wired route, so any client holding
        a stale engagement id got a 500.

        The analysis itself is not privileged, so the correct behaviour is 200
        with nothing filed — matching the foreign-engagement case above.
        """
        user = make_user(email=f"stale_eng_{tool.value}@example.com")
        _override(user, db_session)
        try:
            payload = {**payload_fn(), "engagement_id": 999_999}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(endpoint, json=payload)
            assert response.status_code == 200, response.text
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_nonexistent_engagement_id_on_the_failure_path_still_returns_400(self, db_session, make_user):
        """The sharper half of the same defect: bad input *and* a stale id.

        The intended answer is a 400 about the malformed severity. The
        foreign-key violation replaced it with a 500 — input validation turned
        into a server error by a recording side effect.
        """
        user = make_user(email="stale_eng_failpath@example.com")
        _override(user, db_session)
        try:
            payload = {
                **_sod_payload(),
                "engagement_id": 999_999,
                "extra_rules": [
                    {
                        "code": "X-01",
                        "title": "Bad severity",
                        "severity": "catastrophic",
                        "permissions_required": ["a"],
                        "permissions_alternate": ["b"],
                        "mitigation": "",
                        "rationale": "",
                    }
                ],
            }
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/sod/analyze", json=payload)
            assert response.status_code == 400, response.text
        finally:
            app.dependency_overrides.clear()

    def test_activity_row_is_not_written_with_an_invalid_foreign_key(self, db_session, make_user):
        """Pins the ordering, not merely the absence of a crash.

        A future refactor could suppress the IntegrityError and still write a
        row pointing at a nonexistent engagement. The row must exist and be
        unlinked.
        """
        from models import ToolActivity
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="invalid_fk_probe@example.com")
        maybe_record_tool_run(db_session, 999_999, user.id, "sod_checker", True, None, None)

        rows = db_session.query(ToolActivity).filter(ToolActivity.user_id == user.id).all()
        assert len(rows) == 1
        assert rows[0].engagement_id is None, (
            "The activity row kept an engagement_id that does not resolve, which is an "
            "invalid foreign key waiting to fail on the next flush."
        )


class TestBackgroundTaskOrderingContract:
    """The framework assumption the *other* wired routes still depend on.

    Where `maybe_record_tool_run` is handed a request-scoped `Session` through
    `background_tasks.add_task`, that is only correct while FastAPI runs
    background tasks *before* tearing down `yield` dependencies — otherwise
    `get_db`'s `finally: db.close()` has already fired and the recorder writes
    through a closed session.

    Scope note (PR #183 review): the six routes in this file no longer use a
    background task at all. They record synchronously, because the task also
    runs *after* the response body is sent, which raced the UI's refresh — see
    `TestRecordingIsSynchronousOnTheSuccessPath`. So this contract now protects
    the seven previously-wired routes (ar_aging, audit_flux, audit_pipeline,
    bank_reconciliation, multi_period, sampling, three_way_match) plus the two
    shared helpers, not thirteen.

    Verified on FastAPI 0.136.1 and again on 0.162.0 (Sprint 786b): the task
    runs first. This test keeps it verified. If a future release flips the
    ordering, those routes silently stop recording while
    every other test here still passes — they all override `get_db` with a
    non-generator, so none of them exercises teardown at all.

    Deliberately built on a throwaway app rather than `main.app`: the property
    under test belongs to FastAPI's dependency/background-task machinery, and
    probing it through the real app would drag in auth, rate limiting and the
    database for no added signal.
    """

    @pytest.mark.asyncio
    async def test_background_tasks_run_before_yield_dependency_teardown(self):
        from fastapi import BackgroundTasks, Depends, FastAPI

        order: list[str] = []
        probe = FastAPI()

        def dependency_with_yield():
            try:
                yield "session"
            finally:
                order.append("teardown")

        def record(value: str) -> None:
            order.append(f"task:{value}")

        @probe.get("/probe")
        def endpoint(background_tasks: BackgroundTasks, dep=Depends(dependency_with_yield)):
            background_tasks.add_task(record, dep)
            return {"ok": True}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=probe), base_url="http://t") as client:
            assert (await client.get("/probe")).status_code == 200

        assert order == ["task:session", "teardown"], (
            "FastAPI's ordering of background tasks vs yield-dependency teardown has "
            f"changed (observed {order}). Every route using "
            "background_tasks.add_task(maybe_record_tool_run, db, ...) now hands the "
            "recorder a CLOSED session, so success-path tool runs are no longer filed. "
            "Fix the routes before taking this FastAPI version — see Sprint 786b."
        )


class TestRecordingIsSynchronousOnTheSuccessPath:
    """PR #183 review: the UI refresh raced the recording.

    Sprint 791's hooks call `refreshToolRuns()` as soon as the POST resolves.
    While the six routes recorded via `background_tasks.add_task`, that was a
    race the client lost more often than not: Starlette sends the response body
    (`responses.py:167`) *before* awaiting the background task (`:170`), so the
    GET could return a workpaper list that predated the row, replace the context
    state with it, and never refresh again — leaving the new entry invisible
    until a manual reload.

    Recording is now synchronous on the success path. These tests pin that,
    because the symptom is invisible from the server side: the row does appear,
    just a few milliseconds after the client stopped looking.
    """

    def test_no_promoted_route_defers_the_success_path_recording(self):
        """Structural: the six must not reintroduce a background task here.

        Asserted on the source rather than by timing, because a timing test
        against an in-process ASGI transport would pass either way — the task
        runs almost immediately, just not before the response.
        """
        import pathlib
        import re

        routes_dir = pathlib.Path(__file__).resolve().parent.parent / "routes"
        offenders: list[str] = []
        for _, _, tool in PROMOTED_TOOLS:
            # route module name differs from the slug for sod only
            name = "sod" if tool is ToolName.SOD_CHECKER else tool.value
            src = (routes_dir / f"{name}.py").read_text(encoding="utf-8")
            if re.search(r"background_tasks\.add_task\(\s*\n?\s*maybe_record_tool_run", src):
                offenders.append(f"{name}.py")

        assert offenders == [], (
            "These routes defer the success-path tool-run recording to a background task, "
            "which runs after the response body is sent. The Sprint 791 hooks refresh the "
            f"workpaper list the moment the POST resolves, so the new row is missed: {offenders}"
        )

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=IDS)
    async def test_tool_run_exists_by_the_time_the_response_returns(
        self, db_session, make_user, make_engagement, endpoint, payload_fn, tool
    ):
        """Behavioural counterpart: query immediately, with no await in between."""
        user = make_user(email=f"sync_{tool.value}@example.com")
        engagement = make_engagement(user=user)
        _override(user, db_session)
        try:
            payload = {**payload_fn(), "engagement_id": engagement.id}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(endpoint, json=payload)
            assert response.status_code == 200, response.text
            # The very next thing a client does is re-read the list.
            assert len(_tool_runs(db_session, engagement.id, tool)) == 1
        finally:
            app.dependency_overrides.clear()
