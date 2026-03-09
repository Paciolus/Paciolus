/**
 * Testing config field definitions for practice settings page.
 * Sprint 519 Phase 4: Extracted from page.tsx to reduce page LOC.
 */

export const JE_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'Only flag amounts above this', prefix: '$' },
  { key: 'unusual_amount_stddev', label: 'Unusual Amount Sensitivity', description: 'Standard deviations from mean', step: 0.5, min: 1, max: 5 },
  { key: 'single_user_volume_pct', label: 'User Volume Threshold', description: 'Flag users posting more than this % of entries', suffix: '%', displayScale: 100, fallback: 25, min: 5, max: 80 },
  { key: 'backdate_days_threshold', label: 'Backdating Threshold', description: 'Days between posting and entry date', suffix: 'days', integer: true, fallback: 30, min: 7, max: 180 },
  { key: 'suspicious_keyword_threshold', label: 'Keyword Sensitivity', description: 'Minimum confidence for suspicious keywords', suffix: '%', displayScale: 100, fallback: 60, min: 30, max: 95 },
]

export const JE_TOGGLES = [
  { key: 'weekend_posting_enabled', label: 'Weekend Postings' },
  { key: 'after_hours_enabled', label: 'After-Hours Postings' },
  { key: 'numbering_gap_enabled', label: 'Numbering Gaps' },
  { key: 'backdate_enabled', label: 'Backdated Entries' },
  { key: 'suspicious_keyword_enabled', label: 'Suspicious Keywords' },
]

export const AP_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'Only flag amounts above this', prefix: '$' },
  { key: 'duplicate_days_window', label: 'Duplicate Date Window', description: 'Days to check for fuzzy duplicates', suffix: 'days', integer: true, fallback: 30, min: 7, max: 90 },
  { key: 'unusual_amount_stddev', label: 'Unusual Amount Sensitivity', description: 'Standard deviations from vendor mean', step: 0.5, min: 1, max: 5 },
  { key: 'suspicious_keyword_threshold', label: 'Keyword Sensitivity', description: 'Minimum confidence for suspicious keywords', suffix: '%', displayScale: 100, fallback: 60, min: 30, max: 95 },
]

export const AP_TOGGLES = [
  { key: 'check_number_gap_enabled', label: 'Check Number Gaps' },
  { key: 'payment_before_invoice_enabled', label: 'Payment Before Invoice' },
  { key: 'invoice_reuse_check', label: 'Invoice Reuse' },
  { key: 'weekend_payment_enabled', label: 'Weekend Payments' },
  { key: 'high_frequency_vendor_enabled', label: 'High-Frequency Vendors' },
  { key: 'vendor_variation_enabled', label: 'Vendor Variations' },
  { key: 'threshold_proximity_enabled', label: 'Just-Below-Threshold' },
]

export const PAYROLL_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'Only flag salary amounts above this', prefix: '$' },
  { key: 'unusual_pay_stddev', label: 'Unusual Pay Sensitivity', description: 'Standard deviations from department mean', step: 0.5, min: 1, max: 5 },
  { key: 'benford_min_entries', label: 'Benford Minimum Entries', description: 'Minimum entries for Benford analysis', integer: true, fallback: 500, min: 100, max: 5000, step: 100 },
  { key: 'ghost_min_indicators', label: 'Ghost Employee Min Indicators', description: 'Indicators needed to flag as ghost', integer: true, fallback: 2, min: 1, max: 4 },
]

export const PAYROLL_TOGGLES = [
  { key: 'check_gap_enabled', label: 'Check Number Gaps' },
  { key: 'frequency_enabled', label: 'Pay Frequency Anomalies' },
  { key: 'benford_enabled', label: "Benford's Law Analysis" },
  { key: 'ghost_enabled', label: 'Ghost Employee Indicators' },
  { key: 'duplicate_bank_enabled', label: 'Duplicate Bank/Address' },
  { key: 'duplicate_tax_enabled', label: 'Duplicate Tax IDs' },
]

export const TWM_THRESHOLDS = [
  { key: 'amount_tolerance', label: 'Amount Tolerance', description: 'Maximum difference before flagging a variance', prefix: '$', step: '0.01', min: 0 },
  { key: 'price_variance_threshold', label: 'Price Variance Threshold', description: '% difference in unit price before flagging', suffix: '%', displayScale: 100, fallback: 5, step: 1, min: 1, max: 50 },
  { key: 'date_window_days', label: 'Date Window', description: 'Days between PO and receipt before flagging', suffix: 'd', integer: true, fallback: 30, min: 7, max: 180 },
  { key: 'fuzzy_vendor_threshold', label: 'Vendor Match Sensitivity', description: 'Minimum name similarity for fuzzy matching (0-100%)', suffix: '%', displayScale: 100, fallback: 85, step: 5, min: 50, max: 100 },
]
