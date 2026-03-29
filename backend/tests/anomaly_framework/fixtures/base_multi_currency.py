"""Base multi-currency factory for anomaly testing.

Produces a valid multi-currency trial balance with exchange rates using
Meridian Capital Group naming conventions. TB contains 10 accounts in
USD, EUR, and GBP with matching exchange rates for all foreign currencies.

Key design decisions:
- Presentation currency is USD
- TB has accounts in three currencies: USD (5), EUR (3), GBP (2)
- Rate table has complete coverage for EUR->USD and GBP->USD
- All rates are recent (within 30 days) and realistic
- No unusual currency codes
- Amounts are reasonable business figures
- Rate effective dates are recent weekday dates
"""

# fmt: off
_TB_ROWS: list[dict] = [
    # ── USD accounts ──
    {"Account": "1000", "Account Name": "Cash - Operating (USD)",       "Account Type": "Asset",     "Debit": 167023.00, "Credit": 0.00,     "Currency": "USD"},
    {"Account": "1100", "Account Name": "Accounts Receivable (USD)",    "Account Type": "Asset",     "Debit":  84623.00, "Credit": 0.00,     "Currency": "USD"},
    {"Account": "2000", "Account Name": "Accounts Payable (USD)",       "Account Type": "Liability", "Debit":      0.00, "Credit": 41678.00, "Currency": "USD"},
    {"Account": "4000", "Account Name": "Service Revenue (USD)",        "Account Type": "Revenue",   "Debit":      0.00, "Credit": 98456.00, "Currency": "USD"},
    {"Account": "6000", "Account Name": "Salaries & Wages (USD)",       "Account Type": "Expense",   "Debit":  73123.00, "Credit": 0.00,     "Currency": "USD"},
    # ── EUR accounts ──
    {"Account": "1010", "Account Name": "Cash - Euro Account",          "Account Type": "Asset",     "Debit":  45230.00, "Credit": 0.00,     "Currency": "EUR"},
    {"Account": "1110", "Account Name": "Trade Receivables - Europe",   "Account Type": "Asset",     "Debit":  32150.00, "Credit": 0.00,     "Currency": "EUR"},
    {"Account": "4100", "Account Name": "Consulting Revenue - Europe",  "Account Type": "Revenue",   "Debit":      0.00, "Credit": 67890.00, "Currency": "EUR"},
    # ── GBP accounts ──
    {"Account": "1020", "Account Name": "Cash - Sterling Account",      "Account Type": "Asset",     "Debit":  28750.00, "Credit": 0.00,     "Currency": "GBP"},
    {"Account": "4200", "Account Name": "License Revenue - UK",         "Account Type": "Revenue",   "Debit":      0.00, "Credit": 41325.00, "Currency": "GBP"},
]

_RATE_ROWS: list[dict] = [
    {"From Currency": "EUR", "To Currency": "USD", "Rate": 1.0850, "Effective Date": "2025-06-02"},
    {"From Currency": "GBP", "To Currency": "USD", "Rate": 1.2640, "Effective Date": "2025-06-02"},
]
# fmt: on


def _verify_rate_coverage(tb_rows: list[dict], rate_rows: list[dict], presentation: str) -> None:
    """Raise if any TB currency lacks a rate to presentation currency."""
    tb_currencies = {r["Currency"] for r in tb_rows}
    foreign = tb_currencies - {presentation}
    rate_pairs = {(r["From Currency"], r["To Currency"]) for r in rate_rows}
    for curr in foreign:
        assert (curr, presentation) in rate_pairs, f"Missing rate for {curr}->{presentation}"


# Validate at import time
_verify_rate_coverage(_TB_ROWS, _RATE_ROWS, "USD")


class BaseMultiCurrencyFactory:
    """Factory for clean, fully covered multi-currency TB and rate data."""

    @classmethod
    def as_tb_rows(cls) -> list[dict]:
        """Return trial balance rows as list of dicts."""
        return [dict(r) for r in _TB_ROWS]

    @classmethod
    def tb_column_names(cls) -> list[str]:
        """Return column names for trial balance data."""
        return list(_TB_ROWS[0].keys())

    @classmethod
    def as_rate_rows(cls) -> list[dict]:
        """Return exchange rate rows as list of dicts."""
        return [dict(r) for r in _RATE_ROWS]

    @classmethod
    def rate_column_names(cls) -> list[str]:
        """Return column names for rate table data."""
        return list(_RATE_ROWS[0].keys())
