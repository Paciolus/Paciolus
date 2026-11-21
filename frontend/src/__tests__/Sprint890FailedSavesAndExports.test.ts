/**
 * Sprint 890 (CEO brief 15A, review ST-08): a failed save or export is reported.
 *
 * apiPut and apiDownload resolve `{ ok: false }` on failure; they do not throw.
 * The preferences hook only reverted in a catch block and the export hook only
 * reported in one, so a failed save looked saved until reload and a failed
 * export just stopped its spinner.
 */
import { act, renderHook, waitFor } from '@testing-library/react'
import { useTestingExport } from '@/hooks/useTestingExport'
import { useUserPreferences } from '@/hooks/useUserPreferences'

const mockApiGet = jest.fn()
const mockApiPut = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
}))

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()
jest.mock('@/utils', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({ token: 'test-token' })),
}))

const mockToastError = jest.fn()
const mockToastSuccess = jest.fn()
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({ error: mockToastError, success: mockToastSuccess }),
}))

function deferred<T>() {
  let resolve!: (v: T) => void
  const promise = new Promise<T>(r => {
    resolve = r
  })
  return { promise, resolve }
}

beforeEach(() => {
  jest.clearAllMocks()
  mockApiGet.mockResolvedValue({ ok: true, status: 200, data: { favorite_tools: ['a'] } })
})

describe('useUserPreferences — resolved failures', () => {
  it('reverts and reports when the PUT resolves ok: false', async () => {
    mockApiPut.mockResolvedValue({ ok: false, status: 500, error: 'Server error' })
    const onError = jest.fn()
    const { result } = renderHook(() => useUserPreferences('tok', { onError }))
    await waitFor(() => expect(result.current.favorites).toEqual(['a']))

    await act(async () => {
      await result.current.toggleFavorite('b')
    })

    expect(result.current.favorites).toEqual(['a'])
    expect(onError).toHaveBeenCalledWith('Failed to save preferences')
  })

  it('an older failed save does not undo a newer change', async () => {
    const first = deferred<{ ok: boolean }>()
    const second = deferred<{ ok: boolean }>()
    mockApiPut.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise)
    const onError = jest.fn()
    const { result } = renderHook(() => useUserPreferences('tok', { onError }))
    await waitFor(() => expect(result.current.favorites).toEqual(['a']))

    let p1: Promise<void>, p2: Promise<void>
    act(() => {
      p1 = result.current.toggleFavorite('b')
    })
    act(() => {
      p2 = result.current.toggleFavorite('c')
    })
    expect(result.current.favorites).toEqual(['a', 'b', 'c'])
    expect(mockApiPut).toHaveBeenLastCalledWith('/settings/preferences', 'tok', { favorite_tools: ['a', 'b', 'c'] })

    await act(async () => {
      second.resolve({ ok: true })
      await p2!
    })
    await act(async () => {
      first.resolve({ ok: false })
      await p1!
    })

    expect(result.current.favorites).toEqual(['a', 'b', 'c'])
    expect(onError).not.toHaveBeenCalled()
  })

  it('a late preferences load does not overwrite a change made while it was in flight', async () => {
    const load = deferred<{ ok: boolean; status: number; data: { favorite_tools: string[] } }>()
    mockApiGet.mockReturnValue(load.promise)
    mockApiPut.mockResolvedValue({ ok: true })
    const { result } = renderHook(() => useUserPreferences('tok'))

    await act(async () => {
      await result.current.toggleFavorite('z')
    })
    const afterToggle = result.current.favorites
    expect(afterToggle).toContain('z')

    await act(async () => {
      load.resolve({ ok: true, status: 200, data: { favorite_tools: ['server'] } })
      await load.promise
    })
    expect(result.current.favorites).toEqual(afterToggle)
  })

  it('a new inline onError callback on each render does not refetch', async () => {
    const { rerender } = renderHook(() => useUserPreferences('tok', { onError: () => {} }))
    await waitFor(() => expect(mockApiGet).toHaveBeenCalledTimes(1))
    rerender()
    rerender()
    expect(mockApiGet).toHaveBeenCalledTimes(1)
  })
})

describe('useTestingExport — resolved failures', () => {
  it('reports a memo export that resolves ok: false', async () => {
    mockApiDownload.mockResolvedValue({ ok: false, error: 'Server error' })
    const { result } = renderHook(() => useTestingExport('/export/memo', '/export/csv'))
    await act(async () => {
      await result.current.handleExportMemo({})
    })
    expect(mockDownloadBlob).not.toHaveBeenCalled()
    expect(mockToastError).toHaveBeenCalledWith('Export failed', 'Server error')
    expect(result.current.exporting).toBeNull()
  })

  it('reports a CSV export that resolves ok: true without a file', async () => {
    mockApiDownload.mockResolvedValue({ ok: true, blob: undefined })
    const { result } = renderHook(() => useTestingExport('/export/memo', '/export/csv'))
    await act(async () => {
      await result.current.handleExportCSV({})
    })
    expect(mockDownloadBlob).not.toHaveBeenCalled()
    expect(mockToastError).toHaveBeenCalledWith('Export failed', expect.stringMatching(/no file/i))
  })
})
