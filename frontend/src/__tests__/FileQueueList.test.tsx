/**
 * FileQueueList component tests
 *
 * Tests: empty state, file list rendering, header with count,
 * summary footer, processing indicator.
 */
import { FileQueueList } from '@/components/batch/FileQueueList'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const mockUseBatchUpload = jest.fn()

jest.mock('@/hooks/useBatchUpload', () => ({
  useBatchUpload: () => mockUseBatchUpload(),
}))

jest.mock('@/components/batch/FileQueueItem', () => ({
  FileQueueItem: ({ file }: any) => <div data-testid={`file-${file.id}`}>{file.fileName}</div>,
}))

const baseStats = {
  totalFiles: 0,
  completedFiles: 0,
  failedFiles: 0,
  processingFiles: 0,
  readyFiles: 0,
  totalSizeFormatted: '0 B',
}

describe('FileQueueList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseBatchUpload.mockReturnValue({
      files: [],
      removeFile: jest.fn(),
      isProcessing: false,
      stats: baseStats,
    })
  })

  it('shows empty state when no files', () => {
    render(<FileQueueList />)
    expect(screen.getByText('No files in queue')).toBeInTheDocument()
    expect(screen.getByText('Drop files above or click to browse')).toBeInTheDocument()
  })

  it('shows File Queue header with file count', () => {
    mockUseBatchUpload.mockReturnValue({
      files: [
        { id: '1', fileName: 'test.csv', fileSize: 1000, mimeType: 'text/csv', status: 'ready', progress: 0, error: null, result: null, addedAt: new Date().toISOString() },
      ],
      removeFile: jest.fn(),
      isProcessing: false,
      stats: { ...baseStats, totalFiles: 1, readyFiles: 1 },
    })
    render(<FileQueueList />)
    expect(screen.getByText('File Queue')).toBeInTheDocument()
    expect(screen.getByText('(1 file)')).toBeInTheDocument()
  })

  it('shows plural text for multiple files', () => {
    mockUseBatchUpload.mockReturnValue({
      files: [
        { id: '1', fileName: 'a.csv', fileSize: 1000, mimeType: 'text/csv', status: 'ready', progress: 0, error: null, result: null, addedAt: new Date().toISOString() },
        { id: '2', fileName: 'b.csv', fileSize: 2000, mimeType: 'text/csv', status: 'ready', progress: 0, error: null, result: null, addedAt: new Date().toISOString() },
      ],
      removeFile: jest.fn(),
      isProcessing: false,
      stats: { ...baseStats, totalFiles: 2, readyFiles: 2, totalSizeFormatted: '3 KB' },
    })
    render(<FileQueueList />)
    expect(screen.getByText('(2 files)')).toBeInTheDocument()
  })

  it('shows total size in footer', () => {
    mockUseBatchUpload.mockReturnValue({
      files: [
        { id: '1', fileName: 'a.csv', fileSize: 1000, mimeType: 'text/csv', status: 'ready', progress: 0, error: null, result: null, addedAt: new Date().toISOString() },
      ],
      removeFile: jest.fn(),
      isProcessing: false,
      stats: { ...baseStats, totalFiles: 1, readyFiles: 1, totalSizeFormatted: '1 KB' },
    })
    render(<FileQueueList />)
    expect(screen.getByText('1 KB')).toBeInTheDocument()
  })

  it('shows processing indicator when processing', () => {
    mockUseBatchUpload.mockReturnValue({
      files: [
        { id: '1', fileName: 'a.csv', fileSize: 1000, mimeType: 'text/csv', status: 'processing', progress: 50, error: null, result: null, addedAt: new Date().toISOString() },
      ],
      removeFile: jest.fn(),
      isProcessing: true,
      stats: { ...baseStats, totalFiles: 1, processingFiles: 1, totalSizeFormatted: '1 KB' },
    })
    render(<FileQueueList />)
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })
})
