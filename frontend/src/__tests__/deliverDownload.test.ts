/**
 * Sprint 893: exports that fail say so (apiDownload resolves ok: false; it does not throw).
 * Before, the trial balance, bank rec, workspace and convergence exports reset the button
 * and showed nothing.
 */
import { renderHook, act } from '@testing-library/react'
import { useTrialBalanceExports } from '@/hooks/useTrialBalanceExports'
import { deliverDownload } from '@/utils/deliverDownload'

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()
const mockToastError = jest.fn()

jest.mock('@/utils/apiClient', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
}))
jest.mock('@/utils', () => ({
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({ error: mockToastError, success: jest.fn(), info: jest.fn() }),
}))
jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: () => null,
}))

describe('deliverDownload', () => {
  beforeEach(() => jest.clearAllMocks())

  it('saves the file on success and shows no error', () => {
    const toast = { error: mockToastError }
    const blob = new Blob(['x'])
    expect(deliverDownload({ ok: true, blob, filename: 'a.pdf' }, 'fallback.pdf', 'PDF memo', toast)).toBe(true)
    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'a.pdf')
    expect(mockToastError).not.toHaveBeenCalled()
  })

  it('shows the server error when the request failed', () => {
    const toast = { error: mockToastError }
    expect(deliverDownload({ ok: false, error: 'Rate limit reached' }, 'f.csv', 'CSV export', toast)).toBe(false)
    expect(mockDownloadBlob).not.toHaveBeenCalled()
    expect(mockToastError).toHaveBeenCalledWith('Export failed', 'Rate limit reached')
  })

  it('says no file came back when ok but empty', () => {
    const toast = { error: mockToastError }
    deliverDownload({ ok: true }, 'f.csv', 'CSV export', toast)
    expect(mockToastError).toHaveBeenCalledWith(
      'Export failed',
      'The server returned no file for the CSV export. Please try again.',
    )
  })
})

describe('useTrialBalanceExports on failure', () => {
  beforeEach(() => jest.clearAllMocks())

  it('a failed preflight memo export shows an error instead of nothing', async () => {
    mockApiDownload.mockResolvedValue({ ok: false, error: 'Export failed on the server' })
    const { result } = renderHook(() =>
      useTrialBalanceExports({
        auditResult: null,
        preflightReport: { issues: [] } as never,
        selectedFile: null,
        token: 't',
      }),
    )
    await act(async () => {
      await result.current.handlePreflightExportPDF()
    })
    expect(mockDownloadBlob).not.toHaveBeenCalled()
    expect(mockToastError).toHaveBeenCalledWith('Export failed', 'Export failed on the server')
  })
})
