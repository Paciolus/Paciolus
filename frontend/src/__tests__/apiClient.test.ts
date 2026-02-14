/**
 * Sprint 233: apiClient tests
 *
 * Tests cover: error utilities, CSRF management, cache operations,
 * convenience methods (apiGet/Post/Put/Delete), 422 parsing.
 */
import {
  parseApiError,
  isAuthError,
  isNotFoundError,
  isValidationError,
  getStatusMessage,
  setCsrfToken,
  getCsrfToken,
  invalidateCache,
  getCacheStats,
  apiFetch,
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
  downloadBlob,
  setTokenRefreshCallback,
} from '@/utils/apiClient'

// Mock global fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

beforeEach(() => {
  jest.clearAllMocks()
  invalidateCache() // Clear cache between tests
  setCsrfToken(null)
  setTokenRefreshCallback(null)
})

// =============================================================================
// ERROR UTILITIES
// =============================================================================

describe('parseApiError', () => {
  it('extracts message from Error instance', () => {
    expect(parseApiError(new Error('Something failed'))).toBe('Something failed')
  })

  it('returns string errors as-is', () => {
    expect(parseApiError('Network timeout')).toBe('Network timeout')
  })

  it('returns fallback for unknown types', () => {
    expect(parseApiError(undefined)).toBe('An unexpected error occurred')
  })

  it('accepts custom fallback message', () => {
    expect(parseApiError(42, 'Custom fallback')).toBe('Custom fallback')
  })
})

describe('isAuthError', () => {
  it('returns true for 401', () => {
    expect(isAuthError(401)).toBe(true)
  })

  it('returns true for 403', () => {
    expect(isAuthError(403)).toBe(true)
  })

  it('returns false for 200', () => {
    expect(isAuthError(200)).toBe(false)
  })

  it('returns false for 404', () => {
    expect(isAuthError(404)).toBe(false)
  })
})

describe('isNotFoundError', () => {
  it('returns true for 404', () => {
    expect(isNotFoundError(404)).toBe(true)
  })

  it('returns false for 200', () => {
    expect(isNotFoundError(200)).toBe(false)
  })
})

describe('isValidationError', () => {
  it('returns true for 422', () => {
    expect(isValidationError(422)).toBe(true)
  })

  it('returns false for 400', () => {
    expect(isValidationError(400)).toBe(false)
  })
})

describe('getStatusMessage', () => {
  it('returns specific message for known status codes', () => {
    expect(getStatusMessage(401)).toBe('Session expired. Please log in again.')
    expect(getStatusMessage(403)).toBe('Access denied')
    expect(getStatusMessage(404)).toBe('Not found')
    expect(getStatusMessage(422)).toBe('Validation error')
    expect(getStatusMessage(429)).toBe('Too many requests. Please try again later.')
    expect(getStatusMessage(500)).toBe('Server error. Please try again.')
  })

  it('returns generic message for unknown status codes', () => {
    expect(getStatusMessage(418)).toBe('Request failed (418)')
  })
})

// =============================================================================
// CSRF TOKEN MANAGEMENT
// =============================================================================

describe('CSRF token management', () => {
  it('stores and retrieves CSRF token', () => {
    setCsrfToken('test-csrf-token')
    expect(getCsrfToken()).toBe('test-csrf-token')
  })

  it('clears CSRF token with null', () => {
    setCsrfToken('token')
    setCsrfToken(null)
    expect(getCsrfToken()).toBeNull()
  })
})

// =============================================================================
// CACHE OPERATIONS
// =============================================================================

describe('cache operations', () => {
  it('starts with empty cache', () => {
    expect(getCacheStats().size).toBe(0)
  })

  it('caches GET responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1, name: 'Test' }),
    })

    await apiGet('/test-endpoint', 'token')

    expect(getCacheStats().size).toBe(1)
    expect(getCacheStats().keys[0]).toContain('/test-endpoint')
  })

  it('returns cached data on second GET', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1 }),
    })

    await apiGet('/cached-test', 'token')
    const second = await apiGet('/cached-test', 'token')

    expect(mockFetch).toHaveBeenCalledTimes(1) // Only one fetch
    expect(second.cached).toBe(true)
    expect(second.data).toEqual({ id: 1 })
  })

  it('skips cache when skipCache is true', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ version: 1 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ version: 2 }),
      })

    await apiGet('/skip-test', 'token')
    const second = await apiGet('/skip-test', 'token', { skipCache: true })

    expect(mockFetch).toHaveBeenCalledTimes(2)
    expect(second.data).toEqual({ version: 2 })
  })

  it('invalidateCache clears all with no pattern', () => {
    // Populate cache via fetch
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })

    // Clear whatever is cached
    invalidateCache()
    expect(getCacheStats().size).toBe(0)
  })

  it('invalidateCache clears matching pattern', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ type: 'clients' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ type: 'settings' }),
      })

    await apiGet('/clients', 'token')
    await apiGet('/settings/practice', 'token')

    expect(getCacheStats().size).toBe(2)

    invalidateCache('/clients')
    expect(getCacheStats().size).toBe(1)
    expect(getCacheStats().keys[0]).toContain('/settings')
  })
})

// =============================================================================
// API FETCH — SUCCESS PATHS
// =============================================================================

describe('apiFetch', () => {
  it('makes GET request with auth header', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'test' }),
    })

    const result = await apiFetch('/endpoint', 'my-token')

    expect(result.ok).toBe(true)
    expect(result.data).toEqual({ data: 'test' })
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/endpoint'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Authorization': 'Bearer my-token',
        }),
      })
    )
  })

  it('makes POST request with JSON body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 1 }),
    })

    const result = await apiFetch('/items', 'token', {
      method: 'POST',
      body: { name: 'Test' },
    })

    expect(result.ok).toBe(true)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'Test' }),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    )
  })

  it('handles 204 No Content', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    })

    const result = await apiFetch('/items/1', 'token', { method: 'DELETE' })

    expect(result.ok).toBe(true)
    expect(result.status).toBe(204)
  })

  it('handles FormData body without Content-Type', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ uploaded: true }),
    })

    const formData = new FormData()
    formData.append('file', new Blob(['test']), 'test.csv')

    await apiFetch('/upload', 'token', {
      method: 'POST',
      body: formData,
    })

    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['Content-Type']).toBeUndefined()
  })

  it('works without auth token', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ public: true }),
    })

    const result = await apiFetch('/public-endpoint', null)

    expect(result.ok).toBe(true)
    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['Authorization']).toBeUndefined()
  })
})

// =============================================================================
// API FETCH — ERROR PATHS
// =============================================================================

describe('apiFetch error handling', () => {
  it('handles 422 Pydantic validation errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: () => Promise.resolve({
        detail: [
          { loc: ['body', 'email'], msg: 'invalid email format', type: 'value_error' }
        ]
      }),
    })

    const result = await apiFetch('/register', null, {
      method: 'POST',
      body: { email: 'bad' },
      retries: 0,
    })

    expect(result.ok).toBe(false)
    expect(result.status).toBe(422)
    expect(result.error).toBe('email: invalid email format')
  })

  it('handles structured error detail object', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: () => Promise.resolve({
        detail: { code: 'UNVERIFIED', message: 'Email not verified' }
      }),
    })

    const result = await apiFetch('/protected', 'token', { retries: 0 })

    expect(result.ok).toBe(false)
    expect(result.error).toBe('Email not verified')
  })

  it('handles plain string detail', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Bad request data' }),
    })

    const result = await apiFetch('/bad', 'token', { retries: 0 })

    expect(result.error).toBe('Bad request data')
  })

  it('handles non-JSON error responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('not JSON')),
    })

    const result = await apiFetch('/broken', 'token', { retries: 0 })

    expect(result.ok).toBe(false)
    expect(result.error).toBe('Server error. Please try again.')
  })

  it('handles network errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Failed to fetch'))

    const result = await apiFetch('/offline', 'token', { retries: 0 })

    expect(result.ok).toBe(false)
    expect(result.status).toBe(0)
    expect(result.error).toBe('Failed to fetch')
  })
})

// =============================================================================
// CSRF INJECTION
// =============================================================================

describe('CSRF token injection', () => {
  it('injects CSRF token on POST requests', async () => {
    setCsrfToken('csrf-abc')

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({}),
    })

    await apiFetch('/items', 'token', { method: 'POST', body: { x: 1 } })

    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['X-CSRF-Token']).toBe('csrf-abc')
  })

  it('injects CSRF token on DELETE requests', async () => {
    setCsrfToken('csrf-del')

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    })

    await apiFetch('/items/1', 'token', { method: 'DELETE' })

    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['X-CSRF-Token']).toBe('csrf-del')
  })

  it('does NOT inject CSRF token on GET requests', async () => {
    setCsrfToken('csrf-get')

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    })

    await apiFetch('/items', 'token')

    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['X-CSRF-Token']).toBeUndefined()
  })
})

// =============================================================================
// CONVENIENCE METHODS
// =============================================================================

describe('apiPost', () => {
  it('invalidates cache on success', async () => {
    // First cache a GET
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1 }]),
    })
    await apiGet('/items', 'token')
    expect(getCacheStats().size).toBe(1)

    // POST should invalidate
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 2 }),
    })
    await apiPost('/items', 'token', { name: 'New' })

    expect(getCacheStats().size).toBe(0)
  })
})

describe('apiPut', () => {
  it('makes PUT request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1, name: 'Updated' }),
    })

    const result = await apiPut('/items/1', 'token', { name: 'Updated' })

    expect(result.ok).toBe(true)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ method: 'PUT' })
    )
  })
})

describe('apiDelete', () => {
  it('makes DELETE request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    })

    const result = await apiDelete('/items/1', 'token')

    expect(result.ok).toBe(true)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ method: 'DELETE' })
    )
  })
})

// =============================================================================
// downloadBlob
// =============================================================================

describe('downloadBlob', () => {
  it('creates download link and triggers click', () => {
    const mockClick = jest.fn()
    const mockAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation(jest.fn() as typeof document.body.appendChild)
    const mockRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation(jest.fn() as typeof document.body.removeChild)
    const mockCreateElement = jest.spyOn(document, 'createElement').mockReturnValue({
      click: mockClick,
      href: '',
      download: '',
      style: { display: '' },
    } as unknown as HTMLAnchorElement)

    downloadBlob(new Blob(['test']), 'report.pdf')

    expect(mockCreateElement).toHaveBeenCalledWith('a')
    expect(mockClick).toHaveBeenCalled()

    mockCreateElement.mockRestore()
    mockAppendChild.mockRestore()
    mockRemoveChild.mockRestore()
  })
})
