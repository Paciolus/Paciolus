/**
 * Paciolus Formatting Utilities
 * Phase 1 Refactor: Shared formatting functions
 *
 * PERFORMANCE: Intl.NumberFormat and Intl.DateTimeFormat instances are
 * expensive to create. We memoize them at module level for reuse.
 *
 * ZERO-STORAGE: Pure utility functions with no state persistence.
 */

// =============================================================================
// MEMOIZED FORMATTERS (module-level singletons for performance)
// =============================================================================

/**
 * Currency formatter with 2 decimal places (e.g., $1,234.56)
 */
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Currency formatter without decimals (e.g., $1,235)
 */
const currencyFormatterNoDecimals = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

/**
 * Number formatter with grouping (e.g., 1,234,567)
 */
const numberFormatter = new Intl.NumberFormat('en-US', {
  useGrouping: true,
});

/**
 * Percent formatter (e.g., 12.34%)
 */
const percentFormatter = new Intl.NumberFormat('en-US', {
  style: 'percent',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Date formatter for standard display (e.g., "Feb 2, 2026")
 */
const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

/**
 * Time formatter (e.g., "3:45 PM")
 */
const timeFormatter = new Intl.DateTimeFormat('en-US', {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
});

/**
 * Date + time formatter for compact display (e.g., "Feb 2, 3:45 PM")
 */
const dateTimeCompactFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
});

// =============================================================================
// CURRENCY FORMATTING
// =============================================================================

/**
 * Format a number as USD currency with 2 decimal places.
 * Returns "-" for zero values when showZeroAsEmpty is true.
 *
 * @example
 * formatCurrency(1234.5)     // "$1,234.50"
 * formatCurrency(0, true)    // "-"
 * formatCurrency(0, false)   // "$0.00"
 */
export function formatCurrency(
  amount: number,
  showZeroAsEmpty: boolean = false
): string {
  if (showZeroAsEmpty && amount === 0) return '-';
  return currencyFormatter.format(amount);
}

/**
 * Format a number as USD currency without decimal places.
 * Useful for thresholds and rounded-sm values.
 *
 * @example
 * formatCurrencyWhole(1234.56)  // "$1,235"
 * formatCurrencyWhole(5000)     // "$5,000"
 */
export function formatCurrencyWhole(amount: number): string {
  return currencyFormatterNoDecimals.format(amount);
}

/**
 * Parse a currency string back to a number.
 * Removes currency symbols, commas, and whitespace.
 *
 * @example
 * parseCurrency("$1,234.56")  // 1234.56
 * parseCurrency("1234")       // 1234
 * parseCurrency("invalid")    // null
 */
export function parseCurrency(value: string): number | null {
  const cleaned = value.replace(/[$,\s]/g, '');
  const parsed = parseFloat(cleaned);
  return isNaN(parsed) ? null : parsed;
}

// =============================================================================
// NUMBER FORMATTING
// =============================================================================

/**
 * Format a number with thousands separators.
 *
 * @example
 * formatNumber(1234567)  // "1,234,567"
 * formatNumber(42)       // "42"
 */
export function formatNumber(num: number): string {
  return numberFormatter.format(num);
}

/**
 * Format a number as a percentage.
 * Input should be a decimal (0.1234 = 12.34%).
 *
 * @example
 * formatPercent(0.1234)  // "12.34%"
 * formatPercent(1.5)     // "150.00%"
 */
export function formatPercent(value: number): string {
  return percentFormatter.format(value);
}

/**
 * Format a number as a percentage from a whole number.
 * Input is the percentage value (12.34 = 12.34%).
 *
 * @example
 * formatPercentWhole(12.34)  // "12.34%"
 * formatPercentWhole(150)    // "150.00%"
 */
export function formatPercentWhole(value: number): string {
  return percentFormatter.format(value / 100);
}

// =============================================================================
// DATE/TIME FORMATTING
// =============================================================================

/**
 * Format an ISO date string as a readable date.
 *
 * @example
 * formatDate("2026-02-04T15:45:00Z")  // "Feb 4, 2026"
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return dateFormatter.format(date);
}

/**
 * Format an ISO date string as a readable time.
 *
 * @example
 * formatTime("2026-02-04T15:45:00Z")  // "3:45 PM"
 */
export function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return timeFormatter.format(date);
}

/**
 * Format an ISO date string as "Date at Time".
 * Used for activity logs and timestamps.
 *
 * @example
 * formatDateTime("2026-02-04T15:45:00Z")  // "Feb 4, 2026 at 3:45 PM"
 */
export function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return `${dateFormatter.format(date)} at ${timeFormatter.format(date)}`;
}

/**
 * Format an ISO date string as compact date+time.
 *
 * @example
 * formatDateTimeCompact("2026-02-04T15:45:00Z")  // "Feb 4, 3:45 PM"
 */
export function formatDateTimeCompact(isoString: string): string {
  const date = new Date(isoString);
  return dateTimeCompactFormatter.format(date);
}

/**
 * Get a relative time string for recent dates.
 *
 * @example
 * getRelativeTime(now)             // "Today"
 * getRelativeTime(yesterday)       // "Yesterday"
 * getRelativeTime(lastWeek)        // "5 days ago"
 * getRelativeTime(lastMonth)       // "Feb 1, 2026"
 */
export function getRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

  return formatDate(isoString);
}
