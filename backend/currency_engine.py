"""
Currency Conversion Engine — Sprint 257

Converts multi-currency trial balance amounts to a single presentation currency
for diagnostic analysis. Implements the closing-rate MVP defined in RFC.

Key design decisions:
- Closing rate only (average/historical deferred)
- Vectorized Pandas operations for 500K-row TBs
- Decimal precision (4 internal, 2 display)
- Zero-Storage: rate tables session-scoped, never persisted
"""

import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Optional

import pandas as pd

from shared.column_detector import ColumnFieldConfig, ColumnPattern, detect_columns

# ISO 4217 currency codes (common subset for validation)
ISO_4217_CODES: set[str] = {
    "AED", "AFN", "ALL", "AMD", "ANG", "AOA", "ARS", "AUD", "AWG", "AZN",
    "BAM", "BBD", "BDT", "BGN", "BHD", "BIF", "BMD", "BND", "BOB", "BRL",
    "BSD", "BTN", "BWP", "BYN", "BZD", "CAD", "CDF", "CHF", "CLP", "CNY",
    "COP", "CRC", "CUP", "CVE", "CZK", "DJF", "DKK", "DOP", "DZD", "EGP",
    "ERN", "ETB", "EUR", "FJD", "FKP", "GBP", "GEL", "GHS", "GIP", "GMD",
    "GNF", "GTQ", "GYD", "HKD", "HNL", "HRK", "HTG", "HUF", "IDR", "ILS",
    "INR", "IQD", "IRR", "ISK", "JMD", "JOD", "JPY", "KES", "KGS", "KHR",
    "KMF", "KPW", "KRW", "KWD", "KYD", "KZT", "LAK", "LBP", "LKR", "LRD",
    "LSL", "LYD", "MAD", "MDL", "MGA", "MKD", "MMK", "MNT", "MOP", "MRU",
    "MUR", "MVR", "MWK", "MXN", "MYR", "MZN", "NAD", "NGN", "NIO", "NOK",
    "NPR", "NZD", "OMR", "PAB", "PEN", "PGK", "PHP", "PKR", "PLN", "PYG",
    "QAR", "RON", "RSD", "RUB", "RWF", "SAR", "SBD", "SCR", "SDG", "SEK",
    "SGD", "SHP", "SLE", "SOS", "SRD", "SSP", "STN", "SVC", "SYP", "SZL",
    "THB", "TJS", "TMT", "TND", "TOP", "TRY", "TTD", "TWD", "TZS", "UAH",
    "UGX", "USD", "UYU", "UZS", "VES", "VND", "VUV", "WST", "XAF", "XCD",
    "XOF", "XPF", "YER", "ZAR", "ZMW", "ZWL",
}

# Maximum rows in a rate table upload
MAX_RATE_TABLE_ROWS = 10_000

# Stale rate threshold (days)
STALE_RATE_DAYS = 90

# Decimal precision for internal calculations
INTERNAL_PRECISION = Decimal("0.0001")
DISPLAY_PRECISION = Decimal("0.01")

# Severity thresholds (percentage of category total)
SEVERITY_HIGH_THRESHOLD = Decimal("0.05")   # > 5%
SEVERITY_MEDIUM_THRESHOLD = Decimal("0.01") # > 1%


# =============================================================================
# COLUMN DETECTION — Currency column patterns
# =============================================================================

CURRENCY_COLUMN_PATTERNS: list[ColumnPattern] = [
    (r"^currency$", 0.98, True),
    (r"^currency\s*code$", 0.95, True),
    (r"^ccy$", 0.90, True),
    (r"^curr$", 0.85, True),
    (r"^fx\s*currency$", 0.90, True),
    (r"^reporting\s*currency$", 0.88, True),
    (r"^trans(?:action)?\s*currency$", 0.88, True),
    (r"currency", 0.70, False),
]

CURRENCY_FIELD_CONFIG = ColumnFieldConfig(
    field_name="currency_column",
    patterns=CURRENCY_COLUMN_PATTERNS,
    required=False,
    missing_note="No currency column detected — assuming single-currency TB",
    priority=65,
)


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ExchangeRate:
    """A single exchange rate entry."""
    effective_date: date
    from_currency: str
    to_currency: str
    rate: Decimal

    def to_dict(self) -> dict:
        return {
            "effective_date": self.effective_date.isoformat(),
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "rate": str(self.rate),
        }


@dataclass
class CurrencyRateTable:
    """Session-scoped rate table (Zero-Storage compliant)."""
    rates: list[ExchangeRate] = field(default_factory=list)
    uploaded_at: Optional[datetime] = None
    presentation_currency: str = "USD"

    def to_dict(self) -> dict:
        return {
            "rate_count": len(self.rates),
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "presentation_currency": self.presentation_currency,
            "currency_pairs": list({
                f"{r.from_currency}/{r.to_currency}" for r in self.rates
            }),
        }

    def to_storage_dict(self) -> dict:
        """Full serialization for DB session storage (includes all rates)."""
        return {
            "rates": [r.to_dict() for r in self.rates],
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "presentation_currency": self.presentation_currency,
        }

    @classmethod
    def from_storage_dict(cls, data: dict) -> "CurrencyRateTable":
        """Reconstruct from DB session storage dict (Sprint 262)."""
        rates = []
        for r in data.get("rates", []):
            rates.append(ExchangeRate(
                effective_date=date.fromisoformat(r["effective_date"]),
                from_currency=r["from_currency"],
                to_currency=r["to_currency"],
                rate=Decimal(r["rate"]),
            ))
        uploaded_at = None
        if data.get("uploaded_at"):
            uploaded_at = datetime.fromisoformat(data["uploaded_at"])
        return cls(
            rates=rates,
            uploaded_at=uploaded_at,
            presentation_currency=data.get("presentation_currency", "USD"),
        )


@dataclass
class ConversionFlag:
    """A flagged unconverted or partially converted account."""
    account_number: str
    account_name: str
    original_amount: float
    original_currency: str
    issue: str  # "missing_rate" | "missing_currency_code" | "invalid_currency" | "stale_rate"
    severity: str  # "high" | "medium" | "low"

    def to_dict(self) -> dict:
        return {
            "account_number": self.account_number,
            "account_name": self.account_name,
            "original_amount": self.original_amount,
            "original_currency": self.original_currency,
            "issue": self.issue,
            "severity": self.severity,
        }


@dataclass
class ConversionResult:
    """Result of a multi-currency TB conversion."""
    conversion_performed: bool
    presentation_currency: str
    total_accounts: int
    converted_count: int
    unconverted_count: int
    unconverted_items: list[ConversionFlag] = field(default_factory=list)
    currencies_found: list[str] = field(default_factory=list)
    rates_applied: dict[str, str] = field(default_factory=dict)  # "EUR/USD" -> "1.0523"
    balance_check_passed: bool = True
    balance_imbalance: float = 0.0
    conversion_summary: str = ""
    converted_rows: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "conversion_performed": self.conversion_performed,
            "presentation_currency": self.presentation_currency,
            "total_accounts": self.total_accounts,
            "converted_count": self.converted_count,
            "unconverted_count": self.unconverted_count,
            "unconverted_items": [f.to_dict() for f in self.unconverted_items],
            "currencies_found": self.currencies_found,
            "rates_applied": self.rates_applied,
            "balance_check_passed": self.balance_check_passed,
            "balance_imbalance": self.balance_imbalance,
            "conversion_summary": self.conversion_summary,
        }


# =============================================================================
# RATE TABLE VALIDATION
# =============================================================================

class RateValidationError(ValueError):
    """Raised when rate table validation fails."""
    pass


def validate_currency_code(code: str) -> str:
    """Validate and normalize a currency code to uppercase ISO 4217."""
    normalized = code.strip().upper()
    if not re.match(r"^[A-Z]{3}$", normalized):
        raise RateValidationError(
            f"Invalid currency code '{code}': must be 3 uppercase letters (ISO 4217)"
        )
    if normalized not in ISO_4217_CODES:
        raise RateValidationError(
            f"Unknown currency code '{normalized}': not a recognized ISO 4217 code"
        )
    return normalized


def parse_rate_table(rows: list[dict]) -> list[ExchangeRate]:
    """Parse and validate a rate table from CSV/dict rows.

    Expected columns: effective_date, from_currency, to_currency, rate

    Raises:
        RateValidationError: If validation fails
    """
    if not rows:
        raise RateValidationError("Rate table is empty")

    if len(rows) > MAX_RATE_TABLE_ROWS:
        raise RateValidationError(
            f"Rate table exceeds maximum of {MAX_RATE_TABLE_ROWS:,} rows "
            f"(got {len(rows):,})"
        )

    required_columns = {"effective_date", "from_currency", "to_currency", "rate"}
    if rows:
        available = {k.lower().strip() for k in rows[0].keys()}
        missing = required_columns - available
        if missing:
            raise RateValidationError(
                f"Rate table missing required columns: {', '.join(sorted(missing))}"
            )

    rates: list[ExchangeRate] = []
    seen_keys: set[tuple[str, str, str]] = set()
    errors: list[str] = []

    for i, row in enumerate(rows, start=1):
        # Normalize keys to lowercase
        normalized_row = {k.lower().strip(): v for k, v in row.items()}

        # Parse date
        raw_date = str(normalized_row.get("effective_date", "")).strip()
        try:
            if "/" in raw_date:
                parsed_date = datetime.strptime(raw_date, "%m/%d/%Y").date()
            elif "-" in raw_date:
                parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            else:
                errors.append(f"Row {i}: Invalid date format '{raw_date}' (use YYYY-MM-DD or MM/DD/YYYY)")
                continue
        except ValueError:
            errors.append(f"Row {i}: Invalid date '{raw_date}'")
            continue

        # Validate currency codes
        try:
            from_curr = validate_currency_code(str(normalized_row.get("from_currency", "")))
            to_curr = validate_currency_code(str(normalized_row.get("to_currency", "")))
        except RateValidationError as e:
            errors.append(f"Row {i}: {e}")
            continue

        if from_curr == to_curr:
            errors.append(f"Row {i}: from_currency and to_currency are the same ({from_curr})")
            continue

        # Validate rate
        raw_rate = str(normalized_row.get("rate", "")).strip()
        try:
            rate_val = Decimal(raw_rate)
        except (InvalidOperation, ValueError):
            errors.append(f"Row {i}: Invalid rate '{raw_rate}'")
            continue

        if rate_val <= 0:
            errors.append(f"Row {i}: Rate must be positive (got {raw_rate})")
            continue

        # Check duplicates
        key = (parsed_date.isoformat(), from_curr, to_curr)
        if key in seen_keys:
            errors.append(f"Row {i}: Duplicate rate for {from_curr}/{to_curr} on {parsed_date}")
            continue
        seen_keys.add(key)

        rates.append(ExchangeRate(
            effective_date=parsed_date,
            from_currency=from_curr,
            to_currency=to_curr,
            rate=rate_val,
        ))

    if errors:
        # Show first 10 errors
        error_msg = "; ".join(errors[:10])
        if len(errors) > 10:
            error_msg += f" ... and {len(errors) - 10} more errors"
        raise RateValidationError(f"Rate table validation failed: {error_msg}")

    return rates


def parse_single_rate(
    from_currency: str,
    to_currency: str,
    rate: str,
) -> ExchangeRate:
    """Parse and validate a single manual rate entry.

    Raises:
        RateValidationError: If validation fails
    """
    from_curr = validate_currency_code(from_currency)
    to_curr = validate_currency_code(to_currency)

    if from_curr == to_curr:
        raise RateValidationError(
            f"from_currency and to_currency cannot be the same ({from_curr})"
        )

    try:
        rate_val = Decimal(rate.strip())
    except (InvalidOperation, ValueError):
        raise RateValidationError(f"Invalid rate value: '{rate}'")

    if rate_val <= 0:
        raise RateValidationError(f"Rate must be positive (got {rate})")

    return ExchangeRate(
        effective_date=date.today(),
        from_currency=from_curr,
        to_currency=to_curr,
        rate=rate_val,
    )


# =============================================================================
# RATE LOOKUP
# =============================================================================

def _build_rate_lookup(
    rates: list[ExchangeRate],
) -> dict[tuple[str, str], list[ExchangeRate]]:
    """Build a lookup dict: (from, to) -> sorted list of rates by date desc."""
    lookup: dict[tuple[str, str], list[ExchangeRate]] = {}
    for r in rates:
        key = (r.from_currency, r.to_currency)
        lookup.setdefault(key, []).append(r)

    # Sort each list by date descending (most recent first)
    for key in lookup:
        lookup[key].sort(key=lambda x: x.effective_date, reverse=True)

    return lookup


def find_rate(
    lookup: dict[tuple[str, str], list[ExchangeRate]],
    from_currency: str,
    to_currency: str,
    target_date: Optional[date] = None,
) -> tuple[Optional[Decimal], Optional[str]]:
    """Look up exchange rate for a currency pair.

    Args:
        lookup: Rate lookup dict
        from_currency: Source currency
        to_currency: Target currency
        target_date: Date to match (None = use latest available)

    Returns:
        Tuple of (rate, issue_or_None).
        issue is "stale_rate" if rate date > 90 days from target.
        None rate means no rate found.
    """
    if from_currency == to_currency:
        return Decimal("1"), None

    pair_rates = lookup.get((from_currency, to_currency))
    if not pair_rates:
        # Try inverse
        inverse_rates = lookup.get((to_currency, from_currency))
        if inverse_rates:
            rate, issue = _find_best_rate(inverse_rates, target_date)
            if rate is not None:
                # Invert: 1 / rate
                inverted = (Decimal("1") / rate).quantize(INTERNAL_PRECISION, rounding=ROUND_HALF_EVEN)
                return inverted, issue
        return None, "missing_rate"

    return _find_best_rate(pair_rates, target_date)


def _find_best_rate(
    sorted_rates: list[ExchangeRate],
    target_date: Optional[date],
) -> tuple[Optional[Decimal], Optional[str]]:
    """Find the best matching rate from a sorted (desc) list."""
    if not sorted_rates:
        return None, "missing_rate"

    if target_date is None:
        # Use the most recent rate
        return sorted_rates[0].rate, None

    # Find exact match or nearest prior
    best: Optional[ExchangeRate] = None
    for r in sorted_rates:
        if r.effective_date == target_date:
            return r.rate, None
        if r.effective_date <= target_date:
            best = r
            break

    if best is None:
        # All rates are after target date — use the earliest
        best = sorted_rates[-1]

    # Check staleness
    days_diff = abs((target_date - best.effective_date).days)
    issue = "stale_rate" if days_diff > STALE_RATE_DAYS else None
    return best.rate, issue


# =============================================================================
# CURRENCY DETECTION
# =============================================================================

def detect_currency_column(columns: list[str]) -> Optional[str]:
    """Detect a currency column from TB column names.

    Returns the best-matching column name, or None if not found.
    """
    result = detect_columns(columns, [CURRENCY_FIELD_CONFIG])
    return result.get_column("currency_column")


def detect_currencies_in_tb(
    df: pd.DataFrame,
    currency_column: str,
) -> list[str]:
    """Get unique currencies found in the TB's currency column."""
    if currency_column not in df.columns:
        return []

    currencies = (
        df[currency_column]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
        .tolist()
    )
    return sorted([c for c in currencies if c and len(c) == 3])


# =============================================================================
# CONVERSION ENGINE
# =============================================================================

def convert_trial_balance(
    tb_rows: list[dict],
    rate_table: CurrencyRateTable,
    amount_column: str,
    currency_column: Optional[str] = None,
    account_number_column: Optional[str] = None,
    account_name_column: Optional[str] = None,
    target_date: Optional[date] = None,
) -> ConversionResult:
    """Convert a multi-currency trial balance to the presentation currency.

    This is the main entry point for currency conversion.

    Args:
        tb_rows: List of TB row dicts
        rate_table: Session-scoped rate table with rates and presentation_currency
        amount_column: Column name containing amounts to convert
        currency_column: Column name containing currency codes (None = detect)
        account_number_column: Column for account numbers (for flags)
        account_name_column: Column for account names (for flags)
        target_date: Date for rate lookup (None = use latest)

    Returns:
        ConversionResult with converted rows and flags
    """
    if not tb_rows:
        return ConversionResult(
            conversion_performed=False,
            presentation_currency=rate_table.presentation_currency,
            total_accounts=0,
            converted_count=0,
            unconverted_count=0,
            conversion_summary="No data to convert",
        )

    presentation_currency = rate_table.presentation_currency
    df = pd.DataFrame(tb_rows)

    # Detect currency column if not provided
    if currency_column is None:
        currency_column = detect_currency_column(df.columns.tolist())

    if currency_column is None or currency_column not in df.columns:
        # No currency column — assume all rows are in presentation currency
        return ConversionResult(
            conversion_performed=False,
            presentation_currency=presentation_currency,
            total_accounts=len(df),
            converted_count=len(df),
            unconverted_count=0,
            conversion_summary="No currency column detected — TB assumed to be single-currency",
            converted_rows=tb_rows,
        )

    # Detect account columns for flagging
    if account_number_column is None:
        for col in df.columns:
            if re.search(r"account.*(?:no|num|code|id)", col, re.IGNORECASE):
                account_number_column = col
                break
    if account_name_column is None:
        for col in df.columns:
            if re.search(r"account.*name|description", col, re.IGNORECASE):
                account_name_column = col
                break

    # Normalize currency column
    df["_currency_normalized"] = (
        df[currency_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    currencies_found = sorted(
        df["_currency_normalized"]
        .loc[df["_currency_normalized"].str.len() == 3]
        .unique()
        .tolist()
    )

    # Build rate lookup
    rate_lookup = _build_rate_lookup(rate_table.rates)

    # Vectorized conversion: build rate and issue columns
    converted_amounts: list[Optional[float]] = []
    flags: list[ConversionFlag] = []
    rates_applied: dict[str, str] = {}

    # Pre-compute rates for each unique currency pair
    currency_rates: dict[str, tuple[Optional[Decimal], Optional[str]]] = {}
    for curr in currencies_found:
        if curr == presentation_currency:
            currency_rates[curr] = (Decimal("1"), None)
        else:
            rate, issue = find_rate(rate_lookup, curr, presentation_currency, target_date)
            currency_rates[curr] = (rate, issue)
            if rate is not None:
                rates_applied[f"{curr}/{presentation_currency}"] = str(rate)

    # Process rows
    converted_count = 0
    unconverted_count = 0

    for idx in range(len(df)):
        row_currency = df.at[idx, "_currency_normalized"]
        raw_amount = df.at[idx, amount_column] if amount_column in df.columns else None

        # Parse amount
        try:
            amount = Decimal(str(raw_amount)) if raw_amount is not None and str(raw_amount).strip() else Decimal("0")
        except (InvalidOperation, ValueError):
            amount = Decimal("0")

        if not row_currency or len(row_currency) != 3:
            # Missing currency code
            if amount != 0:
                acct_num = str(df.at[idx, account_number_column]) if account_number_column and account_number_column in df.columns else str(idx)
                acct_name = str(df.at[idx, account_name_column]) if account_name_column and account_name_column in df.columns else ""
                flags.append(ConversionFlag(
                    account_number=acct_num,
                    account_name=acct_name,
                    original_amount=float(amount),
                    original_currency=row_currency or "(none)",
                    issue="missing_currency_code",
                    severity="medium",
                ))
                unconverted_count += 1
            converted_amounts.append(float(amount))  # Pass through as-is
            continue

        rate_info = currency_rates.get(row_currency)
        if rate_info is None or rate_info[0] is None:
            # No rate available
            acct_num = str(df.at[idx, account_number_column]) if account_number_column and account_number_column in df.columns else str(idx)
            acct_name = str(df.at[idx, account_name_column]) if account_name_column and account_name_column in df.columns else ""
            flags.append(ConversionFlag(
                account_number=acct_num,
                account_name=acct_name,
                original_amount=float(amount),
                original_currency=row_currency,
                issue="missing_rate",
                severity="medium",  # Recalculated below
            ))
            unconverted_count += 1
            converted_amounts.append(None)
            continue

        rate, issue = rate_info
        converted = (amount * rate).quantize(INTERNAL_PRECISION, rounding=ROUND_HALF_EVEN)
        converted_amounts.append(float(converted))
        converted_count += 1

        if issue == "stale_rate":
            acct_num = str(df.at[idx, account_number_column]) if account_number_column and account_number_column in df.columns else str(idx)
            acct_name = str(df.at[idx, account_name_column]) if account_name_column and account_name_column in df.columns else ""
            flags.append(ConversionFlag(
                account_number=acct_num,
                account_name=acct_name,
                original_amount=float(amount),
                original_currency=row_currency,
                issue="stale_rate",
                severity="low",
            ))

    # Add converted amounts to DataFrame
    converted_col_name = f"converted_amount_{presentation_currency.lower()}"
    df[converted_col_name] = converted_amounts

    # Recalculate severity for missing_rate flags based on category totals
    _recalculate_flag_severity(flags, df, amount_column)

    # Clean up temp column
    df.drop(columns=["_currency_normalized"], inplace=True)

    # Build converted rows
    converted_rows = df.to_dict(orient="records")

    # Summary
    pct = (converted_count / len(df) * 100) if len(df) > 0 else 0
    summary = (
        f"{converted_count} of {len(df)} accounts converted ({pct:.0f}%). "
        f"Presentation currency: {presentation_currency}."
    )
    if unconverted_count > 0:
        summary += f" {unconverted_count} accounts could not be converted."

    return ConversionResult(
        conversion_performed=True,
        presentation_currency=presentation_currency,
        total_accounts=len(df),
        converted_count=converted_count,
        unconverted_count=unconverted_count,
        unconverted_items=flags,
        currencies_found=currencies_found,
        rates_applied=rates_applied,
        conversion_summary=summary,
        converted_rows=converted_rows,
    )


def _recalculate_flag_severity(
    flags: list[ConversionFlag],
    df: pd.DataFrame,
    amount_column: str,
) -> None:
    """Recalculate severity for flags based on magnitude relative to total."""
    if not flags or amount_column not in df.columns:
        return

    # Calculate total absolute amount
    try:
        total = Decimal(str(math.fsum(
            abs(float(v)) for v in df[amount_column].dropna()
            if str(v).strip()
        )))
    except (ValueError, InvalidOperation):
        return

    if total == 0:
        return

    for flag in flags:
        if flag.issue in ("missing_rate", "missing_currency_code"):
            ratio = Decimal(str(abs(flag.original_amount))) / total
            if ratio > SEVERITY_HIGH_THRESHOLD:
                flag.severity = "high"
            elif ratio > SEVERITY_MEDIUM_THRESHOLD:
                flag.severity = "medium"
            else:
                flag.severity = "low"
