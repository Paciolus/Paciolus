/**
 * Sprint 527 F-005: Unit tests for uploadTransport.ts
 *
 * Covers: successful upload, 401/403/500 error paths, network failure,
 * and header injection (Authorization + X-CSRF-Token).
 */

import { uploadFetch } from '@/utils/uploadTransport'

// Mock getCsrfToken
jest.mock('@/utils/apiClient', () => ({
  getCsrfToken: jest.fn(() => 'test-csrf-token'),
}))

// Mock API_URL constant
jest.mock('@/utils/constants', () => ({
  API_URL: 'http://localhost:8000',
}))

import { getCsrfToken } from '@/utils/apiClient'

const mockGetCsrfToken = getCsrfToken as jest.Mock

describe('uploadFetch', () => {
  const formData = new FormData()
  const token = 'test-bearer-token'

  beforeEach(() => {
    jest.clearAllMocks()
    mockGetCsrfToken.mockReturnValue('test-csrf-token')
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('returns data on successful upload', async () => {
    const mockData = { status: 'success', row_count: 42 }
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockData),
    })

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(true)
    expect(result.status).toBe(200)
    expect(result.data).toEqual(mockData)
  })

  it('returns auth error on 401', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({}),
    })

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(false)
    expect(result.status).toBe(401)
    expect(result.error).toBe('auth')
  })

  it('returns EMAIL_NOT_VERIFIED errorCode on 403 with code', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 403,
      json: () => Promise.resolve({ detail: { code: 'EMAIL_NOT_VERIFIED' } }),
    })

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(false)
    expect(result.status).toBe(403)
    expect(result.errorCode).toBe('EMAIL_NOT_VERIFIED')
    expect(result.error).toBe('email_not_verified')
  })

  it('returns access_denied on generic 403', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 403,
      json: () => Promise.resolve({ detail: 'Forbidden' }),
    })

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(false)
    expect(result.status).toBe(403)
    expect(result.error).toBe('access_denied')
    expect(result.errorCode).toBeUndefined()
  })

  it('returns error message on 500', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Internal server error' }),
    })

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(false)
    expect(result.status).toBe(500)
    expect(result.error).toBe('Internal server error')
  })

  it('returns network error when fetch throws', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValue(new Error('Network failure'))

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(false)
    expect(result.status).toBe(0)
    expect(result.error).toBe('Unable to connect to server. Please try again.')
  })

  it('injects Authorization and X-CSRF-Token headers', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'success' }),
    })

    await uploadFetch('/audit/trial-balance', formData, token)

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/audit/trial-balance',
      expect.objectContaining({
        method: 'POST',
        headers: {
          Authorization: 'Bearer test-bearer-token',
          'X-CSRF-Token': 'test-csrf-token',
        },
        body: formData,
      }),
    )
  })

  it('omits Authorization header when token is null', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'success' }),
    })

    await uploadFetch('/audit/trial-balance', formData, null)

    const callArgs = (global.fetch as jest.Mock).mock.calls[0]
    const headers = callArgs[1].headers
    expect(headers).not.toHaveProperty('Authorization')
    expect(headers).toHaveProperty('X-CSRF-Token', 'test-csrf-token')
  })

  it('omits X-CSRF-Token header when CSRF token is null', async () => {
    mockGetCsrfToken.mockReturnValue(null)
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'success' }),
    })

    await uploadFetch('/audit/trial-balance', formData, token)

    const callArgs = (global.fetch as jest.Mock).mock.calls[0]
    const headers = callArgs[1].headers
    expect(headers).toHaveProperty('Authorization', 'Bearer test-bearer-token')
    expect(headers).not.toHaveProperty('X-CSRF-Token')
  })

  it('handles 403 when json parsing fails', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 403,
      json: () => Promise.reject(new Error('Invalid JSON')),
    })

    const result = await uploadFetch('/audit/trial-balance', formData, token)

    expect(result.ok).toBe(false)
    expect(result.status).toBe(403)
    expect(result.error).toBe('access_denied')
  })
})
