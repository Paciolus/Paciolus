/**
 * Sprint 688: useAccountRiskHeatmap hook tests.
 *
 * Pins the POST /audit/account-risk-heatmap contract and the CSV-export
 * side path (raw fetch → blob → anchor download).
 */
import { renderHook, act } from '@testing-library/react'
import { useAccountRiskHeatmap } from '@/hooks/useAccountRiskHeatmap'
import type {
  HeatmapRequest,
  HeatmapResponse,
} from '@/types/accountRiskHeatmap'

const mockApiPost = jest.fn()
const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ token: 'tok-heat' }),
}))

jest.mock('@/utils/apiClient', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

const sampleRequest: HeatmapRequest = {
  signals: [
    {
      account_number: '4000',
      account_name: 'Revenue',
      source: 'audit_engine',
      severity: 'high',
      issue: 'Rounding anomaly',
      materiality: '10000',
      confidence: 1,
    },
  ],
}

const sampleResponse: HeatmapResponse = {
  rows: [
    {
      account_number: '4000',
      account_name: 'Revenue',
      signal_count: 1,
      weighted_score: 5.0,
      sources: ['audit_engine'],
      severities: { high: 1 },
      issues: ['Rounding anomaly'],
      total_materiality: '10000',
      priority_tier: 'high',
      rank: 1,
    },
  ],
  total_accounts_with_signals: 1,
  high_priority_count: 1,
  moderate_priority_count: 0,
  low_priority_count: 0,
  total_signals: 1,
  sources_active: ['audit_engine'],
}

describe('useAccountRiskHeatmap', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('starts idle', () => {
    const { result } = renderHook(() => useAccountRiskHeatmap())
    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
    expect(result.current.exporting).toBe(false)
  })

  it('generate: success hydrates result', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: sampleResponse })
    const { result } = renderHook(() => useAccountRiskHeatmap())

    await act(async () => {
      await result.current.generate(sampleRequest)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/account-risk-heatmap',
      'tok-heat',
      sampleRequest,
    )
    expect(result.current.status).toBe('success')
    expect(result.current.result).toEqual(sampleResponse)
  })

  it('generate: error path surfaces error', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Rate limited' })
    const { result } = renderHook(() => useAccountRiskHeatmap())

    await act(async () => {
      await result.current.generate(sampleRequest)
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toBe('Rate limited')
  })

  it('downloadCsv: success delegates to apiDownload + downloadBlob and returns true', async () => {
    const blob = new Blob(['rank,account'], { type: 'text/csv' })
    mockApiDownload.mockResolvedValue({ ok: true, blob, filename: 'account_risk_heatmap.csv' })

    const { result } = renderHook(() => useAccountRiskHeatmap())

    let success = false
    await act(async () => {
      success = await result.current.downloadCsv(sampleRequest)
    })

    expect(success).toBe(true)
    expect(mockApiDownload).toHaveBeenCalledWith(
      '/audit/account-risk-heatmap/export.csv',
      'tok-heat',
      expect.objectContaining({ method: 'POST', body: sampleRequest }),
    )
    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'account_risk_heatmap.csv')
  })

  it('downloadCsv: failure returns false and surfaces error', async () => {
    mockApiDownload.mockResolvedValue({ ok: false, error: 'CSV export failed' })

    const { result } = renderHook(() => useAccountRiskHeatmap())

    let success = true
    await act(async () => {
      success = await result.current.downloadCsv(sampleRequest)
    })

    expect(success).toBe(false)
    expect(result.current.error).toBe('CSV export failed')
    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })

  it('reset clears state', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: sampleResponse })
    const { result } = renderHook(() => useAccountRiskHeatmap())

    await act(async () => {
      await result.current.generate(sampleRequest)
    })
    expect(result.current.status).toBe('success')

    act(() => {
      result.current.reset()
    })
    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
  })
})
