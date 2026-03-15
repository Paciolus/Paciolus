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

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


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
    # Sprint 530 Fix 3: Tightened — removed vague terms that matched standard
    # operating accounts (e.g. "holding" matched "Holding Company", "other"
    # matched "Other Revenue", "general" matched "General Ledger").
    # High confidence (0.90+) — definitive suspense terms
    ("suspense", 0.95, False),
    ("suspense account", 0.98, True),
    ("clearing account", 0.95, True),
    ("clearing", 0.85, False),
    ("unallocated", 0.90, False),
    ("pending classification", 0.95, True),
    ("awaiting classification", 0.95, True),
    # Medium confidence (0.70–0.89) — likely suspense terms
    # Sprint 535 P1-3: Changed "temporary" to phrase "temporary account" to
    # avoid false positive on "Temporary Labor" / "Temporary Staff".
    ("temporary account", 0.80, True),
    ("temporary balance", 0.80, True),
    ("hold account", 0.85, True),
    ("in transit", 0.80, True),
    ("intercompany clearing", 0.90, True),
    ("bank clearing", 0.85, True),
    ("payroll clearing", 0.85, True),
    ("cash clearing", 0.85, True),
    ("to be allocated", 0.85, True),
    ("wash account", 0.85, True),
    # Lower confidence
]

# Minimum confidence to flag as suspense account
SUSPENSE_CONFIDENCE_THRESHOLD = 0.60


# =============================================================================
# CONCENTRATION RISK DETECTION (Sprint 42 - Phase III)
# =============================================================================
# Concentration risk occurs when a single account represents an unusually
# large percentage of its category total, indicating:
# - Over-reliance on a single customer/vendor
# - Potential collection/payment risk
# - Audit sampling risk
#
# GAAP/IFRS Notes:
# - Both frameworks require disclosure of significant concentrations
# - US GAAP: ASC 275 (Risks and Uncertainties)
# - IFRS: IFRS 7 (Financial Instruments: Disclosures)
# =============================================================================

# Threshold for flagging concentration risk (percentage of category total)
# An account exceeding this percentage of its category total is flagged
CONCENTRATION_THRESHOLD_HIGH = 0.50  # 50% - high severity
CONCENTRATION_THRESHOLD_MEDIUM = 0.25  # 25% - medium severity

# Minimum category total to apply concentration analysis
# Avoids false positives on small categories
CONCENTRATION_MIN_CATEGORY_TOTAL = 1000.0

# Revenue/Expense-specific concentration thresholds
# Used in detect_revenue_concentration() and detect_expense_concentration()
REVENUE_CONCENTRATION_THRESHOLD = 0.30  # 30% - single account > 30% of total revenue
EXPENSE_CONCENTRATION_THRESHOLD = 0.40  # 40% - single account > 40% of total expenses

# Categories to analyze for concentration risk
# (Revenue and Receivables are most common concerns)
CONCENTRATION_CATEGORIES = [
    AccountCategory.ASSET,
    AccountCategory.LIABILITY,
    AccountCategory.REVENUE,
    AccountCategory.EXPENSE,
]


# =============================================================================
# ROUNDING ANOMALY DETECTION (Sprint 42 - Phase III)
# =============================================================================
# Round numbers in financial data may indicate:
# - Estimates rather than actual transactions
# - Journal entry manipulation
# - Placeholder amounts awaiting final figures
#
# GAAP/IFRS Notes:
# - Both frameworks require transactions to be recorded at actual amounts
# - Benford's Law analysis is a common fraud detection technique
# - Round numbers are not inherently wrong, but clusters warrant investigation
# =============================================================================

# Minimum amount to consider for rounding analysis
# Small amounts are often legitimately round (e.g., $50 subscription)
ROUNDING_MIN_AMOUNT = 10000.0

# Rounding patterns to detect (trailing zeros)
# Format: (divisor, name, severity)
# An amount divisible by the divisor with no remainder is flagged
ROUNDING_PATTERNS: list[tuple[float, str, str]] = [
    (100000.0, "hundred_thousand", "high"),    # $100,000, $200,000, etc.
    (50000.0, "fifty_thousand", "medium"),     # $50,000, $150,000, etc.
    (10000.0, "ten_thousand", "low"),          # $10,000, $20,000, etc.
]

# Maximum number of rounding anomalies to report (prevent noise)
ROUNDING_MAX_ANOMALIES = 20

# Accounts to exclude from rounding analysis (common legitimate round amounts)
ROUNDING_EXCLUDE_KEYWORDS: list[str] = [
    "loan",
    "mortgage",
    "bond",
    "note payable",
    "capital stock",
    "common stock",
    "preferred stock",
    "paid-in capital",
    "credit line",
    "line of credit",
]


# =============================================================================
# RELATED PARTY DETECTION (Sprint 526 / Sprint 527 consolidation)
# =============================================================================
# Keywords indicating related party activity requiring ASC 850 disclosure.
# Tuple format: (keyword, weight, is_phrase)

RELATED_PARTY_KEYWORDS: list[tuple[str, float, bool]] = [
    # Sprint 530 Fix 2: Tightened — require explicit relationship language.
    # Removed bare "officer", "director", "shareholder" (matched insurance/fees).
    ("related party", 0.95, True),
    ("related-party", 0.95, True),
    ("intercompany", 0.90, False),
    ("inter-company", 0.90, True),
    ("affiliate", 0.85, False),
    ("affiliated", 0.85, False),
    ("due to officer", 0.95, True),
    ("due from officer", 0.95, True),
    ("due to shareholder", 0.95, True),
    ("due from shareholder", 0.95, True),
    ("due to director", 0.95, True),
    ("due from director", 0.95, True),
    ("shareholder loan", 0.95, True),
    ("officer loan", 0.95, True),
    ("note receivable — officer", 0.95, True),
    ("note receivable — shareholder", 0.95, True),
    ("note receivable — director", 0.95, True),
    ("note payable — officer", 0.95, True),
    ("note payable — shareholder", 0.95, True),
    ("note payable — director", 0.95, True),
    ("due to parent", 0.90, True),
    ("due from parent", 0.90, True),
    ("due to subsidiary", 0.90, True),
    ("due from subsidiary", 0.90, True),
    ("employee loan", 0.90, True),
    ("ic receivable", 0.85, True),
    ("ic payable", 0.85, True),
    ("management fee", 0.90, True),
]

# Accounts matching these keywords are excluded from related party detection
# even if they match a related party keyword (e.g. "Directors and Officers Insurance").
RELATED_PARTY_EXCLUSION_KEYWORDS: list[str] = [
    "insurance",
    "d&o insurance",
    "board of directors fees",
    "board fees",
]


# =============================================================================
# INTERCOMPANY DETECTION (Sprint 526 / Sprint 527 consolidation)
# =============================================================================
# Keywords indicating intercompany accounts for elimination gap analysis.
# Tuple format: (keyword, weight, is_phrase)

INTERCOMPANY_KEYWORDS: list[tuple[str, float, bool]] = [
    ("intercompany", 0.90, False),
    ("ic receivable", 0.85, True),
    ("ic payable", 0.85, True),
    ("due to", 0.80, True),
    ("due from", 0.80, True),
    ("affiliate", 0.85, False),
]


# =============================================================================
# EQUITY SIGNAL DETECTION (Sprint 526 / Sprint 527 consolidation)
# =============================================================================
# Keywords for identifying equity components relevant to going concern
# and solvency analysis (ASC 205-40).
# Tuple format: (keyword, weight, is_phrase)

EQUITY_RETAINED_EARNINGS_KEYWORDS: list[tuple[str, float, bool]] = [
    ("retained earnings", 0.95, True),
    ("accumulated deficit", 0.95, True),
]

EQUITY_DIVIDEND_KEYWORDS: list[tuple[str, float, bool]] = [
    ("dividend", 0.90, False),
]

EQUITY_TREASURY_KEYWORDS: list[tuple[str, float, bool]] = [
    ("treasury", 0.85, False),
]


# =============================================================================
# CONTRA ACCOUNT RECOGNITION (Sprint 530)
# =============================================================================
# Contra accounts carry balances opposite their parent category's normal
# balance direction.  A contra-asset (e.g. Accumulated Depreciation) is
# expected to carry a credit balance; flagging it as "abnormal" is a false
# positive.  These keyword lists are used by `is_contra_account()` to
# invert the expected normal balance before the abnormal balance check.

CONTRA_ASSET_KEYWORDS: list[str] = [
    "accumulated depreciation",
    "accumulated amortization",
    "allowance for",
    "allowance — ",
    "allowance - ",
    "reserve — ",
    "reserve - ",
    "obsolescence reserve",
    "valuation allowance",
    "contra asset",
    "contra-asset",
    "less accumulated",
]

CONTRA_REVENUE_KEYWORDS: list[str] = [
    "sales discount",
    "sales return",
    "discounts and allowance",
    "returns and allowance",
    "contra revenue",
    "contra-revenue",
    "revenue discount",
    "trade discount",
]

CONTRA_EQUITY_KEYWORDS: list[str] = [
    "treasury stock",
    "dividends declared",
    "contra equity",
    "contra-equity",
    "stock subscription receivable",
    "drawing",
    # Sprint 535 P1-1: AOCI accounts carry debit balances (contra to equity)
    "accumulated other comprehensive",
    "other comprehensive income",
    "other comprehensive loss",
    "aoci",
    "oci loss",
]

CONTRA_LIABILITY_KEYWORDS: list[str] = [
    "discount on bonds payable",
    "discount on notes payable",
    "bond discount",
    "debt issuance cost",
    "debt issuance costs",
    "loan origination cost",
    "loan origination costs",
    "contra liability",
    "contra-liability",
]


def is_contra_account(account_name: str, account_type: AccountCategory) -> bool:
    """Return True if the account is a contra account for its parent category.

    Contra accounts carry the opposite of their parent category's normal
    balance.  Recognised patterns:
    - Contra-asset     (credit balance expected): accumulated depreciation, allowances, reserves
    - Contra-liability (debit balance expected): bond discounts, debt issuance costs
    - Contra-revenue   (debit balance expected): sales discounts, returns
    - Contra-equity    (debit balance expected): treasury stock, dividends declared
    """
    lower = account_name.lower()

    if account_type == AccountCategory.ASSET:
        return any(kw in lower for kw in CONTRA_ASSET_KEYWORDS)
    if account_type == AccountCategory.LIABILITY:
        return any(kw in lower for kw in CONTRA_LIABILITY_KEYWORDS)
    if account_type == AccountCategory.REVENUE:
        return any(kw in lower for kw in CONTRA_REVENUE_KEYWORDS)
    if account_type == AccountCategory.EQUITY:
        return any(kw in lower for kw in CONTRA_EQUITY_KEYWORDS)
    return False
