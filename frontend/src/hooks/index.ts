/**
 * Paciolus Hooks
 * Centralized exports for custom React hooks.
 *
 * Phase 2 Refactor: Named exports only (no default exports)
 */

export { useClients } from './useClients';
export { useSettings } from './useSettings';
export { useActivityHistory } from './useActivityHistory';
export { useTrends, type TrendMetric } from './useTrends';
export { useIndustryRatios } from './useIndustryRatios';
export {
  useRollingWindow,
  type MomentumType,
  type RollingAverage,
  type MomentumIndicator,
  type RollingWindowMetric,
  type RollingWindowAnalysis,
  type RollingWindowResponse,
} from './useRollingWindow';
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
