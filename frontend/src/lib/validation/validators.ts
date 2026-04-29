/**
 * Reusable validation rule builders (Sprint 752).
 *
 * Pure factories — call each one to get a `ValidationRule` you can plug
 * into `ValidationRules<T>`. Decoupled from the React hook so they can
 * be unit-tested directly and reused outside React.
 */

import type { FormValues, ValidationRule } from '@/lib/validation/engine'

export const commonValidators = {
  /** Field is required (non-empty after trim for strings; non-null otherwise). */
  required: (message = 'This field is required'): ValidationRule<FormValues> => ({
    test: value => {
      if (typeof value === 'string') return value.trim().length > 0
      if (typeof value === 'boolean') return true // Booleans are always "filled"
      return value !== null && value !== undefined
    },
    message,
  }),

  /** Minimum string length (after trim). Skipped for non-strings. */
  minLength: (min: number, message?: string): ValidationRule<FormValues> => ({
    test: value => {
      if (typeof value !== 'string') return true
      return value.trim().length >= min
    },
    message: message ?? `Must be at least ${min} characters`,
  }),

  /** Maximum string length (after trim). Skipped for non-strings. */
  maxLength: (max: number, message?: string): ValidationRule<FormValues> => ({
    test: value => {
      if (typeof value !== 'string') return true
      return value.trim().length <= max
    },
    message: message ?? `Must be no more than ${max} characters`,
  }),

  /** RFC-shaped email format (intentionally pragmatic, not RFC 5322). */
  email: (message = 'Invalid email address'): ValidationRule<FormValues> => ({
    test: value => {
      if (typeof value !== 'string' || !value.trim()) return true // Let `required` handle empty
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
    },
    message,
  }),

  /** Field equals another field (e.g., confirm password). */
  matches: <T extends FormValues>(
    otherField: keyof T,
    message = 'Fields must match',
  ): ValidationRule<T> => ({
    test: (value, allValues) => value === allValues[otherField],
    message,
  }),

  /** Numeric minimum. Strings are parsed via `parseFloat`. */
  min: (min: number, message?: string): ValidationRule<FormValues> => ({
    test: value => {
      const num = typeof value === 'string' ? parseFloat(value) : value
      if (typeof num !== 'number' || isNaN(num)) return true
      return num >= min
    },
    message: message ?? `Must be at least ${min}`,
  }),

  /** Numeric maximum. Strings are parsed via `parseFloat`. */
  max: (max: number, message?: string): ValidationRule<FormValues> => ({
    test: value => {
      const num = typeof value === 'string' ? parseFloat(value) : value
      if (typeof num !== 'number' || isNaN(num)) return true
      return num <= max
    },
    message: message ?? `Must be no more than ${max}`,
  }),

  /** Custom regex. Empty strings pass — pair with `required` to enforce. */
  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule<FormValues> => ({
    test: value => {
      if (typeof value !== 'string' || !value.trim()) return true
      return regex.test(value)
    },
    message,
  }),
}
