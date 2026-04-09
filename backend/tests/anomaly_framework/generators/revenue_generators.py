"""Revenue Testing anomaly generators -- 16 detectors.

Each generator injects a specific anomaly pattern into clean revenue entry
data and returns an AnomalyRecord describing the expected detection.

Generators that require large populations (50+ entries for Benford, 10+ per
account for z-score) are marked with `requires_large_population = True`
and are excluded from the default small-population registry.

Test keys match revenue_testing_engine.py exactly:
  RT-01  large_manual_entries
  RT-02  year_end_concentration
  RT-03  round_revenue_amounts
  RT-04  sign_anomalies
  RT-05  unclassified_entries
  RT-06  zscore_outliers           (requires_large_population)
  RT-07  trend_variance            (requires_large_population)
  RT-08  concentration_risk
  RT-09  cutoff_risk
  RT-10  benford_law               (requires_large_population)
  RT-11  duplicate_entries
  RT-12  contra_revenue_anomalies
  RT-13  recognition_before_satisfaction  (ASC 606)
  RT-14  missing_obligation_linkage       (ASC 606)
  RT-15  modification_treatment_mismatch  (ASC 606)
  RT-16  allocation_inconsistency         (ASC 606)
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class RevenueGeneratorBase:
    """Base class for Revenue anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject(self, rows: list[dict], seed: int = 42) -> tuple[list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


# =============================================================================
# TIER 1 -- STRUCTURAL TESTS
# =============================================================================


class RevenueLargeManualEntryGenerator(RevenueGeneratorBase):
    """RT-01: Inject a large manual revenue entry above threshold ($50K default)."""

    name = "revenue_large_manual_entry"
    target_test_key = "large_manual_entries"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Date": "2025-05-14",
                "Amount": 75432.50,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1199 - Enterprise platform implementation",
                "Entry Type": "manual",
                "Reference": "INV-1199",
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_large_manual_entry",
            report_targets=["RT-01"],
            injected_at="Manual revenue entry $75,432.50 above $50K threshold",
            expected_field="large_manual_entries",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 75432.50, "entry_type": "manual"},
        )
        return rows, [record]


class RevenueYearEndConcentrationGenerator(RevenueGeneratorBase):
    """RT-02: Inject entries clustered at end of period to trigger concentration."""

    name = "revenue_year_end_concentration"
    target_test_key = "year_end_concentration"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add 4 large entries in the last 3 days of the data period (June 25-27)
        # to push >20% of total revenue into the last 7 days
        late_entries = [
            {
                "Date": "2025-06-25",
                "Amount": 45678.90,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1200 - Year-end project close-out",
                "Entry Type": "system",
                "Reference": "INV-1200",
            },
            {
                "Date": "2025-06-26",
                "Amount": 38912.45,
                "Account Name": "Consulting Revenue",
                "Account Number": "4100",
                "Description": "Invoice MCG-1201 - Final deliverable acceptance",
                "Entry Type": "system",
                "Reference": "INV-1201",
            },
            {
                "Date": "2025-06-27",
                "Amount": 52341.75,
                "Account Name": "License Revenue",
                "Account Number": "4200",
                "Description": "Invoice MCG-1202 - Enterprise license bundle Q3",
                "Entry Type": "system",
                "Reference": "INV-1202",
            },
            {
                "Date": "2025-06-27",
                "Amount": 29876.30,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1203 - Accelerated services billing",
                "Entry Type": "system",
                "Reference": "INV-1203",
            },
        ]
        rows.extend(late_entries)
        record = AnomalyRecord(
            anomaly_type="revenue_year_end_concentration",
            report_targets=["RT-02"],
            injected_at="4 large entries in last 3 days totaling $166,809.40",
            expected_field="year_end_concentration",
            expected_condition="entries_flagged > 0",
            metadata={"late_total": 166809.40, "entry_count": 4},
        )
        return rows, [record]


class RevenueRoundAmountGenerator(RevenueGeneratorBase):
    """RT-03: Inject a round-dollar revenue entry >= $10K threshold."""

    name = "revenue_round_amount"
    target_test_key = "round_revenue_amounts"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Date": "2025-05-19",
                "Amount": 40000.00,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1210 - Quarterly retainer payment",
                "Entry Type": "system",
                "Reference": "INV-1210",
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_round_amount",
            report_targets=["RT-03"],
            injected_at="Round revenue entry $40,000.00 (divisible by $10,000)",
            expected_field="round_revenue_amounts",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 40000.00},
        )
        return rows, [record]


class RevenueSignAnomalyGenerator(RevenueGeneratorBase):
    """RT-04: Inject a negative (debit) revenue entry."""

    name = "revenue_sign_anomaly"
    target_test_key = "sign_anomalies"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Date": "2025-05-21",
                "Amount": -8765.43,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1211 - Fee reclassification entry",
                "Entry Type": "system",
                "Reference": "INV-1211",
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_sign_anomaly",
            report_targets=["RT-04"],
            injected_at="Negative revenue entry -$8,765.43",
            expected_field="sign_anomalies",
            expected_condition="entries_flagged > 0",
            metadata={"amount": -8765.43},
        )
        return rows, [record]


class RevenueUnclassifiedEntryGenerator(RevenueGeneratorBase):
    """RT-05: Inject entries without proper account classification."""

    name = "revenue_unclassified_entry"
    target_test_key = "unclassified_entries"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Date": "2025-05-16",
                "Amount": 6543.21,
                "Account Name": "",
                "Account Number": "",
                "Description": "Miscellaneous revenue receipt",
                "Entry Type": "system",
                "Reference": "MISC-001",
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_unclassified_entry",
            report_targets=["RT-05"],
            injected_at="Entry with blank Account Name and Account Number",
            expected_field="unclassified_entries",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class RevenueConcentrationRiskGenerator(RevenueGeneratorBase):
    """RT-08: Inject entries that create single-account concentration >50%."""

    name = "revenue_concentration_risk"
    target_test_key = "concentration_risk"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add a very large Service Revenue entry to push that account >50%
        rows.append(
            {
                "Date": "2025-05-08",
                "Amount": 185000.50,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1220 - Enterprise transformation program",
                "Entry Type": "system",
                "Reference": "INV-1220",
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_concentration_risk",
            report_targets=["RT-08"],
            injected_at="Service Revenue entry $185,000.50 creating >50% account concentration",
            expected_field="concentration_risk",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 185000.50, "account": "Service Revenue"},
        )
        return rows, [record]


class RevenueCutoffRiskGenerator(RevenueGeneratorBase):
    """RT-09: Inject entries near period boundaries within cutoff_days."""

    name = "revenue_cutoff_risk"
    target_test_key = "cutoff_risk"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add entry right at the start boundary (April 1) and end boundary (June 30)
        rows.extend(
            [
                {
                    "Date": "2025-04-01",
                    "Amount": 23456.78,
                    "Account Name": "Consulting Revenue",
                    "Account Number": "4100",
                    "Description": "Invoice MCG-1230 - Prior period engagement carryover",
                    "Entry Type": "system",
                    "Reference": "INV-1230",
                },
                {
                    "Date": "2025-06-30",
                    "Amount": 31245.90,
                    "Account Name": "Service Revenue",
                    "Account Number": "4000",
                    "Description": "Invoice MCG-1231 - Last day revenue recognition",
                    "Entry Type": "system",
                    "Reference": "INV-1231",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="revenue_cutoff_risk",
            report_targets=["RT-09"],
            injected_at="Entries at period boundaries: Apr 1 ($23,456.78) and Jun 30 ($31,245.90)",
            expected_field="cutoff_risk",
            expected_condition="entries_flagged > 0",
            metadata={"boundary_entries": 2},
        )
        return rows, [record]


class RevenueDuplicateEntryGenerator(RevenueGeneratorBase):
    """RT-11: Inject duplicate revenue entries (same date + amount + account)."""

    name = "revenue_duplicate_entry"
    target_test_key = "duplicate_entries"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Duplicate the first entry with a different reference
        dup = dict(rows[0])
        dup["Reference"] = "INV-1101-DUP"
        dup["Description"] = "Invoice MCG-1101 - IT consulting services (duplicate submission)"
        rows.append(dup)
        record = AnomalyRecord(
            anomaly_type="revenue_duplicate_entry",
            report_targets=["RT-11"],
            injected_at=f"Duplicated entry: {dup['Date']} / ${dup['Amount']:,.2f} / {dup['Account Name']}",
            expected_field="duplicate_entries",
            expected_condition="entries_flagged > 0",
            metadata={"duplicated_amount": dup["Amount"]},
        )
        return rows, [record]


class RevenueContraAnomalyGenerator(RevenueGeneratorBase):
    """RT-12: Inject entries with contra-revenue keywords (returns, refunds)."""

    name = "revenue_contra_anomaly"
    target_test_key = "contra_revenue_anomalies"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Date": "2025-05-09",
                    "Amount": 4321.50,
                    "Account Name": "Sales Returns and Allowances",
                    "Account Number": "4900",
                    "Description": "Customer return - defective product batch",
                    "Entry Type": "system",
                    "Reference": "RET-001",
                },
                {
                    "Date": "2025-06-05",
                    "Amount": 2150.75,
                    "Account Name": "Service Revenue",
                    "Account Number": "4000",
                    "Description": "Credit memo issued - service level refund",
                    "Entry Type": "system",
                    "Reference": "CM-001",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="revenue_contra_anomaly",
            report_targets=["RT-12"],
            injected_at="Contra-revenue entries with 'return' and 'credit memo' keywords",
            expected_field="contra_revenue_anomalies",
            expected_condition="entries_flagged > 0",
            metadata={"contra_count": 2, "keywords": ["return", "credit memo"]},
        )
        return rows, [record]


# =============================================================================
# ASC 606 / IFRS 15 CONTRACT-AWARE TESTS (RT-13 through RT-16)
# =============================================================================


class RevenueRecognitionBeforeSatisfactionGenerator(RevenueGeneratorBase):
    """RT-13: Inject revenue recognized before obligation satisfaction date.

    Adds contract-aware columns to all rows so the engine detects them.
    """

    name = "revenue_recognition_before_satisfaction"
    target_test_key = "recognition_before_satisfaction"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add contract columns to all existing rows (normal: recognized after satisfaction)
        for r in rows:
            r["Contract ID"] = r.get("Reference", "C-DEFAULT")
            r["Performance Obligation ID"] = f"PO-{r.get('Reference', 'X')}"
            r["Recognition Method"] = "point-in-time"
            r["Obligation Satisfaction Date"] = r["Date"]  # Same day = OK

        # Inject entry recognized 15 days BEFORE satisfaction date
        rows.append(
            {
                "Date": "2025-05-05",
                "Amount": 19876.50,
                "Account Name": "Service Revenue",
                "Account Number": "4000",
                "Description": "Invoice MCG-1240 - Premature milestone billing",
                "Entry Type": "system",
                "Reference": "INV-1240",
                "Contract ID": "C-2025-042",
                "Performance Obligation ID": "PO-042-A",
                "Recognition Method": "point-in-time",
                "Obligation Satisfaction Date": "2025-05-20",  # 15 days AFTER recognition
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_recognition_before_satisfaction",
            report_targets=["RT-13"],
            injected_at="Revenue recognized 15 days before obligation satisfaction (May 5 vs May 20)",
            expected_field="recognition_before_satisfaction",
            expected_condition="entries_flagged > 0",
            metadata={"delta_days": 15, "recognition_date": "2025-05-05", "satisfaction_date": "2025-05-20"},
        )
        return rows, [record]


class RevenueMissingObligationLinkageGenerator(RevenueGeneratorBase):
    """RT-14: Inject entry with contract_id but no performance_obligation_id."""

    name = "revenue_missing_obligation_linkage"
    target_test_key = "missing_obligation_linkage"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add contract columns to all existing rows (properly linked)
        for r in rows:
            r["Contract ID"] = r.get("Reference", "C-DEFAULT")
            r["Performance Obligation ID"] = f"PO-{r.get('Reference', 'X')}"

        # Inject entry with contract but missing PO linkage
        rows.append(
            {
                "Date": "2025-06-11",
                "Amount": 14567.80,
                "Account Name": "License Revenue",
                "Account Number": "4200",
                "Description": "Invoice MCG-1250 - License revenue without PO mapping",
                "Entry Type": "system",
                "Reference": "INV-1250",
                "Contract ID": "C-2025-055",
                "Performance Obligation ID": "",  # Missing linkage
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_missing_obligation_linkage",
            report_targets=["RT-14"],
            injected_at="Entry with Contract ID 'C-2025-055' but empty Performance Obligation ID",
            expected_field="missing_obligation_linkage",
            expected_condition="entries_flagged > 0",
            metadata={"contract_id": "C-2025-055"},
        )
        return rows, [record]


class RevenueModificationTreatmentMismatchGenerator(RevenueGeneratorBase):
    """RT-15: Inject inconsistent contract modification treatment within a contract."""

    name = "revenue_modification_treatment_mismatch"
    target_test_key = "modification_treatment_mismatch"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add contract + modification columns to all existing rows
        for r in rows:
            r["Contract ID"] = r.get("Reference", "C-DEFAULT")
            r["Contract Modification"] = ""  # No modifications for baseline

        # Add two entries for the same contract with different modification treatments
        rows.extend(
            [
                {
                    "Date": "2025-05-13",
                    "Amount": 11234.60,
                    "Account Name": "Service Revenue",
                    "Account Number": "4000",
                    "Description": "Invoice MCG-1260 - Contract modification cumulative",
                    "Entry Type": "system",
                    "Reference": "INV-1260",
                    "Contract ID": "C-2025-070",
                    "Contract Modification": "cumulative catch-up",
                },
                {
                    "Date": "2025-05-27",
                    "Amount": 8765.40,
                    "Account Name": "Service Revenue",
                    "Account Number": "4000",
                    "Description": "Invoice MCG-1261 - Contract modification prospective",
                    "Entry Type": "system",
                    "Reference": "INV-1261",
                    "Contract ID": "C-2025-070",
                    "Contract Modification": "prospective",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="revenue_modification_treatment_mismatch",
            report_targets=["RT-15"],
            injected_at="Contract C-2025-070 with mixed modification treatments (cumulative + prospective)",
            expected_field="modification_treatment_mismatch",
            expected_condition="entries_flagged > 0",
            metadata={"contract_id": "C-2025-070", "treatments": ["cumulative catch-up", "prospective"]},
        )
        return rows, [record]


class RevenueAllocationInconsistencyGenerator(RevenueGeneratorBase):
    """RT-16: Inject inconsistent SSP allocation bases within a contract."""

    name = "revenue_allocation_inconsistency"
    target_test_key = "allocation_inconsistency"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add contract + allocation columns to all existing rows
        for r in rows:
            r["Contract ID"] = r.get("Reference", "C-DEFAULT")
            r["Allocation Basis"] = "observable SSP"

        # Add entries for the same contract with different allocation bases
        rows.extend(
            [
                {
                    "Date": "2025-06-04",
                    "Amount": 9876.50,
                    "Account Name": "License Revenue",
                    "Account Number": "4200",
                    "Description": "Invoice MCG-1270 - License component observable SSP",
                    "Entry Type": "system",
                    "Reference": "INV-1270",
                    "Contract ID": "C-2025-085",
                    "Allocation Basis": "observable SSP",
                },
                {
                    "Date": "2025-06-09",
                    "Amount": 5432.10,
                    "Account Name": "Service Revenue",
                    "Account Number": "4000",
                    "Description": "Invoice MCG-1271 - Service component residual approach",
                    "Entry Type": "system",
                    "Reference": "INV-1271",
                    "Contract ID": "C-2025-085",
                    "Allocation Basis": "residual approach",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="revenue_allocation_inconsistency",
            report_targets=["RT-16"],
            injected_at="Contract C-2025-085 with mixed allocation bases (observable SSP + residual approach)",
            expected_field="allocation_inconsistency",
            expected_condition="entries_flagged > 0",
            metadata={"contract_id": "C-2025-085", "bases": ["observable SSP", "residual approach"]},
        )
        return rows, [record]


# =============================================================================
# Generators requiring large populations (excluded from default registry)
# =============================================================================


class RevenueZScoreOutlierGenerator(RevenueGeneratorBase):
    """RT-06: Inject a statistical outlier. Needs 10+ entries per account for z-score."""

    name = "revenue_zscore_outlier"
    target_test_key = "zscore_outliers"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add several normal entries to build up the account population
        normal_amounts = [5234.50, 4876.30, 5123.75, 5432.10, 4987.65, 5345.20, 5098.40, 4765.90]
        for i, amt in enumerate(normal_amounts):
            rows.append(
                {
                    "Date": f"2025-04-{7 + i:02d}",
                    "Amount": amt,
                    "Account Name": "Consulting Revenue",
                    "Account Number": "4100",
                    "Description": f"Invoice MCG-13{i:02d} - Standard consulting engagement",
                    "Entry Type": "system",
                    "Reference": f"INV-13{i:02d}",
                }
            )
        # Inject outlier at 10x normal
        rows.append(
            {
                "Date": "2025-05-22",
                "Amount": 52345.00,
                "Account Name": "Consulting Revenue",
                "Account Number": "4100",
                "Description": "Invoice MCG-1399 - Unusually large consulting fee",
                "Entry Type": "system",
                "Reference": "INV-1399",
            }
        )
        record = AnomalyRecord(
            anomaly_type="revenue_zscore_outlier",
            report_targets=["RT-06"],
            injected_at="Consulting Revenue entry $52,345.00 (10x normal ~$5,100 range)",
            expected_field="zscore_outliers",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 52345.00, "normal_mean": 5107.98},
        )
        return rows, [record]


class RevenueTrendVarianceGenerator(RevenueGeneratorBase):
    """RT-07: Inject data that triggers trend variance. Requires prior_period_total config."""

    name = "revenue_trend_variance"
    target_test_key = "trend_variance"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # This test compares current total to config.prior_period_total.
        # We cannot inject the config, so we add large entries to inflate total.
        # The test runner should set prior_period_total to a low value.
        rows.extend(
            [
                {
                    "Date": "2025-04-17",
                    "Amount": 95432.10,
                    "Account Name": "Service Revenue",
                    "Account Number": "4000",
                    "Description": "Invoice MCG-1400 - Major engagement surplus",
                    "Entry Type": "system",
                    "Reference": "INV-1400",
                },
                {
                    "Date": "2025-05-06",
                    "Amount": 87654.30,
                    "Account Name": "Consulting Revenue",
                    "Account Number": "4100",
                    "Description": "Invoice MCG-1401 - Unexpected project expansion",
                    "Entry Type": "system",
                    "Reference": "INV-1401",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="revenue_trend_variance",
            report_targets=["RT-07"],
            injected_at="$183,086.40 added to inflate total revenue vs prior period",
            expected_field="trend_variance",
            expected_condition="entries_flagged > 0",
            metadata={"added_total": 183086.40, "note": "Requires prior_period_total config"},
        )
        return rows, [record]


class RevenueBenfordLawGenerator(RevenueGeneratorBase):
    """RT-10: Inject entries that violate Benford's Law. Needs 50+ entries."""

    name = "revenue_benford_law"
    target_test_key = "benford_law"
    requires_large_population = True

    def inject(self, rows, seed=42):
        import random

        rows = deepcopy(rows)
        rng = random.Random(seed)
        accounts = [
            ("Service Revenue", "4000"),
            ("Consulting Revenue", "4100"),
            ("License Revenue", "4200"),
            ("Subscription Revenue", "4500"),
        ]
        # Generate 50 entries all starting with digit 5 (Benford expects ~7.9%)
        weekdays_2025_q2 = (
            [f"2025-04-{d:02d}" for d in range(1, 31) if __import__("datetime").date(2025, 4, d).weekday() < 5]
            + [f"2025-05-{d:02d}" for d in range(1, 32) if __import__("datetime").date(2025, 5, d).weekday() < 5]
            + [f"2025-06-{d:02d}" for d in range(1, 31) if __import__("datetime").date(2025, 6, d).weekday() < 5]
        )
        for i in range(50):
            acct_name, acct_num = rng.choice(accounts)
            dt = rng.choice(weekdays_2025_q2)
            # Force leading digit = 5
            amt = round(rng.uniform(5000.01, 5999.99), 2)
            rows.append(
                {
                    "Date": dt,
                    "Amount": amt,
                    "Account Name": acct_name,
                    "Account Number": acct_num,
                    "Description": f"Invoice MCG-B{i:03d} - Synthetic Benford test entry",
                    "Entry Type": "system",
                    "Reference": f"BEN-{i:03d}",
                }
            )
        record = AnomalyRecord(
            anomaly_type="revenue_benford_law",
            report_targets=["RT-10"],
            injected_at="50 entries with leading digit 5 (expected ~7.9%, observed ~71%)",
            expected_field="benford_law",
            expected_condition="entries_flagged > 0",
            metadata={"injected_count": 50, "forced_leading_digit": 5},
        )
        return rows, [record]


# =============================================================================
# Registry of all Revenue generators
# =============================================================================

REVENUE_REGISTRY: list[RevenueGeneratorBase] = [
    # Tier 1 -- Structural
    RevenueLargeManualEntryGenerator(),
    RevenueYearEndConcentrationGenerator(),
    RevenueRoundAmountGenerator(),
    RevenueSignAnomalyGenerator(),
    RevenueUnclassifiedEntryGenerator(),
    # Tier 2 -- Statistical (small-population-safe)
    RevenueConcentrationRiskGenerator(),
    RevenueCutoffRiskGenerator(),
    # Tier 3 -- Advanced
    RevenueDuplicateEntryGenerator(),
    RevenueContraAnomalyGenerator(),
    # Tier 4 -- Contract-aware (ASC 606)
    RevenueRecognitionBeforeSatisfactionGenerator(),
    RevenueMissingObligationLinkageGenerator(),
    RevenueModificationTreatmentMismatchGenerator(),
    RevenueAllocationInconsistencyGenerator(),
    # Large-population generators
    RevenueZScoreOutlierGenerator(),
    RevenueTrendVarianceGenerator(),
    RevenueBenfordLawGenerator(),
]

# Small-population-safe generators (work with 20-entry baseline)
REVENUE_REGISTRY_SMALL = [g for g in REVENUE_REGISTRY if not g.requires_large_population]
