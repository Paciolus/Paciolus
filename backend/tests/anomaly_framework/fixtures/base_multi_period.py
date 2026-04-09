"""Base multi-period comparison factory for anomaly testing.

Produces two valid, balanced trial balance datasets representing prior and
current periods for Meridian Capital Group. Current-period balances reflect
normal business growth (~5-10% increases) with no significant movements,
new accounts, closed accounts, or sign changes.

Key design decisions:
- 15 accounts covering all five account types
- Both periods are individually balanced (total debits == total credits)
- Growth is organic and consistent (5-10% per account)
- No account appears in only one period
- No balance sign changes (all accounts maintain normal-side balances)
- Account keys use lowercase 'account', 'type' etc. matching compare_trial_balances()
"""

# fmt: off
_PRIOR_PERIOD: list[dict] = [
    # ── Assets ──
    {"account": "1000", "account_name": "Cash - Operating",          "type": "Asset",     "debit": 145230.00, "credit": 0.00},
    {"account": "1100", "account_name": "Accounts Receivable",       "type": "Asset",     "debit":  78412.00, "credit": 0.00},
    {"account": "1300", "account_name": "Inventory",                 "type": "Asset",     "debit":  41350.00, "credit": 0.00},
    {"account": "1500", "account_name": "Property & Equipment",      "type": "Asset",     "debit": 175000.00, "credit": 0.00},
    {"account": "1510", "account_name": "Accumulated Depreciation",  "type": "Asset",     "debit":      0.00, "credit": 56250.00},
    # ── Liabilities ──
    {"account": "2000", "account_name": "Accounts Payable",          "type": "Liability", "debit": 0.00, "credit":  38420.00},
    {"account": "2100", "account_name": "Accrued Salaries",          "type": "Liability", "debit": 0.00, "credit":  24875.00},
    {"account": "2500", "account_name": "Term Loan Payable",         "type": "Liability", "debit": 0.00, "credit": 110000.00},
    # ── Equity ──
    {"account": "3000", "account_name": "Common Stock",              "type": "Equity",    "debit": 0.00, "credit":  50000.00},
    {"account": "3100", "account_name": "Retained Earnings",         "type": "Equity",    "debit": 0.00, "credit": 132847.00},
    # ── Revenue ──
    {"account": "4000", "account_name": "Service Revenue",           "type": "Revenue",   "debit": 0.00, "credit": 105325.00},
    {"account": "4100", "account_name": "Consulting Revenue",        "type": "Revenue",   "debit": 0.00, "credit":  98175.00},
    # ── Expenses ──
    {"account": "6000", "account_name": "Salaries & Wages",          "type": "Expense",   "debit":  89250.00, "credit": 0.00},
    {"account": "6100", "account_name": "Rent Expense",              "type": "Expense",   "debit":  34150.00, "credit": 0.00},
    {"account": "6300", "account_name": "Depreciation Expense",      "type": "Expense",   "debit":  52500.00, "credit": 0.00},
]

_CURRENT_PERIOD: list[dict] = [
    # ── Assets (~7% growth) ──
    {"account": "1000", "account_name": "Cash - Operating",          "type": "Asset",     "debit": 155396.10, "credit": 0.00},
    {"account": "1100", "account_name": "Accounts Receivable",       "type": "Asset",     "debit":  83900.84, "credit": 0.00},
    {"account": "1300", "account_name": "Inventory",                 "type": "Asset",     "debit":  44244.50, "credit": 0.00},
    {"account": "1500", "account_name": "Property & Equipment",      "type": "Asset",     "debit": 183750.00, "credit": 0.00},
    {"account": "1510", "account_name": "Accumulated Depreciation",  "type": "Asset",     "debit":      0.00, "credit": 61875.00},
    # ── Liabilities (~6% growth) ──
    {"account": "2000", "account_name": "Accounts Payable",          "type": "Liability", "debit": 0.00, "credit":  40725.20},
    {"account": "2100", "account_name": "Accrued Salaries",          "type": "Liability", "debit": 0.00, "credit":  26367.50},
    {"account": "2500", "account_name": "Term Loan Payable",         "type": "Liability", "debit": 0.00, "credit": 104500.00},
    # ── Equity (stock unchanged, RE grows) ──
    {"account": "3000", "account_name": "Common Stock",              "type": "Equity",    "debit": 0.00, "credit":  50000.00},
    {"account": "3100", "account_name": "Retained Earnings",         "type": "Equity",    "debit": 0.00, "credit": 150723.74},
    # ── Revenue (~8% growth) ──
    {"account": "4000", "account_name": "Service Revenue",           "type": "Revenue",   "debit": 0.00, "credit": 113751.00},
    {"account": "4100", "account_name": "Consulting Revenue",        "type": "Revenue",   "debit": 0.00, "credit": 106029.00},
    # ── Expenses (~6-8% growth) ──
    {"account": "6000", "account_name": "Salaries & Wages",          "type": "Expense",   "debit":  95497.50, "credit": 0.00},
    {"account": "6100", "account_name": "Rent Expense",              "type": "Expense",   "debit":  36179.00, "credit": 0.00},
    {"account": "6300", "account_name": "Depreciation Expense",      "type": "Expense",   "debit":  55003.50, "credit": 0.00},
]
# fmt: on


def _verify_balance(accounts: list[dict], label: str) -> None:
    """Raise if total debits != total credits."""
    total_debits = sum(a["debit"] for a in accounts)
    total_credits = sum(a["credit"] for a in accounts)
    assert abs(total_debits - total_credits) < 0.01, (
        f"{label} is unbalanced: debits={total_debits}, credits={total_credits}"
    )


# Validate at import time
_verify_balance(_PRIOR_PERIOD, "Prior period")
_verify_balance(_CURRENT_PERIOD, "Current period")


class BaseMultiPeriodFactory:
    """Factory for clean, balanced prior and current period trial balances."""

    @classmethod
    def as_prior_period(cls) -> list[dict]:
        """Return prior period accounts as list of dicts."""
        return [dict(a) for a in _PRIOR_PERIOD]

    @classmethod
    def as_current_period(cls) -> list[dict]:
        """Return current period accounts as list of dicts."""
        return [dict(a) for a in _CURRENT_PERIOD]
