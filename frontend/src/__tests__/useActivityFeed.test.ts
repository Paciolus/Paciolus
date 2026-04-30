/**
 * Sprint 751: useActivityFeed hook tests.
 */
import { act, renderHook, waitFor } from '@testing-library/react'
import { useActivityFeed } from '@/hooks/useActivityFeed'

const mockApiGet = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
}))

const sample = [
  {
    id: 1,
    tool_name: 'journal_entry_testing',
    tool_label: 'JE Testing',
    filename: 'q1.xlsx',
    record_count: 4500,
    summary: { flagged_count: 12 },
    created_at: '2026-04-29T11:30:00Z',
  },
]

describe('useActivityFeed', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches /activity/tool-feed?limit=8 by default on mount', async () => {
    mockApiGet.mockResolvedValue({ ok: true, status: 200, data: sample })
    const { result } = renderHook(() => useActivityFeed('tok'))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(mockApiGet).toHaveBeenCalledWith('/activity/tool-feed?limit=8', 'tok')
    expect(result.current.activity).toEqual(sample)
  })

  it('honors a custom limit option', async () => {
    mockApiGet.mockResolvedValue({ ok: true, status: 200, data: [] })
    renderHook(() => useActivityFeed('tok', { limit: 25 }))
    await waitFor(() => expect(mockApiGet).toHaveBeenCalled())
    expect(mockApiGet).toHaveBeenCalledWith('/activity/tool-feed?limit=25', 'tok')
  })

  it('does not fetch when token is null', () => {
    renderHook(() => useActivityFeed(null))
    expect(mockApiGet).not.toHaveBeenCalled()
  })

  it('sets error and calls onError on fetch failure', async () => {
    mockApiGet.mockRejectedValue(new Error('boom'))
    const onError = jest.fn()
    const { result } = renderHook(() => useActivityFeed('tok', { onError }))
    await waitFor(() => expect(result.current.error).toBe(true))
    expect(onError).toHaveBeenCalledWith('Failed to load activity feed')
  })

  it('retry refetches and clears error', async () => {
    mockApiGet.mockRejectedValueOnce(new Error('boom'))
    const { result } = renderHook(() => useActivityFeed('tok'))
    await waitFor(() => expect(result.current.error).toBe(true))

    mockApiGet.mockResolvedValueOnce({ ok: true, status: 200, data: sample })
    await act(async () => {
      result.current.retry()
    })
    await waitFor(() => expect(result.current.activity).toEqual(sample))
    expect(result.current.error).toBe(false)
  })
})
