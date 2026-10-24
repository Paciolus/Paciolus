"""
Sprint 836: saved testing settings reach the engines.

The settings drawer saved JE / AP / Payroll / Three-Way Match thresholds to
``User.settings`` but every route ran the engine defaults. These tests drive
the real routes with saved settings and check that the engine behaviour
changes, that each result reports ``settings_applied`` (non-default values
only) and ``settings_ignored`` (key + reason), and that a stale or malformed
saved key never breaks a run.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.audit.ap_testing.analysis import APTestingConfig  # noqa: E402
from services.audit.je_testing.analysis import JETestingConfig  # noqa: E402
from services.audit.payroll_testing.analysis import PayrollTestingConfig  # noqa: E402
from shared.saved_testing_config import (  # noqa: E402
    AP_SPEC,
    JE_SPEC,
    PAYROLL_SPEC,
    TWM_SPEC,
    apply_saved_config,
    load_saved_testing_config,
    supersede_with_run_overrides,
)
from three_way_match_engine import ThreeWayMatchConfig  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


class _User:
    def __init__(self, settings: str | None):
        self.settings = settings


# ─── helper: what is applied, what is reported ──────────────────────────


class TestApplySavedConfig:
    def test_valid_values_are_applied(self):
        out = apply_saved_config(
            JETestingConfig(),
            {"round_amount_threshold": 25000, "weekend_posting_enabled": False, "approval_thresholds": [1000, 2500.5]},
            JE_SPEC,
        )
        assert out.config.round_amount_threshold == 25000.0
        assert isinstance(out.config.round_amount_threshold, float)
        assert out.config.weekend_posting_enabled is False
        assert out.config.approval_thresholds == [1000.0, 2500.5]
        assert out.ignored == []

    def test_applied_lists_only_values_that_differ_from_the_engine_default(self):
        out = apply_saved_config(
            JETestingConfig(),
            {"round_amount_threshold": 10000, "unusual_amount_stddev": 3.0, "backdate_days_threshold": 14},
            JE_SPEC,
        )
        assert out.applied == {"backdate_days_threshold": 14}
        assert set(out.overrides) == {"round_amount_threshold", "unusual_amount_stddev", "backdate_days_threshold"}

    @pytest.mark.parametrize(
        ("key", "value", "reason"),
        [
            ("no_such_threshold", 5, "Not a setting this tool recognises"),
            ("weekend_posting_enabled", "false", "must be true or false"),
            ("weekend_posting_enabled", 0, "must be true or false"),
            ("round_amount_threshold", True, "must be a number"),
            ("round_amount_threshold", "5000", "must be a number"),
            ("round_amount_threshold", None, "must be a number"),
            ("round_amount_threshold", -1, "must be at least 0"),
            ("round_amount_threshold", math.inf, "must be a finite number"),
            ("round_amount_threshold", math.nan, "must be a finite number"),
            ("backdate_days_threshold", 2.5, "must be a whole number"),
            ("single_user_volume_pct", 25, "must be between 0 and 1"),
            ("after_hours_start", 24, "must be between 0 and 23"),
            ("approval_thresholds", [], "at least one value"),
            ("approval_thresholds", [5000, "x"], "every value must be a number"),
            ("approval_thresholds", 5000, "must be a list of numbers"),
            ("holiday_excluded_names", ["Columbus Day"], "set for each run"),
            ("sampling_default_rate", 0.2, "sampling run"),
        ],
    )
    def test_invalid_or_unknown_values_are_reported_not_applied(self, key, value, reason):
        out = apply_saved_config(JETestingConfig(), {key: value, "reciprocal_days_window": 14}, JE_SPEC)
        assert [i["key"] for i in out.ignored] == [key]
        assert reason in out.ignored[0]["reason"]
        # The bad key changes nothing; the good key still applies.
        assert out.applied == {"reciprocal_days_window": 14}
        if hasattr(JETestingConfig(), key):
            assert getattr(out.config, key) == getattr(JETestingConfig(), key)

    def test_hidden_pre_836_benford_default_is_reported_not_applied(self):
        # The old form saved benford_min_entries=500 on every JE save without
        # ever showing it; the engine default is 300.
        out = apply_saved_config(JETestingConfig(), {"benford_min_entries": 500}, JE_SPEC)
        assert out.config.benford_min_entries == 300
        assert out.applied == {}
        assert out.ignored[0]["key"] == "benford_min_entries"
        assert "default of 300" in out.ignored[0]["reason"]
        # Any other value is a real choice and applies.
        assert apply_saved_config(JETestingConfig(), {"benford_min_entries": 1000}, JE_SPEC).applied == {
            "benford_min_entries": 1000
        }

    def test_whole_float_is_accepted_for_an_int_field(self):
        out = apply_saved_config(JETestingConfig(), {"backdate_days_threshold": 14.0}, JE_SPEC)
        assert out.config.backdate_days_threshold == 14
        assert isinstance(out.config.backdate_days_threshold, int)

    def test_saved_settings_layer_on_top_of_the_base(self):
        from datetime import date

        base = JETestingConfig(holiday_additional_dates=(date(2025, 12, 24),))
        out = apply_saved_config(base, {"round_amount_threshold": 50000}, JE_SPEC)
        assert out.config.holiday_additional_dates == (date(2025, 12, 24),)
        assert out.config.round_amount_threshold == 50000.0

    def test_payroll_legacy_toggle_names_are_honoured_under_the_engine_name(self):
        out = apply_saved_config(
            PayrollTestingConfig(), {"check_gap_enabled": False, "benford_enabled": False}, PAYROLL_SPEC
        )
        assert out.config.check_number_gap_enabled is False
        assert out.config.enable_benford is False
        assert out.applied == {"check_number_gap_enabled": False, "enable_benford": False}

    def test_engine_name_beats_a_legacy_alias(self):
        out = apply_saved_config(PayrollTestingConfig(), {"ghost_enabled": False, "enable_ghost": True}, PAYROLL_SPEC)
        assert out.config.enable_ghost is True
        assert out.ignored == [{"key": "ghost_enabled", "reason": "Superseded by the saved value for 'enable_ghost'."}]

    def test_twm_bounds_apply_to_saved_values(self):
        out = apply_saved_config(
            ThreeWayMatchConfig(), {"price_variance_threshold": 5, "date_window_days": 400}, TWM_SPEC
        )
        assert {i["key"] for i in out.ignored} == {"price_variance_threshold", "date_window_days"}
        assert out.config == ThreeWayMatchConfig()

    def test_ap_saved_values(self):
        out = apply_saved_config(
            APTestingConfig(), {"duplicate_days_window": 45, "vendor_variation_threshold": 1.5}, AP_SPEC
        )
        assert out.applied == {"duplicate_days_window": 45}
        assert [i["key"] for i in out.ignored] == ["vendor_variation_threshold"]

    def test_run_overrides_supersede_saved_values(self):
        out = apply_saved_config(ThreeWayMatchConfig(), {"date_window_days": 60, "amount_tolerance": 0.01}, TWM_SPEC)
        supersede_with_run_overrides(out, {"date_window_days", "amount_tolerance"})
        assert out.applied == {}
        # Only the saved value that changed something is reported as replaced.
        assert out.ignored == [{"key": "date_window_days", "reason": "Replaced by the value supplied for this run."}]


class TestLoadSavedTestingConfig:
    def test_no_settings_means_engine_defaults(self):
        out = load_saved_testing_config(_User(None), JE_SPEC)
        assert out.config == JETestingConfig()
        assert out.result_fields() == {"settings_applied": {}, "settings_ignored": []}

    def test_reads_the_tool_section(self):
        user = _User(json.dumps({"ap_testing_config": {"round_amount_threshold": 50000}}))
        out = load_saved_testing_config(user, AP_SPEC)
        assert out.config.round_amount_threshold == 50000.0
        assert out.applied == {"round_amount_threshold": 50000.0}

    def test_unreadable_practice_settings_are_reported(self):
        # An invalid sibling field makes PracticeSettings.from_json fall back to
        # defaults; the saved thresholds are lost, and the result must say so.
        user = _User(json.dumps({"default_fiscal_year_end": "bad", "je_testing_config": {"round_amount_threshold": 1}}))
        out = load_saved_testing_config(user, JE_SPEC)
        assert out.config == JETestingConfig()
        assert out.ignored and out.ignored[0]["key"] == "je_testing_config"


# ─── through the real routes ─────────────────────────────────────────────


def _gl_csv() -> bytes:
    rows = ["Entry ID,Date,Account,Description,Debit,Credit"]
    for i in range(1, 31):
        amount = "20000.00" if i == 7 else f"{100 + i * 13}.37"
        rows.append(f"JE{i},2025-03-{(i % 20) + 3:02d},Cash,Receipt {i},{amount},0")
        rows.append(f"JE{i},2025-03-{(i % 20) + 3:02d},Revenue,Receipt {i},0,{amount}")
    return ("\n".join(rows) + "\n").encode()


def _ap_csv() -> bytes:
    rows = ["Invoice Number,Invoice Date,Payment Date,Vendor Name,Amount,Check Number,Description"]
    for i in range(1, 31):
        amount = "20000.00" if i == 7 else f"{100 + i * 17}.42"
        rows.append(f"INV{i:04d},2025-03-03,2025-03-{(i % 20) + 5:02d},Vendor {i % 6},{amount},{1000 + i},Supplies {i}")
    return ("\n".join(rows) + "\n").encode()


def _payroll_csv() -> bytes:
    rows = ["Employee ID,Employee Name,Department,Pay Date,Gross Pay"]
    for i in range(1, 31):
        amount = "20000.00" if i == 7 else f"{3000 + i * 23}.18"
        rows.append(f"E{i:03d},Employee Number{i},Dept {i % 3},2025-03-14,{amount}")
    return ("\n".join(rows) + "\n").encode()


def _twm_files() -> dict:
    po = "PO Number,Vendor,Description,Quantity,Unit Price,Total Amount,Order Date,Expected Delivery\nPO-1,Acme Supply,Widgets,10,100.00,1000.00,2025-01-01,2025-01-10\n"
    inv = "Invoice Number,PO Reference,Vendor,Description,Quantity,Unit Price,Total Amount,Invoice Date\nINV-1,PO-1,Acme Supply,Widgets,10,100.00,1000.00,2025-02-20\n"
    rec = "Receipt Number,PO Reference,Invoice Reference,Vendor,Description,Quantity Received,Receipt Date\nGRN-1,PO-1,INV-1,Acme Supply,Widgets,10,2025-02-24\n"
    return {
        "po_file": ("po.csv", po.encode(), "text/csv"),
        "invoice_file": ("inv.csv", inv.encode(), "text/csv"),
        "receipt_file": ("rec.csv", rec.encode(), "text/csv"),
    }


async def _post(path: str, files: dict, data: dict | None = None) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, files=files, data=data or {})


def _save(user, db_session, section: str, values: dict) -> None:
    user.settings = json.dumps({section: values})
    db_session.flush()


def _flagged(body: dict, test_key: str) -> int:
    return next(t["entries_flagged"] for t in body["test_results"] if t["test_key"] == test_key)


@pytest.mark.usefixtures("bypass_csrf")
class TestRoutesHonourSavedSettings:
    @pytest.mark.asyncio
    async def test_je_saved_threshold_changes_the_result(self, override_auth_verified, db_session):
        baseline = await _post("/audit/journal-entries", {"file": ("gl.csv", _gl_csv(), "text/csv")})
        assert baseline.status_code == 200, baseline.text
        assert _flagged(baseline.json(), "round_amounts") > 0
        assert baseline.json()["settings_applied"] == {}
        assert baseline.json()["settings_ignored"] == []

        _save(override_auth_verified, db_session, "je_testing_config", {"round_amount_threshold": 50000})
        response = await _post("/audit/journal-entries", {"file": ("gl.csv", _gl_csv(), "text/csv")})
        assert response.status_code == 200, response.text
        body = response.json()
        assert _flagged(body, "round_amounts") == 0
        assert body["settings_applied"] == {"round_amount_threshold": 50000.0}

    @pytest.mark.asyncio
    async def test_je_stale_or_invalid_key_is_reported_and_the_run_completes(self, override_auth_verified, db_session):
        _save(
            override_auth_verified,
            db_session,
            "je_testing_config",
            # The pre-836 frontend saved the whole form, defaults included.
            {"retired_threshold": 3, "weekend_posting_enabled": "no", "round_amount_threshold": 10000},
        )
        response = await _post("/audit/journal-entries", {"file": ("gl.csv", _gl_csv(), "text/csv")})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["settings_applied"] == {}, "a saved value equal to the default is not a change"
        assert {i["key"] for i in body["settings_ignored"]} == {"retired_threshold", "weekend_posting_enabled"}
        assert all(i["reason"] for i in body["settings_ignored"])

    @pytest.mark.asyncio
    async def test_je_holiday_calendar_still_applies_on_top_of_saved_settings(self, override_auth_verified, db_session):
        _save(override_auth_verified, db_session, "je_testing_config", {"round_amount_threshold": 50000})
        calendar = json.dumps({"exclude": [], "closed_dates": ["2025-03-10"]})
        response = await _post(
            "/audit/journal-entries",
            {"file": ("gl.csv", _gl_csv(), "text/csv")},
            data={"holiday_calendar": calendar},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert _flagged(body, "round_amounts") == 0, "saved threshold applied"
        assert _flagged(body, "holiday_postings") > 0, "per-run closure day applied"
        assert body["settings_applied"] == {"round_amount_threshold": 50000.0}

    @pytest.mark.asyncio
    async def test_ap_saved_threshold_changes_the_result(self, override_auth_verified, db_session):
        files = {"file": ("ap.csv", _ap_csv(), "text/csv")}
        baseline = await _post("/audit/ap-payments", files)
        assert baseline.status_code == 200, baseline.text
        assert _flagged(baseline.json(), "round_dollar_amounts") > 0

        _save(override_auth_verified, db_session, "ap_testing_config", {"round_amount_threshold": 50000})
        response = await _post("/audit/ap-payments", {"file": ("ap.csv", _ap_csv(), "text/csv")})
        assert response.status_code == 200, response.text
        assert _flagged(response.json(), "round_dollar_amounts") == 0
        assert response.json()["settings_applied"] == {"round_amount_threshold": 50000.0}

    @pytest.mark.asyncio
    async def test_payroll_saved_threshold_changes_the_result(self, override_auth_verified, db_session):
        baseline = await _post("/audit/payroll-testing", {"file": ("pr.csv", _payroll_csv(), "text/csv")})
        assert baseline.status_code == 200, baseline.text
        assert _flagged(baseline.json(), "PR-T3") > 0

        _save(
            override_auth_verified,
            db_session,
            "payroll_testing_config",
            {"round_amount_threshold": 50000, "check_gap_enabled": True},
        )
        response = await _post("/audit/payroll-testing", {"file": ("pr.csv", _payroll_csv(), "text/csv")})
        assert response.status_code == 200, response.text
        assert _flagged(response.json(), "PR-T3") == 0
        assert response.json()["settings_applied"] == {"round_amount_threshold": 50000.0}

    @pytest.mark.asyncio
    async def test_twm_saved_date_window_changes_the_result(self, override_auth_verified, db_session):
        baseline = await _post("/audit/three-way-match", _twm_files())
        assert baseline.status_code == 200, baseline.text
        assert any(v["field"] == "date" for v in baseline.json()["variances"])

        _save(override_auth_verified, db_session, "three_way_match_config", {"date_window_days": 60})
        response = await _post("/audit/three-way-match", _twm_files())
        assert response.status_code == 200, response.text
        body = response.json()
        assert not any(v["field"] == "date" for v in body["variances"])
        assert body["config"]["date_window_days"] == 60
        assert body["settings_applied"] == {"date_window_days": 60}

    @pytest.mark.asyncio
    async def test_twm_per_run_value_beats_the_saved_one(self, override_auth_verified, db_session):
        _save(override_auth_verified, db_session, "three_way_match_config", {"date_window_days": 60})
        response = await _post("/audit/three-way-match", _twm_files(), data={"date_window_days": "10"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["config"]["date_window_days"] == 10
        assert body["settings_applied"] == {}
        assert body["settings_ignored"] == [
            {"key": "date_window_days", "reason": "Replaced by the value supplied for this run."}
        ]


# ─── frontend defaults agree with the engine ─────────────────────────────


def _ts_object(name: str) -> dict[str, str]:
    ts = (REPO_ROOT / "frontend/src/types/settings.ts").read_text(encoding="utf-8")
    start = ts.index(f"export const {name}")
    body = ts[ts.index("{", ts.index("=", start)) + 1 : ts.index("\n};", start)]
    return dict(re.findall(r"^\s*(\w+):\s*([^,\n]+),?\s*$", body, flags=re.M))


def _ts_value(raw: str):
    raw = raw.strip()
    if raw in ("true", "false"):
        return raw == "true"
    return float(raw.replace("_", ""))


@pytest.mark.parametrize(
    ("const", "config_cls", "spec"),
    [
        ("DEFAULT_JE_TESTING_CONFIG", JETestingConfig, JE_SPEC),
        ("DEFAULT_AP_TESTING_CONFIG", APTestingConfig, AP_SPEC),
        ("DEFAULT_PAYROLL_TESTING_CONFIG", PayrollTestingConfig, PAYROLL_SPEC),
        ("DEFAULT_THREE_WAY_MATCH_CONFIG", ThreeWayMatchConfig, TWM_SPEC),
    ],
)
def test_frontend_defaults_match_engine_defaults(const, config_cls, spec):
    """Saving the drawer's defaults must not change any threshold."""
    frontend = _ts_object(const)
    engine = config_cls()
    assert frontend, const
    for key, raw in frontend.items():
        assert key not in spec.aliases, f"{const}.{key} uses a legacy name"
        assert hasattr(engine, key), f"{const}.{key} is not an engine field"
        assert _ts_value(raw) == getattr(engine, key), f"{const}.{key}"


@pytest.mark.parametrize(
    ("const", "config_cls", "preset"),
    [
        ("JE_TESTING_PRESETS", JETestingConfig, "standard"),
        ("AP_TESTING_PRESETS", APTestingConfig, "standard"),
        ("PAYROLL_TESTING_PRESETS", PayrollTestingConfig, "standard"),
        ("THREE_WAY_MATCH_PRESETS", ThreeWayMatchConfig, "standard"),
    ],
)
def test_standard_preset_is_the_engine_default(const, config_cls, preset):
    ts = (REPO_ROOT / "frontend/src/types/settings.ts").read_text(encoding="utf-8")
    start = ts.index(f"export const {const}")
    block = ts[ts.index(f"{preset}: {{", start) :]
    block = block[: block.index("}")]
    values = dict(re.findall(r"(\w+):\s*([\d.]+|true|false)", block.split("{", 1)[1]))
    engine = config_cls()
    assert values
    for key, raw in values.items():
        assert _ts_value(raw) == getattr(engine, key), f"{const}.{preset}.{key}"


# ─── the memo states which thresholds differed from the defaults ─────────


def _pdf_text(pdf: bytes) -> str:
    import io

    from pypdf import PdfReader

    return " ".join(" ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages).split())


class TestMemoDisclosure:
    def test_je_memo_lists_changed_thresholds_and_defaults(self):
        from je_testing_memo_generator import generate_je_testing_memo
        from tests.test_je_testing_memo import _make_je_result

        result = _make_je_result()
        result["settings_applied"] = {"round_amount_threshold": 50000.0, "weekend_posting_enabled": False}
        result["settings_ignored"] = [{"key": "retired_threshold", "reason": "Not a setting this tool recognises."}]
        text = _pdf_text(generate_je_testing_memo(result))
        assert "changed 2 thresholds from the Paciolus defaults" in text
        assert "Round amount threshold 50,000 10,000" in text
        assert "Weekend posting enabled Disabled Enabled" in text
        assert "retired_threshold: Not a setting this tool recognises." in text

    def test_memo_says_defaults_when_nothing_changed(self):
        from ap_testing_memo_generator import generate_ap_testing_memo
        from tests.test_ap_testing_memo import _make_ap_result

        result = _make_ap_result()
        result["settings_applied"] = {}
        assert "Every threshold used on this run was the Paciolus default" in _pdf_text(
            generate_ap_testing_memo(result)
        )

    def test_memo_without_the_fields_is_unchanged(self):
        from payroll_testing_memo_generator import generate_payroll_testing_memo
        from tests.test_payroll_testing_memo import _make_payroll_result

        text = _pdf_text(generate_payroll_testing_memo(_make_payroll_result()))
        assert "Thresholds from saved settings" not in text

    def test_twm_memo_lists_changed_tolerances(self):
        from tests.test_twm_memo import _make_twm_result
        from three_way_match_memo_generator import generate_three_way_match_memo

        result = _make_twm_result()
        result["settings_applied"] = {"date_window_days": 60}
        text = _pdf_text(generate_three_way_match_memo(result))
        assert "changed 1 threshold from the Paciolus defaults" in text
        assert "Date window days 60 30" in text

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_memo_export_endpoint_carries_the_fields(self, override_auth_verified):
        from main import app
        from tests.test_je_testing_memo import _make_je_result

        body = {k: v for k, v in _make_je_result().items() if k in ("composite_score", "test_results", "data_quality")}
        body["settings_applied"] = {"backdate_days_threshold": 14}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/je-testing-memo", json=body)
        assert response.status_code == 200, response.text
        assert "Backdate days threshold 14 30" in _pdf_text(response.content)
