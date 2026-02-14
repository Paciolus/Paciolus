/**
 * Sprint 237: useFetchData hook tests
 */
import { renderHook, act } from '@testing-library/react'

const mockApiGet = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
}))

import { useFetchData } from '@/hooks/useFetchData'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock

describe('useFetchData', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() =>
      useFetchData({ buildUrl: (id) => `/api/${id}` })
    )

    expect(result.current.data).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.hasData).toBe(false)
  })

  it('fetch calls API and sets data', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: { name: 'Test' } })

    const { result } = renderHook(() =>
      useFetchData<{ name: string }>({
        buildUrl: (id) => `/api/${id}`,
      })
    )

    await act(async () => { await result.current.fetch(1) })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/api/1',
      'test-token',
      expect.any(Object)
    )
    expect(result.current.data).toEqual({ name: 'Test' })
    expect(result.current.hasData).toBe(true)
  })

  it('applies transform function', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: { items: [1, 2, 3], total: 3 } })

    const { result } = renderHook(() =>
      useFetchData<{ items: number[]; total: number }, number[]>({
        buildUrl: (id) => `/api/${id}`,
        transform: (res) => res.items,
      })
    )

    await act(async () => { await result.current.fetch(1) })

    expect(result.current.data).toEqual([1, 2, 3])
  })

  it('sets error on failed fetch', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Not found' })

    const { result } = renderHook(() =>
      useFetchData({ buildUrl: (id) => `/api/${id}` })
    )

    await act(async () => { await result.current.fetch(1) })

    expect(result.current.error).toBe('Not found')
    expect(result.current.data).toBeNull()
  })

  it('requires authentication', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() =>
      useFetchData({ buildUrl: (id) => `/api/${id}` })
    )

    await act(async () => { await result.current.fetch(1) })

    expect(mockApiGet).not.toHaveBeenCalled()
    expect(result.current.error).toBe('Authentication required')
  })

  it('clear resets all state', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: { value: 42 } })

    const { result } = renderHook(() =>
      useFetchData({ buildUrl: (id) => `/api/${id}` })
    )

    await act(async () => { await result.current.fetch(1) })
    expect(result.current.data).toBeDefined()

    act(() => { result.current.clear() })

    expect(result.current.data).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.hasData).toBe(false)
  })

  it('refetch reuses last params', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: { value: 1 } })

    const { result } = renderHook(() =>
      useFetchData({ buildUrl: (id) => `/api/${id}` })
    )

    await act(async () => { await result.current.fetch(5) })
    mockApiGet.mockClear()

    await act(async () => { await result.current.refetch() })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/api/5',
      'test-token',
      expect.any(Object)
    )
  })

  it('uses custom hasDataCheck', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: { items: [] } })

    const { result } = renderHook(() =>
      useFetchData<{ items: number[] }>({
        buildUrl: (id) => `/api/${id}`,
        hasDataCheck: (data) => data !== null && data.items.length > 0,
      })
    )

    await act(async () => { await result.current.fetch(1) })

    // data exists but hasData is false because items is empty
    expect(result.current.data).toEqual({ items: [] })
    expect(result.current.hasData).toBe(false)
  })

  it('builds URL with params', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: {} })

    const { result } = renderHook(() =>
      useFetchData({
        buildUrl: (id, params) => `/api/${id}?type=${params?.type}`,
      })
    )

    await act(async () => {
      await result.current.fetch(1, { type: 'summary' })
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/api/1?type=summary',
      'test-token',
      expect.any(Object)
    )
  })
})
