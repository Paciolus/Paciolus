"""Journal Entry Testing anomaly generators — 19 detectors.

Each generator injects a specific anomaly pattern into clean journal entry
data and returns an AnomalyRecord describing the expected detection.

Generators that require large populations (500+ entries) are marked with
`requires_large_population = True` and are excluded from default registry.
"""

import random
from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class JEGeneratorBase:
    """Base class for JE anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject(self, rows: list[dict], seed: int = 42) -> tuple[list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


class JEUnbalancedEntryGenerator(JEGeneratorBase):
    """T1: Inject an unbalanced journal entry (debit != credit)."""

    name = "je_unbalanced_entry"
    target_test_key = "unbalanced_entries"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Entry ID": "JE-099",
                    "Entry Date": "2025-06-10",
                    "Account": "6100",
                    "Account Name": "Rent Expense",
                    "Description": "Unbalanced rent entry",
                    "Debit": 5432.00,
                    "Credit": 0.00,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
                {
                    "Entry ID": "JE-099",
                    "Entry Date": "2025-06-10",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Unbalanced rent entry",
                    "Debit": 0.00,
                    "Credit": 4932.00,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_unbalanced_entry",
            report_targets=["JE-T1"],
            injected_at="Entry JE-099 with $500 imbalance",
            expected_field="unbalanced_entries",
            expected_condition="entries_flagged > 0",
            metadata={"imbalance": 500.00},
        )
        return rows, [record]


class JEMissingFieldsGenerator(JEGeneratorBase):
    """T2: Inject an entry with missing required fields."""

    name = "je_missing_fields"
    target_test_key = "missing_fields"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Entry ID": "",
                    "Entry Date": "",
                    "Account": "",
                    "Account Name": "",
                    "Description": "",
                    "Debit": 1234.56,
                    "Credit": 0.00,
                    "Posted By": "",
                    "Source": "",
                },
                {
                    "Entry ID": "",
                    "Entry Date": "",
                    "Account": "",
                    "Account Name": "",
                    "Description": "",
                    "Debit": 0.00,
                    "Credit": 1234.56,
                    "Posted By": "",
                    "Source": "",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_missing_fields",
            report_targets=["JE-T2"],
            injected_at="Entry with all fields blank",
            expected_field="missing_fields",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JEDuplicateEntryGenerator(JEGeneratorBase):
    """T3: Inject duplicate journal entries."""

    name = "je_duplicate_entry"
    target_test_key = "duplicate_entries"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rng = random.Random(seed)
        # Pick a row and duplicate it with a new entry ID
        source = rng.choice([r for r in rows if r["Debit"] > 0])
        dup = dict(source)
        dup["Entry ID"] = "JE-098"
        rows.append(dup)
        # Add matching credit
        credit_match = next(
            (r for r in rows if r["Entry ID"] == source["Entry ID"] and r["Credit"] > 0),
            None,
        )
        if credit_match:
            dup2 = dict(credit_match)
            dup2["Entry ID"] = "JE-098"
            rows.append(dup2)
        record = AnomalyRecord(
            anomaly_type="je_duplicate_entry",
            report_targets=["JE-T3"],
            injected_at=f"Duplicated entry from {source['Entry ID']}",
            expected_field="duplicate_entries",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JERoundAmountGenerator(JEGeneratorBase):
    """T4: Inject a round-dollar amount entry (>=$10K, divisible by $10K)."""

    name = "je_round_amount"
    target_test_key = "round_amounts"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Entry ID": "JE-097",
                    "Entry Date": "2025-06-11",
                    "Account": "6100",
                    "Account Name": "Rent Expense",
                    "Description": "Quarterly facility payment",
                    "Debit": 50000.00,
                    "Credit": 0.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-097",
                    "Entry Date": "2025-06-11",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Quarterly facility payment",
                    "Debit": 0.00,
                    "Credit": 50000.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_round_amount",
            report_targets=["JE-T4"],
            injected_at="Entry JE-097 with $50,000 round amount",
            expected_field="round_amounts",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 50000.00},
        )
        return rows, [record]


class JEWeekendPostingGenerator(JEGeneratorBase):
    """T7: Inject an entry posted on a weekend."""

    name = "je_weekend_posting"
    target_test_key = "weekend_postings"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # 2025-06-07 is a Saturday
        rows.extend(
            [
                {
                    "Entry ID": "JE-096",
                    "Entry Date": "2025-06-07",
                    "Account": "6700",
                    "Account Name": "Marketing Expense",
                    "Description": "Weekend campaign push",
                    "Debit": 15234.00,
                    "Credit": 0.00,
                    "Posted By": "agarcia",
                    "Source": "CC",
                },
                {
                    "Entry ID": "JE-096",
                    "Entry Date": "2025-06-07",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Weekend campaign push",
                    "Debit": 0.00,
                    "Credit": 15234.00,
                    "Posted By": "agarcia",
                    "Source": "CC",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_weekend_posting",
            report_targets=["JE-T7"],
            injected_at="Entry JE-096 posted on Saturday 2025-06-07",
            expected_field="weekend_postings",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JESuspiciousKeywordGenerator(JEGeneratorBase):
    """T13: Inject an entry with suspicious keywords in description."""

    name = "je_suspicious_keyword"
    target_test_key = "suspicious_keywords"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Entry ID": "JE-095",
                    "Entry Date": "2025-06-12",
                    "Account": "1100",
                    "Account Name": "Accounts Receivable",
                    "Description": "Write off bad debt - customer bankruptcy",
                    "Debit": 0.00,
                    "Credit": 8765.43,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
                {
                    "Entry ID": "JE-095",
                    "Entry Date": "2025-06-12",
                    "Account": "6800",
                    "Account Name": "Bad Debt Expense",
                    "Description": "Write off bad debt - customer bankruptcy",
                    "Debit": 8765.43,
                    "Credit": 0.00,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_suspicious_keyword",
            report_targets=["JE-T13"],
            injected_at="Entry JE-095 with 'write off' keyword",
            expected_field="suspicious_keywords",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JEJustBelowThresholdGenerator(JEGeneratorBase):
    """T16: Inject an entry just below an approval threshold."""

    name = "je_just_below_threshold"
    target_test_key = "just_below_threshold"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # $9,950 is 0.5% below $10,000 threshold (within 5% proximity)
        rows.extend(
            [
                {
                    "Entry ID": "JE-094",
                    "Entry Date": "2025-06-13",
                    "Account": "6600",
                    "Account Name": "Professional Fees",
                    "Description": "Consulting engagement payment",
                    "Debit": 9950.00,
                    "Credit": 0.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-094",
                    "Entry Date": "2025-06-13",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Consulting engagement payment",
                    "Debit": 0.00,
                    "Credit": 9950.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_just_below_threshold",
            report_targets=["JE-T16"],
            injected_at="Entry JE-094 at $9,950 (just below $10K threshold)",
            expected_field="just_below_threshold",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JEBackdatedEntryGenerator(JEGeneratorBase):
    """T12: Inject a backdated entry (posting date >> entry date).

    Adds a Posting Date column to ALL rows so the engine can detect the gap.
    """

    name = "je_backdated_entry"
    target_test_key = "backdated_entries"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add Posting Date = Entry Date for all existing rows (normal)
        for r in rows:
            if "Posting Date" not in r:
                r["Posting Date"] = r["Entry Date"]
        # Inject backdated entry: entry_date is 62 days before posting_date
        rows.extend(
            [
                {
                    "Entry ID": "JE-093",
                    "Entry Date": "2025-04-15",
                    "Posting Date": "2025-06-16",
                    "Account": "4000",
                    "Account Name": "Service Revenue",
                    "Description": "Late-recognized April revenue",
                    "Debit": 0.00,
                    "Credit": 7654.32,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
                {
                    "Entry ID": "JE-093",
                    "Entry Date": "2025-04-15",
                    "Posting Date": "2025-06-16",
                    "Account": "1100",
                    "Account Name": "Accounts Receivable",
                    "Description": "Late-recognized April revenue",
                    "Debit": 7654.32,
                    "Credit": 0.00,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_backdated_entry",
            report_targets=["JE-T12"],
            injected_at="Entry JE-093 backdated 62 days (Apr 15 → Jun 16 posting)",
            expected_field="backdated_entries",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JENumberingGapGenerator(JEGeneratorBase):
    """T11: Inject entries with sequential numbering gaps."""

    name = "je_numbering_gap"
    target_test_key = "numbering_gaps"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add entries that create a visible gap (JE-026 exists but JE-027..JE-029 missing, then JE-030)
        rows.extend(
            [
                {
                    "Entry ID": "JE-026",
                    "Entry Date": "2025-06-27",
                    "Account": "6500",
                    "Account Name": "Office Supplies",
                    "Description": "Printer supplies",
                    "Debit": 234.56,
                    "Credit": 0.00,
                    "Posted By": "agarcia",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-026",
                    "Entry Date": "2025-06-27",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Printer supplies",
                    "Debit": 0.00,
                    "Credit": 234.56,
                    "Posted By": "agarcia",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-030",
                    "Entry Date": "2025-06-27",
                    "Account": "6200",
                    "Account Name": "Utilities Expense",
                    "Description": "Water bill",
                    "Debit": 187.23,
                    "Credit": 0.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-030",
                    "Entry Date": "2025-06-27",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Water bill",
                    "Debit": 0.00,
                    "Credit": 187.23,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_numbering_gap",
            report_targets=["JE-T11"],
            injected_at="Gap in entry IDs: JE-027 through JE-029 missing",
            expected_field="numbering_gaps",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JEHolidayPostingGenerator(JEGeneratorBase):
    """T14: Inject an entry posted on a holiday."""

    name = "je_holiday_posting"
    target_test_key = "holiday_postings"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # 2025-07-04 is Independence Day (Friday)
        rows.extend(
            [
                {
                    "Entry ID": "JE-092",
                    "Entry Date": "2025-07-04",
                    "Account": "6100",
                    "Account Name": "Rent Expense",
                    "Description": "Emergency facility payment",
                    "Debit": 3456.78,
                    "Credit": 0.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-092",
                    "Entry Date": "2025-07-04",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Emergency facility payment",
                    "Debit": 0.00,
                    "Credit": 3456.78,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_holiday_posting",
            report_targets=["JE-T14"],
            injected_at="Entry JE-092 posted on July 4th (Independence Day)",
            expected_field="holiday_postings",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


# =============================================================================
# Generators requiring large populations (excluded from default registry)
# =============================================================================


class JEUnusualAmountGenerator(JEGeneratorBase):
    """T5: Inject an unusually large amount (z-score outlier). Needs 5+ entries per account."""

    name = "je_unusual_amount"
    target_test_key = "unusual_amounts"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add several normal entries to the same account, then one outlier
        for i in range(6):
            rows.extend(
                [
                    {
                        "Entry ID": f"JE-08{i}",
                        "Entry Date": f"2025-06-{10 + i:02d}",
                        "Account": "6100",
                        "Account Name": "Rent Expense",
                        "Description": f"Normal rent payment #{i}",
                        "Debit": 3456.00 + i * 10,
                        "Credit": 0.00,
                        "Posted By": "mwilson",
                        "Source": "AP",
                    },
                    {
                        "Entry ID": f"JE-08{i}",
                        "Entry Date": f"2025-06-{10 + i:02d}",
                        "Account": "1000",
                        "Account Name": "Cash - Operating",
                        "Description": f"Normal rent payment #{i}",
                        "Debit": 0.00,
                        "Credit": 3456.00 + i * 10,
                        "Posted By": "mwilson",
                        "Source": "AP",
                    },
                ]
            )
        # Outlier entry — 10x normal
        rows.extend(
            [
                {
                    "Entry ID": "JE-089",
                    "Entry Date": "2025-06-17",
                    "Account": "6100",
                    "Account Name": "Rent Expense",
                    "Description": "Unusual large rent payment",
                    "Debit": 34560.00,
                    "Credit": 0.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
                {
                    "Entry ID": "JE-089",
                    "Entry Date": "2025-06-17",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Unusual large rent payment",
                    "Debit": 0.00,
                    "Credit": 34560.00,
                    "Posted By": "mwilson",
                    "Source": "AP",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_unusual_amount",
            report_targets=["JE-T5"],
            injected_at="Entry JE-089 with $34,560 (10x normal rent)",
            expected_field="unusual_amounts",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class JEAfterHoursGenerator(JEGeneratorBase):
    """T10: Inject an after-hours posting. Requires time in Entry Date or Posting Date."""

    name = "je_after_hours"
    target_test_key = "after_hours_postings"
    requires_large_population = True  # Needs datetime parsing with time component

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Entry ID": "JE-091",
                    "Entry Date": "2025-06-11 02:30:00",
                    "Account": "6600",
                    "Account Name": "Professional Fees",
                    "Description": "Late night posting",
                    "Debit": 6543.21,
                    "Credit": 0.00,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
                {
                    "Entry ID": "JE-091",
                    "Entry Date": "2025-06-11 02:30:00",
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Description": "Late night posting",
                    "Debit": 0.00,
                    "Credit": 6543.21,
                    "Posted By": "jsmith",
                    "Source": "GL",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="je_after_hours",
            report_targets=["JE-T10"],
            injected_at="Entry JE-091 posted at 02:30 AM",
            expected_field="after_hours_postings",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


# =============================================================================
# Registry of all JE generators
# =============================================================================

JE_REGISTRY: list[JEGeneratorBase] = [
    JEUnbalancedEntryGenerator(),
    JEMissingFieldsGenerator(),
    JEDuplicateEntryGenerator(),
    JERoundAmountGenerator(),
    JEWeekendPostingGenerator(),
    JESuspiciousKeywordGenerator(),
    JEJustBelowThresholdGenerator(),
    JEBackdatedEntryGenerator(),
    JENumberingGapGenerator(),
    JEHolidayPostingGenerator(),
    JEUnusualAmountGenerator(),
    JEAfterHoursGenerator(),
]

# Small-population-safe generators (work with 25-entry baseline)
JE_REGISTRY_SMALL = [g for g in JE_REGISTRY if not g.requires_large_population]
