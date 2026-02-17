"""
Tests for Multi-Period Comparison Memo Generator (Sprint 128)

Tests:
- PDF generation and validation
- Optional workpaper parameters
- Conclusion tier coverage (0 sig, low, moderate, elevated)
- Lead sheet summary handling
- Guardrail compliance (terminology, ISA references)
- Export route registration
- Pydantic input model validation
"""

import inspect

import pytest

from multi_period_memo_generator import generate_multi_period_memo

# =============================================================================
# FIXTURES
# =============================================================================

def _make_comparison_result(
    total_accounts: int = 80,
    material: int = 3,
    significant: int = 8,
    minor: int = 69,
    num_significant_movements: int = 11,
    num_lead_sheets: int = 5,
    budget_label: str | None = None,
    dormant_count: int = 2,
) -> dict:
    """Build a minimal MovementSummaryResponse-shaped dict for testing."""
    significant_movements = []
    for i in range(num_significant_movements):
        ls_idx = (i % num_lead_sheets) if num_lead_sheets > 0 else 0
        significant_movements.append({
            "account_name": f"Account {i + 1}",
            "account_type": "asset" if i % 2 == 0 else "liability",
            "prior_balance": 10000.0 * (i + 1),
            "current_balance": 10000.0 * (i + 1) + 5000.0 * ((-1) ** i),
            "change_amount": 5000.0 * ((-1) ** i),
            "change_percent": 50.0 * ((-1) ** i) / (i + 1),
            "movement_type": "increase" if i % 2 == 0 else "decrease",
            "significance": "material" if i < material else "significant",
            "lead_sheet": chr(65 + ls_idx),
            "lead_sheet_name": f"Lead Sheet {chr(65 + ls_idx)}",
            "lead_sheet_category": "asset" if i % 2 == 0 else "liability",
            "is_dormant": False,
        })

    lead_sheet_summaries = []
    for j in range(num_lead_sheets):
        lead_sheet_summaries.append({
            "lead_sheet": chr(65 + j),
            "lead_sheet_name": f"Lead Sheet {chr(65 + j)}",
            "lead_sheet_category": "asset" if j < 3 else "liability",
            "prior_total": 50000.0 * (j + 1),
            "current_total": 55000.0 * (j + 1),
            "net_change": 5000.0 * (j + 1),
            "change_percent": 10.0,
            "account_count": total_accounts // num_lead_sheets,
            "movements": [],
        })

    result = {
        "prior_label": "FY2024",
        "current_label": "FY2025",
        "total_accounts": total_accounts,
        "movements_by_type": {
            "increase": 30,
            "decrease": 25,
            "new_account": 5,
            "closed_account": 2,
            "sign_change": 1,
            "unchanged": 17,
        },
        "movements_by_significance": {
            "material": material,
            "significant": significant,
            "minor": minor,
        },
        "significant_movements": significant_movements,
        "lead_sheet_summaries": lead_sheet_summaries,
        "dormant_account_count": dormant_count,
    }
    if budget_label:
        result["budget_label"] = budget_label
    return result


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================

class TestMultiPeriodMemoGeneration:
    """Test PDF generation for multi-period comparison memos."""

    def test_generates_pdf_bytes(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_comparison_result()
        pdf = generate_multi_period_memo(
            result,
            filename="test_multi_period",
            client_name="TestCo Ltd",
            period_tested="FY2024 vs FY2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_zero_significant_conclusion(self):
        """No material/significant movements -> optimistic conclusion."""
        result = _make_comparison_result(
            material=0,
            significant=0,
            minor=80,
            num_significant_movements=0,
        )
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_low_rate_conclusion(self):
        """sig_rate <= 0.15 -> investigate conclusion."""
        result = _make_comparison_result(
            total_accounts=100,
            material=2,
            significant=8,
            minor=90,
            num_significant_movements=10,
        )
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_moderate_rate_conclusion(self):
        """0.15 < sig_rate <= 0.30 -> MODERATE conclusion."""
        result = _make_comparison_result(
            total_accounts=100,
            material=10,
            significant=15,
            minor=75,
            num_significant_movements=25,
        )
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_elevated_rate_conclusion(self):
        """sig_rate > 0.30 -> ELEVATED conclusion."""
        result = _make_comparison_result(
            total_accounts=50,
            material=10,
            significant=10,
            minor=30,
            num_significant_movements=20,
        )
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_budget_label(self):
        result = _make_comparison_result(budget_label="Budget 2025")
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_dormant_accounts(self):
        result = _make_comparison_result(dormant_count=0)
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_lead_sheet_summaries(self):
        result = _make_comparison_result(num_lead_sheets=0)
        result["lead_sheet_summaries"] = []
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_many_significant_movements(self):
        """More than 25 significant movements -> truncation message."""
        result = _make_comparison_result(
            total_accounts=200,
            material=15,
            significant=25,
            minor=160,
            num_significant_movements=40,
        )
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_empty_result(self):
        """Edge case: minimal data."""
        result = {
            "prior_label": "Prior",
            "current_label": "Current",
            "total_accounts": 0,
            "movements_by_type": {},
            "movements_by_significance": {},
            "significant_movements": [],
            "lead_sheet_summaries": [],
            "dormant_account_count": 0,
        }
        pdf = generate_multi_period_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestMultiPeriodMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(generate_multi_period_memo)
        assert "ISA 520" in source
        assert "PCAOB AS 2305" in source

    def test_no_forbidden_audit_assertions(self):
        source = inspect.getsource(generate_multi_period_memo)
        forbidden = [
            "financial statements are correct",
            "no misstatement exists",
            "accounts are fairly stated",
            "we conclude that",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"

    def test_disclaimer_called(self):
        source = inspect.getsource(generate_multi_period_memo)
        assert "build_disclaimer" in source

    def test_workpaper_signoff_called(self):
        source = inspect.getsource(generate_multi_period_memo)
        assert "build_workpaper_signoff" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================

class TestMultiPeriodMemoExportRoute:
    """Verify the export route is registered."""

    def test_multi_period_memo_route_exists(self):
        from main import app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        assert "/export/multi-period-memo" in routes

    def test_multi_period_memo_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/export/multi-period-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/multi-period-memo not found")


# =============================================================================
# PYDANTIC INPUT MODEL
# =============================================================================

class TestMultiPeriodMemoInput:
    """Verify the Pydantic input model."""

    def test_valid_data(self):
        from routes.export import MultiPeriodMemoInput
        data = _make_comparison_result()
        model = MultiPeriodMemoInput(**data)
        assert model.total_accounts == 80

    def test_defaults(self):
        from routes.export import MultiPeriodMemoInput
        model = MultiPeriodMemoInput()
        assert model.prior_label == "Prior"
        assert model.current_label == "Current"
        assert model.budget_label is None
        assert model.total_accounts == 0
        assert model.filename == "multi_period_comparison"
        assert model.client_name is None
        assert model.prepared_by is None

    def test_with_all_fields(self):
        from routes.export import MultiPeriodMemoInput
        data = _make_comparison_result(budget_label="Budget 2025")
        data.update({
            "filename": "my_comparison",
            "client_name": "TestCo",
            "period_tested": "FY24 vs FY25",
            "prepared_by": "Auditor A",
            "reviewed_by": "Manager B",
            "workpaper_date": "2025-12-31",
        })
        model = MultiPeriodMemoInput(**data)
        assert model.client_name == "TestCo"
        assert model.budget_label == "Budget 2025"
        assert model.filename == "my_comparison"

    def test_model_dump_roundtrip(self):
        from routes.export import MultiPeriodMemoInput
        data = _make_comparison_result()
        model = MultiPeriodMemoInput(**data)
        dumped = model.model_dump()
        assert dumped["total_accounts"] == 80
        assert dumped["movements_by_type"]["increase"] == 30
        assert len(dumped["significant_movements"]) == 11
        assert len(dumped["lead_sheet_summaries"]) == 5

    def test_movements_preserved(self):
        from routes.export import MultiPeriodMemoInput
        data = _make_comparison_result()
        model = MultiPeriodMemoInput(**data)
        dumped = model.model_dump()
        first_movement = dumped["significant_movements"][0]
        assert "account_name" in first_movement
        assert "change_amount" in first_movement
        assert "movement_type" in first_movement
