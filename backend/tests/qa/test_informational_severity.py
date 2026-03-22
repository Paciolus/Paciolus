"""
Regression test for informational severity in diagnostic schemas (NEW-003).

Verifies that both AbnormalBalanceResponse and ClassificationIssueResponse
accept severity="informational" without raising a ValidationError.
"""

import pytest
from pydantic import ValidationError

from shared.diagnostic_response_schemas import (
    AbnormalBalanceResponse,
    ClassificationIssueResponse,
)


class TestInformationalSeverity:
    """Verify 'informational' is accepted in diagnostic response schemas."""

    def test_abnormal_balance_accepts_informational(self):
        """AbnormalBalanceResponse should accept severity='informational'."""
        response = AbnormalBalanceResponse(
            account="1000 - Cash",
            type="asset",
            issue="Number gap detected",
            amount=0.0,
            debit=0.0,
            credit=0.0,
            materiality="immaterial",
            category="asset",
            confidence=0.70,
            matched_keywords=[],
            requires_review=False,
            anomaly_type="number_gap",
            severity="informational",
            suggestions=[],
        )
        assert response.severity == "informational"

    def test_classification_issue_accepts_informational(self):
        """ClassificationIssueResponse should accept severity='informational'."""
        response = ClassificationIssueResponse(
            account_number="4500",
            account_name="4500 - Misc Revenue",
            issue_type="number_gap",
            description="Gap of 500 between account 4000 and 4500",
            severity="informational",
            confidence=0.70,
            category="revenue",
            suggested_action="Informational — verify gap is intentional",
        )
        assert response.severity == "informational"

    @pytest.mark.parametrize("severity", ["high", "medium", "low", "informational"])
    def test_all_valid_severities_accepted(self, severity: str):
        """All four severity levels should be accepted."""
        response = ClassificationIssueResponse(
            account_number="1000",
            account_name="1000 - Cash",
            issue_type="test",
            description="Test issue",
            severity=severity,
            confidence=0.90,
            category="asset",
            suggested_action="Test",
        )
        assert response.severity == severity

    def test_invalid_severity_rejected(self):
        """An invalid severity value should raise ValidationError."""
        with pytest.raises(ValidationError):
            ClassificationIssueResponse(
                account_number="1000",
                account_name="1000 - Cash",
                issue_type="test",
                description="Test issue",
                severity="critical",
                confidence=0.90,
                category="asset",
                suggested_action="Test",
            )
