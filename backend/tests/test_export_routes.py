"""
Comprehensive integration tests for routes/export_diagnostics.py endpoints.

Tests all 10 diagnostic export endpoints:
- POST /export/pdf
- POST /export/excel
- POST /export/csv/trial-balance
- POST /export/csv/anomalies
- POST /export/leadsheets
- POST /export/financial-statements
- POST /export/csv/preflight-issues
- POST /export/csv/population-profile
- POST /export/csv/expense-category-analytics
- POST /export/csv/accrual-completeness

Covers: auth (401), validation (422), happy-path (200), content assertions.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

MINIMAL_AUDIT_PAYLOAD = {
    "status": "balanced",
    "balanced": True,
    "total_debits": 100000.00,
    "total_credits": 100000.00,
    "difference": 0.00,
    "row_count": 10,
    "message": "Trial balance is balanced",
    "abnormal_balances": [
        {
            "account": "Cash",
            "type": "asset",
            "issue": "test anomaly",
            "amount": 1000.00,
            "materiality": "material",
            "severity": "high",
            "anomaly_type": "abnormal_balance",
            "confidence": 0.9,
        }
    ],
    "has_risk_alerts": True,
    "materiality_threshold": 500.00,
    "material_count": 1,
    "immaterial_count": 0,
    "filename": "test_export.csv",
    "classification_summary": {"assets": [{"account": "Cash", "confidence": 0.95}]},
    "risk_summary": {"high": 1, "medium": 0, "low": 0},
}

EMPTY_AUDIT_PAYLOAD = {
    "status": "balanced",
    "balanced": True,
    "total_debits": 0.0,
    "total_credits": 0.0,
    "difference": 0.0,
    "row_count": 0,
    "message": "Empty",
    "abnormal_balances": [],
    "has_risk_alerts": False,
    "materiality_threshold": 1000.0,
    "material_count": 0,
    "immaterial_count": 0,
}

LEAD_SHEET_PAYLOAD = {
    "flux": {
        "items": [
            {
                "account": "Cash",
                "type": "asset",
                "current": 50000.0,
                "prior": 40000.0,
                "delta_amount": 10000.0,
                "delta_percent": 25.0,
                "is_new": False,
                "is_removed": False,
                "sign_flip": False,
                "risk_level": "low",
                "variance_indicators": [],
            }
        ],
        "summary": {
            "total_items": 1,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "new_accounts": 0,
            "removed_accounts": 0,
            "threshold": 1000.0,
        },
    },
    "recon": {
        "scores": [
            {
                "account": "Cash",
                "score": 25,
                "band": "low",
                "factors": ["Normal activity"],
                "action": "Standard review",
            }
        ],
        "stats": {"high": 0, "medium": 0, "low": 1},
    },
    "filename": "TestLeadSheets",
}

FIN_STMT_PAYLOAD = {
    "lead_sheet_grouping": {
        "summaries": [
            {"category": "Assets", "debit": 50000.0, "credit": 0.0},
            {"category": "Liabilities", "debit": 0.0, "credit": 30000.0},
        ]
    },
    "filename": "TestFinancialStatements",
    "entity_name": "Acme Corp",
    "period_end": "2025-12-31",
}

PREFLIGHT_PAYLOAD = {
    "issues": [
        {
            "category": "missing_data",
            "severity": "warning",
            "message": "Some rows have empty account names",
            "affected_count": 5,
            "remediation": "Fill in missing account names",
        }
    ],
    "filename": "preflight_test",
}

POP_PROFILE_PAYLOAD = {
    "account_count": 25,
    "total_abs_balance": 500000.0,
    "mean_abs_balance": 20000.0,
    "median_abs_balance": 15000.0,
    "std_dev_abs_balance": 8000.0,
    "min_abs_balance": 50.0,
    "max_abs_balance": 120000.0,
    "p25": 5000.0,
    "p75": 35000.0,
    "gini_coefficient": 0.38,
    "gini_interpretation": "Moderate",
    "buckets": [{"label": "< $1K", "count": 3, "percent_count": 12.0, "sum_abs": 1500.0}],
    "top_accounts": [
        {
            "rank": 1,
            "account": "Revenue",
            "category": "Income",
            "net_balance": 120000.0,
            "abs_balance": 120000.0,
            "percent_of_total": 24.0,
        }
    ],
    "filename": "pop_profile_test",
}

EXPENSE_CATEGORY_PAYLOAD = {
    "total_expenses": 75000.0,
    "total_revenue": 300000.0,
    "revenue_available": True,
    "prior_available": False,
    "materiality_threshold": 5000.0,
    "category_count": 2,
    "categories": [
        {"label": "Office Supplies", "amount": 25000.0, "pct_of_revenue": 8.33},
        {"label": "Professional Fees", "amount": 50000.0, "pct_of_revenue": 16.67},
    ],
    "filename": "expense_cat_test",
}

ACCRUAL_PAYLOAD = {
    "accrual_account_count": 3,
    "total_accrued_balance": 18000.0,
    "prior_available": False,
    "accrual_accounts": [
        {
            "account_name": "Accrued Wages",
            "balance": 12000.0,
            "matched_keyword": "accru",
        },
        {
            "account_name": "Accrued Utilities",
            "balance": 6000.0,
            "matched_keyword": "accru",
        },
    ],
    "threshold_pct": 15.0,
    "below_threshold": False,
    "filename": "accrual_test",
}


# ---------------------------------------------------------------------------
# 1. PDF Export
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestPdfExport:
    """POST /export/pdf — generates PDF audit report."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_pdf_content_type(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 fake content"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/pdf", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_response_has_content_disposition_attachment(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 data"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/pdf", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "test_export" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/pdf", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/pdf", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_field_returns_422(self, override_auth_verified):
        from main import app

        # Missing 'balanced', 'row_count', 'message', etc.
        partial = {"status": "balanced", "total_debits": 100.0}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/pdf", json=partial)

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 2. Excel Export
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExcelExport:
    """POST /export/excel — generates Excel workpaper."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_excel_content_type(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_workpaper", return_value=b"PK\x03\x04 fake xlsx"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/excel", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 200
        ct = response.headers["content-type"]
        assert "spreadsheetml" in ct or "vnd.ms-excel" in ct or "application/octet-stream" in ct

    @pytest.mark.asyncio
    async def test_response_body_is_non_empty(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_workpaper", return_value=b"PK\x03\x04 excel bytes"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/excel", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/excel", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/excel", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 3. CSV Trial Balance
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvTrialBalanceExport:
    """POST /export/csv/trial-balance — CSV trial balance export."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_csv_content(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        content = response.content.decode("utf-8-sig")
        assert "Reference" in content
        assert "Account" in content
        assert "TOTALS" in content

    @pytest.mark.asyncio
    async def test_anomaly_appears_in_csv_rows(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=MINIMAL_AUDIT_PAYLOAD)

        content = response.content.decode("utf-8-sig")
        assert "Cash" in content
        assert "TB-0001" in content

    @pytest.mark.asyncio
    async def test_totals_match_input_values(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=MINIMAL_AUDIT_PAYLOAD)

        content = response.content.decode("utf-8-sig")
        assert "100000.00" in content

    @pytest.mark.asyncio
    async def test_empty_anomalies_still_returns_csv(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=EMPTY_AUDIT_PAYLOAD)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "TOTALS" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. CSV Anomalies
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvAnomaliesExport:
    """POST /export/csv/anomalies — CSV anomaly list export."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_csv_content(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        content = response.content.decode("utf-8-sig")
        assert "Reference" in content
        assert "SUMMARY" in content

    @pytest.mark.asyncio
    async def test_material_anomaly_gets_m_prefix(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=MINIMAL_AUDIT_PAYLOAD)

        content = response.content.decode("utf-8-sig")
        assert "TB-M001" in content
        assert "Cash" in content

    @pytest.mark.asyncio
    async def test_immaterial_anomaly_gets_i_prefix(self, override_auth_verified):
        from main import app

        payload = {
            **MINIMAL_AUDIT_PAYLOAD,
            "abnormal_balances": [
                {
                    "account": "Petty Cash",
                    "type": "asset",
                    "issue": "small variance",
                    "amount": 25.0,
                    "materiality": "immaterial",
                    "severity": "low",
                    "anomaly_type": "rounding",
                    "confidence": 0.5,
                }
            ],
            "material_count": 0,
            "immaterial_count": 1,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=payload)

        content = response.content.decode("utf-8-sig")
        assert "TB-I001" in content

    @pytest.mark.asyncio
    async def test_risk_summary_section_present(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=MINIMAL_AUDIT_PAYLOAD)

        content = response.content.decode("utf-8-sig")
        assert "RISK BREAKDOWN" in content
        assert "High" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=MINIMAL_AUDIT_PAYLOAD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 5. Lead Sheets
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestLeadSheetsExport:
    """POST /export/leadsheets — Excel lead sheets export."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_leadsheets", return_value=b"PK\x03\x04 fake xlsx"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/leadsheets", json=LEAD_SHEET_PAYLOAD)

        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_generator_receives_correct_data(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_leadsheets", return_value=b"PK fake") as mock_gen:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/leadsheets", json=LEAD_SHEET_PAYLOAD)

        assert response.status_code == 200
        mock_gen.assert_called_once()
        # First arg is FluxResult, second is ReconResult, third is filename
        args = mock_gen.call_args
        assert args[0][2] == "TestLeadSheets"

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/leadsheets", json=LEAD_SHEET_PAYLOAD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/leadsheets", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_recon_returns_422(self, override_auth_verified):
        from main import app

        partial = {"flux": LEAD_SHEET_PAYLOAD["flux"], "filename": "test"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/leadsheets", json=partial)

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 6. Financial Statements
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestFinancialStatementsExport:
    """POST /export/financial-statements — PDF or Excel financial statements."""

    @pytest.mark.asyncio
    async def test_pdf_format_default_returns_pdf(self, override_auth_verified):
        from main import app

        mock_builder = MagicMock()
        mock_builder.build.return_value = {}
        with patch("routes.export_diagnostics.FinancialStatementBuilder", return_value=mock_builder):
            with patch("routes.export_diagnostics.generate_financial_statements_pdf", return_value=b"%PDF-1.4 fs"):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/export/financial-statements", json=FIN_STMT_PAYLOAD)

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_excel_format_query_param(self, override_auth_verified):
        from main import app

        mock_builder = MagicMock()
        mock_builder.build.return_value = {}
        with patch("routes.export_diagnostics.FinancialStatementBuilder", return_value=mock_builder):
            with patch(
                "routes.export_diagnostics.generate_financial_statements_excel", return_value=b"PK xlsx"
            ) as mock_excel:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/export/financial-statements?format=excel", json=FIN_STMT_PAYLOAD)

        assert response.status_code == 200
        mock_excel.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_format_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements?format=csv", json=FIN_STMT_PAYLOAD)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_summaries_returns_400(self, override_auth_verified):
        from main import app

        payload = {"lead_sheet_grouping": {"summaries": []}, "filename": "empty"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements", json=payload)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_lead_sheet_grouping_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements", json={"filename": "test"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements", json=FIN_STMT_PAYLOAD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_body_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 7. CSV Pre-Flight Issues
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvPreflightIssuesExport:
    """POST /export/csv/preflight-issues — CSV pre-flight issues export."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_csv(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/preflight-issues", json=PREFLIGHT_PAYLOAD)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        content = response.content.decode("utf-8-sig")
        assert "Category" in content
        assert "Severity" in content
        assert "Missing Data" in content  # category title-cased with underscore replaced

    @pytest.mark.asyncio
    async def test_empty_issues_returns_header_only(self, override_auth_verified):
        from main import app

        payload = {"issues": [], "filename": "preflight_empty"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/preflight-issues", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Category" in content
        assert "Remediation" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/preflight-issues", json=PREFLIGHT_PAYLOAD)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# 8. CSV Population Profile
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvPopulationProfileExport:
    """POST /export/csv/population-profile — CSV population profile export."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_all_sections(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/population-profile", json=POP_PROFILE_PAYLOAD)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "TB POPULATION PROFILE" in content
        assert "MAGNITUDE DISTRIBUTION" in content
        assert "TOP ACCOUNTS BY ABSOLUTE BALANCE" in content
        assert "Gini Coefficient" in content
        assert "0.3800" in content  # gini formatted to 4 decimals

    @pytest.mark.asyncio
    async def test_top_accounts_data_present(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/population-profile", json=POP_PROFILE_PAYLOAD)

        content = response.content.decode("utf-8-sig")
        assert "Revenue" in content
        assert "120000.00" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/population-profile", json=POP_PROFILE_PAYLOAD)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# 9. CSV Expense Category Analytics
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvExpenseCategoryExport:
    """POST /export/csv/expense-category-analytics — CSV expense categories."""

    @pytest.mark.asyncio
    async def test_no_prior_period_returns_basic_columns(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/expense-category-analytics", json=EXPENSE_CATEGORY_PAYLOAD)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "EXPENSE CATEGORY ANALYTICAL PROCEDURES" in content
        assert "Office Supplies" in content
        assert "Professional Fees" in content
        assert "16.67%" in content

    @pytest.mark.asyncio
    async def test_with_prior_period_adds_comparison_columns(self, override_auth_verified):
        from main import app

        payload = {
            **EXPENSE_CATEGORY_PAYLOAD,
            "prior_available": True,
            "categories": [
                {
                    "label": "Office Supplies",
                    "amount": 25000.0,
                    "pct_of_revenue": 8.33,
                    "prior_amount": 20000.0,
                    "dollar_change": 5000.0,
                    "exceeds_threshold": True,
                }
            ],
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/expense-category-analytics", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Prior Amount" in content
        assert "Dollar Change" in content
        assert "Yes" in content  # exceeds_threshold

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/expense-category-analytics", json=EXPENSE_CATEGORY_PAYLOAD)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# 10. CSV Accrual Completeness
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestCsvAccrualCompletenessExport:
    """POST /export/csv/accrual-completeness — CSV accrual completeness."""

    @pytest.mark.asyncio
    async def test_authenticated_returns_200_with_sections(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=ACCRUAL_PAYLOAD)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "ACCRUAL COMPLETENESS ESTIMATOR" in content
        assert "ACCRUAL ACCOUNTS" in content
        assert "Accrued Wages" in content
        assert "12000.00" in content

    @pytest.mark.asyncio
    async def test_with_prior_and_narrative(self, override_auth_verified):
        from main import app

        payload = {
            **ACCRUAL_PAYLOAD,
            "prior_available": True,
            "prior_operating_expenses": 60000.0,
            "monthly_run_rate": 5000.0,
            "accrual_to_run_rate_pct": 360.0,
            "narrative": "Accrual balance significantly exceeds monthly run-rate.",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Prior Operating Expenses" in content
        assert "Monthly Run-Rate" in content
        assert "NARRATIVE" in content
        assert "exceeds" in content

    @pytest.mark.asyncio
    async def test_below_threshold_flag_shows_yes(self, override_auth_verified):
        from main import app

        payload = {**ACCRUAL_PAYLOAD, "below_threshold": True}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Yes" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=ACCRUAL_PAYLOAD)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Cross-cutting: validation errors
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestValidationErrors:
    """Verify that invalid payloads return 422 across multiple endpoints."""

    @pytest.mark.asyncio
    async def test_pdf_invalid_type_for_total_debits_returns_422(self, override_auth_verified):
        from main import app

        payload = {**MINIMAL_AUDIT_PAYLOAD, "total_debits": "not_a_number"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/pdf", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_csv_anomalies_invalid_type_returns_422(self, override_auth_verified):
        from main import app

        payload = {**MINIMAL_AUDIT_PAYLOAD, "abnormal_balances": "not_a_list"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_leadsheets_invalid_flux_structure_returns_422(self, override_auth_verified):
        from main import app

        payload = {"flux": "bad", "recon": "bad", "filename": "test"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/leadsheets", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_financial_statements_invalid_grouping_type_returns_422(self, override_auth_verified):
        from main import app

        payload = {"lead_sheet_grouping": "not_a_dict"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements", json=payload)

        assert response.status_code == 422
