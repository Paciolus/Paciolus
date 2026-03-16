/**
 * Paciolus API Client — Thin Orchestrator
 *
 * Composes transport, auth middleware, cache plugin, and download adapter.
 * All call sites continue to work via re-exports from this module.
 *
 * Architecture (Sprint 539):
 *   transport.ts      — base fetch, timeout, retry policy, error helpers
 *   authMiddleware.ts — CSRF state, token refresh callback, header injection
 *   cachePlugin.ts    — stale-while-revalidate, in-flight deduplication
 *   downloadAdapter.ts — file/blob download transport
 *   apiClient.ts      — this file, composes the above
 */

import {
  DEFAULT_REQUEST_TIMEOUT,
  BASE_RETRY_DELAY,
  MAX_RETRIES,
} from '@/utils/constants'

// --- Re-exports (preserve all existing import paths) ---
export type { ApiResponse, ApiRequestOptions } from '@/utils/transport'
export {
  parseApiError,
  isAuthError,
  isNotFoundError,
  isValidationError,
  getStatusMessage,
  IDEMPOTENT_METHODS,
  performFetch,
  buildUrl,
  isRetryableError,
} from '@/utils/transport'

export {
  setTokenRefreshCallback,
  setCsrfToken,
  getCsrfToken,
  fetchCsrfToken,
  CSRF_METHODS,
  injectAuthHeaders,
} from '@/utils/authMiddleware'

export {
  invalidateCache,
  getCacheStats,
  getCacheTelemetry,
  resetCacheTelemetry,
  startCacheSweep,
  stopCacheSweep,
  getCacheKey,
  getEndpointTtl,
  getCached,
  getCachedWithStale,
  setCached,
  invalidateRelatedCaches,
  inflightRequests,
} from '@/utils/cachePlugin'

export { apiDownload, downloadBlob } from '@/utils/downloadAdapter'

// --- Internal imports for orchestration ---
import type { ApiResponse, ApiRequestOptions } from '@/utils/transport'
import {
  performFetch,
  buildUrl,
  serializeBody,
  isRetryableError,
} from '@/utils/transport'

import {
  getTokenRefreshCallback,
  getCsrfToken as _getCsrfToken,
  fetchCsrfToken as _fetchCsrfToken,
  CSRF_METHODS as _CSRF_METHODS,
  injectAuthHeaders,
} from '@/utils/authMiddleware'

import {
  getCacheKey,
  getEndpointTtl,
  getCached,
  getCachedWithStale,
  setCached,
  invalidateRelatedCaches,
  inflightRequests,
  performBackgroundRevalidation,
} from '@/utils/cachePlugin'

const IDEMPOTENT = new Set(['GET', 'PUT', 'HEAD', 'OPTIONS']);

// =============================================================================
// CORE ORCHESTRATOR
// =============================================================================

/**
 * Make an authenticated API request with caching, deduplication, and retry support.
 */
export async function apiFetch<T>(
  endpoint: string,
  token: string | null,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    method = 'GET',
    body,
    headers: customHeaders = {},
    timeout = DEFAULT_REQUEST_TIMEOUT,
    skipCache = false,
    cacheTtl,
    retries = IDEMPOTENT.has(options.method ?? 'GET') ? MAX_RETRIES : 0,
    idempotencyKey,
    staleWhileRevalidate = false,
    onRevalidate,
  } = options;

  // Dev-mode warning: mutation retries without idempotency key
  if (
    process.env.NODE_ENV === 'development' &&
    retries > 0 &&
    !IDEMPOTENT.has(method) &&
    !idempotencyKey
  ) {
    console.warn(
      `[apiClient] ${method} ${endpoint}: retries=${retries} without idempotencyKey — risk of duplicate side effects`
    );
  }

  const isGetRequest = method === 'GET';
  const cacheKey = isGetRequest ? getCacheKey(endpoint, options) : '';

  // --- Cache check for GET requests ---
  if (isGetRequest && !skipCache && cacheKey) {
    if (staleWhileRevalidate) {
      const { data: staleData, isStale } = getCachedWithStale<T>(cacheKey);
      if (staleData !== null) {
        if (!isStale) {
          return { data: staleData, status: 200, ok: true, cached: true, stale: false };
        }
        performBackgroundRevalidation(endpoint, token, options, cacheKey, onRevalidate);
        return { data: staleData, status: 200, ok: true, cached: true, stale: true };
      }
    } else {
      const cached = getCached<T>(cacheKey);
      if (cached !== null) {
        return { data: cached, status: 200, ok: true, cached: true };
      }
    }
  }

  // --- In-flight deduplication ---
  if (isGetRequest && cacheKey && inflightRequests.has(cacheKey)) {
    return inflightRequests.get(cacheKey) as Promise<ApiResponse<T>>;
  }

  // --- Build headers ---
  const headers: Record<string, string> = { ...customHeaders };
  injectAuthHeaders(headers, token, method, idempotencyKey);

  const requestBody = serializeBody(body, headers);
  const url = buildUrl(endpoint);

  // --- Fetch with retry + 401 refresh ---
  const fetchPromise = (async (): Promise<ApiResponse<T>> => {
    let lastError: ApiResponse<T> | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const result = await performFetch<T>(url, headers, method, requestBody, timeout);

      if (result.ok) {
        if (isGetRequest && cacheKey) {
          const ttl = cacheTtl ?? getEndpointTtl(endpoint);
          setCached(cacheKey, result.data, ttl);
        }
        return result;
      }

      lastError = result;

      if (!isRetryableError(result.status) || attempt === retries) {
        break;
      }

      const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    // Silent token refresh on 401
    const tokenRefreshCallback = getTokenRefreshCallback();
    if (
      lastError?.status === 401 &&
      tokenRefreshCallback &&
      !endpoint.includes('/auth/refresh') &&
      !endpoint.includes('/auth/login') &&
      !endpoint.includes('/auth/register')
    ) {
      const newToken = await tokenRefreshCallback();
      if (newToken) {
        await _fetchCsrfToken(newToken);
        const refreshedHeaders = {
          ...headers,
          'Authorization': `Bearer ${newToken}`,
          ...(_getCsrfToken() && _CSRF_METHODS.has(method) ? { 'X-CSRF-Token': _getCsrfToken()! } : {}),
        };
        const retryResult = await performFetch<T>(url, refreshedHeaders, method, requestBody, timeout);
        if (retryResult.ok && isGetRequest && cacheKey) {
          const ttl = cacheTtl ?? getEndpointTtl(endpoint);
          setCached(cacheKey, retryResult.data, ttl);
        }
        return retryResult;
      }
    }

    return lastError!;
  })();

  // Track in-flight GET requests for deduplication
  if (isGetRequest && cacheKey) {
    inflightRequests.set(cacheKey, fetchPromise as Promise<ApiResponse<unknown>>);
    fetchPromise.finally(() => {
      inflightRequests.delete(cacheKey);
    });
  }

  return fetchPromise;
}

// =============================================================================
// CONVENIENCE METHODS
// =============================================================================

export async function apiGet<T>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, token, { ...options, method: 'GET' });
}

export async function apiPost<T>(
  endpoint: string,
  token: string | null,
  body: object | FormData,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'POST', body });
  if (result.ok) invalidateRelatedCaches(endpoint);
  return result;
}

export async function apiPut<T>(
  endpoint: string,
  token: string | null,
  body: object,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'PUT', body });
  if (result.ok) invalidateRelatedCaches(endpoint);
  return result;
}

export async function apiPatch<T>(
  endpoint: string,
  token: string | null,
  body: object,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'PATCH', body });
  if (result.ok) invalidateRelatedCaches(endpoint);
  return result;
}

export async function apiDelete<T = void>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'DELETE' });
  if (result.ok) invalidateRelatedCaches(endpoint);
  return result;
}

/**
 * Prefetch data for an endpoint in the background.
 */
export async function prefetch<T>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body' | 'staleWhileRevalidate' | 'onRevalidate'>
): Promise<void> {
  const cacheKey = getCacheKey(endpoint, { method: 'GET' });
  const cached = getCached<T>(cacheKey);
  if (cached !== null) return;
  if (inflightRequests.has(cacheKey)) return;

  try {
    await apiFetch<T>(endpoint, token, {
      ...options,
      method: 'GET',
      retries: 1,
    });
  } catch {
    // Silently fail for prefetch
  }
}
