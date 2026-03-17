/**
 * useAdminDashboard Hook Tests — Sprint 545a
 */

import { renderHook, act } from '@testing-library/react'
import { useAdminDashboard } from '@/hooks/useAdminDashboard'

// Mock auth context
const mockToken = 'test-token'
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ token: mockToken, isAuthenticated: true }),
}))

// Mock API client
const mockApiGet = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
}))

// Mock download adapter
const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()
jest.mock('@/utils/downloadAdapter', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

describe('useAdminDashboard', () => {
  beforeEach(() => {
    mockApiGet.mockReset()
    mockApiDownload.mockReset()
    mockDownloadBlob.mockReset()
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useAdminDashboard())
    expect(result.current.overview).toBeNull()
    expect(result.current.teamActivity).toEqual([])
    expect(result.current.memberUsage).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchOverview sets overview data on success', async () => {
    const mockOverview = {
      total_members: 5,
      total_uploads_30d: 42,
      active_members_30d: 3,
      top_tool: 'trial_balance',
    }
    mockApiGet.mockResolvedValueOnce({ data: mockOverview, ok: true })

    const { result } = renderHook(() => useAdminDashboard())

    await act(async () => {
      await result.current.fetchOverview()
    })

    expect(result.current.overview).toEqual(mockOverview)
    expect(result.current.error).toBeNull()
    expect(mockApiGet).toHaveBeenCalledWith('/admin/overview', mockToken)
  })

  it('fetchOverview sets error on failure', async () => {
    mockApiGet.mockResolvedValueOnce({ data: null, ok: false, error: 'Server error' })

    const { result } = renderHook(() => useAdminDashboard())

    await act(async () => {
      await result.current.fetchOverview()
    })

    expect(result.current.overview).toBeNull()
    expect(result.current.error).toBe('Server error')
  })

  it('fetchTeamActivity passes filter params', async () => {
    mockApiGet.mockResolvedValueOnce({ data: [], ok: true })

    const { result } = renderHook(() => useAdminDashboard())

    await act(async () => {
      await result.current.fetchTeamActivity(7, 'je_testing', 'user@test.com')
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/admin/team-activity?days=7&tool=je_testing&member=user%40test.com',
      mockToken,
    )
  })

  it('fetchUsageByMember returns member usage', async () => {
    const mockUsage = [
      { user_id: 1, email: 'a@test.com', uploads_30d: 10, last_active: '2026-03-17', top_tool: 'ap_testing' },
    ]
    mockApiGet.mockResolvedValueOnce({ data: mockUsage, ok: true })

    const { result } = renderHook(() => useAdminDashboard())

    await act(async () => {
      await result.current.fetchUsageByMember()
    })

    expect(result.current.memberUsage).toEqual(mockUsage)
  })

  it('exportActivityCsv triggers download', async () => {
    const blob = new Blob(['csv data'], { type: 'text/csv' })
    mockApiDownload.mockResolvedValueOnce({ blob, filename: 'activity.csv', ok: true })

    const { result } = renderHook(() => useAdminDashboard())

    await act(async () => {
      const ok = await result.current.exportActivityCsv()
      expect(ok).toBe(true)
    })

    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'activity.csv')
  })
})
