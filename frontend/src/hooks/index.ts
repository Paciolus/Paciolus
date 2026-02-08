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
export {
  useBatchUpload,
  type BatchStats,
  type UseBatchUploadReturn,
} from './useBatchUpload';
export {
  useFetchData,
  type UseFetchDataOptions,
  type UseFetchDataReturn,
} from './useFetchData';
export {
  useBenchmarks,
  type BenchmarkData,
  type BenchmarkSet,
  type BenchmarkComparisonResult,
  type BenchmarkComparisonResponse,
  type BenchmarkSourceInfo,
  type BenchmarkSourcesResponse,
} from './useBenchmarks';
export {
  usePriorPeriod,
  type UsePriorPeriodReturn,
} from './usePriorPeriod';
export {
  useAdjustments,
  type UseAdjustmentsReturn,
} from './useAdjustments';
export {
  useVerification,
  type UseVerificationReturn,
} from './useVerification';
export {
  useMultiPeriodComparison,
  type AccountMovement,
  type BudgetVariance,
  type LeadSheetMovementSummary,
  type MovementSummaryResponse,
  type UseMultiPeriodComparisonReturn,
} from './useMultiPeriodComparison';
export {
  useJETesting,
  type UseJETestingReturn,
} from './useJETesting';
export {
  useAPTesting,
  type UseAPTestingReturn,
} from './useAPTesting';
export {
  useFileUpload,
  type UseFileUploadReturn,
} from './useFileUpload';
export {
  useAuditUpload,
  type UseAuditUploadReturn,
} from './useAuditUpload';
export {
  useBankReconciliation,
  type UseBankReconciliationReturn,
} from './useBankReconciliation';
export {
  usePayrollTesting,
  type UsePayrollTestingReturn,
} from './usePayrollTesting';
export {
  useTestingExport,
  type UseTestingExportReturn,
  type ExportType,
} from './useTestingExport';
export {
  useThreeWayMatch,
  type UseThreeWayMatchReturn,
} from './useThreeWayMatch';
export {
  useEngagement,
  type UseEngagementReturn,
} from './useEngagement';
export {
  useFollowUpItems,
  type UseFollowUpItemsReturn,
} from './useFollowUpItems';
