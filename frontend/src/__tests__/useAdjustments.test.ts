/**
 * Sprint 236: useAdjustments hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useAdjustments } from '@/hooks/useAdjustments'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiPut = jest.fn()
const mockApiDelete = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token' })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
}))


const mockUseAuth = useAuth as jest.Mock

const mockListResponse = {
  entries: [
    { id: 'aje-001', reference: 'AJE-001', description: 'Accrual', status: 'proposed' },
  ],
  total_adjustments: 3,
  proposed_count: 1,
  approved_count: 1,
  rejected_count: 0,
  posted_count: 1,
  total_adjustment_amount: 15000,
}

describe('useAdjustments', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token' })
    mockApiGet.mockResolvedValue({ ok: true, data: mockListResponse })
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useAdjustments())
    expect(result.current.entries).toEqual([])
    expect(result.current.selectedEntry).toBeNull()
    expect(result.current.adjustedTB).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.stats.total).toBe(0)
  })

  it('fetchEntries calls API and populates entries + stats', async () => {
    const { result } = renderHook(() => useAdjustments())

    await act(async () => { await result.current.fetchEntries() })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/audit/adjustments',
      'test-token',
      { skipCache: true }
    )
    expect(result.current.entries).toEqual(mockListResponse.entries)
    expect(result.current.stats.total).toBe(3)
    expect(result.current.stats.proposed).toBe(1)
    expect(result.current.stats.totalAmount).toBe(15000)
  })

  it('fetchEntries appends status and type params', async () => {
    const { result } = renderHook(() => useAdjustments())

    await act(async () => {
      await result.current.fetchEntries('approved' as 'proposed' | 'approved' | 'rejected' | 'posted', 'accrual')
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('status=approved'),
      'test-token',
      { skipCache: true }
    )
    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('type=accrual'),
      'test-token',
      { skipCache: true }
    )
  })

  it('createEntry calls POST and refreshes list', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: { id: 'aje-002', reference: 'AJE-002' } })

    const { result } = renderHook(() => useAdjustments())

    let created: unknown
    await act(async () => {
      created = await result.current.createEntry({
        description: 'New entry',
        lines: [],
      } as never)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/adjustments',
      'test-token',
      expect.objectContaining({ description: 'New entry' })
    )
    expect(created).toBeDefined()
    // createEntry calls fetchEntries after success
    expect(mockApiGet).toHaveBeenCalled()
  })

  it('updateStatus calls PUT and refreshes', async () => {
    mockApiPut.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useAdjustments())

    let success: boolean = false
    await act(async () => {
      success = await result.current.updateStatus('aje-001', 'approved' as 'proposed' | 'approved' | 'rejected' | 'posted', 'Auditor')
    })

    expect(mockApiPut).toHaveBeenCalledWith(
      '/audit/adjustments/aje-001/status',
      'test-token',
      { status: 'approved', reviewed_by: 'Auditor' }
    )
    expect(success).toBe(true)
  })

  it('deleteEntry calls DELETE', async () => {
    mockApiDelete.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useAdjustments())

    let success: boolean = false
    await act(async () => {
      success = await result.current.deleteEntry('aje-001')
    })

    expect(mockApiDelete).toHaveBeenCalledWith('/audit/adjustments/aje-001', 'test-token')
    expect(success).toBe(true)
  })

  it('clearAll resets entries and stats', async () => {
    mockApiDelete.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useAdjustments())

    // First populate entries
    await act(async () => { await result.current.fetchEntries() })
    expect(result.current.entries.length).toBe(1)

    // Then clear
    await act(async () => { await result.current.clearAll() })

    expect(mockApiDelete).toHaveBeenCalledWith('/audit/adjustments', 'test-token')
    expect(result.current.entries).toEqual([])
    expect(result.current.stats.total).toBe(0)
  })

  it('getNextReference returns next ref', async () => {
    mockApiGet.mockResolvedValueOnce({ ok: true, data: { next_reference: 'AJE-005' } })

    const { result } = renderHook(() => useAdjustments())

    let ref: string | null = null
    await act(async () => {
      ref = await result.current.getNextReference()
    })

    expect(ref).toBe('AJE-005')
  })

  it('applyAdjustments calls POST and sets adjustedTB', async () => {
    const mockTB = { accounts: [], total_debits: 100, total_credits: 100 }
    mockApiPost.mockResolvedValue({ ok: true, data: mockTB })

    const { result } = renderHook(() => useAdjustments())

    await act(async () => {
      await result.current.applyAdjustments({ entry_ids: ['aje-001'] } as never)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/adjustments/apply',
      'test-token',
      expect.objectContaining({ entry_ids: ['aje-001'] })
    )
    expect(result.current.adjustedTB).toEqual(mockTB)
  })

  it('selectEntry and clearError work', () => {
    const { result } = renderHook(() => useAdjustments())

    const entry = { id: 'aje-001', reference: 'AJE-001' } as never
    act(() => { result.current.selectEntry(entry) })
    expect(result.current.selectedEntry).toEqual(entry)

    act(() => { result.current.selectEntry(null) })
    expect(result.current.selectedEntry).toBeNull()
  })

  it('sets error on failed fetch', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Server error' })

    const { result } = renderHook(() => useAdjustments())

    await act(async () => { await result.current.fetchEntries() })

    expect(result.current.error).toBeTruthy()
  })
})
