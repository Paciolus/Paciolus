"""
Per-tool account extraction utilities for Cross-Tool Convergence Index.

Each function extracts unique GL account names from a tool's result dict.
Account names are structural COA metadata (same as lead sheet mappings),
NOT financial data — safe to persist per Zero-Storage policy.

Returns sorted, deduplicated list[str].
"""
from collections.abc import Callable


def _dedupe_sort(accounts: list[str]) -> list[str]:
    """Deduplicate and sort account names, filtering blanks."""
    return sorted({a.strip() for a in accounts if a and a.strip()})


def extract_tb_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from TB Diagnostics (abnormal_balances)."""
    accounts = []
    for item in result.get("abnormal_balances", []):
        acct = item.get("account")
        if acct:
            accounts.append(str(acct))
    return _dedupe_sort(accounts)


def extract_flux_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from Flux Analysis (items with risk)."""
    accounts = []
    for item in result.get("items", []):
        risk = item.get("risk_level", "none")
        if risk and risk != "none":
            acct = item.get("account")
            if acct:
                accounts.append(str(acct))
    return _dedupe_sort(accounts)


def extract_multi_period_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from Multi-Period Comparison (significant_movements)."""
    accounts = []
    for m in result.get("significant_movements", []):
        significance = m.get("significance", "")
        if significance in ("material", "significant"):
            acct = m.get("account_name") or m.get("account")
            if acct:
                accounts.append(str(acct))
    return _dedupe_sort(accounts)


def _extract_testing_accounts(result: dict, field: str = "account") -> list[str]:
    """Generic extractor for testing tools with test_results[].flagged_entries[].entry[field]."""
    accounts = []
    for test_result in result.get("test_results", []):
        for flagged in test_result.get("flagged_entries", []):
            entry = flagged.get("entry", {})
            acct = entry.get(field)
            if acct:
                accounts.append(str(acct))
    return _dedupe_sort(accounts)


def extract_je_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from JE Testing."""
    return _extract_testing_accounts(result, field="account")


def extract_ap_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from AP Testing (gl_account field)."""
    return _extract_testing_accounts(result, field="gl_account")


def extract_revenue_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from Revenue Testing (account_name field)."""
    return _extract_testing_accounts(result, field="account_name")


def extract_ar_aging_accounts(result: dict) -> list[str]:
    """Extract flagged accounts from AR Aging (account_name for TB entries)."""
    return _extract_testing_accounts(result, field="account_name")


# Registry mapping ToolName enum values -> extractor functions
ACCOUNT_EXTRACTORS: dict[str, Callable[[dict], list[str]]] = {
    "trial_balance": extract_tb_accounts,
    "multi_period": extract_multi_period_accounts,
    "journal_entry_testing": extract_je_accounts,
    "ap_testing": extract_ap_accounts,
    "revenue_testing": extract_revenue_accounts,
    "ar_aging": extract_ar_aging_accounts,
    "flux_analysis": extract_flux_accounts,
}
