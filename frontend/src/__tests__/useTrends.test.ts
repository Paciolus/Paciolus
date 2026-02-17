/**
 * Sprint 276: useTrends hook tests
 */
import { renderHook, act } from '@testing-library/react'

const mockApiGet = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  isAuthError: jest.fn((status: number) => status === 401 || status === 403),
}))

jest.mock('@/types/metrics', () => ({
  METRIC_DISPLAY_NAMES: {} as Record<string, string>,
  PERCENTAGE_METRICS: new Set<string>(),
  CURRENCY_METRICS: new Set<string>(),
}))

jest.mock('@/components/analytics/TrendSparkline', () => ({
  __esModule: true,
}))

import { useTrends } from '@/hooks/useTrends'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock

const mockTrendSummary = {
  metric_name: 'total_assets',
  data_points: [
    { period_date: '2025-01-01', value: 100000, change_from_previous: null, change_percent: null },
    { period_date: '2025-06-01', value: 120000, change_from_previous: 20000, change_percent: 20 },
  ],
  overall_direction: 'positive',
  total_change: 20000,
  total_change_percent: 20,
  periods_analyzed: 2,
  average_value: 110000,
  min_value: 100000,
  max_value: 120000,
}

const mockApiResponse = {
  client_id: 1,
  client_name: 'Acme Corp',
  analysis: {
    periods_analyzed: 2,
    date_range: { start: '2025-01-01', end: '2025-06-01' },
    category_trends: { total_assets: mockTrendSummary },
    ratio_trends: { current_ratio: { ...mockTrendSummary, metric_name: 'current_ratio' } },
  },
  periods_analyzed: 2,
  period_type_filter: null,
}

describe('useTrends', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
  })

  it('initializes with empty trends', () => {
    const { result } = renderHook(() => useTrends())

    expect(result.current.categoryTrends).toEqual([])
    expect(result.current.ratioTrends).toEqual([])
    expect(result.current.periodsAnalyzed).toBe(0)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.hasData).toBe(false)
  })

  it('fetchTrends calls apiGet with correct URL and params', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('/clients/1/trends'),
      'test-token'
    )
    // Default limit=12 should be in the URL
    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('limit=12'),
      'test-token'
    )
  })

  it('fetchTrends with periodType adds query param', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1, 'quarterly')
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('period_type=quarterly'),
      'test-token'
    )
  })

  it('sets categoryTrends and ratioTrends on success', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(result.current.categoryTrends).toHaveLength(1)
    expect(result.current.categoryTrends[0].metricName).toBe('total_assets')
    expect(result.current.ratioTrends).toHaveLength(1)
    expect(result.current.ratioTrends[0].metricName).toBe('current_ratio')
    expect(result.current.periodsAnalyzed).toBe(2)
  })

  it('hasData true when trends exist', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(result.current.hasData).toBe(true)
  })

  it('clearTrends resets all state', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })
    expect(result.current.categoryTrends).toHaveLength(1)

    act(() => { result.current.clearTrends() })

    expect(result.current.categoryTrends).toEqual([])
    expect(result.current.ratioTrends).toEqual([])
    expect(result.current.periodsAnalyzed).toBe(0)
    expect(result.current.dateRange).toEqual({ start: null, end: null })
    expect(result.current.error).toBeNull()
    expect(result.current.hasData).toBe(false)
  })

  it('handles auth error (isAuthError)', async () => {
    mockApiGet.mockResolvedValue({
      ok: false,
      error: 'Unauthorized',
      status: 401,
    })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(result.current.error).toBe('Session expired. Please log in again.')
    expect(result.current.categoryTrends).toEqual([])
    expect(result.current.ratioTrends).toEqual([])
  })

  it('handles API error (sets error message)', async () => {
    mockApiGet.mockResolvedValue({
      ok: false,
      error: 'Internal server error',
      status: 500,
    })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(result.current.error).toBe('Internal server error')
    expect(result.current.categoryTrends).toEqual([])
  })

  it('handles null analysis in response', async () => {
    mockApiGet.mockResolvedValue({
      ok: true,
      data: {
        client_id: 1,
        client_name: 'Acme',
        analysis: null,
        periods_analyzed: 0,
        period_type_filter: null,
      },
    })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(result.current.error).toBe('No trend data available')
    expect(result.current.categoryTrends).toEqual([])
    expect(result.current.ratioTrends).toEqual([])
  })

  it('no fetch when token is null (sets Authentication required error)', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useTrends())

    await act(async () => {
      await result.current.fetchTrends(1)
    })

    expect(mockApiGet).not.toHaveBeenCalled()
    expect(result.current.error).toBe('Authentication required')
  })
})
