/**
 * Sprint 235: useTestingExport hook tests
 */
import { renderHook, act } from '@testing-library/react'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token' })),
}))

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/utils', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

import { useTestingExport } from '@/hooks/useTestingExport'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock

describe('useTestingExport', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token' })
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['test']),
      filename: 'result.pdf',
    })
  })

  it('initializes with exporting null', () => {
    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )
    expect(result.current.exporting).toBeNull()
  })

  it('handleExportMemo downloads PDF', async () => {
    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({ data: 'test' })
    })

    expect(mockApiDownload).toHaveBeenCalledWith(
      '/export/memo',
      'test-token',
      expect.objectContaining({ method: 'POST' })
    )
    expect(mockDownloadBlob).toHaveBeenCalledWith(expect.any(Blob), 'result.pdf')
    expect(result.current.exporting).toBeNull() // Reset after download
  })

  it('handleExportCSV downloads CSV', async () => {
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['csv data']),
      filename: 'export.csv',
    })

    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportCSV({ data: 'test' })
    })

    expect(mockApiDownload).toHaveBeenCalledWith(
      '/export/csv',
      'test-token',
      expect.objectContaining({ method: 'POST' })
    )
    expect(mockDownloadBlob).toHaveBeenCalled()
  })

  it('uses fallback filenames when server does not provide one', async () => {
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['data']),
      filename: undefined,
    })

    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv', 'custom_memo.pdf', 'custom_flagged.csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({})
    })

    expect(mockDownloadBlob).toHaveBeenCalledWith(expect.any(Blob), 'custom_memo.pdf')
  })

  it('does nothing when no auth token', async () => {
    mockUseAuth.mockReturnValue({ token: null })

    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({})
    })

    expect(mockApiDownload).not.toHaveBeenCalled()
  })

  it('resets exporting state after error', async () => {
    mockApiDownload.mockResolvedValue({ ok: false, error: 'Server error' })

    const { result } = renderHook(() =>
      useTestingExport('/export/memo', '/export/csv')
    )

    await act(async () => {
      await result.current.handleExportMemo({})
    })

    expect(result.current.exporting).toBeNull()
    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })
})
