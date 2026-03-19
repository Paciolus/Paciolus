/**
 * FileQueueItem component tests
 *
 * Tests: rendering file info, status badges, remove button,
 * error display, progress bar, different file statuses.
 */
import { FileQueueItem } from '@/components/batch/FileQueueItem'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, style, children, ...rest }: any) =>
      <div {...rest} style={style}>{children}</div>,
  },
}))

jest.mock('@/utils/themeUtils', () => ({
  cx: (...args: any[]) => args.filter(Boolean).join(' '),
  getBadgeClasses: () => 'badge-class',
}))

const baseFile = {
  id: 'file-1',
  fileName: 'test-data.csv',
  fileSize: 1024000,
  mimeType: 'text/csv',
  status: 'ready' as const,
  progress: 0,
  error: null,
  result: null,
  addedAt: new Date().toISOString(),
  clientId: undefined,
}

describe('FileQueueItem', () => {
  const mockOnRemove = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders file name', () => {
    render(<FileQueueItem file={baseFile} index={0} onRemove={mockOnRemove} />)
    expect(screen.getByText('test-data.csv')).toBeInTheDocument()
  })

  it('renders Ready status badge', () => {
    render(<FileQueueItem file={baseFile} index={0} onRemove={mockOnRemove} />)
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('renders Complete status badge for completed files', () => {
    const completedFile = { ...baseFile, status: 'completed' as const }
    render(<FileQueueItem file={completedFile} index={0} onRemove={mockOnRemove} />)
    expect(screen.getByText('Complete')).toBeInTheDocument()
  })

  it('renders Error status badge for failed files', () => {
    const errorFile = {
      ...baseFile,
      status: 'error' as const,
      error: { message: 'Upload failed', details: 'Network error' },
    }
    render(<FileQueueItem file={errorFile} index={0} onRemove={mockOnRemove} />)
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Upload failed')).toBeInTheDocument()
  })

  it('calls onRemove when remove button is clicked', () => {
    render(<FileQueueItem file={baseFile} index={0} onRemove={mockOnRemove} />)
    const removeBtn = screen.getByRole('button', { name: 'Remove file' })
    fireEvent.click(removeBtn)
    expect(mockOnRemove).toHaveBeenCalledWith('file-1')
  })

  it('disables remove button when removeDisabled is true', () => {
    render(<FileQueueItem file={baseFile} index={0} onRemove={mockOnRemove} removeDisabled={true} />)
    const removeBtn = screen.getByRole('button', { name: /Cannot remove/ })
    expect(removeBtn).toBeDisabled()
  })

  it('shows row count when result has rowCount', () => {
    const fileWithResult = {
      ...baseFile,
      status: 'completed' as const,
      result: { rowCount: 1500, anomalyCount: 0 },
    }
    render(<FileQueueItem file={fileWithResult} index={0} onRemove={mockOnRemove} />)
    expect(screen.getByText('1,500 rows')).toBeInTheDocument()
  })

  it('shows anomaly count when present', () => {
    const fileWithAnomalies = {
      ...baseFile,
      status: 'completed' as const,
      result: { rowCount: 1000, anomalyCount: 5 },
    }
    render(<FileQueueItem file={fileWithAnomalies} index={0} onRemove={mockOnRemove} />)
    expect(screen.getByText('5 anomalies')).toBeInTheDocument()
  })
})
