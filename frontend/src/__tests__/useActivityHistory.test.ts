/**
 * Sprint 276: useActivityHistory hook tests
 * Updated: Remove sessionStorage fallback tests (zero-storage remediation)
 */
import { renderHook, act } from '@testing-library/react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useActivityHistory } from '@/hooks/useActivityHistory'

const mockApiGet = jest.fn()
const mockPrefetch = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    token: 'test-token',
    isAuthenticated: true,
    isLoading: false,
  })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  isAuthError: jest.fn((status: number) => status === 401 || status === 403),
  prefetch: (...args: unknown[]) => mockPrefetch(...args),
}))


const mockUseAuthSession = useAuthSession as jest.Mock

/**
 * Sprint 889 (14D, review TQ-09): a raw `/activity/history` item exactly as
 * ActivityLogResponse (backend/routes/activity.py) sends it, run through the
 * real mapper. The old test replaced the mapper with an identity function and
 * mocked camelCase fields the backend never sends.
 */
const rawActivityLog = {
  id: 1,
  filename_hash: 'abc123',
  filename_display: 'TB-2026.xlsx',
  timestamp: '2026-02-15T10:00:00Z',
  record_count: 100,
  total_debits: 50000.25,
  total_credits: 50000,
  materiality_threshold: 1000,
  was_balanced: false,
  anomaly_count: 2,
  material_count: 1,
  immaterial_count: 1,
  is_consolidated: false,
  sheet_count: null,
  chain_hash: null,
}

const mockApiResponse = {
  items: [rawActivityLog],
  total_count: 55,
  page: 1,
  page_size: 50,
}

describe('useActivityHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuthSession.mockReturnValue({
      token: 'test-token',
      isAuthenticated: true,
      isLoading: false,
    })
  })

  it('initializes with empty activities and loading', () => {
    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    expect(result.current.activities).toEqual([])
    expect(result.current.isLoading).toBe(true)
    expect(result.current.error).toBeNull()
    expect(result.current.totalCount).toBe(0)
    expect(result.current.page).toBe(1)
  })

  it('fetches activities from API on mount when autoFetch is true', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: true })
    )

    // Wait for the auto-fetch effect to fire
    await act(async () => {})

    expect(mockApiGet).toHaveBeenCalledWith(
      '/activity/history?page=1&page_size=50',
      'test-token'
    )
    expect(result.current.activities).toHaveLength(1)
    const [activity] = result.current.activities
    expect(activity.rowCount).toBe(100)
    expect(activity.totalDebits).toBe(50000.25)
    expect(activity.totalCredits).toBe(50000)
    expect(activity.difference).toBeCloseTo(0.25, 10)
    expect(activity.balanced).toBe(false)
    expect(activity.filenameDisplay).toBe('TB-2026.xlsx')
    expect(result.current.isLoading).toBe(false)
  })

  it('returns paginated data (totalCount, page, totalPages)', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false, pageSize: 50 })
    )

    await act(async () => { await result.current.refetch() })

    expect(result.current.totalCount).toBe(55)
    expect(result.current.page).toBe(1)
    // 55 items / 50 per page = 2 pages
    expect(result.current.totalPages).toBe(2)
  })

  it('hasNextPage/hasPrevPage computed correctly', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false, pageSize: 50 })
    )

    await act(async () => { await result.current.refetch() })

    // Page 1 of 2: hasNextPage=true, hasPrevPage=false
    expect(result.current.hasNextPage).toBe(true)
    expect(result.current.hasPrevPage).toBe(false)
  })

  it('nextPage/prevPage update page number', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false, pageSize: 50 })
    )

    await act(async () => { await result.current.refetch() })

    // Go to next page
    act(() => { result.current.nextPage() })
    expect(result.current.page).toBe(2)

    // Go back to prev page
    act(() => { result.current.prevPage() })
    expect(result.current.page).toBe(1)

    // prevPage should not go below 1
    act(() => { result.current.prevPage() })
    expect(result.current.page).toBe(1)
  })

  it('shows empty state when unauthenticated (no sessionStorage fallback)', async () => {
    mockUseAuthSession.mockReturnValue({
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })

    expect(mockApiGet).not.toHaveBeenCalled()
    expect(result.current.activities).toEqual([])
    expect(result.current.totalCount).toBe(0)
    expect(result.current.isLoading).toBe(false)
  })

  it('shows error on auth error without sessionStorage fallback', async () => {
    mockApiGet.mockResolvedValue({ ok: false, status: 401, data: null })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })

    expect(result.current.activities).toEqual([])
    expect(result.current.totalCount).toBe(0)
    expect(result.current.error).toBe('Session expired. Please log in again.')
  })

  it('handles API error gracefully without sessionStorage fallback', async () => {
    mockApiGet.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })

    expect(result.current.error).toBe('Failed to load history. Please try again.')
    expect(result.current.activities).toEqual([])
    expect(result.current.totalCount).toBe(0)
    expect(result.current.isLoading).toBe(false)
  })

  it('refetch triggers new API call', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })
    expect(mockApiGet).toHaveBeenCalledTimes(1)

    mockApiGet.mockClear()

    await act(async () => { await result.current.refetch() })
    expect(mockApiGet).toHaveBeenCalledTimes(1)
  })

  it('respects autoFetch=false', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: mockApiResponse })

    renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    // Wait for any potential effects
    await act(async () => {})

    expect(mockApiGet).not.toHaveBeenCalled()
  })
})
