"""Intercompany elimination generators (Sprint 823 item 3) — 4 generators."""

from decimal import Decimal

from intercompany_elimination_engine import EntityAccount, run_intercompany_elimination
from tests.anomaly_framework.fixtures.base_config_tools import intercompany_baseline
from tests.anomaly_framework.generators.config_tool_base import ConfigGenerator, ToolHarness

INTERCOMPANY_HARNESS = ToolHarness(
    tool="intercompany_elimination",
    engine="intercompany_elimination_engine.run_intercompany_elimination",
    baseline=intercompany_baseline,
    run=lambda config: run_intercompany_elimination(config).to_dict(),
)


def _sub_account(config, name: str) -> EntityAccount:
    return next(a for a in config.entities[1].accounts if a.account == name)


def _has_mismatch(result: dict, kind: str) -> bool:
    return any(m["kind"] == kind for m in result["mismatches"])


class IntercompanyNoReciprocalGenerator(ConfigGenerator):
    """Only one side booked: the subsidiary never recorded its payable."""

    name = "ic_no_reciprocal"
    target = "mismatches[kind=no_reciprocal]"
    injected_at = "Sub Co 'Due to Parent' removed"

    def mutate(self, config):
        config.entities[1].accounts.remove(_sub_account(config, "Due to Parent"))

    def detected(self, result):
        return _has_mismatch(result, "no_reciprocal") and not result["summary"]["consolidation_complete"]


class IntercompanyAmountMismatchGenerator(ConfigGenerator):
    """Both sides booked, $5,000 apart (a timing or cut-off difference)."""

    name = "ic_amount_mismatch"
    target = "mismatches[kind=amount_mismatch]"
    injected_at = "Sub Co 'Due to Parent' 45,000 against Parent's 50,000"

    def mutate(self, config):
        _sub_account(config, "Due to Parent").credit = Decimal("45000")

    def detected(self, result):
        return _has_mismatch(result, "amount_mismatch")


class IntercompanyDirectionMismatchGenerator(ConfigGenerator):
    """Both entities book a receivable from each other — same direction."""

    name = "ic_direction_mismatch"
    target = "mismatches[kind=direction_mismatch]"
    injected_at = "Sub Co books 'Due from Parent' (debit) instead of 'Due to Parent'"

    def mutate(self, config):
        account = _sub_account(config, "Due to Parent")
        account.account, account.debit, account.credit = "Due from Parent", Decimal("50000"), Decimal("0")

    def detected(self, result):
        return _has_mismatch(result, "direction_mismatch")


class IntercompanyEliminationDirectionGenerator(ConfigGenerator):
    """I1 (Sprint 827): the fee elimination must debit revenue, credit expense.

    The baseline already has the pair; the injection doubles the fee on both
    sides so the check reads a fresh, known amount. Revenue/expense was
    reversed in both entity orders for the life of the product.
    """

    name = "ic_elimination_direction"
    target = "elimination_journal_entries[revenue debit]"
    injected_at = "management fee raised to 240,000 on both sides"

    def mutate(self, config):
        next(a for a in config.entities[0].accounts if a.account == "Management fee revenue").credit = Decimal("240000")
        _sub_account(config, "Management fee expense").debit = Decimal("240000")

    def detected(self, result):
        return any(
            "revenue" in je["debit_account"].lower()
            and "expense" in je["credit_account"].lower()
            and Decimal(je["amount"]) == Decimal("240000")
            for je in result["elimination_journal_entries"]
        )


INTERCOMPANY_REGISTRY = [
    IntercompanyNoReciprocalGenerator(),
    IntercompanyAmountMismatchGenerator(),
    IntercompanyDirectionMismatchGenerator(),
    IntercompanyEliminationDirectionGenerator(),
]
