/**
 * uploadTransport — Shared upload fetch primitive (Sprint 519 Phase 1A)
 *
 * Encapsulates: Authorization header, CSRF token injection,
 * and unified 401/403/5xx error semantics for FormData uploads.
 *
 * Replaces direct fetch() calls in useAuditUpload, usePreflight,
 * useTrialBalanceAudit, and BatchUploadContext.
 */

import { getCsrfToken } from '@/utils/apiClient'
import { API_URL } from '@/utils/constants'

export interface UploadTransportResult<T = unknown> {
  ok: boolean
  status: number
  data?: T
  error?: string
  /** Structured error code from 403 responses (e.g., 'EMAIL_NOT_VERIFIED') */
  errorCode?: string
}

/**
 * Perform an authenticated FormData upload to the given endpoint.
 *
 * Handles:
 * - Authorization header attachment (Bearer token)
 * - CSRF token injection (X-CSRF-Token)
 * - 401 → { ok: false, error: 'auth', status: 401 }
 * - 403 with EMAIL_NOT_VERIFIED code → { ok: false, errorCode: 'EMAIL_NOT_VERIFIED', status: 403 }
 * - 403 generic → { ok: false, error: 'access_denied', status: 403 }
 * - 4xx/5xx → { ok: false, error: detail string, status }
 * - Network error → { ok: false, error: message, status: 0 }
 */
export async function uploadFetch<T = unknown>(
  endpoint: string,
  formData: FormData,
  token: string | null,
): Promise<UploadTransportResult<T>> {
  try {
    const csrfToken = getCsrfToken()
    const headers: Record<string, string> = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    if (csrfToken) headers['X-CSRF-Token'] = csrfToken

    const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'include',
    })

    if (response.status === 401) {
      return { ok: false, status: 401, error: 'auth' }
    }

    if (response.status === 403) {
      const errData = await response.json().catch(() => ({}))
      const detail = errData.detail
      if (typeof detail === 'object' && detail?.code === 'EMAIL_NOT_VERIFIED') {
        return { ok: false, status: 403, error: 'email_not_verified', errorCode: 'EMAIL_NOT_VERIFIED' }
      }
      return { ok: false, status: 403, error: 'access_denied' }
    }

    const data = await response.json()

    if (response.ok) {
      return { ok: true, status: response.status, data: data as T }
    }

    // 4xx/5xx with body
    const errorMessage = data.detail || data.message || `Request failed (${response.status})`
    return { ok: false, status: response.status, error: errorMessage }
  } catch {
    return { ok: false, status: 0, error: 'Unable to connect to server. Please try again.' }
  }
}
