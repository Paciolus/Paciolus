/**
 * Sprint 276: useIndustryRatios hook tests
 */
import { renderHook, act } from '@testing-library/react'

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

jest.mock('@/components/analytics/IndustryMetricsSection', () => ({
  __esModule: true,
}))

jest.mock('@/hooks/useFetchData', () => ({
  useFetchData: jest.fn((options: { buildUrl: (id: number) => string; hasDataCheck?: (data: unknown) => boolean; autoFetch?: boolean; initialId?: number }) => {
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

import { useIndustryRatios } from '@/hooks/useIndustryRatios'

describe('useIndustryRatios', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockData = null
    mockIsLoading = false
    mockError = null
    mockHasData = false
  })

  it('initializes with null data', () => {
    const { result } = renderHook(() => useIndustryRatios())

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.hasData).toBe(false)
  })

  it('fetchRatios calls underlying fetch with clientId', async () => {
    const { result } = renderHook(() => useIndustryRatios())

    await act(async () => {
      await result.current.fetchRatios(123)
    })

    expect(mockFetch).toHaveBeenCalledWith(123)
  })

  it('hasData reflects data presence (hasDataCheck: data.ratios !== null)', () => {
    mockHasData = true
    mockData = { ratios: { current_ratio: 1.5 } }

    const { result } = renderHook(() => useIndustryRatios())

    expect(result.current.hasData).toBe(true)
  })

  it('hasData is false when ratios are null', () => {
    // The hasDataCheck in the hook checks data.ratios !== null
    // We verify the check function was passed correctly
    renderHook(() => useIndustryRatios())

    const useFetchDataModule = jest.requireMock('@/hooks/useFetchData') as {
      __lastOptions: { hasDataCheck?: (data: unknown) => boolean }
    }
    const hasDataCheck = useFetchDataModule.__lastOptions.hasDataCheck

    expect(hasDataCheck).toBeDefined()
    // null data
    expect(hasDataCheck!(null)).toBe(false)
    // data with null ratios
    expect(hasDataCheck!({ ratios: null })).toBe(false)
    // data with ratios
    expect(hasDataCheck!({ ratios: { current_ratio: 1.5 } })).toBe(true)
  })

  it('clearRatios calls underlying clear', () => {
    const { result } = renderHook(() => useIndustryRatios())

    result.current.clearRatios()

    expect(mockClear).toHaveBeenCalledTimes(1)
  })

  it('propagates error from useFetchData', () => {
    mockError = 'Server error'

    const { result } = renderHook(() => useIndustryRatios())

    expect(result.current.error).toBe('Server error')
  })

  it('respects autoFetch=false', () => {
    renderHook(() => useIndustryRatios({ autoFetch: false }))

    const useFetchDataModule = jest.requireMock('@/hooks/useFetchData') as {
      __lastOptions: { autoFetch?: boolean }
    }

    expect(useFetchDataModule.__lastOptions.autoFetch).toBe(false)
  })

  it('passes autoFetch and clientId to useFetchData', () => {
    renderHook(() => useIndustryRatios({ autoFetch: true, clientId: 99 }))

    const useFetchDataModule = jest.requireMock('@/hooks/useFetchData') as {
      __lastOptions: { autoFetch?: boolean; initialId?: number }
    }

    expect(useFetchDataModule.__lastOptions.autoFetch).toBe(true)
    expect(useFetchDataModule.__lastOptions.initialId).toBe(99)
  })

  it('buildUrl generates correct URL for clientId', () => {
    renderHook(() => useIndustryRatios())

    const useFetchDataModule = jest.requireMock('@/hooks/useFetchData') as {
      __lastBuildUrl: (id: number) => string
    }
    const buildUrl = useFetchDataModule.__lastBuildUrl

    expect(buildUrl(42)).toBe('/clients/42/industry-ratios')
    expect(buildUrl(1)).toBe('/clients/1/industry-ratios')
  })
})
