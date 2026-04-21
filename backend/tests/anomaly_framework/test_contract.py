"""Sprint 700: unit tests for the generator ↔ engine contract layer.

These tests exercise ``check_contract`` in isolation. The full
cross-registry meta-test lives in ``tests/anomaly_framework/
test_contract_compliance.py`` and walks every annotated generator/engine
pair; that file stays in report-only mode during Sprints B–D and flips
to fail-mode in Sprint E.
"""

from __future__ import annotations

from shared.engine_contract import (
    ContractViolation,
    DetectionPreconditions,
    EngineInputContract,
    GeneratorEvidence,
    check_contract,
)


class TestCheckContractHappyPath:
    def test_all_preconditions_met_returns_empty_list(self):
        contract = EngineInputContract(
            tool="revenue",
            required_columns=frozenset({"Account Name", "Debit", "Credit"}),
            detection_targets={
                "contra_revenue": DetectionPreconditions(
                    requires_columns=frozenset({"Account Name", "Credit"}),
                    account_name_patterns=frozenset({"returns", "allowances"}),
                    scope="standalone",
                    description="ASC 606: Contra-revenue accounts — returns, allowances, refunds.",
                )
            },
        )
        evidence = GeneratorEvidence(
            target_test_key="contra_revenue",
            populates_columns=frozenset({"Account Name", "Debit", "Credit"}),
            account_name_values=frozenset({"Returns and Allowances"}),
            scope="standalone",
        )
        violations = check_contract(contract, evidence, "returns_and_allowances_contra")
        assert violations == []


class TestCheckContractViolationCases:
    def test_unknown_test_key_is_first_class_violation(self):
        contract = EngineInputContract(
            tool="payroll",
            required_columns=frozenset({"Employee ID"}),
            detection_targets={},  # engine declares no tests
        )
        evidence = GeneratorEvidence(
            target_test_key="ghost_employee",
            populates_columns=frozenset({"Employee ID"}),
        )
        violations = check_contract(contract, evidence, "ghost_gen")
        assert len(violations) == 1
        assert violations[0].test_key == "ghost_employee"
        assert "no contract entry" in violations[0].notes

    def test_missing_required_column_surfaces_in_violation(self):
        contract = EngineInputContract(
            tool="revenue",
            required_columns=frozenset({"Account Name"}),
            detection_targets={
                "weekend_revenue": DetectionPreconditions(
                    requires_columns=frozenset({"Account Name", "Date"}),
                )
            },
        )
        evidence = GeneratorEvidence(
            target_test_key="weekend_revenue",
            populates_columns=frozenset({"Account Name"}),  # missing Date
        )
        violations = check_contract(contract, evidence, "sunday_posting")
        assert len(violations) == 1
        assert violations[0].missing_columns == frozenset({"Date"})

    def test_missing_account_name_pattern_surfaces(self):
        contract = EngineInputContract(
            tool="revenue",
            required_columns=frozenset({"Account Name"}),
            detection_targets={
                "contra_revenue": DetectionPreconditions(
                    requires_columns=frozenset({"Account Name"}),
                    account_name_patterns=frozenset({"returns"}),
                )
            },
        )
        evidence = GeneratorEvidence(
            target_test_key="contra_revenue",
            populates_columns=frozenset({"Account Name"}),
            account_name_values=frozenset({"Contra Revenue"}),  # doesn't contain "returns"
        )
        violations = check_contract(contract, evidence, "generic_contra")
        assert len(violations) == 1
        assert violations[0].missing_account_name_patterns == frozenset({"returns"})

    def test_account_name_pattern_match_is_case_insensitive(self):
        """The generator emits 'RETURNS AND ALLOWANCES' (uppercase); the
        precondition lowercase-patterns should still match."""
        contract = EngineInputContract(
            tool="revenue",
            required_columns=frozenset(),
            detection_targets={
                "contra_revenue": DetectionPreconditions(
                    requires_columns=frozenset(),
                    account_name_patterns=frozenset({"returns"}),
                )
            },
        )
        evidence = GeneratorEvidence(
            target_test_key="contra_revenue",
            account_name_values=frozenset({"RETURNS AND ALLOWANCES"}),
        )
        violations = check_contract(contract, evidence, "uppercase_returns")
        assert violations == []

    def test_scope_mismatch_surfaces_in_violation(self):
        contract = EngineInputContract(
            tool="ar_aging",
            required_columns=frozenset(),
            detection_targets={
                "ar_tb_sign_mismatch": DetectionPreconditions(
                    requires_columns=frozenset(),
                    scope="tb",  # engine requires evidence in TB
                )
            },
        )
        evidence = GeneratorEvidence(
            target_test_key="ar_tb_sign_mismatch",
            scope="sub_ledger",  # generator mutates sub-ledger
        )
        violations = check_contract(contract, evidence, "ar_sl_sign")
        assert len(violations) == 1
        assert violations[0].scope_mismatch == ("tb", "sub_ledger")

    def test_scope_either_accepts_any(self):
        contract = EngineInputContract(
            tool="twm",
            required_columns=frozenset(),
            detection_targets={
                "any_boundary": DetectionPreconditions(scope="either"),
            },
        )
        for scope in ("tb", "sub_ledger", "standalone"):
            evidence = GeneratorEvidence(
                target_test_key="any_boundary",
                scope=scope,  # type: ignore[arg-type]
            )
            assert check_contract(contract, evidence, f"gen_{scope}") == []

    def test_multiple_violations_returned_in_one_call(self):
        """Sprint 700 invariant: surface all gaps in one pass so fixers
        can address them together instead of fix-one-see-next."""
        contract = EngineInputContract(
            tool="revenue",
            required_columns=frozenset(),
            detection_targets={
                "contra_revenue": DetectionPreconditions(
                    requires_columns=frozenset({"Account Name", "Date"}),
                    account_name_patterns=frozenset({"returns"}),
                    scope="standalone",
                )
            },
        )
        evidence = GeneratorEvidence(
            target_test_key="contra_revenue",
            populates_columns=frozenset({"Account Name"}),
            account_name_values=frozenset({"Generic Contra"}),
            scope="sub_ledger",
        )
        violations = check_contract(contract, evidence, "messy_gen")
        # One violation record, but it names all three gaps.
        assert len(violations) == 1
        v = violations[0]
        assert v.missing_columns == frozenset({"Date"})
        assert v.missing_account_name_patterns == frozenset({"returns"})
        assert v.scope_mismatch == ("standalone", "sub_ledger")


class TestContractViolationStringRepr:
    def test_str_includes_tool_and_generator(self):
        v = ContractViolation(
            tool="revenue",
            generator_name="returns_contra",
            test_key="contra_revenue",
            missing_columns=frozenset({"Date"}),
        )
        s = str(v)
        assert "revenue/returns_contra" in s
        assert "contra_revenue" in s
        assert "Date" in s
