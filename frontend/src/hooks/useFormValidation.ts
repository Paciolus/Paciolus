/**
 * useFormValidation — React adapter over the pure validation engine.
 *
 * Sprint 752: split into `lib/validation/engine.ts` (pure functions +
 * types) + `lib/validation/validators.ts` (commonValidators) + this
 * adapter (`useState` + `useCallback` + `useMemo` glue).
 *
 * The adapter owns React-only concerns:
 *   - state slots (values, errors, touched, isSubmitting, isSubmitted)
 *   - event handlers (handleChange, handleBlur, handleSubmit)
 *   - render-stable convenience getters (getFieldProps, getFieldState)
 *
 * Re-exports types + commonValidators from the engine + validators
 * modules for backward compatibility — existing call sites
 * (`import { useFormValidation, commonValidators } from '@/hooks'`)
 * continue to work without churn.
 *
 * @example
 * const { values, errors, handleSubmit, isValid } = useFormValidation({
 *   initialValues: { name: '', email: '' },
 *   validationRules: {
 *     name: [commonValidators.required(), commonValidators.minLength(2)],
 *     email: [commonValidators.required(), commonValidators.email()],
 *   },
 *   onSubmit: async (values) => { ... },
 * })
 */
import { useCallback, useMemo, useState } from 'react'
import {
  type FormErrors,
  type FormValues,
  type TouchedFields,
  type ValidationRules,
  isFormDirty,
  isFormValid as isFormValidPure,
  validateAllFields,
  validateFieldValue,
} from '@/lib/validation/engine'

// Re-export engine types so existing call sites keep their imports.
export type {
  FormErrors,
  FormValues,
  TouchedFields,
  ValidationRule,
  ValidationRules,
} from '@/lib/validation/engine'
export { commonValidators } from '@/lib/validation/validators'

/** Configuration for `useFormValidation`. */
export interface UseFormValidationConfig<T extends FormValues> {
  /** Initial form values. */
  initialValues: T
  /** Validation rules per field. */
  validationRules?: ValidationRules<T>
  /** Callback invoked when the form submits and `validate()` returns true. */
  onSubmit?: (values: T) => void | Promise<void>
  /** Validate inside `setValue` / `handleChange` (default: false). */
  validateOnChange?: boolean
  /** Validate inside `handleBlur` (default: true). */
  validateOnBlur?: boolean
}

/** Return type of `useFormValidation`. */
export interface UseFormValidationReturn<T extends FormValues> {
  values: T
  errors: FormErrors<T>
  touched: TouchedFields<T>
  isSubmitting: boolean
  isSubmitted: boolean
  isValid: boolean
  isDirty: boolean

  setValue: <K extends keyof T>(field: K, value: T[K]) => void
  setValues: (values: Partial<T>) => void
  handleChange: (
    field: keyof T,
  ) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void
  handleBlur: (field: keyof T) => () => void
  setTouched: (field: keyof T, isTouched?: boolean) => void
  setAllTouched: () => void

  validateField: (field: keyof T) => string | undefined
  validate: () => boolean
  setError: (field: keyof T, message: string | undefined) => void
  clearErrors: () => void

  handleSubmit: (e?: React.FormEvent) => Promise<void>
  reset: (newInitialValues?: T) => void
  getFieldProps: (field: keyof T) => {
    value: T[keyof T]
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void
    onBlur: () => void
  }
  getFieldState: (field: keyof T) => {
    error: string | undefined
    touched: boolean
    hasValue: boolean
    hasError: boolean
    showError: boolean
  }
}

export function useFormValidation<T extends FormValues>(
  config: UseFormValidationConfig<T>,
): UseFormValidationReturn<T> {
  const {
    initialValues,
    validationRules = {} as ValidationRules<T>,
    onSubmit,
    validateOnChange = false,
    validateOnBlur = true,
  } = config

  const [values, setValuesState] = useState<T>(initialValues)
  const [errors, setErrors] = useState<FormErrors<T>>({})
  const [touched, setTouchedState] = useState<TouchedFields<T>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  // ----- Validation (delegates to the pure engine) -----

  const validateField = useCallback(
    (field: keyof T) => validateFieldValue(field, values, validationRules),
    [values, validationRules],
  )

  const validate = useCallback((): boolean => {
    const newErrors = validateAllFields(values, validationRules)
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [values, validationRules])

  // ----- Computed (memoized over values + rules) -----

  const isValid = useMemo(
    () => isFormValidPure(values, validationRules),
    [values, validationRules],
  )

  const isDirty = useMemo(
    () => isFormDirty(values, initialValues),
    [values, initialValues],
  )

  // ----- Field handlers -----

  const setValue = useCallback(
    <K extends keyof T>(field: K, value: T[K]) => {
      setValuesState(prev => {
        const next = { ...prev, [field]: value }
        if (validateOnChange) {
          // Validate against the post-update values so the closure stays
          // consistent. Updating errors inside the setter callback avoids
          // the stale-closure bug the legacy hook hid behind a setTimeout.
          const error = validateFieldValue(field, next, validationRules)
          setErrors(prevErrors => ({ ...prevErrors, [field]: error }))
        }
        return next
      })
    },
    [validateOnChange, validationRules],
  )

  const setValues = useCallback((newValues: Partial<T>) => {
    setValuesState(prev => ({ ...prev, ...newValues }))
  }, [])

  const handleChange = useCallback(
    (field: keyof T) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { type } = e.target
        const value =
          type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value
        setValue(field, value as T[keyof T])
      },
    [setValue],
  )

  const handleBlur = useCallback(
    (field: keyof T) => () => {
      setTouchedState(prev => ({ ...prev, [field]: true }))
      if (validateOnBlur) {
        const error = validateFieldValue(field, values, validationRules)
        setErrors(prev => ({ ...prev, [field]: error }))
      }
    },
    [validateOnBlur, values, validationRules],
  )

  const setTouched = useCallback((field: keyof T, isTouched = true) => {
    setTouchedState(prev => ({ ...prev, [field]: isTouched }))
  }, [])

  const setAllTouched = useCallback(() => {
    const allTouched: TouchedFields<T> = {}
    for (const key of Object.keys(initialValues) as (keyof T)[]) {
      allTouched[key] = true
    }
    setTouchedState(allTouched)
  }, [initialValues])

  // ----- Error handlers -----

  const setError = useCallback((field: keyof T, message: string | undefined) => {
    setErrors(prev => ({ ...prev, [field]: message }))
  }, [])

  const clearErrors = useCallback(() => {
    setErrors({})
  }, [])

  // ----- Form actions -----

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault()
      setIsSubmitted(true)
      setAllTouched()
      if (!validate()) return
      if (onSubmit) {
        setIsSubmitting(true)
        try {
          await onSubmit(values)
        } finally {
          setIsSubmitting(false)
        }
      }
    },
    [validate, onSubmit, values, setAllTouched],
  )

  const reset = useCallback(
    (newInitialValues?: T) => {
      const resetValues = newInitialValues ?? initialValues
      setValuesState(resetValues)
      setErrors({})
      setTouchedState({})
      setIsSubmitting(false)
      setIsSubmitted(false)
    },
    [initialValues],
  )

  // ----- Convenience getters -----

  const getFieldProps = useCallback(
    (field: keyof T) => ({
      value: values[field],
      onChange: handleChange(field),
      onBlur: handleBlur(field),
    }),
    [values, handleChange, handleBlur],
  )

  const getFieldState = useCallback(
    (field: keyof T) => {
      const error = errors[field]
      const isTouched = touched[field] ?? false
      const value = values[field]
      const hasValue = value !== undefined && value !== null && value !== ''
      return {
        error,
        touched: isTouched,
        hasValue,
        hasError: !!error,
        showError: (isTouched || isSubmitted) && !!error,
      }
    },
    [errors, touched, values, isSubmitted],
  )

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isSubmitted,
    isValid,
    isDirty,

    setValue,
    setValues,
    handleChange,
    handleBlur,
    setTouched,
    setAllTouched,

    validateField,
    validate,
    setError,
    clearErrors,

    handleSubmit,
    reset,
    getFieldProps,
    getFieldState,
  }
}

export default useFormValidation
