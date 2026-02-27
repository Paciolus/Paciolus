/**
 * Paciolus API Client Utilities
 * Phase 1 Refactor: Shared authenticated fetch functions
 * Sprint 41: Added caching, request deduplication, and retry logic
 *
 * Eliminates duplicate fetch/auth/error handling patterns across hooks.
 *
 * ZERO-STORAGE: No data persistence, pure API communication.
 * Cache is in-memory only and cleared on page refresh.
 */

import {
  API_URL,
  DEFAULT_REQUEST_TIMEOUT,
  DOWNLOAD_TIMEOUT,
  MAX_RETRIES,
  BASE_RETRY_DELAY,
  DEFAULT_CACHE_TTL,
  MAX_CACHE_ENTRIES,
  minutes,
  hours,
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

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

// =============================================================================
// TOKEN REFRESH CALLBACK (Sprint 198)
// =============================================================================

/**
 * Callback registered by AuthContext to handle 401 token refresh.
 * Returns the new access token if refresh succeeds, null if it fails.
 */
let _tokenRefreshCallback: (() => Promise<string | null>) | null = null;

/**
 * Register a callback that will be invoked when a 401 is received.
 * Called by AuthProvider on mount to wire up silent token refresh.
 */
export function setTokenRefreshCallback(cb: (() => Promise<string | null>) | null): void {
  _tokenRefreshCallback = cb;
}

// =============================================================================
// CSRF TOKEN MANAGEMENT (Sprint 200)
// =============================================================================

/** Module-level CSRF token — set by AuthContext after login/register/refresh. */
let _csrfToken: string | null = null;

/** Store the CSRF token (called by AuthContext). */
export function setCsrfToken(token: string | null): void {
  _csrfToken = token;
}

/** Get the current CSRF token (used by direct-fetch callers like useAuditUpload). */
export function getCsrfToken(): string | null {
  return _csrfToken;
}

/**
 * Fetch a fresh CSRF token from the backend (auth-guarded endpoint).
 * Primarily used for edge-case re-fetches when the CSRF token expires
 * before the access token (30-min CSRF vs 30-min access token window).
 * Normal flow: read csrf_token from login/register/refresh responses instead.
 *
 * @param accessToken - Bearer token to authenticate the request (required since /auth/csrf is auth-guarded)
 */
export async function fetchCsrfToken(accessToken?: string): Promise<string | null> {
  try {
    const headers: HeadersInit = {}
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
    const response = await fetch(`${API_URL}/auth/csrf`, { headers });
    if (response.ok) {
      const data = await response.json();
      _csrfToken = data.csrf_token;
      return _csrfToken;
    }
  } catch {
    // CSRF fetch failure is non-fatal — request may still succeed
    // if the backend CSRF middleware is not yet enforcing
  }
  return null;
}

/** HTTP methods that require CSRF token injection. */
const CSRF_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

/** HTTP methods safe to retry automatically (RFC 9110 Section 9.2.2). */
const IDEMPOTENT_METHODS = new Set(['GET', 'PUT', 'HEAD', 'OPTIONS']);

// =============================================================================
// CACHE & DEDUPLICATION STATE
// =============================================================================

/** In-memory cache for GET request responses */
const queryCache = new Map<string, CacheEntry<unknown>>();

/** Cache telemetry counters. */
const cacheTelemetry = { hits: 0, misses: 0, evictions: 0, staleReturns: 0 };

/** Handle for the periodic cache sweep timer. */
let sweepTimerId: ReturnType<typeof setInterval> | null = null;

/** Track in-flight requests to prevent duplicate concurrent calls */
const inflightRequests = new Map<string, Promise<ApiResponse<unknown>>>();

/** Default cache TTL values by endpoint pattern (in milliseconds) */
const ENDPOINT_TTL_CONFIG: Record<string, number> = {
  '/clients/industries': hours(1),
  '/settings/practice': minutes(30),
  '/industry-ratios': minutes(30),
  '/trends': minutes(10),
  '/rolling-analysis': minutes(10),
  '/clients': minutes(10),
  '/activity/history': minutes(5),
  '/activity/recent': minutes(5),
  '/diagnostics/summary': minutes(10),
  '/dashboard/stats': minutes(1),
  '/engagements': minutes(2),
  '/periods': minutes(10),
};

// =============================================================================
// CACHE UTILITIES
// =============================================================================

/**
 * Generate a cache key from endpoint and options.
 */
function getCacheKey(endpoint: string, options: ApiRequestOptions = {}): string {
  // Only cache GET requests
  if (options.method && options.method !== 'GET') {
    return '';
  }
  // Include relevant options in key (excluding body for GET)
  const keyParts = [endpoint];
  if (options.headers) {
    keyParts.push(JSON.stringify(options.headers));
  }
  return keyParts.join('|');
}

/**
 * Get TTL for an endpoint based on configuration.
 */
function getEndpointTtl(endpoint: string): number {
  for (const [pattern, ttl] of Object.entries(ENDPOINT_TTL_CONFIG)) {
    if (endpoint.includes(pattern)) {
      return ttl;
    }
  }
  return DEFAULT_CACHE_TTL;
}

/**
 * Check if a cache entry is still valid.
 */
function isCacheValid<T>(entry: CacheEntry<T>): boolean {
  return Date.now() - entry.timestamp < entry.ttl;
}

/**
 * Get a cached response if valid.
 * Uses Map delete+re-set trick to move accessed entry to end (LRU touch).
 */
function getCached<T>(key: string): T | null {
  if (!key) return null;

  const entry = queryCache.get(key) as CacheEntry<T> | undefined;
  if (entry && isCacheValid(entry)) {
    // LRU touch: move to end of insertion order
    queryCache.delete(key);
    queryCache.set(key, entry);
    cacheTelemetry.hits++;
    return entry.data;
  }

  // Clean up expired entry
  if (entry) {
    queryCache.delete(key);
  }
  cacheTelemetry.misses++;
  return null;
}

/**
 * Get cached data even if stale (for SWR pattern).
 * Returns { data, isStale } where isStale indicates if data is past TTL.
 */
function getCachedWithStale<T>(key: string): { data: T | null; isStale: boolean } {
  if (!key) return { data: null, isStale: false };

  const entry = queryCache.get(key) as CacheEntry<T> | undefined;
  if (!entry) {
    cacheTelemetry.misses++;
    return { data: null, isStale: false };
  }

  const isStale = !isCacheValid(entry);
  if (isStale) {
    cacheTelemetry.staleReturns++;
  } else {
    // LRU touch for fresh entries
    queryCache.delete(key);
    queryCache.set(key, entry);
    cacheTelemetry.hits++;
  }
  return { data: entry.data, isStale };
}

/**
 * Perform background revalidation for SWR pattern.
 * Fetches fresh data and updates cache, then calls onRevalidate callback.
 */
async function performBackgroundRevalidation<T>(
  endpoint: string,
  token: string | null,
  options: ApiRequestOptions,
  cacheKey: string,
  onRevalidate?: (response: ApiResponse<unknown>) => void
): Promise<void> {
  const {
    headers: customHeaders = {},
    timeout = DEFAULT_REQUEST_TIMEOUT,
    cacheTtl,
    retries = MAX_RETRIES,
  } = options;

  // Build headers
  const headers: Record<string, string> = { ...customHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;

  try {
    // Perform fetch with retry
    let lastError: ApiResponse<T> | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const result = await performFetch<T>(url, headers, 'GET', undefined, timeout);

      if (result.ok) {
        // Update cache with fresh data
        const ttl = cacheTtl ?? getEndpointTtl(endpoint);
        setCached(cacheKey, result.data, ttl);

        // Notify caller of fresh data
        if (onRevalidate) {
          onRevalidate({
            ...result,
            cached: false,
            stale: false,
          });
        }
        return;
      }

      lastError = result;

      if (!isRetryableError(result.status) || attempt === retries) {
        break;
      }

      const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    // Background revalidation failed - log but don't throw
    console.warn(`Background revalidation failed for ${endpoint}:`, lastError?.error);
  } catch (err) {
    console.warn(`Background revalidation error for ${endpoint}:`, err);
  }
}

/**
 * Store a response in cache.
 * Evicts oldest entry (first key in Map insertion order) when at capacity.
 */
function setCached<T>(key: string, data: T, ttl: number): void {
  if (!key) return;

  // If key already exists, delete first so re-set moves it to end
  if (queryCache.has(key)) {
    queryCache.delete(key);
  }

  // LRU eviction: remove oldest entries until under capacity
  while (queryCache.size >= MAX_CACHE_ENTRIES) {
    const oldest = queryCache.keys().next().value;
    if (oldest !== undefined) {
      queryCache.delete(oldest);
      cacheTelemetry.evictions++;
    }
  }

  queryCache.set(key, {
    data,
    timestamp: Date.now(),
    ttl,
  });
}

/**
 * Invalidate cache entries matching a pattern.
 *
 * @example
 * // Invalidate all client-related cache
 * invalidateCache('/clients');
 *
 * // Invalidate specific client
 * invalidateCache('/clients/123');
 *
 * // Clear all cache
 * invalidateCache();
 */
export function invalidateCache(pattern?: string): void {
  if (!pattern) {
    queryCache.clear();
    return;
  }

  for (const key of queryCache.keys()) {
    if (key.includes(pattern)) {
      queryCache.delete(key);
    }
  }
}

/**
 * Get cache statistics for debugging.
 */
export function getCacheStats(): { size: number; keys: string[] } {
  return {
    size: queryCache.size,
    keys: Array.from(queryCache.keys()),
  };
}

/**
 * Get cache telemetry counters (hits, misses, evictions, staleReturns).
 */
export function getCacheTelemetry(): { hits: number; misses: number; evictions: number; staleReturns: number } {
  return { ...cacheTelemetry };
}

/**
 * Reset cache telemetry counters to zero (for testing).
 */
export function resetCacheTelemetry(): void {
  cacheTelemetry.hits = 0;
  cacheTelemetry.misses = 0;
  cacheTelemetry.evictions = 0;
  cacheTelemetry.staleReturns = 0;
}

/**
 * Remove all expired entries from the cache.
 */
function sweepExpiredEntries(): void {
  for (const [key, entry] of queryCache.entries()) {
    if (!isCacheValid(entry as CacheEntry<unknown>)) {
      queryCache.delete(key);
    }
  }
}

/**
 * Start the periodic cache sweep timer (60s interval).
 * Only runs in browser environments.
 */
export function startCacheSweep(): void {
  if (sweepTimerId !== null) return;
  if (typeof window === 'undefined') return;
  sweepTimerId = setInterval(sweepExpiredEntries, 60_000);
}

/**
 * Stop the periodic cache sweep timer.
 */
export function stopCacheSweep(): void {
  if (sweepTimerId !== null) {
    clearInterval(sweepTimerId);
    sweepTimerId = null;
  }
}

// Auto-start sweep in browser environments
if (typeof window !== 'undefined') {
  startCacheSweep();
}

/**
 * Prefetch data for an endpoint in the background.
 * Useful for preloading next pages or related data.
 *
 * @example
 * // Prefetch next page while viewing current
 * prefetch('/activity/history?page=2&page_size=50', token);
 *
 * // Prefetch related client data
 * prefetch(`/clients/${clientId}/trends`, token);
 */
export async function prefetch<T>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body' | 'staleWhileRevalidate' | 'onRevalidate'>
): Promise<void> {
  const cacheKey = getCacheKey(endpoint, { method: 'GET' });

  // Skip if already cached and fresh
  const cached = getCached<T>(cacheKey);
  if (cached !== null) {
    return;
  }

  // Skip if already being fetched
  if (inflightRequests.has(cacheKey)) {
    return;
  }

  // Fetch in background (don't await in calling code)
  try {
    await apiFetch<T>(endpoint, token, {
      ...options,
      method: 'GET',
      // Lower priority for prefetch - fewer retries
      retries: 1,
    });
  } catch {
    // Silently fail for prefetch - it's opportunistic
  }
}

// =============================================================================
// ERROR HANDLING
// =============================================================================

/**
 * Parse an error into a user-friendly message.
 *
 * @example
 * parseApiError(new Error("Network failed"))  // "Network failed"
 * parseApiError(undefined)                     // "An unexpected error occurred"
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

/**
 * Check if an HTTP status code indicates an authentication error.
 */
export function isAuthError(status: number): boolean {
  return status === 401 || status === 403;
}

/**
 * Check if an HTTP status code indicates a not found error.
 */
export function isNotFoundError(status: number): boolean {
  return status === 404;
}

/**
 * Check if an HTTP status code indicates a validation error.
 */
export function isValidationError(status: number): boolean {
  return status === 422;
}

/**
 * Check if an error is retryable (network errors, 5xx, 429).
 */
function isRetryableError(status: number): boolean {
  // Network errors (status 0) and server errors are retryable
  return status === 0 || status === 429 || (status >= 500 && status < 600);
}

/**
 * Get a human-readable message for common HTTP status codes.
 */
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
// API CLIENT
// =============================================================================

/**
 * Internal fetch implementation with timeout and error handling.
 */
async function performFetch<T>(
  url: string,
  headers: Record<string, string>,
  method: string,
  requestBody: string | FormData | undefined,
  timeout: number
): Promise<ApiResponse<T>> {
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method,
      headers,
      body: requestBody,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Handle non-OK responses
    if (!response.ok) {
      let errorMessage: string;

      try {
        const errorData = await response.json();
        const detail = errorData.detail;
        // Handle Pydantic 422 validation errors: detail is array of {msg, loc, type}
        if (Array.isArray(detail) && detail.length > 0) {
          const first = detail[0];
          const field = first.loc?.slice(1).join('.') || '';
          errorMessage = field ? `${field}: ${first.msg}` : first.msg || getStatusMessage(response.status);
        // Handle structured error detail from require_verified_user (e.g. {code, message})
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

    // Parse successful response
    // Handle 204 No Content
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

    // Handle abort (timeout)
    if (err instanceof Error && err.name === 'AbortError') {
      return {
        error: 'Request timed out',
        status: 0,
        ok: false,
      };
    }

    // Handle network errors
    return {
      error: parseApiError(err, 'Network error. Please check your connection.'),
      status: 0,
      ok: false,
    };
  }
}

/**
 * Make an authenticated API request with caching, deduplication, and retry support.
 *
 * Features:
 * - Authorization header injection
 * - JSON serialization/parsing
 * - Response caching for GET requests (configurable TTL)
 * - Request deduplication (concurrent identical requests share one network call)
 * - Automatic retry with exponential backoff for transient failures
 * - Timeout handling
 *
 * @example
 * // GET request (cached by default)
 * const { data, error, ok, cached } = await apiFetch<User[]>('/clients', token);
 *
 * // POST request with body (not cached)
 * const { data, error } = await apiFetch<Client>('/clients', token, {
 *   method: 'POST',
 *   body: { name: 'Acme Corp', industry: 'technology' }
 * });
 *
 * // Force fresh data (skip cache)
 * const { data } = await apiFetch<Client[]>('/clients', token, { skipCache: true });
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
    retries = IDEMPOTENT_METHODS.has(options.method ?? 'GET') ? MAX_RETRIES : 0,
    idempotencyKey,
    staleWhileRevalidate = false,
    onRevalidate,
  } = options;

  // Dev-mode warning: mutation retries without idempotency key risk duplicate side effects
  if (
    process.env.NODE_ENV === 'development' &&
    retries > 0 &&
    !IDEMPOTENT_METHODS.has(method) &&
    !idempotencyKey
  ) {
    console.warn(
      `[apiClient] ${method} ${endpoint}: retries=${retries} without idempotencyKey — risk of duplicate side effects`
    );
  }

  const isGetRequest = method === 'GET';
  const cacheKey = isGetRequest ? getCacheKey(endpoint, options) : '';

  // Check cache for GET requests
  if (isGetRequest && !skipCache && cacheKey) {
    // For SWR pattern, check if we have stale data to return immediately
    if (staleWhileRevalidate) {
      const { data: staleData, isStale } = getCachedWithStale<T>(cacheKey);
      if (staleData !== null) {
        if (!isStale) {
          // Fresh cache - return immediately
          return {
            data: staleData,
            status: 200,
            ok: true,
            cached: true,
            stale: false,
          };
        }
        // Stale cache - return stale data and trigger background revalidation
        // Don't await - let it run in background
        performBackgroundRevalidation(endpoint, token, options, cacheKey, onRevalidate);
        return {
          data: staleData,
          status: 200,
          ok: true,
          cached: true,
          stale: true,
        };
      }
    } else {
      // Standard cache check (fresh only)
      const cached = getCached<T>(cacheKey);
      if (cached !== null) {
        return {
          data: cached,
          status: 200,
          ok: true,
          cached: true,
        };
      }
    }
  }

  // Check for in-flight request (deduplication)
  if (isGetRequest && cacheKey && inflightRequests.has(cacheKey)) {
    return inflightRequests.get(cacheKey) as Promise<ApiResponse<T>>;
  }

  // Build headers
  const headers: Record<string, string> = {
    ...customHeaders,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Sprint 200: Inject CSRF token for mutation requests
  if (CSRF_METHODS.has(method) && _csrfToken) {
    headers['X-CSRF-Token'] = _csrfToken;
  }

  // Sprint 417: Inject idempotency key for safe mutation retries
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }

  // Handle body - FormData doesn't need Content-Type (browser sets it with boundary)
  let requestBody: string | FormData | undefined;
  if (body) {
    if (body instanceof FormData) {
      requestBody = body;
    } else {
      headers['Content-Type'] = 'application/json';
      requestBody = JSON.stringify(body);
    }
  }

  // Build full URL
  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;

  // Create the fetch promise with retry logic
  const fetchPromise = (async (): Promise<ApiResponse<T>> => {
    let lastError: ApiResponse<T> | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const result = await performFetch<T>(url, headers, method, requestBody, timeout);

      if (result.ok) {
        // Cache successful GET responses
        if (isGetRequest && cacheKey) {
          const ttl = cacheTtl ?? getEndpointTtl(endpoint);
          setCached(cacheKey, result.data, ttl);
        }
        return result;
      }

      lastError = result;

      // Don't retry on non-retryable errors or last attempt
      if (!isRetryableError(result.status) || attempt === retries) {
        break;
      }

      // Exponential backoff: 1s, 2s, 4s...
      const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    // Sprint 198: Silent token refresh on 401
    // Skip refresh for auth endpoints to prevent infinite loops
    if (
      lastError?.status === 401 &&
      _tokenRefreshCallback &&
      !endpoint.includes('/auth/refresh') &&
      !endpoint.includes('/auth/login') &&
      !endpoint.includes('/auth/register')
    ) {
      const newToken = await _tokenRefreshCallback();
      if (newToken) {
        // Security Sprint: CSRF token is set by refreshAccessToken from the refresh response.
        // Pass newToken as fallback in case the refresh response didn't include csrf_token.
        await fetchCsrfToken(newToken);
        // Retry the original request with the new token + fresh CSRF
        const refreshedHeaders = {
          ...headers,
          'Authorization': `Bearer ${newToken}`,
          ...(_csrfToken && CSRF_METHODS.has(method) ? { 'X-CSRF-Token': _csrfToken } : {}),
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

    // Clean up when done
    fetchPromise.finally(() => {
      inflightRequests.delete(cacheKey);
    });
  }

  return fetchPromise;
}

// =============================================================================
// CONVENIENCE METHODS
// =============================================================================

/**
 * Make an authenticated GET request (cached by default).
 *
 * @example
 * const { data, error } = await apiGet<Client[]>('/clients', token);
 *
 * // Force fresh data
 * const { data } = await apiGet<Client[]>('/clients', token, { skipCache: true });
 */
export async function apiGet<T>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, token, { ...options, method: 'GET' });
}

/**
 * Make an authenticated POST request.
 *
 * Automatically invalidates related cache entries based on endpoint.
 *
 * @example
 * const { data, error } = await apiPost<Client>('/clients', token, {
 *   name: 'Acme Corp',
 *   industry: 'technology'
 * });
 */
export async function apiPost<T>(
  endpoint: string,
  token: string | null,
  body: object | FormData,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'POST', body });

  // Invalidate related cache on successful mutation
  if (result.ok) {
    // Extract base path for cache invalidation
    const basePath = endpoint.split('?')[0] ?? endpoint;
    invalidateCache(basePath);
    // Also invalidate parent path (e.g., /clients when posting to /clients/1/notes)
    const parentPath = basePath.split('/').slice(0, -1).join('/');
    if (parentPath) {
      invalidateCache(parentPath);
    }
  }

  return result;
}

/**
 * Make an authenticated PUT request.
 *
 * Automatically invalidates related cache entries based on endpoint.
 *
 * @example
 * const { data, error } = await apiPut<Client>('/clients/1', token, {
 *   name: 'Acme Corporation'
 * });
 */
export async function apiPut<T>(
  endpoint: string,
  token: string | null,
  body: object,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'PUT', body });

  // Invalidate related cache on successful mutation
  if (result.ok) {
    const basePath = endpoint.split('?')[0] ?? endpoint;
    invalidateCache(basePath);
    // Also invalidate parent path (e.g., /clients when updating /clients/1)
    const parentPath = basePath.split('/').slice(0, -1).join('/');
    if (parentPath) {
      invalidateCache(parentPath);
    }
  }

  return result;
}

/**
 * Make an authenticated PATCH request.
 *
 * Automatically invalidates related cache entries based on endpoint.
 * Sprint 113: Added for partial updates (comment edits, assignments).
 */
export async function apiPatch<T>(
  endpoint: string,
  token: string | null,
  body: object,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'PATCH', body });

  if (result.ok) {
    const basePath = endpoint.split('?')[0] ?? endpoint;
    invalidateCache(basePath);
    const parentPath = basePath.split('/').slice(0, -1).join('/');
    if (parentPath) {
      invalidateCache(parentPath);
    }
  }

  return result;
}

/**
 * Make an authenticated DELETE request.
 *
 * Automatically invalidates related cache entries based on endpoint.
 *
 * @example
 * const { ok, error } = await apiDelete('/clients/1', token);
 */
export async function apiDelete<T = void>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'DELETE' });

  // Invalidate related cache on successful mutation
  if (result.ok) {
    const basePath = endpoint.split('?')[0] ?? endpoint;
    invalidateCache(basePath);
    // Also invalidate parent path
    const parentPath = basePath.split('/').slice(0, -1).join('/');
    if (parentPath) {
      invalidateCache(parentPath);
    }
  }

  return result;
}

// =============================================================================
// BLOB/FILE DOWNLOADS
// =============================================================================

/**
 * Download a file from an API endpoint.
 *
 * @example
 * const { blob, filename, error } = await apiDownload('/export/pdf', token, {
 *   method: 'POST',
 *   body: { auditResult }
 * });
 *
 * if (blob) {
 *   downloadBlob(blob, filename || 'report.pdf');
 * }
 */
export async function apiDownload(
  endpoint: string,
  token: string | null,
  options: ApiRequestOptions = {}
): Promise<{ blob?: Blob; filename?: string; error?: string; ok: boolean }> {
  const {
    method = 'GET',
    body,
    headers: customHeaders = {},
    timeout = DOWNLOAD_TIMEOUT,
    retries = IDEMPOTENT_METHODS.has(options.method ?? 'GET') ? MAX_RETRIES : 0,
    idempotencyKey,
  } = options;

  const headers: Record<string, string> = {
    ...customHeaders,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Sprint 200: Inject CSRF token for mutation downloads (POST exports)
  if (CSRF_METHODS.has(method) && _csrfToken) {
    headers['X-CSRF-Token'] = _csrfToken;
  }

  // Sprint 417: Inject idempotency key for safe mutation retries
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }

  let requestBody: string | FormData | undefined;
  if (body) {
    if (body instanceof FormData) {
      requestBody = body;
    } else {
      headers['Content-Type'] = 'application/json';
      requestBody = JSON.stringify(body);
    }
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;

  // Retry loop for downloads
  let lastError: string | undefined;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        method,
        headers,
        body: requestBody,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        lastError = getStatusMessage(response.status);

        // Don't retry on non-retryable errors
        if (!isRetryableError(response.status)) {
          return { error: lastError, ok: false };
        }

        if (attempt < retries) {
          const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        return { error: lastError, ok: false };
      }

      // Extract filename from Content-Disposition header
      let filename: string | undefined;
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      const blob = await response.blob();
      return { blob, filename, ok: true };
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        lastError = 'Download timed out';
      } else {
        lastError = parseApiError(err, 'Download failed');
      }

      if (attempt < retries) {
        const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
    }
  }

  return { error: lastError, ok: false };
}

/**
 * Trigger a browser download for a blob.
 *
 * @example
 * downloadBlob(blob, 'report.pdf');
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  // Cleanup after a short delay
  setTimeout(() => {
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }, 100);
}
