"""Segregation of Duties generators (Sprint 823 item 3) — 5 generators."""

from sod_engine import RolePermission, UserRoleAssignment, analyze_segregation_of_duties
from tests.anomaly_framework.fixtures.base_config_tools import sod_baseline
from tests.anomaly_framework.generators.config_tool_base import ConfigGenerator, ToolHarness


def _run(config) -> dict:
    return analyze_segregation_of_duties(config["users"], config["roles"]).to_dict()


SOD_HARNESS = ToolHarness(
    tool="sod_checker",
    engine="sod_engine.analyze_segregation_of_duties",
    baseline=sod_baseline,
    run=_run,
)


def _has_rule(result: dict, code: str, user_id: str) -> bool:
    return any(c["rule_code"] == code and c["user_id"] == user_id for c in result["conflicts"])


class SodInvoiceAndPayGenerator(ConfigGenerator):
    """AP-02: the AP clerk is also granted the payment-release role."""

    name = "sod_ap_invoice_and_pay"
    target = "conflicts[rule_code=AP-02]"
    injected_at = "u1 (AP_CLERK) also assigned AP_PAYER"

    def mutate(self, config):
        config["users"][0].role_codes.append("AP_PAYER")

    def detected(self, result):
        return _has_rule(result, "AP-02", "u1")


class SodJournalCreateAndApproveGenerator(ConfigGenerator):
    """JE-01: the GL preparer can approve their own entries."""

    name = "sod_je_create_and_approve"
    target = "conflicts[rule_code=JE-01]"
    injected_at = "u3 (GL_PREPARER) also assigned GL_APPROVER"

    def mutate(self, config):
        config["users"][2].role_codes.append("GL_APPROVER")

    def detected(self, result):
        return _has_rule(result, "JE-01", "u3")


class SodAdminWithTransactionalAccessGenerator(ConfigGenerator):
    """ADM-01: the user administrator also posts journal entries."""

    name = "sod_admin_transactional"
    target = "conflicts[rule_code=ADM-01]"
    injected_at = "IT_ADMIN role gains je_create"

    def mutate(self, config):
        config["roles"].append(RolePermission("IT_ADMIN", ["je_create"]))

    def detected(self, result):
        return _has_rule(result, "ADM-01", "u5")


class SodLongFormatRoleRowsGenerator(ConfigGenerator):
    """D1 (Sprint 827): a role whose two conflicting permissions sit on two rows.

    The second row used to overwrite the first, hiding the conflict.
    """

    name = "sod_long_format_role_rows"
    target = "conflicts[rule_code=AP-02]"
    injected_at = "second AP_CLERK row grants ap_payment_release; u1 also listed on a second row"

    def mutate(self, config):
        config["roles"].append(RolePermission("AP_CLERK", ["ap_payment_release"]))
        config["users"].append(UserRoleAssignment("u1", "Avery Clerk", ["AP_CLERK"]))

    def detected(self, result):
        return _has_rule(result, "AP-02", "u1") and result["users_evaluated"] == 5


class SodUnrecognisedPermissionGenerator(ConfigGenerator):
    """D2 (Sprint 827): a permission spelled so no rule can match it.

    A matrix written ``ap.invoice.create`` produced a clean result
    indistinguishable from a genuinely clean one; it must be surfaced.
    """

    name = "sod_unrecognised_permission"
    target = "unmatched_permissions"
    injected_at = "AP_PAYER role gains 'ap.invoice.create'"

    def mutate(self, config):
        config["roles"].append(RolePermission("AP_PAYER", ["ap.invoice.create"]))

    def detected(self, result):
        return "ap.invoice.create" in result["unmatched_permissions"]


SOD_REGISTRY = [
    SodInvoiceAndPayGenerator(),
    SodJournalCreateAndApproveGenerator(),
    SodAdminWithTransactionalAccessGenerator(),
    SodLongFormatRoleRowsGenerator(),
    SodUnrecognisedPermissionGenerator(),
]
