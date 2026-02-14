/**
 * Paciolus Client Types
 * Sprint 16: Client Core Infrastructure
 *
 * TypeScript interfaces for client management.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Client objects contain ONLY identification metadata
 * - No financial data, transactions, or audit results are included
 * - Client-specific audits remain ephemeral (in-memory only)
 */

/**
 * Industry classification for clients.
 * Matches the backend Industry enum.
 */
export type Industry =
  | 'technology'
  | 'healthcare'
  | 'financial_services'
  | 'manufacturing'
  | 'retail'
  | 'professional_services'
  | 'real_estate'
  | 'construction'
  | 'hospitality'
  | 'nonprofit'
  | 'education'
  | 'other';

/**
 * Industry option for dropdowns.
 */
export interface IndustryOption {
  value: Industry;
  label: string;
}

/**
 * Industry labels for display.
 */
export const INDUSTRY_LABELS: Record<Industry, string> = {
  technology: 'Technology',
  healthcare: 'Healthcare',
  financial_services: 'Financial Services',
  manufacturing: 'Manufacturing',
  retail: 'Retail',
  professional_services: 'Professional Services',
  real_estate: 'Real Estate',
  construction: 'Construction',
  hospitality: 'Hospitality',
  nonprofit: 'Nonprofit',
  education: 'Education',
  other: 'Other',
};

/**
 * Client entity.
 *
 * Represents a CFO's client company.
 *
 * DATA BOUNDARY:
 * | What IS Stored          | What is NEVER Stored         |
 * |-------------------------|------------------------------|
 * | Client name             | Trial balance data           |
 * | Industry classification | Transaction details          |
 * | Fiscal year end         | Account balances             |
 * | Created/updated times   | Audit results                |
 */
export interface Client {
  /** Unique identifier */
  id: number;
  /** Owner user ID (for multi-tenant isolation) */
  user_id: number;
  /** Client company name */
  name: string;
  /** Industry classification */
  industry: Industry;
  /** Fiscal year end date (MM-DD format) */
  fiscal_year_end: string;
  /** ISO timestamp of creation */
  created_at: string;
  /** ISO timestamp of last update */
  updated_at: string;
  /** JSON string of client-specific settings */
  settings: string;
}

/**
 * Input for creating a new client.
 */
export interface ClientCreateInput {
  name: string;
  industry?: Industry;
  fiscal_year_end?: string;
  settings?: string;
}

/**
 * Input for updating a client.
 */
export interface ClientUpdateInput {
  name?: string;
  industry?: Industry;
  fiscal_year_end?: string;
  settings?: string;
}

/**
 * Paginated client list response.
 */
export interface ClientListResponse {
  clients: Client[];
  total_count: number;
  page: number;
  page_size: number;
}

/**
 * Client preferences stored as JSON in the client model.
 * Simple per-client preferences (distinct from ClientSettings in settings.ts
 * which is used for materiality formulas).
 */
export interface ClientPreferences {
  /** Default materiality threshold for this client */
  default_materiality_threshold?: number;
  /** Preferred column mappings for this client's files */
  default_column_mapping?: {
    account_column?: string;
    debit_column?: string;
    credit_column?: string;
  };
  /** Notes about this client (not financial data) */
  notes?: string;
}

/**
 * Parse client preferences from JSON string.
 */
export function parseClientPreferences(settingsJson: string): ClientPreferences {
  try {
    return JSON.parse(settingsJson) as ClientPreferences;
  } catch {
    return {};
  }
}

/**
 * Stringify client preferences to JSON.
 */
export function stringifyClientPreferences(settings: ClientPreferences): string {
  return JSON.stringify(settings);
}

/**
 * Format fiscal year end for display.
 * @param fiscalYearEnd MM-DD format string
 * @returns Human-readable format (e.g., "December 31")
 */
export function formatFiscalYearEnd(fiscalYearEnd: string): string {
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const [month = 0, day = 0] = fiscalYearEnd.split('-').map(Number);
  if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
    return `${months[month - 1]!} ${day}`;
  }
  return fiscalYearEnd;
}

/**
 * Common fiscal year end options for dropdown.
 */
export const FISCAL_YEAR_END_OPTIONS = [
  { value: '12-31', label: 'December 31 (Calendar Year)' },
  { value: '06-30', label: 'June 30' },
  { value: '03-31', label: 'March 31' },
  { value: '09-30', label: 'September 30' },
  { value: '01-31', label: 'January 31' },
];
