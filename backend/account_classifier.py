"""
Paciolus Account Classifier
Weighted Heuristic Classification for Trial Balance Accounts

Maintains Zero-Storage compliance: all rules loaded at startup,
no persistent state per-request. User overrides are session-only.

See: logs/dev-log.md for IP documentation
"""

import re
from typing import Optional

from classification_rules import (
    AccountCategory,
    NormalBalance,
    ClassificationRule,
    ClassificationResult,
    DEFAULT_RULES,
    ACCOUNT_NUMBER_RANGES,
    NORMAL_BALANCE_MAP,
    CATEGORY_DISPLAY_NAMES,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
)


class AccountClassifier:
    """
    Weighted heuristic classifier for trial balance accounts.

    Algorithm:
    1. Check user overrides first (highest priority)
    2. Extract account number (if present) for supplementary signal
    3. Calculate keyword match scores for each category
    4. Select highest-scoring category
    5. Apply confidence threshold for UNKNOWN fallback

    Zero-Storage: No data persists beyond the request lifecycle.
    """

    def __init__(
        self,
        rules: Optional[list[ClassificationRule]] = None,
        user_overrides: Optional[dict[str, str]] = None
    ):
        """
        Initialize classifier with rules.

        Args:
            rules: Custom classification rules (defaults to DEFAULT_RULES)
            user_overrides: account_name -> category_string mappings (session-level)
        """
        self.rules = rules or DEFAULT_RULES
        self._user_overrides: dict[str, AccountCategory] = {}

        # Parse user overrides from string format
        if user_overrides:
            for account_name, category_str in user_overrides.items():
                try:
                    category = AccountCategory(category_str.lower())
                    self._user_overrides[account_name.lower().strip()] = category
                except ValueError:
                    pass  # Silently ignore invalid categories

        # Pre-compile phrase patterns for efficiency
        self._phrase_patterns: list[tuple[re.Pattern, ClassificationRule]] = []
        self._keyword_rules: list[ClassificationRule] = []

        for rule in self.rules:
            if rule.is_phrase:
                # Use word boundaries for phrase matching
                escaped = re.escape(rule.keyword)
                pattern = re.compile(rf'\b{escaped}\b', re.IGNORECASE)
                self._phrase_patterns.append((pattern, rule))
            else:
                self._keyword_rules.append(rule)

    def _extract_account_number(self, account_name: str) -> Optional[str]:
        """
        Extract leading account number from account name.
        Handles formats: "1000 Cash", "1000-Cash", "1000.00 Cash"
        """
        match = re.match(r'^(\d{3,6})[\s\-\.]', account_name)
        return match.group(1) if match else None

    def _get_number_signal(self, account_number: Optional[str]) -> dict[AccountCategory, float]:
        """Get category weights from account number pattern matching."""
        signals: dict[AccountCategory, float] = {}

        if not account_number:
            return signals

        for start, end, category, weight in ACCOUNT_NUMBER_RANGES:
            if start <= account_number <= end:
                signals[category] = weight
                break  # Only one range match

        return signals

    def _calculate_keyword_scores(
        self,
        account_name: str
    ) -> tuple[dict[AccountCategory, float], list[str]]:
        """
        Calculate weighted scores for each category based on keyword matches.

        Returns:
            Tuple of (category -> score dict, matched keyword list)
        """
        scores: dict[AccountCategory, float] = {cat: 0.0 for cat in AccountCategory}
        matched_keywords: list[str] = []
        account_lower = account_name.lower()

        # Check phrase patterns first (higher specificity)
        for pattern, rule in self._phrase_patterns:
            if pattern.search(account_lower):
                scores[rule.category] += rule.weight
                matched_keywords.append(rule.keyword)

        # Check single keywords
        for rule in self._keyword_rules:
            if rule.keyword in account_lower:
                scores[rule.category] += rule.weight
                matched_keywords.append(rule.keyword)

        return scores, matched_keywords

    def classify(
        self,
        account_name: str,
        net_balance: float = 0.0
    ) -> ClassificationResult:
        """
        Classify an account using weighted heuristics.

        Args:
            account_name: The account name/description
            net_balance: Net balance (debit - credit) for abnormal detection

        Returns:
            ClassificationResult with category, confidence, and abnormal flag
        """
        account_key = account_name.lower().strip()

        # 1. Check user overrides first (highest priority)
        if account_key in self._user_overrides:
            category = self._user_overrides[account_key]
            return ClassificationResult(
                account_name=account_name,
                category=category,
                confidence=1.0,
                normal_balance=NORMAL_BALANCE_MAP[category],
                matched_keywords=["USER_OVERRIDE"],
                is_abnormal=self._is_abnormal(category, net_balance),
                requires_review=False
            )

        # 2. Extract account number for supplementary signal
        account_number = self._extract_account_number(account_name)

        # 3. Calculate keyword scores
        keyword_scores, matched_keywords = self._calculate_keyword_scores(account_name)

        # 4. Add account number signal
        number_signals = self._get_number_signal(account_number)
        for category, weight in number_signals.items():
            keyword_scores[category] += weight
            if weight > 0:
                matched_keywords.append(f"ACCT#{account_number}")

        # 5. Find highest scoring category
        best_category = AccountCategory.UNKNOWN
        best_score = 0.0

        for category, score in keyword_scores.items():
            if category != AccountCategory.UNKNOWN and score > best_score:
                best_score = score
                best_category = category

        # 6. Apply confidence threshold
        if best_score < CONFIDENCE_MEDIUM:
            best_category = AccountCategory.UNKNOWN
            confidence = best_score
        else:
            # Normalize confidence (cap at 1.0)
            confidence = min(best_score, 1.0)

        # 7. Determine normal balance and abnormality
        normal_balance = NORMAL_BALANCE_MAP[best_category]
        is_abnormal = self._is_abnormal(best_category, net_balance)
        requires_review = confidence < CONFIDENCE_HIGH

        return ClassificationResult(
            account_name=account_name,
            category=best_category,
            confidence=round(confidence, 2),
            normal_balance=normal_balance,
            matched_keywords=matched_keywords[:5],  # Top 5 for brevity
            is_abnormal=is_abnormal,
            requires_review=requires_review
        )

    def _is_abnormal(self, category: AccountCategory, net_balance: float) -> bool:
        """
        Determine if the balance direction is abnormal for this category.

        Standard double-entry bookkeeping rules:
        - Assets/Expenses: Normal debit balance (net_balance > 0)
        - Liabilities/Equity/Revenue: Normal credit balance (net_balance < 0)
        """
        if abs(net_balance) < 0.01:  # Zero balance is never abnormal
            return False

        if category == AccountCategory.UNKNOWN:
            return False  # Cannot determine abnormality for unknown

        normal = NORMAL_BALANCE_MAP[category]

        if normal == NormalBalance.DEBIT:
            # Debit accounts should have positive net (debit > credit)
            return net_balance < 0
        else:
            # Credit accounts should have negative net (credit > debit)
            return net_balance > 0

    def get_category_display(self, category: AccountCategory) -> str:
        """Get human-readable category name."""
        return CATEGORY_DISPLAY_NAMES.get(category, "Unknown")

    def add_override(self, account_name: str, category: AccountCategory) -> None:
        """Add a session-level user override mapping."""
        self._user_overrides[account_name.lower().strip()] = category

    def clear_overrides(self) -> None:
        """Clear all user overrides (for session end)."""
        self._user_overrides.clear()


def create_classifier(overrides: Optional[dict[str, str]] = None) -> AccountClassifier:
    """
    Factory function to create a classifier with optional overrides.

    Args:
        overrides: Optional dict of account_name -> category_string mappings

    Returns:
        Configured AccountClassifier instance
    """
    return AccountClassifier(user_overrides=overrides)
