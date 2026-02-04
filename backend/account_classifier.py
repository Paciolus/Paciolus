"""
Weighted heuristic classification for trial balance accounts.

Sprint 31: Classification Intelligence
- Adds suggestion generation for low-confidence classifications
- Implements Levenshtein distance for fuzzy keyword matching
- Returns top 3 alternative classifications when confidence < 50%
"""

import re
from typing import Optional

from classification_rules import (
    AccountCategory,
    NormalBalance,
    ClassificationRule,
    ClassificationResult,
    ClassificationSuggestion,
    DEFAULT_RULES,
    ACCOUNT_NUMBER_RANGES,
    NORMAL_BALANCE_MAP,
    CATEGORY_DISPLAY_NAMES,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
)


# Sprint 31: Threshold for generating suggestions
SUGGESTION_THRESHOLD = 0.5  # Generate suggestions when confidence below 50%


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings.

    Sprint 31: Used for fuzzy keyword matching to improve classification
    suggestions for misspelled or variant account names.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost is 0 if characters match, 1 otherwise
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def fuzzy_match_score(account_name: str, keyword: str, max_distance: int = 2) -> float:
    """
    Calculate fuzzy match score between account name and keyword.

    Returns a score between 0.0 and 1.0 based on Levenshtein distance.
    Returns 0.0 if no reasonable match found.

    Sprint 31: Enables "Did you mean?" suggestions for near-matches.
    """
    account_lower = account_name.lower()
    keyword_lower = keyword.lower()

    # Exact substring match
    if keyword_lower in account_lower:
        return 1.0

    # Check each word in account name for fuzzy match
    words = re.split(r'\W+', account_lower)
    best_score = 0.0

    for word in words:
        if len(word) < 3:  # Skip very short words
            continue

        distance = levenshtein_distance(word, keyword_lower)

        # Only consider matches within max_distance
        if distance <= max_distance:
            # Convert distance to score (closer = higher score)
            max_len = max(len(word), len(keyword_lower))
            score = 1.0 - (distance / max_len)
            best_score = max(best_score, score)

    return best_score


class AccountClassifier:
    """Weighted heuristic classifier for trial balance accounts."""

    def __init__(
        self,
        rules: Optional[list[ClassificationRule]] = None,
        user_overrides: Optional[dict[str, str]] = None
    ):
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
        """Calculate weighted scores for each category based on keyword matches."""
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
        """Classify an account using weighted heuristics."""
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

        # 8. Sprint 31: Generate suggestions for low-confidence classifications
        suggestions: list[ClassificationSuggestion] = []
        if confidence < SUGGESTION_THRESHOLD:
            suggestions = self._generate_suggestions(
                account_name,
                keyword_scores,
                matched_keywords,
                best_category,
                best_score
            )

        return ClassificationResult(
            account_name=account_name,
            category=best_category,
            confidence=round(confidence, 2),
            normal_balance=normal_balance,
            matched_keywords=matched_keywords[:5],  # Top 5 for brevity
            is_abnormal=is_abnormal,
            requires_review=requires_review,
            suggestions=suggestions
        )

    def _is_abnormal(self, category: AccountCategory, net_balance: float) -> bool:
        """Determine if balance direction is abnormal for this category."""
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

    def _generate_suggestions(
        self,
        account_name: str,
        keyword_scores: dict[AccountCategory, float],
        matched_keywords: list[str],
        best_category: AccountCategory,
        best_score: float
    ) -> list[ClassificationSuggestion]:
        """
        Generate alternative classification suggestions for low-confidence accounts.

        Sprint 31: Classification Intelligence feature.
        Returns top 3 alternatives sorted by confidence.
        """
        suggestions: list[ClassificationSuggestion] = []

        # Get all categories with scores, excluding the best one and UNKNOWN
        alternatives = [
            (cat, score) for cat, score in keyword_scores.items()
            if cat != best_category and cat != AccountCategory.UNKNOWN and score > 0
        ]

        # Sort by score descending
        alternatives.sort(key=lambda x: x[1], reverse=True)

        # Take top 3
        for category, score in alternatives[:3]:
            # Find keywords that contributed to this category's score
            category_keywords = [
                rule.keyword for rule in self.rules
                if rule.category == category and rule.keyword.lower() in account_name.lower()
            ]

            # Generate reason based on matched keywords
            if category_keywords:
                reason = f"Contains: {', '.join(category_keywords[:2])}"
            else:
                reason = f"Partial match for {CATEGORY_DISPLAY_NAMES[category]}"

            suggestions.append(ClassificationSuggestion(
                category=category,
                confidence=round(min(score, 1.0), 2),
                reason=reason,
                matched_keywords=category_keywords[:3]
            ))

        # If we have few suggestions, try fuzzy matching for additional ideas
        if len(suggestions) < 3:
            fuzzy_suggestions = self._generate_fuzzy_suggestions(
                account_name,
                best_category,
                [s.category for s in suggestions]
            )
            suggestions.extend(fuzzy_suggestions)
            suggestions = suggestions[:3]  # Keep only top 3

        return suggestions

    def _generate_fuzzy_suggestions(
        self,
        account_name: str,
        exclude_category: AccountCategory,
        exclude_categories: list[AccountCategory]
    ) -> list[ClassificationSuggestion]:
        """
        Generate suggestions using fuzzy (Levenshtein) matching.

        Sprint 31: Handles misspellings and variant account names.
        """
        fuzzy_matches: list[tuple[AccountCategory, float, str]] = []

        for rule in self.rules:
            if rule.category in exclude_categories or rule.category == exclude_category:
                continue

            # Get fuzzy match score
            score = fuzzy_match_score(account_name, rule.keyword)

            if score > 0.6:  # Only consider reasonable fuzzy matches
                fuzzy_matches.append((
                    rule.category,
                    score * rule.weight,  # Weight by rule confidence
                    rule.keyword
                ))

        # Group by category and take best match per category
        category_best: dict[AccountCategory, tuple[float, str]] = {}
        for category, score, keyword in fuzzy_matches:
            if category not in category_best or score > category_best[category][0]:
                category_best[category] = (score, keyword)

        # Convert to suggestions
        suggestions = []
        for category, (score, keyword) in sorted(
            category_best.items(),
            key=lambda x: x[1][0],
            reverse=True
        )[:2]:  # Max 2 fuzzy suggestions
            suggestions.append(ClassificationSuggestion(
                category=category,
                confidence=round(min(score, 0.6), 2),  # Cap fuzzy confidence
                reason=f"Similar to '{keyword}'",
                matched_keywords=[keyword]
            ))

        return suggestions

    def add_override(self, account_name: str, category: AccountCategory) -> None:
        """Add a session-level user override mapping."""
        self._user_overrides[account_name.lower().strip()] = category

    def clear_overrides(self) -> None:
        """Clear all user overrides (for session end)."""
        self._user_overrides.clear()


def create_classifier(overrides: Optional[dict[str, str]] = None) -> AccountClassifier:
    """Factory function to create a classifier with optional overrides."""
    return AccountClassifier(user_overrides=overrides)
