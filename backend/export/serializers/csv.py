"""
CSV serializers for Paciolus diagnostic exports.

Each function accepts a validated Pydantic input model and returns UTF-8-sig
encoded CSV bytes. The format_variant concept is implicit in having separate
functions for trial_balance, anomalies, preflight_issues, population_profile,
expense_category, and accrual_completeness — all the "diagnostic" CSV flavors.
"""

from collections import Counter
from io import StringIO

from expense_category_engine import CHANGE_BAND_LABELS
from shared.export_schemas import (
    AccrualCompletenessCSVInput,
    ExpenseCategoryCSVInput,
    PopulationProfileCSVInput,
    PreFlightCSVInput,
)
from shared.filenames import number_cell, safe_csv_writer, sanitize_csv_value
from shared.monetary import quantize_monetary
from shared.schemas import AuditResultInput

ALL_ACCOUNTS_REQUIRED = (
    "all_accounts is required to export the trial balance: send the full account list from the analysis "
    "response, not only the flagged accounts."
)


class MissingAccountListError(ValueError):
    """Sprint 884 (OUT-04): a trial balance export needs every account, not only the flagged ones."""

    def __init__(self) -> None:
        super().__init__(ALL_ACCOUNTS_REQUIRED)


def _as_dicts(items: list | None) -> list[dict]:
    """Nested export items (typed models since Sprint 885) as plain dicts."""
    return [i.model_dump(exclude_unset=True) if hasattr(i, "model_dump") else i for i in (items or [])]


def flag_counts(abnormal_balances: list) -> Counter[str]:
    """How many flags each account carries (one per abnormal_balances entry)."""
    return Counter(a.get("account", "Unknown") for a in _as_dicts(abnormal_balances) if isinstance(a, dict))


def flag_label(count: int) -> str:
    return f"Yes ({count})" if count else ""


def _encode_csv(output: StringIO) -> bytes:
    """Encode a StringIO CSV buffer to UTF-8-sig bytes (BOM for Excel compat)."""
    return output.getvalue().encode("utf-8-sig")


def serialize_trial_balance_csv(audit_result: AuditResultInput) -> bytes:
    """Serialize the full trial balance from an audit result into CSV bytes.

    Sprint 884 (OUT-04): one row per account in ``all_accounts`` (every
    account, once), a Flagged column giving each account's flag count, and a
    TOTALS footer that is the sum of the rows as shown (half-up to cents). It
    used to list only flagged accounts above the full ledger's totals.
    Raises ``MissingAccountListError`` when ``all_accounts`` is not supplied.
    """
    if not audit_result.all_accounts:
        raise MissingAccountListError()

    output = StringIO()
    writer = safe_csv_writer(output)

    writer.writerow(
        ["Reference", "Account", "Debit", "Credit", "Net Balance", "Category", "Classification Confidence", "Flagged"]
    )

    classification = audit_result.classification_summary or {}
    category_map = {}
    for category, accounts in classification.items():
        if isinstance(accounts, list):
            for acct in accounts:
                if isinstance(acct, dict):
                    category_map[acct.get("account", "")] = {
                        "category": category,
                        "confidence": acct.get("confidence", 0),
                    }

    flags = flag_counts(audit_result.abnormal_balances)
    total_debit = total_credit = total_net = quantize_monetary(0)
    ref_idx = 1

    for acct in _as_dicts(audit_result.all_accounts):
        if not isinstance(acct, dict):
            continue
        account = acct.get("account", "Unknown")
        debit = quantize_monetary(acct.get("debit"))
        credit = quantize_monetary(acct.get("credit"))
        net = debit - credit
        total_debit += debit
        total_credit += credit
        total_net += net
        category_info = category_map.get(account, {})

        writer.writerow(
            [
                f"TB-{ref_idx:04d}",
                sanitize_csv_value(account),
                number_cell(debit) if debit else "",
                number_cell(credit) if credit else "",
                number_cell(net),
                sanitize_csv_value(category_info.get("category", acct.get("type", "Unknown"))),
                number_cell(category_info.get("confidence", 0), ".0%") if category_info.get("confidence") else "",
                flag_label(flags.get(account, 0)),
            ]
        )
        ref_idx += 1

    writer.writerow([])
    writer.writerow(
        ["TOTALS", "", number_cell(total_debit), number_cell(total_credit), number_cell(total_net), "", "", ""]
    )

    return _encode_csv(output)


def serialize_anomalies_csv(audit_result: AuditResultInput) -> bytes:
    """Serialize anomaly list from an audit result into CSV bytes.

    Material anomalies get TB-M### references; immaterial get TB-I###.
    Includes SUMMARY and optional RISK BREAKDOWN footer sections.
    """
    output = StringIO()
    writer = safe_csv_writer(output)

    writer.writerow(
        [
            "Reference",
            "Account",
            "Category",
            "Issue",
            "Amount",
            "Materiality",
            "Severity",
            "Anomaly Type",
            "Confidence",
        ]
    )

    material_idx = 1
    immaterial_idx = 1

    for anomaly in _as_dicts(audit_result.abnormal_balances):
        if isinstance(anomaly, dict):
            materiality = anomaly.get("materiality", "immaterial")

            if materiality == "material":
                ref_num = f"TB-M{material_idx:03d}"
                material_idx += 1
            else:
                ref_num = f"TB-I{immaterial_idx:03d}"
                immaterial_idx += 1

            writer.writerow(
                [
                    ref_num,
                    sanitize_csv_value(anomaly.get("account", "Unknown")),
                    sanitize_csv_value(anomaly.get("type", "Unknown")),
                    sanitize_csv_value(anomaly.get("issue", "")),
                    number_cell(anomaly.get("amount", 0), ".2f"),
                    materiality.title(),
                    anomaly.get("severity", "low").title(),
                    anomaly.get("anomaly_type", "abnormal_balance"),
                    number_cell(anomaly.get("confidence", 0), ".0%") if anomaly.get("confidence") else "",
                ]
            )

    writer.writerow([])
    writer.writerow(["SUMMARY", "", "", "", "", "", "", "", ""])
    writer.writerow(["Material Count", audit_result.material_count, "", "", "", "", "", "", ""])
    writer.writerow(["Immaterial Count", audit_result.immaterial_count, "", "", "", "", "", "", ""])
    writer.writerow(["Total Anomalies", len(audit_result.abnormal_balances), "", "", "", "", "", "", ""])

    if audit_result.risk_summary:
        writer.writerow([])
        writer.writerow(["RISK BREAKDOWN", "", "", "", "", "", "", "", ""])
        for risk_type, count in audit_result.risk_summary.items():
            if isinstance(count, int) and count > 0:
                writer.writerow([risk_type.replace("_", " ").title(), count, "", "", "", "", "", "", ""])

    return _encode_csv(output)


def serialize_preflight_issues_csv(pf_input: PreFlightCSVInput) -> bytes:
    """Serialize pre-flight quality issues into CSV bytes."""
    output = StringIO()
    writer = safe_csv_writer(output)

    writer.writerow(["Category", "Severity", "Message", "Affected Count", "Remediation"])

    for issue in pf_input.issues:
        if isinstance(issue, dict):
            writer.writerow(
                [
                    sanitize_csv_value(issue.get("category", "").replace("_", " ").title()),
                    issue.get("severity", "").upper(),
                    sanitize_csv_value(issue.get("message", "")),
                    number_cell(issue.get("affected_count", 0)),
                    sanitize_csv_value(issue.get("remediation", "")),
                ]
            )

    return _encode_csv(output)


def serialize_population_profile_csv(pp_input: PopulationProfileCSVInput) -> bytes:
    """Serialize population profile statistics, magnitude distribution, and top accounts into CSV bytes."""
    output = StringIO()
    writer = safe_csv_writer(output)

    # Summary section
    writer.writerow(["TB POPULATION PROFILE"])
    writer.writerow([])
    writer.writerow(["Statistic", "Value"])
    writer.writerow(["Account Count", pp_input.account_count])
    writer.writerow(["Total Absolute Balance", number_cell(pp_input.total_abs_balance, ".2f")])
    writer.writerow(["Mean (Absolute)", number_cell(pp_input.mean_abs_balance, ".2f")])
    writer.writerow(["Median (Absolute)", number_cell(pp_input.median_abs_balance, ".2f")])
    writer.writerow(["Standard Deviation", number_cell(pp_input.std_dev_abs_balance, ".2f")])
    writer.writerow(["Minimum", number_cell(pp_input.min_abs_balance, ".2f")])
    writer.writerow(["Maximum", number_cell(pp_input.max_abs_balance, ".2f")])
    writer.writerow(["P25", number_cell(pp_input.p25, ".2f")])
    writer.writerow(["P75", number_cell(pp_input.p75, ".2f")])
    writer.writerow(["Gini Coefficient", number_cell(pp_input.gini_coefficient, ".4f")])
    writer.writerow(["Gini Interpretation", pp_input.gini_interpretation])
    writer.writerow([])

    # Magnitude distribution
    writer.writerow(["MAGNITUDE DISTRIBUTION"])
    writer.writerow(["Bucket", "Count", "% of Accounts", "Sum of Balances"])
    for b in pp_input.buckets:
        if isinstance(b, dict):
            writer.writerow(
                [
                    sanitize_csv_value(b.get("label", "")),
                    b.get("count", 0),
                    number_cell(b.get("percent_count", 0), ".1f", "%"),
                    number_cell(b.get("sum_abs", 0), ".2f"),
                ]
            )
    writer.writerow([])

    # Top accounts
    writer.writerow(["TOP ACCOUNTS BY ABSOLUTE BALANCE"])
    writer.writerow(["Rank", "Account", "Category", "Net Balance", "Absolute Balance", "% of Total"])
    for t in pp_input.top_accounts:
        if isinstance(t, dict):
            writer.writerow(
                [
                    t.get("rank", ""),
                    sanitize_csv_value(str(t.get("account", ""))),
                    sanitize_csv_value(t.get("category", "Unknown")),
                    number_cell(t.get("net_balance", 0), ".2f"),
                    number_cell(t.get("abs_balance", 0), ".2f"),
                    number_cell(t.get("percent_of_total", 0), ".1f", "%"),
                ]
            )

    return _encode_csv(output)


def serialize_expense_category_csv(ec_input: ExpenseCategoryCSVInput) -> bytes:
    """Serialize expense category analytical procedures into CSV bytes.

    Adapts layout based on whether prior-period comparison data is available.
    """
    output = StringIO()
    writer = safe_csv_writer(output)

    # Summary section
    writer.writerow(["EXPENSE CATEGORY ANALYTICAL PROCEDURES"])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Expenses", number_cell(ec_input.total_expenses, ".2f")])
    writer.writerow(["Total Revenue", number_cell(ec_input.total_revenue, ".2f")])
    writer.writerow(["Revenue Available", "Yes" if ec_input.revenue_available else "No"])
    writer.writerow(["Prior Period Data", "Yes" if ec_input.prior_available else "No"])
    writer.writerow(["Materiality Threshold", number_cell(ec_input.materiality_threshold, ".2f")])
    writer.writerow(["Active Categories", ec_input.category_count])
    # Sprint 887: the thresholds behind the Change Band column, as on screen and in the memo.
    thresholds = ec_input.change_thresholds or {}
    if thresholds:
        writer.writerow(
            [
                "Change Band Thresholds",
                f"{thresholds.get('pct_either', 10):.0f}% and {thresholds.get('pct_both', 20):.0f}% change "
                "(Paciolus defaults); materiality as above",
            ]
        )
    writer.writerow([])

    # Category breakdown
    has_prior = ec_input.prior_available and any(
        isinstance(c, dict) and c.get("prior_amount") is not None for c in ec_input.categories
    )

    if has_prior:
        writer.writerow(["CATEGORY BREAKDOWN"])
        writer.writerow(
            [
                "Category",
                "Amount",
                "% of Revenue",
                "Prior Amount",
                "Dollar Change",
                "% Change",
                "Exceeds Materiality",
                "Change Band",
            ]
        )
    else:
        writer.writerow(["CATEGORY BREAKDOWN"])
        writer.writerow(["Category", "Amount", "% of Revenue"])

    for c in ec_input.categories:
        if isinstance(c, dict):
            amount = c.get("amount", 0)
            pct = c.get("pct_of_revenue")
            pct_str = number_cell(pct, ".2f", "%") if pct is not None else "N/A"

            if has_prior:
                prior_amt = c.get("prior_amount")
                dollar_change = c.get("dollar_change")
                exceeds = c.get("exceeds_threshold", False)
                pct_change = c.get("pct_change")
                band = c.get("change_band")
                writer.writerow(
                    [
                        sanitize_csv_value(c.get("label", "")),
                        number_cell(amount, ".2f"),
                        pct_str,
                        number_cell(prior_amt, ".2f") if prior_amt is not None else "N/A",
                        number_cell(dollar_change, ".2f") if dollar_change is not None else "N/A",
                        number_cell(pct_change, ".2f", "%") if pct_change is not None else "N/A",
                        "Yes" if exceeds else "No",
                        CHANGE_BAND_LABELS.get(band, "N/A") if band else "N/A",
                    ]
                )
            else:
                writer.writerow(
                    [
                        sanitize_csv_value(c.get("label", "")),
                        number_cell(amount, ".2f"),
                        pct_str,
                    ]
                )

    return _encode_csv(output)


def serialize_accrual_completeness_csv(ac_input: AccrualCompletenessCSVInput) -> bytes:
    """Serialize accrual completeness estimator data into CSV bytes."""
    output = StringIO()
    writer = safe_csv_writer(output)

    # Summary section
    writer.writerow(["ACCRUAL COMPLETENESS ESTIMATOR"])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Accrual Accounts Identified", ac_input.accrual_account_count])
    writer.writerow(["Total Accrued Balance", number_cell(ac_input.total_accrued_balance, ".2f")])
    writer.writerow(["Prior Period Data", "Yes" if ac_input.prior_available else "No"])
    if ac_input.prior_operating_expenses is not None:
        writer.writerow(["Prior Operating Expenses", number_cell(ac_input.prior_operating_expenses, ".2f")])
    if ac_input.monthly_run_rate is not None:
        writer.writerow(["Monthly Run-Rate", number_cell(ac_input.monthly_run_rate, ".2f")])
    if ac_input.accrual_to_run_rate_pct is not None:
        writer.writerow(["Accrual-to-Run-Rate %", number_cell(ac_input.accrual_to_run_rate_pct, ".1f", "%")])
    writer.writerow(["Threshold", number_cell(ac_input.threshold_pct, ".0f", "%")])
    writer.writerow(["Below Threshold", "Yes" if ac_input.below_threshold else "No"])
    writer.writerow([])

    # Accrual accounts
    writer.writerow(["ACCRUAL ACCOUNTS"])
    writer.writerow(["Account", "Balance", "Matched Keyword"])
    for a in ac_input.accrual_accounts:
        if isinstance(a, dict):
            writer.writerow(
                [
                    sanitize_csv_value(str(a.get("account_name", ""))),
                    number_cell(a.get("balance", 0), ".2f"),
                    sanitize_csv_value(a.get("matched_keyword", "")),
                ]
            )
    writer.writerow([])

    # Narrative
    if ac_input.narrative:
        writer.writerow(["NARRATIVE"])
        writer.writerow([sanitize_csv_value(ac_input.narrative)])

    return _encode_csv(output)
