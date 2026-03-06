/**
 * Paciolus Utility Functions
 * Phase 1 Refactor: Centralized utilities
 */

// Formatting utilities
export {
  formatCurrency,
  formatCurrencyWhole,
  parseCurrency,
  formatNumber,
  formatPercent,
  formatPercentWhole,
  formatDate,
  formatTime,
  formatDateTime,
  formatDateTimeCompact,
  getRelativeTime,
} from './formatting';

// API client utilities
export {
  apiFetch,
  apiGet,
  apiPost,
  apiPut,
  apiPatch,
  apiDelete,
  apiDownload,
  downloadBlob,
  parseApiError,
  isAuthError,
  isNotFoundError,
  isValidationError,
  getStatusMessage,
  // Cache utilities (Sprint 41)
  invalidateCache,
  getCacheStats,
  prefetch,
  // Cache telemetry + sweep control (Sprint 417)
  getCacheTelemetry,
  resetCacheTelemetry,
  stopCacheSweep,
  startCacheSweep,
  // Token refresh callback (Sprint 198)
  setTokenRefreshCallback,
  // CSRF token management (Sprint 200)
  setCsrfToken,
  getCsrfToken,
  fetchCsrfToken,
} from './apiClient';

export type { ApiResponse, ApiRequestOptions } from './apiClient';

// Theme utilities (Oat & Obsidian)
export {
  // Threshold status
  THRESHOLD_STATUS_CLASSES,
  getThresholdClasses,
  getThresholdLabel,
  // Variance/trend
  getVarianceClasses,
  // Input state
  INPUT_BASE_CLASSES,
  INPUT_STATE_CLASSES,
  getInputClasses,
  getSelectClasses,
  // Badges
  BADGE_CLASSES,
  getBadgeClasses,
  // Risk levels
  RISK_LEVEL_CLASSES,
  getRiskLevelClasses,
  // Animation presets
  SPRING,
  // Animation variants
  createTimelineEntryVariants,
  createTimelineNodeVariants,
  // Utility
  cx,
} from './themeUtils';

export type {
  ThresholdStatus,
  ThresholdClasses,
  VarianceDirection,
  InputState,
  BadgeVariant,
  RiskLevel,
} from './themeUtils';

// Marketing motion presets (Sprint 337)
export {
  VIEWPORT,
  DRAW,
  HOVER,
  AXIS,
  CountUp,
} from './marketingMotion'

// Motion tokens (Sprint 401)
export {
  TIMING,
  EASE,
  STATE_CROSSFADE,
  RESOLVE_ENTER,
  EMPHASIS_SETTLE,
} from './motionTokens';
