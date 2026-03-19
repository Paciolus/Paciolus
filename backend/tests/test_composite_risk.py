"""
Tests for Composite Risk Scoring Engine

ISA 315 (Revised 2019) composite risk scoring — structures auditor-provided
risk assessments alongside automated diagnostic data.

Covers:
- compute_combined_risk_level for all risk level combinations
- build_composite_risk_profile with various inputs
- Edge cases: no assessments, all high risk, all low risk, mixed
- Automated data passthrough (TB diagnostic, testing scores, going concern)
- Risk distribution computation
- Overall risk tier computation
- Fraud risk accounting
- Disclaimer always present
- AccountRiskAssessment.to_dict()
- CompositeRiskProfile.to_dict()
"""

from composite_risk_engine import (
    DISCLAIMER,
    RISK_LEVEL_WEIGHTS,
    VALID_ASSERTIONS,
    AccountRiskAssessment,
    CompositeRiskProfile,
    RiskLevel,
    _compute_overall_risk_tier,
    build_composite_risk_profile,
    compute_combined_risk_level,
)

# =============================================================================
# HELPERS
# =============================================================================


def _make_assessment(
    account_name: str = "Revenue",
    assertion: str = "existence",
    inherent_risk: RiskLevel = "low",
    control_risk: RiskLevel = "low",
    fraud_risk_factor: bool = False,
    auditor_notes: str = "",
) -> AccountRiskAssessment:
    """Helper to build an AccountRiskAssessment with defaults."""
    return AccountRiskAssessment(
        account_name=account_name,
        assertion=assertion,
        inherent_risk=inherent_risk,
        control_risk=control_risk,
        fraud_risk_factor=fraud_risk_factor,
        auditor_notes=auditor_notes,
    )


# =============================================================================
# TEST: compute_combined_risk_level
# =============================================================================


class TestComputeCombinedRiskLevel:
    """Tests for compute_combined_risk_level() — conservative max approach."""

    def test_both_low(self):
        assert compute_combined_risk_level("low", "low") == "low"

    def test_both_moderate(self):
        assert compute_combined_risk_level("moderate", "moderate") == "moderate"

    def test_both_elevated(self):
        assert compute_combined_risk_level("elevated", "elevated") == "elevated"

    def test_both_high(self):
        assert compute_combined_risk_level("high", "high") == "high"

    def test_inherent_higher(self):
        assert compute_combined_risk_level("high", "low") == "high"

    def test_control_higher(self):
        assert compute_combined_risk_level("low", "high") == "high"

    def test_moderate_and_elevated(self):
        assert compute_combined_risk_level("moderate", "elevated") == "elevated"

    def test_elevated_and_moderate(self):
        assert compute_combined_risk_level("elevated", "moderate") == "elevated"

    def test_low_and_high(self):
        assert compute_combined_risk_level("low", "high") == "high"

    def test_low_and_moderate(self):
        assert compute_combined_risk_level("low", "moderate") == "moderate"

    def test_moderate_and_high(self):
        assert compute_combined_risk_level("moderate", "high") == "high"

    def test_elevated_and_high(self):
        assert compute_combined_risk_level("elevated", "high") == "high"

    def test_all_combinations_return_valid_level(self):
        """Exhaustive: every combination returns a valid RiskLevel."""
        levels = ["low", "moderate", "elevated", "high"]
        for inherent in levels:
            for control in levels:
                result = compute_combined_risk_level(inherent, control)
                assert result in levels

    def test_combined_always_gte_both_inputs(self):
        """The combined risk is always >= both inputs (conservative)."""
        levels = ["low", "moderate", "elevated", "high"]
        for inherent in levels:
            for control in levels:
                result = compute_combined_risk_level(inherent, control)
                assert RISK_LEVEL_WEIGHTS[result] >= RISK_LEVEL_WEIGHTS[inherent]
                assert RISK_LEVEL_WEIGHTS[result] >= RISK_LEVEL_WEIGHTS[control]


# =============================================================================
# TEST: _compute_overall_risk_tier
# =============================================================================


class TestComputeOverallRiskTier:
    """Tests for _compute_overall_risk_tier() — summary of auditor inputs."""

    def test_no_assessments_returns_none(self):
        assert _compute_overall_risk_tier([]) is None

    def test_all_low_returns_low(self):
        assessments = [_make_assessment(inherent_risk="low", control_risk="low") for _ in range(5)]
        assert _compute_overall_risk_tier(assessments) == "low"

    def test_any_high_returns_high(self):
        assessments = [
            _make_assessment(inherent_risk="low", control_risk="low"),
            _make_assessment(inherent_risk="low", control_risk="low"),
            _make_assessment(inherent_risk="high", control_risk="low"),
        ]
        assert _compute_overall_risk_tier(assessments) == "high"

    def test_majority_elevated_returns_elevated(self):
        assessments = [
            _make_assessment(inherent_risk="elevated", control_risk="elevated"),
            _make_assessment(inherent_risk="elevated", control_risk="low"),
            _make_assessment(inherent_risk="low", control_risk="low"),
        ]
        # 2/3 are elevated combined => >50% elevated => "elevated"
        assert _compute_overall_risk_tier(assessments) == "elevated"

    def test_majority_moderate_returns_moderate(self):
        assessments = [
            _make_assessment(inherent_risk="moderate", control_risk="low"),
            _make_assessment(inherent_risk="moderate", control_risk="low"),
            _make_assessment(inherent_risk="low", control_risk="low"),
        ]
        # 2/3 are moderate combined => >50% moderate or above => "moderate"
        assert _compute_overall_risk_tier(assessments) == "moderate"

    def test_single_assessment_low(self):
        assessments = [_make_assessment(inherent_risk="low", control_risk="low")]
        assert _compute_overall_risk_tier(assessments) == "low"

    def test_single_assessment_high(self):
        assessments = [_make_assessment(inherent_risk="high", control_risk="moderate")]
        assert _compute_overall_risk_tier(assessments) == "high"

    def test_even_split_moderate_low(self):
        """50/50 moderate/low — moderate count == total/2, not > total/2, so 'low'."""
        assessments = [
            _make_assessment(inherent_risk="moderate", control_risk="low"),
            _make_assessment(inherent_risk="low", control_risk="low"),
        ]
        # 1/2 moderate => not >50% => "low"
        assert _compute_overall_risk_tier(assessments) == "low"


# =============================================================================
# TEST: build_composite_risk_profile — basic cases
# =============================================================================


class TestBuildCompositeRiskProfile:
    """Tests for build_composite_risk_profile() main function."""

    def test_single_low_risk_assessment(self):
        assessments = [_make_assessment(inherent_risk="low", control_risk="low")]
        profile = build_composite_risk_profile(assessments)

        assert profile.total_assessments == 1
        assert profile.high_risk_accounts == 0
        assert profile.fraud_risk_accounts == 0
        assert profile.overall_risk_tier == "low"
        assert profile.risk_distribution == {"low": 1, "moderate": 0, "elevated": 0, "high": 0}

    def test_single_high_risk_assessment(self):
        assessments = [_make_assessment(inherent_risk="high", control_risk="moderate")]
        profile = build_composite_risk_profile(assessments)

        assert profile.total_assessments == 1
        assert profile.high_risk_accounts == 1
        assert profile.overall_risk_tier == "high"
        assert profile.risk_distribution["high"] == 1

    def test_fraud_risk_counted(self):
        assessments = [
            _make_assessment(fraud_risk_factor=True),
            _make_assessment(fraud_risk_factor=False),
            _make_assessment(fraud_risk_factor=True),
        ]
        profile = build_composite_risk_profile(assessments)
        assert profile.fraud_risk_accounts == 2

    def test_mixed_risk_distribution(self):
        assessments = [
            _make_assessment(inherent_risk="low", control_risk="low"),
            _make_assessment(inherent_risk="moderate", control_risk="low"),
            _make_assessment(inherent_risk="elevated", control_risk="low"),
        ]
        profile = build_composite_risk_profile(assessments)
        assert profile.risk_distribution == {
            "low": 1,
            "moderate": 1,
            "elevated": 1,
            "high": 0,
        }
        assert profile.total_assessments == 3

    def test_empty_assessments(self):
        profile = build_composite_risk_profile([])

        assert profile.total_assessments == 0
        assert profile.high_risk_accounts == 0
        assert profile.fraud_risk_accounts == 0
        assert profile.overall_risk_tier is None
        assert profile.risk_distribution == {"low": 0, "moderate": 0, "elevated": 0, "high": 0}

    def test_all_high_risk(self):
        assessments = [
            _make_assessment(inherent_risk="high", control_risk="high"),
            _make_assessment(inherent_risk="high", control_risk="elevated"),
            _make_assessment(inherent_risk="elevated", control_risk="high"),
        ]
        profile = build_composite_risk_profile(assessments)
        assert profile.high_risk_accounts == 3
        assert profile.overall_risk_tier == "high"
        assert profile.risk_distribution["high"] == 3


# =============================================================================
# TEST: Automated data passthrough
# =============================================================================


class TestAutomatedDataPassthrough:
    """Tests that automated data is passed through correctly."""

    def test_tb_diagnostic_score_passthrough(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(assessments, tb_diagnostic_score=75)
        assert profile.tb_diagnostic_score == 75

    def test_tb_diagnostic_tier_passthrough(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(assessments, tb_diagnostic_tier="Elevated")
        assert profile.tb_diagnostic_tier == "Elevated"

    def test_testing_scores_passthrough(self):
        assessments = [_make_assessment()]
        scores = {"je_testing": 82.5, "ap_testing": 91.0}
        profile = build_composite_risk_profile(assessments, testing_scores=scores)
        assert profile.testing_scores == scores

    def test_testing_scores_default_empty(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(assessments)
        assert profile.testing_scores == {}

    def test_testing_scores_none_becomes_empty(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(assessments, testing_scores=None)
        assert profile.testing_scores == {}

    def test_going_concern_indicators_passthrough(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(assessments, going_concern_indicators_triggered=3)
        assert profile.going_concern_indicators_triggered == 3

    def test_all_automated_data_combined(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(
            assessments,
            tb_diagnostic_score=42,
            tb_diagnostic_tier="Moderate",
            testing_scores={"revenue_testing": 67.0},
            going_concern_indicators_triggered=2,
        )
        assert profile.tb_diagnostic_score == 42
        assert profile.tb_diagnostic_tier == "Moderate"
        assert profile.testing_scores == {"revenue_testing": 67.0}
        assert profile.going_concern_indicators_triggered == 2

    def test_none_automated_data_defaults(self):
        assessments = [_make_assessment()]
        profile = build_composite_risk_profile(assessments)
        assert profile.tb_diagnostic_score is None
        assert profile.tb_diagnostic_tier is None
        assert profile.testing_scores == {}
        assert profile.going_concern_indicators_triggered == 0


# =============================================================================
# TEST: Disclaimer always present
# =============================================================================


class TestDisclaimer:
    """The disclaimer must ALWAYS be present in every profile."""

    def test_disclaimer_present_in_profile(self):
        profile = build_composite_risk_profile([_make_assessment()])
        assert profile.disclaimer == DISCLAIMER
        assert "auditor judgment" in profile.disclaimer
        assert "ISA 315" in profile.disclaimer

    def test_disclaimer_present_in_empty_profile(self):
        profile = build_composite_risk_profile([])
        assert profile.disclaimer == DISCLAIMER

    def test_disclaimer_present_in_to_dict(self):
        profile = build_composite_risk_profile([_make_assessment()])
        d = profile.to_dict()
        assert "disclaimer" in d
        assert d["disclaimer"] == DISCLAIMER

    def test_disclaimer_not_evaluative(self):
        """Disclaimer must not use evaluative language."""
        assert "this entity has" not in DISCLAIMER.lower()
        assert "we conclude" not in DISCLAIMER.lower()
        assert "we determine" not in DISCLAIMER.lower()


# =============================================================================
# TEST: AccountRiskAssessment.to_dict()
# =============================================================================


class TestAccountRiskAssessmentToDict:
    """Tests for AccountRiskAssessment.to_dict() serialization."""

    def test_basic_to_dict(self):
        a = _make_assessment(
            account_name="Cash",
            assertion="existence",
            inherent_risk="moderate",
            control_risk="low",
        )
        d = a.to_dict()
        assert d["account_name"] == "Cash"
        assert d["assertion"] == "existence"
        assert d["inherent_risk"] == "moderate"
        assert d["control_risk"] == "low"
        assert d["combined_risk"] == "moderate"  # max of moderate, low
        assert d["fraud_risk_factor"] is False

    def test_to_dict_with_notes(self):
        a = _make_assessment(auditor_notes="Complex estimates present")
        d = a.to_dict()
        assert d["auditor_notes"] == "Complex estimates present"

    def test_to_dict_without_notes(self):
        a = _make_assessment(auditor_notes="")
        d = a.to_dict()
        assert "auditor_notes" not in d

    def test_combined_risk_in_to_dict(self):
        a = _make_assessment(inherent_risk="elevated", control_risk="high")
        d = a.to_dict()
        assert d["combined_risk"] == "high"

    def test_fraud_risk_in_to_dict(self):
        a = _make_assessment(fraud_risk_factor=True)
        d = a.to_dict()
        assert d["fraud_risk_factor"] is True


# =============================================================================
# TEST: CompositeRiskProfile.to_dict()
# =============================================================================


class TestCompositeRiskProfileToDict:
    """Tests for CompositeRiskProfile.to_dict() serialization."""

    def test_to_dict_structure(self):
        assessments = [
            _make_assessment(inherent_risk="moderate", control_risk="low"),
        ]
        profile = build_composite_risk_profile(
            assessments,
            tb_diagnostic_score=55,
            tb_diagnostic_tier="Moderate",
            testing_scores={"je_testing": 80.0},
            going_concern_indicators_triggered=1,
        )
        d = profile.to_dict()

        assert "account_assessments" in d
        assert len(d["account_assessments"]) == 1
        assert d["tb_diagnostic_score"] == 55
        assert d["tb_diagnostic_tier"] == "Moderate"
        assert d["testing_scores"] == {"je_testing": 80.0}
        assert d["going_concern_indicators_triggered"] == 1
        assert d["high_risk_accounts"] == 0
        assert d["fraud_risk_accounts"] == 0
        assert d["total_assessments"] == 1
        assert d["risk_distribution"] == {"low": 0, "moderate": 1, "elevated": 0, "high": 0}
        assert d["overall_risk_tier"] == "moderate"
        assert d["disclaimer"] == DISCLAIMER

    def test_to_dict_empty_profile(self):
        profile = build_composite_risk_profile([])
        d = profile.to_dict()
        assert d["account_assessments"] == []
        assert d["total_assessments"] == 0
        assert d["overall_risk_tier"] is None
        assert d["disclaimer"] == DISCLAIMER

    def test_to_dict_nested_assessments(self):
        """Assessment dicts within to_dict() include combined_risk."""
        assessments = [
            _make_assessment(inherent_risk="high", control_risk="low"),
        ]
        profile = build_composite_risk_profile(assessments)
        d = profile.to_dict()
        assert d["account_assessments"][0]["combined_risk"] == "high"


# =============================================================================
# TEST: VALID_ASSERTIONS constant
# =============================================================================


class TestValidAssertions:
    """Tests for the VALID_ASSERTIONS constant."""

    def test_five_assertions(self):
        assert len(VALID_ASSERTIONS) == 5

    def test_expected_assertions(self):
        expected = {"existence", "completeness", "valuation", "rights", "presentation"}
        assert VALID_ASSERTIONS == expected


# =============================================================================
# TEST: RISK_LEVEL_WEIGHTS constant
# =============================================================================


class TestRiskLevelWeights:
    """Tests for the RISK_LEVEL_WEIGHTS constant."""

    def test_four_levels(self):
        assert len(RISK_LEVEL_WEIGHTS) == 4

    def test_ordering(self):
        assert RISK_LEVEL_WEIGHTS["low"] < RISK_LEVEL_WEIGHTS["moderate"]
        assert RISK_LEVEL_WEIGHTS["moderate"] < RISK_LEVEL_WEIGHTS["elevated"]
        assert RISK_LEVEL_WEIGHTS["elevated"] < RISK_LEVEL_WEIGHTS["high"]

    def test_specific_values(self):
        assert RISK_LEVEL_WEIGHTS["low"] == 1
        assert RISK_LEVEL_WEIGHTS["moderate"] == 2
        assert RISK_LEVEL_WEIGHTS["elevated"] == 3
        assert RISK_LEVEL_WEIGHTS["high"] == 4


# =============================================================================
# TEST: Large input
# =============================================================================


class TestLargeInput:
    """Tests with many assessments to verify scaling behavior."""

    def test_hundred_assessments(self):
        assessments = [
            _make_assessment(
                account_name=f"Account_{i}",
                inherent_risk="moderate",
                control_risk="low",
            )
            for i in range(100)
        ]
        profile = build_composite_risk_profile(assessments)
        assert profile.total_assessments == 100
        assert profile.risk_distribution["moderate"] == 100
        assert profile.overall_risk_tier == "moderate"

    def test_mixed_large_set(self):
        """60% low, 20% moderate, 10% elevated, 10% high."""
        assessments = (
            [_make_assessment(inherent_risk="low", control_risk="low") for _ in range(60)]
            + [_make_assessment(inherent_risk="moderate", control_risk="low") for _ in range(20)]
            + [_make_assessment(inherent_risk="elevated", control_risk="low") for _ in range(10)]
            + [_make_assessment(inherent_risk="high", control_risk="low") for _ in range(10)]
        )
        profile = build_composite_risk_profile(assessments)
        assert profile.total_assessments == 100
        assert profile.high_risk_accounts == 10
        assert profile.overall_risk_tier == "high"  # any high => overall high


# =============================================================================
# TEST: Multiple assertions per account
# =============================================================================


class TestMultipleAssertionsPerAccount:
    """An account can have separate risk assessments per assertion."""

    def test_same_account_different_assertions(self):
        assessments = [
            _make_assessment(account_name="Revenue", assertion="existence", inherent_risk="high"),
            _make_assessment(account_name="Revenue", assertion="completeness", inherent_risk="low"),
            _make_assessment(account_name="Revenue", assertion="valuation", inherent_risk="moderate"),
        ]
        profile = build_composite_risk_profile(assessments)
        assert profile.total_assessments == 3
        assert profile.high_risk_accounts == 1
        assert profile.overall_risk_tier == "high"


# =============================================================================
# TEST: CompositeRiskProfile default construction
# =============================================================================


class TestCompositeRiskProfileDefaults:
    """Tests for default values on CompositeRiskProfile dataclass."""

    def test_default_disclaimer(self):
        profile = CompositeRiskProfile()
        assert profile.disclaimer == DISCLAIMER

    def test_default_empty_fields(self):
        profile = CompositeRiskProfile()
        assert profile.account_assessments == []
        assert profile.tb_diagnostic_score is None
        assert profile.tb_diagnostic_tier is None
        assert profile.testing_scores == {}
        assert profile.going_concern_indicators_triggered == 0
        assert profile.high_risk_accounts == 0
        assert profile.fraud_risk_accounts == 0
        assert profile.total_assessments == 0
        assert profile.risk_distribution == {}
        assert profile.overall_risk_tier is None
