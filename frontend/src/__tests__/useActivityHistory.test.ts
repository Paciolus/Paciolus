/**
 * Sprint 276: useActivityHistory hook tests
 */
import { renderHook, act } from '@testing-library/react'

const mockApiGet = jest.fn()
const mockPrefetch = jest.fn()
const mockMapActivityLogToAuditActivity = jest.fn((x: unknown) => x)

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
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
  HISTORY_STORAGE_KEY: 'paciolus_audit_history',
  HISTORY_VERSION: '1.0.0',
  mapActivityLogToAuditActivity: (...args: unknown[]) => mockMapActivityLogToAuditActivity(...args),
}))

import { useActivityHistory } from '@/hooks/useActivityHistory'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock

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
  activities: [mockActivity],
  total_count: 55,
  page: 1,
  page_size: 50,
}

// localStorage mock
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => { store[key] = value }),
    removeItem: jest.fn((key: string) => { delete store[key] }),
    clear: jest.fn(() => { store = {} }),
  }
})()
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('useActivityHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorageMock.clear()
    mockUseAuth.mockReturnValue({
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

  it('falls back to localStorage when unauthenticated', async () => {
    mockUseAuth.mockReturnValue({
      token: null,
      isAuthenticated: false,
      isLoading: false,
    })

    const storedData = {
      version: '1.0.0',
      activities: [mockActivity],
    }
    localStorageMock.getItem.mockReturnValue(JSON.stringify(storedData))

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })

    expect(mockApiGet).not.toHaveBeenCalled()
    expect(localStorageMock.getItem).toHaveBeenCalledWith('paciolus_audit_history')
    expect(result.current.activities).toEqual([mockActivity])
    expect(result.current.totalCount).toBe(1)
  })

  it('falls back to localStorage on auth error (isAuthError returns true)', async () => {
    mockApiGet.mockResolvedValue({ ok: false, status: 401, data: null })

    const storedData = {
      version: '1.0.0',
      activities: [mockActivity],
    }
    localStorageMock.getItem.mockReturnValue(JSON.stringify(storedData))

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })

    expect(localStorageMock.getItem).toHaveBeenCalledWith('paciolus_audit_history')
    expect(result.current.activities).toEqual([mockActivity])
  })

  it('handles API error gracefully (sets error, falls back to localStorage)', async () => {
    mockApiGet.mockRejectedValue(new Error('Network error'))

    const storedData = {
      version: '1.0.0',
      activities: [mockActivity],
    }
    localStorageMock.getItem.mockReturnValue(JSON.stringify(storedData))

    const { result } = renderHook(() =>
      useActivityHistory({ autoFetch: false })
    )

    await act(async () => { await result.current.refetch() })

    expect(result.current.error).toBe('Failed to load history. Showing local data.')
    expect(result.current.activities).toEqual([mockActivity])
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
