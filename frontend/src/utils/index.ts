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
} from './apiClient';

export type { ApiResponse, ApiRequestOptions } from './apiClient';

// Theme utilities (Oat & Obsidian)
export {
  // Health status
  HEALTH_STATUS_CLASSES,
  getHealthClasses,
  getHealthLabel,
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
  // Animation variants
  MODAL_OVERLAY_VARIANTS,
  MODAL_CONTENT_VARIANTS,
  CONTAINER_VARIANTS,
  createContainerVariants,
  createCardStaggerVariants,
  createTimelineEntryVariants,
  createTimelineNodeVariants,
  // Utility
  cx,
} from './themeUtils';

export type {
  HealthStatus,
  HealthClasses,
  VarianceDirection,
  InputState,
  BadgeVariant,
  RiskLevel,
} from './themeUtils';
