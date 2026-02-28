/**
 * Sprint 236: useBenchmarks hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useBenchmarks } from '@/hooks/useBenchmarks'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  isAuthError: jest.fn((status: number) => status === 401 || status === 403),
}))


const mockUseAuth = useAuth as jest.Mock

const mockBenchmarkSet = {
  industry: 'technology',
  fiscal_year: 2025,
  benchmarks: { current_ratio: { ratio_name: 'current_ratio', p50: 1.5, mean: 1.6 } },
  source_attribution: 'Public data',
  data_quality_score: 0.85,
  available_ratios: ['current_ratio'],
}

const mockComparison = {
  industry: 'technology',
  fiscal_year: 2025,
  comparisons: [{ ratio_name: 'current_ratio', percentile: 65, position: 'above_average' }],
  overall_score: 72,
  overall_health: 'mid_range',
  source_attribution: 'Public data',
  generated_at: '2026-01-15T12:00:00Z',
  disclaimer: 'For informational purposes only.',
}

describe('useBenchmarks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useBenchmarks())
    expect(result.current.availableIndustries).toEqual([])
    expect(result.current.benchmarkSet).toBeNull()
    expect(result.current.comparisonResults).toBeNull()
    expect(result.current.sources).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('fetchIndustries calls public endpoint (no token)', async () => {
    mockApiGet.mockResolvedValue({
      ok: true,
      data: ['technology', 'healthcare', 'retail'],
    })

    const { result } = renderHook(() => useBenchmarks())

    await act(async () => { await result.current.fetchIndustries() })

    expect(mockApiGet).toHaveBeenCalledWith('/benchmarks/industries', null)
    expect(result.current.availableIndustries).toEqual(['technology', 'healthcare', 'retail'])
  })

  it('fetchBenchmarks calls public endpoint with industry', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockBenchmarkSet })

    const { result } = renderHook(() => useBenchmarks())

    await act(async () => { await result.current.fetchBenchmarks('technology') })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/benchmarks/technology?fiscal_year=2025',
      null
    )
    expect(result.current.benchmarkSet).toEqual(mockBenchmarkSet)
  })

  it('compareToBenchmarks calls POST with auth', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparison })

    const { result } = renderHook(() => useBenchmarks())

    await act(async () => {
      await result.current.compareToBenchmarks(
        { current_ratio: 1.8 },
        'Technology'
      )
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/benchmarks/compare',
      'test-token',
      { ratios: { current_ratio: 1.8 }, industry: 'technology' }
    )
    expect(result.current.comparisonResults).toEqual(mockComparison)
  })

  it('compareToBenchmarks requires auth', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useBenchmarks())

    await act(async () => {
      await result.current.compareToBenchmarks({ current_ratio: 1.8 }, 'technology')
    })

    expect(mockApiPost).not.toHaveBeenCalled()
    expect(result.current.error).toBe('Authentication required for comparison')
  })

  it('fetchSources calls public endpoint', async () => {
    const mockSources = {
      primary_sources: [{ name: 'RMA', description: 'Annual Statement Studies' }],
      coverage: { industries: 6, ratios_per_industry: 9, fiscal_year: 2025 },
      disclaimer: 'For reference only.',
      last_updated: '2026-01-01',
      available_industries: ['technology'],
    }
    mockApiGet.mockResolvedValue({ ok: true, data: mockSources })

    const { result } = renderHook(() => useBenchmarks())

    await act(async () => { await result.current.fetchSources() })

    expect(mockApiGet).toHaveBeenCalledWith('/benchmarks/sources', null)
    expect(result.current.sources).toEqual(mockSources)
  })

  it('clear resets data but not industries', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockBenchmarkSet })

    const { result } = renderHook(() => useBenchmarks())

    // Populate benchmark data
    await act(async () => { await result.current.fetchBenchmarks('technology') })
    expect(result.current.benchmarkSet).toBeDefined()

    // Clear
    act(() => { result.current.clear() })

    expect(result.current.benchmarkSet).toBeNull()
    expect(result.current.comparisonResults).toBeNull()
    expect(result.current.sources).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('sets error on failed fetch', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Not found' })

    const { result } = renderHook(() => useBenchmarks())

    await act(async () => { await result.current.fetchBenchmarks('unknown') })

    expect(result.current.error).toBe('Not found')
    expect(result.current.benchmarkSet).toBeNull()
  })
})
