# RFC: Multi-Currency TB Conversion

**Status:** Approved
**Phase:** XXXIV (Sprints 257-259)
**Author:** Agent Council
**Date:** 2026-02-15

---

## 1. Problem Statement

Trial balances may contain accounts denominated in multiple currencies. Without conversion to a common presentation currency, ratio analysis, benchmarks, and anomaly detection produce misleading results when comparing USD receivables against EUR payables.

## 2. Scope

### In Scope (Diagnostic Analysis)
- **Currency column detection** in uploaded TBs (leverage `column_detector.py`)
- **Presentation currency conversion** — convert all TB amounts to a single currency for analysis
- **Rate table upload** — user-provided CSV with exchange rates
- **Manual single-rate entry** — simple same-day conversions
- **Dual-column output** — original amount alongside converted amount
- **Unconverted item flagging** — surface accounts where rate lookup failed
- **Conversion memo** — document methodology and rates applied

### Out of Scope (Accounting Operations)
- Functional currency determination (auditor judgment per IAS 21 / ASC 830)
- Monetary vs non-monetary classification (user must provide if needed)
- Translation adjustments / CTA entries (belongs in accounting system)
- Foreign subsidiary consolidation
- Intercompany eliminations
- Average / historical rate application (deferred — closing rate MVP covers 80% of use cases)

## 3. Exchange Rate Model

### MVP: Closing Rate Only

All accounts converted at the user-provided closing rate. This covers the primary use case: converting a multi-currency TB to a common presentation currency for diagnostic analysis.

### Rate Table Format (CSV)

```
effective_date,from_currency,to_currency,rate
2026-01-31,EUR,USD,1.0523
2026-01-31,GBP,USD,1.2634
2026-01-31,JPY,USD,0.0066
```

**Validation rules:**
- Currency codes must be valid ISO 4217 (3-letter uppercase)
- Rates must be positive (> 0)
- No duplicate `(effective_date, from_currency, to_currency)` pairs
- Max 10,000 rows per rate table

### Rate Lookup

1. Exact date match for `(from_currency, to_currency)` pair
2. Fallback: nearest prior date (within 90 days — flag if stale)
3. Missing: flag account as unconverted, do NOT estimate

### Manual Single-Rate Entry

For simple cases: user provides `(from_currency, to_currency, rate)` applied uniformly. No date lookup needed.

## 4. Conversion Engine

### Algorithm

1. Detect currency column in TB (or accept user override)
2. Identify presentation currency (user-selected target)
3. For each row: look up rate for `(row_currency, target_currency)`
4. Convert: `converted_amount = original_amount * rate`
5. Flag unconverted rows
6. Recalculate totals from converted individual amounts (not category subtotals)

### Rounding

- Internal precision: `Decimal` with 4 decimal places
- Display: 2 decimal places (standard currency format)
- Method: Banker's rounding (`ROUND_HALF_EVEN`)
- TB balance check after conversion: flag if `|Assets - (Liabilities + Equity)| > 0.01 * num_accounts`

### Performance

- Vectorized Pandas operations (no row-by-row `.apply()`)
- Must handle 500K-row TBs
- Rate lookup via merged DataFrame join, not per-row dictionary lookup

## 5. Unconverted Item Handling

### Flag Structure

```python
@dataclass
class ConversionFlag:
    account_number: str
    account_name: str
    original_amount: Decimal
    original_currency: str
    issue: str  # "missing_rate" | "missing_currency_code" | "invalid_currency" | "stale_rate"
    severity: str  # "high" | "medium" | "low"
```

### Severity Logic

- **High:** Unconverted balance > 5% of category total
- **Medium:** 1-5% of category total
- **Low:** < 1% of category total

### User Experience

- Conversion summary: "42 of 45 accounts converted (93%)"
- Expandable unconverted items section
- Option to proceed with partial conversion
- Memo disclaimer lists excluded accounts

## 6. Zero-Storage Compliance

### Ephemeral Storage

```python
# Session-scoped (in-memory dict keyed by user_id)
currency_rates_store: dict[int, CurrencyRateTable] = {}
```

### Rate Table Lifecycle

- Created on rate upload
- Cleared on: new TB upload, logout, session timeout
- NEVER persisted to database

### Metadata Persistence (allowed)

Only non-financial metadata in `DiagnosticSummary`:
- `conversion_performed: bool`
- `presentation_currency: str` (e.g., "USD")
- `unconverted_count: int`

NO individual rates, account amounts, or PII stored.

## 7. API Design

```
POST /audit/currency-rates     — Upload rate table CSV (session-scoped)
POST /audit/currency-rate      — Manual single-rate entry
DELETE /audit/currency-rates   — Clear rate table
```

Rate table is consumed automatically during TB upload/analysis when present in session.

## 8. Frontend Design

- Rate table upload: CSV drag-and-drop (matches existing TB upload pattern)
- Manual rate entry: simple form (from, to, rate)
- Converted amounts toggle on TB results (original <-> converted)
- Currency-aware number formatting with ISO 4217 symbols
- Unconverted items section with severity badges

## 9. Disclaimer

> This tool converts trial balance amounts to a common presentation currency for diagnostic analysis only. It does not perform functional currency determination, translation adjustment calculations, or GAAP/IFRS compliance assessments. Converted amounts are for analytical comparability and do not constitute accounting entries.

## 10. Future Extensions (Deferred)

- Average rate support for income statement accounts
- Historical rate support for non-monetary items
- Multi-period rate tables with temporal matching
- Automatic currency detection from account names
