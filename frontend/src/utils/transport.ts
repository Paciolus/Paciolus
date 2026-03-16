/**
 * Low-level HTTP transport layer.
 *
 * Owns: base fetch with timeout, error parsing, retry policy helpers.
 * No auth, cache, or download concerns — those compose on top.
 */

import {
  API_URL,
  DEFAULT_REQUEST_TIMEOUT,
  BASE_RETRY_DELAY,
  MAX_RETRIES,
} from '@/utils/constants'

// =============================================================================
// TYPES
// =============================================================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
  ok: boolean;
  /** Whether the response came from cache */
  cached?: boolean;
  /** Whether the cached data is stale (past TTL but still usable) */
  stale?: boolean;
}

export interface ApiRequestOptions {
  /** HTTP method (default: GET) */
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  /** Request body (will be JSON stringified). Accepts any typed object or FormData. */
  body?: object | FormData;
  /** Additional headers */
  headers?: Record<string, string>;
  /** Request timeout in ms (default: DEFAULT_REQUEST_TIMEOUT) */
  timeout?: number;
  /** Skip cache lookup (default: false) */
  skipCache?: boolean;
  /** Cache TTL in ms (default: 300000 = 5 minutes) */
  cacheTtl?: number;
  /**
   * Number of retry attempts for failed requests.
   * Default: MAX_RETRIES for idempotent methods (GET, PUT, HEAD, OPTIONS), 0 for mutations (POST, DELETE, PATCH).
   * RFC 9110 Section 9.2.2: only idempotent methods are safe to retry automatically.
   */
  retries?: number;
  /**
   * Idempotency key for safe mutation retries.
   * When provided, injected as `Idempotency-Key` header so the server can deduplicate.
   * Required when explicitly setting retries > 0 on non-idempotent methods.
   */
  idempotencyKey?: string;
  /**
   * Enable stale-while-revalidate pattern.
   * If true, returns stale cached data immediately while fetching fresh data in background.
   * The callback is called when fresh data arrives.
   */
  staleWhileRevalidate?: boolean;
  /** Callback when background revalidation completes (for SWR pattern) */
  onRevalidate?: (response: ApiResponse<unknown>) => void;
}

/** HTTP methods safe to retry automatically (RFC 9110 Section 9.2.2). */
export const IDEMPOTENT_METHODS = new Set(['GET', 'PUT', 'HEAD', 'OPTIONS']);

// =============================================================================
// ERROR HANDLING
// =============================================================================

/**
 * Parse an error into a user-friendly message.
 */
export function parseApiError(
  err: unknown,
  fallbackMessage: string = 'An unexpected error occurred'
): string {
  if (err instanceof Error) {
    return err.message;
  }
  if (typeof err === 'string') {
    return err;
  }
  return fallbackMessage;
}

export function isAuthError(status: number): boolean {
  return status === 401 || status === 403;
}

export function isNotFoundError(status: number): boolean {
  return status === 404;
}

export function isValidationError(status: number): boolean {
  return status === 422;
}

export function isRetryableError(status: number): boolean {
  return status === 0 || status === 429 || (status >= 500 && status < 600);
}

export function getStatusMessage(status: number): string {
  const messages: Record<number, string> = {
    400: 'Invalid request',
    401: 'Session expired. Please log in again.',
    403: 'Access denied',
    404: 'Not found',
    422: 'Validation error',
    429: 'Too many requests. Please try again later.',
    500: 'Server error. Please try again.',
    502: 'Service temporarily unavailable',
    503: 'Service temporarily unavailable',
  };
  return messages[status] || `Request failed (${status})`;
}

// =============================================================================
// CORE FETCH
// =============================================================================

/**
 * Internal fetch implementation with timeout and error handling.
 */
export async function performFetch<T>(
  url: string,
  headers: Record<string, string>,
  method: string,
  requestBody: string | FormData | undefined,
  timeout: number
): Promise<ApiResponse<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: requestBody,
      signal: controller.signal,
      credentials: 'include',
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage: string;

      try {
        const errorData = await response.json();
        const detail = errorData.detail;
        if (Array.isArray(detail) && detail.length > 0) {
          const first = detail[0];
          const field = first.loc?.slice(1).join('.') || '';
          errorMessage = field ? `${field}: ${first.msg}` : first.msg || getStatusMessage(response.status);
        } else if (typeof detail === 'object' && detail !== null) {
          errorMessage = detail.message || detail.code || getStatusMessage(response.status);
        } else {
          errorMessage = detail || errorData.message || getStatusMessage(response.status);
        }
      } catch {
        errorMessage = getStatusMessage(response.status);
      }

      return {
        error: errorMessage,
        status: response.status,
        ok: false,
      };
    }

    if (response.status === 204) {
      return {
        data: undefined as T,
        status: response.status,
        ok: true,
      };
    }

    const data = await response.json();
    return {
      data,
      status: response.status,
      ok: true,
    };
  } catch (err) {
    clearTimeout(timeoutId);

    if (err instanceof Error && err.name === 'AbortError') {
      return {
        error: 'Request timed out',
        status: 0,
        ok: false,
      };
    }

    return {
      error: parseApiError(err, 'Network error. Please check your connection.'),
      status: 0,
      ok: false,
    };
  }
}

/**
 * Build a full URL from an endpoint string.
 */
export function buildUrl(endpoint: string): string {
  return endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;
}

/**
 * Serialize a request body for fetch.
 */
export function serializeBody(
  body: object | FormData | undefined,
  headers: Record<string, string>
): string | FormData | undefined {
  if (!body) return undefined;
  if (body instanceof FormData) return body;
  headers['Content-Type'] = 'application/json';
  return JSON.stringify(body);
}

export { DEFAULT_REQUEST_TIMEOUT, BASE_RETRY_DELAY, MAX_RETRIES }
