/**
 * Sprint 652: useExportSharing hook tests — happy + error paths for
 * list / create / revoke, plus the token-pass-through invariant.
 *
 * Export sharing is a Professional+ feature that delivers user data via
 * a shareable link, so the error path is at least as important as the
 * happy path — callers must not silently pretend a failed revocation
 * succeeded.
 */
import { renderHook, act } from '@testing-library/react'
import { useExportSharing } from '@/hooks/useExportSharing'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiDelete = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ token: 'tok-xyz' }),
}))

jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
}))

const shareA = {
  token: 'sh_a',
  tool: 'tb',
  format: 'pdf',
  created_at: '2026-04-01T00:00:00Z',
  expires_at: '2026-04-08T00:00:00Z',
  single_use: false,
  accessed_count: 0,
}
const shareB = { ...shareA, token: 'sh_b' }

describe('useExportSharing', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('initializes empty with no error', () => {
    const { result } = renderHook(() => useExportSharing())
    expect(result.current.shares).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('listShares: populates state on success and forwards the token', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: [shareA, shareB] })
    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      const rows = await result.current.listShares()
      expect(rows).toEqual([shareA, shareB])
    })

    expect(mockApiGet).toHaveBeenCalledWith('/export-sharing/', 'tok-xyz')
    expect(result.current.shares).toEqual([shareA, shareB])
    expect(result.current.error).toBeNull()
  })

  it('listShares: sets error message on failure', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Forbidden' })
    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      const rows = await result.current.listShares()
      expect(rows).toBeNull()
    })

    expect(result.current.error).toBe('Forbidden')
    expect(result.current.shares).toEqual([])
  })

  it('createShare: prepends new share to state', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: [shareA] })
    mockApiPost.mockResolvedValue({ ok: true, data: shareB })

    const { result } = renderHook(() => useExportSharing())
    await act(async () => {
      await result.current.listShares()
    })

    await act(async () => {
      const created = await result.current.createShare('tb', 'pdf', 'Zm9v')
      expect(created).toEqual(shareB)
    })

    expect(result.current.shares[0]).toEqual(shareB)
    expect(result.current.shares[1]).toEqual(shareA)
  })

  it('createShare: forwards passcode and single_use opts', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: shareA })
    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      await result.current.createShare('tb', 'pdf', 'Zm9v', { passcode: 'secret', singleUse: true })
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/export-sharing/create',
      'tok-xyz',
      expect.objectContaining({ tool: 'tb', format: 'pdf', data: 'Zm9v', passcode: 'secret', single_use: true }),
    )
  })

  it('createShare: surfaces error and returns null on failure', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Plan does not include sharing' })
    const { result } = renderHook(() => useExportSharing())

    await act(async () => {
      const created = await result.current.createShare('tb', 'pdf', 'Zm9v')
      expect(created).toBeNull()
    })

    expect(result.current.error).toBe('Plan does not include sharing')
  })

  it('revokeShare: removes the target share on success', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: [shareA, shareB] })
    mockApiDelete.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useExportSharing())
    await act(async () => {
      await result.current.listShares()
    })

    await act(async () => {
      const ok = await result.current.revokeShare('sh_a')
      expect(ok).toBe(true)
    })

    expect(result.current.shares.map(s => s.token)).toEqual(['sh_b'])
    expect(mockApiDelete).toHaveBeenCalledWith('/export-sharing/sh_a', 'tok-xyz')
  })

  it('revokeShare: returns false and preserves state on failure', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: [shareA] })
    mockApiDelete.mockResolvedValue({ ok: false, error: 'Already revoked' })

    const { result } = renderHook(() => useExportSharing())
    await act(async () => {
      await result.current.listShares()
    })

    await act(async () => {
      const ok = await result.current.revokeShare('sh_a')
      expect(ok).toBe(false)
    })

    expect(result.current.shares.map(s => s.token)).toEqual(['sh_a'])
    expect(result.current.error).toBe('Already revoked')
  })
})
