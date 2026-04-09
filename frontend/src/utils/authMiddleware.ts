/**
 * Auth middleware layer for API client.
 *
 * Owns: CSRF token state, token refresh callback, auth header injection.
 * No cache, retry, or transport concerns.
 */

import { API_URL } from '@/utils/constants'

// =============================================================================
// TOKEN REFRESH CALLBACK (Sprint 198)
// =============================================================================

let _tokenRefreshCallback: (() => Promise<string | null>) | null = null;

export function setTokenRefreshCallback(cb: (() => Promise<string | null>) | null): void {
  _tokenRefreshCallback = cb;
}

export function getTokenRefreshCallback(): (() => Promise<string | null>) | null {
  return _tokenRefreshCallback;
}

// =============================================================================
// CSRF TOKEN MANAGEMENT (Sprint 200)
// =============================================================================

let _csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  _csrfToken = token;
}

export function getCsrfToken(): string | null {
  return _csrfToken;
}

/**
 * Fetch a fresh CSRF token from the backend (auth-guarded endpoint).
 * Auth is provided via HttpOnly cookie — no Bearer header needed.
 */
export async function fetchCsrfToken(_accessToken?: string): Promise<string | null> {
  try {
    const response = await fetch(`${API_URL}/auth/csrf`, {
      credentials: 'include',
    });
    if (response.ok) {
      const data = await response.json();
      _csrfToken = data.csrf_token;
      return _csrfToken;
    }
  } catch {
    // CSRF fetch failure is non-fatal
  }
  return null;
}

/** HTTP methods that require CSRF token injection. */
export const CSRF_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

/**
 * Inject CSRF and idempotency headers into a request header object.
 *
 * Access token is delivered via HttpOnly cookie (set by the backend on
 * login/register/refresh) — the browser sends it automatically with
 * credentials: 'include'.  No Authorization header is injected for
 * browser clients, eliminating JS-readable token exposure.
 *
 * Non-browser API clients can still send Authorization: Bearer manually.
 */
export function injectAuthHeaders(
  headers: Record<string, string>,
  _token: string | null,
  method: string,
  idempotencyKey?: string
): void {
  if (CSRF_METHODS.has(method) && _csrfToken) {
    headers['X-CSRF-Token'] = _csrfToken;
  }
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }
}
