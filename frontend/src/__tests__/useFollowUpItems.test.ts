/**
 * Sprint 276: useFollowUpItems hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useFollowUpItems } from '@/hooks/useFollowUpItems'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiPut = jest.fn()
const mockApiDelete = jest.fn()
const mockIsAuthError = jest.fn(() => false)

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
  isAuthError: (...args: unknown[]) => mockIsAuthError(...args),
}))


const mockUseAuth = useAuth as jest.Mock

const mockItem = {
  id: 1,
  engagement_id: 10,
  title: 'Review suspense accounts',
  description: 'Suspense accounts detected in TB diagnostics',
  severity: 'high',
  disposition: 'open',
  tool_source: 'TB Diagnostics',
  created_at: '2026-02-01T00:00:00Z',
  updated_at: '2026-02-01T00:00:00Z',
}

const mockSummary = {
  total: 5,
  by_severity: { high: 2, medium: 2, low: 1 },
  by_disposition: { open: 3, resolved: 2 },
}

describe('useFollowUpItems', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
    mockApiGet.mockResolvedValue({
      ok: true,
      data: { items: [mockItem], total_count: 1 },
    })
  })

  it('initializes with empty items', () => {
    const { result } = renderHook(() => useFollowUpItems())
    expect(result.current.items).toEqual([])
    expect(result.current.totalCount).toBe(0)
    expect(result.current.summary).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchItems calls apiGet with engagement ID', async () => {
    const { result } = renderHook(() => useFollowUpItems())

    await act(async () => {
      await result.current.fetchItems(10)
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/engagements/10/follow-up-items',
      'test-token',
      { skipCache: true }
    )
    expect(result.current.items).toEqual([mockItem])
    expect(result.current.totalCount).toBe(1)
  })

  it('fetchItems applies severity/disposition/toolSource filters as query params', async () => {
    const { result } = renderHook(() => useFollowUpItems())

    await act(async () => {
      await result.current.fetchItems(10, 'high', 'open', 'TB Diagnostics')
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('/engagements/10/follow-up-items?'),
      'test-token',
      { skipCache: true }
    )
    const calledUrl = (mockApiGet as jest.Mock).mock.calls[0][0] as string
    expect(calledUrl).toContain('severity=high')
    expect(calledUrl).toContain('disposition=open')
    expect(calledUrl).toContain('tool_source=TB+Diagnostics')
  })

  it('fetchItems handles auth error', async () => {
    mockIsAuthError.mockReturnValue(true)
    mockApiGet.mockResolvedValue({ ok: false, error: 'Unauthorized', status: 401 })

    const { result } = renderHook(() => useFollowUpItems())

    await act(async () => {
      await result.current.fetchItems(10)
    })

    expect(mockIsAuthError).toHaveBeenCalledWith(401)
    expect(result.current.error).toBe('Session expired. Please log in again.')
  })

  it('createItem calls apiPost and prepends to items list', async () => {
    const newItem = { ...mockItem, id: 2, title: 'New follow-up' }
    mockApiPost.mockResolvedValue({ ok: true, data: newItem })

    const { result } = renderHook(() => useFollowUpItems())

    // First populate with existing item
    await act(async () => {
      await result.current.fetchItems(10)
    })

    let created: unknown
    await act(async () => {
      created = await result.current.createItem(10, {
        title: 'New follow-up',
        description: 'Test description',
        severity: 'medium',
        disposition: 'open',
        tool_source: 'JE Testing',
      })
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/engagements/10/follow-up-items',
      'test-token',
      expect.objectContaining({ title: 'New follow-up' })
    )
    expect(created).toEqual(newItem)
    // New item should be prepended
    expect(result.current.items[0]).toEqual(newItem)
  })

  it('updateItem calls apiPut and replaces item in list', async () => {
    const updated = { ...mockItem, title: 'Updated title' }
    mockApiPut.mockResolvedValue({ ok: true, data: updated })

    const { result } = renderHook(() => useFollowUpItems())

    // Populate list
    await act(async () => {
      await result.current.fetchItems(10)
    })

    let returnedItem: unknown
    await act(async () => {
      returnedItem = await result.current.updateItem(1, { title: 'Updated title' })
    })

    expect(mockApiPut).toHaveBeenCalledWith(
      '/follow-up-items/1',
      'test-token',
      expect.objectContaining({ title: 'Updated title' })
    )
    expect(returnedItem).toEqual(updated)
    expect(result.current.items[0].title).toBe('Updated title')
  })

  it('deleteItem calls apiDelete and removes item from list', async () => {
    mockApiDelete.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useFollowUpItems())

    // Populate list
    await act(async () => {
      await result.current.fetchItems(10)
    })
    expect(result.current.items).toHaveLength(1)

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.deleteItem(1)
    })

    expect(mockApiDelete).toHaveBeenCalledWith('/follow-up-items/1', 'test-token')
    expect(success).toBe(true)
    expect(result.current.items).toHaveLength(0)
  })

  it('deleteItem returns false when not authenticated', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useFollowUpItems())

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.deleteItem(1)
    })

    expect(success).toBe(false)
    expect(result.current.error).toBe('Not authenticated')
    expect(mockApiDelete).not.toHaveBeenCalled()
  })

  it('fetchSummary calls apiGet and returns summary', async () => {
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockSummary })

    const { result } = renderHook(() => useFollowUpItems())

    let summary: unknown
    await act(async () => {
      summary = await result.current.fetchSummary(10)
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/engagements/10/follow-up-items/summary',
      'test-token',
      { skipCache: true }
    )
    expect(summary).toEqual(mockSummary)
    expect(result.current.summary).toEqual(mockSummary)
  })

  it('handles API errors gracefully', async () => {
    mockIsAuthError.mockReturnValue(false)
    mockApiGet.mockResolvedValue({ ok: false, error: 'Server error', status: 500 })

    const { result } = renderHook(() => useFollowUpItems())

    await act(async () => {
      await result.current.fetchItems(10)
    })

    expect(result.current.error).toBe('Server error')
    expect(result.current.items).toEqual([])
    expect(result.current.isLoading).toBe(false)
  })
})
