/**
 * Sprint 237: useSettings hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useSettings } from '@/hooks/useSettings'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiPut = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
  isAuthError: jest.fn((status: number) => status === 401 || status === 403),
}))


const mockUseAuth = useAuth as jest.Mock

const mockPracticeSettings = {
  firm_name: 'Test Firm',
  materiality_formula: 'percentage_revenue',
  materiality_percentage: 5,
  default_currency: 'USD',
}

describe('useSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
    // Auto-fetch on mount calls fetchPracticeSettings
    mockApiGet.mockResolvedValue({ ok: true, data: mockPracticeSettings })
  })

  it('fetches practice settings on mount when authenticated', async () => {
    const { result } = renderHook(() => useSettings())

    // Wait for useEffect to fire
    await act(async () => {})

    expect(mockApiGet).toHaveBeenCalledWith('/settings/practice', 'test-token')
    expect(result.current.practiceSettings).toEqual(mockPracticeSettings)
  })

  it('updatePracticeSettings calls PUT', async () => {
    const updated = { ...mockPracticeSettings, firm_name: 'New Firm' }
    mockApiPut.mockResolvedValue({ ok: true, data: updated })

    const { result } = renderHook(() => useSettings())
    await act(async () => {}) // Wait for auto-fetch

    let success: boolean = false
    await act(async () => {
      success = await result.current.updatePracticeSettings({ firm_name: 'New Firm' } as never)
    })

    expect(mockApiPut).toHaveBeenCalledWith(
      '/settings/practice',
      'test-token',
      expect.objectContaining({ firm_name: 'New Firm' })
    )
    expect(success).toBe(true)
    expect(result.current.practiceSettings).toEqual(updated)
  })

  it('fetchClientSettings returns client settings', async () => {
    const clientSettings = { materiality_override: 100000 }
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockPracticeSettings }) // auto-fetch
    mockApiGet.mockResolvedValueOnce({ ok: true, data: clientSettings })

    const { result } = renderHook(() => useSettings())
    await act(async () => {})

    let settings: unknown
    await act(async () => {
      settings = await result.current.fetchClientSettings(1)
    })

    expect(settings).toEqual(clientSettings)
    expect(mockApiGet).toHaveBeenCalledWith('/clients/1/settings', 'test-token')
  })

  it('updateClientSettings calls PUT', async () => {
    mockApiPut.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useSettings())
    await act(async () => {})

    let success: boolean = false
    await act(async () => {
      success = await result.current.updateClientSettings(1, { materiality_override: 200000 } as never)
    })

    expect(mockApiPut).toHaveBeenCalledWith(
      '/clients/1/settings',
      'test-token',
      expect.objectContaining({ materiality_override: 200000 })
    )
    expect(success).toBe(true)
  })

  it('previewMateriality calls POST', async () => {
    const preview = { overall: 50000, performance: 37500, trivial: 2500 }
    mockApiPost.mockResolvedValue({ ok: true, data: preview })

    const { result } = renderHook(() => useSettings())
    await act(async () => {})

    let previewResult: unknown
    await act(async () => {
      previewResult = await result.current.previewMateriality(
        'percentage_revenue' as never,
        1000000
      )
    })

    expect(previewResult).toEqual(preview)
    expect(mockApiPost).toHaveBeenCalledWith(
      '/settings/materiality/preview',
      'test-token',
      expect.objectContaining({ total_revenue: 1000000 })
    )
  })

  it('resolveMateriality calls GET with params', async () => {
    const resolved = { source: 'practice', threshold: 50000 }
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockPracticeSettings }) // auto-fetch
    mockApiGet.mockResolvedValueOnce({ ok: true, data: resolved })

    const { result } = renderHook(() => useSettings())
    await act(async () => {})

    let resolvedResult: unknown
    await act(async () => {
      resolvedResult = await result.current.resolveMateriality(1, 75000)
    })

    expect(resolvedResult).toEqual(resolved)
    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('client_id=1'),
      'test-token'
    )
  })

  it('does nothing when not authenticated', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useSettings())
    await act(async () => {})

    expect(mockApiGet).not.toHaveBeenCalled()
    expect(result.current.practiceSettings).toBeNull()
  })

  it('sets error on auth failure', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Unauthorized', status: 401 })

    const { result } = renderHook(() => useSettings())
    await act(async () => {})

    expect(result.current.error).toBe('Session expired. Please log in again.')
  })
})
