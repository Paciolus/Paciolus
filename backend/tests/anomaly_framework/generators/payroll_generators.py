"""Payroll Testing anomaly generators — 11 detectors.

Each generator injects a specific anomaly pattern into clean payroll register
data and returns an AnomalyRecord describing the expected detection.

Generators that require large populations (500+ entries) are marked with
`requires_large_population = True` and are excluded from the small registry.

Uses Meridian Capital Group employee data conventions.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class PayrollGeneratorBase:
    """Base class for Payroll anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject(self, rows: list[dict], seed: int = 42) -> tuple[list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


# =============================================================================
# Tier 1: Structural Tests (PR-T1 through PR-T5)
# =============================================================================


class PayrollDuplicateEmployeeIDsGenerator(PayrollGeneratorBase):
    """PR-T1: Inject duplicate Employee IDs with different names."""

    name = "duplicate_employee_ids"
    target_test_key = "PR-T1"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add two entries with the same employee ID but different names
        rows.extend(
            [
                {
                    "Employee ID": "EMP-101",
                    "Employee Name": "Margarita Chen-Lopez",
                    "Department": "Accounting",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 4231.75,
                    "Net Pay": 2954.22,
                    "Tax ID": "***-**-9901",
                    "Address": "2200 River Road, Glastonbury, CT 06033",
                    "Bank Account": "****1122",
                    "Check Number": "5016",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="duplicate_employee_ids",
            report_targets=["PR-T1"],
            injected_at="Employee ID EMP-101 used with two different names",
            expected_field="PR-T1",
            expected_condition="entries_flagged > 0",
            metadata={
                "duplicate_id": "EMP-101",
                "original_name": "Margaret Chen",
                "injected_name": "Margarita Chen-Lopez",
            },
        )
        return rows, [record]


class PayrollDuplicateNamesGenerator(PayrollGeneratorBase):
    """PR-T2: Inject duplicate Employee Names (different IDs, same name)."""

    name = "duplicate_names"
    target_test_key = "PR-T2"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add an entry with a name matching an existing employee but different ID
        rows.extend(
            [
                {
                    "Employee ID": "EMP-201",
                    "Employee Name": "David Kowalski",
                    "Department": "Operations",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 5847.50,
                    "Net Pay": 4093.25,
                    "Tax ID": "***-**-8802",
                    "Address": "445 Ash Street, Bristol, CT 06010",
                    "Bank Account": "****2233",
                    "Check Number": "5016",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="duplicate_names",
            report_targets=["PR-T2"],
            injected_at="Employee Name 'David Kowalski' appears under EMP-102 and EMP-201",
            expected_field="PR-T2",
            expected_condition="entries_flagged > 0",
            metadata={"duplicate_name": "David Kowalski", "employee_ids": ["EMP-102", "EMP-201"]},
        )
        return rows, [record]


class PayrollRoundSalaryAmountsGenerator(PayrollGeneratorBase):
    """PR-T3: Inject round gross pay amounts >= $10,000."""

    name = "round_salary_amounts"
    target_test_key = "PR-T3"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.extend(
            [
                {
                    "Employee ID": "EMP-202",
                    "Employee Name": "Gerald Thornton",
                    "Department": "Executive",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 20000.00,
                    "Net Pay": 13800.00,
                    "Tax ID": "***-**-5503",
                    "Address": "12 Presidential Lane, Avon, CT 06001",
                    "Bank Account": "****3344",
                    "Check Number": "5016",
                },
                {
                    "Employee ID": "EMP-203",
                    "Employee Name": "Diane Prescott",
                    "Department": "Executive",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 50000.00,
                    "Net Pay": 34500.00,
                    "Tax ID": "***-**-7704",
                    "Address": "800 Ridgewood Avenue, West Hartford, CT 06119",
                    "Bank Account": "****4455",
                    "Check Number": "5017",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="round_salary_amounts",
            report_targets=["PR-T3"],
            injected_at="Two employees with round gross pay ($20,000 and $50,000)",
            expected_field="PR-T3",
            expected_condition="entries_flagged > 0",
            metadata={"amounts": [20000.00, 50000.00]},
        )
        return rows, [record]


class PayrollPayAfterTerminationGenerator(PayrollGeneratorBase):
    """PR-T4: Inject payment after termination date."""

    name = "pay_after_termination"
    target_test_key = "PR-T4"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add an employee with a termination date before their pay date
        rows.extend(
            [
                {
                    "Employee ID": "EMP-204",
                    "Employee Name": "Walter Simmons",
                    "Department": "Sales",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 4875.42,
                    "Net Pay": 3412.79,
                    "Tax ID": "***-**-6605",
                    "Address": "1033 Poplar Drive, Enfield, CT 06082",
                    "Bank Account": "****5566",
                    "Check Number": "5016",
                    "Termination Date": "2025-05-15",
                },
            ]
        )
        # Add Termination Date column to all existing rows (empty = active)
        for r in rows:
            if "Termination Date" not in r:
                r["Termination Date"] = ""
        record = AnomalyRecord(
            anomaly_type="pay_after_termination",
            report_targets=["PR-T4"],
            injected_at="Employee EMP-204 (Walter Simmons) paid 2025-06-20 after termination 2025-05-15",
            expected_field="PR-T4",
            expected_condition="entries_flagged > 0",
            metadata={"employee_id": "EMP-204", "term_date": "2025-05-15", "pay_date": "2025-06-20"},
        )
        return rows, [record]


class PayrollCheckNumberGapsGenerator(PayrollGeneratorBase):
    """PR-T5: Inject gaps in check number sequence."""

    name = "check_number_gaps"
    target_test_key = "PR-T5"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add entries with check numbers that create a gap (5015 -> 5020, missing 5016-5019)
        rows.extend(
            [
                {
                    "Employee ID": "EMP-205",
                    "Employee Name": "Patricia Hoffman",
                    "Department": "Legal",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 5234.67,
                    "Net Pay": 3664.27,
                    "Tax ID": "***-**-8806",
                    "Address": "279 Sycamore Boulevard, Canton, CT 06019",
                    "Bank Account": "****6677",
                    "Check Number": "5020",
                },
                {
                    "Employee ID": "EMP-206",
                    "Employee Name": "Richard Yamamoto",
                    "Department": "Engineering",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 6178.33,
                    "Net Pay": 4324.83,
                    "Tax ID": "***-**-1107",
                    "Address": "563 Dogwood Circle, Vernon, CT 06066",
                    "Bank Account": "****7788",
                    "Check Number": "5021",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="check_number_gaps",
            report_targets=["PR-T5"],
            injected_at="Check number gap: 5015 -> 5020 (missing 5016-5019)",
            expected_field="PR-T5",
            expected_condition="entries_flagged > 0",
            metadata={"gap_start": 5015, "gap_end": 5020, "missing_count": 4},
        )
        return rows, [record]


# =============================================================================
# Tier 2: Statistical Tests (PR-T6 through PR-T8)
# =============================================================================


class PayrollUnusualPayAmountsGenerator(PayrollGeneratorBase):
    """PR-T6: Inject z-score outlier gross pay. Requires large population."""

    name = "unusual_pay_amounts"
    target_test_key = "PR-T6"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        import random

        rng = random.Random(seed)
        # Build a population of normal-range entries in the same department
        for i in range(20):
            rows.append(
                {
                    "Employee ID": f"EMP-3{i:02d}",
                    "Employee Name": f"Staff Member {i + 1}",
                    "Department": "Operations",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": round(3500 + rng.gauss(0, 200), 2),
                    "Net Pay": round(2450 + rng.gauss(0, 140), 2),
                    "Tax ID": f"***-**-{9100 + i}",
                    "Address": f"{100 + i} Test Ave, Hartford, CT 06{100 + i}",
                    "Bank Account": f"****{9100 + i}",
                    "Check Number": str(5016 + i),
                }
            )
        # Inject an extreme outlier (10x normal)
        rows.append(
            {
                "Employee ID": "EMP-399",
                "Employee Name": "Outlier Employee",
                "Department": "Operations",
                "Pay Date": "2025-06-20",
                "Gross Pay": 35000.50,
                "Net Pay": 24500.35,
                "Tax ID": "***-**-9999",
                "Address": "999 Outlier Road, Hartford, CT 06199",
                "Bank Account": "****9999",
                "Check Number": "5036",
            }
        )
        record = AnomalyRecord(
            anomaly_type="unusual_pay_amounts",
            report_targets=["PR-T6"],
            injected_at="Employee EMP-399 with $35,000.50 gross pay (10x department average)",
            expected_field="PR-T6",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 35000.50, "expected_range": "~$3,500"},
        )
        return rows, [record]


class PayrollPayFrequencyAnomaliesGenerator(PayrollGeneratorBase):
    """PR-T7: Inject irregular pay dates for an employee. Requires large population."""

    name = "pay_frequency_anomalies"
    target_test_key = "PR-T7"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Create a series of regular bi-weekly pays for one employee, then an irregular one
        regular_dates = [
            "2025-01-10",
            "2025-01-24",
            "2025-02-07",
            "2025-02-21",
            "2025-03-07",
            "2025-03-21",
            "2025-04-04",
            "2025-04-18",
            "2025-05-02",
            "2025-05-16",
            "2025-05-30",
        ]
        for i, dt in enumerate(regular_dates):
            rows.append(
                {
                    "Employee ID": "EMP-401",
                    "Employee Name": "Frequency Test Employee",
                    "Department": "Accounting",
                    "Pay Date": dt,
                    "Gross Pay": 4100.25,
                    "Net Pay": 2870.18,
                    "Tax ID": "***-**-4401",
                    "Address": "100 Frequency Lane, Hartford, CT 06101",
                    "Bank Account": "****4401",
                    "Check Number": str(6001 + i),
                }
            )
        # Inject an off-cycle payment (only 5 days after last regular pay)
        rows.append(
            {
                "Employee ID": "EMP-401",
                "Employee Name": "Frequency Test Employee",
                "Department": "Accounting",
                "Pay Date": "2025-06-04",
                "Gross Pay": 4100.25,
                "Net Pay": 2870.18,
                "Tax ID": "***-**-4401",
                "Address": "100 Frequency Lane, Hartford, CT 06101",
                "Bank Account": "****4401",
                "Check Number": "6012",
            }
        )
        record = AnomalyRecord(
            anomaly_type="pay_frequency_anomalies",
            report_targets=["PR-T7"],
            injected_at="Employee EMP-401 paid 5 days after prior cycle (expected 14-day cadence)",
            expected_field="PR-T7",
            expected_condition="entries_flagged > 0",
            metadata={"employee_id": "EMP-401", "irregular_date": "2025-06-04", "prior_date": "2025-05-30"},
        )
        return rows, [record]


class PayrollBenfordAnalysisGenerator(PayrollGeneratorBase):
    """PR-T8: Inject Benford's law violation on gross pay. Requires large population."""

    name = "benford_analysis"
    target_test_key = "PR-T8"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        import random

        rng = random.Random(seed)
        # Inject 500+ entries all starting with digit 9 (Benford expects ~4.6%)
        for i in range(520):
            gross = round(rng.uniform(9000, 9999), 2)
            net = round(gross * 0.70, 2)
            rows.append(
                {
                    "Employee ID": f"EMP-5{i:03d}",
                    "Employee Name": f"Benford Employee {i + 1}",
                    "Department": rng.choice(["Sales", "Engineering", "Operations", "Marketing"]),
                    "Pay Date": f"2025-06-{(i % 20) + 1:02d}" if (i % 20) + 1 <= 28 else "2025-06-20",
                    "Gross Pay": gross,
                    "Net Pay": net,
                    "Tax ID": f"***-**-{1000 + i}",
                    "Address": f"{1000 + i} Benford St, Hartford, CT 06{100 + i % 100}",
                    "Bank Account": f"****{1000 + i}",
                    "Check Number": str(7001 + i),
                }
            )
        record = AnomalyRecord(
            anomaly_type="benford_analysis",
            report_targets=["PR-T8"],
            injected_at="520 entries with gross pay starting with digit 9 (expected ~4.6%, actual ~97%)",
            expected_field="PR-T8",
            expected_condition="entries_flagged > 0",
            metadata={"injected_count": 520, "leading_digit": 9, "expected_benford_pct": 4.6},
        )
        return rows, [record]


# =============================================================================
# Tier 3: Advanced / Fraud Indicators (PR-T9 through PR-T11)
# =============================================================================


class PayrollGhostEmployeeIndicatorsGenerator(PayrollGeneratorBase):
    """PR-T9: Inject ghost employee patterns (missing address, no department, single entry)."""

    name = "ghost_employee_indicators"
    target_test_key = "PR-T9"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Ghost employee: no department, single pay entry, suspicious pattern
        rows.extend(
            [
                {
                    "Employee ID": "EMP-207",
                    "Employee Name": "J. Smith",
                    "Department": "",
                    "Pay Date": "2025-06-06",
                    "Gross Pay": 4500.00,
                    "Net Pay": 3150.00,
                    "Tax ID": "",
                    "Address": "",
                    "Bank Account": "****8899",
                    "Check Number": "5016",
                },
            ]
        )
        record = AnomalyRecord(
            anomaly_type="ghost_employee_indicators",
            report_targets=["PR-T9"],
            injected_at="Employee EMP-207 (J. Smith): no department, no tax ID, no address, single entry",
            expected_field="PR-T9",
            expected_condition="entries_flagged > 0",
            metadata={
                "employee_id": "EMP-207",
                "indicators": ["No department assignment", "Single pay entry in period"],
            },
        )
        return rows, [record]


class PayrollDuplicateBankAccountsGenerator(PayrollGeneratorBase):
    """PR-T10: Inject same bank account on different employees."""

    name = "duplicate_bank_accounts"
    target_test_key = "PR-T10"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Two different employees sharing the same bank account
        rows.extend(
            [
                {
                    "Employee ID": "EMP-208",
                    "Employee Name": "Victor Hernandez",
                    "Department": "Marketing",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 4312.58,
                    "Net Pay": 3018.81,
                    "Tax ID": "***-**-3308",
                    "Address": "721 Hemlock Drive, Tolland, CT 06084",
                    "Bank Account": "****7291",
                    "Check Number": "5016",
                },
            ]
        )
        # ****7291 matches Margaret Chen (EMP-101)
        record = AnomalyRecord(
            anomaly_type="duplicate_bank_accounts",
            report_targets=["PR-T10"],
            injected_at="Bank account ****7291 shared between EMP-101 (Margaret Chen) and EMP-208 (Victor Hernandez)",
            expected_field="PR-T10",
            expected_condition="entries_flagged > 0",
            metadata={
                "bank_account": "****7291",
                "employees": ["EMP-101 (Margaret Chen)", "EMP-208 (Victor Hernandez)"],
            },
        )
        return rows, [record]


class PayrollDuplicateTaxIDsGenerator(PayrollGeneratorBase):
    """PR-T11: Inject same Tax ID on different employees."""

    name = "duplicate_tax_ids"
    target_test_key = "PR-T11"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Two different employees sharing the same tax ID
        rows.extend(
            [
                {
                    "Employee ID": "EMP-209",
                    "Employee Name": "Christine Park",
                    "Department": "IT",
                    "Pay Date": "2025-06-20",
                    "Gross Pay": 5678.91,
                    "Net Pay": 3975.24,
                    "Tax ID": "***-**-4821",
                    "Address": "339 Juniper Court, Ellington, CT 06029",
                    "Bank Account": "****1199",
                    "Check Number": "5016",
                },
            ]
        )
        # ***-**-4821 matches Margaret Chen (EMP-101)
        record = AnomalyRecord(
            anomaly_type="duplicate_tax_ids",
            report_targets=["PR-T11"],
            injected_at="Tax ID ***-**-4821 shared between EMP-101 (Margaret Chen) and EMP-209 (Christine Park)",
            expected_field="PR-T11",
            expected_condition="entries_flagged > 0",
            metadata={
                "tax_id": "***-**-4821",
                "employees": ["EMP-101 (Margaret Chen)", "EMP-209 (Christine Park)"],
            },
        )
        return rows, [record]


# =============================================================================
# Registries
# =============================================================================

PAYROLL_REGISTRY: list[PayrollGeneratorBase] = [
    # Tier 1: Structural
    PayrollDuplicateEmployeeIDsGenerator(),
    PayrollDuplicateNamesGenerator(),
    PayrollRoundSalaryAmountsGenerator(),
    PayrollPayAfterTerminationGenerator(),
    PayrollCheckNumberGapsGenerator(),
    # Tier 2: Statistical
    PayrollUnusualPayAmountsGenerator(),
    PayrollPayFrequencyAnomaliesGenerator(),
    PayrollBenfordAnalysisGenerator(),
    # Tier 3: Advanced
    PayrollGhostEmployeeIndicatorsGenerator(),
    PayrollDuplicateBankAccountsGenerator(),
    PayrollDuplicateTaxIDsGenerator(),
]

# Small-population-safe generators (work with 15-entry baseline)
PAYROLL_REGISTRY_SMALL = [g for g in PAYROLL_REGISTRY if not g.requires_large_population]
