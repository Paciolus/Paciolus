/**
 * Per-run setting inputs — Sprint 839.
 *
 * Parses the optional number fields on tool pages (bank reconciliation
 * materiality, three-way match tolerances). An empty field means "not set for
 * this run", so nothing is sent and the saved setting or Paciolus default
 * applies. A field that cannot be used returns an error message for display;
 * the page must not run with it.
 */

export interface ParsedRunInput {
  /** The parsed value, or undefined when the field is empty or invalid. */
  value: number | undefined
  /** A message to show next to the field, or null when the input is usable. */
  error: string | null
}

export interface RunInputRule {
  /** Inclusive lower bound (in the units the user types). Default 0. */
  min?: number
  /** Inclusive upper bound (in the units the user types). */
  max?: number
  /** Require a whole number. */
  integer?: boolean
  /** Field name used in messages, e.g. "Materiality". */
  label: string
  /** Allow a leading "$" and thousands separators (dollar amounts). */
  currency?: boolean
}

export function parseRunInput(raw: string, rule: RunInputRule): ParsedRunInput {
  const text = raw.trim()
  if (text === '') return { value: undefined, error: null }
  const cleaned = rule.currency ? text.replace(/^\$/, '').replace(/,/g, '') : text
  // Number('') and Number(' ') are 0, so the empty case is handled above;
  // reject anything that is not a plain decimal number.
  if (!/^-?(\d+\.?\d*|\.\d+)$/.test(cleaned)) {
    return { value: undefined, error: `${rule.label} must be a number.` }
  }
  const value = Number(cleaned)
  if (!Number.isFinite(value)) return { value: undefined, error: `${rule.label} must be a number.` }
  const min = rule.min ?? 0
  if (rule.integer && !Number.isInteger(value)) {
    return { value: undefined, error: `${rule.label} must be a whole number.` }
  }
  if (value < min || (rule.max !== undefined && value > rule.max)) {
    const range = rule.max !== undefined ? `between ${min} and ${rule.max}` : `${min} or more`
    return { value: undefined, error: `${rule.label} must be ${range}.` }
  }
  return { value, error: null }
}
