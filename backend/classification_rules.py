"""
Paciolus Classification Rules
Weighted Heuristic Account Classification

All keywords are derived from publicly available accounting terminology:
- GAAP standard categories (public domain)
- Investopedia, AccountingCoach.com (public educational)
- GnuCash/Odoo/ERPNext schemas (GPL/LGPL licensed)

See: logs/dev-log.md for full IP documentation

IFRS/GAAP Classification Compatibility
--------------------------------------
These classification rules use terminology common to both US GAAP and IFRS.
Key differences to be aware of:

DEFERRED REVENUE / UNEARNED REVENUE:
- Both: Classified as LIABILITY until performance obligation satisfied
- IFRS 15 may accelerate recognition for certain contract modifications
- Classification confidence: 0.90 for "deferred revenue"

LEASES (Post-2019):
- Both frameworks recognize right-of-use assets and lease liabilities
- US GAAP (ASC 842): Operating leases may show single expense line
- IFRS 16: Almost all leases show depreciation + interest expense
- Classification: "right-of-use" → ASSET, "lease liability" → LIABILITY

DEVELOPMENT COSTS:
- US GAAP: Expensed as incurred (classified as EXPENSE)
- IFRS: May be capitalized if 6 criteria met (classified as ASSET)
- Classification: "development costs" → EXPENSE (conservative default)
- Note: IFRS-prepared statements may show as intangible asset

PROVISIONS / CONTINGENT LIABILITIES:
- US GAAP: Recognize when "probable" (~75%+ likelihood)
- IFRS: Recognize when "more likely than not" (>50% likelihood)
- Result: IFRS may recognize more provisions as liabilities
- Classification rules do not distinguish; treats "provision" as LIABILITY

See docs/STANDARDS.md for detailed framework comparison.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AccountCategory(str, Enum):
    """Primary account categories following standard chart of accounts."""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    UNKNOWN = "unknown"


class NormalBalance(str, Enum):
    """Expected normal balance direction per accounting fundamentals."""
    DEBIT = "debit"    # Assets, Expenses increase with debits
    CREDIT = "credit"  # Liabilities, Equity, Revenue increase with credits


@dataclass
class ClassificationRule:
    """A single weighted keyword rule for account classification."""
    keyword: str                   # Keyword to match (case-insensitive)
    category: AccountCategory      # Target category
    weight: float                  # Confidence contribution (0.0 to 1.0)
    is_phrase: bool = False        # True if multi-word phrase (stricter match)


@dataclass
class ClassificationSuggestion:
    """
    A suggested alternative classification for low-confidence accounts.

    Sprint 31: Classification Intelligence feature.
    """
    category: AccountCategory
    confidence: float              # Estimated confidence if this category were applied
    reason: str                    # Why this suggestion is offered
    matched_keywords: list[str]    # Keywords that support this suggestion


@dataclass
class ClassificationResult:
    """Result of account classification."""
    account_name: str
    category: AccountCategory
    confidence: float              # 0.0 to 1.0
    normal_balance: NormalBalance
    matched_keywords: list[str]
    is_abnormal: bool              # Balance direction opposite of normal
    requires_review: bool          # True if confidence below threshold
    suggestions: list[ClassificationSuggestion] = field(default_factory=list)  # Sprint 31: Alternative classifications


# Confidence thresholds
CONFIDENCE_HIGH = 0.7     # Confident classification
CONFIDENCE_MEDIUM = 0.4   # Probable classification (flag for review)


# =============================================================================
# NORMAL BALANCE MAPPING (Standard Double-Entry Bookkeeping)
# =============================================================================

NORMAL_BALANCE_MAP: dict[AccountCategory, NormalBalance] = {
    AccountCategory.ASSET: NormalBalance.DEBIT,
    AccountCategory.LIABILITY: NormalBalance.CREDIT,
    AccountCategory.EQUITY: NormalBalance.CREDIT,
    AccountCategory.REVENUE: NormalBalance.CREDIT,
    AccountCategory.EXPENSE: NormalBalance.DEBIT,
    AccountCategory.UNKNOWN: NormalBalance.DEBIT,  # Default assumption
}


# =============================================================================
# WEIGHTED KEYWORD RULES (~80 keywords, standard accounting terminology)
# =============================================================================

DEFAULT_RULES: list[ClassificationRule] = [
    # -------------------------------------------------------------------------
    # ASSETS (25 keywords)
    # Source: GAAP standard terminology, Investopedia, GnuCash schema
    #
    # IFRS/GAAP Notes:
    # - Inventory: LIFO permitted (US GAAP) vs prohibited (IFRS)
    # - PPE revaluation: Permitted (IFRS) vs prohibited (US GAAP)
    # - Development costs: May be asset (IFRS) vs expense (US GAAP)
    # - Right-of-use assets: Both frameworks post-2019 (ASC 842 / IFRS 16)
    # -------------------------------------------------------------------------
    # High confidence (0.85-0.95) - definitive asset terms
    ClassificationRule("cash", AccountCategory.ASSET, 0.95),
    ClassificationRule("petty cash", AccountCategory.ASSET, 0.95, is_phrase=True),
    ClassificationRule("bank", AccountCategory.ASSET, 0.85),
    ClassificationRule("checking", AccountCategory.ASSET, 0.90),
    ClassificationRule("savings", AccountCategory.ASSET, 0.90),
    ClassificationRule("accounts receivable", AccountCategory.ASSET, 0.95, is_phrase=True),
    ClassificationRule("a/r", AccountCategory.ASSET, 0.85),
    ClassificationRule("receivable", AccountCategory.ASSET, 0.80),
    ClassificationRule("inventory", AccountCategory.ASSET, 0.90),
    ClassificationRule("prepaid", AccountCategory.ASSET, 0.85),
    ClassificationRule("equipment", AccountCategory.ASSET, 0.85),
    ClassificationRule("furniture", AccountCategory.ASSET, 0.85),
    ClassificationRule("vehicle", AccountCategory.ASSET, 0.85),
    ClassificationRule("land", AccountCategory.ASSET, 0.90),
    ClassificationRule("building", AccountCategory.ASSET, 0.85),
    ClassificationRule("property", AccountCategory.ASSET, 0.70),
    ClassificationRule("machinery", AccountCategory.ASSET, 0.85),
    ClassificationRule("goodwill", AccountCategory.ASSET, 0.90),
    ClassificationRule("patent", AccountCategory.ASSET, 0.85),
    ClassificationRule("trademark", AccountCategory.ASSET, 0.85),
    ClassificationRule("investment", AccountCategory.ASSET, 0.75),
    ClassificationRule("securities", AccountCategory.ASSET, 0.80),
    ClassificationRule("deposit", AccountCategory.ASSET, 0.70),
    ClassificationRule("due from", AccountCategory.ASSET, 0.80, is_phrase=True),
    ClassificationRule("accumulated depreciation", AccountCategory.ASSET, 0.90, is_phrase=True),

    # -------------------------------------------------------------------------
    # LIABILITIES (20 keywords)
    # Source: GAAP standard terminology, Investopedia, Odoo schema
    #
    # IFRS/GAAP Notes:
    # - "Deferred revenue" / "Unearned revenue": Liability under both frameworks
    # - "Provision": IFRS has lower recognition threshold (>50% vs ~75%)
    # - Lease liabilities: Both frameworks post-2019 (ASC 842 / IFRS 16)
    # - Redeemable preferred may be liability (IFRS) vs equity (US GAAP)
    # -------------------------------------------------------------------------
    ClassificationRule("accounts payable", AccountCategory.LIABILITY, 0.95, is_phrase=True),
    ClassificationRule("a/p", AccountCategory.LIABILITY, 0.85),
    ClassificationRule("payable", AccountCategory.LIABILITY, 0.75),
    ClassificationRule("accrued", AccountCategory.LIABILITY, 0.75),
    ClassificationRule("accrued expense", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("wages payable", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("salaries payable", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("interest payable", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("tax payable", AccountCategory.LIABILITY, 0.85, is_phrase=True),
    ClassificationRule("unearned", AccountCategory.LIABILITY, 0.85),
    ClassificationRule("deferred revenue", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("customer deposit", AccountCategory.LIABILITY, 0.85, is_phrase=True),
    ClassificationRule("loan", AccountCategory.LIABILITY, 0.75),
    ClassificationRule("note payable", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("notes payable", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("mortgage", AccountCategory.LIABILITY, 0.90),
    ClassificationRule("bonds payable", AccountCategory.LIABILITY, 0.90, is_phrase=True),
    ClassificationRule("debt", AccountCategory.LIABILITY, 0.75),
    ClassificationRule("credit card", AccountCategory.LIABILITY, 0.80, is_phrase=True),
    ClassificationRule("due to", AccountCategory.LIABILITY, 0.80, is_phrase=True),

    # -------------------------------------------------------------------------
    # EQUITY (12 keywords)
    # Source: GAAP standard terminology, ERPNext schema
    # -------------------------------------------------------------------------
    ClassificationRule("common stock", AccountCategory.EQUITY, 0.95, is_phrase=True),
    ClassificationRule("preferred stock", AccountCategory.EQUITY, 0.95, is_phrase=True),
    ClassificationRule("capital stock", AccountCategory.EQUITY, 0.90, is_phrase=True),
    ClassificationRule("paid-in capital", AccountCategory.EQUITY, 0.90, is_phrase=True),
    ClassificationRule("retained earnings", AccountCategory.EQUITY, 0.95, is_phrase=True),
    ClassificationRule("treasury stock", AccountCategory.EQUITY, 0.90, is_phrase=True),
    ClassificationRule("owner's equity", AccountCategory.EQUITY, 0.90, is_phrase=True),
    ClassificationRule("owner equity", AccountCategory.EQUITY, 0.85, is_phrase=True),
    ClassificationRule("capital", AccountCategory.EQUITY, 0.65),
    ClassificationRule("drawing", AccountCategory.EQUITY, 0.80),
    ClassificationRule("distribution", AccountCategory.EQUITY, 0.70),
    ClassificationRule("dividend", AccountCategory.EQUITY, 0.75),

    # -------------------------------------------------------------------------
    # REVENUE (12 keywords)
    # Source: GAAP standard terminology, Investopedia
    # -------------------------------------------------------------------------
    ClassificationRule("revenue", AccountCategory.REVENUE, 0.85),
    ClassificationRule("sales", AccountCategory.REVENUE, 0.80),
    ClassificationRule("service revenue", AccountCategory.REVENUE, 0.90, is_phrase=True),
    ClassificationRule("service income", AccountCategory.REVENUE, 0.90, is_phrase=True),
    ClassificationRule("fee income", AccountCategory.REVENUE, 0.85, is_phrase=True),
    ClassificationRule("consulting revenue", AccountCategory.REVENUE, 0.90, is_phrase=True),
    ClassificationRule("interest income", AccountCategory.REVENUE, 0.85, is_phrase=True),
    ClassificationRule("dividend income", AccountCategory.REVENUE, 0.85, is_phrase=True),
    ClassificationRule("rental income", AccountCategory.REVENUE, 0.85, is_phrase=True),
    ClassificationRule("gain on sale", AccountCategory.REVENUE, 0.80, is_phrase=True),
    ClassificationRule("other income", AccountCategory.REVENUE, 0.75, is_phrase=True),
    ClassificationRule("income", AccountCategory.REVENUE, 0.55),

    # -------------------------------------------------------------------------
    # EXPENSES (20 keywords)
    # Source: GAAP standard terminology, AccountingCoach.com
    #
    # IFRS/GAAP Notes:
    # - R&D: US GAAP expenses all; IFRS may capitalize development costs
    # - Lease expense: Single line (US GAAP operating) vs split (IFRS 16)
    # - Extraordinary items: Prohibited under both frameworks (post-2015)
    # - Interest expense: May be operating (US GAAP) or financing (IFRS)
    # -------------------------------------------------------------------------
    ClassificationRule("cost of goods sold", AccountCategory.EXPENSE, 0.95, is_phrase=True),
    ClassificationRule("cogs", AccountCategory.EXPENSE, 0.90),
    ClassificationRule("cost of sales", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("salary expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("wage expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("payroll expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("rent expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("utilities expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("insurance expense", AccountCategory.EXPENSE, 0.85, is_phrase=True),
    ClassificationRule("depreciation expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("advertising expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("office expense", AccountCategory.EXPENSE, 0.85, is_phrase=True),
    ClassificationRule("supplies expense", AccountCategory.EXPENSE, 0.85, is_phrase=True),
    ClassificationRule("professional fees", AccountCategory.EXPENSE, 0.85, is_phrase=True),
    ClassificationRule("interest expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("bad debt expense", AccountCategory.EXPENSE, 0.90, is_phrase=True),
    ClassificationRule("tax expense", AccountCategory.EXPENSE, 0.75, is_phrase=True),
    ClassificationRule("loss on sale", AccountCategory.EXPENSE, 0.85, is_phrase=True),
    ClassificationRule("expense", AccountCategory.EXPENSE, 0.50),
    ClassificationRule("cost", AccountCategory.EXPENSE, 0.45),
]


# =============================================================================
# ACCOUNT NUMBER PATTERNS (Supplementary Signal)
# Source: Standard Chart of Accounts numbering (GnuCash, academic textbooks)
# =============================================================================

ACCOUNT_NUMBER_RANGES: list[tuple[str, str, AccountCategory, float]] = [
    # (start, end, category, weight)
    ("1000", "1999", AccountCategory.ASSET, 0.30),
    ("2000", "2999", AccountCategory.LIABILITY, 0.30),
    ("3000", "3999", AccountCategory.EQUITY, 0.30),
    ("4000", "4999", AccountCategory.REVENUE, 0.30),
    ("5000", "5999", AccountCategory.EXPENSE, 0.30),
    ("6000", "6999", AccountCategory.EXPENSE, 0.30),
    ("7000", "7999", AccountCategory.EXPENSE, 0.25),
    ("8000", "8999", AccountCategory.EXPENSE, 0.20),
]


# Human-readable category names for API responses
CATEGORY_DISPLAY_NAMES: dict[AccountCategory, str] = {
    AccountCategory.ASSET: "Asset",
    AccountCategory.LIABILITY: "Liability",
    AccountCategory.EQUITY: "Equity",
    AccountCategory.REVENUE: "Revenue",
    AccountCategory.EXPENSE: "Expense",
    AccountCategory.UNKNOWN: "Unknown",
}


# =============================================================================
# SUSPENSE ACCOUNT DETECTION (Sprint 41 - Phase III)
# =============================================================================
# Suspense accounts indicate items awaiting proper classification.
# Their existence in a trial balance is a potential control weakness.
#
# GAAP/IFRS Notes:
# - Both frameworks require proper account classification
# - Suspense accounts should be temporary and cleared regularly
# - Material suspense balances may indicate internal control deficiencies
# =============================================================================

# Keywords that indicate a suspense or clearing account
# Tuple format: (keyword, weight, is_phrase)
# Weight indicates confidence that the account is truly a suspense account
SUSPENSE_KEYWORDS: list[tuple[str, float, bool]] = [
    # High confidence (0.90+) - definitive suspense terms
    ("suspense", 0.95, False),
    ("suspense account", 0.98, True),
    ("clearing account", 0.95, True),
    ("clearing", 0.85, False),
    ("unallocated", 0.90, False),
    ("unidentified", 0.90, False),
    ("unclassified", 0.90, False),
    ("pending classification", 0.95, True),
    ("awaiting classification", 0.95, True),

    # Medium confidence (0.70-0.89) - likely suspense terms
    ("temporary", 0.75, False),
    ("holding account", 0.85, True),
    ("holding", 0.60, False),
    ("in transit", 0.80, True),
    ("intercompany clearing", 0.90, True),
    ("bank clearing", 0.85, True),
    ("payroll clearing", 0.85, True),
    ("cash clearing", 0.85, True),

    # Lower confidence (0.50-0.69) - contextual terms
    # These need additional signals to confirm suspense status
    ("miscellaneous", 0.55, False),
    ("other", 0.40, False),  # Very common, low weight
    ("sundry", 0.60, False),
    ("general", 0.35, False),  # Too common, very low weight
]

# Minimum confidence to flag as suspense account
SUSPENSE_CONFIDENCE_THRESHOLD = 0.60
