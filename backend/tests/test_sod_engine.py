"""Tests for sod_engine (Sprint 630)."""

from __future__ import annotations

from sod_engine import (
    DEFAULT_SOD_RULES,
    HIGH_CONFLICT_TIER_REASON,
    RolePermission,
    SodRule,
    SodSeverity,
    UserRoleAssignment,
    analyze_segregation_of_duties,
    sod_result_to_csv,
)

# =============================================================================
# Single-user single-conflict
# =============================================================================


class TestSingleConflict:
    def test_je_create_and_post_triggers_je01(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Alice", role_codes=["accountant"])]
        roles = [RolePermission(role_code="accountant", permissions=["JE_create", "JE_post"])]
        result = analyze_segregation_of_duties(users, roles)
        assert result.users_with_conflicts == 1
        assert any(c.rule_code == "JE-01" for c in result.conflicts)
        je01 = next(c for c in result.conflicts if c.rule_code == "JE-01")
        assert je01.severity == SodSeverity.HIGH

    def test_no_conflict_when_only_one_permission(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Bob", role_codes=["clerk"])]
        roles = [RolePermission(role_code="clerk", permissions=["JE_create"])]
        result = analyze_segregation_of_duties(users, roles)
        assert result.users_with_conflicts == 0
        assert result.conflicts == []

    def test_normalized_permission_matching(self):
        """Permission strings are case- and whitespace-insensitive."""
        users = [UserRoleAssignment(user_id="u1", user_name="Eve", role_codes=["accountant"])]
        roles = [RolePermission(role_code="accountant", permissions=["  JE Create ", "je post"])]
        result = analyze_segregation_of_duties(users, roles)
        assert any(c.rule_code == "JE-01" for c in result.conflicts)


# =============================================================================
# Multi-user / multi-conflict
# =============================================================================


class TestMultiConflict:
    def test_user_with_multiple_conflicts_gets_multiple_rules(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Mallory", role_codes=["super"])]
        roles = [
            RolePermission(
                role_code="super",
                permissions=[
                    "vendor_create",
                    "ap_invoice_create",
                    "ap_payment_release",
                    "je_create",
                    "je_post",
                ],
            )
        ]
        result = analyze_segregation_of_duties(users, roles)
        # Should trigger AP-01 (vendor + AP), AP-02 (invoice + payment), JE-01
        rule_codes = {c.rule_code for c in result.conflicts}
        assert {"AP-01", "AP-02", "JE-01"}.issubset(rule_codes)
        # Single user → all attributed to u1
        assert all(c.user_id == "u1" for c in result.conflicts)

    def test_users_ranked_by_risk_score_descending(self):
        users = [
            UserRoleAssignment(user_id="low", user_name="Low Risk", role_codes=["clerk"]),
            UserRoleAssignment(user_id="high", user_name="High Risk", role_codes=["super"]),
        ]
        roles = [
            RolePermission(role_code="clerk", permissions=["ap_invoice_create"]),
            RolePermission(
                role_code="super",
                permissions=["ap_invoice_create", "ap_payment_release", "vendor_create"],
            ),
        ]
        result = analyze_segregation_of_duties(users, roles)
        # Ranked descending — high-risk user should be first
        assert result.user_summaries[0].user_id == "high"
        assert result.user_summaries[0].risk_tier == "high"
        # Low-risk has no conflicts
        assert result.user_summaries[1].user_id == "low"
        assert result.user_summaries[1].conflict_count == 0
        assert result.user_summaries[1].risk_tier == "low"


# =============================================================================
# Triggering permissions / roles enrichment
# =============================================================================


class TestTriggeringDetail:
    def test_triggering_roles_listed_per_conflict(self):
        users = [UserRoleAssignment(user_id="u1", user_name="X", role_codes=["ap_clerk", "treasury"])]
        roles = [
            RolePermission(role_code="ap_clerk", permissions=["ap_invoice_create"]),
            RolePermission(role_code="treasury", permissions=["ap_payment_release"]),
        ]
        result = analyze_segregation_of_duties(users, roles)
        ap02 = next(c for c in result.conflicts if c.rule_code == "AP-02")
        assert "ap_clerk" in ap02.triggering_roles
        assert "treasury" in ap02.triggering_roles


# =============================================================================
# System admin combinator (ADM-01)
# =============================================================================


class TestSystemAdminCombinator:
    def test_admin_with_transactional_access_triggers_adm01(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Admin", role_codes=["sysadmin", "ap_clerk"])]
        roles = [
            RolePermission(role_code="sysadmin", permissions=["user_admin"]),
            RolePermission(role_code="ap_clerk", permissions=["ap_invoice_create"]),
        ]
        result = analyze_segregation_of_duties(users, roles)
        assert any(c.rule_code == "ADM-01" for c in result.conflicts)

    def test_admin_alone_does_not_trigger_adm01(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Pure Admin", role_codes=["sysadmin"])]
        roles = [RolePermission(role_code="sysadmin", permissions=["user_admin"])]
        result = analyze_segregation_of_duties(users, roles)
        assert not any(c.rule_code == "ADM-01" for c in result.conflicts)


# =============================================================================
# Custom rules
# =============================================================================


class TestCustomRules:
    def test_extra_rules_evaluated_alongside_defaults(self):
        custom = SodRule(
            code="CUSTOM-01",
            title="Custom: foo + bar",
            severity=SodSeverity.LOW,
            permissions_required=frozenset({"foo"}),
            permissions_alternate=frozenset({"bar"}),
        )
        users = [UserRoleAssignment(user_id="u1", user_name="Carol", role_codes=["x"])]
        roles = [RolePermission(role_code="x", permissions=["foo", "bar"])]
        result = analyze_segregation_of_duties(users, roles, extra_rules=[custom])
        assert any(c.rule_code == "CUSTOM-01" for c in result.conflicts)
        assert result.rules_evaluated == len(DEFAULT_SOD_RULES) + 1


# =============================================================================
# Risk tier thresholds
# =============================================================================


class TestRiskTierThresholds:
    def test_high_tier_at_score_6_or_more(self):
        # Two HIGH conflicts (3 + 3 = 6) → high tier
        users = [UserRoleAssignment(user_id="u1", user_name="X", role_codes=["x"])]
        roles = [
            RolePermission(
                role_code="x",
                permissions=["je_create", "je_post", "vendor_create", "ap_invoice_create"],
            )
        ]
        result = analyze_segregation_of_duties(users, roles)
        # JE-01 (high) + AP-01 (high) at minimum
        summary = result.user_summaries[0]
        assert summary.risk_tier == "high"

    def test_low_tier_no_conflicts(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Innocent", role_codes=["read_only"])]
        roles = [RolePermission(role_code="read_only", permissions=["report_view"])]
        result = analyze_segregation_of_duties(users, roles)
        assert result.user_summaries[0].risk_tier == "low"
        assert result.user_summaries[0].conflict_count == 0


# =============================================================================
# Aggregation
# =============================================================================


class TestAggregation:
    def test_aggregate_counts(self):
        users = [
            UserRoleAssignment(user_id="u1", user_name="A", role_codes=["super"]),
            UserRoleAssignment(user_id="u2", user_name="B", role_codes=["clean"]),
        ]
        roles = [
            RolePermission(role_code="super", permissions=["je_create", "je_post"]),
            RolePermission(role_code="clean", permissions=["report_view"]),
        ]
        result = analyze_segregation_of_duties(users, roles)
        assert result.users_evaluated == 2
        assert result.users_with_conflicts == 1
        # u1 has only JE-01 (one HIGH conflict, score 3). Sprint 833 changed
        # this from "moderate" (score band) to "high": any HIGH conflict
        # floors the tier at high (CEO decision on Sprint 827 item D2).
        u1_summary = next(s for s in result.user_summaries if s.user_id == "u1")
        assert u1_summary.risk_score == 3
        assert u1_summary.risk_tier == "high"
        assert result.high_risk_users == 1


# =============================================================================
# HIGH-conflict tier floor (Sprint 833)
# =============================================================================


class TestHighConflictTierFloor:
    def _single_high(self):
        users = [UserRoleAssignment(user_id="u1", user_name="Poster", role_codes=["gl"])]
        roles = [RolePermission(role_code="gl", permissions=["je_create", "je_post"])]
        return analyze_segregation_of_duties(users, roles)

    def test_single_high_conflict_tiers_high_with_reason(self):
        result = self._single_high()
        summary = result.user_summaries[0]
        assert summary.high_severity_count == 1
        assert summary.risk_score == 3  # score unchanged
        assert summary.risk_tier == "high"
        assert summary.risk_tier_reason == HIGH_CONFLICT_TIER_REASON
        assert result.high_risk_users == 1
        d = summary.to_dict()
        assert d["risk_tier"] == "high"
        assert d["risk_tier_reason"] == HIGH_CONFLICT_TIER_REASON

    def test_score_band_high_has_no_floor_reason(self):
        users = [UserRoleAssignment(user_id="u1", user_name="X", role_codes=["x"])]
        roles = [
            RolePermission(
                role_code="x",
                permissions=["je_create", "je_post", "vendor_create", "ap_invoice_create"],
            )
        ]
        summary = analyze_segregation_of_duties(users, roles).user_summaries[0]
        assert summary.risk_score >= 6
        assert summary.risk_tier == "high"
        assert summary.risk_tier_reason is None

    def test_medium_only_user_is_not_floored(self):
        custom = SodRule(
            code="CUSTOM-M",
            title="Custom medium",
            severity=SodSeverity.MEDIUM,
            permissions_required=frozenset({"foo"}),
            permissions_alternate=frozenset({"bar"}),
        )
        users = [UserRoleAssignment(user_id="u1", user_name="M", role_codes=["x"])]
        roles = [RolePermission(role_code="x", permissions=["foo", "bar"])]
        summary = analyze_segregation_of_duties(users, roles, extra_rules=[custom]).user_summaries[0]
        assert summary.high_severity_count == 0
        assert summary.risk_tier == "low"  # score 2
        assert summary.risk_tier_reason is None

    def test_floored_high_user_ranks_above_higher_scoring_moderate(self):
        # Two MEDIUM conflicts = score 4 ("moderate"); one HIGH = score 3
        # but floored "high". The high-tier user must rank first.
        meds = [
            SodRule(
                code=f"CUSTOM-M{i}",
                title="Custom medium",
                severity=SodSeverity.MEDIUM,
                permissions_required=frozenset({f"foo{i}"}),
                permissions_alternate=frozenset({f"bar{i}"}),
            )
            for i in (1, 2)
        ]
        users = [
            UserRoleAssignment(user_id="mod", user_name="Moderate", role_codes=["m"]),
            UserRoleAssignment(user_id="hi", user_name="High", role_codes=["gl"]),
        ]
        roles = [
            RolePermission(role_code="m", permissions=["foo1", "bar1", "foo2", "bar2"]),
            RolePermission(role_code="gl", permissions=["je_create", "je_post"]),
        ]
        result = analyze_segregation_of_duties(users, roles, extra_rules=meds)
        by_id = {s.user_id: s for s in result.user_summaries}
        assert by_id["mod"].risk_score == 4 and by_id["mod"].risk_tier == "moderate"
        assert by_id["hi"].risk_score == 3 and by_id["hi"].risk_tier == "high"
        assert [s.user_id for s in result.user_summaries] == ["hi", "mod"]

    def test_csv_includes_tier_basis(self):
        csv_text = sod_result_to_csv(self._single_high())
        assert "Tier Basis" in csv_text
        assert HIGH_CONFLICT_TIER_REASON in csv_text


# =============================================================================
# CSV export
# =============================================================================


class TestCsvExport:
    def test_csv_contains_summary_and_conflicts_sections(self):
        users = [UserRoleAssignment(user_id="u1", user_name="X", role_codes=["x"])]
        roles = [RolePermission(role_code="x", permissions=["je_create", "je_post"])]
        result = analyze_segregation_of_duties(users, roles)
        csv_text = sod_result_to_csv(result)
        assert "USER RISK SUMMARY" in csv_text
        assert "CONFLICTS" in csv_text
        assert "JE-01" in csv_text
