/**
 * Sprint 277: useBatchUpload hook tests
 *
 * Tests the useBatchUpload hook that wraps BatchUploadContext
 * with computed stats, derived state, and helper functions.
 */
import { renderHook } from '@testing-library/react'

const mockContext = {
  files: [] as any[],
  status: 'idle' as const,
  totalFiles: 0,
  completedFiles: 0,
  failedFiles: 0,
  isProcessing: false,
  overallProgress: 0,
  addFiles: jest.fn(),
  removeFile: jest.fn(),
  clearQueue: jest.fn(),
  processAll: jest.fn(),
  processFile: jest.fn(),
  cancelProcessing: jest.fn(),
  retryFailed: jest.fn(),
  updateFileStatus: jest.fn(),
  updateFileProgress: jest.fn(),
}

jest.mock('@/contexts/BatchUploadContext', () => ({
  useBatchUploadContext: jest.fn(() => mockContext),
}))

jest.mock('@/types/batch', () => ({
  FILE_SIZE_LIMITS: { MAX_FILES: 10 },
  formatFileSize: jest.fn((s: number) => s + ' bytes'),
}))

import { useBatchUpload } from '@/hooks/useBatchUpload'

function makeFile(overrides: Record<string, unknown> = {}) {
  return {
    id: 'file-1',
    file: new File(['data'], 'test.csv', { type: 'text/csv' }),
    fileName: 'test.csv',
    fileSize: 1024,
    mimeType: 'text/csv',
    status: 'ready',
    progress: 0,
    addedAt: new Date(),
    ...overrides,
  }
}

describe('useBatchUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockContext.files = []
    mockContext.status = 'idle'
    mockContext.isProcessing = false
    mockContext.overallProgress = 0
  })

  it('initializes with empty state from context', () => {
    const { result } = renderHook(() => useBatchUpload())

    expect(result.current.files).toEqual([])
    expect(result.current.status).toBe('idle')
    expect(result.current.isProcessing).toBe(false)
    expect(result.current.stats.totalFiles).toBe(0)
  })

  it('computes stats correctly from file list', () => {
    mockContext.files = [
      makeFile({ id: 'f1', status: 'pending', fileSize: 100 }),
      makeFile({ id: 'f2', status: 'ready', fileSize: 200 }),
      makeFile({ id: 'f3', status: 'processing', fileSize: 300 }),
      makeFile({ id: 'f4', status: 'completed', fileSize: 400 }),
      makeFile({ id: 'f5', status: 'error', fileSize: 500 }),
      makeFile({ id: 'f6', status: 'cancelled', fileSize: 600 }),
    ]

    const { result } = renderHook(() => useBatchUpload())
    const { stats } = result.current

    expect(stats.totalFiles).toBe(6)
    expect(stats.pendingFiles).toBe(1)
    expect(stats.readyFiles).toBe(1)
    expect(stats.processingFiles).toBe(1)
    expect(stats.completedFiles).toBe(1)
    expect(stats.failedFiles).toBe(1)
    expect(stats.cancelledFiles).toBe(1)
    expect(stats.totalSize).toBe(2100)
    expect(stats.remainingSlots).toBe(4)
    expect(stats.canAddMore).toBe(true)
  })

  it('hasFiles is true when files exist', () => {
    mockContext.files = [makeFile()]

    const { result } = renderHook(() => useBatchUpload())
    expect(result.current.hasFiles).toBe(true)
  })

  it('isEmpty is true when no files', () => {
    mockContext.files = []

    const { result } = renderHook(() => useBatchUpload())
    expect(result.current.isEmpty).toBe(true)
    expect(result.current.hasFiles).toBe(false)
  })

  it('canProcess is true only when ready files exist and not processing', () => {
    mockContext.files = [makeFile({ status: 'ready' })]
    mockContext.isProcessing = false

    const { result: r1 } = renderHook(() => useBatchUpload())
    expect(r1.current.canProcess).toBe(true)

    // When processing, canProcess should be false
    mockContext.isProcessing = true
    const { result: r2 } = renderHook(() => useBatchUpload())
    expect(r2.current.canProcess).toBe(false)

    // When no ready files, canProcess should be false
    mockContext.isProcessing = false
    mockContext.files = [makeFile({ status: 'completed' })]
    const { result: r3 } = renderHook(() => useBatchUpload())
    expect(r3.current.canProcess).toBe(false)
  })

  it('hasReadyFiles reflects file statuses', () => {
    mockContext.files = [makeFile({ status: 'completed' })]
    const { result: r1 } = renderHook(() => useBatchUpload())
    expect(r1.current.hasReadyFiles).toBe(false)

    mockContext.files = [makeFile({ status: 'ready' })]
    const { result: r2 } = renderHook(() => useBatchUpload())
    expect(r2.current.hasReadyFiles).toBe(true)
  })

  it('hasFailedFiles reflects file statuses', () => {
    mockContext.files = [makeFile({ status: 'ready' })]
    const { result: r1 } = renderHook(() => useBatchUpload())
    expect(r1.current.hasFailedFiles).toBe(false)

    mockContext.files = [makeFile({ status: 'error' })]
    const { result: r2 } = renderHook(() => useBatchUpload())
    expect(r2.current.hasFailedFiles).toBe(true)
  })

  it('getFileById returns correct file', () => {
    const targetFile = makeFile({ id: 'target-id', fileName: 'target.csv' })
    mockContext.files = [
      makeFile({ id: 'other-id', fileName: 'other.csv' }),
      targetFile,
    ]

    const { result } = renderHook(() => useBatchUpload())
    const found = result.current.getFileById('target-id')
    expect(found).toBeDefined()
    expect(found?.fileName).toBe('target.csv')

    const notFound = result.current.getFileById('nonexistent')
    expect(notFound).toBeUndefined()
  })

  it('getFilesByStatus filters by status', () => {
    mockContext.files = [
      makeFile({ id: 'f1', status: 'ready' }),
      makeFile({ id: 'f2', status: 'error' }),
      makeFile({ id: 'f3', status: 'ready' }),
    ]

    const { result } = renderHook(() => useBatchUpload())
    const readyFiles = result.current.getFilesByStatus('ready')
    expect(readyFiles).toHaveLength(2)
    expect(readyFiles[0].id).toBe('f1')
    expect(readyFiles[1].id).toBe('f3')

    const errorFiles = result.current.getFilesByStatus('error')
    expect(errorFiles).toHaveLength(1)
  })

  it('getStatusLabel returns human-readable batch status labels', () => {
    const { result } = renderHook(() => useBatchUpload())

    expect(result.current.getStatusLabel('idle')).toBe('No files')
    expect(result.current.getStatusLabel('queued')).toBe('Ready to process')
    expect(result.current.getStatusLabel('validating')).toBe('Validating...')
    expect(result.current.getStatusLabel('processing')).toBe('Processing...')
    expect(result.current.getStatusLabel('completed')).toBe('All complete')
    expect(result.current.getStatusLabel('partial')).toBe('Partially complete')
    expect(result.current.getStatusLabel('failed')).toBe('All failed')
  })

  it('getFileStatusLabel returns human-readable file status labels', () => {
    const { result } = renderHook(() => useBatchUpload())

    expect(result.current.getFileStatusLabel('pending')).toBe('Pending')
    expect(result.current.getFileStatusLabel('validating')).toBe('Validating')
    expect(result.current.getFileStatusLabel('ready')).toBe('Ready')
    expect(result.current.getFileStatusLabel('processing')).toBe('Processing')
    expect(result.current.getFileStatusLabel('completed')).toBe('Complete')
    expect(result.current.getFileStatusLabel('error')).toBe('Error')
    expect(result.current.getFileStatusLabel('cancelled')).toBe('Cancelled')
  })
})
