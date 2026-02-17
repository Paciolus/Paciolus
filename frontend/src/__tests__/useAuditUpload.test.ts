/**
 * Sprint 276: useAuditUpload hook tests
 */
import { renderHook, act } from '@testing-library/react'

const mockGetCsrfToken = jest.fn(() => 'csrf-token-123')

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    token: 'test-token',
    user: { email: 'user@test.com', is_verified: true },
  })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))

jest.mock('@/utils/constants', () => ({
  API_URL: 'http://test',
}))

jest.mock('@/utils/apiClient', () => ({
  getCsrfToken: (...args: unknown[]) => mockGetCsrfToken(...args),
}))

import { useAuditUpload } from '@/hooks/useAuditUpload'
import { useAuth } from '@/contexts/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'

const mockUseAuth = useAuth as jest.Mock
const mockUseOptionalEngagement = useOptionalEngagementContext as jest.Mock

const mockFetch = jest.fn()
global.fetch = mockFetch

const defaultOptions = {
  endpoint: '/audit/test-tool',
  toolName: 'Test Tool',
  buildFormData: (...files: File[]) => {
    const fd = new FormData()
    files.forEach(f => fd.append('file', f))
    return fd
  },
  parseResult: (data: unknown) => data as { score: number },
}

describe('useAuditUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({
      token: 'test-token',
      user: { email: 'user@test.com', is_verified: true },
    })
    mockUseOptionalEngagement.mockReturnValue(null)
    mockGetCsrfToken.mockReturnValue('csrf-token-123')
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ score: 95 }),
    })
  })

  it('initializes with idle status and null result', () => {
    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('')
  })

  it('run calls fetch with correct URL and auth header', async () => {
    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      'http://test/audit/test-tool',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token',
        }),
        body: expect.any(FormData),
      })
    )
  })

  it('run attaches CSRF token header', async () => {
    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(mockGetCsrfToken).toHaveBeenCalled()
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-CSRF-Token': 'csrf-token-123',
        }),
      })
    )
  })

  it('run injects engagement_id from context when available', async () => {
    const mockRefreshToolRuns = jest.fn()
    const mockTriggerLinkToast = jest.fn()
    mockUseOptionalEngagement.mockReturnValue({
      engagementId: 42,
      refreshToolRuns: mockRefreshToolRuns,
      triggerLinkToast: mockTriggerLinkToast,
    })

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    // Verify engagement_id was appended to FormData
    const calledBody = (mockFetch as jest.Mock).mock.calls[0][1].body as FormData
    expect(calledBody.get('engagement_id')).toBe('42')
    // Should have refreshed tool runs and triggered toast
    expect(mockRefreshToolRuns).toHaveBeenCalled()
    expect(mockTriggerLinkToast).toHaveBeenCalledWith('Test Tool')
  })

  it('run checks user email verification before upload', async () => {
    mockUseAuth.mockReturnValue({
      token: 'test-token',
      user: { email: 'user@test.com', is_verified: false },
    })

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(mockFetch).not.toHaveBeenCalled()
    expect(result.current.status).toBe('error')
    expect(result.current.error).toContain('verify your email')
  })

  it('run handles 401 unauthorized', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Not authenticated' }),
    })

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toContain('sign in')
  })

  it('run handles 403 with EMAIL_NOT_VERIFIED code', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: { code: 'EMAIL_NOT_VERIFIED' } }),
    })

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toContain('verify your email')
  })

  it('run sets success status and parsed result on success', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ score: 95 }),
    })

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(result.current.status).toBe('success')
    expect(result.current.result).toEqual({ score: 95 })
    expect(result.current.error).toBe('')
  })

  it('run handles network error', async () => {
    mockFetch.mockRejectedValue(new Error('Network failure'))

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    await act(async () => {
      await result.current.run(file)
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toBe('Unable to connect to server. Please try again.')
  })

  it('reset clears status and result', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ score: 95 }),
    })

    const { result } = renderHook(() => useAuditUpload(defaultOptions))
    const file = new File(['data'], 'test.csv')

    // First run to populate state
    await act(async () => {
      await result.current.run(file)
    })
    expect(result.current.status).toBe('success')

    // Reset
    act(() => {
      result.current.reset()
    })

    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('')
  })
})
