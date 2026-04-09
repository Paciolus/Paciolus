"""Bank Reconciliation anomaly generators.

Each generator injects a specific reconciliation anomaly into clean bank
statement and GL data, returning AnomalyRecords describing the expected
detection outcome.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class BankRecGeneratorBase:
    """Base class for bank reconciliation anomaly generators."""

    name: str
    target_test_key: str

    def inject(
        self,
        bank_rows: list[dict],
        gl_rows: list[dict],
        seed: int = 42,
    ) -> tuple[list[dict], list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


class BankOnlyItemsGenerator(BankRecGeneratorBase):
    """Inject an unmatched bank transaction (no GL counterpart).

    Adds an extra bank deposit with no corresponding GL entry, simulating
    a bank transaction that was never recorded in the general ledger.
    """

    name = "bank_only_items"
    target_test_key = "unmatched_bank"

    def inject(self, bank_rows, gl_rows, seed=42):
        bank_rows = deepcopy(bank_rows)
        gl_rows = deepcopy(gl_rows)

        bank_rows.append(
            {
                "Date": "2025-06-18",
                "Amount": 4567.89,
                "Description": "Wire Deposit - Unknown Remitter",
                "Check Number": "",
                "Transaction ID": "TXN-20250618-001",
            }
        )

        record = AnomalyRecord(
            anomaly_type="bank_only_items",
            report_targets=["BANKREC-01"],
            injected_at="Bank deposit TXN-20250618-001 with no GL match",
            expected_field="unmatched_bank",
            expected_condition="items_count > 0",
            metadata={"amount": 4567.89, "description": "Wire Deposit - Unknown Remitter"},
        )
        return bank_rows, gl_rows, [record]


class GLOnlyItemsGenerator(BankRecGeneratorBase):
    """Inject an unmatched GL entry (no bank counterpart).

    Adds an extra GL payment with no corresponding bank transaction,
    simulating a check that was recorded but not yet cleared.
    """

    name = "gl_only_items"
    target_test_key = "unmatched_gl"

    def inject(self, bank_rows, gl_rows, seed=42):
        bank_rows = deepcopy(bank_rows)
        gl_rows = deepcopy(gl_rows)

        gl_rows.append(
            {
                "Entry Date": "2025-06-19",
                "Account": "1000",
                "Description": "Vendor payment - outstanding check #10455",
                "Debit": 0.00,
                "Credit": 3245.67,
            }
        )

        record = AnomalyRecord(
            anomaly_type="gl_only_items",
            report_targets=["BANKREC-02"],
            injected_at="GL payment of $3,245.67 with no bank match",
            expected_field="unmatched_gl",
            expected_condition="items_count > 0",
            metadata={"amount": 3245.67, "description": "Vendor payment - outstanding check #10455"},
        )
        return bank_rows, gl_rows, [record]


class AmountDiscrepancyGenerator(BankRecGeneratorBase):
    """Inject a matched transaction with differing amounts.

    Modifies an existing bank transaction amount so it no longer matches
    the corresponding GL entry, simulating a recording error.
    """

    name = "amount_discrepancy"
    target_test_key = "amount_mismatches"

    def inject(self, bank_rows, gl_rows, seed=42):
        bank_rows = deepcopy(bank_rows)
        gl_rows = deepcopy(gl_rows)

        # Modify the insurance payment (index 6) — change bank amount by $150
        original_amount = bank_rows[6]["Amount"]  # -1897.50
        bank_rows[6]["Amount"] = -2047.50  # $150 discrepancy

        record = AnomalyRecord(
            anomaly_type="amount_discrepancy",
            report_targets=["BANKREC-03"],
            injected_at="Insurance payment: bank=$2,047.50 vs GL=$1,897.50",
            expected_field="amount_mismatches",
            expected_condition="items_count > 0",
            metadata={
                "bank_amount": -2047.50,
                "gl_amount": 1897.50,
                "discrepancy": 150.00,
                "original_bank_amount": original_amount,
            },
        )
        return bank_rows, gl_rows, [record]


class MissingCheckNumberGenerator(BankRecGeneratorBase):
    """Inject a check transaction without a check number.

    Adds a bank transaction that appears to be a check (based on description)
    but has no check number, which may indicate an irregularity.
    """

    name = "missing_check_number"
    target_test_key = "missing_references"

    def inject(self, bank_rows, gl_rows, seed=42):
        bank_rows = deepcopy(bank_rows)
        gl_rows = deepcopy(gl_rows)

        # Add a check-type payment with no check number
        bank_rows.append(
            {
                "Date": "2025-06-20",
                "Amount": -6234.00,
                "Description": "Check Payment - Vendor Services",
                "Check Number": "",
                "Transaction ID": "TXN-20250620-001",
            }
        )

        # Add matching GL entry so it reconciles on amount
        gl_rows.append(
            {
                "Entry Date": "2025-06-20",
                "Account": "1000",
                "Description": "Vendor services payment - check",
                "Debit": 0.00,
                "Credit": 6234.00,
            }
        )

        record = AnomalyRecord(
            anomaly_type="missing_check_number",
            report_targets=["BANKREC-04"],
            injected_at="Check payment of $6,234.00 with no check number",
            expected_field="missing_references",
            expected_condition="items_count > 0",
            metadata={"amount": -6234.00, "description": "Check Payment - Vendor Services"},
        )
        return bank_rows, gl_rows, [record]


BANK_REC_REGISTRY: list[BankRecGeneratorBase] = [
    BankOnlyItemsGenerator(),
    GLOnlyItemsGenerator(),
    AmountDiscrepancyGenerator(),
    MissingCheckNumberGenerator(),
]
