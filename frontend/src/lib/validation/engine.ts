/**
 * Pure validation engine (Sprint 752 — Phase 4 hook decomposition).
 *
 * No React imports. Functions are deterministic and side-effect free,
 * so they're trivially testable without `renderHook` and reusable
 * outside React components (CLI scripts, server-side validation, etc.).
 *
 * The React adapter (`hooks/useFormValidation`) wires these into
 * `useState` + `useCallback` + `useMemo`; consumers that just want to
 * "validate this object once" should import from here directly.
 */

/** Single validation rule for a field. */
export interface ValidationRule<T, K extends keyof T = keyof T> {
  /** Returns `true` if the value passes the rule. */
  test: (value: T[K], allValues: T) => boolean
  /** Error message surfaced when `test` returns `false`. */
  message: string
}

/** Validation rules indexed by field name. */
export type ValidationRules<T> = {
  [K in keyof T]?: ValidationRule<T, K>[]
}

/** Errors object — field name → first failing message (or undefined). */
export type FormErrors<T> = {
  [K in keyof T]?: string
}

/** Touched flags — field name → has-been-blurred. */
export type TouchedFields<T> = {
  [K in keyof T]?: boolean
}

/** Base constraint — any object with string keys. */
export type FormValues = Record<string, unknown>

/**
 * Run the rules for a single field and return the first failing message,
 * or `undefined` if every rule passes (or no rules exist).
 */
export function validateFieldValue<T extends FormValues, K extends keyof T>(
  field: K,
  values: T,
  rules: ValidationRules<T>,
): string | undefined {
  const fieldRules = rules[field]
  if (!fieldRules || fieldRules.length === 0) {
    return undefined
  }
  const value = values[field]
  for (const rule of fieldRules) {
    if (!rule.test(value, values)) {
      return rule.message
    }
  }
  return undefined
}

/**
 * Run every field's rules; return the full errors map. Pure — does not
 * mutate inputs.
 */
export function validateAllFields<T extends FormValues>(
  values: T,
  rules: ValidationRules<T>,
): FormErrors<T> {
  const errors: FormErrors<T> = {}
  for (const field of Object.keys(rules) as (keyof T)[]) {
    const error = validateFieldValue(field, values, rules)
    if (error) {
      errors[field] = error
    }
  }
  return errors
}

/**
 * Convenience: returns `true` iff every field passes its rules. Avoids
 * allocating the errors map when callers only need the boolean.
 */
export function isFormValid<T extends FormValues>(
  values: T,
  rules: ValidationRules<T>,
): boolean {
  for (const field of Object.keys(rules) as (keyof T)[]) {
    if (validateFieldValue(field, values, rules) !== undefined) {
      return false
    }
  }
  return true
}

/**
 * Returns `true` if any field in `values` differs from its corresponding
 * entry in `initialValues`. Uses `Object.is`-style strict equality
 * (matches React's reconciliation default).
 */
export function isFormDirty<T extends FormValues>(values: T, initialValues: T): boolean {
  for (const key of Object.keys(initialValues) as (keyof T)[]) {
    if (values[key] !== initialValues[key]) return true
  }
  return false
}
