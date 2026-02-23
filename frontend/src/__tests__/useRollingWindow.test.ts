/**
 * Sprint 276: useRollingWindow hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useRollingWindow } from '@/hooks/useRollingWindow'

const mockFetch = jest.fn()
const mockClear = jest.fn()
const mockRefetch = jest.fn()

let mockData: unknown = null
let mockIsLoading = false
let mockError: string | null = null
let mockHasData = false

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/hooks/useFetchData', () => ({
  useFetchData: jest.fn((options: { buildUrl: (id: number, params?: Record<string, unknown>) => string; hasDataCheck?: (data: unknown) => boolean }) => {
    // Capture the buildUrl for test assertions
    ;(jest.requireMock('@/hooks/useFetchData') as { __lastBuildUrl: typeof options.buildUrl }).__lastBuildUrl = options.buildUrl
    ;(jest.requireMock('@/hooks/useFetchData') as { __lastOptions: typeof options }).__lastOptions = options
    return {
      data: mockData,
      isLoading: mockIsLoading,
      error: mockError,
      hasData: mockHasData,
      isStale: false,
      isRevalidating: false,
      fetch: mockFetch,
      clear: mockClear,
      refetch: mockRefetch,
    }
  }),
}))


describe('useRollingWindow', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockData = null
    mockIsLoading = false
    mockError = null
    mockHasData = false
  })

  it('initializes with null data, not loading', () => {
    const { result } = renderHook(() => useRollingWindow())

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.hasData).toBe(false)
  })

  it('fetchAnalysis calls underlying fetch with correct ID', async () => {
    const { result } = renderHook(() => useRollingWindow())

    await act(async () => {
      await result.current.fetchAnalysis(42)
    })

    expect(mockFetch).toHaveBeenCalledWith(42, {
      window: undefined,
      period_type: undefined,
    })
  })

  it('fetchAnalysis passes window param', async () => {
    const { result } = renderHook(() => useRollingWindow())

    await act(async () => {
      await result.current.fetchAnalysis(10, 6)
    })

    expect(mockFetch).toHaveBeenCalledWith(10, {
      window: 6,
      period_type: undefined,
    })
  })

  it('fetchAnalysis passes periodType param', async () => {
    const { result } = renderHook(() => useRollingWindow())

    await act(async () => {
      await result.current.fetchAnalysis(10, undefined, 'quarterly')
    })

    expect(mockFetch).toHaveBeenCalledWith(10, {
      window: undefined,
      period_type: 'quarterly',
    })
  })

  it('hasData reflects whether data is present', () => {
    mockHasData = true
    mockData = { client_id: 1, analysis: {} }

    const { result } = renderHook(() => useRollingWindow())

    expect(result.current.hasData).toBe(true)
  })

  it('clearAnalysis calls underlying clear', () => {
    const { result } = renderHook(() => useRollingWindow())

    result.current.clearAnalysis()

    expect(mockClear).toHaveBeenCalledTimes(1)
  })

  it('propagates error from useFetchData', () => {
    mockError = 'Failed to fetch data'

    const { result } = renderHook(() => useRollingWindow())

    expect(result.current.error).toBe('Failed to fetch data')
  })

  it('buildUrl generates correct URL with params', () => {
    renderHook(() => useRollingWindow())

    const useFetchDataModule = jest.requireMock('@/hooks/useFetchData') as {
      __lastBuildUrl: (id: number, params?: Record<string, unknown>) => string
    }
    const buildUrl = useFetchDataModule.__lastBuildUrl

    // Without params
    expect(buildUrl(5, {})).toBe('/clients/5/rolling-analysis')

    // With window param
    expect(buildUrl(5, { window: 6 })).toContain('window=6')

    // With period_type param
    expect(buildUrl(5, { period_type: 'quarterly' })).toContain('period_type=quarterly')

    // With both params
    const url = buildUrl(5, { window: 12, period_type: 'monthly' })
    expect(url).toContain('/clients/5/rolling-analysis?')
    expect(url).toContain('window=12')
    expect(url).toContain('period_type=monthly')
  })
})
