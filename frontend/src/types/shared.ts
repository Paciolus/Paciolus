/**
 * Shared Types (Sprint 225)
 *
 * Cross-domain type definitions used by diagnostics, testing, engagement,
 * and other modules. Single source of truth for common enumerations.
 */

// ─── Severity ────────────────────────────────────────────────────────────────
// Canonical severity type used across ALL domains:
//   - Diagnostics: abnormal balances, classification issues, balance sheet validation
//   - Testing: flagged entries in all 7 testing tools
//   - Three-Way Match: variance severity
//   - Follow-Up Items: item severity
// Backend enforces: Literal["high", "medium", "low"] in all Pydantic response schemas.

export type Severity = 'high' | 'medium' | 'low'

// ─── Upload Status ───────────────────────────────────────────────────────────
// Shared upload/processing lifecycle status used by useAuditUpload, PeriodFileDropZone, etc.

export type UploadStatus = 'idle' | 'loading' | 'success' | 'error'
