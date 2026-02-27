"""
Phase LXII: Integration tests for routes/export_testing.py.

Tests all 9 CSV export endpoints:
- POST /export/csv/je-testing
- POST /export/csv/ap-testing
- POST /export/csv/payroll-testing
- POST /export/csv/three-way-match
- POST /export/csv/revenue-testing
- POST /export/csv/ar-aging
- POST /export/csv/fixed-assets
- POST /export/csv/inventory
- POST /export/csv/sampling-selection

All endpoints return CSV — no mocking needed.
"""

import httpx
import pytest

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

COMPOSITE_SCORE = {
    "score": 78.5,
    "risk_tier": "low",
    "total_flagged": 0,
    "tests_run": 8,
    "tests_skipped": 0,
    "has_subledger": False,
}

DATA_QUALITY = {"overall_quality": "good", "issues": []}


def _flagged_entry(test_name, test_key, entry, severity="medium", confidence=0.8):
    """Build a standard flagged_entry dict."""
    return {
        "test_name": test_name,
        "test_key": test_key,
        "test_tier": "tier2",
        "severity": severity,
        "issue": f"{test_name} issue detected",
        "confidence": confidence,
        "entry": entry,
    }


# ---------------------------------------------------------------------------
# JE Testing CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvJETesting:
    @pytest.mark.asyncio
    async def test_empty_test_results_returns_header(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "data_quality": DATA_QUALITY,
            "filename": "je_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/je-testing", json=payload)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        content = response.content.decode("utf-8-sig")
        assert "Test" in content
        assert "Entry ID" in content

    @pytest.mark.asyncio
    async def test_flagged_entry_written_as_row(self, override_auth_verified):
        from main import app

        entry = {
            "entry_id": "JE-0042",
            "posting_date": "2024-01-15",
            "account": "Cash - Operating",
            "description": "Late night journal adjustment",
            "debit": 5000.0,
            "credit": 0.0,
        }
        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [{"flagged_entries": [_flagged_entry("Unusual Hours", "JT-04", entry, severity="high")]}],
            "data_quality": DATA_QUALITY,
            "filename": "je_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/je-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "JE-0042" in content
        assert "Unusual Hours" in content
        assert "Cash - Operating" in content

    @pytest.mark.asyncio
    async def test_download_header_attachment(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "data_quality": DATA_QUALITY,
            "filename": "my_je_file",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/je-testing", json=payload)

        assert "attachment" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/je-testing",
                json={"composite_score": COMPOSITE_SCORE, "test_results": [], "data_quality": DATA_QUALITY},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# AP Testing CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvAPTesting:
    @pytest.mark.asyncio
    async def test_empty_returns_header(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "data_quality": DATA_QUALITY,
            "filename": "ap_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/ap-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Vendor" in content
        assert "Invoice #" in content

    @pytest.mark.asyncio
    async def test_flagged_payment_written(self, override_auth_verified):
        from main import app

        entry = {
            "vendor_name": "Acme Supplies Ltd",
            "invoice_number": "INV-9999",
            "payment_date": "2024-02-01",
            "amount": 1500.0,
            "check_number": "CHK-100",
            "description": "Office supplies Q1",
        }
        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [
                {"flagged_entries": [_flagged_entry("Duplicate Invoice", "AP-02", entry, severity="high")]}
            ],
            "data_quality": DATA_QUALITY,
            "filename": "ap_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/ap-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Acme Supplies Ltd" in content
        assert "INV-9999" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/ap-testing",
                json={"composite_score": COMPOSITE_SCORE, "test_results": [], "data_quality": DATA_QUALITY},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Payroll Testing CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvPayrollTesting:
    @pytest.mark.asyncio
    async def test_empty_returns_header(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "data_quality": DATA_QUALITY,
            "filename": "payroll_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/payroll-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Employee" in content
        assert "Department" in content

    @pytest.mark.asyncio
    async def test_flagged_employee_written(self, override_auth_verified):
        from main import app

        entry = {
            "employee_name": "Jane Ghost",
            "employee_id": "EMP-0099",
            "department": "Operations",
            "pay_date": "2024-03-31",
            "gross_pay": 8500.0,
        }
        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [{"flagged_entries": [_flagged_entry("Ghost Employee", "PR-05", entry, severity="high")]}],
            "data_quality": DATA_QUALITY,
            "filename": "payroll_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/payroll-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Jane Ghost" in content
        assert "EMP-0099" in content
        assert "8500.00" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/payroll-testing",
                json={"composite_score": COMPOSITE_SCORE, "test_results": [], "data_quality": DATA_QUALITY},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Three-Way Match CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvThreeWayMatch:
    TWM_SUMMARY = {
        "total_pos": 10,
        "total_invoices": 10,
        "total_receipts": 9,
        "full_match_count": 8,
        "partial_match_count": 1,
        "full_match_rate": 0.8,
        "net_variance": 500.0,
        "risk_assessment": "Low Risk",
    }

    @pytest.mark.asyncio
    async def test_no_matches_returns_summary(self, override_auth_verified):
        from main import app

        payload = {
            "summary": self.TWM_SUMMARY,
            "full_matches": [],
            "partial_matches": [],
            "filename": "twm_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/three-way-match", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Match Type" in content
        assert "SUMMARY" in content
        assert "Full Match Rate" in content
        assert "Low Risk" in content

    @pytest.mark.asyncio
    async def test_full_match_written_as_row(self, override_auth_verified):
        from main import app

        payload = {
            "summary": self.TWM_SUMMARY,
            "full_matches": [
                {
                    "match_type": "full",
                    "match_confidence": 0.98,
                    "variances": [],
                    "po": {"po_number": "PO-001", "vendor": "Acme Corp", "total_amount": 5000.0},
                    "invoice": {"invoice_number": "INV-001", "total_amount": 5000.0},
                    "receipt": {"receipt_number": "REC-001", "total_amount": 5000.0},
                }
            ],
            "partial_matches": [],
            "filename": "twm_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/three-way-match", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "PO-001" in content
        assert "INV-001" in content
        assert "REC-001" in content

    @pytest.mark.asyncio
    async def test_partial_match_also_written(self, override_auth_verified):
        from main import app

        payload = {
            "summary": self.TWM_SUMMARY,
            "full_matches": [],
            "partial_matches": [
                {
                    "match_type": "partial",
                    "match_confidence": 0.72,
                    "variances": [{"variance_amount": 100.0, "variance_pct": 0.02}],
                    "po": {"po_number": "PO-002", "vendor": "Beta LLC", "total_amount": 5100.0},
                    "invoice": {"invoice_number": "INV-002", "total_amount": 5000.0},
                    "receipt": {"receipt_number": "REC-002", "total_amount": 5000.0},
                }
            ],
            "filename": "twm_partial",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/three-way-match", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "PO-002" in content
        assert "partial" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/three-way-match",
                json={"summary": self.TWM_SUMMARY, "full_matches": [], "partial_matches": []},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Revenue Testing CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvRevenueTesting:
    @pytest.mark.asyncio
    async def test_empty_returns_header(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "data_quality": DATA_QUALITY,
            "filename": "revenue_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/revenue-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Account Name" in content
        assert "Entry Type" in content

    @pytest.mark.asyncio
    async def test_flagged_entry_written(self, override_auth_verified):
        from main import app

        entry = {
            "account_name": "Revenue - Product Sales",
            "account_number": "4000",
            "date": "2024-03-29",
            "amount": 120000.0,
            "description": "Bulk order Q4",
            "entry_type": "credit",
            "reference": "ORD-9876",
        }
        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [{"flagged_entries": [_flagged_entry("End-of-Period Spike", "RT-07", entry)]}],
            "data_quality": DATA_QUALITY,
            "filename": "revenue_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/revenue-testing", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Revenue - Product Sales" in content
        assert "ORD-9876" in content
        assert "120000.00" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/revenue-testing",
                json={"composite_score": COMPOSITE_SCORE, "test_results": [], "data_quality": DATA_QUALITY},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# AR Aging CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvARAging:
    AR_SCORE = {**COMPOSITE_SCORE, "has_subledger": True}

    @pytest.mark.asyncio
    async def test_empty_returns_summary_with_has_subledger(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": self.AR_SCORE,
            "test_results": [],
            "data_quality": DATA_QUALITY,
            "filename": "ar_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/ar-aging", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "SUMMARY" in content
        assert "Has Sub-Ledger" in content

    @pytest.mark.asyncio
    async def test_flagged_receivable_written(self, override_auth_verified):
        from main import app

        entry = {
            "account_name": "Accounts Receivable",
            "customer_name": "Slow Payer Inc",
            "invoice_number": "INV-555",
            "date": "2023-09-01",
            "amount": 75000.0,
            "aging_days": 210,
        }
        payload = {
            "composite_score": self.AR_SCORE,
            "test_results": [
                {"flagged_entries": [_flagged_entry("Overdue Receivable", "AR-03", entry, severity="high")]}
            ],
            "data_quality": DATA_QUALITY,
            "filename": "ar_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/ar-aging", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Slow Payer Inc" in content
        assert "75000.00" in content
        assert "210" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/ar-aging",
                json={"composite_score": self.AR_SCORE, "test_results": [], "data_quality": DATA_QUALITY},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Fixed Asset Testing CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvFixedAssets:
    @pytest.mark.asyncio
    async def test_empty_returns_header(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "filename": "fa_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/fixed-assets", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Asset ID" in content
        assert "Accum Depreciation" in content

    @pytest.mark.asyncio
    async def test_flagged_asset_written(self, override_auth_verified):
        from main import app

        entry = {
            "asset_id": "AST-0012",
            "description": "Forklift Model X",
            "category": "Equipment",
            "cost": 45000.0,
            "accumulated_depreciation": 45000.0,
            "useful_life": 5,
            "acquisition_date": "2018-01-01",
        }
        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [{"flagged_entries": [_flagged_entry("Fully Depreciated In-Use", "FA-05", entry)]}],
            "filename": "fa_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/fixed-assets", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "AST-0012" in content
        assert "Forklift Model X" in content
        assert "45000.00" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/fixed-assets",
                json={"composite_score": COMPOSITE_SCORE, "test_results": []},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Inventory Testing CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvInventory:
    @pytest.mark.asyncio
    async def test_empty_returns_header(self, override_auth_verified):
        from main import app

        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [],
            "filename": "inv_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/inventory", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Item ID" in content
        assert "Extended Value" in content

    @pytest.mark.asyncio
    async def test_flagged_item_written(self, override_auth_verified):
        from main import app

        entry = {
            "item_id": "ITEM-0056",
            "description": "Widget Part #7",
            "category": "Raw Materials",
            "quantity": 500.0,
            "unit_cost": 12.50,
            "extended_value": 6250.0,
            "location": "Warehouse B",
            "last_movement_date": "2023-06-01",
        }
        payload = {
            "composite_score": COMPOSITE_SCORE,
            "test_results": [{"flagged_entries": [_flagged_entry("Slow Moving", "INV-07", entry)]}],
            "filename": "inv_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/inventory", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "ITEM-0056" in content
        assert "Widget Part #7" in content
        assert "Warehouse B" in content
        assert "6250.00" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/inventory",
                json={"composite_score": COMPOSITE_SCORE, "test_results": []},
            )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Sampling Selection CSV
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvSamplingSelection:
    @pytest.mark.asyncio
    async def test_no_items_returns_header_and_summary(self, override_auth_verified):
        from main import app

        payload = {
            "selected_items": [],
            "method": "mus",
            "population_size": 1000,
            "population_value": 5000000.0,
            "filename": "sampling_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/sampling-selection", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Row #" in content
        assert "Audited Amount" in content
        assert "SUMMARY" in content
        assert "MUS" in content

    @pytest.mark.asyncio
    async def test_item_row_written_with_blank_audited_amount(self, override_auth_verified):
        from main import app

        payload = {
            "selected_items": [
                {
                    "row_index": 1,
                    "item_id": "INV-0001",
                    "description": "Q1 shipment payment",
                    "recorded_amount": 12500.0,
                    "stratum": "high_value",
                    "selection_method": "mus",
                }
            ],
            "method": "mus",
            "population_size": 500,
            "population_value": 2500000.0,
            "filename": "sampling_test",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/sampling-selection", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "INV-0001" in content
        assert "12500.00" in content
        assert "high_value" in content

    @pytest.mark.asyncio
    async def test_random_method_in_summary(self, override_auth_verified):
        from main import app

        payload = {
            "selected_items": [],
            "method": "random",
            "population_size": 200,
            "population_value": 800000.0,
            "filename": "sampling_random",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/sampling-selection", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "RANDOM" in content
        assert "200" in content

    @pytest.mark.asyncio
    async def test_population_stats_in_summary(self, override_auth_verified):
        from main import app

        payload = {
            "selected_items": [],
            "method": "mus",
            "population_size": 750,
            "population_value": 3000000.0,
            "filename": "sampling_stats",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/sampling-selection", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Population Size" in content
        assert "Population Value" in content
        assert "750" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/sampling-selection",
                json={"selected_items": [], "method": "mus", "population_size": 100, "population_value": 0.0},
            )

        assert response.status_code == 401
