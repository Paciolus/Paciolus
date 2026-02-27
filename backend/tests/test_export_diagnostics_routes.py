"""
Phase LXII: Integration tests for routes/export_diagnostics.py.

Tests all 10 endpoints:
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
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Shared payloads
# ---------------------------------------------------------------------------

BASE_AUDIT = {
    "status": "balanced",
    "balanced": True,
    "total_debits": 100000.0,
    "total_credits": 100000.0,
    "difference": 0.0,
    "row_count": 10,
    "message": "Balanced",
    "abnormal_balances": [],
    "has_risk_alerts": False,
    "materiality_threshold": 1000.0,
    "material_count": 0,
    "immaterial_count": 0,
    "filename": "TestTB",
}

LEAD_SHEET_PAYLOAD = {
    "flux": {
        "items": [],
        "summary": {
            "total_items": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "new_accounts": 0,
            "removed_accounts": 0,
            "threshold": 1000.0,
        },
    },
    "recon": {
        "scores": [],
        "stats": {"high": 0, "medium": 0, "low": 0},
    },
    "filename": "TestLeadSheet",
}

FIN_STMT_PAYLOAD = {
    "lead_sheet_grouping": {"summaries": [{"category": "Assets", "debit": 50000.0, "credit": 0.0}]},
    "filename": "TestFinStmts",
}


# ---------------------------------------------------------------------------
# PDF Export
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportPdf:
    @pytest.mark.asyncio
    async def test_happy_path_returns_pdf(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 fake"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/pdf", json=BASE_AUDIT)

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_download_filename_uses_input_filename(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 fake"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/pdf", json={**BASE_AUDIT, "filename": "ClientABC"})

        assert response.status_code == 200
        assert "ClientABC" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_with_anomalies_still_200(self, override_auth_verified):
        from main import app

        payload = {
            **BASE_AUDIT,
            "abnormal_balances": [
                {
                    "account": "Suspense Clearing",
                    "type": "suspense",
                    "issue": "Uncleared balance",
                    "amount": 500.0,
                    "materiality": "immaterial",
                    "severity": "low",
                    "confidence": 0.8,
                    "anomaly_type": "suspense",
                }
            ],
            "immaterial_count": 1,
        }
        with patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 ok"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/pdf", json=payload)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/pdf", json=BASE_AUDIT)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Excel Export
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportExcel:
    @pytest.mark.asyncio
    async def test_happy_path_returns_xlsx(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_workpaper", return_value=b"PK\x03\x04 fake xlsx"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/excel", json=BASE_AUDIT)

        assert response.status_code == 200
        ct = response.headers["content-type"]
        assert "spreadsheetml" in ct or "vnd.ms-excel" in ct or "application/octet-stream" in ct

    @pytest.mark.asyncio
    async def test_download_header_contains_filename(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_workpaper", return_value=b"PK fake"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/excel", json={**BASE_AUDIT, "filename": "CorpClient"})

        assert response.status_code == 200
        assert "CorpClient" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/excel", json=BASE_AUDIT)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# CSV Trial Balance
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvTrialBalance:
    @pytest.mark.asyncio
    async def test_empty_anomalies_returns_csv(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=BASE_AUDIT)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        content = response.content.decode("utf-8-sig")
        assert "Reference" in content
        assert "Account" in content
        assert "TOTALS" in content

    @pytest.mark.asyncio
    async def test_anomaly_written_as_row(self, override_auth_verified):
        from main import app

        payload = {
            **BASE_AUDIT,
            "abnormal_balances": [
                {
                    "account": "Cash - Operating",
                    "type": "asset",
                    "issue": "Unusual debit",
                    "amount": 1000.0,
                    "debit": 1000.0,
                    "credit": 0.0,
                    "materiality": "material",
                    "severity": "high",
                    "confidence": 0.95,
                    "anomaly_type": "abnormal_balance",
                }
            ],
            "material_count": 1,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Cash - Operating" in content
        assert "TB-0001" in content

    @pytest.mark.asyncio
    async def test_classification_summary_populates_category(self, override_auth_verified):
        from main import app

        payload = {
            **BASE_AUDIT,
            "classification_summary": {"Assets": [{"account": "Cash", "confidence": 0.99}]},
            "abnormal_balances": [
                {
                    "account": "Cash",
                    "type": "asset",
                    "amount": 5000.0,
                    "materiality": "material",
                    "severity": "low",
                    "confidence": 0.9,
                    "anomaly_type": "abnormal_balance",
                }
            ],
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Assets" in content

    @pytest.mark.asyncio
    async def test_totals_row_matches_input(self, override_auth_verified):
        from main import app

        payload = {**BASE_AUDIT, "total_debits": 250000.0, "total_credits": 250000.0}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "250000.00" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=BASE_AUDIT)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# CSV Anomalies
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvAnomalies:
    @pytest.mark.asyncio
    async def test_empty_returns_summary_only(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=BASE_AUDIT)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "SUMMARY" in content
        assert "Material Count" in content
        assert "Total Anomalies" in content

    @pytest.mark.asyncio
    async def test_material_gets_m_prefix_immaterial_gets_i_prefix(self, override_auth_verified):
        from main import app

        payload = {
            **BASE_AUDIT,
            "abnormal_balances": [
                {
                    "account": "Revenue",
                    "type": "income",
                    "issue": "Large credit",
                    "amount": 50000.0,
                    "materiality": "material",
                    "severity": "high",
                    "confidence": 0.9,
                    "anomaly_type": "concentration",
                },
                {
                    "account": "Misc Expense",
                    "type": "expense",
                    "issue": "Small rounding",
                    "amount": 50.0,
                    "materiality": "immaterial",
                    "severity": "low",
                    "confidence": 0.5,
                    "anomaly_type": "rounding",
                },
            ],
            "material_count": 1,
            "immaterial_count": 1,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "TB-M001" in content
        assert "TB-I001" in content

    @pytest.mark.asyncio
    async def test_risk_summary_appended_when_present(self, override_auth_verified):
        from main import app

        payload = {
            **BASE_AUDIT,
            "risk_summary": {"concentration_risk": 2, "suspense_accounts": 1},
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "RISK BREAKDOWN" in content
        assert "Concentration Risk" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json=BASE_AUDIT)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Lead Sheets
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportLeadSheets:
    @pytest.mark.asyncio
    async def test_empty_flux_returns_xlsx(self, override_auth_verified):
        from main import app

        with patch("routes.export_diagnostics.generate_leadsheets", return_value=b"PK fake xlsx"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/leadsheets", json=LEAD_SHEET_PAYLOAD)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_with_flux_items_calls_generator(self, override_auth_verified):
        from main import app

        payload = {
            **LEAD_SHEET_PAYLOAD,
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
        }
        with patch("routes.export_diagnostics.generate_leadsheets", return_value=b"PK xlsx ok") as mock_gen:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/export/leadsheets", json=payload)

        assert response.status_code == 200
        mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/leadsheets", json=LEAD_SHEET_PAYLOAD)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Financial Statements
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportFinancialStatements:
    @pytest.mark.asyncio
    async def test_pdf_default_format(self, override_auth_verified):
        from main import app

        mock_builder = MagicMock()
        mock_builder.build.return_value = {}
        with patch("routes.export_diagnostics.FinancialStatementBuilder", return_value=mock_builder):
            with patch("routes.export_diagnostics.generate_financial_statements_pdf", return_value=b"%PDF-1.4 ok"):
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
    async def test_empty_summaries_returns_400(self, override_auth_verified):
        from main import app

        payload = {"lead_sheet_grouping": {"summaries": []}, "filename": "test"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements", json=payload)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_format_returns_422(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/financial-statements?format=csv", json=FIN_STMT_PAYLOAD)

        assert response.status_code == 422

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


# ---------------------------------------------------------------------------
# CSV Pre-Flight Issues
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvPreflightIssues:
    @pytest.mark.asyncio
    async def test_empty_issues_returns_header_only(self, override_auth_verified):
        from main import app

        payload = {"issues": [], "filename": "preflight"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/preflight-issues", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Category" in content
        assert "Severity" in content
        assert "Remediation" in content

    @pytest.mark.asyncio
    async def test_issue_row_written_correctly(self, override_auth_verified):
        from main import app

        payload = {
            "issues": [
                {
                    "category": "duplicate_accounts",
                    "severity": "error",
                    "message": "Duplicate account code detected",
                    "affected_count": 3,
                    "remediation": "Remove duplicate entries",
                }
            ],
            "filename": "preflight",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/preflight-issues", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        # category replaces _ with space and title-cases
        assert "Duplicate Accounts" in content
        assert "ERROR" in content
        assert "Remove duplicate entries" in content

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/preflight-issues", json={"issues": []})

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# CSV Population Profile
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvPopulationProfile:
    PAYLOAD = {
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
    }

    @pytest.mark.asyncio
    async def test_all_sections_present(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/population-profile", json=self.PAYLOAD)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "TB POPULATION PROFILE" in content
        assert "Gini Coefficient" in content
        assert "MAGNITUDE DISTRIBUTION" in content
        assert "TOP ACCOUNTS BY ABSOLUTE BALANCE" in content
        assert "Revenue" in content

    @pytest.mark.asyncio
    async def test_gini_value_formatted(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/population-profile", json=self.PAYLOAD)

        content = response.content.decode("utf-8-sig")
        assert "0.4500" in content  # gini_coefficient formatted to 4 decimal places

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/population-profile", json=self.PAYLOAD)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# CSV Expense Category Analytics
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvExpenseCategory:
    @pytest.mark.asyncio
    async def test_no_prior_period(self, override_auth_verified):
        from main import app

        payload = {
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
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/expense-category-analytics", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "EXPENSE CATEGORY ANALYTICAL PROCEDURES" in content
        assert "Cost of Sales" in content
        assert "15.00%" in content

    @pytest.mark.asyncio
    async def test_with_prior_period_adds_comparison_columns(self, override_auth_verified):
        from main import app

        payload = {
            "total_expenses": 50000.0,
            "total_revenue": 200000.0,
            "revenue_available": True,
            "prior_available": True,
            "materiality_threshold": 5000.0,
            "category_count": 1,
            "categories": [
                {
                    "label": "Cost of Sales",
                    "amount": 30000.0,
                    "pct_of_revenue": 15.0,
                    "prior_amount": 25000.0,
                    "dollar_change": 5000.0,
                    "exceeds_materiality": True,
                }
            ],
            "filename": "expense_prior",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/expense-category-analytics", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Prior Amount" in content
        assert "Dollar Change" in content
        assert "Yes" in content  # exceeds_materiality

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        payload = {
            "total_expenses": 0.0,
            "total_revenue": 0.0,
            "revenue_available": False,
            "prior_available": False,
            "materiality_threshold": 1000.0,
            "category_count": 0,
            "categories": [],
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/expense-category-analytics", json=payload)

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# CSV Accrual Completeness
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestExportCsvAccrualCompleteness:
    @pytest.mark.asyncio
    async def test_no_prior_period(self, override_auth_verified):
        from main import app

        payload = {
            "accrual_account_count": 5,
            "total_accrued_balance": 25000.0,
            "prior_available": False,
            "accrual_accounts": [
                {
                    "account_name": "Accrued Liabilities",
                    "balance": 15000.0,
                    "matched_keyword": "accru",
                }
            ],
            "threshold_pct": 15.0,
            "below_threshold": False,
            "filename": "accrual",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "ACCRUAL COMPLETENESS ESTIMATOR" in content
        assert "Accrued Liabilities" in content
        assert "15%" in content  # threshold_pct formatted as :.0f%

    @pytest.mark.asyncio
    async def test_with_prior_run_rate_and_narrative(self, override_auth_verified):
        from main import app

        payload = {
            "accrual_account_count": 3,
            "total_accrued_balance": 12000.0,
            "prior_available": True,
            "prior_operating_expenses": 80000.0,
            "monthly_run_rate": 6666.67,
            "accrual_to_run_rate_pct": 180.0,
            "accrual_accounts": [],
            "threshold_pct": 15.0,
            "below_threshold": False,
            "narrative": "Balance elevated relative to monthly run-rate.",
            "filename": "accrual_prior",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Monthly Run-Rate" in content
        assert "Prior Operating Expenses" in content
        assert "NARRATIVE" in content
        assert "elevated" in content

    @pytest.mark.asyncio
    async def test_below_threshold_flag(self, override_auth_verified):
        from main import app

        payload = {
            "accrual_account_count": 2,
            "total_accrued_balance": 1000.0,
            "prior_available": False,
            "accrual_accounts": [],
            "threshold_pct": 15.0,
            "below_threshold": True,
            "filename": "accrual_low",
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=payload)

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        assert "Yes" in content  # below_threshold = True

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self):
        from main import app

        payload = {
            "accrual_account_count": 0,
            "total_accrued_balance": 0.0,
            "prior_available": False,
            "accrual_accounts": [],
            "threshold_pct": 15.0,
            "below_threshold": False,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/accrual-completeness", json=payload)

        assert response.status_code == 401
