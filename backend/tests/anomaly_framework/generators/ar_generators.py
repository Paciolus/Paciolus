"""AR Aging anomaly generators — 11 detectors.

Each generator injects a specific anomaly pattern into clean AR Aging
data (TB + sub-ledger) and returns an AnomalyRecord describing the
expected detection.

Generators that require large populations are marked with
`requires_large_population = True` and are excluded from the small registry.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class ARGeneratorBase:
    """Base class for AR Aging anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject_tb(
        self, tb_rows: list[dict], sl_rows: list[dict], seed: int = 42
    ) -> tuple[list[dict], list[dict], list[AnomalyRecord]]:
        """Inject anomaly into TB and/or SL rows.

        Returns:
            Tuple of (mutated_tb_rows, mutated_sl_rows, anomaly_records).
        """
        raise NotImplementedError


class ARSignAnomaliesGenerator(ARGeneratorBase):
    """AR-01: Inject negative amounts in sub-ledger (sign anomalies)."""

    name = "ar_sign_anomalies"
    target_test_key = "ar_sign_anomalies"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Add a negative-amount invoice to the sub-ledger
        sl_rows.append(
            {
                "Customer ID": "CUST-006",
                "Customer Name": "Negative Balance LLC",
                "Invoice Number": "INV-9901",
                "Invoice Date": "2025-05-01",
                "Amount": -3500.00,
                "Days Past Due": 15,
                "Aging Bucket": "Current",
            }
        )
        # Adjust TB AR balance to keep reconciliation clean
        for row in tb_rows:
            if row["Account"] == "1100":
                row["Debit"] -= 3500.00
                break
        record = AnomalyRecord(
            anomaly_type="ar_sign_anomalies",
            report_targets=["AR-01"],
            injected_at="SL invoice INV-9901 with negative amount -$3,500",
            expected_field="ar_sign_anomalies",
            expected_condition="entries_flagged > 0",
            metadata={"amount": -3500.00},
        )
        return tb_rows, sl_rows, [record]


class ARMissingAllowanceGenerator(ARGeneratorBase):
    """AR-02: Remove allowance account from TB."""

    name = "ar_missing_allowance"
    target_test_key = "missing_allowance"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Remove the allowance account
        tb_rows = [r for r in tb_rows if "Allowance" not in r["Account Name"]]
        # Rebalance by adding the allowance amount to an expense account
        for row in tb_rows:
            if row["Account"] == "6100":
                row["Debit"] += 4231.15
                break
        record = AnomalyRecord(
            anomaly_type="ar_missing_allowance",
            report_targets=["AR-02"],
            injected_at="Removed Allowance for Doubtful Accounts (1105) from TB",
            expected_field="missing_allowance",
            expected_condition="entries_flagged > 0",
        )
        return tb_rows, sl_rows, [record]


class ARNegativeAgingGenerator(ARGeneratorBase):
    """AR-03: Inject negative aging bucket amounts."""

    name = "ar_negative_aging"
    target_test_key = "negative_aging"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Add an invoice with a negative days past due
        sl_rows.append(
            {
                "Customer ID": "CUST-006",
                "Customer Name": "Early Pay Corp",
                "Invoice Number": "INV-9902",
                "Invoice Date": "2025-06-15",
                "Amount": 2750.00,
                "Days Past Due": -10,
                "Aging Bucket": "Current",
            }
        )
        # Adjust TB AR balance
        for row in tb_rows:
            if row["Account"] == "1100":
                row["Debit"] += 2750.00
                break
        # Rebalance TB
        for row in tb_rows:
            if row["Account"] == "6100":
                row["Debit"] -= 2750.00
                break
        record = AnomalyRecord(
            anomaly_type="ar_negative_aging",
            report_targets=["AR-03"],
            injected_at="SL invoice INV-9902 with -10 Days Past Due",
            expected_field="negative_aging",
            expected_condition="entries_flagged > 0",
            metadata={"days_past_due": -10},
        )
        return tb_rows, sl_rows, [record]


class ARUnreconciledDetailGenerator(ARGeneratorBase):
    """AR-04: Make SL total not match TB AR balance."""

    name = "ar_unreconciled_detail"
    target_test_key = "unreconciled_detail"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Inflate TB AR balance without changing SL
        for row in tb_rows:
            if row["Account"] == "1100":
                row["Debit"] += 15000.00
                break
        # Rebalance TB with expense reduction
        for row in tb_rows:
            if row["Account"] == "6100":
                row["Debit"] -= 15000.00
                break
        record = AnomalyRecord(
            anomaly_type="ar_unreconciled_detail",
            report_targets=["AR-04"],
            injected_at="TB AR balance inflated by $15,000 vs SL total",
            expected_field="unreconciled_detail",
            expected_condition="entries_flagged > 0",
            metadata={"variance": 15000.00},
        )
        return tb_rows, sl_rows, [record]


class ARBucketConcentrationGenerator(ARGeneratorBase):
    """AR-05: Concentrate >50% of AR in one aging bucket."""

    name = "ar_bucket_concentration"
    target_test_key = "bucket_concentration"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Move all invoices to 91+ bucket
        for row in sl_rows:
            row["Aging Bucket"] = "91+"
            row["Days Past Due"] = 120
        record = AnomalyRecord(
            anomaly_type="ar_bucket_concentration",
            report_targets=["AR-05"],
            injected_at="All invoices moved to 91+ aging bucket (100% concentration)",
            expected_field="bucket_concentration",
            expected_condition="entries_flagged > 0",
            metadata={"bucket": "91+", "concentration_pct": 1.0},
        )
        return tb_rows, sl_rows, [record]


class ARPastDueConcentrationGenerator(ARGeneratorBase):
    """AR-06: Make high past-due ratio (>50% of AR past due)."""

    name = "ar_past_due_concentration"
    target_test_key = "past_due_concentration"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Set all invoices to 45+ days past due
        for row in sl_rows:
            row["Days Past Due"] = 75
            row["Aging Bucket"] = "61-90"
        record = AnomalyRecord(
            anomaly_type="ar_past_due_concentration",
            report_targets=["AR-06"],
            injected_at="All invoices set to 75 days past due (100% past-due ratio)",
            expected_field="past_due_concentration",
            expected_condition="entries_flagged > 0",
            metadata={"past_due_pct": 1.0},
        )
        return tb_rows, sl_rows, [record]


class ARCustomerConcentrationGenerator(ARGeneratorBase):
    """AR-08: Concentrate >40% of AR in one customer."""

    name = "ar_customer_concentration"
    target_test_key = "customer_concentration"

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Reassign all invoices to a single customer
        for row in sl_rows:
            row["Customer ID"] = "CUST-001"
            row["Customer Name"] = "Acme Corporation"
        record = AnomalyRecord(
            anomaly_type="ar_customer_concentration",
            report_targets=["AR-08"],
            injected_at="All invoices assigned to CUST-001 (100% customer concentration)",
            expected_field="customer_concentration",
            expected_condition="entries_flagged > 0",
            metadata={"customer": "CUST-001", "concentration_pct": 1.0},
        )
        return tb_rows, sl_rows, [record]


# =============================================================================
# Generators requiring large populations (excluded from default registry)
# =============================================================================


class ARAllowanceAdequacyGenerator(ARGeneratorBase):
    """AR-07: Allowance adequacy ratio anomaly. Needs sufficient data for ratio calculation."""

    name = "ar_allowance_adequacy"
    target_test_key = "allowance_adequacy"
    requires_large_population = True

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Reduce allowance to near-zero to trigger inadequacy flag
        for row in tb_rows:
            if "Allowance" in row["Account Name"]:
                row["Credit"] = 10.00
                break
        # Rebalance TB
        for row in tb_rows:
            if row["Account"] == "6100":
                row["Debit"] -= 4221.15
                break
        record = AnomalyRecord(
            anomaly_type="ar_allowance_adequacy",
            report_targets=["AR-07"],
            injected_at="Allowance reduced to $10 (vs $84,623 AR = 0.01%)",
            expected_field="allowance_adequacy",
            expected_condition="entries_flagged > 0",
            metadata={"allowance": 10.00, "ar_balance": 84623.00},
        )
        return tb_rows, sl_rows, [record]


class ARDSOTrendGenerator(ARGeneratorBase):
    """AR-09: DSO trend variance anomaly. Needs multi-period data."""

    name = "ar_dso_trend"
    target_test_key = "dso_trend"
    requires_large_population = True

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Set all invoices to very high days past due to spike DSO
        for row in sl_rows:
            row["Days Past Due"] = 180
            row["Aging Bucket"] = "91+"
        record = AnomalyRecord(
            anomaly_type="ar_dso_trend",
            report_targets=["AR-09"],
            injected_at="All invoices set to 180 days past due (extreme DSO)",
            expected_field="dso_trend",
            expected_condition="entries_flagged > 0",
        )
        return tb_rows, sl_rows, [record]


class ARRollForwardGenerator(ARGeneratorBase):
    """AR-10: Roll-forward reconciliation anomaly. Needs prior period data."""

    name = "ar_roll_forward"
    target_test_key = "rollforward_reconciliation"
    requires_large_population = True

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # This test requires prior-period comparisons; inject a large
        # unexplained variance by inflating the current AR balance
        for row in tb_rows:
            if row["Account"] == "1100":
                row["Debit"] += 50000.00
                break
        # Rebalance TB
        for row in tb_rows:
            if row["Account"] == "6100":
                row["Debit"] -= 50000.00
                break
        record = AnomalyRecord(
            anomaly_type="ar_roll_forward",
            report_targets=["AR-10"],
            injected_at="TB AR balance inflated by $50,000 (roll-forward gap)",
            expected_field="rollforward_reconciliation",
            expected_condition="entries_flagged > 0",
            metadata={"variance": 50000.00},
        )
        return tb_rows, sl_rows, [record]


class ARCreditLimitGenerator(ARGeneratorBase):
    """AR-11: Credit limit breach anomaly. Needs credit limit column."""

    name = "ar_credit_limit"
    target_test_key = "credit_limit_breaches"
    requires_large_population = True

    def inject_tb(self, tb_rows, sl_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        sl_rows = deepcopy(sl_rows)
        # Add Credit Limit column and set one customer way over limit
        for row in sl_rows:
            row["Credit Limit"] = 50000.00
        # Make CUST-001's total exceed credit limit
        sl_rows.append(
            {
                "Customer ID": "CUST-001",
                "Customer Name": "Acme Corporation",
                "Invoice Number": "INV-9903",
                "Invoice Date": "2025-06-01",
                "Amount": 45000.00,
                "Days Past Due": 0,
                "Aging Bucket": "Current",
                "Credit Limit": 50000.00,
            }
        )
        # Adjust TB AR balance
        for row in tb_rows:
            if row["Account"] == "1100":
                row["Debit"] += 45000.00
                break
        # Rebalance TB
        for row in tb_rows:
            if row["Account"] == "6100":
                row["Debit"] -= 45000.00
                break
        record = AnomalyRecord(
            anomaly_type="ar_credit_limit",
            report_targets=["AR-11"],
            injected_at="CUST-001 total $69,665 exceeds $50,000 credit limit",
            expected_field="credit_limit_breaches",
            expected_condition="entries_flagged > 0",
            metadata={"customer": "CUST-001", "total": 69665.00, "limit": 50000.00},
        )
        return tb_rows, sl_rows, [record]


# =============================================================================
# Registry of all AR generators
# =============================================================================

AR_REGISTRY: list[ARGeneratorBase] = [
    ARSignAnomaliesGenerator(),
    ARMissingAllowanceGenerator(),
    ARNegativeAgingGenerator(),
    ARUnreconciledDetailGenerator(),
    ARBucketConcentrationGenerator(),
    ARPastDueConcentrationGenerator(),
    ARCustomerConcentrationGenerator(),
    ARAllowanceAdequacyGenerator(),
    ARDSOTrendGenerator(),
    ARRollForwardGenerator(),
    ARCreditLimitGenerator(),
]

# Small-population-safe generators (work with baseline data)
AR_REGISTRY_SMALL = [g for g in AR_REGISTRY if not g.requires_large_population]
