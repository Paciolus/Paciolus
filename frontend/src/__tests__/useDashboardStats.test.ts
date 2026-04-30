/**
 * Sprint 751: useDashboardStats hook tests.
 */
import { act, renderHook, waitFor } from '@testing-library/react'
import { useDashboardStats } from '@/hooks/useDashboardStats'

const mockApiGet = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
}))

const sample = {
  total_clients: 3,
  assessments_today: 1,
  last_assessment_date: '2026-04-29T10:00:00Z',
  total_assessments: 10,
  tool_runs_today: 2,
  total_tool_runs: 25,
  active_workspaces: 1,
  tools_used: 5,
}

describe('useDashboardStats', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('starts in loading=true and fetches /dashboard/stats on mount', async () => {
    mockApiGet.mockResolvedValue({ ok: true, status: 200, data: sample })
    const { result } = renderHook(() => useDashboardStats('tok'))
    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(mockApiGet).toHaveBeenCalledWith('/dashboard/stats', 'tok')
    expect(result.current.stats).toEqual(sample)
    expect(result.current.error).toBe(false)
  })

  it('does not fetch when token is null', async () => {
    const { result } = renderHook(() => useDashboardStats(null))
    // No fetch issued — loading stays at initial value.
    expect(mockApiGet).not.toHaveBeenCalled()
    expect(result.current.stats).toBeNull()
  })

  it('sets error=true and calls onError on fetch failure', async () => {
    mockApiGet.mockRejectedValue(new Error('500'))
    const onError = jest.fn()
    const { result } = renderHook(() => useDashboardStats('tok', { onError }))
    await waitFor(() => expect(result.current.error).toBe(true))
    expect(onError).toHaveBeenCalledWith('Failed to load dashboard stats')
    expect(result.current.stats).toBeNull()
  })

  it('retry refetches and clears error', async () => {
    mockApiGet.mockRejectedValueOnce(new Error('500'))
    const { result } = renderHook(() => useDashboardStats('tok'))
    await waitFor(() => expect(result.current.error).toBe(true))

    mockApiGet.mockResolvedValueOnce({ ok: true, status: 200, data: sample })
    await act(async () => {
      result.current.retry()
    })
    await waitFor(() => expect(result.current.error).toBe(false))
    expect(result.current.stats).toEqual(sample)
  })
})
