/**
 * Paciolus History Types
 * Audit history metadata types for the Heritage Timeline
 *
 * Day 14: Activity Logging & Metadata History
 *
 * IMPORTANT: Zero-Storage architecture means we store ONLY metadata,
 * never actual financial data. File contents are never persisted.
 *
 * GDPR/CCPA COMPLIANT: No PII stored, filenames are hashed.
 *
 * See: logs/dev-log.md for IP documentation
 */

// Audit activity entry - metadata only, no financial data stored
// Matches backend ActivityLogResponse model
export interface AuditActivity {
  id: number | string;
  timestamp: string;  // ISO 8601 format
  filenameHash: string;  // SHA-256 hash of filename
  filenameDisplay?: string;  // First 12 chars + "..." for UI display
  rowCount: number;
  balanced: boolean;
  totalDebits: number;
  totalCredits: number;
  difference?: number;  // Calculated client-side if not provided
  materialityThreshold: number;
  anomalyCount: number;
  materialCount: number;
  immaterialCount: number;
  isConsolidated?: boolean;
  sheetCount?: number;
}

// Backend API response for activity history
export interface ActivityHistoryResponse {
  activities: ActivityLogResponse[];
  total_count: number;
  page: number;
  page_size: number;
}

// Backend API response for single activity log
export interface ActivityLogResponse {
  id: number;
  filename_hash: string;
  filename_display: string | null;
  timestamp: string;
  record_count: number;
  total_debits: number;
  total_credits: number;
  materiality_threshold: number;
  was_balanced: boolean;
  anomaly_count: number;
  material_count: number;
  immaterial_count: number;
  is_consolidated: boolean;
  sheet_count: number | null;
}

// Convert backend response to frontend AuditActivity
export function mapActivityLogToAuditActivity(log: ActivityLogResponse): AuditActivity {
  return {
    id: log.id,
    timestamp: log.timestamp,
    filenameHash: log.filename_hash,
    filenameDisplay: log.filename_display || undefined,
    rowCount: log.record_count,
    balanced: log.was_balanced,
    totalDebits: log.total_debits,
    totalCredits: log.total_credits,
    difference: Math.abs(log.total_debits - log.total_credits),
    materialityThreshold: log.materiality_threshold,
    anomalyCount: log.anomaly_count,
    materialCount: log.material_count,
    immaterialCount: log.immaterial_count,
    isConsolidated: log.is_consolidated,
    sheetCount: log.sheet_count || undefined,
  };
}

// Stored metadata structure (localStorage - fallback for non-authenticated users)
export interface AuditHistoryStorage {
  version: string;
  activities: AuditActivity[];
  lastUpdated: string;
}

// Storage constants
export const HISTORY_STORAGE_KEY = 'paciolus_audit_history';
export const HISTORY_VERSION = '1.0.0';
export const MAX_HISTORY_ENTRIES = 50;  // Limit stored entries

// What IS stored vs NOT stored (for Zero-Storage transparency)
export const STORED_METADATA = [
  'Timestamp of audit',
  'File hash (SHA-256, not actual filename)',
  'Row count',
  'Balance status (Balanced/Unbalanced)',
  'Summary totals (Debits/Credits)',
  'Materiality threshold used',
  'Anomaly counts (aggregate only)',
] as const;

export const NOT_STORED = [
  'Actual file contents',
  'Account names or details',
  'Individual transactions',
  'Specific anomaly descriptions',
  'Original filename (only hash stored)',
  'Any PII (Personally Identifiable Information)',
] as const;
