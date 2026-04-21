/**
 * Trial-balance upload orchestration — shared by the main TB audit hook
 * and any tool that needs to POST a TB file to /audit/trial-balance
 * (e.g. the multi-period comparison page, which audits each period
 * independently before running the comparison step).
 *
 * Centralizes:
 *   - FormData construction (file, threshold, overrides, mapping, sheets, engagement, preflight)
 *   - uploadFetch invocation (CSRF, HttpOnly-cookie auth, unified error shaping)
 *   - 401 / 403 / 422 / 429 / 5xx message selection via getActionableUploadError
 *
 * Call sites should NOT hand-build FormData or call apiPost(FormData) directly;
 * that bypass skips the upload-specific error semantics and diverges messages.
 */
import type { ColumnMapping } from '@/components/mapping'
import type {
  AuditResult,
  AuditResultResponse,
  AuditRunResponse,
} from '@/types/diagnostic'
import { isAuditErrorResponse } from '@/types/diagnostic'
import { uploadFetch, type UploadTransportResult } from '@/utils/uploadTransport'

export interface TrialBalanceUploadArgs {
  file: File
  materialityThreshold: number
  /** MappingContext overrides (account -> type) */
  accountTypeOverrides?: Record<string, string>
  columnMapping?: ColumnMapping | null
  selectedSheets?: string[] | null
  engagementId?: number | null
  preflightToken?: string | null
}

/** Build the FormData body expected by POST /audit/trial-balance. */
export function buildTrialBalanceFormData(args: TrialBalanceUploadArgs): FormData {
  const fd = new FormData()
  fd.append('file', args.file)
  fd.append('materiality_threshold', args.materialityThreshold.toString())

  if (args.accountTypeOverrides && Object.keys(args.accountTypeOverrides).length > 0) {
    fd.append('account_type_overrides', JSON.stringify(args.accountTypeOverrides))
  }
  if (args.columnMapping) {
    fd.append('column_mapping', JSON.stringify(args.columnMapping))
  }
  if (args.selectedSheets && args.selectedSheets.length > 0) {
    fd.append('selected_sheets', JSON.stringify(args.selectedSheets))
  }
  if (args.engagementId !== null && args.engagementId !== undefined) {
    fd.append('engagement_id', args.engagementId.toString())
  }
  if (args.preflightToken) {
    fd.append('preflight_token', args.preflightToken)
  }
  return fd
}

export type TrialBalanceUploadOutcome =
  | { kind: 'success'; result: AuditResultResponse }
  | { kind: 'audit_error'; message: string }
  | { kind: 'auth'; message: string }
  | { kind: 'email_not_verified'; message: string }
  | { kind: 'forbidden'; message: string }
  | { kind: 'transport'; status: number; message: string }

const EMAIL_NOT_VERIFIED_MSG =
  'Please verify your email address before running diagnostics. Check your inbox for the verification link.'

/** Map a failed UploadTransportResult into a UI-friendly outcome. */
export function classifyTrialBalanceFailure(
  raw: UploadTransportResult,
): TrialBalanceUploadOutcome {
  if (raw.status === 401) {
    return { kind: 'auth', message: 'Please sign in to run diagnostics.' }
  }
  if (raw.errorCode === 'EMAIL_NOT_VERIFIED') {
    return { kind: 'email_not_verified', message: EMAIL_NOT_VERIFIED_MSG }
  }
  if (raw.status === 403) {
    return { kind: 'forbidden', message: 'Access denied.' }
  }
  return {
    kind: 'transport',
    status: raw.status,
    message: raw.error || `Failed to analyze file (${raw.status})`,
  }
}

/**
 * POST a trial balance file to /audit/trial-balance.
 *
 * Returns a discriminated outcome — callers pattern-match on `outcome.kind`
 * and are insulated from transport details (status codes, errorCode strings).
 *
 * The second argument is the legacy `token` parameter forwarded to
 * uploadFetch for signature compatibility; in production, auth flows
 * through the HttpOnly access cookie (credentials: 'include') and the
 * token is unused.
 */
export async function uploadTrialBalance(
  args: TrialBalanceUploadArgs,
  token: string | null = null,
): Promise<TrialBalanceUploadOutcome> {
  const formData = buildTrialBalanceFormData(args)
  const raw = await uploadFetch<AuditRunResponse>('/audit/trial-balance', formData, token)

  if (!raw.ok) {
    return classifyTrialBalanceFailure(raw)
  }

  const data = raw.data
  if (!data || isAuditErrorResponse(data)) {
    const err = data as { message?: string; detail?: string } | undefined
    return {
      kind: 'audit_error',
      message: err?.message || err?.detail || 'Failed to analyze file',
    }
  }

  return { kind: 'success', result: data }
}

/**
 * Convenience: collapse a TrialBalanceUploadOutcome into the
 * `(AuditResult | null, string | null)` pair used by legacy call sites.
 */
export function outcomeToLegacyPair(
  outcome: TrialBalanceUploadOutcome,
): { result: AuditResult | null; error: string | null } {
  if (outcome.kind === 'success') {
    return { result: outcome.result as AuditResult, error: null }
  }
  return { result: null, error: outcome.message }
}
