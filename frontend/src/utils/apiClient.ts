/**
 * Paciolus API Client Utilities
 * Phase 1 Refactor: Shared authenticated fetch functions
 *
 * Eliminates duplicate fetch/auth/error handling patterns across hooks.
 *
 * ZERO-STORAGE: No data persistence, pure API communication.
 */

// =============================================================================
// TYPES
// =============================================================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
  ok: boolean;
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
 * Make an authenticated API request.
 *
 * Handles:
 * - Authorization header injection
 * - JSON serialization/parsing
 * - Error extraction from response body
 * - Timeout handling
 *
 * @example
 * // GET request
 * const { data, error, ok } = await apiFetch<User[]>('/clients', token);
 *
 * // POST request with body
 * const { data, error } = await apiFetch<Client>('/clients', token, {
 *   method: 'POST',
 *   body: { name: 'Acme Corp', industry: 'technology' }
 * });
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
  } = options;

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

  try {
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

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

// =============================================================================
// CONVENIENCE METHODS
// =============================================================================

/**
 * Make an authenticated GET request.
 *
 * @example
 * const { data, error } = await apiGet<Client[]>('/clients', token);
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
  return apiFetch<T>(endpoint, token, { ...options, method: 'POST', body });
}

/**
 * Make an authenticated PUT request.
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
  return apiFetch<T>(endpoint, token, { ...options, method: 'PUT', body });
}

/**
 * Make an authenticated DELETE request.
 *
 * @example
 * const { ok, error } = await apiDelete('/clients/1', token);
 */
export async function apiDelete<T = void>(
  endpoint: string,
  token: string | null,
  options?: Omit<ApiRequestOptions, 'method' | 'body'>
): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, token, { ...options, method: 'DELETE' });
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
      return {
        error: getStatusMessage(response.status),
        ok: false,
      };
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
      return { error: 'Download timed out', ok: false };
    }
    return {
      error: parseApiError(err, 'Download failed'),
      ok: false,
    };
  }
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
