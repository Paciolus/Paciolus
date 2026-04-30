/**
 * Sprint 750: useMultiPeriodMemoExport hook tests.
 *
 * Pins the apiDownload payload shape (lead-sheet stripping, default
 * "Not specified" fallback, blob filename) and the exporting state flag.
 */
import { act, renderHook } from '@testing-library/react'
import { useMultiPeriodMemoExport } from '@/hooks/useMultiPeriodMemoExport'

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/utils', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

const sampleComparison = {
  prior_label: 'FY24',
  current_label: 'FY25',
  budget_label: null,
  total_accounts: 120,
  movements_by_type: { increased: 30, decreased: 20 },
  movements_by_significance: { material: 5 },
  significant_movements: [],
  lead_sheet_summaries: [
    {
      lead_sheet: 'A',
      lead_sheet_name: 'Cash',
      account_count: 3,
      prior_total: 1000,
      current_total: 1200,
      net_change: 200,
      // extra fields the stripper drops:
      drilldown_url: '/d/A',
      detail_anomalies: [],
    },
  ],
  dormant_accounts: [{ account: 'X' }, { account: 'Y' }],
} as any

const baseMetadata = {
  clientName: 'Meridian',
  fiscalYearEnd: '2025-12-31',
  practitioner: 'Alice',
  reviewer: 'Bob',
}

describe('useMultiPeriodMemoExport', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('starts with exporting=false', () => {
    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    expect(result.current.exporting).toBe(false)
  })

  it('no-ops if token is null', async () => {
    const { result } = renderHook(() => useMultiPeriodMemoExport(null))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, baseMetadata)
    })
    expect(mockApiDownload).not.toHaveBeenCalled()
    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })

  it('strips extra lead-sheet fields and forwards the canonical payload', async () => {
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(),
      filename: 'MultiPeriod_Memo.pdf',
    })

    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, baseMetadata)
    })

    expect(mockApiDownload).toHaveBeenCalledTimes(1)
    const [endpoint, token, options] = mockApiDownload.mock.calls[0]
    expect(endpoint).toBe('/export/multi-period-memo')
    expect(token).toBe('test-token')
    expect(options.method).toBe('POST')
    expect(options.body.lead_sheet_summaries).toEqual([
      {
        lead_sheet: 'A',
        lead_sheet_name: 'Cash',
        account_count: 3,
        prior_total: 1000,
        current_total: 1200,
        net_change: 200,
      },
    ])
    expect(options.body.client_name).toBe('Meridian')
    expect(options.body.dormant_account_count).toBe(2)
  })

  it('falls back to "Not specified" when metadata fields are blank', async () => {
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(),
      filename: 'memo.pdf',
    })

    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, {
        clientName: '',
        fiscalYearEnd: '',
        practitioner: '',
        reviewer: '',
      })
    })

    const body = mockApiDownload.mock.calls[0][2].body
    expect(body.client_name).toBe('Not specified')
    expect(body.period_tested).toBe('Not specified')
    expect(body.prepared_by).toBe('Not specified')
    expect(body.reviewed_by).toBe('Not specified')
  })

  it('triggers downloadBlob with the server-provided filename when ok', async () => {
    const blob = new Blob(['memo'])
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob,
      filename: 'CustomName.pdf',
    })

    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, baseMetadata)
    })

    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'CustomName.pdf')
  })

  it('falls back to default filename when server omits it', async () => {
    mockApiDownload.mockResolvedValue({ ok: true, blob: new Blob() })

    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, baseMetadata)
    })

    expect(mockDownloadBlob).toHaveBeenCalledWith(expect.any(Blob), 'MultiPeriod_Memo.pdf')
  })

  it('skips downloadBlob when apiDownload returns ok=false', async () => {
    mockApiDownload.mockResolvedValue({ ok: false })

    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, baseMetadata)
    })

    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })

  it('resets exporting flag after a thrown error', async () => {
    mockApiDownload.mockRejectedValue(new Error('network'))

    const { result } = renderHook(() => useMultiPeriodMemoExport('test-token'))
    await act(async () => {
      await result.current.exportMemo(sampleComparison, baseMetadata)
    })

    expect(result.current.exporting).toBe(false)
    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })
})
