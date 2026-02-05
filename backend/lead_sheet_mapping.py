"""
Lead Sheet Mapping Module
Sprint 50: Lead Sheet Mapping

Maps trial balance accounts to standard audit lead sheet designations.
Lead sheets are the fundamental organizational unit for audit workpapers.

Standard Lead Sheet Designations:
    A: Cash and Cash Equivalents
    B: Receivables
    C: Inventory
    D: Prepaid Expenses and Other Current Assets
    E: Property, Plant & Equipment (Fixed Assets)
    F: Other Assets / Intangibles
    G: Accounts Payable and Accrued Liabilities
    H: Other Current Liabilities
    I: Long-term Debt
    J: Other Long-term Liabilities / Deferred Items
    K: Equity / Stockholders' Equity
    L: Revenue / Sales
    M: Cost of Goods Sold
    N: Operating Expenses
    O: Other Income / Expense
    Z: Unclassified (requires manual assignment)

IFRS/GAAP Note:
    Lead sheet organization is consistent across both frameworks.
    The classification logic handles framework-specific terminology.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from classification_rules import AccountCategory
from security_utils import log_secure_operation


class LeadSheet(str, Enum):
    """
    Standard audit lead sheet designations.

    These letters follow common audit practice and map to major
    account groupings in a trial balance.
    """
    A = "A"  # Cash and Cash Equivalents
    B = "B"  # Receivables
    C = "C"  # Inventory
    D = "D"  # Prepaid Expenses and Other Current Assets
    E = "E"  # Property, Plant & Equipment
    F = "F"  # Other Assets / Intangibles
    G = "G"  # Accounts Payable and Accrued Liabilities
    H = "H"  # Other Current Liabilities
    I = "I"  # Long-term Debt
    J = "J"  # Other Long-term Liabilities / Deferred Items
    K = "K"  # Equity / Stockholders' Equity
    L = "L"  # Revenue / Sales
    M = "M"  # Cost of Goods Sold
    N = "N"  # Operating Expenses
    O = "O"  # Other Income / Expense
    Z = "Z"  # Unclassified


# Lead sheet display names for UI
LEAD_SHEET_NAMES: dict[LeadSheet, str] = {
    LeadSheet.A: "Cash and Cash Equivalents",
    LeadSheet.B: "Receivables",
    LeadSheet.C: "Inventory",
    LeadSheet.D: "Prepaid Expenses & Other Current Assets",
    LeadSheet.E: "Property, Plant & Equipment",
    LeadSheet.F: "Other Assets & Intangibles",
    LeadSheet.G: "Accounts Payable & Accrued Liabilities",
    LeadSheet.H: "Other Current Liabilities",
    LeadSheet.I: "Long-term Debt",
    LeadSheet.J: "Other Long-term Liabilities",
    LeadSheet.K: "Stockholders' Equity",
    LeadSheet.L: "Revenue",
    LeadSheet.M: "Cost of Goods Sold",
    LeadSheet.N: "Operating Expenses",
    LeadSheet.O: "Other Income & Expense",
    LeadSheet.Z: "Unclassified",
}


# Lead sheet category (for grouping in UI)
LEAD_SHEET_CATEGORY: dict[LeadSheet, str] = {
    LeadSheet.A: "Current Assets",
    LeadSheet.B: "Current Assets",
    LeadSheet.C: "Current Assets",
    LeadSheet.D: "Current Assets",
    LeadSheet.E: "Non-Current Assets",
    LeadSheet.F: "Non-Current Assets",
    LeadSheet.G: "Current Liabilities",
    LeadSheet.H: "Current Liabilities",
    LeadSheet.I: "Non-Current Liabilities",
    LeadSheet.J: "Non-Current Liabilities",
    LeadSheet.K: "Equity",
    LeadSheet.L: "Revenue",
    LeadSheet.M: "Cost of Sales",
    LeadSheet.N: "Operating Expenses",
    LeadSheet.O: "Other",
    LeadSheet.Z: "Unclassified",
}


@dataclass
class LeadSheetRule:
    """A keyword rule for lead sheet assignment."""
    keyword: str
    lead_sheet: LeadSheet
    weight: float = 1.0  # Higher weight takes precedence
    is_phrase: bool = False  # True for multi-word matches


@dataclass
class LeadSheetAssignment:
    """Result of lead sheet assignment for an account."""
    account_name: str
    lead_sheet: LeadSheet
    lead_sheet_name: str
    confidence: float
    matched_keywords: list[str] = field(default_factory=list)
    is_override: bool = False  # True if manually overridden


@dataclass
class LeadSheetSummary:
    """Summary of a single lead sheet."""
    lead_sheet: LeadSheet
    name: str
    category: str
    total_debit: float
    total_credit: float
    net_balance: float
    account_count: int
    accounts: list[dict] = field(default_factory=list)


@dataclass
class LeadSheetGrouping:
    """Complete lead sheet grouping for a trial balance."""
    summaries: list[LeadSheetSummary]
    total_debits: float
    total_credits: float
    unclassified_count: int


# =============================================================================
# LEAD SHEET ASSIGNMENT RULES
# =============================================================================

# Keywords that map accounts to specific lead sheets
# Higher weight = higher precedence when multiple matches
LEAD_SHEET_RULES: list[LeadSheetRule] = [
    # -------------------------------------------------------------------------
    # A: Cash and Cash Equivalents
    # -------------------------------------------------------------------------
    LeadSheetRule("cash", LeadSheet.A, 1.0),
    LeadSheetRule("petty cash", LeadSheet.A, 1.0, is_phrase=True),
    LeadSheetRule("bank", LeadSheet.A, 0.9),
    LeadSheetRule("checking", LeadSheet.A, 0.95),
    LeadSheetRule("savings", LeadSheet.A, 0.95),
    LeadSheetRule("money market", LeadSheet.A, 0.95, is_phrase=True),
    LeadSheetRule("cash equivalent", LeadSheet.A, 1.0, is_phrase=True),
    LeadSheetRule("treasury bill", LeadSheet.A, 0.85, is_phrase=True),

    # -------------------------------------------------------------------------
    # B: Receivables
    # -------------------------------------------------------------------------
    LeadSheetRule("accounts receivable", LeadSheet.B, 1.0, is_phrase=True),
    LeadSheetRule("a/r", LeadSheet.B, 0.95),
    LeadSheetRule("receivable", LeadSheet.B, 0.85),
    LeadSheetRule("trade receivable", LeadSheet.B, 1.0, is_phrase=True),
    LeadSheetRule("notes receivable", LeadSheet.B, 0.95, is_phrase=True),
    LeadSheetRule("allowance for doubtful", LeadSheet.B, 0.95, is_phrase=True),
    LeadSheetRule("bad debt", LeadSheet.B, 0.80, is_phrase=True),
    LeadSheetRule("due from", LeadSheet.B, 0.80, is_phrase=True),

    # -------------------------------------------------------------------------
    # C: Inventory
    # -------------------------------------------------------------------------
    LeadSheetRule("inventory", LeadSheet.C, 1.0),
    LeadSheetRule("raw material", LeadSheet.C, 0.95, is_phrase=True),
    LeadSheetRule("work in process", LeadSheet.C, 0.95, is_phrase=True),
    LeadSheetRule("work in progress", LeadSheet.C, 0.95, is_phrase=True),
    LeadSheetRule("wip", LeadSheet.C, 0.85),
    LeadSheetRule("finished goods", LeadSheet.C, 0.95, is_phrase=True),
    LeadSheetRule("merchandise", LeadSheet.C, 0.90),
    LeadSheetRule("supplies", LeadSheet.C, 0.70),  # Could be prepaid
    LeadSheetRule("inventory reserve", LeadSheet.C, 0.95, is_phrase=True),

    # -------------------------------------------------------------------------
    # D: Prepaid Expenses and Other Current Assets
    # -------------------------------------------------------------------------
    LeadSheetRule("prepaid", LeadSheet.D, 0.95),
    LeadSheetRule("prepaid expense", LeadSheet.D, 1.0, is_phrase=True),
    LeadSheetRule("prepaid insurance", LeadSheet.D, 1.0, is_phrase=True),
    LeadSheetRule("prepaid rent", LeadSheet.D, 1.0, is_phrase=True),
    LeadSheetRule("deposit", LeadSheet.D, 0.75),
    LeadSheetRule("security deposit", LeadSheet.D, 0.85, is_phrase=True),
    LeadSheetRule("advance", LeadSheet.D, 0.70),
    LeadSheetRule("other current asset", LeadSheet.D, 0.90, is_phrase=True),

    # -------------------------------------------------------------------------
    # E: Property, Plant & Equipment
    # -------------------------------------------------------------------------
    LeadSheetRule("property", LeadSheet.E, 0.75),
    LeadSheetRule("plant", LeadSheet.E, 0.80),
    LeadSheetRule("equipment", LeadSheet.E, 0.90),
    LeadSheetRule("machinery", LeadSheet.E, 0.90),
    LeadSheetRule("furniture", LeadSheet.E, 0.90),
    LeadSheetRule("fixture", LeadSheet.E, 0.90),
    LeadSheetRule("vehicle", LeadSheet.E, 0.90),
    LeadSheetRule("automobile", LeadSheet.E, 0.90),
    LeadSheetRule("building", LeadSheet.E, 0.95),
    LeadSheetRule("land", LeadSheet.E, 0.95),
    LeadSheetRule("leasehold improvement", LeadSheet.E, 0.95, is_phrase=True),
    LeadSheetRule("construction in progress", LeadSheet.E, 0.95, is_phrase=True),
    LeadSheetRule("accumulated depreciation", LeadSheet.E, 1.0, is_phrase=True),
    LeadSheetRule("right-of-use", LeadSheet.E, 0.90, is_phrase=True),
    LeadSheetRule("rou asset", LeadSheet.E, 0.90, is_phrase=True),

    # -------------------------------------------------------------------------
    # F: Other Assets / Intangibles
    # -------------------------------------------------------------------------
    LeadSheetRule("goodwill", LeadSheet.F, 1.0),
    LeadSheetRule("intangible", LeadSheet.F, 0.95),
    LeadSheetRule("patent", LeadSheet.F, 0.95),
    LeadSheetRule("trademark", LeadSheet.F, 0.95),
    LeadSheetRule("copyright", LeadSheet.F, 0.95),
    LeadSheetRule("software", LeadSheet.F, 0.80),
    LeadSheetRule("license", LeadSheet.F, 0.75),
    LeadSheetRule("franchise", LeadSheet.F, 0.85),
    LeadSheetRule("investment", LeadSheet.F, 0.80),
    LeadSheetRule("long-term investment", LeadSheet.F, 0.90, is_phrase=True),
    LeadSheetRule("other asset", LeadSheet.F, 0.85, is_phrase=True),
    LeadSheetRule("deferred tax asset", LeadSheet.F, 0.95, is_phrase=True),
    LeadSheetRule("amortization", LeadSheet.F, 0.85),

    # -------------------------------------------------------------------------
    # G: Accounts Payable and Accrued Liabilities
    # -------------------------------------------------------------------------
    LeadSheetRule("accounts payable", LeadSheet.G, 1.0, is_phrase=True),
    LeadSheetRule("a/p", LeadSheet.G, 0.95),
    LeadSheetRule("payable", LeadSheet.G, 0.80),
    LeadSheetRule("trade payable", LeadSheet.G, 1.0, is_phrase=True),
    LeadSheetRule("accrued", LeadSheet.G, 0.85),
    LeadSheetRule("accrued expense", LeadSheet.G, 0.95, is_phrase=True),
    LeadSheetRule("accrued liability", LeadSheet.G, 0.95, is_phrase=True),
    LeadSheetRule("accrued wages", LeadSheet.G, 0.95, is_phrase=True),
    LeadSheetRule("wages payable", LeadSheet.G, 0.95, is_phrase=True),
    LeadSheetRule("salaries payable", LeadSheet.G, 0.95, is_phrase=True),
    LeadSheetRule("due to", LeadSheet.G, 0.80, is_phrase=True),

    # -------------------------------------------------------------------------
    # H: Other Current Liabilities
    # -------------------------------------------------------------------------
    LeadSheetRule("unearned", LeadSheet.H, 0.90),
    LeadSheetRule("unearned revenue", LeadSheet.H, 0.95, is_phrase=True),
    LeadSheetRule("deferred revenue", LeadSheet.H, 0.95, is_phrase=True),
    LeadSheetRule("customer deposit", LeadSheet.H, 0.90, is_phrase=True),
    LeadSheetRule("sales tax payable", LeadSheet.H, 0.95, is_phrase=True),
    LeadSheetRule("income tax payable", LeadSheet.H, 0.95, is_phrase=True),
    LeadSheetRule("tax payable", LeadSheet.H, 0.85, is_phrase=True),
    LeadSheetRule("payroll tax", LeadSheet.H, 0.90, is_phrase=True),
    LeadSheetRule("current portion", LeadSheet.H, 0.85, is_phrase=True),
    LeadSheetRule("short-term", LeadSheet.H, 0.70, is_phrase=True),
    LeadSheetRule("lease liability current", LeadSheet.H, 0.95, is_phrase=True),

    # -------------------------------------------------------------------------
    # I: Long-term Debt
    # -------------------------------------------------------------------------
    LeadSheetRule("long-term debt", LeadSheet.I, 1.0, is_phrase=True),
    LeadSheetRule("notes payable", LeadSheet.I, 0.85, is_phrase=True),
    LeadSheetRule("loan", LeadSheet.I, 0.80),
    LeadSheetRule("mortgage", LeadSheet.I, 0.95),
    LeadSheetRule("bonds payable", LeadSheet.I, 0.95, is_phrase=True),
    LeadSheetRule("debenture", LeadSheet.I, 0.95),
    LeadSheetRule("line of credit", LeadSheet.I, 0.85, is_phrase=True),
    LeadSheetRule("bank loan", LeadSheet.I, 0.90, is_phrase=True),
    LeadSheetRule("term loan", LeadSheet.I, 0.90, is_phrase=True),

    # -------------------------------------------------------------------------
    # J: Other Long-term Liabilities / Deferred Items
    # -------------------------------------------------------------------------
    LeadSheetRule("deferred tax liability", LeadSheet.J, 0.95, is_phrase=True),
    LeadSheetRule("pension liability", LeadSheet.J, 0.95, is_phrase=True),
    LeadSheetRule("post-retirement", LeadSheet.J, 0.90, is_phrase=True),
    LeadSheetRule("other long-term", LeadSheet.J, 0.90, is_phrase=True),
    LeadSheetRule("lease liability long", LeadSheet.J, 0.95, is_phrase=True),
    LeadSheetRule("lease liability non-current", LeadSheet.J, 0.95, is_phrase=True),
    LeadSheetRule("contingent liability", LeadSheet.J, 0.90, is_phrase=True),
    LeadSheetRule("provision", LeadSheet.J, 0.75),

    # -------------------------------------------------------------------------
    # K: Equity / Stockholders' Equity
    # -------------------------------------------------------------------------
    LeadSheetRule("common stock", LeadSheet.K, 1.0, is_phrase=True),
    LeadSheetRule("preferred stock", LeadSheet.K, 1.0, is_phrase=True),
    LeadSheetRule("capital stock", LeadSheet.K, 1.0, is_phrase=True),
    LeadSheetRule("share capital", LeadSheet.K, 1.0, is_phrase=True),
    LeadSheetRule("paid-in capital", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("additional paid-in", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("apic", LeadSheet.K, 0.90),
    LeadSheetRule("retained earnings", LeadSheet.K, 1.0, is_phrase=True),
    LeadSheetRule("accumulated deficit", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("treasury stock", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("owner equity", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("partner capital", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("member equity", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("drawing", LeadSheet.K, 0.85),
    LeadSheetRule("distribution", LeadSheet.K, 0.80),
    LeadSheetRule("dividend", LeadSheet.K, 0.85),
    LeadSheetRule("accumulated other comprehensive", LeadSheet.K, 0.95, is_phrase=True),
    LeadSheetRule("aoci", LeadSheet.K, 0.90),

    # -------------------------------------------------------------------------
    # L: Revenue / Sales
    # -------------------------------------------------------------------------
    LeadSheetRule("revenue", LeadSheet.L, 0.90),
    LeadSheetRule("sales", LeadSheet.L, 0.90),
    LeadSheetRule("service revenue", LeadSheet.L, 0.95, is_phrase=True),
    LeadSheetRule("product revenue", LeadSheet.L, 0.95, is_phrase=True),
    LeadSheetRule("fee income", LeadSheet.L, 0.90, is_phrase=True),
    LeadSheetRule("commission income", LeadSheet.L, 0.90, is_phrase=True),
    LeadSheetRule("sales discount", LeadSheet.L, 0.85, is_phrase=True),
    LeadSheetRule("sales return", LeadSheet.L, 0.85, is_phrase=True),
    LeadSheetRule("sales allowance", LeadSheet.L, 0.85, is_phrase=True),

    # -------------------------------------------------------------------------
    # M: Cost of Goods Sold
    # -------------------------------------------------------------------------
    LeadSheetRule("cost of goods sold", LeadSheet.M, 1.0, is_phrase=True),
    LeadSheetRule("cogs", LeadSheet.M, 0.95),
    LeadSheetRule("cost of sales", LeadSheet.M, 0.95, is_phrase=True),
    LeadSheetRule("cost of revenue", LeadSheet.M, 0.95, is_phrase=True),
    LeadSheetRule("cost of service", LeadSheet.M, 0.90, is_phrase=True),
    LeadSheetRule("direct cost", LeadSheet.M, 0.85, is_phrase=True),
    LeadSheetRule("direct labor", LeadSheet.M, 0.85, is_phrase=True),
    LeadSheetRule("direct material", LeadSheet.M, 0.85, is_phrase=True),
    LeadSheetRule("manufacturing cost", LeadSheet.M, 0.90, is_phrase=True),
    LeadSheetRule("production cost", LeadSheet.M, 0.85, is_phrase=True),
    LeadSheetRule("purchase", LeadSheet.M, 0.70),
    LeadSheetRule("freight in", LeadSheet.M, 0.80, is_phrase=True),

    # -------------------------------------------------------------------------
    # N: Operating Expenses
    # -------------------------------------------------------------------------
    LeadSheetRule("salary expense", LeadSheet.N, 0.90, is_phrase=True),
    LeadSheetRule("wage expense", LeadSheet.N, 0.90, is_phrase=True),
    LeadSheetRule("payroll expense", LeadSheet.N, 0.90, is_phrase=True),
    LeadSheetRule("rent expense", LeadSheet.N, 0.90, is_phrase=True),
    LeadSheetRule("utilities", LeadSheet.N, 0.85),
    LeadSheetRule("insurance expense", LeadSheet.N, 0.90, is_phrase=True),
    LeadSheetRule("depreciation expense", LeadSheet.N, 0.95, is_phrase=True),
    LeadSheetRule("amortization expense", LeadSheet.N, 0.95, is_phrase=True),
    LeadSheetRule("advertising", LeadSheet.N, 0.85),
    LeadSheetRule("marketing", LeadSheet.N, 0.85),
    LeadSheetRule("professional fee", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("legal expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("accounting expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("office expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("office supplies", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("telephone", LeadSheet.N, 0.80),
    LeadSheetRule("internet", LeadSheet.N, 0.80),
    LeadSheetRule("travel expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("meals", LeadSheet.N, 0.75),
    LeadSheetRule("entertainment", LeadSheet.N, 0.75),
    LeadSheetRule("repair", LeadSheet.N, 0.75),
    LeadSheetRule("maintenance", LeadSheet.N, 0.75),
    LeadSheetRule("training", LeadSheet.N, 0.75),
    LeadSheetRule("subscription", LeadSheet.N, 0.75),
    LeadSheetRule("dues", LeadSheet.N, 0.70),
    LeadSheetRule("bad debt expense", LeadSheet.N, 0.90, is_phrase=True),
    LeadSheetRule("operating expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("general expense", LeadSheet.N, 0.80, is_phrase=True),
    LeadSheetRule("administrative expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("selling expense", LeadSheet.N, 0.85, is_phrase=True),
    LeadSheetRule("sg&a", LeadSheet.N, 0.90),

    # -------------------------------------------------------------------------
    # O: Other Income / Expense
    # -------------------------------------------------------------------------
    LeadSheetRule("interest income", LeadSheet.O, 0.95, is_phrase=True),
    LeadSheetRule("interest expense", LeadSheet.O, 0.95, is_phrase=True),
    LeadSheetRule("dividend income", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("gain on sale", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("loss on sale", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("gain on disposal", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("loss on disposal", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("foreign exchange", LeadSheet.O, 0.85, is_phrase=True),
    LeadSheetRule("fx gain", LeadSheet.O, 0.85, is_phrase=True),
    LeadSheetRule("fx loss", LeadSheet.O, 0.85, is_phrase=True),
    LeadSheetRule("other income", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("other expense", LeadSheet.O, 0.90, is_phrase=True),
    LeadSheetRule("miscellaneous income", LeadSheet.O, 0.85, is_phrase=True),
    LeadSheetRule("miscellaneous expense", LeadSheet.O, 0.85, is_phrase=True),
    LeadSheetRule("income tax expense", LeadSheet.O, 0.95, is_phrase=True),
    LeadSheetRule("tax expense", LeadSheet.O, 0.80, is_phrase=True),
    LeadSheetRule("extraordinary", LeadSheet.O, 0.85),
]


# =============================================================================
# CATEGORY-TO-LEADSHEET FALLBACK MAPPING
# =============================================================================

# When keyword matching fails, use account category as fallback
CATEGORY_FALLBACK_MAP: dict[AccountCategory, LeadSheet] = {
    AccountCategory.ASSET: LeadSheet.F,       # Other Assets (catch-all)
    AccountCategory.LIABILITY: LeadSheet.J,   # Other Long-term Liabilities
    AccountCategory.EQUITY: LeadSheet.K,      # Equity
    AccountCategory.REVENUE: LeadSheet.L,     # Revenue
    AccountCategory.EXPENSE: LeadSheet.N,     # Operating Expenses
    AccountCategory.UNKNOWN: LeadSheet.Z,     # Unclassified
}


# =============================================================================
# LEAD SHEET ASSIGNMENT FUNCTIONS
# =============================================================================

def assign_lead_sheet(
    account_name: str,
    account_category: Optional[AccountCategory] = None,
    override: Optional[LeadSheet] = None
) -> LeadSheetAssignment:
    """
    Assign a lead sheet to an account based on keywords and category.

    Args:
        account_name: The account name to classify
        account_category: Optional pre-determined account category
        override: Optional manual lead sheet override

    Returns:
        LeadSheetAssignment with lead sheet and confidence
    """
    # Handle override
    if override is not None:
        return LeadSheetAssignment(
            account_name=account_name,
            lead_sheet=override,
            lead_sheet_name=LEAD_SHEET_NAMES[override],
            confidence=1.0,
            matched_keywords=[],
            is_override=True
        )

    account_lower = account_name.lower().strip()
    best_match: Optional[LeadSheetRule] = None
    best_weight = 0.0
    matched_keywords: list[str] = []

    # Try phrase matches first (more specific)
    for rule in LEAD_SHEET_RULES:
        if rule.is_phrase:
            if rule.keyword in account_lower:
                if rule.weight > best_weight:
                    best_match = rule
                    best_weight = rule.weight
                    matched_keywords = [rule.keyword]

    # Then try single keyword matches
    for rule in LEAD_SHEET_RULES:
        if not rule.is_phrase:
            if rule.keyword in account_lower:
                if rule.weight > best_weight:
                    best_match = rule
                    best_weight = rule.weight
                    matched_keywords = [rule.keyword]
                elif rule.weight == best_weight and rule.keyword not in matched_keywords:
                    matched_keywords.append(rule.keyword)

    # If we found a match, use it
    if best_match is not None:
        return LeadSheetAssignment(
            account_name=account_name,
            lead_sheet=best_match.lead_sheet,
            lead_sheet_name=LEAD_SHEET_NAMES[best_match.lead_sheet],
            confidence=best_weight,
            matched_keywords=matched_keywords,
            is_override=False
        )

    # Fallback to category-based assignment
    if account_category is not None and account_category in CATEGORY_FALLBACK_MAP:
        fallback_sheet = CATEGORY_FALLBACK_MAP[account_category]
        return LeadSheetAssignment(
            account_name=account_name,
            lead_sheet=fallback_sheet,
            lead_sheet_name=LEAD_SHEET_NAMES[fallback_sheet],
            confidence=0.5,  # Lower confidence for fallback
            matched_keywords=[],
            is_override=False
        )

    # No match found - unclassified
    return LeadSheetAssignment(
        account_name=account_name,
        lead_sheet=LeadSheet.Z,
        lead_sheet_name=LEAD_SHEET_NAMES[LeadSheet.Z],
        confidence=0.0,
        matched_keywords=[],
        is_override=False
    )


def group_by_lead_sheet(
    accounts: list[dict],
    overrides: Optional[dict[str, LeadSheet]] = None
) -> LeadSheetGrouping:
    """
    Group a list of accounts by their lead sheet assignment.

    Args:
        accounts: List of account dicts with 'account', 'debit', 'credit', 'type' keys
        overrides: Optional dict mapping account names to lead sheet overrides

    Returns:
        LeadSheetGrouping with summaries for each lead sheet
    """
    overrides = overrides or {}

    # Initialize summaries for all lead sheets
    summaries_dict: dict[LeadSheet, LeadSheetSummary] = {}

    for ls in LeadSheet:
        summaries_dict[ls] = LeadSheetSummary(
            lead_sheet=ls,
            name=LEAD_SHEET_NAMES[ls],
            category=LEAD_SHEET_CATEGORY[ls],
            total_debit=0.0,
            total_credit=0.0,
            net_balance=0.0,
            account_count=0,
            accounts=[]
        )

    total_debits = 0.0
    total_credits = 0.0

    # Assign each account to a lead sheet
    for account in accounts:
        account_name = account.get('account', '')
        debit = float(account.get('debit', 0) or 0)
        credit = float(account.get('credit', 0) or 0)
        account_type = account.get('type', 'unknown')

        # Get category from account type
        try:
            category = AccountCategory(account_type)
        except ValueError:
            category = AccountCategory.UNKNOWN

        # Check for override
        override = overrides.get(account_name)

        # Assign lead sheet
        assignment = assign_lead_sheet(account_name, category, override)

        # Update summary
        summary = summaries_dict[assignment.lead_sheet]
        summary.total_debit += debit
        summary.total_credit += credit
        summary.account_count += 1
        summary.accounts.append({
            **account,
            'lead_sheet': assignment.lead_sheet.value,
            'lead_sheet_confidence': assignment.confidence,
            'lead_sheet_keywords': assignment.matched_keywords,
            'is_override': assignment.is_override
        })

        total_debits += debit
        total_credits += credit

    # Calculate net balances and filter empty lead sheets
    summaries: list[LeadSheetSummary] = []
    unclassified_count = 0

    for ls in LeadSheet:
        summary = summaries_dict[ls]
        if summary.account_count > 0:
            summary.net_balance = summary.total_debit - summary.total_credit
            summaries.append(summary)

            if ls == LeadSheet.Z:
                unclassified_count = summary.account_count

    # Sort by lead sheet letter
    summaries.sort(key=lambda s: s.lead_sheet.value)

    log_secure_operation(
        "lead_sheet_grouping",
        f"Grouped {len(accounts)} accounts into {len(summaries)} lead sheets"
    )

    return LeadSheetGrouping(
        summaries=summaries,
        total_debits=total_debits,
        total_credits=total_credits,
        unclassified_count=unclassified_count
    )


def get_lead_sheet_options() -> list[dict]:
    """
    Get list of lead sheet options for UI dropdown.

    Returns:
        List of dicts with 'value', 'label', 'category' keys
    """
    return [
        {
            'value': ls.value,
            'label': f"{ls.value}: {LEAD_SHEET_NAMES[ls]}",
            'category': LEAD_SHEET_CATEGORY[ls]
        }
        for ls in LeadSheet
    ]


def lead_sheet_grouping_to_dict(grouping: LeadSheetGrouping) -> dict:
    """Convert LeadSheetGrouping to JSON-serializable dict."""
    return {
        'summaries': [
            {
                'lead_sheet': s.lead_sheet.value,
                'name': s.name,
                'category': s.category,
                'total_debit': s.total_debit,
                'total_credit': s.total_credit,
                'net_balance': s.net_balance,
                'account_count': s.account_count,
                'accounts': s.accounts
            }
            for s in grouping.summaries
        ],
        'total_debits': grouping.total_debits,
        'total_credits': grouping.total_credits,
        'unclassified_count': grouping.unclassified_count
    }
