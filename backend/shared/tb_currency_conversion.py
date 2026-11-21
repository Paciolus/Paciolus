"""Convenience currency conversion for a trial balance — Sprint 890 (CEO brief 15D, review ST-11).

CEO decision 2026-11-20: every account is converted at one closing rate per currency — the latest
rate in the user's saved rate table — and the result is labelled a **convenience conversion**. It
is not translation under ASC 830 or IAS 21 (which would use average rates for income and expenses
and historical rates for equity). Every converted figure carries the rate, the rate's date and its
source.

Input is typed: ``TBAccountCurrency`` carries each account's net balance and currency, built from
the engine's ``all_accounts`` and the currency column it captured (``account_currencies``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from currency_engine import CurrencyRateTable, ExchangeRate

METHOD = "convenience_single_closing_rate"
LABEL = (
    "Convenience conversion: every account converted at one closing rate per currency (the latest rate in "
    "your rate table). This is not translation under ASC 830 or IAS 21, which would use average rates for "
    "income and expenses and historical rates for equity."
)
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class TBAccountCurrency:
    """One account to convert: its net balance (debit positive) and the currency it is in."""

    account: str
    net_balance: Decimal
    currency: Optional[str]  # None when the file gave no single currency for the account


@dataclass
class ConvertedAccount:
    account: str
    currency: Optional[str]
    original_amount: Decimal
    converted_amount: Optional[Decimal]
    rate: Optional[str]
    rate_date: Optional[str]
    rate_source: Optional[str]
    issue: Optional[str] = None  # "missing_rate" | "no_currency" | "mixed_currency"

    def to_dict(self) -> dict[str, Any]:
        return {
            "account": self.account,
            "currency": self.currency,
            "original_amount": self.original_amount,
            "converted_amount": self.converted_amount,
            "rate": self.rate,
            "rate_date": self.rate_date,
            "rate_source": self.rate_source,
            "issue": self.issue,
        }


@dataclass
class TBCurrencyConversion:
    presentation_currency: str
    rows: list[ConvertedAccount] = field(default_factory=list)
    method: str = METHOD
    label: str = LABEL

    def to_dict(self) -> dict[str, Any]:
        converted = [r for r in self.rows if r.converted_amount is not None]
        return {
            "method": self.method,
            "label": self.label,
            "presentation_currency": self.presentation_currency,
            "converted_count": len(converted),
            "unconverted_count": len(self.rows) - len(converted),
            "rows": [r.to_dict() for r in self.rows],
        }


def closing_rate(table: CurrencyRateTable, from_currency: str) -> Optional[tuple[Decimal, ExchangeRate]]:
    """The latest rate from ``from_currency`` to the presentation currency, with the record it came from.

    A direct pair wins; otherwise the latest inverse pair is inverted. Returns None if neither exists.
    """
    to_currency = table.presentation_currency
    direct = [r for r in table.rates if r.from_currency == from_currency and r.to_currency == to_currency]
    if direct:
        latest = max(direct, key=lambda r: r.effective_date)
        return latest.rate, latest
    inverse = [r for r in table.rates if r.from_currency == to_currency and r.to_currency == from_currency]
    if inverse:
        latest = max(inverse, key=lambda r: r.effective_date)
        return Decimal("1") / latest.rate, latest
    return None


def _source(table: CurrencyRateTable) -> str:
    when = table.uploaded_at.date().isoformat() if table.uploaded_at else "date not recorded"
    return f"Your rate table (uploaded {when})"


def convert_accounts(accounts: list[TBAccountCurrency], table: CurrencyRateTable) -> TBCurrencyConversion:
    presentation = table.presentation_currency
    result = TBCurrencyConversion(presentation_currency=presentation)
    source = _source(table)
    for acct in accounts:
        if acct.currency is None:
            result.rows.append(
                ConvertedAccount(acct.account, None, acct.net_balance, None, None, None, None, issue="no_currency")
            )
            continue
        if acct.currency == "MIXED":
            result.rows.append(
                ConvertedAccount(acct.account, None, acct.net_balance, None, None, None, None, issue="mixed_currency")
            )
            continue
        if acct.currency == presentation:
            result.rows.append(
                ConvertedAccount(
                    acct.account, acct.currency, acct.net_balance, acct.net_balance, "1", None, "Same currency"
                )
            )
            continue
        found = closing_rate(table, acct.currency)
        if found is None:
            result.rows.append(
                ConvertedAccount(
                    acct.account, acct.currency, acct.net_balance, None, None, None, None, issue="missing_rate"
                )
            )
            continue
        rate, record = found
        converted = (acct.net_balance * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
        result.rows.append(
            ConvertedAccount(
                account=acct.account,
                currency=acct.currency,
                original_amount=acct.net_balance,
                converted_amount=converted,
                rate=format(record.rate if record.from_currency == acct.currency else rate, "f"),
                rate_date=record.effective_date.isoformat(),
                rate_source=source,
            )
        )
    return result


def accounts_with_currencies(result: dict[str, Any]) -> list[TBAccountCurrency]:
    """Typed inputs from the engine's ``all_accounts`` and ``account_currencies``."""
    currencies: dict[str, list[str]] = result.get("account_currencies") or {}
    out: list[TBAccountCurrency] = []
    for a in result.get("all_accounts") or []:
        found = currencies.get(a["account"], [])
        currency = found[0] if len(found) == 1 else ("MIXED" if len(found) > 1 else None)
        net = Decimal(str(a["debit"])) - Decimal(str(a["credit"]))
        out.append(TBAccountCurrency(account=a["account"], net_balance=net, currency=currency))
    return out
