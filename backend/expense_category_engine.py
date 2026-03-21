"""
Paciolus — Expense Category Analytical Procedures Engine
Sprint 289: Phase XXXIX

ISA 520-compliant expense category decomposition for Trial Balance diagnostics.
Decomposes total expenses into 5 sub-categories (COGS, Payroll, Depreciation/Amortization,
Interest/Tax, Other Operating), computes ratios-to-revenue, and optionally compares
to prior period aggregates.

Keyword priority: COGS > Payroll > Depreciation > Interest/Tax > Other Operating
Prior comparison is aggregate-only (COGS, OpEx, Total from DiagnosticSummary).

Guardrail: raw metrics only — no evaluative language.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from column_detector import detect_columns
from ratio_engine import COGS_KEYWORDS
from shared.parsing_helpers import safe_decimal

# ═══════════════════════════════════════════════════════════════
# Sub-category keyword lists
# ═══════════════════════════════════════════════════════════════

PAYROLL_KEYWORDS = [
    "salary",
    "salaries",
    "wage",
    "wages",
    "payroll",
    "bonus",
    "bonuses",
    "commission",
    "commissions",
    "employee benefit",
    "staff cost",
    "staff expense",
    "pension",
    "retirement",
    "compensation",
]

DEPRECIATION_KEYWORDS = [
    "depreciation",
    "amortization",
    "amortisation",
    "depletion",
    "writedown",
    "write-down",
    "impairment",
]

INTEREST_TAX_KEYWORDS = [
    "interest expense",
    "interest payment",
    "finance cost",
    "tax",
    "income tax",
    "tax expense",
    "tax provision",
    "withholding",
    "vat expense",
    "sales tax expense",
]

# Category keys (used for dict lookups and serialization)
CAT_COGS = "cogs"
CAT_PAYROLL = "payroll"
CAT_DEPRECIATION = "depreciation_amortization"
CAT_INTEREST_TAX = "interest_tax"
CAT_OTHER_OPERATING = "other_operating"

CATEGORY_LABELS = {
    CAT_COGS: "Cost of Goods Sold",
    CAT_PAYROLL: "Payroll & Employee Costs",
    CAT_DEPRECIATION: "Depreciation & Amortization",
    CAT_INTEREST_TAX: "Interest & Tax",
    CAT_OTHER_OPERATING: "Other Operating Expenses",
}

CATEGORY_ORDER = [CAT_COGS, CAT_PAYROLL, CAT_DEPRECIATION, CAT_INTEREST_TAX, CAT_OTHER_OPERATING]

NEAR_ZERO = 1e-10


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════


@dataclass
class ExpenseCategory:
    """One row in the expense category breakdown."""

    label: str
    key: str
    amount: Decimal
    pct_of_revenue: Optional[Decimal]
    prior_amount: Optional[float] = None
    prior_pct_of_revenue: Optional[float] = None
    dollar_change: Optional[Decimal] = None
    exceeds_threshold: bool = False
    benchmark_pct: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "key": self.key,
            "amount": round(self.amount, 2),
            "pct_of_revenue": round(self.pct_of_revenue, 4) if self.pct_of_revenue is not None else None,
            "prior_amount": round(self.prior_amount, 2) if self.prior_amount is not None else None,
            "prior_pct_of_revenue": round(self.prior_pct_of_revenue, 4)
            if self.prior_pct_of_revenue is not None
            else None,
            "dollar_change": round(self.dollar_change, 2) if self.dollar_change is not None else None,
            "exceeds_threshold": self.exceeds_threshold,
            "benchmark_pct": round(self.benchmark_pct, 4) if self.benchmark_pct is not None else None,
        }


@dataclass
class ExpenseCategoryReport:
    """Complete expense category analytical result."""

    categories: list[ExpenseCategory] = field(default_factory=list)
    total_expenses: Decimal = field(default_factory=lambda: Decimal("0"))
    total_revenue: float = 0.0
    revenue_available: bool = False
    prior_available: bool = False
    materiality_threshold: float = 0.0
    category_count: int = 0

    def to_dict(self) -> dict:
        return {
            "categories": [c.to_dict() for c in self.categories],
            "total_expenses": round(self.total_expenses, 2),
            "total_revenue": round(self.total_revenue, 2),
            "revenue_available": self.revenue_available,
            "prior_available": self.prior_available,
            "materiality_threshold": round(self.materiality_threshold, 2),
            "category_count": self.category_count,
        }


# ═══════════════════════════════════════════════════════════════
# Sub-category classifier
# ═══════════════════════════════════════════════════════════════


def _classify_expense_subcategory(account_name: str) -> Optional[str]:
    """Classify an expense account into one of the 5 sub-categories.

    Priority order: COGS > Payroll > Depreciation > Interest/Tax > Other Operating.
    Returns None for non-expense accounts (those should be filtered upstream).
    """
    name_lower = account_name.lower()

    # Priority 1: COGS
    if any(kw in name_lower for kw in COGS_KEYWORDS):
        return CAT_COGS

    # Priority 2: Payroll
    if any(kw in name_lower for kw in PAYROLL_KEYWORDS):
        return CAT_PAYROLL

    # Priority 3: Depreciation / Amortization
    if any(kw in name_lower for kw in DEPRECIATION_KEYWORDS):
        return CAT_DEPRECIATION

    # Priority 4: Interest / Tax
    if any(kw in name_lower for kw in INTEREST_TAX_KEYWORDS):
        return CAT_INTEREST_TAX

    # No keyword match — will be classified as Other Operating by caller
    return None


# ═══════════════════════════════════════════════════════════════
# Core computation
# ═══════════════════════════════════════════════════════════════


def compute_expense_categories(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: dict[str, str],
    total_revenue: float,
    materiality_threshold: float = 0.0,
    prior_cogs: Optional[float] = None,
    prior_opex: Optional[float] = None,
    prior_total_expenses: Optional[float] = None,
    prior_revenue: Optional[float] = None,
) -> ExpenseCategoryReport:
    """Compute expense category breakdown from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: {account_name: category_string} from classifier
        total_revenue: Total revenue from category_totals
        materiality_threshold: Dollar threshold for flagging
        prior_cogs: Prior period COGS (aggregate from DiagnosticSummary)
        prior_opex: Prior period operating expenses (aggregate)
        prior_total_expenses: Prior period total expenses (aggregate)
        prior_revenue: Prior period revenue (for ratio comparison)

    Returns:
        ExpenseCategoryReport with 5 sub-categories.
    """
    if not account_balances:
        return ExpenseCategoryReport()

    # Convert float parameters to Decimal for consistent arithmetic
    total_revenue_dec = safe_decimal(total_revenue) if total_revenue is not None else Decimal("0")
    materiality_threshold_dec = safe_decimal(materiality_threshold)

    # Accumulate amounts by sub-category
    category_amounts: dict[str, Decimal] = {k: Decimal("0") for k in CATEGORY_ORDER}
    expense_types = {"expense"}

    for acct_name, bals in account_balances.items():
        classification = classified_accounts.get(acct_name, "").lower()
        if classification not in expense_types:
            continue

        # Net balance (expenses are typically debit-heavy)
        net = safe_decimal(bals["debit"]) - safe_decimal(bals["credit"])
        if abs(net) < NEAR_ZERO:
            continue

        subcategory = _classify_expense_subcategory(acct_name)
        if subcategory is None:
            subcategory = CAT_OTHER_OPERATING

        category_amounts[subcategory] += net

    total_expenses = sum(category_amounts.values(), Decimal("0"))
    revenue_available = abs(total_revenue_dec) > NEAR_ZERO
    prior_available = prior_total_expenses is not None

    # Build category objects
    categories: list[ExpenseCategory] = []
    for key in CATEGORY_ORDER:
        amount = category_amounts[key]
        pct_of_revenue = amount / total_revenue_dec * 100 if revenue_available else None

        cat = ExpenseCategory(
            label=CATEGORY_LABELS[key],
            key=key,
            amount=amount,
            pct_of_revenue=pct_of_revenue,
        )

        # Prior comparison (aggregate-only)
        if prior_available:
            prior_amt = _get_prior_for_category(
                key,
                prior_cogs,
                prior_opex,
                prior_total_expenses,
            )
            if prior_amt is not None:
                prior_dec = safe_decimal(prior_amt)
                cat.prior_amount = prior_amt
                if prior_revenue is not None and abs(prior_revenue) > NEAR_ZERO:
                    cat.prior_pct_of_revenue = prior_amt / prior_revenue * 100
                cat.dollar_change = amount - prior_dec
                cat.exceeds_threshold = abs(amount - prior_dec) > materiality_threshold_dec

        categories.append(cat)

    return ExpenseCategoryReport(
        categories=categories,
        total_expenses=total_expenses,
        total_revenue=total_revenue,
        revenue_available=revenue_available,
        prior_available=prior_available,
        materiality_threshold=materiality_threshold,
        category_count=len([c for c in categories if abs(c.amount) > NEAR_ZERO]),
    )


def _get_prior_for_category(
    key: str,
    prior_cogs: Optional[float],
    prior_opex: Optional[float],
    prior_total_expenses: Optional[float],
) -> Optional[float]:
    """Map a sub-category key to its aggregate prior-period value.

    Prior data only has COGS and OpEx breakdowns. Sub-categories within
    OpEx (payroll, depreciation, interest/tax, other) cannot be individually
    compared — only the COGS aggregate maps directly.
    """
    if key == CAT_COGS:
        return prior_cogs
    # All other sub-categories fall under OpEx aggregate — no individual prior
    return None


# ═══════════════════════════════════════════════════════════════
# Standalone entry point (for /audit/expense-category-analytics)
# ═══════════════════════════════════════════════════════════════


def run_expense_category_analytics(
    column_names: list[str],
    rows: list[dict],
    filename: str,
    materiality_threshold: float = 0.0,
    prior_cogs: Optional[float] = None,
    prior_opex: Optional[float] = None,
    prior_total_expenses: Optional[float] = None,
    prior_revenue: Optional[float] = None,
) -> ExpenseCategoryReport:
    """Run expense category analytics from raw parsed file data.

    Uses column_detector.detect_columns() to find account/debit/credit
    columns, accumulates per-account balances, then classifies and computes.
    """
    from account_classifier import create_classifier

    detection = detect_columns(column_names)
    account_col = detection.account_column
    debit_col = detection.debit_column
    credit_col = detection.credit_column

    if not account_col or not debit_col or not credit_col:
        return ExpenseCategoryReport()

    # Accumulate per-account balances
    account_balances: dict[str, dict[str, float]] = {}
    for row in rows:
        acct = row.get(account_col)
        if acct is None:
            continue
        acct_str = str(acct).strip()
        if not acct_str:
            continue

        debit = safe_decimal(row.get(debit_col))
        credit = safe_decimal(row.get(credit_col))

        if acct_str not in account_balances:
            account_balances[acct_str] = {"debit": 0.0, "credit": 0.0}
        account_balances[acct_str]["debit"] += float(debit)
        account_balances[acct_str]["credit"] += float(credit)

    # Classify accounts
    classifier = create_classifier()
    classified_accounts: dict[str, str] = {}
    total_revenue_acc = 0.0
    for acct_name, bals in account_balances.items():
        net = bals["debit"] - bals["credit"]
        cls_result = classifier.classify(acct_name, net)
        classified_accounts[acct_name] = cls_result.category.value
        if cls_result.category.value.lower() == "revenue":
            total_revenue_acc += abs(net)

    return compute_expense_categories(
        account_balances,
        classified_accounts,
        total_revenue_acc,
        materiality_threshold,
        prior_cogs=prior_cogs,
        prior_opex=prior_opex,
        prior_total_expenses=prior_total_expenses,
        prior_revenue=prior_revenue,
    )
