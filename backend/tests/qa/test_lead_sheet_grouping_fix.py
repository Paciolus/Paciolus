"""
Regression tests for lead sheet grouping aggregation (NEW-006).

Verifies that apply_lead_sheet_grouping uses all_accounts when available,
producing correct A–Z aggregated groups instead of one-account-per-sheet.
"""

from shared.tb_post_processor import apply_lead_sheet_grouping


def _make_accounts(n: int) -> list[dict]:
    """Generate n accounts across a few account types."""
    types_cycle = ["asset", "liability", "equity", "revenue", "expense"]
    accounts = []
    for i in range(n):
        acct_type = types_cycle[i % len(types_cycle)]
        accounts.append(
            {
                "account": f"{1000 + i} - Account {i}",
                "debit": 1000.0 * (i + 1),
                "credit": 500.0 * (i + 1),
                "type": acct_type,
            }
        )
    return accounts


def test_groups_all_accounts_not_just_anomalies():
    """With all_accounts present, grouping should cover every account."""
    all_accounts = _make_accounts(20)
    result = {
        "all_accounts": all_accounts,
        "abnormal_balances": [all_accounts[0]],  # Only 1 anomaly
    }

    apply_lead_sheet_grouping(result, materiality_threshold=1000.0)

    grouping = result["lead_sheet_grouping"]
    total_accounts = sum(s["account_count"] for s in grouping["summaries"])
    assert total_accounts == 20, f"Expected 20 accounts grouped, got {total_accounts}"


def test_single_account_produces_one_group():
    """Single-account TB should produce exactly one lead sheet group."""
    result = {
        "all_accounts": [{"account": "1000 - Cash", "debit": 10000.0, "credit": 0.0, "type": "asset"}],
    }

    apply_lead_sheet_grouping(result, materiality_threshold=1000.0)

    grouping = result["lead_sheet_grouping"]
    assert len(grouping["summaries"]) == 1
    assert grouping["summaries"][0]["account_count"] == 1


def test_same_letter_accounts_aggregate():
    """Multiple cash accounts should aggregate into one lead sheet group."""
    result = {
        "all_accounts": [
            {"account": "1000 - Cash", "debit": 10000.0, "credit": 0.0, "type": "asset"},
            {"account": "1001 - Petty Cash", "debit": 500.0, "credit": 0.0, "type": "asset"},
            {"account": "1010 - Savings Account", "debit": 25000.0, "credit": 0.0, "type": "asset"},
        ],
    }

    apply_lead_sheet_grouping(result, materiality_threshold=1000.0)

    grouping = result["lead_sheet_grouping"]
    # All three cash-like accounts should be in the same group (lead sheet A)
    cash_groups = [s for s in grouping["summaries"] if s["lead_sheet"] == "A"]
    assert len(cash_groups) == 1
    assert cash_groups[0]["account_count"] == 3
    assert cash_groups[0]["total_debit"] == 35500.0


def test_fallback_to_abnormal_balances():
    """When all_accounts is missing, falls back to abnormal_balances."""
    result = {
        "abnormal_balances": [
            {
                "account": "1000 - Cash",
                "debit": 10000.0,
                "credit": 0.0,
                "type": "asset",
                "issue": "test",
                "materiality": "material",
                "severity": "high",
                "anomaly_type": "test",
            },
        ],
    }

    apply_lead_sheet_grouping(result, materiality_threshold=1000.0)

    grouping = result["lead_sheet_grouping"]
    total_accounts = sum(s["account_count"] for s in grouping["summaries"])
    assert total_accounts == 1


def test_summed_balances_correct():
    """Verify summed balances across multiple accounts in same group."""
    result = {
        "all_accounts": [
            {"account": "4000 - Sales Revenue", "debit": 0.0, "credit": 100000.0, "type": "revenue"},
            {"account": "4100 - Service Revenue", "debit": 0.0, "credit": 50000.0, "type": "revenue"},
        ],
    }

    apply_lead_sheet_grouping(result, materiality_threshold=1000.0)

    grouping = result["lead_sheet_grouping"]
    # Find the revenue group
    rev_groups = [s for s in grouping["summaries"] if s["account_count"] == 2]
    assert len(rev_groups) == 1
    assert rev_groups[0]["total_credit"] == 150000.0
