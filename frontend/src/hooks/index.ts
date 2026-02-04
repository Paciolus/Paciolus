/**
 * Paciolus Hooks
 * Centralized exports for custom React hooks.
 *
 * Phase 2 Refactor: Named exports only (no default exports)
 */

export { useClients } from './useClients';
export { useSettings } from './useSettings';
export {
  useFormValidation,
  commonValidators,
  type ValidationRule,
  type ValidationRules,
  type FormValues,
  type FormErrors,
  type TouchedFields,
  type UseFormValidationConfig,
  type UseFormValidationReturn,
} from './useFormValidation';
