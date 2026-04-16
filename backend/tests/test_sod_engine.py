"""Tests for sod_engine (Sprint 630)."""

from __future__ import annotations

from sod_engine import (
    DEFAULT_SOD_RULES,
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
        # u1 has only JE-01 (one conflict, score 3, but moderate tier — score
        # threshold for high is 6)
        u1_summary = next(s for s in result.user_summaries if s.user_id == "u1")
        assert u1_summary.risk_tier == "moderate"


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
