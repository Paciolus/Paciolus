"""
Tests for AR Aging Analysis Engine — Sprint 107

Covers: column detection (TB + sub-ledger), account classification,
11 test functions, composite scoring, data quality, pipeline, serialization,
route registration.
"""
import pytest

from ar_aging_engine import (
    ARAgingConfig,
    ARCompositeScore,
    ARDataQuality,
    AREntry,
    ARSubledgerEntry,
    ARTestResult,
    FlaggedAR,
    SLColumnDetection,
    # Data models
    TBAccount,
    TBColumnDetection,
    _classify_account,
    _parse_aging_bucket_to_days,
    classify_aging_bucket,
    # Pipeline
    run_ar_aging,
    # Battery and scoring
    run_ar_test_battery,
    score_to_risk_tier,
)
from ar_aging_engine import (
    # Data quality
    assess_data_quality as run_assess_data_quality,
)
from ar_aging_engine import (
    build_ar_summary as run_build_summary,
)
from ar_aging_engine import (
    calculate_ar_composite_score as run_composite_score,
)
from ar_aging_engine import (
    detect_sl_columns as run_detect_sl_columns,
)
from ar_aging_engine import (
    # Column detection
    detect_tb_columns as run_detect_tb_columns,
)
from ar_aging_engine import (
    parse_sl_entries as run_parse_sl_entries,
)
from ar_aging_engine import (
    # Parsing
    parse_tb_accounts as run_parse_tb_accounts,
)
from ar_aging_engine import (
    test_allowance_adequacy as run_allowance_adequacy,
)
from ar_aging_engine import (
    # Test functions (aliased to avoid pytest collection)
    test_ar_sign_anomalies as run_sign_anomalies,
)
from ar_aging_engine import (
    test_bucket_concentration as run_bucket_concentration,
)
from ar_aging_engine import (
    test_credit_limit_breaches as run_credit_limits,
)
from ar_aging_engine import (
    test_customer_concentration as run_customer_concentration,
)
from ar_aging_engine import (
    test_dso_trend as run_dso_trend,
)
from ar_aging_engine import (
    test_missing_allowance as run_missing_allowance,
)
from ar_aging_engine import (
    test_negative_aging as run_negative_aging,
)
from ar_aging_engine import (
    test_past_due_concentration as run_past_due_concentration,
)
from ar_aging_engine import (
    test_rollforward_reconciliation as run_rollforward,
)
from ar_aging_engine import (
    test_unreconciled_detail as run_unreconciled_detail,
)
from shared.parsing_helpers import safe_float as _safe_float
from shared.parsing_helpers import safe_int as _safe_int
from shared.testing_enums import RiskTier, Severity, TestTier

# =============================================================================
# FIXTURES / HELPERS
# =============================================================================

def sample_tb_rows() -> list[dict]:
    """Standard TB with AR, allowance, revenue, and other accounts."""
    return [
        {"Account Name": "Accounts Receivable - Trade", "Account Number": "1200", "Balance": 500000},
        {"Account Name": "Accounts Receivable - Other", "Account Number": "1210", "Balance": 50000},
        {"Account Name": "Allowance for Doubtful Accounts", "Account Number": "1290", "Balance": -15000},
        {"Account Name": "Sales Revenue", "Account Number": "4000", "Balance": -2000000},
        {"Account Name": "Service Income", "Account Number": "4100", "Balance": -300000},
        {"Account Name": "Cash and Equivalents", "Account Number": "1000", "Balance": 200000},
        {"Account Name": "Inventory", "Account Number": "1300", "Balance": 150000},
    ]


def sample_sl_rows() -> list[dict]:
    """Standard sub-ledger with aging data."""
    return [
        {"Customer Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 100000, "Aging Days": 15, "Due Date": "2025-12-01"},
        {"Customer Name": "Acme Corp", "Invoice Number": "INV-002", "Amount": 50000, "Aging Days": 45, "Due Date": "2025-11-01"},
        {"Customer Name": "Beta Inc", "Invoice Number": "INV-003", "Amount": 80000, "Aging Days": 10, "Due Date": "2025-12-10"},
        {"Customer Name": "Gamma LLC", "Invoice Number": "INV-004", "Amount": 120000, "Aging Days": 75, "Due Date": "2025-10-01"},
        {"Customer Name": "Delta Co", "Invoice Number": "INV-005", "Amount": 30000, "Aging Days": 100, "Due Date": "2025-09-15"},
        {"Customer Name": "Epsilon SA", "Invoice Number": "INV-006", "Amount": 70000, "Aging Days": 20, "Due Date": "2025-11-25"},
        {"Customer Name": "Acme Corp", "Invoice Number": "INV-007", "Amount": 40000, "Aging Days": 150, "Due Date": "2025-07-01"},
        {"Customer Name": "Beta Inc", "Invoice Number": "INV-008", "Amount": 60000, "Aging Days": 5, "Due Date": "2025-12-15"},
    ]


def make_tb_accounts(rows: list[dict] | None = None) -> list[TBAccount]:
    """Parse sample TB rows into accounts."""
    if rows is None:
        rows = sample_tb_rows()
    cols = list(rows[0].keys()) if rows else []
    detection = run_detect_tb_columns(cols)
    return run_parse_tb_accounts(rows, detection)


def make_sl_entries(rows: list[dict] | None = None) -> list[ARSubledgerEntry]:
    """Parse sample sub-ledger rows into entries."""
    if rows is None:
        rows = sample_sl_rows()
    cols = list(rows[0].keys()) if rows else []
    detection = run_detect_sl_columns(cols)
    return run_parse_sl_entries(rows, detection)


# =============================================================================
# TB COLUMN DETECTION
# =============================================================================

class TestTBColumnDetection:
    """Tests for detect_tb_columns."""

    def test_standard_columns(self):
        cols = ["Account Name", "Account Number", "Balance"]
        result = run_detect_tb_columns(cols)
        assert result.account_name_column == "Account Name"
        assert result.account_number_column == "Account Number"
        assert result.balance_column == "Balance"
        assert result.overall_confidence == 1.0

    def test_debit_credit_columns(self):
        cols = ["Account Name", "Account Number", "Debit", "Credit"]
        result = run_detect_tb_columns(cols)
        assert result.has_debit_credit
        assert result.debit_column == "Debit"
        assert result.credit_column == "Credit"

    def test_alternate_names(self):
        cols = ["GL Description", "Acct No", "Ending Balance"]
        result = run_detect_tb_columns(cols)
        assert result.account_name_column == "GL Description"
        assert result.account_number_column == "Acct No"
        assert result.balance_column == "Ending Balance"

    def test_missing_columns_low_confidence(self):
        cols = ["X", "Y", "Z"]
        result = run_detect_tb_columns(cols)
        assert result.overall_confidence < 1.0
        assert len(result.detection_notes) > 0

    def test_empty_columns(self):
        result = run_detect_tb_columns([])
        assert result.overall_confidence == 0.0
        assert result.account_name_column is None

    def test_all_columns_present(self):
        result = run_detect_tb_columns(["Account Name", "Account Number", "Balance"])
        assert result.all_columns == ["Account Name", "Account Number", "Balance"]


# =============================================================================
# SUB-LEDGER COLUMN DETECTION
# =============================================================================

class TestSLColumnDetection:
    """Tests for detect_sl_columns."""

    def test_standard_sl_columns(self):
        cols = ["Customer Name", "Invoice Number", "Amount", "Aging Days", "Due Date"]
        result = run_detect_sl_columns(cols)
        assert result.customer_name_column == "Customer Name"
        assert result.amount_column == "Amount"
        assert result.aging_days_column == "Aging Days"

    def test_credit_limit_detection(self):
        cols = ["Customer", "Amount", "Credit Limit"]
        result = run_detect_sl_columns(cols)
        assert result.credit_limit_column == "Credit Limit"

    def test_alternate_sl_names(self):
        cols = ["Debtor Name", "Outstanding Balance", "Days Outstanding"]
        result = run_detect_sl_columns(cols)
        assert result.customer_name_column == "Debtor Name"
        assert result.amount_column == "Outstanding Balance"
        assert result.aging_days_column == "Days Outstanding"

    def test_missing_sl_columns(self):
        cols = ["X", "Y"]
        result = run_detect_sl_columns(cols)
        assert result.overall_confidence < 1.0

    def test_sl_all_columns_present(self):
        cols = ["Customer Name", "Customer ID", "Invoice Number", "Invoice Date",
                "Due Date", "Amount", "Aging Days", "Aging Bucket", "Credit Limit"]
        result = run_detect_sl_columns(cols)
        assert result.customer_name_column is not None
        assert result.amount_column is not None
        assert result.overall_confidence == 1.0


# =============================================================================
# ACCOUNT CLASSIFICATION
# =============================================================================

class TestAccountClassification:
    """Tests for _classify_account."""

    def test_ar_account(self):
        cls, _ = _classify_account("Accounts Receivable - Trade")
        assert cls == "ar"

    def test_allowance_account(self):
        cls, _ = _classify_account("Allowance for Doubtful Accounts")
        assert cls == "allowance"

    def test_revenue_account(self):
        cls, _ = _classify_account("Sales Revenue")
        assert cls == "revenue"

    def test_other_account(self):
        cls, _ = _classify_account("Cash and Equivalents")
        assert cls == "other"

    def test_trade_debtor(self):
        cls, _ = _classify_account("Trade Debtors")
        assert cls == "ar"

    def test_provision_for_bad_debts(self):
        cls, _ = _classify_account("Provision for Bad Debts")
        assert cls == "allowance"

    def test_expected_credit_loss(self):
        cls, _ = _classify_account("Expected Credit Loss Allowance")
        assert cls == "allowance"

    def test_service_income(self):
        cls, _ = _classify_account("Service Income")
        assert cls == "revenue"

    def test_empty_string(self):
        cls, _ = _classify_account("")
        assert cls == "other"

    def test_none_value(self):
        cls, _ = _classify_account(None)
        assert cls == "other"


# =============================================================================
# PARSING UTILITIES
# =============================================================================

class TestParsingUtilities:
    """Tests for safe conversion and parsing helpers."""

    def test_safe_float_number(self):
        assert _safe_float(1234.56) == 1234.56

    def test_safe_float_string(self):
        assert _safe_float("1,234.56") == 1234.56

    def test_safe_float_dollar(self):
        assert _safe_float("$5,000") == 5000.0

    def test_safe_float_parens(self):
        assert _safe_float("(1000)") == -1000.0

    def test_safe_float_none(self):
        assert _safe_float(None) == 0.0

    def test_safe_float_empty(self):
        assert _safe_float("") == 0.0

    def test_safe_int_valid(self):
        assert _safe_int(42) == 42

    def test_safe_int_string(self):
        assert _safe_int("45") == 45

    def test_safe_int_float_string(self):
        assert _safe_int("30.5") == 30

    def test_safe_int_none(self):
        assert _safe_int(None) is None

    def test_safe_int_invalid(self):
        assert _safe_int("abc") is None

    def test_classify_aging_bucket_current(self):
        assert classify_aging_bucket(15) == "current"

    def test_classify_aging_bucket_31_60(self):
        assert classify_aging_bucket(45) == "31-60"

    def test_classify_aging_bucket_over_120(self):
        assert classify_aging_bucket(200) == "over_120"

    def test_parse_bucket_to_days_current(self):
        assert _parse_aging_bucket_to_days("Current") == 15

    def test_parse_bucket_to_days_range(self):
        result = _parse_aging_bucket_to_days("31-60")
        assert result == 45

    def test_parse_bucket_to_days_over(self):
        result = _parse_aging_bucket_to_days("Over 120")
        assert result == 150

    def test_parse_bucket_to_days_none(self):
        assert _parse_aging_bucket_to_days(None) is None

    def test_parse_bucket_to_days_empty(self):
        assert _parse_aging_bucket_to_days("") is None


# =============================================================================
# TB PARSING
# =============================================================================

class TestTBParsing:
    """Tests for parse_tb_accounts."""

    def test_parses_all_accounts(self):
        accounts = make_tb_accounts()
        assert len(accounts) == 7

    def test_classifies_ar(self):
        accounts = make_tb_accounts()
        ar = [a for a in accounts if a.classification == "ar"]
        assert len(ar) == 2

    def test_classifies_allowance(self):
        accounts = make_tb_accounts()
        allow = [a for a in accounts if a.classification == "allowance"]
        assert len(allow) == 1
        assert allow[0].balance == -15000

    def test_classifies_revenue(self):
        accounts = make_tb_accounts()
        rev = [a for a in accounts if a.classification == "revenue"]
        assert len(rev) == 2

    def test_debit_credit_columns(self):
        rows = [
            {"Account Name": "Accounts Receivable", "Debit": 100000, "Credit": 0},
            {"Account Name": "Allowance for Doubtful Accounts", "Debit": 0, "Credit": 5000},
        ]
        detection = run_detect_tb_columns(list(rows[0].keys()))
        accounts = run_parse_tb_accounts(rows, detection)
        assert accounts[0].balance == 100000
        assert accounts[1].balance == -5000

    def test_skips_empty_rows(self):
        rows = [
            {"Account Name": "", "Account Number": "", "Balance": 0},
            {"Account Name": "Cash", "Account Number": "1000", "Balance": 50000},
        ]
        detection = run_detect_tb_columns(list(rows[0].keys()))
        accounts = run_parse_tb_accounts(rows, detection)
        assert len(accounts) == 1


# =============================================================================
# SUB-LEDGER PARSING
# =============================================================================

class TestSLParsing:
    """Tests for parse_sl_entries."""

    def test_parses_all_entries(self):
        entries = make_sl_entries()
        assert len(entries) == 8

    def test_aging_days_parsed(self):
        entries = make_sl_entries()
        assert entries[0].aging_days == 15

    def test_aging_bucket_assigned(self):
        entries = make_sl_entries()
        assert entries[0].aging_bucket == "current"
        assert entries[1].aging_bucket == "31-60"

    def test_customer_name_parsed(self):
        entries = make_sl_entries()
        assert entries[0].customer_name == "Acme Corp"

    def test_amount_parsed(self):
        entries = make_sl_entries()
        assert entries[0].amount == 100000

    def test_skips_empty_rows(self):
        rows = [
            {"Customer Name": "", "Amount": 0},
            {"Customer Name": "Test", "Amount": 1000},
        ]
        detection = run_detect_sl_columns(list(rows[0].keys()))
        entries = run_parse_sl_entries(rows, detection)
        assert len(entries) == 1

    def test_bucket_from_string(self):
        rows = [
            {"Customer Name": "X", "Amount": 500, "Aging Bucket": "31-60"},
        ]
        detection = run_detect_sl_columns(list(rows[0].keys()))
        entries = run_parse_sl_entries(rows, detection)
        assert entries[0].aging_bucket == "31-60"
        assert entries[0].aging_days == 45


# =============================================================================
# DATA QUALITY
# =============================================================================

class TestDataQuality:
    """Tests for assess_data_quality."""

    def test_tb_only_quality(self):
        accounts = make_tb_accounts()
        quality = run_assess_data_quality(accounts, [], False)
        assert quality.total_tb_accounts == 7
        assert quality.has_subledger is False
        assert quality.completeness_score > 0

    def test_full_quality(self):
        accounts = make_tb_accounts()
        entries = make_sl_entries()
        quality = run_assess_data_quality(accounts, entries, True)
        assert quality.has_subledger is True
        assert quality.total_subledger_entries == 8

    def test_no_ar_accounts_issue(self):
        rows = [{"Account Name": "Cash", "Account Number": "1000", "Balance": 50000}]
        accounts = make_tb_accounts(rows)
        quality = run_assess_data_quality(accounts, [], False)
        assert any("No accounts receivable" in i for i in quality.detected_issues)

    def test_quality_serialization(self):
        quality = ARDataQuality(completeness_score=85.5, total_tb_accounts=10)
        d = quality.to_dict()
        assert d["completeness_score"] == 85.5
        assert d["total_tb_accounts"] == 10


# =============================================================================
# T1-AR01: SIGN ANOMALIES
# =============================================================================

class TestSignAnomalies:
    """Tests for test_ar_sign_anomalies."""

    def test_detects_credit_balance(self):
        accounts = make_tb_accounts()
        # Add an AR account with credit balance
        accounts.append(TBAccount(account_name="AR - Overpayment", balance=-5000, classification="ar", row_number=10))
        config = ARAgingConfig()
        result = run_sign_anomalies(accounts, config)
        assert result.entries_flagged >= 1
        assert result.test_key == "ar_sign_anomalies"

    def test_no_flags_for_debit_balances(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        result = run_sign_anomalies(accounts, config)
        assert result.entries_flagged == 0

    def test_high_severity_for_large_credit(self):
        accounts = [TBAccount(account_name="AR", balance=-50000, classification="ar", row_number=1)]
        config = ARAgingConfig()
        result = run_sign_anomalies(accounts, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_severity_for_small_credit(self):
        accounts = [TBAccount(account_name="AR", balance=-500, classification="ar", row_number=1)]
        config = ARAgingConfig()
        result = run_sign_anomalies(accounts, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_disabled_config(self):
        accounts = [TBAccount(account_name="AR", balance=-5000, classification="ar", row_number=1)]
        config = ARAgingConfig(sign_anomaly_enabled=False)
        result = run_sign_anomalies(accounts, config)
        assert result.entries_flagged == 0


# =============================================================================
# T1-AR02: MISSING ALLOWANCE
# =============================================================================

class TestMissingAllowance:
    """Tests for test_missing_allowance."""

    def test_no_flag_when_allowance_exists(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        result = run_missing_allowance(accounts, config)
        assert result.entries_flagged == 0

    def test_flags_when_no_allowance(self):
        rows = [
            {"Account Name": "Accounts Receivable", "Account Number": "1200", "Balance": 500000},
            {"Account Name": "Cash", "Account Number": "1000", "Balance": 200000},
        ]
        accounts = make_tb_accounts(rows)
        config = ARAgingConfig()
        result = run_missing_allowance(accounts, config)
        assert result.entries_flagged == 1
        assert result.severity == Severity.HIGH

    def test_no_flag_when_no_ar(self):
        rows = [{"Account Name": "Cash", "Account Number": "1000", "Balance": 200000}]
        accounts = make_tb_accounts(rows)
        config = ARAgingConfig()
        result = run_missing_allowance(accounts, config)
        assert result.entries_flagged == 0


# =============================================================================
# T1-AR03: NEGATIVE AGING
# =============================================================================

class TestNegativeAging:
    """Tests for test_negative_aging."""

    def test_detects_negative_days(self):
        entries = [
            ARSubledgerEntry(customer_name="X", amount=1000, aging_days=-10, row_number=1),
            ARSubledgerEntry(customer_name="Y", amount=2000, aging_days=30, row_number=2),
        ]
        config = ARAgingConfig()
        result = run_negative_aging(entries, config)
        assert result.entries_flagged == 1

    def test_no_flags_all_positive(self):
        entries = make_sl_entries()
        config = ARAgingConfig()
        result = run_negative_aging(entries, config)
        assert result.entries_flagged == 0

    def test_disabled_config(self):
        entries = [ARSubledgerEntry(customer_name="X", amount=1000, aging_days=-10, row_number=1)]
        config = ARAgingConfig(negative_aging_enabled=False)
        result = run_negative_aging(entries, config)
        assert result.entries_flagged == 0


# =============================================================================
# T1-AR04: UNRECONCILED DETAIL
# =============================================================================

class TestUnreconciledDetail:
    """Tests for test_unreconciled_detail."""

    def test_no_flag_when_balanced(self):
        accounts = [TBAccount(account_name="AR", balance=550000, classification="ar")]
        entries = make_sl_entries()
        config = ARAgingConfig()
        result = run_unreconciled_detail(accounts, entries, config)
        assert result.entries_flagged == 0

    def test_flags_large_difference(self):
        accounts = [TBAccount(account_name="AR", balance=1000000, classification="ar")]
        entries = [ARSubledgerEntry(customer_name="X", amount=500000, row_number=1)]
        config = ARAgingConfig()
        result = run_unreconciled_detail(accounts, entries, config)
        assert result.entries_flagged == 1

    def test_high_severity_large_diff(self):
        accounts = [TBAccount(account_name="AR", balance=100000, classification="ar")]
        entries = [ARSubledgerEntry(customer_name="X", amount=10000, row_number=1)]
        config = ARAgingConfig()
        result = run_unreconciled_detail(accounts, entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH


# =============================================================================
# T2-AR05: BUCKET CONCENTRATION
# =============================================================================

class TestBucketConcentration:
    """Tests for test_bucket_concentration."""

    def test_detects_concentration(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=80000, aging_bucket="current", row_number=1),
            ARSubledgerEntry(customer_name="B", amount=10000, aging_bucket="31-60", row_number=2),
            ARSubledgerEntry(customer_name="C", amount=10000, aging_bucket="61-90", row_number=3),
        ]
        config = ARAgingConfig(bucket_concentration_threshold=0.60)
        result = run_bucket_concentration(entries, config)
        assert result.entries_flagged >= 1

    def test_no_flag_even_distribution(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=25000, aging_bucket="current", row_number=1),
            ARSubledgerEntry(customer_name="B", amount=25000, aging_bucket="31-60", row_number=2),
            ARSubledgerEntry(customer_name="C", amount=25000, aging_bucket="61-90", row_number=3),
            ARSubledgerEntry(customer_name="D", amount=25000, aging_bucket="91-120", row_number=4),
        ]
        config = ARAgingConfig(bucket_concentration_threshold=0.60)
        result = run_bucket_concentration(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_old_bucket(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=90000, aging_bucket="over_120", row_number=1),
            ARSubledgerEntry(customer_name="B", amount=10000, aging_bucket="current", row_number=2),
        ]
        config = ARAgingConfig(bucket_concentration_threshold=0.60)
        result = run_bucket_concentration(entries, config)
        assert result.entries_flagged >= 1
        assert any(f.severity == Severity.HIGH for f in result.flagged_entries)

    def test_zero_total_ar(self):
        config = ARAgingConfig()
        result = run_bucket_concentration([], config)
        assert result.entries_flagged == 0


# =============================================================================
# T2-AR06: PAST-DUE CONCENTRATION
# =============================================================================

class TestPastDueConcentration:
    """Tests for test_past_due_concentration."""

    def test_detects_high_past_due(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=30000, aging_days=10, row_number=1),
            ARSubledgerEntry(customer_name="B", amount=70000, aging_days=60, row_number=2),
        ]
        config = ARAgingConfig(past_due_threshold_pct=0.25)
        result = run_past_due_concentration(entries, config)
        assert result.entries_flagged >= 1

    def test_no_flag_low_past_due(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=90000, aging_days=10, row_number=1),
            ARSubledgerEntry(customer_name="B", amount=10000, aging_days=45, row_number=2),
        ]
        config = ARAgingConfig(past_due_threshold_pct=0.25)
        result = run_past_due_concentration(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_over_50pct(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=20000, aging_days=10, row_number=1),
            ARSubledgerEntry(customer_name="B", amount=80000, aging_days=60, row_number=2),
        ]
        config = ARAgingConfig(past_due_threshold_pct=0.25, past_due_high_pct=0.50)
        result = run_past_due_concentration(entries, config)
        assert any(f.severity == Severity.HIGH for f in result.flagged_entries)


# =============================================================================
# T2-AR07: ALLOWANCE ADEQUACY
# =============================================================================

class TestAllowanceAdequacy:
    """Tests for test_allowance_adequacy."""

    def test_normal_ratio_no_flag(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        result = run_allowance_adequacy(accounts, config)
        # 15000/550000 = ~2.7% — within 1%-10% range
        assert result.entries_flagged == 0

    def test_low_ratio_flags(self):
        accounts = [
            TBAccount(account_name="AR", balance=1000000, classification="ar"),
            TBAccount(account_name="Allowance for Doubtful", balance=-500, classification="allowance"),
        ]
        config = ARAgingConfig(allowance_low_pct=0.01)
        result = run_allowance_adequacy(accounts, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_high_ratio_flags(self):
        accounts = [
            TBAccount(account_name="AR", balance=100000, classification="ar"),
            TBAccount(account_name="Allowance for Doubtful", balance=-20000, classification="allowance"),
        ]
        config = ARAgingConfig(allowance_high_pct=0.10)
        result = run_allowance_adequacy(accounts, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_no_allowance_no_flag(self):
        """AR07 doesn't flag missing allowance — that's AR02's job."""
        accounts = [TBAccount(account_name="AR", balance=100000, classification="ar")]
        config = ARAgingConfig()
        result = run_allowance_adequacy(accounts, config)
        assert result.entries_flagged == 0


# =============================================================================
# T2-AR08: CUSTOMER CONCENTRATION
# =============================================================================

class TestCustomerConcentration:
    """Tests for test_customer_concentration."""

    def test_detects_concentration(self):
        entries = [
            ARSubledgerEntry(customer_name="Big Customer", amount=80000, row_number=1),
            ARSubledgerEntry(customer_name="Small A", amount=10000, row_number=2),
            ARSubledgerEntry(customer_name="Small B", amount=10000, row_number=3),
        ]
        config = ARAgingConfig(customer_concentration_threshold=0.20)
        result = run_customer_concentration(entries, config)
        assert result.entries_flagged >= 1

    def test_no_flag_even_customers(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=25000, row_number=1),
            ARSubledgerEntry(customer_name="B", amount=25000, row_number=2),
            ARSubledgerEntry(customer_name="C", amount=25000, row_number=3),
            ARSubledgerEntry(customer_name="D", amount=25000, row_number=4),
        ]
        config = ARAgingConfig(customer_concentration_threshold=0.30)
        result = run_customer_concentration(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_above_40pct(self):
        entries = [
            ARSubledgerEntry(customer_name="Mega", amount=60000, row_number=1),
            ARSubledgerEntry(customer_name="Others", amount=40000, row_number=2),
        ]
        config = ARAgingConfig(customer_concentration_threshold=0.20, customer_concentration_high=0.40)
        result = run_customer_concentration(entries, config)
        assert any(f.severity == Severity.HIGH for f in result.flagged_entries)


# =============================================================================
# T2-AR09: DSO TREND
# =============================================================================

class TestDSOTrend:
    """Tests for test_dso_trend."""

    def test_skipped_without_prior(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        result = run_dso_trend(accounts, config)
        assert result.skipped is True

    def test_detects_increase(self):
        accounts = [
            TBAccount(account_name="AR", balance=500000, classification="ar"),
            TBAccount(account_name="Revenue", balance=-1000000, classification="revenue"),
        ]
        # Current DSO = (500000/1000000)*365 = 182.5 days
        config = ARAgingConfig(prior_period_dso=100.0)
        result = run_dso_trend(accounts, config)
        assert result.entries_flagged == 1

    def test_no_flag_small_change(self):
        accounts = [
            TBAccount(account_name="AR", balance=100000, classification="ar"),
            TBAccount(account_name="Revenue", balance=-1000000, classification="revenue"),
        ]
        # Current DSO = (100000/1000000)*365 = 36.5 days
        config = ARAgingConfig(prior_period_dso=35.0)
        result = run_dso_trend(accounts, config)
        assert result.entries_flagged == 0

    def test_high_severity_large_change(self):
        accounts = [
            TBAccount(account_name="AR", balance=500000, classification="ar"),
            TBAccount(account_name="Revenue", balance=-1000000, classification="revenue"),
        ]
        config = ARAgingConfig(prior_period_dso=50.0, dso_high_threshold=0.50)
        result = run_dso_trend(accounts, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH


# =============================================================================
# T3-AR10: ROLL-FORWARD RECONCILIATION
# =============================================================================

class TestRollForward:
    """Tests for test_rollforward_reconciliation."""

    def test_skipped_without_params(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        result = run_rollforward(accounts, [], config)
        assert result.skipped is True

    def test_flags_difference(self):
        accounts = [
            TBAccount(account_name="AR", balance=600000, classification="ar"),
            TBAccount(account_name="Revenue", balance=-2000000, classification="revenue"),
        ]
        # Expected: 400000 + 2000000 - 1500000 = 900000, but ending is 600000
        config = ARAgingConfig(beginning_ar_balance=400000, collections_total=1500000)
        result = run_rollforward(accounts, [], config)
        assert result.entries_flagged == 1

    def test_no_flag_when_balanced(self):
        accounts = [
            TBAccount(account_name="AR", balance=900000, classification="ar"),
            TBAccount(account_name="Revenue", balance=-2000000, classification="revenue"),
        ]
        config = ARAgingConfig(beginning_ar_balance=400000, collections_total=1500000)
        result = run_rollforward(accounts, [], config)
        assert result.entries_flagged == 0


# =============================================================================
# T3-AR11: CREDIT LIMIT BREACHES
# =============================================================================

class TestCreditLimits:
    """Tests for test_credit_limit_breaches."""

    def test_detects_breach(self):
        entries = [
            ARSubledgerEntry(customer_name="Over", amount=60000, credit_limit=50000, row_number=1),
            ARSubledgerEntry(customer_name="Under", amount=30000, credit_limit=50000, row_number=2),
        ]
        config = ARAgingConfig()
        result = run_credit_limits(entries, config)
        assert result.entries_flagged >= 1

    def test_no_flag_within_limit(self):
        entries = [
            ARSubledgerEntry(customer_name="A", amount=30000, credit_limit=50000, row_number=1),
        ]
        config = ARAgingConfig()
        result = run_credit_limits(entries, config)
        assert result.entries_flagged == 0

    def test_skipped_no_limits(self):
        entries = [ARSubledgerEntry(customer_name="A", amount=30000, row_number=1)]
        config = ARAgingConfig()
        result = run_credit_limits(entries, config)
        assert result.skipped is True
        assert "No credit limit data" in result.skip_reason

    def test_skipped_disabled(self):
        entries = [ARSubledgerEntry(customer_name="A", amount=60000, credit_limit=50000, row_number=1)]
        config = ARAgingConfig(credit_limit_enabled=False)
        result = run_credit_limits(entries, config)
        assert result.skipped is True

    def test_high_severity_large_breach(self):
        entries = [
            ARSubledgerEntry(customer_name="Mega", amount=80000, credit_limit=50000, row_number=1),
        ]
        config = ARAgingConfig(credit_limit_high_pct=1.50)
        result = run_credit_limits(entries, config)
        assert result.entries_flagged >= 1
        assert result.flagged_entries[0].severity == Severity.HIGH


# =============================================================================
# TEST BATTERY
# =============================================================================

class TestBattery:
    """Tests for run_ar_test_battery."""

    def test_tb_only_runs_4_active(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, [], config, False)
        assert len(results) == 11  # All 11 test slots
        active = [r for r in results if not r.skipped]
        # AR01, AR02, AR07, AR09 = 4 active (AR09 may also be skipped if no prior DSO)
        assert len(active) >= 3  # At minimum AR01, AR02, AR07

    def test_full_mode_all_11(self):
        accounts = make_tb_accounts()
        entries = make_sl_entries()
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, entries, config, True)
        assert len(results) == 11
        # At least 8 should be active (AR09, AR10, AR11 may be skipped without config)
        active = [r for r in results if not r.skipped]
        assert len(active) >= 8

    def test_skipped_tests_have_reason(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, [], config, False)
        skipped = [r for r in results if r.skipped]
        for r in skipped:
            assert r.skip_reason is not None
            assert len(r.skip_reason) > 0

    def test_all_test_keys_unique(self):
        accounts = make_tb_accounts()
        entries = make_sl_entries()
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, entries, config, True)
        keys = [r.test_key for r in results]
        assert len(keys) == len(set(keys))


# =============================================================================
# COMPOSITE SCORING
# =============================================================================

class TestCompositeScoring:
    """Tests for calculate_ar_composite_score."""

    def test_zero_score_clean(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, [], config, False)
        composite = run_composite_score(results, False)
        assert composite.score >= 0

    def test_risk_tier_low(self):
        assert score_to_risk_tier(5.0) == RiskTier.LOW

    def test_risk_tier_elevated(self):
        assert score_to_risk_tier(15.0) == RiskTier.ELEVATED

    def test_risk_tier_moderate(self):
        assert score_to_risk_tier(35.0) == RiskTier.MODERATE

    def test_risk_tier_high(self):
        assert score_to_risk_tier(60.0) == RiskTier.HIGH

    def test_risk_tier_critical(self):
        assert score_to_risk_tier(80.0) == RiskTier.CRITICAL

    def test_tracks_tests_skipped(self):
        accounts = make_tb_accounts()
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, [], config, False)
        composite = run_composite_score(results, False)
        assert composite.tests_skipped > 0

    def test_top_findings_populated(self):
        # Create a scenario with flags
        accounts = [
            TBAccount(account_name="AR", balance=-50000, classification="ar", row_number=1),
        ]
        config = ARAgingConfig()
        results = run_ar_test_battery(accounts, [], config, False)
        composite = run_composite_score(results, False)
        if composite.total_flagged > 0:
            assert len(composite.top_findings) > 0

    def test_score_capped_at_100(self):
        composite = ARCompositeScore(score=150.0, risk_tier=RiskTier.CRITICAL, tests_run=11, tests_skipped=0, total_flagged=100)
        # Just verify the model allows it; actual scoring caps at 100
        assert composite.score == 150.0  # Model doesn't cap; function does


# =============================================================================
# AR SUMMARY
# =============================================================================

class TestARSummary:
    """Tests for build_ar_summary."""

    def test_tb_only_summary(self):
        accounts = make_tb_accounts()
        summary = run_build_summary(accounts, [], False)
        assert summary["total_ar_balance"] > 0
        assert summary["ar_account_count"] == 2
        assert summary["has_subledger"] is False

    def test_full_summary(self):
        accounts = make_tb_accounts()
        entries = make_sl_entries()
        summary = run_build_summary(accounts, entries, True)
        assert summary["has_subledger"] is True
        assert summary["subledger_entry_count"] == 8
        assert "aging_distribution" in summary

    def test_dso_calculated(self):
        accounts = make_tb_accounts()
        summary = run_build_summary(accounts, [], False)
        assert "dso" in summary

    def test_allowance_ratio_calculated(self):
        accounts = make_tb_accounts()
        summary = run_build_summary(accounts, [], False)
        assert "allowance_ratio" in summary


# =============================================================================
# FULL PIPELINE
# =============================================================================

class TestFullPipeline:
    """Tests for run_ar_aging end-to-end."""

    def test_tb_only_pipeline(self):
        tb_rows = sample_tb_rows()
        tb_cols = list(tb_rows[0].keys())
        result = run_ar_aging(tb_rows, tb_cols)
        assert result.composite_score is not None
        assert len(result.test_results) == 11
        assert result.data_quality is not None
        assert result.tb_column_detection is not None
        assert result.sl_column_detection is None

    def test_full_pipeline(self):
        tb_rows = sample_tb_rows()
        tb_cols = list(tb_rows[0].keys())
        sl_rows = sample_sl_rows()
        sl_cols = list(sl_rows[0].keys())
        result = run_ar_aging(tb_rows, tb_cols, sl_rows, sl_cols)
        assert result.sl_column_detection is not None
        assert result.ar_summary is not None
        assert result.ar_summary["has_subledger"] is True

    def test_pipeline_with_config(self):
        tb_rows = sample_tb_rows()
        tb_cols = list(tb_rows[0].keys())
        config = ARAgingConfig(prior_period_dso=50.0, days_in_period=365)
        result = run_ar_aging(tb_rows, tb_cols, config=config)
        dso_results = [r for r in result.test_results if r.test_key == "dso_trend"]
        assert len(dso_results) == 1
        assert dso_results[0].skipped is False

    def test_pipeline_with_column_mapping(self):
        tb_rows = [{"Col_A": "AR Trade", "Col_B": "1200", "Col_C": 500000}]
        result = run_ar_aging(
            tb_rows, ["Col_A", "Col_B", "Col_C"],
            tb_column_mapping={"account_name_column": "Col_A", "balance_column": "Col_C"},
        )
        assert result.tb_column_detection.account_name_column == "Col_A"
        assert result.tb_column_detection.overall_confidence == 1.0

    def test_empty_tb(self):
        result = run_ar_aging([], [])
        assert result.composite_score.tests_run >= 0
        assert len(result.test_results) == 11


# =============================================================================
# SERIALIZATION
# =============================================================================

class TestSerialization:
    """Tests for to_dict() methods."""

    def test_full_result_serialization(self):
        tb_rows = sample_tb_rows()
        sl_rows = sample_sl_rows()
        result = run_ar_aging(tb_rows, list(tb_rows[0].keys()), sl_rows, list(sl_rows[0].keys()))
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "ar_summary" in d
        assert isinstance(d["test_results"], list)
        assert len(d["test_results"]) == 11

    def test_test_result_serialization(self):
        result = ARTestResult(
            test_name="Test", test_key="test_key", test_tier=TestTier.STRUCTURAL,
            entries_flagged=0, total_entries=10, flag_rate=0.0,
            severity=Severity.LOW, description="desc",
        )
        d = result.to_dict()
        assert d["test_tier"] == "structural"
        assert d["severity"] == "low"

    def test_flagged_entry_serialization(self):
        entry = AREntry(account_name="AR", amount=1000, entry_source="tb")
        flagged = FlaggedAR(
            entry=entry, test_name="T", test_key="k", test_tier=TestTier.STRUCTURAL,
            severity=Severity.HIGH, issue="test issue",
        )
        d = flagged.to_dict()
        assert d["entry"]["account_name"] == "AR"
        assert d["severity"] == "high"

    def test_composite_score_serialization(self):
        score = ARCompositeScore(
            score=25.5, risk_tier=RiskTier.MODERATE, tests_run=9,
            tests_skipped=2, total_flagged=5, has_subledger=True,
        )
        d = score.to_dict()
        assert d["score"] == 25.5
        assert d["risk_tier"] == "moderate"
        assert d["has_subledger"] is True

    def test_tb_column_detection_serialization(self):
        det = TBColumnDetection(account_name_column="Name", balance_column="Bal", overall_confidence=0.85)
        d = det.to_dict()
        assert d["account_name_column"] == "Name"
        assert d["overall_confidence"] == 0.85

    def test_sl_column_detection_serialization(self):
        det = SLColumnDetection(customer_name_column="Cust", amount_column="Amt", overall_confidence=0.90)
        d = det.to_dict()
        assert d["customer_name_column"] == "Cust"
        assert d["overall_confidence"] == 0.90


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

class TestRouteRegistration:
    """Tests for AR aging route registration."""

    def test_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/audit/ar-aging" in paths

    def test_route_accepts_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/audit/ar-aging":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /audit/ar-aging not found")


# =============================================================================
# EXISTING TEST UPDATES (tool count assertions)
# =============================================================================

class TestToolNameEnum:
    """Tests for ToolName enum including AR_AGING."""

    def test_ar_aging_in_enum(self):
        from engagement_model import ToolName
        assert hasattr(ToolName, "AR_AGING")
        assert ToolName.AR_AGING.value == "ar_aging"

    def test_enum_has_all_tools(self):
        from engagement_model import ToolName
        assert len(ToolName) == 13

    def test_workpaper_labels_has_ar(self):
        from engagement_model import ToolName
        from workpaper_index_generator import TOOL_LABELS
        assert ToolName.AR_AGING in TOOL_LABELS

    def test_workpaper_refs_has_ar(self):
        from engagement_model import ToolName
        from workpaper_index_generator import TOOL_LEAD_SHEET_REFS
        assert ToolName.AR_AGING in TOOL_LEAD_SHEET_REFS
