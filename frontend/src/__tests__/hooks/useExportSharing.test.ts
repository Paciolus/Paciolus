/**
 * useExportSharing Hook Tests — Sprint 545c
 */

import { renderHook, act } from '@testing-library/react'
import { useExportSharing } from '@/hooks/useExportSharing'

// Mock auth context
const mockToken = 'test-token'
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ token: mockToken, isAuthenticated: true }),
}))

// Mock API client
const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiDelete = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
}))

const mockShare = {
  token: 'abc123',
  tool: 'trial_balance',
  format: 'pdf',
  created_at: '2026-03-17T10:00:00Z',
  expires_at: '2026-03-19T10:00:00Z',
  access_count: 3,
}

describe('useExportSharing', () => {
  beforeEach(() => {
    mockApiGet.mockReset()
    mockApiPost.mockReset()
    mockApiDelete.mockReset()
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useExportSharing())
    expect(result.current.shares).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('listShares fetches share data', async () => {
    mockApiGet.mockResolvedValueOnce({ data: [mockShare], ok: true })

    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      await result.current.listShares()
    })

    expect(result.current.shares).toEqual([mockShare])
    expect(mockApiGet).toHaveBeenCalledWith('/export-sharing/', mockToken)
  })

  it('createShare adds new share to list', async () => {
    const newShare = { ...mockShare, token: 'new123' }
    mockApiPost.mockResolvedValueOnce({ data: newShare, ok: true })

    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      const share = await result.current.createShare('trial_balance', 'pdf', 'base64data')
      expect(share).toEqual(newShare)
    })

    expect(result.current.shares).toContainEqual(newShare)
    expect(mockApiPost).toHaveBeenCalledWith(
      '/export-sharing/create',
      mockToken,
      { tool: 'trial_balance', format: 'pdf', data: 'base64data' },
    )
  })

  it('revokeShare removes share from list', async () => {
    // First populate
    mockApiGet.mockResolvedValueOnce({ data: [mockShare], ok: true })
    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      await result.current.listShares()
    })
    expect(result.current.shares).toHaveLength(1)

    // Now revoke
    mockApiDelete.mockResolvedValueOnce({ ok: true })

    await act(async () => {
      const ok = await result.current.revokeShare('abc123')
      expect(ok).toBe(true)
    })

    expect(result.current.shares).toHaveLength(0)
  })

  it('handles list error', async () => {
    mockApiGet.mockResolvedValueOnce({ data: null, ok: false, error: 'Forbidden' })

    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      await result.current.listShares()
    })

    expect(result.current.error).toBe('Forbidden')
    expect(result.current.shares).toEqual([])
  })

  it('handles revoke error', async () => {
    mockApiDelete.mockResolvedValueOnce({ ok: false, error: 'Not found' })

    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      const ok = await result.current.revokeShare('nonexistent')
      expect(ok).toBe(false)
    })

    expect(result.current.error).toBe('Not found')
  })
})
