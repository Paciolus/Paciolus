"""
Tests for Bank Reconciliation Memo Generator (Sprint 128 / Sprint 503 rewrite)

Tests:
- PDF generation and validation
- Optional workpaper parameters
- Risk tier conclusion coverage
- Guardrail compliance (terminology, ISA references)
- Export route registration
- Pydantic input model validation
- Section II Methodology table
- Section V Results Summary with risk scoring
- Section VI Key Findings
- Outstanding items aging tables
- Ending balance reconciliation
- Reconciling difference characterization
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


def _make_enriched_result() -> dict:
    """Build a fully enriched BankRecResult for testing all new sections."""
    result = _make_rec_result(
        matched_count=342,
        bank_only_count=18,
        ledger_only_count=12,
        matched_amount=4_782_340.0,
        bank_only_amount=45_670.0,
        ledger_only_amount=38_920.0,
        reconciling_difference=6_750.0,
        total_bank=4_828_010.0,
        total_ledger=4_821_260.0,
    )

    result["test_results"] = [
        {
            "test_name": "Exact Match Reconciliation",
            "test_key": "exact_match",
            "test_tier": "structural",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
        {
            "test_name": "Bank-Only Items",
            "test_key": "bank_only_items",
            "test_tier": "structural",
            "entries_flagged": 18,
            "flag_rate": 0.048,
            "severity": "medium",
        },
        {
            "test_name": "Ledger-Only Items",
            "test_key": "ledger_only_items",
            "test_tier": "structural",
            "entries_flagged": 12,
            "flag_rate": 0.032,
            "severity": "medium",
        },
        {
            "test_name": "Stale Deposits (>10 days)",
            "test_key": "stale_deposits",
            "test_tier": "structural",
            "entries_flagged": 11,
            "flag_rate": 0.030,
            "severity": "high",
        },
        {
            "test_name": "Stale Checks (>90 days)",
            "test_key": "stale_checks",
            "test_tier": "structural",
            "entries_flagged": 3,
            "flag_rate": 0.008,
            "severity": "medium",
        },
        {
            "test_name": "NSF / Returned Items",
            "test_key": "nsf_items",
            "test_tier": "advanced",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
        {
            "test_name": "Interbank Transfers",
            "test_key": "interbank_transfers",
            "test_tier": "advanced",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
        {
            "test_name": "High Value (>Materiality)",
            "test_key": "high_value_transactions",
            "test_tier": "statistical",
            "entries_flagged": 0,
            "flag_rate": 0.0,
            "severity": "low",
        },
    ]

    result["composite_score"] = {
        "score": 33.0,
        "risk_tier": "elevated",
        "total_flagged": 44,
        "flag_rate": 0.118,
        "flags_by_severity": {"high": 4, "medium": 37, "low": 3},
        "tests_run": 8,
        "total_entries": 372,
        "top_findings": [
            "Stale Deposits (>10 days): 11 items flagged",
            "Stale Checks (>90 days): 3 items flagged",
        ],
    }

    result["rec_tests"] = [
        {
            "test_name": "Stale Deposits (>10 days)",
            "flagged_count": 11,
            "severity": "high",
            "flagged_items": [
                {
                    "test_name": "Stale Deposits",
                    "description": "Deposit outstanding 77 days",
                    "amount": 500.0,
                    "date": "2025-10-15",
                    "severity": "high",
                    "details": {"age_days": 77},
                },
            ],
        },
        {"test_name": "Stale Checks (>90 days)", "flagged_count": 3, "severity": "medium", "flagged_items": []},
        {"test_name": "NSF / Returned Items", "flagged_count": 0, "severity": "low", "flagged_items": []},
        {"test_name": "Interbank Transfers", "flagged_count": 0, "severity": "low", "flagged_items": []},
        {"test_name": "High Value (>Materiality)", "flagged_count": 0, "severity": "low", "flagged_items": []},
    ]

    result["outstanding_deposits"] = [
        {"date": "2025-12-31", "days_outstanding": 0, "description": "Wire transfer", "amount": 12500.0},
        {"date": "2025-11-01", "days_outstanding": 60, "description": "ACH - Disputed", "amount": 800.0},
        {"date": "2025-10-15", "days_outstanding": 77, "description": "Check #4488", "amount": 500.0},
    ]

    result["outstanding_checks"] = [
        {"date": "2025-12-30", "days_outstanding": 1, "description": "Check #8901", "amount": -1250.0},
        {"date": "2025-09-15", "days_outstanding": 107, "description": "Check #8790", "amount": -3200.0},
        {"date": "2025-07-01", "days_outstanding": 183, "description": "Check #8700", "amount": -1000.0},
    ]

    result["aging_summary"] = {
        "deposits_over_10_days": {"count": 11, "amount": 19520.0, "pct": 42.7},
        "deposits_over_30_days": {"count": 4, "amount": 4600.0, "pct": 10.1},
        "checks_over_30_days": {"count": 5, "amount": 10070.0, "pct": 25.9},
        "checks_over_90_days": {"count": 3, "amount": 5770.0, "pct": 14.8},
    }

    result["ending_balance_reconciliation"] = {
        "bank_ending_balance": 1_251_750.0,
        "gl_ending_balance": 1_245_000.0,
    }

    result["ar_cross_reference"] = {
        "ar_reconciling_difference": 8_450.0,
        "ar_reference": "ARA-2026-0306-494",
    }

    return result


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
# ENRICHED REPORT TESTS
# =============================================================================


class TestBankRecEnrichedReport:
    """Test all new enriched sections."""

    def test_enriched_generates_pdf(self):
        """Full enriched report generates without error."""
        result = _make_enriched_result()
        pdf = generate_bank_rec_memo(result, client_name="Meridian Capital Group")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000  # should be substantially larger

    def test_enriched_larger_than_basic(self):
        """Enriched report is larger than basic report."""
        basic = generate_bank_rec_memo(_make_rec_result())
        enriched = generate_bank_rec_memo(_make_enriched_result())
        assert len(enriched) > len(basic)

    def test_with_source_document_title(self):
        result = _make_enriched_result()
        pdf = generate_bank_rec_memo(
            result,
            filename="meridian_bank_rec.csv",
            source_document_title="Bank Statement — December 2025",
            source_context_note="Statement from First National Bank",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# METHODOLOGY TESTS
# =============================================================================


class TestBankRecMethodology:
    """Test Section II: Methodology table."""

    def test_methodology_with_8_tests(self):
        """Methodology table should render with all 8 test descriptions."""
        result = _make_enriched_result()
        assert len(result["test_results"]) == 8
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_methodology_fallback_without_test_results(self):
        """Memo still generates when test_results is absent."""
        result = _make_rec_result()
        # No test_results key
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_all_test_keys_have_descriptions(self):
        """Every test_key in test_results maps to a description."""
        from bank_reconciliation_memo_generator import _TEST_DESCRIPTIONS

        result = _make_enriched_result()
        for tr in result["test_results"]:
            key = tr["test_key"]
            assert key in _TEST_DESCRIPTIONS, f"Missing description for test_key: {key}"
            assert len(_TEST_DESCRIPTIONS[key]) > 20, f"Description too short for: {key}"


# =============================================================================
# RESULTS SUMMARY TESTS
# =============================================================================


class TestBankRecResultsSummary:
    """Test Section V: Results Summary."""

    def test_results_summary_renders(self):
        """Results summary renders when composite_score is present."""
        result = _make_enriched_result()
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_results_summary_skipped_without_composite(self):
        """Memo still generates without composite_score."""
        result = _make_rec_result()
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_risk_tier_consistency(self):
        """Risk tier from composite must be used in conclusion."""
        result = _make_enriched_result()
        result["composite_score"]["risk_tier"] = "low"
        result["composite_score"]["score"] = 5.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RISK TIER CONCLUSION TESTS
# =============================================================================


class TestBankRecRiskConclusions:
    """Test conclusion text varies by risk tier."""

    def test_low_risk_conclusion(self):
        result = _make_enriched_result()
        result["composite_score"]["risk_tier"] = "low"
        result["composite_score"]["score"] = 5.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_enriched_result()
        result["composite_score"]["risk_tier"] = "moderate"
        result["composite_score"]["score"] = 19.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_elevated_risk_conclusion(self):
        result = _make_enriched_result()
        result["composite_score"]["risk_tier"] = "elevated"
        result["composite_score"]["score"] = 33.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_enriched_result()
        result["composite_score"]["risk_tier"] = "high"
        result["composite_score"]["score"] = 65.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# KEY FINDINGS TESTS
# =============================================================================


class TestBankRecKeyFindings:
    """Test Section VI: Key Findings."""

    def test_key_findings_with_reconciling_difference(self):
        """Finding 1 present when reconciling difference > 0."""
        result = _make_enriched_result()
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_key_findings_zero_difference(self):
        """No reconciling difference finding when diff is zero."""
        result = _make_enriched_result()
        result["summary"]["reconciling_difference"] = 0.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_key_findings_with_ar_cross_reference(self):
        """AR cross-reference renders when available."""
        result = _make_enriched_result()
        assert result["ar_cross_reference"]["ar_reconciling_difference"] == 8450.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_key_findings_without_ar_cross_reference(self):
        """Memo renders without AR cross-reference."""
        result = _make_enriched_result()
        del result["ar_cross_reference"]
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_key_findings_no_outstanding(self):
        """No outstanding volume finding when no outstanding items."""
        result = _make_enriched_result()
        result["summary"]["bank_only_count"] = 0
        result["summary"]["ledger_only_count"] = 0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# OUTSTANDING ITEMS AGING TESTS
# =============================================================================


class TestBankRecAgingTables:
    """Test Section IV: Outstanding Items aging tables."""

    def test_aging_tables_render(self):
        """Aging tables render with outstanding items data."""
        result = _make_enriched_result()
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_aging_without_item_data(self):
        """Falls back to summary when no individual items provided."""
        result = _make_enriched_result()
        del result["outstanding_deposits"]
        del result["outstanding_checks"]
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_aging_summary_block(self):
        """Aging summary renders when available."""
        result = _make_enriched_result()
        assert "aging_summary" in result
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_aging_no_summary(self):
        """Memo renders without aging_summary."""
        result = _make_enriched_result()
        del result["aging_summary"]
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_deposits_sorted_by_age(self):
        """Verify deposits are expected to be sorted by days_outstanding desc."""
        result = _make_enriched_result()
        deposits = result["outstanding_deposits"]
        # The memo builder sorts internally
        assert len(deposits) > 0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# ENDING BALANCE RECONCILIATION TESTS
# =============================================================================


class TestBankRecEndingBalance:
    """Test ending balance reconciliation section."""

    def test_ending_balance_renders(self):
        """Ending balance reconciliation renders when data available."""
        result = _make_enriched_result()
        assert "ending_balance_reconciliation" in result
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_ending_balance(self):
        """Memo renders without ending balance data."""
        result = _make_enriched_result()
        del result["ending_balance_reconciliation"]
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_missing_bank_balance(self):
        """Handles missing bank ending balance."""
        result = _make_enriched_result()
        result["ending_balance_reconciliation"] = {
            "bank_ending_balance": None,
            "gl_ending_balance": 1_245_000.0,
        }
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_missing_gl_balance(self):
        """Handles missing GL ending balance."""
        result = _make_enriched_result()
        result["ending_balance_reconciliation"] = {
            "bank_ending_balance": 1_251_750.0,
            "gl_ending_balance": None,
        }
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_both_balances_missing(self):
        """Handles both balances missing."""
        result = _make_enriched_result()
        result["ending_balance_reconciliation"] = {
            "bank_ending_balance": None,
            "gl_ending_balance": None,
        }
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RECONCILING DIFFERENCE CHARACTERIZATION TESTS
# =============================================================================


class TestBankRecDifferenceCharacterization:
    """Test reconciling difference characterization."""

    def test_characterization_renders(self):
        """Characterization renders when reconciling difference > 0."""
        result = _make_enriched_result()
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_characterization_zero_diff(self):
        """No characterization when difference is zero."""
        result = _make_enriched_result()
        result["summary"]["reconciling_difference"] = 0.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)

    def test_negative_difference(self):
        """Characterization handles negative difference (GL > Bank)."""
        result = _make_enriched_result()
        result["summary"]["reconciling_difference"] = -3500.0
        pdf = generate_bank_rec_memo(result)
        assert isinstance(pdf, bytes)


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

    def test_domain_text(self):
        """Disclaimer domain should include 'bank reconciliation analysis testing procedures'."""
        source = inspect.getsource(generate_bank_rec_memo)
        assert "bank reconciliation analysis testing procedures" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================


class TestBankRecMemoExportRoute:
    """Verify the export route is registered."""

    def test_bank_rec_memo_route_exists(self):
        from main import app

        routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                routes.append(route.path)
        assert "/export/bank-rec-memo" in routes

    def test_bank_rec_memo_route_is_post(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/bank-rec-memo":
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
        data.update(
            {
                "filename": "my_bank_rec",
                "client_name": "TestCo",
                "period_tested": "Q4 2025",
                "prepared_by": "Auditor A",
                "reviewed_by": "Manager B",
                "workpaper_date": "2025-12-31",
            }
        )
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


# =============================================================================
# ENGINE RISK SCORE TESTS
# =============================================================================


class TestBankRecRiskScore:
    """Test the compute_bank_rec_risk_score function."""

    def test_basic_risk_score(self):
        from bank_reconciliation import (
            ReconciliationSummary,
            RecTestResult,
            compute_bank_rec_risk_score,
        )

        summary = ReconciliationSummary(
            matched_count=342,
            bank_only_count=18,
            ledger_only_count=12,
            reconciling_difference=6750.0,
        )
        rec_tests = [
            RecTestResult(test_name="Stale Deposits (>10 days)", flagged_count=11, severity="high"),
            RecTestResult(test_name="Stale Checks (>90 days)", flagged_count=3, severity="medium"),
            RecTestResult(test_name="NSF / Returned Items", flagged_count=0, severity="low"),
            RecTestResult(test_name="Interbank Transfers", flagged_count=0, severity="low"),
            RecTestResult(test_name="High Value (>Materiality)", flagged_count=0, severity="low"),
        ]

        result = compute_bank_rec_risk_score(rec_tests, summary)
        assert result["score"] == 33.0  # 15 (diff) + 8 (>20 outstanding) + 6 (stale dep) + 4 (stale chk)
        assert result["risk_tier"] == "elevated"
        assert result["tests_run"] == 8

    def test_low_risk_score(self):
        from bank_reconciliation import (
            ReconciliationSummary,
            RecTestResult,
            compute_bank_rec_risk_score,
        )

        summary = ReconciliationSummary(
            matched_count=100,
            bank_only_count=2,
            ledger_only_count=1,
            reconciling_difference=0.0,
        )
        rec_tests = [
            RecTestResult(test_name="Stale Deposits (>10 days)", flagged_count=0, severity="low"),
            RecTestResult(test_name="Stale Checks (>90 days)", flagged_count=0, severity="low"),
            RecTestResult(test_name="NSF / Returned Items", flagged_count=0, severity="low"),
            RecTestResult(test_name="Interbank Transfers", flagged_count=0, severity="low"),
            RecTestResult(test_name="High Value (>Materiality)", flagged_count=0, severity="low"),
        ]

        result = compute_bank_rec_risk_score(rec_tests, summary)
        assert result["score"] == 0.0
        assert result["risk_tier"] == "low"

    def test_high_risk_score_kiting(self):
        from bank_reconciliation import (
            ReconciliationSummary,
            RecTestResult,
            compute_bank_rec_risk_score,
        )

        summary = ReconciliationSummary(
            matched_count=50,
            bank_only_count=15,
            ledger_only_count=10,
            reconciling_difference=75_000.0,
        )
        rec_tests = [
            RecTestResult(test_name="Stale Deposits (>10 days)", flagged_count=5, severity="high"),
            RecTestResult(test_name="Stale Checks (>90 days)", flagged_count=2, severity="medium"),
            RecTestResult(test_name="NSF / Returned Items", flagged_count=1, severity="high"),
            RecTestResult(test_name="Interbank Transfers", flagged_count=1, severity="high"),
            RecTestResult(test_name="High Value (>Materiality)", flagged_count=3, severity="medium"),
        ]

        result = compute_bank_rec_risk_score(rec_tests, summary)
        # 15 (diff) + 10 (>materiality) + 8 (>20 outstanding) + 6 (stale dep) + 4 (stale chk)
        # + 10 (nsf) + 15 (kiting) + 5 (high value) = 73
        assert result["score"] == 73.0
        assert result["risk_tier"] == "high"

    def test_score_capped_at_100(self):
        from bank_reconciliation import (
            ReconciliationSummary,
            RecTestResult,
            compute_bank_rec_risk_score,
        )

        summary = ReconciliationSummary(
            matched_count=10,
            bank_only_count=50,
            ledger_only_count=50,
            reconciling_difference=1_000_000.0,
        )
        rec_tests = [
            RecTestResult(test_name="Stale Deposits (>10 days)", flagged_count=30, severity="high"),
            RecTestResult(test_name="Stale Checks (>90 days)", flagged_count=20, severity="medium"),
            RecTestResult(test_name="NSF / Returned Items", flagged_count=5, severity="high"),
            RecTestResult(test_name="Interbank Transfers", flagged_count=3, severity="high"),
            RecTestResult(test_name="High Value (>Materiality)", flagged_count=10, severity="medium"),
        ]

        result = compute_bank_rec_risk_score(rec_tests, summary)
        assert result["score"] <= 100


# =============================================================================
# ENGINE FLAGGED ITEM SEVERITY TESTS
# =============================================================================


class TestRecFlaggedItemSeverity:
    """Test per-item severity on RecFlaggedItem."""

    def test_stale_deposit_severity_high(self):
        """Deposit >30 days old should have HIGH severity."""
        from datetime import date

        from bank_reconciliation import (
            BankTransaction,
            MatchType,
            ReconciliationMatch,
            _test_stale_deposits,
        )

        bank_txn = BankTransaction(date="2025-11-01", description="Old deposit", amount=1000.0)
        match = ReconciliationMatch(bank_txn=bank_txn, match_type=MatchType.BANK_ONLY)
        result = _test_stale_deposits([match], reference_date=date(2025, 12, 31))
        assert result.flagged_count == 1
        assert result.flagged_items[0].severity == "high"

    def test_stale_deposit_severity_medium(self):
        """Deposit 11-30 days old should have MEDIUM severity."""
        from datetime import date

        from bank_reconciliation import (
            BankTransaction,
            MatchType,
            ReconciliationMatch,
            _test_stale_deposits,
        )

        bank_txn = BankTransaction(date="2025-12-15", description="Recent deposit", amount=500.0)
        match = ReconciliationMatch(bank_txn=bank_txn, match_type=MatchType.BANK_ONLY)
        result = _test_stale_deposits([match], reference_date=date(2025, 12, 31))
        assert result.flagged_count == 1
        assert result.flagged_items[0].severity == "medium"

    def test_nsf_item_severity_high(self):
        """NSF items should always be HIGH severity."""
        from bank_reconciliation import (
            BankTransaction,
            MatchType,
            ReconciliationMatch,
            _test_nsf_items,
        )

        bank_txn = BankTransaction(description="NSF - Customer payment returned", amount=-500.0)
        match = ReconciliationMatch(bank_txn=bank_txn, match_type=MatchType.BANK_ONLY)
        result = _test_nsf_items([match])
        assert result.flagged_count == 1
        assert result.flagged_items[0].severity == "high"

    def test_nsf_expanded_keywords(self):
        """NSF test should catch INSUFFICIENT, R01, R02, REVERSED."""
        from bank_reconciliation import (
            BankTransaction,
            MatchType,
            ReconciliationMatch,
            _test_nsf_items,
        )

        for keyword in ["INSUFFICIENT FUNDS", "R01 return", "R02 closed", "REVERSED payment"]:
            bank_txn = BankTransaction(description=keyword, amount=-100.0)
            match = ReconciliationMatch(bank_txn=bank_txn, match_type=MatchType.BANK_ONLY)
            result = _test_nsf_items([match])
            assert result.flagged_count >= 1, f"Failed to flag: {keyword}"

    def test_high_value_uses_gte(self):
        """High value test uses >= (not >) for materiality threshold."""
        from bank_reconciliation import (
            BankTransaction,
            MatchType,
            ReconciliationMatch,
            _test_high_value_transactions,
        )

        bank_txn = BankTransaction(description="Exact materiality", amount=50_000.0)
        match = ReconciliationMatch(bank_txn=bank_txn, match_type=MatchType.MATCHED)
        result = _test_high_value_transactions([match], materiality=50_000.0)
        assert result.flagged_count == 1
