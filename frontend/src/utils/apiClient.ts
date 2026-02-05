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
}

export interface ApiRequestOptions {
  /** HTTP method (default: GET) */
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  /** Request body (will be JSON stringified) */
  body?: Record<string, unknown> | FormData;
  /** Additional headers */
  headers?: Record<string, string>;
  /** Request timeout in ms (default: 30000) */
  timeout?: number;
  /** Skip cache lookup (default: false) */
  skipCache?: boolean;
  /** Cache TTL in ms (default: 300000 = 5 minutes) */
  cacheTtl?: number;
  /** Number of retry attempts for failed requests (default: 3) */
  retries?: number;
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

// =============================================================================
// CACHE & DEDUPLICATION STATE
// =============================================================================

/** In-memory cache for GET request responses */
const queryCache = new Map<string, CacheEntry<unknown>>();

/** Track in-flight requests to prevent duplicate concurrent calls */
const inflightRequests = new Map<string, Promise<ApiResponse<unknown>>>();

/** Default cache TTL values by endpoint pattern (in milliseconds) */
const ENDPOINT_TTL_CONFIG: Record<string, number> = {
  '/clients/industries': 60 * 60 * 1000,      // 1 hour - rarely changes
  '/settings/practice': 30 * 60 * 1000,       // 30 min - settings stable
  '/industry-ratios': 30 * 60 * 1000,         // 30 min - benchmarks static
  '/trends': 10 * 60 * 1000,                  // 10 min - historical data
  '/rolling-analysis': 10 * 60 * 1000,        // 10 min - rolling window data
  '/clients': 10 * 60 * 1000,                 // 10 min - client list
  '/activity/history': 5 * 60 * 1000,         // 5 min - activity updates frequently
  '/diagnostics/summary': 10 * 60 * 1000,     // 10 min - diagnostic summaries
};

/** Default TTL for endpoints not in config */
const DEFAULT_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/** Maximum retry attempts */
const MAX_RETRIES = 3;

/** Base delay for exponential backoff (in ms) */
const BASE_RETRY_DELAY = 1000;

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
 */
function getCached<T>(key: string): T | null {
  if (!key) return null;

  const entry = queryCache.get(key) as CacheEntry<T> | undefined;
  if (entry && isCacheValid(entry)) {
    return entry.data;
  }

  // Clean up expired entry
  if (entry) {
    queryCache.delete(key);
  }
  return null;
}

/**
 * Store a response in cache.
 */
function setCached<T>(key: string, data: T, ttl: number): void {
  if (!key) return;

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

const API_URL = process.env.NEXT_PUBLIC_API_URL;

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
        errorMessage = errorData.detail || errorData.message || getStatusMessage(response.status);
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
    timeout = 30000,
    skipCache = false,
    cacheTtl,
    retries = MAX_RETRIES,
  } = options;

  const isGetRequest = method === 'GET';
  const cacheKey = isGetRequest ? getCacheKey(endpoint, options) : '';

  // Check cache for GET requests
  if (isGetRequest && !skipCache && cacheKey) {
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
  body: Record<string, unknown> | FormData,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'POST', body });

  // Invalidate related cache on successful mutation
  if (result.ok) {
    // Extract base path for cache invalidation
    const basePath = endpoint.split('?')[0];
    invalidateCache(basePath);
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
  body: Record<string, unknown>,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  const result = await apiFetch<T>(endpoint, token, { ...options, method: 'PUT', body });

  // Invalidate related cache on successful mutation
  if (result.ok) {
    const basePath = endpoint.split('?')[0];
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
    const basePath = endpoint.split('?')[0];
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
    timeout = 60000, // Longer timeout for downloads
    retries = MAX_RETRIES,
  } = options;

  const headers: Record<string, string> = {
    ...customHeaders,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
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
