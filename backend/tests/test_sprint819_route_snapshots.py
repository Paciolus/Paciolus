"""Sprint 819: route-level output snapshots (promoted JSON tools + export endpoints).

Companion to ``test_sprint819_output_snapshots.py``. Captured on the code
*before* the Sprint 819 route refactors (``run_json_tool``, the export helper
consolidation, ``export/pipeline.py``'s ``_run_export``) and kept green across
them.

What is pinned per case:

* status code and response body (JSON exactly; CSV as text; binary bodies as a
  SHA-256 under a frozen clock),
* ``Content-Type``, ``Content-Disposition`` and ``Cache-Control``,
* for the promoted JSON tools, which ToolRun rows the request left behind
  (success / failure recording is part of the route's contract),
* for the diagnostic export pipeline, the ``log_secure_operation`` events.

``Content-Length`` is framing, not content: where present it must equal the
body length, which is asserted rather than snapshotted.

Regenerate only when a change is intended::

    SPRINT819_UPDATE_SNAPSHOTS=1 pytest tests/test_sprint819_route_snapshots.py
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import zipfile
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from freezegun import freeze_time

from auth import require_current_user, require_verified_user
from database import get_db
from engagement_model import ToolRun
from main import app
from models import Client, Industry
from tests.test_admin_dashboard_api import admin_user  # noqa: F401  (fixture)
from tests.test_export_diagnostics_routes import BASE_AUDIT, FIN_STMT_PAYLOAD, LEAD_SHEET_PAYLOAD
from tests.test_promoted_tool_engagement_wiring import PROMOTED_TOOLS
from tests.test_sprint819_output_snapshots import check_snapshot

FROZEN_NOW = "2026-06-30 12:00:00"

pytestmark = pytest.mark.usefixtures("bypass_csrf")


def _override(user: Any, db_session: Any) -> None:
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session


def _capture(response: httpx.Response) -> dict[str, Any]:
    headers = response.headers
    body = response.content
    if "content-length" in headers and "content-encoding" not in headers:
        assert int(headers["content-length"]) == len(body)
    ctype = headers.get("content-type", "")
    out: dict[str, Any] = {
        "status": response.status_code,
        "content_type": ctype,
        "content_disposition": headers.get("content-disposition"),
        "cache_control": headers.get("cache-control"),
        "content_encoding": headers.get("content-encoding"),
    }
    if ctype.startswith("application/json"):
        body_json = response.json()
        if isinstance(body_json, dict):
            body_json.pop("request_id", None)  # per-request random id
        out["json"] = body_json
    elif ctype.startswith("text/"):
        out["text"] = body.decode("utf-8")
    elif body[:4] == b"PK":
        # xlsx / zip: the archive bytes carry wall-clock entry timestamps, so pin
        # each member's content instead.
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            out["zip_members"] = {name: hashlib.sha256(zf.read(name)).hexdigest() for name in sorted(zf.namelist())}
    elif body[:5] == b"%PDF-":
        # PDF bytes are not stable run to run (object layout), so pin the text
        # of every page.
        from pypdf import PdfReader

        out["pdf_pages"] = [page.extract_text() for page in PdfReader(io.BytesIO(body)).pages]
    else:
        out["sha256"] = hashlib.sha256(body).hexdigest()
        out["length"] = len(body)
        out["magic"] = body[:4].hex()
    return out


async def _call(method: str, url: str, **kwargs: Any) -> httpx.Response:
    # Uncaught exceptions become the 500 a real server would send, so an error
    # path that escapes the route's own handling is pinned too.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)


# =============================================================================
# Promoted JSON tools (item 6: run_json_tool)
# =============================================================================


def _map_strings(obj: Any, fn: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _map_strings(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_map_strings(v, fn) for v in obj]
    if isinstance(obj, str):
        return fn(obj)
    return obj


def _is_decimal_text(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    return True


def _variants(payload: dict) -> dict[str, dict]:
    def empty_lists(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: ([] if isinstance(v, list) else empty_lists(v)) for k, v in obj.items()}
        return obj

    sod_bad_rule = copy.deepcopy(payload)
    if "extra_rules" in sod_bad_rule:
        sod_bad_rule["extra_rules"] = [{"code": "X1", "title": "Bad", "severity": "catastrophic"}]
    return {
        "ok": payload,
        "bad_decimal": _map_strings(payload, lambda s: "abc" if _is_decimal_text(s) else s),
        "huge": _map_strings(payload, lambda s: "1e400" if _is_decimal_text(s) else s),
        "negative": _map_strings(payload, lambda s: f"-{s}" if _is_decimal_text(s) else s),
        "empty_lists": empty_lists(payload),
        "bad_rule": sod_bad_rule,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(("endpoint", "payload_fn", "tool"), PROMOTED_TOOLS, ids=[t[2].value for t in PROMOTED_TOOLS])
async def test_promoted_tool_routes_unchanged(db_session, make_user, make_engagement, endpoint, payload_fn, tool):
    user = make_user(email=f"snap819_{tool.value}@example.com")
    engagement = make_engagement(user=user)
    _override(user, db_session)
    out: dict[str, Any] = {}
    try:
        with freeze_time(FROZEN_NOW):
            for label, payload in _variants(payload_fn()).items():
                before = db_session.query(ToolRun).filter(ToolRun.engagement_id == engagement.id).count()
                response = await _call("POST", endpoint, json={**payload, "engagement_id": engagement.id})
                runs = (
                    db_session.query(ToolRun)
                    .filter(ToolRun.engagement_id == engagement.id)
                    .order_by(ToolRun.run_number)
                    .all()[before:]
                )
                case = _capture(response)
                case["tool_runs"] = [
                    {"tool": r.tool_name.value, "status": r.status.value, "score": r.composite_score} for r in runs
                ]
                out[label] = case
                export = await _call("POST", endpoint.replace("/analyze", "") + _export_suffix(endpoint), json=payload)
                out[label + ":export"] = _capture(export)
    finally:
        app.dependency_overrides.clear()
    check_snapshot(f"route_{tool.value}", out)


def _export_suffix(endpoint: str) -> str:
    return "/analyze.csv" if endpoint.endswith("/analyze") else "/export.csv"


# =============================================================================
# Form-input exports (item 7)
# =============================================================================

_FORM_EXPORTS: dict[str, tuple[str, dict]] = {
    "heatmap_csv": (
        "/audit/account-risk-heatmap/export.csv",
        {
            "signals": [
                {
                    "account_number": "1000",
                    "account_name": "Cash",
                    "source": "manual",
                    "severity": "high",
                    "issue": "Unreconciled",
                    "materiality": "5000",
                },
                {"account_name": "Revenue", "source": "cutoff", "issue": "Late entry", "confidence": 0.5},
            ],
            "audit_anomalies": [
                {"account": "Suspense", "severity": "high", "issue": "Suspense balance", "amount": 1200}
            ],
        },
    ),
    "depreciation_csv": (
        "/audit/depreciation/export.csv",
        {
            "asset_name": "Delivery Truck #4 (2025)",
            "cost": "75000",
            "salvage_value": "5000",
            "useful_life_years": 5,
            "placed_in_service_year": 2025,
            "book_method": "declining_balance",
            "macrs_system": "gds_200db",
            "macrs_property_class": 5,
        },
    ),
    "depreciation_csv_book_only": (
        "/audit/depreciation/export.csv",
        {"asset_name": "Desk", "cost": "1200", "useful_life_years": 7},
    ),
    "lease_csv": (
        "/audit/lease-accounting/export.csv",
        {
            "lease_name": "HQ Office / Floor 3",
            "payment_amount": "10000",
            "term_periods": 24,
            "annual_discount_rate": "0.06",
            "annual_escalation_rate": "0.03",
            "start_date": "2026-01-01",
        },
    ),
    "loan_csv": (
        "/audit/loan-amortization/export.csv",
        {"principal": "200000", "annual_rate": "0.06", "term_periods": 24, "start_date": "2026-01-01"},
    ),
    "loan_xlsx": (
        "/audit/loan-amortization/export.xlsx",
        {"principal": "200000", "annual_rate": "0.06", "term_periods": 24, "start_date": "2026-01-01"},
    ),
    "loan_pdf": (
        "/audit/loan-amortization/export.pdf",
        {"principal": "200000", "annual_rate": "0.06", "term_periods": 24, "start_date": "2026-01-01"},
    ),
    "movements_csv": (
        "/export/csv/movements",
        {
            "prior_accounts": [
                {"account": "Cash", "debit": 10000, "credit": 0, "type": "asset"},
                {"account": "Revenue", "debit": 0, "credit": 10000, "type": "income"},
            ],
            "current_accounts": [
                {"account": "Cash", "debit": 14000, "credit": 0, "type": "asset"},
                {"account": "Revenue", "debit": 0, "credit": 14000, "type": "income"},
            ],
            "prior_label": "FY24",
            "current_label": "FY25",
            "materiality_threshold": 500.0,
        },
    ),
}


@pytest.mark.asyncio
async def test_form_export_routes_unchanged(db_session, make_user):
    user = make_user(email="snap819_exports@example.com")
    _override(user, db_session)
    out: dict[str, Any] = {}
    try:
        with freeze_time(FROZEN_NOW):
            for label, (url, payload) in _FORM_EXPORTS.items():
                out[label] = _capture(await _call("POST", url, json=payload))
            # bank rec: rebuild-from-JSON route
            from bank_reconciliation import calculate_summary
            from tests.test_bank_rec_export_838 import _matches  # local: module-level helpers only

            summary = json.loads(json.dumps(calculate_summary(_matches()).to_dict(), default=float))
            out["bank_rec_csv"] = _capture(
                await _call(
                    "POST",
                    "/export/csv/bank-rec",
                    json={"summary": summary, "matches": summary["matches"], "filename": "rec"},
                )
            )
    finally:
        app.dependency_overrides.clear()
    check_snapshot("route_form_exports", out)


@pytest.mark.asyncio
async def test_admin_activity_csv_unchanged(db_session, admin_user):  # noqa: F811
    app.dependency_overrides[require_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with freeze_time(FROZEN_NOW):
            out = _capture(await _call("GET", "/admin/export-activity-csv"))
    finally:
        app.dependency_overrides.clear()
    check_snapshot("route_admin_activity_csv", out)


# =============================================================================
# Engagement exports (item 7)
# =============================================================================


@pytest.mark.asyncio
async def test_engagement_export_routes_unchanged(db_session, make_user, make_engagement):
    from datetime import UTC, datetime

    user = make_user(email="snap819_eng@example.com")
    client = Client(user_id=user.id, name="Snapshot Client", industry=Industry.TECHNOLOGY, fiscal_year_end="12-31")
    db_session.add(client)
    db_session.flush()
    with freeze_time(FROZEN_NOW):
        engagement = make_engagement(
            client=client,
            user=user,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )
    _override(user, db_session)
    out: dict[str, Any] = {}
    try:
        with freeze_time(FROZEN_NOW):
            for slug in ("anomaly-summary", "package", "convergence-csv", "analytical-expectations", "sum-schedule"):
                captured = _capture(await _call("POST", f"/engagements/{engagement.id}/export/{slug}"))
                # The engagement id is assigned by the DB; keep the snapshot independent of it.
                if captured.get("content_disposition"):
                    captured["content_disposition"] = captured["content_disposition"].replace(
                        f"_{engagement.id}.csv", "_<id>.csv"
                    )
                out[slug] = captured
                out[slug + ":missing"] = _capture(await _call("POST", "/engagements/999999/export/" + slug))
    finally:
        app.dependency_overrides.clear()
    check_snapshot("route_engagement_exports", out)


# =============================================================================
# Diagnostic export pipeline (item 8: _run_export)
# =============================================================================

_PIPELINE: dict[str, tuple[str, dict, str]] = {
    # label: (url, payload, serializer patched for the error case)
    "pdf": ("/export/pdf", {**BASE_AUDIT, "filename": "Client ABC"}, "serialize_audit_pdf"),
    "excel": ("/export/excel", BASE_AUDIT, "serialize_audit_excel"),
    "csv_tb": ("/export/csv/trial-balance", BASE_AUDIT, "serialize_trial_balance_csv"),
    "csv_tb_nofilename": ("/export/csv/trial-balance", {**BASE_AUDIT, "filename": ""}, "serialize_trial_balance_csv"),
    "csv_anomalies": ("/export/csv/anomalies", BASE_AUDIT, "serialize_anomalies_csv"),
    "leadsheets": ("/export/leadsheets", LEAD_SHEET_PAYLOAD, "serialize_leadsheets_excel"),
    "fin_stmts_pdf": ("/export/financial-statements", FIN_STMT_PAYLOAD, "serialize_financial_statements_pdf"),
    "fin_stmts_excel": (
        "/export/financial-statements?format=excel",
        FIN_STMT_PAYLOAD,
        "serialize_financial_statements_excel",
    ),
    "preflight": (
        "/export/csv/preflight-issues",
        {
            "issues": [
                {"category": "columns", "severity": "high", "message": "Missing debit", "affected_count": 3},
            ],
            "filename": "preflight",
        },
        "serialize_preflight_issues_csv",
    ),
    "population_profile": (
        "/export/csv/population-profile",
        {
            "account_count": 50,
            "total_abs_balance": 1000000.0,
            "mean_abs_balance": 20000.0,
            "median_abs_balance": 15000.0,
            "std_dev_abs_balance": 10000.0,
            "min_abs_balance": 100.0,
            "max_abs_balance": 200000.0,
            "p25": 8000.0,
            "p75": 30000.0,
            "gini_coefficient": 0.45,
            "gini_interpretation": "Moderate concentration",
            "buckets": [{"label": "< $1K", "count": 5, "percent_count": 10.0, "sum_abs": 2000.0}],
            "top_accounts": [
                {
                    "rank": 1,
                    "account": "Revenue",
                    "category": "Income",
                    "net_balance": 200000.0,
                    "abs_balance": 200000.0,
                    "percent_of_total": 20.0,
                }
            ],
            "filename": "pop_profile",
        },
        "serialize_population_profile_csv",
    ),
    "expense_category": (
        "/export/csv/expense-category-analytics",
        {
            "total_expenses": 50000.0,
            "total_revenue": 200000.0,
            "revenue_available": True,
            "prior_available": False,
            "materiality_threshold": 5000.0,
            "category_count": 2,
            "categories": [
                {"label": "Cost of Sales", "amount": 30000.0, "pct_of_revenue": 15.0},
                {"label": "Operating Expenses", "amount": 20000.0, "pct_of_revenue": 10.0},
            ],
            "filename": "expense_cat",
        },
        "serialize_expense_category_csv",
    ),
    "accrual_completeness": (
        "/export/csv/accrual-completeness",
        {
            "accrual_account_count": 5,
            "total_accrued_balance": 25000.0,
            "prior_available": False,
            "accrual_accounts": [
                {"account_name": "Accrued Liabilities", "balance": 15000.0, "matched_keyword": "accru"}
            ],
            "threshold_pct": 15.0,
            "below_threshold": False,
            "filename": "accrual",
        },
        "serialize_accrual_completeness_csv",
    ),
}


@pytest.mark.asyncio
async def test_diagnostic_export_pipeline_unchanged(db_session, make_user):
    user = make_user(email="snap819_pipeline@example.com")
    _override(user, db_session)
    out: dict[str, Any] = {}
    events: list[list[str]] = []
    try:
        with (
            freeze_time(FROZEN_NOW),
            patch("export.pipeline.log_secure_operation", side_effect=lambda *a: events.append(list(a))),
        ):
            for label, (url, payload, serializer) in _PIPELINE.items():
                events.clear()
                case = _capture(await _call("POST", url, json=payload))
                case["events"] = list(events)
                out[label] = case
                for exc in (ValueError("boom"), OSError("disk"), UnicodeEncodeError("utf-8", "x", 0, 1, "bad")):
                    events.clear()
                    with patch(f"export.pipeline.{serializer}", side_effect=exc):
                        err = _capture(await _call("POST", url, json=payload))
                    err["events"] = list(events)
                    out[f"{label}:{type(exc).__name__}"] = err
    finally:
        app.dependency_overrides.clear()
    check_snapshot("route_export_pipeline", out)


# =============================================================================
# Testing-tool CSV exports + memo PDFs (item 7: the shared response helpers)
# =============================================================================

_TESTING_EXPORTS: dict[str, tuple[str, str, str]] = {
    # engine case: (csv route, memo route, filename)
    "je": ("/export/csv/je-testing", "/export/je-testing-memo", "GL Detail FY25"),
    "ap": ("/export/csv/ap-testing", "/export/ap-testing-memo", "ap_payments"),
    "payroll": ("/export/csv/payroll-testing", "/export/payroll-testing-memo", "payroll"),
    "revenue": ("/export/csv/revenue-testing", "/export/revenue-testing-memo", "revenue"),
    "fixed_assets": ("/export/csv/fixed-assets", "/export/fixed-asset-memo", "fa_register"),
    "inventory": ("/export/csv/inventory", "/export/inventory-memo", "inventory"),
}


@pytest.mark.asyncio
async def test_testing_tool_exports_unchanged(db_session, make_user):
    from tests.test_sprint819_output_snapshots import CASES

    user = make_user(email="snap819_testing_exports@example.com")
    _override(user, db_session)
    out: dict[str, Any] = {}
    try:
        # shared/memo_template.py seeds its follow-up wording rotation with the
        # builtin str hash(), which is randomised per process (PYTHONHASHSEED), so
        # memo wording differs between server restarts — pre-existing, outside
        # Sprint 819. Pin it here so the snapshot is reproducible.
        with (
            freeze_time(FROZEN_NOW),
            patch("shared.memo_template.hash", create=True, side_effect=lambda s: sum(map(ord, s))),
        ):
            for case, (csv_url, memo_url, filename) in _TESTING_EXPORTS.items():
                # The wire shape the frontend posts back: FastAPI's encoder sends
                # Decimal as a JSON number.
                result = json.loads(
                    json.dumps(CASES[case](), default=lambda o: float(o) if isinstance(o, Decimal) else str(o))
                )
                body = {**result, "filename": filename}
                out[f"{case}:csv"] = _capture(await _call("POST", csv_url, json=body))
                out[f"{case}:memo"] = _capture(await _call("POST", memo_url, json=body))
    finally:
        app.dependency_overrides.clear()
    check_snapshot("route_testing_exports", out)
