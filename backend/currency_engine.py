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

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Optional

import pandas as pd

from shared.column_detector import ColumnFieldConfig, ColumnPattern, detect_columns

# ISO 4217 currency codes (common subset for validation)
ISO_4217_CODES: set[str] = {
    "AED",
    "AFN",
    "ALL",
    "AMD",
    "ANG",
    "AOA",
    "ARS",
    "AUD",
    "AWG",
    "AZN",
    "BAM",
    "BBD",
    "BDT",
    "BGN",
    "BHD",
    "BIF",
    "BMD",
    "BND",
    "BOB",
    "BRL",
    "BSD",
    "BTN",
    "BWP",
    "BYN",
    "BZD",
    "CAD",
    "CDF",
    "CHF",
    "CLP",
    "CNY",
    "COP",
    "CRC",
    "CUP",
    "CVE",
    "CZK",
    "DJF",
    "DKK",
    "DOP",
    "DZD",
    "EGP",
    "ERN",
    "ETB",
    "EUR",
    "FJD",
    "FKP",
    "GBP",
    "GEL",
    "GHS",
    "GIP",
    "GMD",
    "GNF",
    "GTQ",
    "GYD",
    "HKD",
    "HNL",
    "HRK",
    "HTG",
    "HUF",
    "IDR",
    "ILS",
    "INR",
    "IQD",
    "IRR",
    "ISK",
    "JMD",
    "JOD",
    "JPY",
    "KES",
    "KGS",
    "KHR",
    "KMF",
    "KPW",
    "KRW",
    "KWD",
    "KYD",
    "KZT",
    "LAK",
    "LBP",
    "LKR",
    "LRD",
    "LSL",
    "LYD",
    "MAD",
    "MDL",
    "MGA",
    "MKD",
    "MMK",
    "MNT",
    "MOP",
    "MRU",
    "MUR",
    "MVR",
    "MWK",
    "MXN",
    "MYR",
    "MZN",
    "NAD",
    "NGN",
    "NIO",
    "NOK",
    "NPR",
    "NZD",
    "OMR",
    "PAB",
    "PEN",
    "PGK",
    "PHP",
    "PKR",
    "PLN",
    "PYG",
    "QAR",
    "RON",
    "RSD",
    "RUB",
    "RWF",
    "SAR",
    "SBD",
    "SCR",
    "SDG",
    "SEK",
    "SGD",
    "SHP",
    "SLE",
    "SOS",
    "SRD",
    "SSP",
    "STN",
    "SVC",
    "SYP",
    "SZL",
    "THB",
    "TJS",
    "TMT",
    "TND",
    "TOP",
    "TRY",
    "TTD",
    "TWD",
    "TZS",
    "UAH",
    "UGX",
    "USD",
    "UYU",
    "UZS",
    "VES",
    "VND",
    "VUV",
    "WST",
    "XAF",
    "XCD",
    "XOF",
    "XPF",
    "YER",
    "ZAR",
    "ZMW",
    "ZWL",
}

# Maximum rows in a rate table upload
MAX_RATE_TABLE_ROWS = 10_000

# Stale rate threshold (days)
STALE_RATE_DAYS = 90

# Decimal precision for internal calculations
INTERNAL_PRECISION = Decimal("0.0001")
DISPLAY_PRECISION = Decimal("0.01")

# Severity thresholds (percentage of category total)
SEVERITY_HIGH_THRESHOLD = Decimal("0.05")  # > 5%
SEVERITY_MEDIUM_THRESHOLD = Decimal("0.01")  # > 1%


# =============================================================================
# Sprint 700: generator ↔ engine contract
# =============================================================================
# Declarative contract the anomaly-framework meta-test uses to verify each
# multi-currency generator produces data the engine actually inspects.
# Kept next to the detection logic so an auditor reviewing the engine can
# read the contract and the detection code in one place.
from shared.engine_contract import DetectionPreconditions, EngineInputContract

ENGINE_CONTRACT = EngineInputContract(
    tool="currency",
    required_columns=frozenset({"Currency"}),
    optional_columns=frozenset({"Account", "Account Name", "Debit", "Credit"}),
    entry_point="currency_engine.convert_trial_balance",
    detection_targets={
        "missing_rates": DetectionPreconditions(
            requires_columns=frozenset({"Currency"}),
            scope="standalone",
            description=(
                "TB row's currency has no matching pair in the CurrencyRateTable. "
                "Engine emits ConversionFlag(issue='missing_rate')."
            ),
            emits_fields=frozenset({"unconverted_items", "unconverted_count"}),
        ),
        "invalid_currencies": DetectionPreconditions(
            requires_columns=frozenset({"Currency"}),
            scope="standalone",
            description=(
                "Currency code fails ISO 4217 validation. Engine emits "
                "ConversionFlag(issue='missing_currency_code' or 'invalid_currency')."
            ),
            emits_fields=frozenset({"unconverted_items"}),
        ),
        "zero_rates": DetectionPreconditions(
            requires_columns=frozenset(),
            scope="standalone",
            description=(
                "Rate = 0. Sprint 699 — rejected at ExchangeRate construction; "
                "use-time defense-in-depth also flags as 'invalid_rate'."
            ),
            emits_fields=frozenset({"unconverted_items"}),
        ),
        "negative_rates": DetectionPreconditions(
            requires_columns=frozenset(),
            scope="standalone",
            description=("Rate < 0. Sprint 699 — rejected at ExchangeRate construction."),
            emits_fields=frozenset({"unconverted_items"}),
        ),
        "stale_rates": DetectionPreconditions(
            requires_columns=frozenset(),
            scope="standalone",
            description=(
                "Rate's effective_date is older than staleness_threshold_days "
                "relative to either target_date or the table's newest cohort date. "
                "Sprint 699 — cohort check fires even without a target_date."
            ),
            emits_fields=frozenset({"unconverted_items"}),
        ),
    },
)


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
    """A single exchange rate entry.

    Sprint 699: validate-at-construction. Previously this was an unvalidated
    dataclass — any path that bypassed ``parse_rate_table`` (programmatic
    construction, ``from_storage_dict`` DB hydration, test fixtures) could
    admit zero, negative, or malformed rates into a ``CurrencyRateTable``,
    which the conversion engine then used as-is, silently producing bad
    output. Validation here is the first line of defense; ``convert_trial_
    balance`` adds a second (defense-in-depth) check in case a malformed
    rate still slips through via unsafe reflection or a future attribute
    mutation.
    """

    effective_date: date
    from_currency: str
    to_currency: str
    rate: Decimal

    def __post_init__(self) -> None:
        # Normalise rate to Decimal — a programmatic caller may pass str/int/float.
        # Doing the coercion here means the invariants below can rely on Decimal.
        if not isinstance(self.rate, Decimal):
            try:
                object.__setattr__(self, "rate", Decimal(str(self.rate)))
            except (InvalidOperation, TypeError, ValueError) as exc:
                # Use ValueError directly — RateValidationError is defined later
                # in the module and importing it here would create a forward
                # reference loop.
                raise ValueError(f"ExchangeRate.rate must be convertible to Decimal (got {self.rate!r})") from exc

        if self.rate <= 0:
            raise ValueError(
                f"ExchangeRate.rate must be positive (got {self.rate}); "
                "zero and negative rates are mathematically invalid for currency conversion."
            )

        if not isinstance(self.from_currency, str) or not self.from_currency.strip():
            raise ValueError("ExchangeRate.from_currency is required and must be non-empty.")
        if not isinstance(self.to_currency, str) or not self.to_currency.strip():
            raise ValueError("ExchangeRate.to_currency is required and must be non-empty.")

        # Uppercase ISO-4217-shaped currency codes. We do NOT enforce the full
        # ISO_4217_CODES set here — ``validate_currency_code`` is the upload-path
        # boundary check; here we only ensure the code is a non-empty 3-letter
        # string so downstream dict-keyed rate lookup behaves deterministically.
        if len(self.from_currency) != 3 or len(self.to_currency) != 3:
            raise ValueError(
                "ExchangeRate currency codes must be 3 letters "
                f"(got from={self.from_currency!r}, to={self.to_currency!r})."
            )

        if self.from_currency == self.to_currency:
            raise ValueError(f"ExchangeRate from_currency and to_currency must differ (both are {self.from_currency}).")

        if not isinstance(self.effective_date, date):
            raise ValueError(f"ExchangeRate.effective_date must be a date (got {type(self.effective_date).__name__}).")

    def to_dict(self) -> dict:
        return {
            "effective_date": self.effective_date.isoformat(),
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "rate": str(self.rate),
        }


@dataclass
class CurrencyRateTable:
    """Session-scoped rate table (Zero-Storage compliant).

    Sprint 699: ``staleness_threshold_days`` promoted from a module-level
    constant to a first-class configurable field. The table can now detect
    stale rates against its own cohort (newest rate in the table) even when
    the caller hasn't supplied an as-of-date — which the prior implementation
    required. Set to 0 to disable the cohort-based staleness check.
    """

    rates: list[ExchangeRate] = field(default_factory=list)
    uploaded_at: Optional[datetime] = None
    presentation_currency: str = "USD"
    staleness_threshold_days: int = STALE_RATE_DAYS  # Sprint 699: configurable

    def to_dict(self) -> dict:
        return {
            "rate_count": len(self.rates),
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "presentation_currency": self.presentation_currency,
            "currency_pairs": list({f"{r.from_currency}/{r.to_currency}" for r in self.rates}),
            "staleness_threshold_days": self.staleness_threshold_days,
        }

    def to_storage_dict(self) -> dict:
        """Full serialization for DB session storage (includes all rates)."""
        return {
            "rates": [r.to_dict() for r in self.rates],
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "presentation_currency": self.presentation_currency,
            "staleness_threshold_days": self.staleness_threshold_days,
        }

    @classmethod
    def from_storage_dict(cls, data: dict) -> "CurrencyRateTable":
        """Reconstruct from DB session storage dict (Sprint 262).

        Sprint 699: every reconstructed ExchangeRate now runs through
        ``__post_init__`` validation, so a corrupted DB row can no longer
        silently re-admit a zero/negative rate.
        """
        rates = []
        for r in data.get("rates", []):
            rates.append(
                ExchangeRate(
                    effective_date=date.fromisoformat(r["effective_date"]),
                    from_currency=r["from_currency"],
                    to_currency=r["to_currency"],
                    rate=Decimal(r["rate"]),
                )
            )
        uploaded_at = None
        if data.get("uploaded_at"):
            uploaded_at = datetime.fromisoformat(data["uploaded_at"])
        return cls(
            rates=rates,
            uploaded_at=uploaded_at,
            presentation_currency=data.get("presentation_currency", "USD"),
            staleness_threshold_days=int(data.get("staleness_threshold_days", STALE_RATE_DAYS)),
        )

    def newest_rate_date(self) -> Optional[date]:
        """Return the latest ``effective_date`` across all rates.

        Sprint 699: used by the cohort-based staleness check — a rate from
        2024-01-01 is "stale" relative to a 2024-12-31 entry in the same
        table even when the caller hasn't supplied a target_date.
        """
        if not self.rates:
            return None
        return max(r.effective_date for r in self.rates)


@dataclass
class ConversionFlag:
    """A flagged unconverted or partially converted account."""

    account_number: str
    account_name: str
    original_amount: Decimal
    original_currency: str
    # Sprint 699: added "invalid_rate" for use-time defense-in-depth rejection
    # (zero/negative rates that leaked through parse-time validation).
    issue: str  # "missing_rate" | "missing_currency_code" | "invalid_currency" | "stale_rate" | "invalid_rate"
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
class CurrencyExposure:
    """Per-currency aggregation for the conversion output table."""

    currency: str
    account_count: int
    foreign_total: Decimal
    rate: str  # rate applied or "N/A"
    usd_equivalent: Decimal
    pct_of_total: Decimal

    def to_dict(self) -> dict:
        return {
            "currency": self.currency,
            "account_count": self.account_count,
            "foreign_total": self.foreign_total,
            "rate": self.rate,
            "usd_equivalent": self.usd_equivalent,
            "pct_of_total": self.pct_of_total,
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
    currency_exposure: list[CurrencyExposure] = field(default_factory=list)

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
            "currency_exposure": [e.to_dict() for e in self.currency_exposure],
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
        raise RateValidationError(f"Invalid currency code '{code}': must be 3 uppercase letters (ISO 4217)")
    if normalized not in ISO_4217_CODES:
        raise RateValidationError(f"Unknown currency code '{normalized}': not a recognized ISO 4217 code")
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
        raise RateValidationError(f"Rate table exceeds maximum of {MAX_RATE_TABLE_ROWS:,} rows (got {len(rows):,})")

    required_columns = {"effective_date", "from_currency", "to_currency", "rate"}
    if rows:
        available = {k.lower().strip() for k in rows[0].keys()}
        missing = required_columns - available
        if missing:
            raise RateValidationError(f"Rate table missing required columns: {', '.join(sorted(missing))}")

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

        rates.append(
            ExchangeRate(
                effective_date=parsed_date,
                from_currency=from_curr,
                to_currency=to_curr,
                rate=rate_val,
            )
        )

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
        raise RateValidationError(f"from_currency and to_currency cannot be the same ({from_curr})")

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
    newest_cohort_date: Optional[date] = None,
    staleness_threshold_days: int = STALE_RATE_DAYS,
) -> tuple[Optional[Decimal], Optional[str]]:
    """Look up exchange rate for a currency pair.

    Args:
        lookup: Rate lookup dict.
        from_currency: Source currency.
        to_currency: Target currency.
        target_date: Date to match (None = use latest available).
        newest_cohort_date: Sprint 699 — the newest ``effective_date`` across
            the entire rate table. Used as a fallback staleness reference
            when ``target_date`` is None. Without this, a rate from 2024-01
            alongside a rate from 2024-12 would never be flagged stale on a
            ``target_date=None`` call because the "most recent" rate wins by
            default.
        staleness_threshold_days: Days beyond the reference date after which
            a rate is considered stale. Sprint 699: was a hardcoded 90;
            now plumbed through so callers can tune per engagement.

    Returns:
        Tuple of (rate, issue_or_None). ``issue`` is ``"stale_rate"`` when
        the matched rate's date exceeds the threshold, or ``"missing_rate"``
        when no rate exists for the pair. ``None`` rate means no rate found.
    """
    if from_currency == to_currency:
        return Decimal("1"), None

    pair_rates = lookup.get((from_currency, to_currency))
    if not pair_rates:
        # Try inverse
        inverse_rates = lookup.get((to_currency, from_currency))
        if inverse_rates:
            rate, issue = _find_best_rate(
                inverse_rates,
                target_date,
                newest_cohort_date=newest_cohort_date,
                staleness_threshold_days=staleness_threshold_days,
            )
            if rate is not None:
                # Invert: 1 / rate
                inverted = (Decimal("1") / rate).quantize(INTERNAL_PRECISION, rounding=ROUND_HALF_EVEN)
                return inverted, issue
        return None, "missing_rate"

    return _find_best_rate(
        pair_rates,
        target_date,
        newest_cohort_date=newest_cohort_date,
        staleness_threshold_days=staleness_threshold_days,
    )


def _find_best_rate(
    sorted_rates: list[ExchangeRate],
    target_date: Optional[date],
    *,
    newest_cohort_date: Optional[date] = None,
    staleness_threshold_days: int = STALE_RATE_DAYS,
) -> tuple[Optional[Decimal], Optional[str]]:
    """Find the best matching rate from a sorted (desc) list.

    Sprint 699: staleness is now checked in two independent modes:
      * If ``target_date`` is supplied, staleness = days between the matched
        rate's date and ``target_date`` (the original behaviour).
      * If ``target_date`` is None but ``newest_cohort_date`` is supplied,
        staleness = days between the matched rate's date and the newest
        rate in the whole table. This catches "stale rate alongside a
        fresh one" cases that the original target-date-only check missed.

    If both are None, no staleness check runs (original behaviour preserved
    for call sites that opt out).
    """
    if not sorted_rates:
        return None, "missing_rate"

    if target_date is None:
        # Use the most recent rate
        best = sorted_rates[0]
        # Sprint 699: cohort-based staleness check when no target_date.
        if newest_cohort_date is not None and staleness_threshold_days > 0:
            days_diff = abs((newest_cohort_date - best.effective_date).days)
            if days_diff > staleness_threshold_days:
                return best.rate, "stale_rate"
        return best.rate, None

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

    # Check staleness against the supplied target_date
    days_diff = abs((target_date - best.effective_date).days)
    issue = "stale_rate" if days_diff > staleness_threshold_days else None
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

    currencies = df[currency_column].dropna().astype(str).str.strip().str.upper().unique().tolist()
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
    df["_currency_normalized"] = df[currency_column].fillna("").astype(str).str.strip().str.upper()

    currencies_found = sorted(
        df["_currency_normalized"].loc[df["_currency_normalized"].str.len() == 3].unique().tolist()
    )

    # Build rate lookup
    rate_lookup = _build_rate_lookup(rate_table.rates)

    # Sprint 699: cohort-based staleness check — when no target_date is
    # supplied, we still want to catch "stale rate alongside a fresh one"
    # by comparing each matched rate to the table's newest entry.
    newest_cohort_date = rate_table.newest_rate_date()
    staleness_threshold = rate_table.staleness_threshold_days

    # Vectorized conversion: build rate and issue columns
    converted_amounts: list[Optional[Decimal]] = []
    flags: list[ConversionFlag] = []
    rates_applied: dict[str, str] = {}

    # Pre-compute rates for each unique currency pair
    currency_rates: dict[str, tuple[Optional[Decimal], Optional[str]]] = {}
    for curr in currencies_found:
        if curr == presentation_currency:
            currency_rates[curr] = (Decimal("1"), None)
        else:
            rate, issue = find_rate(
                rate_lookup,
                curr,
                presentation_currency,
                target_date,
                newest_cohort_date=newest_cohort_date,
                staleness_threshold_days=staleness_threshold,
            )
            # Sprint 699: defense-in-depth at use time. ExchangeRate
            # __post_init__ enforces rate > 0, but a future attribute
            # mutation or an unvalidated construction path could still
            # leak a bad rate into rate_lookup. Reject it here so the
            # engine never produces silent 0 or negative conversions.
            if rate is not None and rate <= 0:
                rate, issue = None, "invalid_rate"
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
                acct_num = (
                    str(df.at[idx, account_number_column])
                    if account_number_column and account_number_column in df.columns
                    else str(idx)
                )
                acct_name = (
                    str(df.at[idx, account_name_column])
                    if account_name_column and account_name_column in df.columns
                    else ""
                )
                flags.append(
                    ConversionFlag(
                        account_number=acct_num,
                        account_name=acct_name,
                        original_amount=amount,
                        original_currency=row_currency or "(none)",
                        issue="missing_currency_code",
                        severity="medium",
                    )
                )
                unconverted_count += 1
            converted_amounts.append(amount)  # Pass through as-is
            continue

        rate_info = currency_rates.get(row_currency)
        if rate_info is None or rate_info[0] is None:
            # No rate available — either the pair wasn't in the table
            # ("missing_rate") or the matched rate failed use-time validation
            # ("invalid_rate") — Sprint 699 defense-in-depth.
            acct_num = (
                str(df.at[idx, account_number_column])
                if account_number_column and account_number_column in df.columns
                else str(idx)
            )
            acct_name = (
                str(df.at[idx, account_name_column])
                if account_name_column and account_name_column in df.columns
                else ""
            )
            # Carry through the specific issue from find_rate so downstream
            # memos / reports can distinguish "data wasn't there" from "data
            # was there but invalid" — different remediation for the auditor.
            carried_issue = rate_info[1] if rate_info and rate_info[1] else "missing_rate"
            flags.append(
                ConversionFlag(
                    account_number=acct_num,
                    account_name=acct_name,
                    original_amount=amount,
                    original_currency=row_currency,
                    issue=carried_issue,
                    severity="high" if carried_issue == "invalid_rate" else "medium",
                )
            )
            unconverted_count += 1
            converted_amounts.append(None)
            continue

        rate, issue = rate_info
        assert rate is not None  # guarded by rate_info[0] is None check above
        converted = (amount * rate).quantize(INTERNAL_PRECISION, rounding=ROUND_HALF_EVEN)
        converted_amounts.append(converted)
        converted_count += 1

        if issue == "stale_rate":
            acct_num = (
                str(df.at[idx, account_number_column])
                if account_number_column and account_number_column in df.columns
                else str(idx)
            )
            acct_name = (
                str(df.at[idx, account_name_column])
                if account_name_column and account_name_column in df.columns
                else ""
            )
            flags.append(
                ConversionFlag(
                    account_number=acct_num,
                    account_name=acct_name,
                    original_amount=amount,
                    original_currency=row_currency,
                    issue="stale_rate",
                    severity="low",
                )
            )

    # Add converted amounts to DataFrame
    converted_col_name = f"converted_amount_{presentation_currency.lower()}"
    df[converted_col_name] = converted_amounts

    # Recalculate severity for missing_rate flags based on category totals
    _recalculate_flag_severity(flags, df, amount_column)

    # Build currency exposure summary (per-currency aggregation)
    currency_exposure = _build_currency_exposure(
        df, amount_column, converted_col_name, presentation_currency, rates_applied
    )

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
        currency_exposure=currency_exposure,
    )


def _build_currency_exposure(
    df: pd.DataFrame,
    amount_column: str,
    converted_col_name: str,
    presentation_currency: str,
    rates_applied: dict[str, str],
) -> list[CurrencyExposure]:
    """Aggregate conversion results by currency for the exposure summary table."""
    if "_currency_normalized" not in df.columns or amount_column not in df.columns:
        return []

    exposure: list[CurrencyExposure] = []
    total_usd = Decimal("0")

    for curr in sorted(df["_currency_normalized"].unique()):
        if not curr or len(curr) != 3:
            continue
        mask = df["_currency_normalized"] == curr
        acct_count = int(mask.sum())

        # Foreign currency total (original amounts) — aggregate as Decimal
        foreign_total = Decimal("0")
        for v in df.loc[mask, amount_column].dropna():
            try:
                foreign_total += Decimal(str(v))
            except (InvalidOperation, ValueError):
                pass

        # USD equivalent (converted amounts) — aggregate as Decimal
        usd_equiv = Decimal("0")
        if converted_col_name in df.columns:
            for v in df.loc[mask, converted_col_name].dropna():
                try:
                    usd_equiv += Decimal(str(v))
                except (InvalidOperation, ValueError):
                    pass

        # Rate applied
        rate_key = f"{curr}/{presentation_currency}"
        rate_str = rates_applied.get(rate_key, "1.0000" if curr == presentation_currency else "N/A")

        total_usd += usd_equiv
        exposure.append(
            CurrencyExposure(
                currency=curr,
                account_count=acct_count,
                foreign_total=foreign_total.quantize(DISPLAY_PRECISION, rounding=ROUND_HALF_EVEN),
                rate=rate_str,
                usd_equivalent=usd_equiv.quantize(DISPLAY_PRECISION, rounding=ROUND_HALF_EVEN),
                pct_of_total=Decimal("0"),  # Calculated below
            )
        )

    # Calculate percentages
    if total_usd != 0:
        for exp in exposure:
            exp.pct_of_total = (
                (abs(exp.usd_equivalent) / abs(total_usd) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_EVEN)
                if total_usd
                else Decimal("0")
            )

    return exposure


def _recalculate_flag_severity(
    flags: list[ConversionFlag],
    df: pd.DataFrame,
    amount_column: str,
) -> None:
    """Recalculate severity for flags based on magnitude relative to total."""
    if not flags or amount_column not in df.columns:
        return

    # Calculate total absolute amount using Decimal aggregation
    total = Decimal("0")
    try:
        for v in df[amount_column].dropna():
            s = str(v).strip()
            if s:
                total += abs(Decimal(s))
    except (ValueError, InvalidOperation):
        return

    if total == 0:
        return

    for flag in flags:
        if flag.issue in ("missing_rate", "missing_currency_code"):
            ratio = abs(Decimal(str(flag.original_amount))) / total
            if ratio > SEVERITY_HIGH_THRESHOLD:
                flag.severity = "high"
            elif ratio > SEVERITY_MEDIUM_THRESHOLD:
                flag.severity = "medium"
            else:
                flag.severity = "low"
