"""
Sprint 839 — API inputs the app never sent now have a path from the app.

* Bank reconciliation: per-run materiality / performance materiality are
  validated with a clear message, and the result says per threshold whether
  the run supplied it or the default applied.
* Three-Way Match: values supplied for one run are disclosed as such
  (``settings_run_overrides``) in the result and the memo; the three manual
  column mappings, previously parsed and then ignored, are applied to column
  detection, and anything malformed is refused rather than dropped.
* W-2: a read-only endpoint lists the tax years the web form can run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def _post(path: str, files: dict, data: dict | None = None) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, files=files, data=data or {})


# ─── Bank reconciliation ─────────────────────────────────────────────────


def _bank_files() -> dict:
    bank = "Date,Description,Amount\n2025-03-01,Deposit,1000.00\n2025-03-02,Check 101,-250.00\n2025-03-03,Bank fee,-15.00\n"
    ledger = "Date,Description,Amount\n2025-03-01,Deposit,1000.00\n2025-03-02,Check 101,-250.00\n2025-03-04,Check 102,-80.00\n"
    return {
        "bank_file": ("bank.csv", bank.encode(), "text/csv"),
        "ledger_file": ("ledger.csv", ledger.encode(), "text/csv"),
    }


@pytest.mark.usefixtures("bypass_csrf")
class TestBankRecMateriality:
    @pytest.mark.asyncio
    async def test_no_values_uses_defaults_and_says_so(self, override_auth_verified):
        response = await _post("/audit/bank-reconciliation", _bank_files())
        assert response.status_code == 200, response.text
        thresholds = response.json()["active_thresholds"]
        assert thresholds["materiality_source"] == "default"
        assert thresholds["materiality"] == "50000.00"
        assert thresholds["threshold_sources"] == {"materiality": "default", "performance_materiality": "default"}

    @pytest.mark.asyncio
    async def test_both_values_applied_and_disclosed(self, override_auth_verified):
        response = await _post(
            "/audit/bank-reconciliation",
            _bank_files(),
            data={"materiality": "25000", "performance_materiality": "18750"},
        )
        assert response.status_code == 200, response.text
        thresholds = response.json()["active_thresholds"]
        assert thresholds["materiality_source"] == "caller"
        assert float(thresholds["materiality"]) == 25000
        assert float(thresholds["performance_materiality"]) == 18750
        assert thresholds["threshold_sources"] == {"materiality": "caller", "performance_materiality": "caller"}

    @pytest.mark.asyncio
    async def test_one_value_does_not_present_the_other_as_entered(self, override_auth_verified):
        response = await _post("/audit/bank-reconciliation", _bank_files(), data={"materiality": "60000"})
        assert response.status_code == 200, response.text
        thresholds = response.json()["active_thresholds"]
        assert float(thresholds["materiality"]) == 60000
        assert thresholds["performance_materiality"] == "50000.00"
        assert thresholds["threshold_sources"] == {"materiality": "caller", "performance_materiality": "default"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("data", "message"),
        [
            ({"materiality": "-1"}, "Materiality must be a dollar amount of zero or more."),
            ({"performance_materiality": "-5"}, "Performance materiality must be a dollar amount of zero or more."),
            ({"materiality": "nan"}, "Materiality must be a dollar amount of zero or more."),
            ({"materiality": "inf"}, "Materiality must be a dollar amount of zero or more."),
            (
                {"materiality": "10000", "performance_materiality": "20000"},
                "Performance materiality cannot exceed materiality.",
            ),
        ],
    )
    async def test_unusable_values_refused_with_a_clear_message(self, override_auth_verified, data, message):
        response = await _post("/audit/bank-reconciliation", _bank_files(), data=data)
        assert response.status_code == 400, response.text
        assert response.json()["detail"] == message


# ─── Three-Way Match: per-run overrides ──────────────────────────────────


def _twm_files(po_header: str | None = None) -> dict:
    po_head = po_header or "PO Number,Vendor,Description,Quantity,Unit Price,Total Amount,Order Date,Expected Delivery"
    po = f"{po_head}\nPO-1,Acme Supply,Widgets,10,100.00,1000.00,2025-01-01,2025-01-10\n"
    inv = "Invoice Number,PO Reference,Vendor,Description,Quantity,Unit Price,Total Amount,Invoice Date\nINV-1,PO-1,Acme Supply,Widgets,10,100.00,1000.00,2025-02-20\n"
    rec = "Receipt Number,PO Reference,Invoice Reference,Vendor,Description,Quantity Received,Receipt Date\nGRN-1,PO-1,INV-1,Acme Supply,Widgets,10,2025-02-24\n"
    return {
        "po_file": ("po.csv", po.encode(), "text/csv"),
        "invoice_file": ("inv.csv", inv.encode(), "text/csv"),
        "receipt_file": ("rec.csv", rec.encode(), "text/csv"),
    }


def _save(user, db_session, values: dict) -> None:
    user.settings = json.dumps({"three_way_match_config": values})
    db_session.flush()


@pytest.mark.usefixtures("bypass_csrf")
class TestTwmRunOverrides:
    @pytest.mark.asyncio
    async def test_no_run_values_reports_an_empty_disclosure(self, override_auth_verified):
        response = await _post("/audit/three-way-match", _twm_files())
        assert response.status_code == 200, response.text
        assert response.json()["settings_run_overrides"] == {}

    @pytest.mark.asyncio
    async def test_run_values_are_disclosed_as_applied(self, override_auth_verified):
        response = await _post(
            "/audit/three-way-match",
            _twm_files(),
            data={
                "fuzzy_composite_threshold": "0.8",
                "quantity_tolerance": "2",
                "enable_fuzzy_matching": "false",
                "date_window_days": "45",
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["config"]["fuzzy_composite_threshold"] == 0.8
        assert body["settings_run_overrides"] == {
            "date_window_days": 45,
            "enable_fuzzy_matching": False,
            "fuzzy_composite_threshold": 0.8,
            "quantity_tolerance": 2.0,
        }
        assert body["settings_applied"] == {}

    @pytest.mark.asyncio
    async def test_run_value_over_a_saved_one_is_disclosed_both_ways(self, override_auth_verified, db_session):
        _save(override_auth_verified, db_session, {"date_window_days": 60, "amount_tolerance": 5})
        response = await _post("/audit/three-way-match", _twm_files(), data={"date_window_days": "10"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["settings_run_overrides"] == {"date_window_days": 10}
        assert body["settings_applied"] == {"amount_tolerance": 5.0}
        assert body["settings_ignored"] == [
            {"key": "date_window_days", "reason": "Replaced by the value supplied for this run."}
        ]

    @pytest.mark.asyncio
    async def test_out_of_range_run_value_is_refused(self, override_auth_verified):
        response = await _post("/audit/three-way-match", _twm_files(), data={"fuzzy_composite_threshold": "1.5"})
        assert response.status_code == 400
        assert "fuzzy_composite_threshold" in response.json()["detail"]


# ─── Three-Way Match: column mapping is applied, never ignored ───────────

_ODD_PO_HEADER = "Doc Ref,Supplier Party,Item Text,Qty,Each,Line Value,Raised,Due"
_PO_MAPPING = {
    "po_number_column": "Doc Ref",
    "vendor_column": "Supplier Party",
    "total_amount_column": "Line Value",
    "quantity_column": "Qty",
    "unit_price_column": "Each",
}


@pytest.mark.usefixtures("bypass_csrf")
class TestTwmColumnMapping:
    @pytest.mark.asyncio
    async def test_mapping_is_applied_to_detection_and_matching(self, override_auth_verified):
        unmapped = await _post("/audit/three-way-match", _twm_files(_ODD_PO_HEADER))
        assert unmapped.status_code == 200, unmapped.text
        assert unmapped.json()["column_detection"]["po"]["po_number_column"] != "Doc Ref"
        assert unmapped.json()["summary"]["full_match_count"] == 0

        response = await _post(
            "/audit/three-way-match",
            _twm_files(_ODD_PO_HEADER),
            data={"po_column_mapping": json.dumps(_PO_MAPPING)},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        po_detection = body["column_detection"]["po"]
        assert po_detection["po_number_column"] == "Doc Ref"
        assert po_detection["vendor_column"] == "Supplier Party"
        assert po_detection["overall_confidence"] == 1.0
        assert po_detection["requires_mapping"] is False
        assert any("Manual column mapping applied" in n for n in po_detection["detection_notes"])
        assert body["summary"]["full_match_count"] == 1

    @pytest.mark.asyncio
    async def test_partial_mapping_keeps_the_detection_confidence(self, override_auth_verified):
        response = await _post(
            "/audit/three-way-match",
            _twm_files(_ODD_PO_HEADER),
            data={"po_column_mapping": json.dumps({"po_number_column": "Doc Ref"})},
        )
        assert response.status_code == 200, response.text
        po_detection = response.json()["column_detection"]["po"]
        assert po_detection["po_number_column"] == "Doc Ref"
        assert po_detection["overall_confidence"] < 1.0

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("field", "raw", "fragment"),
        [
            ("po_column_mapping", "{not json", "PO column mapping is not valid JSON."),
            ("invoice_column_mapping", json.dumps(["a"]), "Invoice column mapping must be an object"),
            ("receipt_column_mapping", json.dumps({"bogus_column": "X"}), "unknown field(s): bogus_column"),
            ("po_column_mapping", json.dumps({"vendor_column": 5}), "must name a column for: vendor_column"),
            ("po_column_mapping", json.dumps({"vendor_column": "Nope"}), "not in the file: 'Nope'"),
        ],
    )
    async def test_malformed_mapping_is_refused(self, override_auth_verified, field, raw, fragment):
        response = await _post("/audit/three-way-match", _twm_files(), data={field: raw})
        assert response.status_code == 400, response.text
        assert fragment in response.json()["detail"]


# ─── Three-Way Match memo states the per-run values ──────────────────────


def _pdf_text(pdf: bytes) -> str:
    import io

    from pypdf import PdfReader

    return " ".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(pdf)).pages).replace("\n", " ")


class TestTwmMemoRunOverrides:
    def test_memo_lists_run_values_separately(self):
        from tests.test_twm_memo import _make_twm_result
        from three_way_match_memo_generator import generate_three_way_match_memo

        result = _make_twm_result()
        result["settings_applied"] = {}
        result["settings_ignored"] = []
        result["settings_run_overrides"] = {"date_window_days": 45}
        text = _pdf_text(generate_three_way_match_memo(result))
        assert "Thresholds set for this run and from saved settings" in text
        assert "1 threshold was set by the preparer for this run only" in text
        assert "Date window days 45 30" in text
        assert "Every threshold used on this run was the Paciolus default" not in text

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_memo_export_accepts_the_field(self, override_auth_verified):
        from main import app
        from tests.test_twm_memo import _make_twm_result

        body = {**_make_twm_result(), "full_matches": []}
        body["settings_run_overrides"] = {"fuzzy_composite_threshold": 0.8}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/three-way-match-memo", json=body)
        assert response.status_code == 200, response.text
        assert "Fuzzy composite threshold 0.8 0.7" in _pdf_text(response.content)


# ─── W-2 supported years ─────────────────────────────────────────────────


class TestW2SupportedYears:
    @pytest.mark.asyncio
    async def test_lists_the_tabulated_years(self):
        from main import app
        from w2_reconciliation_engine import STATUTORY_LIMITS_BY_YEAR

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/audit/w2-reconciliation/supported-years")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["tax_years"] == sorted(STATUTORY_LIMITS_BY_YEAR)
        assert 2025 in body["tax_years"]
        assert body["note"]
