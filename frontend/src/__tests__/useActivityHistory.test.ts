/**
 * Sprint 276: useActivityHistory hook tests
 * Updated: Remove sessionStorage fallback tests (zero-storage remediation)
 */
import { renderHook, act } from '@testing-library/react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useActivityHistory } from '@/hooks/useActivityHistory'

const mockApiGet = jest.fn()
const mockPrefetch = jest.fn()
const mockMapActivityLogToAuditActivity = jest.fn((x: unknown) => x)

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

jest.mock('@/types/history', () => ({
  mapActivityLogToAuditActivity: (...args: unknown[]) => mockMapActivityLogToAuditActivity(...args),
}))


const mockUseAuthSession = useAuthSession as jest.Mock

const mockActivity = {
  id: 1,
  timestamp: '2026-02-15T10:00:00Z',
  filenameHash: 'abc123',
  rowCount: 100,
  balanced: true,
  totalDebits: 50000,
  totalCredits: 50000,
  materialityThreshold: 1000,
  anomalyCount: 2,
  materialCount: 1,
  immaterialCount: 1,
}

const mockApiResponse = {
  items: [mockActivity],
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
    mockMapActivityLogToAuditActivity.mockImplementation((x: unknown) => x)
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
    expect(result.current.activities).toEqual([mockActivity])
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
