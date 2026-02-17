/**
 * Sprint 276: useMultiPeriodComparison hook tests
 */
import { renderHook, act } from '@testing-library/react'

const mockApiPost = jest.fn()
const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/utils', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

import { useMultiPeriodComparison } from '@/hooks/useMultiPeriodComparison'
import type { AuditResultForComparison } from '@/hooks/useMultiPeriodComparison'

const makePriorResult = (accounts: Array<{ account: string; debit: number; credit: number; type: string }>): AuditResultForComparison => ({
  lead_sheet_grouping: {
    summaries: [{ accounts }],
  },
})

const mockAccounts = [
  { account: 'Cash', debit: 10000, credit: 0, type: 'asset' },
  { account: 'Revenue', debit: 0, credit: 50000, type: 'revenue' },
]

const mockPriorResult = makePriorResult(mockAccounts)
const mockCurrentResult = makePriorResult(mockAccounts)

const mockComparisonResponse = {
  prior_label: 'FY2024',
  current_label: 'FY2025',
  total_accounts: 2,
  movements_by_type: {},
  movements_by_significance: {},
  all_movements: [],
  lead_sheet_summaries: [],
  significant_movements: [],
  new_accounts: [],
  closed_accounts: [],
  dormant_accounts: [],
  prior_total_debits: 10000,
  prior_total_credits: 50000,
  current_total_debits: 10000,
  current_total_credits: 50000,
}

describe('useMultiPeriodComparison', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('initializes with null comparison', () => {
    const { result } = renderHook(() => useMultiPeriodComparison())

    expect(result.current.comparison).toBeNull()
    expect(result.current.isComparing).toBe(false)
    expect(result.current.isExporting).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('compareResults extracts accounts and calls apiPost', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparisonResponse })

    const { result } = renderHook(() => useMultiPeriodComparison())

    let success: boolean = false
    await act(async () => {
      success = await result.current.compareResults(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    expect(success).toBe(true)
    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/compare-periods',
      'test-token',
      expect.objectContaining({
        prior_accounts: mockAccounts,
        current_accounts: mockAccounts,
        prior_label: 'FY2024',
        current_label: 'FY2025',
        materiality_threshold: 5000,
      })
    )
    expect(result.current.comparison).toEqual(mockComparisonResponse)
  })

  it('compareResults uses three-way endpoint when budget provided', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparisonResponse })

    const budgetResult = makePriorResult([
      { account: 'Cash', debit: 12000, credit: 0, type: 'asset' },
    ])

    const { result } = renderHook(() => useMultiPeriodComparison())

    await act(async () => {
      await result.current.compareResults(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token',
        budgetResult,
        'Budget 2025'
      )
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/compare-three-way',
      'test-token',
      expect.objectContaining({
        budget_accounts: [{ account: 'Cash', debit: 12000, credit: 0, type: 'asset' }],
        budget_label: 'Budget 2025',
      })
    )
  })

  it('compareResults injects engagement_id when provided', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparisonResponse })

    const { result } = renderHook(() => useMultiPeriodComparison(42))

    await act(async () => {
      await result.current.compareResults(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/compare-periods',
      'test-token',
      expect.objectContaining({
        engagement_id: 42,
      })
    )
  })

  it('compareResults returns false on empty accounts', async () => {
    const emptyResult: AuditResultForComparison = {
      lead_sheet_grouping: { summaries: [{ accounts: [] }] },
    }

    const { result } = renderHook(() => useMultiPeriodComparison())

    let success: boolean = true
    await act(async () => {
      success = await result.current.compareResults(
        emptyResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    expect(success).toBe(false)
    expect(mockApiPost).not.toHaveBeenCalled()
    expect(result.current.error).toBe('Could not extract account data from one or both audit results.')
  })

  it('compareResults handles API error', async () => {
    mockApiPost.mockResolvedValue({
      ok: false,
      error: 'Comparison failed',
      data: null,
    })

    const { result } = renderHook(() => useMultiPeriodComparison())

    let success: boolean = true
    await act(async () => {
      success = await result.current.compareResults(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    expect(success).toBe(false)
    expect(result.current.error).toBe('Comparison failed')
    expect(result.current.comparison).toBeNull()
  })

  it('exportCsv calls apiDownload and downloadBlob', async () => {
    const mockBlob = new Blob(['csv-data'], { type: 'text/csv' })
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: mockBlob,
      filename: 'Movement_Comparison.csv',
    })

    const { result } = renderHook(() => useMultiPeriodComparison())

    await act(async () => {
      await result.current.exportCsv(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    expect(mockApiDownload).toHaveBeenCalledWith(
      '/export/csv/movements',
      'test-token',
      expect.objectContaining({
        method: 'POST',
        body: expect.objectContaining({
          prior_accounts: mockAccounts,
          current_accounts: mockAccounts,
          prior_label: 'FY2024',
          current_label: 'FY2025',
          materiality_threshold: 5000,
        }),
      })
    )
    expect(mockDownloadBlob).toHaveBeenCalledWith(
      mockBlob,
      'Movement_Comparison.csv'
    )
  })

  it('exportCsv handles error', async () => {
    mockApiDownload.mockResolvedValue({
      ok: false,
      error: 'Export failed',
      blob: null,
    })

    const { result } = renderHook(() => useMultiPeriodComparison())

    await act(async () => {
      await result.current.exportCsv(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    expect(result.current.error).toBe('Export failed')
    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })

  it('clear resets comparison and error', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockComparisonResponse })

    const { result } = renderHook(() => useMultiPeriodComparison())

    // First populate data
    await act(async () => {
      await result.current.compareResults(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })
    expect(result.current.comparison).toBeDefined()

    // Clear
    act(() => { result.current.clear() })

    expect(result.current.comparison).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('isComparing/isExporting reflect loading states', async () => {
    // Create a deferred promise so we can observe isComparing=true
    let resolvePost: ((value: unknown) => void) | undefined
    mockApiPost.mockReturnValue(new Promise((resolve) => { resolvePost = resolve }))

    const { result } = renderHook(() => useMultiPeriodComparison())

    // Start comparison (do not await)
    let comparePromise: Promise<boolean>
    act(() => {
      comparePromise = result.current.compareResults(
        mockPriorResult,
        mockCurrentResult,
        'FY2024',
        'FY2025',
        5000,
        'test-token'
      )
    })

    // isComparing should be true while awaiting
    expect(result.current.isComparing).toBe(true)

    // Resolve the API call
    await act(async () => {
      resolvePost!({ ok: true, data: mockComparisonResponse })
      await comparePromise!
    })

    expect(result.current.isComparing).toBe(false)
  })
})
