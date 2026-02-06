"""
Multi-Period Trial Balance Comparison Engine - Sprint 61 / Sprint 63

Compares two or three trial balance datasets at the account level to identify
movements, new/closed accounts, sign changes, and significant variances.
Groups results by lead sheet for organized workpaper presentation.

Sprint 63 addition: Three-way comparison (Prior + Current + Budget/Forecast)
with budget variance analysis.

ZERO-STORAGE COMPLIANCE:
- All trial balances processed in-memory only
- Comparison results are ephemeral (computed on demand)
- No raw account data is stored

GAAP/IFRS Notes:
- ASC 205-10: Comparative financial statements preferred for two periods
- IAS 1.38: Requires comparative information for prior period minimum
- Movement classification supports both frameworks' disclosure requirements
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re

from lead_sheet_mapping import (
    assign_lead_sheet,
    LeadSheet,
    LEAD_SHEET_NAMES,
    LEAD_SHEET_CATEGORY,
)
from classification_rules import AccountCategory


# =============================================================================
# CONSTANTS
# =============================================================================

# Significance thresholds
SIGNIFICANT_VARIANCE_PERCENT = 10.0  # Flag variances > 10%
SIGNIFICANT_VARIANCE_AMOUNT = 10000.0  # Flag variances > $10,000

# Account matching
ABBREVIATION_MAP: dict[str, str] = {
    "a/r": "accounts receivable",
    "a/p": "accounts payable",
    "ar": "accounts receivable",
    "ap": "accounts payable",
    "pp&e": "property plant and equipment",
    "ppe": "property plant and equipment",
    "cogs": "cost of goods sold",
    "sg&a": "selling general and administrative",
    "wip": "work in progress",
    "r&d": "research and development",
    "g&a": "general and administrative",
}

# Characters to strip during normalization
STRIP_PATTERN = re.compile(r"[^a-z0-9\s]")


# =============================================================================
# ENUMS
# =============================================================================

class MovementType(str, Enum):
    """Classification of account movement between periods."""
    NEW_ACCOUNT = "new_account"
    CLOSED_ACCOUNT = "closed_account"
    SIGN_CHANGE = "sign_change"
    INCREASE = "increase"
    DECREASE = "decrease"
    UNCHANGED = "unchanged"


class SignificanceTier(str, Enum):
    """Significance level of an account movement."""
    MATERIAL = "material"          # Exceeds materiality threshold
    SIGNIFICANT = "significant"    # >10% or >$10K but below materiality
    MINOR = "minor"                # Below both thresholds


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AccountMovement:
    """Movement analysis for a single account between two periods."""
    account_name: str
    account_type: str
    prior_balance: float
    current_balance: float
    change_amount: float
    change_percent: Optional[float]
    movement_type: MovementType
    significance: SignificanceTier
    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    is_dormant: bool = False

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "account_type": self.account_type,
            "prior_balance": self.prior_balance,
            "current_balance": self.current_balance,
            "change_amount": self.change_amount,
            "change_percent": self.change_percent,
            "movement_type": self.movement_type.value,
            "significance": self.significance.value,
            "lead_sheet": self.lead_sheet,
            "lead_sheet_name": self.lead_sheet_name,
            "lead_sheet_category": self.lead_sheet_category,
            "is_dormant": self.is_dormant,
        }


@dataclass
class LeadSheetMovementSummary:
    """Summary of movements within a single lead sheet."""
    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    prior_total: float
    current_total: float
    net_change: float
    change_percent: Optional[float]
    account_count: int
    movements: list[AccountMovement] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "lead_sheet": self.lead_sheet,
            "lead_sheet_name": self.lead_sheet_name,
            "lead_sheet_category": self.lead_sheet_category,
            "prior_total": self.prior_total,
            "current_total": self.current_total,
            "net_change": self.net_change,
            "change_percent": self.change_percent,
            "account_count": self.account_count,
            "movements": [m.to_dict() for m in self.movements],
        }


@dataclass
class MovementSummary:
    """Complete comparison between two trial balance periods."""
    prior_label: str
    current_label: str
    total_accounts: int
    movements_by_type: dict[str, int] = field(default_factory=dict)
    movements_by_significance: dict[str, int] = field(default_factory=dict)
    all_movements: list[AccountMovement] = field(default_factory=list)
    lead_sheet_summaries: list[LeadSheetMovementSummary] = field(default_factory=list)
    significant_movements: list[AccountMovement] = field(default_factory=list)
    new_accounts: list[str] = field(default_factory=list)
    closed_accounts: list[str] = field(default_factory=list)
    dormant_accounts: list[str] = field(default_factory=list)
    prior_total_debits: float = 0.0
    prior_total_credits: float = 0.0
    current_total_debits: float = 0.0
    current_total_credits: float = 0.0

    def to_dict(self) -> dict:
        return {
            "prior_label": self.prior_label,
            "current_label": self.current_label,
            "total_accounts": self.total_accounts,
            "movements_by_type": self.movements_by_type,
            "movements_by_significance": self.movements_by_significance,
            "all_movements": [m.to_dict() for m in self.all_movements],
            "lead_sheet_summaries": [s.to_dict() for s in self.lead_sheet_summaries],
            "significant_movements": [m.to_dict() for m in self.significant_movements],
            "new_accounts": self.new_accounts,
            "closed_accounts": self.closed_accounts,
            "dormant_accounts": self.dormant_accounts,
            "prior_total_debits": self.prior_total_debits,
            "prior_total_credits": self.prior_total_credits,
            "current_total_debits": self.current_total_debits,
            "current_total_credits": self.current_total_credits,
        }


# =============================================================================
# ACCOUNT NAME NORMALIZATION
# =============================================================================

def normalize_account_name(name: str) -> str:
    """
    Normalize an account name for fuzzy matching between periods.

    Strips whitespace, lowercases, removes special characters,
    and expands common abbreviations.
    """
    normalized = name.lower().strip()

    # Check abbreviation map first (exact match on normalized)
    if normalized in ABBREVIATION_MAP:
        return ABBREVIATION_MAP[normalized]

    # Remove special characters except spaces
    normalized = STRIP_PATTERN.sub("", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Expand abbreviations that appear as parts of longer names
    for abbrev, expansion in ABBREVIATION_MAP.items():
        clean_abbrev = STRIP_PATTERN.sub("", abbrev)
        if clean_abbrev and clean_abbrev in normalized:
            normalized = normalized.replace(clean_abbrev, expansion)

    return normalized


def match_accounts(
    prior_accounts: list[dict],
    current_accounts: list[dict],
) -> list[tuple[Optional[dict], Optional[dict], str]]:
    """
    Match accounts between prior and current trial balances.

    Returns list of (prior_account, current_account, display_name) tuples.
    Unmatched accounts have None for the missing side.
    """
    # Build normalized name → account mapping for both periods
    prior_by_norm: dict[str, dict] = {}
    for acct in prior_accounts:
        name = acct.get("account", "")
        norm = normalize_account_name(name)
        prior_by_norm[norm] = acct

    current_by_norm: dict[str, dict] = {}
    for acct in current_accounts:
        name = acct.get("account", "")
        norm = normalize_account_name(name)
        current_by_norm[norm] = acct

    matched: list[tuple[Optional[dict], Optional[dict], str]] = []
    matched_current_norms: set[str] = set()

    # Match prior accounts to current
    for norm, prior_acct in prior_by_norm.items():
        current_acct = current_by_norm.get(norm)
        display_name = prior_acct.get("account", "")

        if current_acct is not None:
            matched_current_norms.add(norm)
            # Prefer current name for display if available
            display_name = current_acct.get("account", display_name)

        matched.append((prior_acct, current_acct, display_name))

    # Add unmatched current accounts (new accounts)
    for norm, current_acct in current_by_norm.items():
        if norm not in matched_current_norms:
            display_name = current_acct.get("account", "")
            matched.append((None, current_acct, display_name))

    return matched


# =============================================================================
# MOVEMENT CLASSIFICATION
# =============================================================================

def _get_net_balance(account: dict) -> float:
    """Calculate net balance from an account dict."""
    debit = float(account.get("debit", 0) or 0)
    credit = float(account.get("credit", 0) or 0)
    return debit - credit


def calculate_movement(
    prior_balance: float,
    current_balance: float,
    is_new: bool = False,
    is_closed: bool = False,
) -> tuple[MovementType, float, Optional[float]]:
    """
    Classify the movement between prior and current balance.

    Returns:
        (movement_type, change_amount, change_percent)
    """
    change_amount = current_balance - prior_balance

    # Calculate percent change
    if prior_balance != 0:
        change_percent = (change_amount / abs(prior_balance)) * 100
    else:
        change_percent = None

    # Classify movement type
    if is_new:
        return MovementType.NEW_ACCOUNT, change_amount, change_percent

    if is_closed:
        return MovementType.CLOSED_ACCOUNT, change_amount, change_percent

    # Sign change: balance flipped from positive to negative or vice versa
    if prior_balance != 0 and current_balance != 0:
        if (prior_balance > 0) != (current_balance > 0):
            return MovementType.SIGN_CHANGE, change_amount, change_percent

    # Standard movement classification
    if abs(change_amount) < 0.01:  # Effectively unchanged (floating point)
        return MovementType.UNCHANGED, 0.0, 0.0

    if change_amount > 0:
        return MovementType.INCREASE, change_amount, change_percent

    return MovementType.DECREASE, change_amount, change_percent


def classify_significance(
    change_amount: float,
    change_percent: Optional[float],
    materiality_threshold: float = 0.0,
    movement_type: MovementType = MovementType.UNCHANGED,
) -> SignificanceTier:
    """
    Determine the significance tier of a movement.

    Material: exceeds materiality threshold (if set)
    Significant: >10% or >$10K but below materiality
    Minor: below both thresholds
    """
    abs_change = abs(change_amount)

    # New and closed accounts are always at least significant
    if movement_type in (MovementType.NEW_ACCOUNT, MovementType.CLOSED_ACCOUNT):
        if materiality_threshold > 0 and abs_change >= materiality_threshold:
            return SignificanceTier.MATERIAL
        if abs_change >= SIGNIFICANT_VARIANCE_AMOUNT:
            return SignificanceTier.SIGNIFICANT
        return SignificanceTier.SIGNIFICANT  # Always significant regardless of amount

    # Sign changes are always at least significant
    if movement_type == MovementType.SIGN_CHANGE:
        if materiality_threshold > 0 and abs_change >= materiality_threshold:
            return SignificanceTier.MATERIAL
        return SignificanceTier.SIGNIFICANT

    # Material threshold check
    if materiality_threshold > 0 and abs_change >= materiality_threshold:
        return SignificanceTier.MATERIAL

    # Standard significance thresholds
    if abs_change >= SIGNIFICANT_VARIANCE_AMOUNT:
        return SignificanceTier.SIGNIFICANT
    if change_percent is not None and abs(change_percent) >= SIGNIFICANT_VARIANCE_PERCENT:
        return SignificanceTier.SIGNIFICANT

    return SignificanceTier.MINOR


# =============================================================================
# LEAD SHEET GROUPING
# =============================================================================

def _get_lead_sheet_info(
    account_name: str,
    account_type: str,
) -> tuple[str, str, str]:
    """
    Get lead sheet assignment for an account.

    Returns (lead_sheet_letter, lead_sheet_name, lead_sheet_category).
    """
    try:
        category = AccountCategory(account_type)
    except ValueError:
        category = AccountCategory.UNKNOWN

    assignment = assign_lead_sheet(account_name, category)
    return (
        assignment.lead_sheet.value,
        LEAD_SHEET_NAMES[assignment.lead_sheet],
        LEAD_SHEET_CATEGORY[assignment.lead_sheet],
    )


def _group_movements_by_lead_sheet(
    movements: list[AccountMovement],
) -> list[LeadSheetMovementSummary]:
    """Group account movements by their lead sheet assignment."""
    groups: dict[str, list[AccountMovement]] = {}

    for movement in movements:
        ls = movement.lead_sheet
        if ls not in groups:
            groups[ls] = []
        groups[ls].append(movement)

    summaries: list[LeadSheetMovementSummary] = []

    for ls_letter in sorted(groups.keys()):
        ls_movements = groups[ls_letter]
        first = ls_movements[0]

        prior_total = sum(m.prior_balance for m in ls_movements)
        current_total = sum(m.current_balance for m in ls_movements)
        net_change = current_total - prior_total

        if prior_total != 0:
            change_percent = (net_change / abs(prior_total)) * 100
        else:
            change_percent = None

        summaries.append(LeadSheetMovementSummary(
            lead_sheet=ls_letter,
            lead_sheet_name=first.lead_sheet_name,
            lead_sheet_category=first.lead_sheet_category,
            prior_total=prior_total,
            current_total=current_total,
            net_change=net_change,
            change_percent=change_percent,
            account_count=len(ls_movements),
            movements=ls_movements,
        ))

    return summaries


# =============================================================================
# MAIN COMPARISON FUNCTION
# =============================================================================

def compare_trial_balances(
    prior_accounts: list[dict],
    current_accounts: list[dict],
    prior_label: str = "Prior Period",
    current_label: str = "Current Period",
    materiality_threshold: float = 0.0,
) -> MovementSummary:
    """
    Compare two trial balance datasets at the account level.

    Args:
        prior_accounts: List of account dicts from prior period.
            Each dict must have 'account', 'debit', 'credit', 'type' keys.
        current_accounts: List of account dicts from current period.
            Same structure as prior_accounts.
        prior_label: Display label for the prior period (e.g., "FY2024").
        current_label: Display label for the current period (e.g., "FY2025").
        materiality_threshold: Dollar threshold for material classification.

    Returns:
        MovementSummary with all movements classified and grouped by lead sheet.
    """
    matched = match_accounts(prior_accounts, current_accounts)

    all_movements: list[AccountMovement] = []
    type_counts: dict[str, int] = {mt.value: 0 for mt in MovementType}
    sig_counts: dict[str, int] = {st.value: 0 for st in SignificanceTier}
    new_accounts: list[str] = []
    closed_accounts: list[str] = []
    dormant_accounts: list[str] = []

    for prior_acct, current_acct, display_name in matched:
        is_new = prior_acct is None
        is_closed = current_acct is None

        prior_balance = _get_net_balance(prior_acct) if prior_acct else 0.0
        current_balance = _get_net_balance(current_acct) if current_acct else 0.0

        # Get account type from whichever side is available
        if current_acct:
            account_type = current_acct.get("type", "unknown")
        elif prior_acct:
            account_type = prior_acct.get("type", "unknown")
        else:
            account_type = "unknown"

        # Classify movement
        movement_type, change_amount, change_percent = calculate_movement(
            prior_balance, current_balance, is_new, is_closed
        )

        # Classify significance
        significance = classify_significance(
            change_amount, change_percent, materiality_threshold, movement_type
        )

        # Get lead sheet info
        ls_letter, ls_name, ls_category = _get_lead_sheet_info(
            display_name, account_type
        )

        # Detect dormant accounts (unchanged with zero balance)
        is_dormant = (
            movement_type == MovementType.UNCHANGED
            and abs(current_balance) < 0.01
            and abs(prior_balance) < 0.01
        )

        movement = AccountMovement(
            account_name=display_name,
            account_type=account_type,
            prior_balance=prior_balance,
            current_balance=current_balance,
            change_amount=change_amount,
            change_percent=change_percent,
            movement_type=movement_type,
            significance=significance,
            lead_sheet=ls_letter,
            lead_sheet_name=ls_name,
            lead_sheet_category=ls_category,
            is_dormant=is_dormant,
        )

        all_movements.append(movement)

        # Track counts
        type_counts[movement_type.value] += 1
        sig_counts[significance.value] += 1

        # Track lists
        if is_new:
            new_accounts.append(display_name)
        elif is_closed:
            closed_accounts.append(display_name)
        if is_dormant:
            dormant_accounts.append(display_name)

    # Calculate totals
    prior_total_debits = sum(
        float(a.get("debit", 0) or 0) for a in prior_accounts
    )
    prior_total_credits = sum(
        float(a.get("credit", 0) or 0) for a in prior_accounts
    )
    current_total_debits = sum(
        float(a.get("debit", 0) or 0) for a in current_accounts
    )
    current_total_credits = sum(
        float(a.get("credit", 0) or 0) for a in current_accounts
    )

    # Group by lead sheet
    lead_sheet_summaries = _group_movements_by_lead_sheet(all_movements)

    # Filter significant movements
    significant = [
        m for m in all_movements
        if m.significance in (SignificanceTier.MATERIAL, SignificanceTier.SIGNIFICANT)
    ]
    # Sort by absolute change amount descending
    significant.sort(key=lambda m: abs(m.change_amount), reverse=True)

    return MovementSummary(
        prior_label=prior_label,
        current_label=current_label,
        total_accounts=len(all_movements),
        movements_by_type=type_counts,
        movements_by_significance=sig_counts,
        all_movements=all_movements,
        lead_sheet_summaries=lead_sheet_summaries,
        significant_movements=significant,
        new_accounts=new_accounts,
        closed_accounts=closed_accounts,
        dormant_accounts=dormant_accounts,
        prior_total_debits=prior_total_debits,
        prior_total_credits=prior_total_credits,
        current_total_debits=current_total_debits,
        current_total_credits=current_total_credits,
    )


# =============================================================================
# THREE-WAY COMPARISON (Sprint 63)
# =============================================================================

@dataclass
class BudgetVariance:
    """Budget variance data for a single account."""
    budget_balance: float
    variance_amount: float  # current - budget
    variance_percent: Optional[float]
    variance_significance: SignificanceTier

    def to_dict(self) -> dict:
        return {
            "budget_balance": self.budget_balance,
            "variance_amount": self.variance_amount,
            "variance_percent": self.variance_percent,
            "variance_significance": self.variance_significance.value,
        }


@dataclass
class ThreeWayLeadSheetSummary:
    """Lead sheet summary with optional budget totals."""
    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    prior_total: float
    current_total: float
    net_change: float
    change_percent: Optional[float]
    budget_total: Optional[float]
    budget_variance: Optional[float]
    budget_variance_percent: Optional[float]
    account_count: int

    def to_dict(self) -> dict:
        d: dict = {
            "lead_sheet": self.lead_sheet,
            "lead_sheet_name": self.lead_sheet_name,
            "lead_sheet_category": self.lead_sheet_category,
            "prior_total": self.prior_total,
            "current_total": self.current_total,
            "net_change": self.net_change,
            "change_percent": self.change_percent,
            "budget_total": self.budget_total,
            "budget_variance": self.budget_variance,
            "budget_variance_percent": self.budget_variance_percent,
            "account_count": self.account_count,
        }
        return d


@dataclass
class ThreeWayMovementSummary:
    """
    Complete three-way comparison: Prior vs Current vs Budget.

    Wraps a standard two-way MovementSummary and adds budget variance data.
    """
    prior_label: str
    current_label: str
    budget_label: str
    total_accounts: int
    movements_by_type: dict[str, int] = field(default_factory=dict)
    movements_by_significance: dict[str, int] = field(default_factory=dict)
    # Each movement dict includes budget_variance (may be None if no budget match)
    all_movements: list[dict] = field(default_factory=list)
    lead_sheet_summaries: list[ThreeWayLeadSheetSummary] = field(default_factory=list)
    significant_movements: list[dict] = field(default_factory=list)
    new_accounts: list[str] = field(default_factory=list)
    closed_accounts: list[str] = field(default_factory=list)
    dormant_accounts: list[str] = field(default_factory=list)
    prior_total_debits: float = 0.0
    prior_total_credits: float = 0.0
    current_total_debits: float = 0.0
    current_total_credits: float = 0.0
    budget_total_debits: float = 0.0
    budget_total_credits: float = 0.0
    # Budget-specific aggregates
    budget_variances_by_significance: dict[str, int] = field(default_factory=dict)
    accounts_over_budget: int = 0
    accounts_under_budget: int = 0
    accounts_on_budget: int = 0

    def to_dict(self) -> dict:
        return {
            "prior_label": self.prior_label,
            "current_label": self.current_label,
            "budget_label": self.budget_label,
            "total_accounts": self.total_accounts,
            "movements_by_type": self.movements_by_type,
            "movements_by_significance": self.movements_by_significance,
            "all_movements": self.all_movements,
            "lead_sheet_summaries": [s.to_dict() for s in self.lead_sheet_summaries],
            "significant_movements": self.significant_movements,
            "new_accounts": self.new_accounts,
            "closed_accounts": self.closed_accounts,
            "dormant_accounts": self.dormant_accounts,
            "prior_total_debits": self.prior_total_debits,
            "prior_total_credits": self.prior_total_credits,
            "current_total_debits": self.current_total_debits,
            "current_total_credits": self.current_total_credits,
            "budget_total_debits": self.budget_total_debits,
            "budget_total_credits": self.budget_total_credits,
            "budget_variances_by_significance": self.budget_variances_by_significance,
            "accounts_over_budget": self.accounts_over_budget,
            "accounts_under_budget": self.accounts_under_budget,
            "accounts_on_budget": self.accounts_on_budget,
        }


def compare_three_periods(
    prior_accounts: list[dict],
    current_accounts: list[dict],
    budget_accounts: list[dict],
    prior_label: str = "Prior Year",
    current_label: str = "Current Year",
    budget_label: str = "Budget",
    materiality_threshold: float = 0.0,
) -> ThreeWayMovementSummary:
    """
    Compare three trial balance datasets: Prior vs Current vs Budget/Forecast.

    Performs the standard two-way (prior vs current) comparison first, then
    enriches each account movement with budget variance data.

    Args:
        prior_accounts: List of account dicts from prior period.
        current_accounts: List of account dicts from current period.
        budget_accounts: List of account dicts from budget/forecast.
        prior_label: Display label for prior period.
        current_label: Display label for current period.
        budget_label: Display label for budget/forecast.
        materiality_threshold: Dollar threshold for material classification.

    Returns:
        ThreeWayMovementSummary with movements, budget variances, and lead sheet grouping.
    """
    # Step 1: Run standard two-way comparison
    two_way = compare_trial_balances(
        prior_accounts, current_accounts,
        prior_label, current_label,
        materiality_threshold,
    )

    # Step 2: Build budget lookup by normalized account name
    budget_by_norm: dict[str, dict] = {}
    for acct in budget_accounts:
        name = acct.get("account", "")
        norm = normalize_account_name(name)
        budget_by_norm[norm] = acct

    # Step 3: Enrich each movement with budget variance
    enriched_movements: list[dict] = []
    budget_sig_counts: dict[str, int] = {st.value: 0 for st in SignificanceTier}
    over_budget = 0
    under_budget = 0
    on_budget = 0

    for movement in two_way.all_movements:
        m_dict = movement.to_dict()
        norm = normalize_account_name(movement.account_name)
        budget_acct = budget_by_norm.get(norm)

        if budget_acct is not None:
            budget_balance = _get_net_balance(budget_acct)
            variance_amount = movement.current_balance - budget_balance

            if budget_balance != 0:
                variance_percent = (variance_amount / abs(budget_balance)) * 100
            else:
                variance_percent = None

            variance_sig = classify_significance(
                variance_amount, variance_percent, materiality_threshold
            )

            m_dict["budget_variance"] = BudgetVariance(
                budget_balance=budget_balance,
                variance_amount=variance_amount,
                variance_percent=variance_percent,
                variance_significance=variance_sig,
            ).to_dict()

            budget_sig_counts[variance_sig.value] += 1

            if abs(variance_amount) < 0.01:
                on_budget += 1
            elif variance_amount > 0:
                over_budget += 1
            else:
                under_budget += 1
        else:
            m_dict["budget_variance"] = None

        enriched_movements.append(m_dict)

    # Step 4: Enrich significant movements
    enriched_significant: list[dict] = []
    for movement in two_way.significant_movements:
        m_dict = movement.to_dict()
        norm = normalize_account_name(movement.account_name)
        budget_acct = budget_by_norm.get(norm)

        if budget_acct is not None:
            budget_balance = _get_net_balance(budget_acct)
            variance_amount = movement.current_balance - budget_balance
            if budget_balance != 0:
                variance_percent = (variance_amount / abs(budget_balance)) * 100
            else:
                variance_percent = None
            variance_sig = classify_significance(
                variance_amount, variance_percent, materiality_threshold
            )
            m_dict["budget_variance"] = BudgetVariance(
                budget_balance=budget_balance,
                variance_amount=variance_amount,
                variance_percent=variance_percent,
                variance_significance=variance_sig,
            ).to_dict()
        else:
            m_dict["budget_variance"] = None

        enriched_significant.append(m_dict)

    # Step 5: Build three-way lead sheet summaries
    budget_totals_by_norm: dict[str, float] = {}
    for acct in budget_accounts:
        norm = normalize_account_name(acct.get("account", ""))
        budget_totals_by_norm[norm] = _get_net_balance(acct)

    three_way_ls: list[ThreeWayLeadSheetSummary] = []
    for ls in two_way.lead_sheet_summaries:
        budget_total = 0.0
        for m in ls.movements:
            norm = normalize_account_name(m.account_name)
            budget_total += budget_totals_by_norm.get(norm, 0.0)

        budget_variance = ls.current_total - budget_total
        if budget_total != 0:
            budget_variance_pct = (budget_variance / abs(budget_total)) * 100
        else:
            budget_variance_pct = None

        three_way_ls.append(ThreeWayLeadSheetSummary(
            lead_sheet=ls.lead_sheet,
            lead_sheet_name=ls.lead_sheet_name,
            lead_sheet_category=ls.lead_sheet_category,
            prior_total=ls.prior_total,
            current_total=ls.current_total,
            net_change=ls.net_change,
            change_percent=ls.change_percent,
            budget_total=budget_total,
            budget_variance=budget_variance,
            budget_variance_percent=budget_variance_pct,
            account_count=ls.account_count,
        ))

    # Step 6: Calculate budget totals
    budget_total_debits = sum(
        float(a.get("debit", 0) or 0) for a in budget_accounts
    )
    budget_total_credits = sum(
        float(a.get("credit", 0) or 0) for a in budget_accounts
    )

    return ThreeWayMovementSummary(
        prior_label=two_way.prior_label,
        current_label=two_way.current_label,
        budget_label=budget_label,
        total_accounts=two_way.total_accounts,
        movements_by_type=two_way.movements_by_type,
        movements_by_significance=two_way.movements_by_significance,
        all_movements=enriched_movements,
        lead_sheet_summaries=three_way_ls,
        significant_movements=enriched_significant,
        new_accounts=two_way.new_accounts,
        closed_accounts=two_way.closed_accounts,
        dormant_accounts=two_way.dormant_accounts,
        prior_total_debits=two_way.prior_total_debits,
        prior_total_credits=two_way.prior_total_credits,
        current_total_debits=two_way.current_total_debits,
        current_total_credits=two_way.current_total_credits,
        budget_total_debits=budget_total_debits,
        budget_total_credits=budget_total_credits,
        budget_variances_by_significance=budget_sig_counts,
        accounts_over_budget=over_budget,
        accounts_under_budget=under_budget,
        accounts_on_budget=on_budget,
    )


# =============================================================================
# CSV EXPORT (Sprint 63)
# =============================================================================

def export_movements_csv(
    summary: MovementSummary,
    include_budget: bool = False,
    budget_data: Optional[dict] = None,
) -> str:
    """
    Generate CSV content for movement comparison data.

    Args:
        summary: A MovementSummary from compare_trial_balances().
        include_budget: Whether to include budget columns.
        budget_data: Optional dict mapping account_name → budget_balance.

    Returns:
        CSV string content (encode with utf-8-sig for Excel compatibility).
    """
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Header row
    headers = [
        "Account", "Lead Sheet", "Category", "Prior Balance", "Current Balance",
        "Change Amount", "Change %", "Movement Type", "Significance",
    ]
    if include_budget and budget_data is not None:
        headers.extend(["Budget Balance", "Budget Variance", "Budget Variance %"])
    writer.writerow(headers)

    # Data rows
    for movement in summary.all_movements:
        m = movement.to_dict() if hasattr(movement, "to_dict") else movement
        row = [
            m["account_name"],
            f"{m['lead_sheet']}: {m['lead_sheet_name']}",
            m["lead_sheet_category"],
            f"{m['prior_balance']:.2f}",
            f"{m['current_balance']:.2f}",
            f"{m['change_amount']:.2f}",
            f"{m['change_percent']:.1f}%" if m["change_percent"] is not None else "N/A",
            m["movement_type"],
            m["significance"],
        ]
        if include_budget and budget_data is not None:
            bv = m.get("budget_variance") if isinstance(m, dict) else None
            if bv:
                row.extend([
                    f"{bv['budget_balance']:.2f}",
                    f"{bv['variance_amount']:.2f}",
                    f"{bv['variance_percent']:.1f}%" if bv["variance_percent"] is not None else "N/A",
                ])
            else:
                row.extend(["", "", ""])
        writer.writerow(row)

    # Blank separator
    writer.writerow([])

    # Lead sheet summary rows
    writer.writerow(["=== LEAD SHEET SUMMARY ==="])
    ls_headers = ["Lead Sheet", "Category", "", "Prior Total", "Current Total",
                   "Net Change", "Change %", "", "Account Count"]
    if include_budget and budget_data is not None:
        ls_headers.extend(["Budget Total", "Budget Variance", "Budget Variance %"])
    writer.writerow(ls_headers)

    summaries = summary.lead_sheet_summaries
    for ls in summaries:
        ls_d = ls.to_dict() if hasattr(ls, "to_dict") else ls
        row = [
            f"{ls_d['lead_sheet']}: {ls_d['lead_sheet_name']}",
            ls_d["lead_sheet_category"],
            "",
            f"{ls_d['prior_total']:.2f}",
            f"{ls_d['current_total']:.2f}",
            f"{ls_d['net_change']:.2f}",
            f"{ls_d['change_percent']:.1f}%" if ls_d["change_percent"] is not None else "N/A",
            "",
            str(ls_d["account_count"]),
        ]
        if include_budget and budget_data is not None:
            bt = ls_d.get("budget_total")
            bv = ls_d.get("budget_variance")
            bvp = ls_d.get("budget_variance_percent")
            row.extend([
                f"{bt:.2f}" if bt is not None else "",
                f"{bv:.2f}" if bv is not None else "",
                f"{bvp:.1f}%" if bvp is not None else "N/A",
            ])
        writer.writerow(row)

    # Summary statistics
    writer.writerow([])
    writer.writerow(["=== SUMMARY STATISTICS ==="])
    writer.writerow(["Total Accounts", str(summary.total_accounts if hasattr(summary, "total_accounts") else "")])
    mbt = summary.movements_by_type if hasattr(summary, "movements_by_type") else {}
    for mt_key, mt_val in (mbt.items() if isinstance(mbt, dict) else []):
        writer.writerow([f"  {mt_key}", str(mt_val)])

    return output.getvalue()
