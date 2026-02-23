/**
 * Sprint 237: usePriorPeriod hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { usePriorPeriod } from '@/hooks/usePriorPeriod'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))


describe('usePriorPeriod', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => usePriorPeriod('test-token'))

    expect(result.current.periods).toEqual([])
    expect(result.current.comparison).toBeNull()
    expect(result.current.isLoadingPeriods).toBe(false)
    expect(result.current.isLoadingComparison).toBe(false)
    expect(result.current.isSaving).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchPeriods calls API and populates periods', async () => {
    const mockPeriods = [
      { id: 1, period_label: 'FY2024', created_at: '2025-06-01' },
      { id: 2, period_label: 'FY2023', created_at: '2024-06-01' },
    ]
    mockApiGet.mockResolvedValue({ ok: true, data: mockPeriods })

    const { result } = renderHook(() => usePriorPeriod('test-token'))

    await act(async () => { await result.current.fetchPeriods(1) })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/clients/1/periods',
      'test-token'
    )
    expect(result.current.periods).toEqual(mockPeriods)
  })

  it('savePeriod calls POST and refreshes list', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: { period_id: 3 } })
    mockApiGet.mockResolvedValue({ ok: true, data: [] })

    const { result } = renderHook(() => usePriorPeriod('test-token'))

    let saved: unknown
    await act(async () => {
      saved = await result.current.savePeriod(1, {
        period_label: 'FY2025',
      } as never)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/clients/1/periods',
      'test-token',
      expect.objectContaining({ period_label: 'FY2025' })
    )
    expect(saved).toEqual({ period_id: 3 })
    // savePeriod calls fetchPeriods after success
    expect(mockApiGet).toHaveBeenCalled()
  })

  it('comparePeriods calls POST and sets comparison', async () => {
    const mockComparison = {
      current_label: 'FY2025',
      prior_label: 'FY2024',
      accounts: [],
      summary: { total_variance: 5000 },
    }
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparison })

    const { result } = renderHook(() => usePriorPeriod('test-token'))

    let comparison: unknown
    await act(async () => {
      comparison = await result.current.comparePeriods({
        period_id: 1,
      } as never)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/compare',
      'test-token',
      expect.objectContaining({ period_id: 1 })
    )
    expect(comparison).toEqual(mockComparison)
    expect(result.current.comparison).toEqual(mockComparison)
  })

  it('clearComparison resets comparison', async () => {
    const mockComparison = { accounts: [], summary: {} }
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparison })

    const { result } = renderHook(() => usePriorPeriod('test-token'))

    await act(async () => {
      await result.current.comparePeriods({ period_id: 1 } as never)
    })
    expect(result.current.comparison).toBeDefined()

    act(() => { result.current.clearComparison() })
    expect(result.current.comparison).toBeNull()
  })

  it('sets error when no token provided', async () => {
    const { result } = renderHook(() => usePriorPeriod(undefined))

    await act(async () => { await result.current.fetchPeriods(1) })

    expect(mockApiGet).not.toHaveBeenCalled()
    expect(result.current.error).toBe('Authentication required')
  })

  it('sets error on failed fetch', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Server error' })

    const { result } = renderHook(() => usePriorPeriod('test-token'))

    await act(async () => { await result.current.fetchPeriods(1) })

    expect(result.current.error).toBeTruthy()
    expect(result.current.periods).toEqual([])
  })

  it('clearError resets error', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Server error' })

    const { result } = renderHook(() => usePriorPeriod('test-token'))

    await act(async () => { await result.current.fetchPeriods(1) })
    expect(result.current.error).toBeTruthy()

    act(() => { result.current.clearError() })
    expect(result.current.error).toBeNull()
  })
})
