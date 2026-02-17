"""
Tests for Bank Reconciliation Memo Generator (Sprint 128)

Tests:
- PDF generation and validation
- Optional workpaper parameters
- Risk tier conclusion coverage
- Guardrail compliance (terminology, ISA references)
- Export route registration
- Pydantic input model validation
"""

import inspect

import pytest

from bank_reconciliation_memo_generator import generate_bank_rec_memo

# =============================================================================
# FIXTURES
# =============================================================================

def _make_rec_result(
    matched_count: int = 50,
    bank_only_count: int = 3,
    ledger_only_count: int = 5,
    matched_amount: float = 100000.0,
    bank_only_amount: float = 2500.0,
    ledger_only_amount: float = 4200.0,
    reconciling_difference: float = 150.0,
    total_bank: float = 102500.0,
    total_ledger: float = 104200.0,
    bank_confidence: float = 0.95,
    ledger_confidence: float = 0.90,
) -> dict:
    """Build a minimal BankRecResult-shaped dict for testing."""
    return {
        "summary": {
            "matched_count": matched_count,
            "bank_only_count": bank_only_count,
            "ledger_only_count": ledger_only_count,
            "matched_amount": matched_amount,
            "bank_only_amount": bank_only_amount,
            "ledger_only_amount": ledger_only_amount,
            "reconciling_difference": reconciling_difference,
            "total_bank": total_bank,
            "total_ledger": total_ledger,
            "matches": [],
        },
        "bank_column_detection": {
            "overall_confidence": bank_confidence,
            "date_column": "Date",
            "amount_column": "Amount",
            "description_column": "Description",
        },
        "ledger_column_detection": {
            "overall_confidence": ledger_confidence,
            "date_column": "Post Date",
            "amount_column": "Debit",
            "description_column": "Memo",
        },
    }


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================

class TestBankRecMemoGeneration:
    """Test PDF generation for bank reconciliation memos."""

    def test_generates_pdf_bytes(self):
        result = _make_rec_result()
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_rec_result()
        pdf = generate_bank_rec_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_rec_result()
        pdf = generate_bank_rec_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_rec_result()
        pdf = generate_bank_rec_memo(
            result,
            filename="test_bank_rec",
            client_name="TestCo Ltd",
            period_tested="FY 2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_low_risk_conclusion(self):
        """rec_diff < 1.0 and match_rate >= 0.95 -> LOW risk."""
        result = _make_rec_result(
            matched_count=100,
            bank_only_count=2,
            ledger_only_count=1,
            reconciling_difference=0.50,
        )
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_moderate_risk_conclusion(self):
        """rec_diff < 1000 and match_rate >= 0.80 -> MODERATE risk."""
        result = _make_rec_result(
            matched_count=80,
            bank_only_count=10,
            ledger_only_count=10,
            reconciling_difference=500.0,
        )
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_elevated_risk_conclusion(self):
        """rec_diff >= 1000 or match_rate < 0.80 -> ELEVATED risk."""
        result = _make_rec_result(
            matched_count=20,
            bank_only_count=30,
            ledger_only_count=25,
            reconciling_difference=5000.0,
        )
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_outstanding_items(self):
        """No bank-only or ledger-only items."""
        result = _make_rec_result(
            bank_only_count=0,
            ledger_only_count=0,
            bank_only_amount=0,
            ledger_only_amount=0,
        )
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_zero_transactions(self):
        """Edge case: no transactions at all."""
        result = _make_rec_result(
            matched_count=0,
            bank_only_count=0,
            ledger_only_count=0,
            matched_amount=0,
            bank_only_amount=0,
            ledger_only_amount=0,
            reconciling_difference=0,
            total_bank=0,
            total_ledger=0,
        )
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_column_detection(self):
        """Missing column detection data."""
        result = _make_rec_result()
        result["bank_column_detection"] = {}
        result["ledger_column_detection"] = {}
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestBankRecMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(generate_bank_rec_memo)
        assert "ISA 500" in source
        assert "ISA 505" in source
        assert "PCAOB AS 2310" in source

    def test_no_forbidden_audit_assertions(self):
        source = inspect.getsource(generate_bank_rec_memo)
        forbidden = [
            "bank balance is correct",
            "reconciliation is complete",
            "no errors exist",
            "accounts are accurate",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"

    def test_disclaimer_called(self):
        source = inspect.getsource(generate_bank_rec_memo)
        assert "build_disclaimer" in source

    def test_workpaper_signoff_called(self):
        source = inspect.getsource(generate_bank_rec_memo)
        assert "build_workpaper_signoff" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================

class TestBankRecMemoExportRoute:
    """Verify the export route is registered."""

    def test_bank_rec_memo_route_exists(self):
        from main import app
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        assert "/export/bank-rec-memo" in routes

    def test_bank_rec_memo_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/export/bank-rec-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/bank-rec-memo not found")


# =============================================================================
# PYDANTIC INPUT MODEL
# =============================================================================

class TestBankRecMemoInput:
    """Verify the Pydantic input model."""

    def test_valid_data(self):
        from routes.export import BankRecMemoInput
        data = _make_rec_result()
        model = BankRecMemoInput(**data)
        assert model.summary["matched_count"] == 50

    def test_defaults(self):
        from routes.export import BankRecMemoInput
        model = BankRecMemoInput(summary={"matched_count": 10})
        assert model.filename == "bank_reconciliation"
        assert model.client_name is None
        assert model.period_tested is None
        assert model.prepared_by is None
        assert model.reviewed_by is None
        assert model.workpaper_date is None

    def test_with_all_fields(self):
        from routes.export import BankRecMemoInput
        data = _make_rec_result()
        data.update({
            "filename": "my_bank_rec",
            "client_name": "TestCo",
            "period_tested": "Q4 2025",
            "prepared_by": "Auditor A",
            "reviewed_by": "Manager B",
            "workpaper_date": "2025-12-31",
        })
        model = BankRecMemoInput(**data)
        assert model.client_name == "TestCo"
        assert model.filename == "my_bank_rec"

    def test_model_dump_roundtrip(self):
        from routes.export import BankRecMemoInput
        data = _make_rec_result()
        model = BankRecMemoInput(**data)
        dumped = model.model_dump()
        assert dumped["summary"]["matched_count"] == 50
        assert dumped["bank_column_detection"]["overall_confidence"] == 0.95
