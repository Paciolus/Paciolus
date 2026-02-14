/**
 * useFormValidation - Shared Form Validation Hook
 *
 * Abstracts common form patterns from:
 * - CreateClientModal (field-level validation, touched tracking)
 * - Login/Register pages (form-level validation, submit state)
 *
 * Features:
 * - Generic type support for form values
 * - Declarative validation rules
 * - Per-field and form-level validation
 * - Touched state tracking
 * - Submit state management
 * - Reset functionality
 *
 * @example
 * const { values, errors, touched, handleChange, handleBlur, handleSubmit, isValid } = useFormValidation({
 *   initialValues: { name: '', email: '' },
 *   validationRules: {
 *     name: [
 *       { test: (v) => !!v.trim(), message: 'Name is required' },
 *       { test: (v) => v.length >= 2, message: 'Name must be at least 2 characters' },
 *     ],
 *     email: [
 *       { test: (v) => !!v.trim(), message: 'Email is required' },
 *       { test: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), message: 'Invalid email format' },
 *     ],
 *   },
 *   onSubmit: async (values) => { ... },
 * });
 */

import { useState, useCallback, useMemo } from 'react';

// ============================================================================
// Types
// ============================================================================

/**
 * Single validation rule for a field
 */
export interface ValidationRule<T, K extends keyof T = keyof T> {
  /** Test function - returns true if valid */
  test: (value: T[K], allValues: T) => boolean;
  /** Error message to display when test fails */
  message: string;
}

/**
 * Validation rules mapped to form field keys
 */
export type ValidationRules<T> = {
  [K in keyof T]?: ValidationRule<T, K>[];
};

/**
 * Errors object - maps field names to error messages
 */
export type FormErrors<T> = {
  [K in keyof T]?: string;
};

/**
 * Touched state - maps field names to boolean (has been blurred)
 */
export type TouchedFields<T> = {
  [K in keyof T]?: boolean;
};

/**
 * Base constraint for form values - allows any object with string keys
 */
export type FormValues = Record<string, unknown>;

/**
 * Configuration for useFormValidation hook
 */
export interface UseFormValidationConfig<T extends FormValues> {
  /** Initial form values */
  initialValues: T;
  /** Validation rules per field */
  validationRules?: ValidationRules<T>;
  /** Callback when form is submitted and valid */
  onSubmit?: (values: T) => void | Promise<void>;
  /** Whether to validate on change (default: false, validates on blur) */
  validateOnChange?: boolean;
  /** Whether to validate on blur (default: true) */
  validateOnBlur?: boolean;
}

/**
 * Return type of useFormValidation hook
 */
export interface UseFormValidationReturn<T extends FormValues> {
  /** Current form values */
  values: T;
  /** Current validation errors */
  errors: FormErrors<T>;
  /** Fields that have been touched (blurred) */
  touched: TouchedFields<T>;
  /** Whether form is currently submitting */
  isSubmitting: boolean;
  /** Whether form has been submitted at least once */
  isSubmitted: boolean;
  /** Whether all fields are valid */
  isValid: boolean;
  /** Whether form has any changes from initial values */
  isDirty: boolean;

  // Field handlers
  /** Set a single field value */
  setValue: <K extends keyof T>(field: K, value: T[K]) => void;
  /** Set multiple field values at once */
  setValues: (values: Partial<T>) => void;
  /** Handle input change event */
  handleChange: (field: keyof T) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
  /** Handle field blur event */
  handleBlur: (field: keyof T) => () => void;
  /** Set a field as touched */
  setTouched: (field: keyof T, isTouched?: boolean) => void;
  /** Set all fields as touched */
  setAllTouched: () => void;

  // Validation
  /** Validate a single field, returns error message or undefined */
  validateField: (field: keyof T) => string | undefined;
  /** Validate all fields, returns true if valid */
  validate: () => boolean;
  /** Set a custom error for a field */
  setError: (field: keyof T, message: string | undefined) => void;
  /** Clear all errors */
  clearErrors: () => void;

  // Form actions
  /** Handle form submission */
  handleSubmit: (e?: React.FormEvent) => Promise<void>;
  /** Reset form to initial values */
  reset: (newInitialValues?: T) => void;
  /** Get props for an input field (value, onChange, onBlur) */
  getFieldProps: (field: keyof T) => {
    value: T[keyof T];
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
    onBlur: () => void;
  };
  /** Get field state (error, touched, hasValue) for styling */
  getFieldState: (field: keyof T) => {
    error: string | undefined;
    touched: boolean;
    hasValue: boolean;
    hasError: boolean;
    showError: boolean;
  };
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useFormValidation<T extends FormValues>(
  config: UseFormValidationConfig<T>
): UseFormValidationReturn<T> {
  const {
    initialValues,
    validationRules = {} as ValidationRules<T>,
    onSubmit,
    validateOnChange = false,
    validateOnBlur = true,
  } = config;

  // Core state
  const [values, setValuesState] = useState<T>(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [touched, setTouchedState] = useState<TouchedFields<T>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  // -------------------------------------------------------------------------
  // Validation
  // -------------------------------------------------------------------------

  /**
   * Validate a single field against its rules
   */
  const validateField = useCallback(
    (field: keyof T): string | undefined => {
      const fieldRules = validationRules[field];
      if (!fieldRules || fieldRules.length === 0) {
        return undefined;
      }

      const value = values[field];

      for (const rule of fieldRules) {
        if (!rule.test(value, values)) {
          return rule.message;
        }
      }

      return undefined;
    },
    [values, validationRules]
  );

  /**
   * Validate all fields
   */
  const validate = useCallback((): boolean => {
    const newErrors: FormErrors<T> = {};
    let isValid = true;

    // Validate each field that has rules
    for (const field of Object.keys(validationRules) as (keyof T)[]) {
      const error = validateField(field);
      if (error) {
        newErrors[field] = error;
        isValid = false;
      }
    }

    setErrors(newErrors);
    return isValid;
  }, [validateField, validationRules]);

  // -------------------------------------------------------------------------
  // Computed values
  // -------------------------------------------------------------------------

  const isValid = useMemo(() => {
    for (const field of Object.keys(validationRules) as (keyof T)[]) {
      const error = validateField(field);
      if (error) return false;
    }
    return true;
  }, [validateField, validationRules]);

  const isDirty = useMemo(() => {
    for (const key of Object.keys(initialValues) as (keyof T)[]) {
      if (values[key] !== initialValues[key]) return true;
    }
    return false;
  }, [values, initialValues]);

  // -------------------------------------------------------------------------
  // Field handlers
  // -------------------------------------------------------------------------

  const setValue = useCallback(
    <K extends keyof T>(field: K, value: T[K]) => {
      setValuesState((prev) => ({ ...prev, [field]: value }));

      if (validateOnChange) {
        // Validate after state update
        setTimeout(() => {
          const fieldRules = validationRules[field];
          if (fieldRules) {
            const newValues = { ...values, [field]: value };
            let error: string | undefined;
            for (const rule of fieldRules) {
              if (!rule.test(value, newValues)) {
                error = rule.message;
                break;
              }
            }
            setErrors((prev) => ({ ...prev, [field]: error }));
          }
        }, 0);
      }
    },
    [validateOnChange, validationRules, values]
  );

  const setValues = useCallback((newValues: Partial<T>) => {
    setValuesState((prev) => ({ ...prev, ...newValues }));
  }, []);

  const handleChange = useCallback(
    (field: keyof T) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { type } = e.target;
        const value = type === 'checkbox'
          ? (e.target as HTMLInputElement).checked
          : e.target.value;
        setValue(field, value as T[keyof T]);
      },
    [setValue]
  );

  const handleBlur = useCallback(
    (field: keyof T) => () => {
      setTouchedState((prev) => ({ ...prev, [field]: true }));

      if (validateOnBlur) {
        const error = validateField(field);
        setErrors((prev) => ({ ...prev, [field]: error }));
      }
    },
    [validateOnBlur, validateField]
  );

  const setTouched = useCallback((field: keyof T, isTouched = true) => {
    setTouchedState((prev) => ({ ...prev, [field]: isTouched }));
  }, []);

  const setAllTouched = useCallback(() => {
    const allTouched: TouchedFields<T> = {};
    for (const key of Object.keys(initialValues) as (keyof T)[]) {
      allTouched[key] = true;
    }
    setTouchedState(allTouched);
  }, [initialValues]);

  // -------------------------------------------------------------------------
  // Error handlers
  // -------------------------------------------------------------------------

  const setError = useCallback((field: keyof T, message: string | undefined) => {
    setErrors((prev) => ({ ...prev, [field]: message }));
  }, []);

  const clearErrors = useCallback(() => {
    setErrors({});
  }, []);

  // -------------------------------------------------------------------------
  // Form actions
  // -------------------------------------------------------------------------

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) {
        e.preventDefault();
      }

      setIsSubmitted(true);
      setAllTouched();

      if (!validate()) {
        return;
      }

      if (onSubmit) {
        setIsSubmitting(true);
        try {
          await onSubmit(values);
        } finally {
          setIsSubmitting(false);
        }
      }
    },
    [validate, onSubmit, values, setAllTouched]
  );

  const reset = useCallback(
    (newInitialValues?: T) => {
      const resetValues = newInitialValues ?? initialValues;
      setValuesState(resetValues);
      setErrors({});
      setTouchedState({});
      setIsSubmitting(false);
      setIsSubmitted(false);
    },
    [initialValues]
  );

  // -------------------------------------------------------------------------
  // Convenience getters
  // -------------------------------------------------------------------------

  const getFieldProps = useCallback(
    (field: keyof T) => ({
      value: values[field],
      onChange: handleChange(field),
      onBlur: handleBlur(field),
    }),
    [values, handleChange, handleBlur]
  );

  const getFieldState = useCallback(
    (field: keyof T) => {
      const error = errors[field];
      const isTouched = touched[field] ?? false;
      const value = values[field];
      const hasValue = value !== undefined && value !== null && value !== '';

      return {
        error,
        touched: isTouched,
        hasValue,
        hasError: !!error,
        showError: (isTouched || isSubmitted) && !!error,
      };
    },
    [errors, touched, values, isSubmitted]
  );

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    // State
    values,
    errors,
    touched,
    isSubmitting,
    isSubmitted,
    isValid,
    isDirty,

    // Field handlers
    setValue,
    setValues,
    handleChange,
    handleBlur,
    setTouched,
    setAllTouched,

    // Validation
    validateField,
    validate,
    setError,
    clearErrors,

    // Form actions
    handleSubmit,
    reset,
    getFieldProps,
    getFieldState,
  };
}

// ============================================================================
// Common Validation Rules (Reusable)
// ============================================================================

/**
 * Pre-built validation rules for common use cases
 */
export const commonValidators = {
  /** Field is required (non-empty after trim) */
  required: (message = 'This field is required'): ValidationRule<FormValues> => ({
    test: (value) => {
      if (typeof value === 'string') return value.trim().length > 0;
      if (typeof value === 'boolean') return true; // Booleans are always "filled"
      return value !== null && value !== undefined;
    },
    message,
  }),

  /** Minimum length for strings */
  minLength: (min: number, message?: string): ValidationRule<FormValues> => ({
    test: (value) => {
      if (typeof value !== 'string') return true;
      return value.trim().length >= min;
    },
    message: message ?? `Must be at least ${min} characters`,
  }),

  /** Maximum length for strings */
  maxLength: (max: number, message?: string): ValidationRule<FormValues> => ({
    test: (value) => {
      if (typeof value !== 'string') return true;
      return value.trim().length <= max;
    },
    message: message ?? `Must be no more than ${max} characters`,
  }),

  /** Valid email format */
  email: (message = 'Invalid email address'): ValidationRule<FormValues> => ({
    test: (value) => {
      if (typeof value !== 'string' || !value.trim()) return true; // Let required handle empty
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    message,
  }),

  /** Matches another field (e.g., confirm password) */
  matches: <T extends FormValues>(
    otherField: keyof T,
    message = 'Fields must match'
  ): ValidationRule<T> => ({
    test: (value, allValues) => value === allValues[otherField],
    message,
  }),

  /** Minimum numeric value */
  min: (min: number, message?: string): ValidationRule<FormValues> => ({
    test: (value) => {
      const num = typeof value === 'string' ? parseFloat(value) : value;
      if (typeof num !== 'number' || isNaN(num)) return true;
      return num >= min;
    },
    message: message ?? `Must be at least ${min}`,
  }),

  /** Maximum numeric value */
  max: (max: number, message?: string): ValidationRule<FormValues> => ({
    test: (value) => {
      const num = typeof value === 'string' ? parseFloat(value) : value;
      if (typeof num !== 'number' || isNaN(num)) return true;
      return num <= max;
    },
    message: message ?? `Must be no more than ${max}`,
  }),

  /** Custom regex pattern */
  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule<FormValues> => ({
    test: (value) => {
      if (typeof value !== 'string' || !value.trim()) return true;
      return regex.test(value);
    },
    message,
  }),
};

export default useFormValidation;
