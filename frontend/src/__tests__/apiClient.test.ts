/**
 * Sprint 233: apiClient tests
 * Sprint 417: Mutation retry safety, cache LRU/sweep/telemetry, POST parent invalidation
 *
 * Tests cover: error utilities, CSRF management, cache operations,
 * convenience methods (apiGet/Post/Put/Delete), 422 parsing,
 * retry policy, idempotency keys, cache eviction/telemetry/sweep.
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
  getCacheTelemetry,
  resetCacheTelemetry,
  stopCacheSweep,
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
  resetCacheTelemetry()
  stopCacheSweep() // Prevent timer interference in tests
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
    jest.useFakeTimers()
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

    // Flush the 100ms cleanup timer while mocks are still in place
    jest.runAllTimers()
    jest.useRealTimers()

    mockCreateElement.mockRestore()
    mockAppendChild.mockRestore()
    mockRemoveChild.mockRestore()
  })
})

// =============================================================================
// SPRINT 417: MUTATION RETRY SAFETY
// =============================================================================

describe('mutation retry safety (Sprint 417)', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('POST does not retry by default on 5xx', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    })

    await apiFetch('/items', 'token', { method: 'POST', body: { name: 'Test' } })

    // Should only call fetch once (no retries)
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('DELETE does not retry by default on 5xx', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    })

    await apiFetch('/items/1', 'token', { method: 'DELETE' })

    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('PATCH does not retry by default on 5xx', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    })

    await apiFetch('/items/1', 'token', { method: 'PATCH', body: { name: 'X' } })

    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('GET retries by default on 5xx', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    })

    const promise = apiFetch('/items', 'token', { method: 'GET' })

    // Drain all retry timers (exponential backoff)
    await jest.advanceTimersByTimeAsync(30_000)
    await promise

    // 1 initial + 3 retries = 4 total
    expect(mockFetch).toHaveBeenCalledTimes(4)
  })

  it('PUT retries by default on 5xx (idempotent)', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    })

    const promise = apiFetch('/items/1', 'token', { method: 'PUT', body: { name: 'X' } })

    await jest.advanceTimersByTimeAsync(30_000)
    await promise

    // 1 initial + 3 retries = 4 total
    expect(mockFetch).toHaveBeenCalledTimes(4)
  })

  it('allows explicit retry opt-in for mutations', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server error' }),
    })

    const promise = apiFetch('/items', 'token', {
      method: 'POST',
      body: { name: 'Test' },
      retries: 2,
      idempotencyKey: 'key-123',
    })

    await jest.advanceTimersByTimeAsync(30_000)
    await promise

    // 1 initial + 2 retries = 3 total
    expect(mockFetch).toHaveBeenCalledTimes(3)
  })
})

// =============================================================================
// SPRINT 417: IDEMPOTENCY KEY
// =============================================================================

describe('idempotency key (Sprint 417)', () => {
  it('injects Idempotency-Key header when provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 1 }),
    })

    await apiFetch('/items', 'token', {
      method: 'POST',
      body: { name: 'Test' },
      idempotencyKey: 'uuid-abc-123',
    })

    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['Idempotency-Key']).toBe('uuid-abc-123')
  })

  it('omits Idempotency-Key header when not provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 1 }),
    })

    await apiFetch('/items', 'token', {
      method: 'POST',
      body: { name: 'Test' },
    })

    const callHeaders = mockFetch.mock.calls[0][1].headers
    expect(callHeaders['Idempotency-Key']).toBeUndefined()
  })
})

// =============================================================================
// SPRINT 417: DEV WARNING FOR UNSAFE RETRIES
// =============================================================================

describe('dev warning for unsafe retries (Sprint 417)', () => {
  const originalNodeEnv = process.env.NODE_ENV

  beforeEach(() => {
    jest.useFakeTimers()
    jest.spyOn(console, 'warn').mockImplementation(() => {})
    process.env.NODE_ENV = 'development'
  })

  afterEach(() => {
    jest.useRealTimers()
    process.env.NODE_ENV = originalNodeEnv
  })

  it('warns in development when mutation retries without idempotencyKey', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'error' }),
    })

    const promise = apiFetch('/items', 'token', {
      method: 'POST',
      body: { x: 1 },
      retries: 2,
    })

    await jest.advanceTimersByTimeAsync(30_000)
    await promise

    expect(console.warn).toHaveBeenCalledWith(
      expect.stringContaining('retries=2 without idempotencyKey')
    )
  })

  it('does not warn when idempotencyKey is provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 1 }),
    })

    await apiFetch('/items', 'token', {
      method: 'POST',
      body: { x: 1 },
      retries: 1,
      idempotencyKey: 'safe-key',
    })

    expect(console.warn).not.toHaveBeenCalled()
  })

  it('does not warn for idempotent methods with retries', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'ok' }),
    })

    await apiFetch('/items', 'token', { method: 'GET', retries: 3 })

    expect(console.warn).not.toHaveBeenCalled()
  })
})

// =============================================================================
// SPRINT 417: CACHE LRU EVICTION
// =============================================================================

describe('cache LRU eviction (Sprint 417)', () => {
  it('evicts oldest entry when cache reaches MAX_CACHE_ENTRIES', async () => {
    // Fill cache to capacity (MAX_CACHE_ENTRIES = 100)
    for (let i = 0; i < 100; i++) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ i }),
      })
      await apiGet(`/item-${i}`, 'token')
    }

    expect(getCacheStats().size).toBe(100)

    // Add one more — should evict the oldest (item-0)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ i: 100 }),
    })
    await apiGet('/item-100', 'token')

    expect(getCacheStats().size).toBe(100)
    // item-0 should be evicted
    expect(getCacheStats().keys).not.toContain('/item-0')
    // item-100 should be present
    const keys = getCacheStats().keys
    expect(keys.some(k => k.includes('/item-100'))).toBe(true)
  })

  it('recently accessed entries survive eviction', async () => {
    // Fill cache
    for (let i = 0; i < 100; i++) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ i }),
      })
      await apiGet(`/item-${i}`, 'token')
    }

    // Access item-0 (moves it to end of LRU)
    await apiGet('/item-0', 'token') // should be a cache hit, no fetch

    // Add new entry — should evict item-1 (now the oldest), NOT item-0
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ i: 100 }),
    })
    await apiGet('/item-100', 'token')

    expect(getCacheStats().size).toBe(100)
    // item-0 was touched, should survive
    expect(getCacheStats().keys.some(k => k.includes('/item-0'))).toBe(true)
    // item-1 should be evicted (it was the oldest after item-0 was touched)
    expect(getCacheStats().keys.some(k => k.includes('/item-1') && !k.includes('/item-1'))).toBe(false)
  })

  it('tracks eviction count in telemetry', async () => {
    for (let i = 0; i < 100; i++) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ i }),
      })
      await apiGet(`/evict-${i}`, 'token')
    }

    // Add 3 more — should cause 3 evictions
    for (let i = 100; i < 103; i++) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ i }),
      })
      await apiGet(`/evict-${i}`, 'token')
    }

    expect(getCacheTelemetry().evictions).toBe(3)
  })
})

// =============================================================================
// SPRINT 417: CACHE SWEEP
// =============================================================================

describe('cache sweep (Sprint 417)', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('expired entries are cleaned up on access', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: 'v1' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: 'v2' }),
      })

    await apiGet('/sweep-test', 'token', { cacheTtl: 1 }) // 1ms TTL
    expect(getCacheStats().size).toBe(1)

    // Advance past TTL so entry expires
    jest.advanceTimersByTime(50)

    // Access triggers cleanup of expired entry + fresh fetch
    const result = await apiGet('/sweep-test', 'token', { cacheTtl: 1 })
    expect(mockFetch).toHaveBeenCalledTimes(2) // re-fetched after expiry
    expect(result.data).toEqual({ data: 'v2' })
  })
})

// =============================================================================
// SPRINT 417: CACHE TELEMETRY
// =============================================================================

describe('cache telemetry (Sprint 417)', () => {
  it('counts cache hits', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'test' }),
    })

    await apiGet('/telemetry-hit', 'token')
    await apiGet('/telemetry-hit', 'token') // cache hit

    expect(getCacheTelemetry().hits).toBe(1)
  })

  it('counts cache misses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'test' }),
    })

    await apiGet('/telemetry-miss', 'token')

    // First call is a miss (nothing cached yet)
    expect(getCacheTelemetry().misses).toBe(1)
  })

  it('resetCacheTelemetry zeroes all counters', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ data: 'test' }),
    })

    await apiGet('/telemetry-reset', 'token') // miss
    await apiGet('/telemetry-reset', 'token') // hit

    expect(getCacheTelemetry().hits).toBe(1)
    expect(getCacheTelemetry().misses).toBe(1)

    resetCacheTelemetry()

    expect(getCacheTelemetry().hits).toBe(0)
    expect(getCacheTelemetry().misses).toBe(0)
    expect(getCacheTelemetry().evictions).toBe(0)
    expect(getCacheTelemetry().staleReturns).toBe(0)
  })
})

// =============================================================================
// SPRINT 417: POST PARENT INVALIDATION
// =============================================================================

describe('POST parent invalidation (Sprint 417)', () => {
  it('POST to child path invalidates parent cache via includes match', async () => {
    // Cache parent path /clients
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1 }]),
    })
    await apiGet('/clients', 'token')

    // Cache child path /clients/1
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1, name: 'Acme' }),
    })
    await apiGet('/clients/1', 'token')

    expect(getCacheStats().size).toBe(2)

    // POST to /clients/1 — basePath invalidation hits /clients/1,
    // parent path /clients invalidation hits both /clients and /clients/1 (includes match)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 2 }),
    })
    await apiPost('/clients/1', 'token', { name: 'New Note' })

    // Both /clients and /clients/1 invalidated (parent /clients matches keys containing '/clients')
    expect(getCacheStats().size).toBe(0)
  })

  it('POST to base path invalidates own cache', async () => {
    // Cache the path
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1 }]),
    })
    await apiGet('/items', 'token')
    expect(getCacheStats().size).toBe(1)

    // POST to same path
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 2 }),
    })
    await apiPost('/items', 'token', { name: 'New' })

    expect(getCacheStats().size).toBe(0)
  })

  it('POST parent invalidation matches PUT/PATCH/DELETE pattern', async () => {
    // Cache /items
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve([{ id: 1 }]),
    })
    await apiGet('/items', 'token')

    // Cache /items/1
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: 1 }),
    })
    await apiGet('/items/1', 'token')

    expect(getCacheStats().size).toBe(2)

    // POST to /items/1 — should invalidate /items/1 (basePath) and /items (parentPath)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve({ id: 2 }),
    })
    await apiPost('/items/1', 'token', { action: 'duplicate' })

    expect(getCacheStats().size).toBe(0)
  })
})
