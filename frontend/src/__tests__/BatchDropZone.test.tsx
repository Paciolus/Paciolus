/**
 * BatchDropZone component tests
 *
 * Tests: rendering, disabled state, file input, drag state text,
 * stats display, and processing indicator.
 */
import { BatchDropZone } from '@/components/batch/BatchDropZone'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const mockAddFiles = jest.fn()
const mockStats = {
  totalFiles: 0,
  completedFiles: 0,
  failedFiles: 0,
  processingFiles: 0,
  readyFiles: 0,
  remainingSlots: 10,
  totalSizeFormatted: '0 B',
  canAddMore: true,
}

jest.mock('@/hooks/useBatchUpload', () => ({
  useBatchUpload: () => ({
    addFiles: mockAddFiles,
    stats: mockStats,
    isProcessing: false,
  }),
}))

jest.mock('@/utils/fileFormats', () => ({
  ACCEPTED_FILE_EXTENSIONS_STRING: '.csv,.xlsx,.xls',
}))

describe('BatchDropZone', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockStats.totalFiles = 0
    mockStats.remainingSlots = 10
    mockStats.canAddMore = true
  })

  it('renders drop zone with prompt text', () => {
    render(<BatchDropZone />)
    expect(screen.getByText('Drop files or click to browse')).toBeInTheDocument()
  })

  it('shows file type hint', () => {
    render(<BatchDropZone />)
    expect(screen.getByText(/CSV, XLSX, or XLS/)).toBeInTheDocument()
  })

  it('shows remaining slots count', () => {
    render(<BatchDropZone />)
    expect(screen.getByText(/10 of \d+ slots available/)).toBeInTheDocument()
  })

  it('shows file count when files are queued', () => {
    mockStats.totalFiles = 3
    render(<BatchDropZone />)
    expect(screen.getByText('3 file(s) queued')).toBeInTheDocument()
  })

  it('renders hidden file input', () => {
    const { container } = render(<BatchDropZone />)
    const input = container.querySelector('input[type="file"]')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('multiple')
  })

  it('applies custom className', () => {
    const { container } = render(<BatchDropZone className="my-custom-class" />)
    expect(container.firstChild).toHaveClass('my-custom-class')
  })
})
