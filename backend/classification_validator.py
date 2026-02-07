"""
Classification Validator — Sprint 95

Structural chart-of-accounts checks integrated into TB Diagnostics (Tool 1).
SCOPE BOUNDARY: Structural checks ONLY — no accounting judgment, no "should be classified as X".

6 checks:
  CV-1: Duplicate Account Numbers
  CV-2: Orphan Accounts (zero balance + zero activity)
  CV-3: Unclassified Accounts (unknown type or lead sheet)
  CV-4: Account Number Gaps (significant sequential gaps)
  CV-5: Inconsistent Naming (pattern violations within lead sheet group)
  CV-6: Sign Anomalies (credit assets, debit liabilities)
"""

import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Optional


class ClassificationIssueType(str, Enum):
    DUPLICATE_NUMBER = "duplicate_number"
    ORPHAN_ACCOUNT = "orphan_account"
    UNCLASSIFIED = "unclassified"
    NUMBER_GAP = "number_gap"
    INCONSISTENT_NAMING = "inconsistent_naming"
    SIGN_ANOMALY = "sign_anomaly"


ISSUE_TYPE_LABELS = {
    ClassificationIssueType.DUPLICATE_NUMBER: "Duplicate Account Numbers",
    ClassificationIssueType.ORPHAN_ACCOUNT: "Orphan Accounts",
    ClassificationIssueType.UNCLASSIFIED: "Unclassified Accounts",
    ClassificationIssueType.NUMBER_GAP: "Account Number Gaps",
    ClassificationIssueType.INCONSISTENT_NAMING: "Inconsistent Naming",
    ClassificationIssueType.SIGN_ANOMALY: "Sign Anomalies",
}


@dataclass
class ClassificationIssue:
    account_number: str
    account_name: str
    issue_type: ClassificationIssueType
    description: str
    severity: str  # "high", "medium", "low"
    confidence: float
    category: str  # account category if known
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["issue_type"] = self.issue_type.value
        return d


@dataclass
class ClassificationResult:
    issues: list[ClassificationIssue] = field(default_factory=list)
    quality_score: float = 100.0
    issue_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "quality_score": round(self.quality_score, 1),
            "issue_counts": self.issue_counts,
            "total_issues": len(self.issues),
        }


# =============================================================================
# Account number extraction helpers
# =============================================================================

_ACCOUNT_NUMBER_PATTERN = re.compile(r'^(\d[\d\-\.]*\d|\d+)')


def extract_account_number(account_name: str) -> Optional[str]:
    """Extract a numeric account number prefix from an account name."""
    m = _ACCOUNT_NUMBER_PATTERN.match(account_name.strip())
    if m:
        return m.group(1).replace("-", "").replace(".", "")
    return None


def extract_numeric_prefix(account_name: str) -> Optional[int]:
    """Extract the leading numeric portion as an integer."""
    num_str = extract_account_number(account_name)
    if num_str:
        try:
            return int(num_str)
        except ValueError:
            return None
    return None


# =============================================================================
# Natural balance expectations by category
# =============================================================================

NATURAL_DEBIT_CATEGORIES = {"asset", "expense"}
NATURAL_CREDIT_CATEGORIES = {"liability", "equity", "revenue"}


# =============================================================================
# Individual checks
# =============================================================================

def check_duplicate_numbers(
    accounts: dict[str, dict[str, float]],
) -> list[ClassificationIssue]:
    """CV-1: Flag accounts sharing same numeric prefix with different names."""
    number_map: dict[str, list[str]] = {}
    for name in accounts:
        num = extract_account_number(name)
        if num:
            number_map.setdefault(num, []).append(name)

    issues = []
    for num, names in number_map.items():
        if len(names) > 1:
            # Only flag if the names are genuinely different (not just whitespace)
            unique_names = set(n.strip().lower() for n in names)
            if len(unique_names) > 1:
                for name in names:
                    issues.append(ClassificationIssue(
                        account_number=num,
                        account_name=name,
                        issue_type=ClassificationIssueType.DUPLICATE_NUMBER,
                        description=f"Account number {num} appears {len(names)} times with different names",
                        severity="high",
                        confidence=0.95,
                        category="",
                        suggested_action="Review for data entry error or chart-of-accounts consolidation",
                    ))
    return issues


def check_orphan_accounts(
    accounts: dict[str, dict[str, float]],
) -> list[ClassificationIssue]:
    """CV-2: Flag accounts with zero balance AND zero activity."""
    issues = []
    for name, balances in accounts.items():
        debit = balances.get("debit", 0.0)
        credit = balances.get("credit", 0.0)
        # Zero balance AND zero activity
        if abs(debit) < 0.01 and abs(credit) < 0.01:
            issues.append(ClassificationIssue(
                account_number=extract_account_number(name) or "",
                account_name=name,
                issue_type=ClassificationIssueType.ORPHAN_ACCOUNT,
                description="Account has zero balance and zero activity",
                severity="medium",
                confidence=0.90,
                category="",
                suggested_action="Review if account is still active; consider removing from chart of accounts",
            ))
    return issues


def check_unclassified_accounts(
    accounts: dict[str, dict[str, float]],
    classifications: dict[str, str],
) -> list[ClassificationIssue]:
    """CV-3: Flag accounts classified as 'unknown' type."""
    issues = []
    for name, balances in accounts.items():
        category = classifications.get(name, "unknown")
        if category in ("unknown", "Unknown", ""):
            debit = balances.get("debit", 0.0)
            credit = balances.get("credit", 0.0)
            net_balance = abs(debit - credit)
            is_material = net_balance >= 1000  # Simple material threshold for classification context

            issues.append(ClassificationIssue(
                account_number=extract_account_number(name) or "",
                account_name=name,
                issue_type=ClassificationIssueType.UNCLASSIFIED,
                description=f"Account could not be classified (balance: ${net_balance:,.2f})",
                severity="high" if is_material else "medium",
                confidence=0.85,
                category="unknown",
                suggested_action="Manually classify account in chart of accounts",
            ))
    return issues


def check_number_gaps(
    accounts: dict[str, dict[str, float]],
    classifications: dict[str, str],
    gap_threshold: int = 100,
) -> list[ClassificationIssue]:
    """CV-4: Detect significant gaps in sequential numbering within same category."""
    # Group accounts by category
    category_numbers: dict[str, list[tuple[int, str]]] = {}
    for name in accounts:
        num = extract_numeric_prefix(name)
        if num is not None:
            cat = classifications.get(name, "unknown")
            category_numbers.setdefault(cat, []).append((num, name))

    issues = []
    for cat, entries in category_numbers.items():
        if cat == "unknown" or len(entries) < 3:
            continue
        sorted_entries = sorted(entries, key=lambda x: x[0])
        for i in range(1, len(sorted_entries)):
            prev_num, prev_name = sorted_entries[i - 1]
            curr_num, curr_name = sorted_entries[i]
            gap = curr_num - prev_num
            if gap >= gap_threshold:
                issues.append(ClassificationIssue(
                    account_number=str(curr_num),
                    account_name=curr_name,
                    issue_type=ClassificationIssueType.NUMBER_GAP,
                    description=f"Gap of {gap} between account {prev_num} and {curr_num} in {cat} range",
                    severity="low",
                    confidence=0.70,
                    category=cat,
                    suggested_action="Informational — verify gap is intentional",
                ))
    return issues


def check_inconsistent_naming(
    accounts: dict[str, dict[str, float]],
    classifications: dict[str, str],
    similarity_threshold: float = 0.6,
    min_group_size: int = 4,
) -> list[ClassificationIssue]:
    """CV-5: Detect naming pattern violations within same category group."""
    # Group account names by category
    category_names: dict[str, list[str]] = {}
    for name in accounts:
        cat = classifications.get(name, "unknown")
        if cat != "unknown":
            category_names.setdefault(cat, []).append(name)

    issues = []
    for cat, names in category_names.items():
        if len(names) < min_group_size:
            continue

        # Find the most common prefix pattern (first word)
        prefixes = []
        for n in names:
            # Strip account number prefix if present
            clean = re.sub(r'^\d[\d\-\.]*\s*[-–—]?\s*', '', n.strip())
            first_word = clean.split()[0] if clean.split() else ""
            if first_word:
                prefixes.append(first_word.lower())

        if not prefixes:
            continue

        # Find dominant prefix (at least 40% of accounts)
        prefix_counts = Counter(prefixes)
        most_common_prefix, most_common_count = prefix_counts.most_common(1)[0]
        if most_common_count < len(names) * 0.4:
            continue

        # Flag accounts that don't match the dominant pattern
        for i, name in enumerate(names):
            if i < len(prefixes) and prefixes[i] != most_common_prefix:
                # Verify it's not similar (avoid false positives)
                sim = SequenceMatcher(None, prefixes[i], most_common_prefix).ratio()
                if sim < similarity_threshold:
                    issues.append(ClassificationIssue(
                        account_number=extract_account_number(name) or "",
                        account_name=name,
                        issue_type=ClassificationIssueType.INCONSISTENT_NAMING,
                        description=f"Naming pattern differs from group norm ('{most_common_prefix}' prefix expected)",
                        severity="low",
                        confidence=0.65,
                        category=cat,
                        suggested_action="Verify naming convention consistency in chart of accounts",
                    ))
    return issues


def check_sign_anomalies(
    accounts: dict[str, dict[str, float]],
    classifications: dict[str, str],
) -> list[ClassificationIssue]:
    """CV-6: Assets with credit balances, liabilities with debit balances."""
    issues = []
    for name, balances in accounts.items():
        debit = balances.get("debit", 0.0)
        credit = balances.get("credit", 0.0)
        net_balance = debit - credit

        if abs(net_balance) < 0.01:
            continue

        category = classifications.get(name, "unknown")
        if category == "unknown":
            continue

        # Check for reversed signs
        has_anomaly = False
        expected = ""
        actual = ""

        if category in NATURAL_DEBIT_CATEGORIES and net_balance < 0:
            has_anomaly = True
            expected = "debit"
            actual = "credit"
        elif category in NATURAL_CREDIT_CATEGORIES and net_balance > 0:
            has_anomaly = True
            expected = "credit"
            actual = "debit"

        if has_anomaly:
            issues.append(ClassificationIssue(
                account_number=extract_account_number(name) or "",
                account_name=name,
                issue_type=ClassificationIssueType.SIGN_ANOMALY,
                description=f"{category.title()} account has {actual} balance (expected {expected})",
                severity="medium",
                confidence=0.80,
                category=category,
                suggested_action="Verify account balance direction is correct for its classification",
            ))
    return issues


# =============================================================================
# Main entry point
# =============================================================================

def run_classification_validation(
    accounts: dict[str, dict[str, float]],
    classifications: dict[str, str],
    gap_threshold: int = 100,
) -> ClassificationResult:
    """Run all 6 structural classification checks.

    Args:
        accounts: {account_name: {"debit": float, "credit": float}}
        classifications: {account_name: category_string} from classifier
        gap_threshold: minimum gap to flag for CV-4

    Returns:
        ClassificationResult with issues and quality score
    """
    all_issues: list[ClassificationIssue] = []

    # CV-1: Duplicate Account Numbers
    all_issues.extend(check_duplicate_numbers(accounts))

    # CV-2: Orphan Accounts
    all_issues.extend(check_orphan_accounts(accounts))

    # CV-3: Unclassified Accounts
    all_issues.extend(check_unclassified_accounts(accounts, classifications))

    # CV-4: Account Number Gaps
    all_issues.extend(check_number_gaps(accounts, classifications, gap_threshold))

    # CV-5: Inconsistent Naming
    all_issues.extend(check_inconsistent_naming(accounts, classifications))

    # CV-6: Sign Anomalies
    all_issues.extend(check_sign_anomalies(accounts, classifications))

    # Calculate quality score (100 = perfect, reduced by issues)
    # High = -5, Medium = -3, Low = -1
    penalty = 0.0
    for issue in all_issues:
        if issue.severity == "high":
            penalty += 5.0
        elif issue.severity == "medium":
            penalty += 3.0
        else:
            penalty += 1.0

    quality_score = max(0.0, 100.0 - penalty)

    # Issue counts by type
    issue_counts: dict[str, int] = {}
    for issue in all_issues:
        key = issue.issue_type.value
        issue_counts[key] = issue_counts.get(key, 0) + 1

    return ClassificationResult(
        issues=all_issues,
        quality_score=quality_score,
        issue_counts=issue_counts,
    )
