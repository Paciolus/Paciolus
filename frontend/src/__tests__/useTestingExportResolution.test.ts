/**
 * Sprint 405: useTestingExport — export resolution state machine tests
 *
 * Verifies lastExportSuccess sets on successful download and auto-clears after 1.5s.
 */
import { renderHook, act } from '@testing-library/react'
import { useTestingExport } from '@/hooks/useTestingExport'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token' })),
}))

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/utils', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))


describe('useTestingExport — resolution state', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['test']),
      filename: 'result.pdf',
    })
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('initializes with lastExportSuccess null', () => {
    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )
    expect(result.current.lastExportSuccess).toBeNull()
  })

  it('sets lastExportSuccess to pdf after successful memo export', async () => {
    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({ data: 'test' })
    })

    expect(result.current.lastExportSuccess).toBe('pdf')
  })

  it('sets lastExportSuccess to csv after successful CSV export', async () => {
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['csv']),
      filename: 'result.csv',
    })

    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportCSV({ data: 'test' })
    })

    expect(result.current.lastExportSuccess).toBe('csv')
  })

  it('auto-clears lastExportSuccess after 1.5s', async () => {
    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({ data: 'test' })
    })

    expect(result.current.lastExportSuccess).toBe('pdf')

    // Advance past the 1.5s timeout
    act(() => {
      jest.advanceTimersByTime(1500)
    })

    expect(result.current.lastExportSuccess).toBeNull()
  })

  it('does not set lastExportSuccess on failed download', async () => {
    mockApiDownload.mockResolvedValue({ ok: false, error: 'Server error' })

    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({})
    })

    expect(result.current.lastExportSuccess).toBeNull()
  })
})
