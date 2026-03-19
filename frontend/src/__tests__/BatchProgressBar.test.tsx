/**
 * BatchProgressBar component tests
 *
 * Tests: rendering, progress percentage, status label,
 * detail stats, empty state (no files), active state spinner.
 */
import { BatchProgressBar } from '@/components/batch/BatchProgressBar'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, style, children, ...rest }: any) =>
      <div {...rest} style={style}>{children}</div>,
  },
}))

const mockUseBatchUpload = jest.fn()

jest.mock('@/hooks/useBatchUpload', () => ({
  useBatchUpload: () => mockUseBatchUpload(),
}))

const baseHook = {
  status: 'idle' as string,
  overallProgress: 0,
  stats: {
    totalFiles: 0,
    completedFiles: 0,
    failedFiles: 0,
    processingFiles: 0,
    readyFiles: 0,
    totalSizeFormatted: '0 B',
  },
  getStatusLabel: (s: string) => s.charAt(0).toUpperCase() + s.slice(1),
}

describe('BatchProgressBar', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseBatchUpload.mockReturnValue({ ...baseHook })
  })

  it('renders nothing when no files', () => {
    const { container } = render(<BatchProgressBar />)
    expect(container.firstChild).toBeNull()
  })

  it('renders progress percentage when files exist', () => {
    mockUseBatchUpload.mockReturnValue({
      ...baseHook,
      status: 'processing',
      overallProgress: 45,
      stats: { ...baseHook.stats, totalFiles: 3, completedFiles: 1, processingFiles: 1, readyFiles: 1 },
    })
    render(<BatchProgressBar />)
    expect(screen.getByText('45%')).toBeInTheDocument()
  })

  it('shows status label', () => {
    mockUseBatchUpload.mockReturnValue({
      ...baseHook,
      status: 'completed',
      overallProgress: 100,
      stats: { ...baseHook.stats, totalFiles: 2, completedFiles: 2 },
    })
    render(<BatchProgressBar />)
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })

  it('shows completed file count in details', () => {
    mockUseBatchUpload.mockReturnValue({
      ...baseHook,
      status: 'completed',
      overallProgress: 100,
      stats: { ...baseHook.stats, totalFiles: 3, completedFiles: 3 },
    })
    render(<BatchProgressBar showDetails={true} />)
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('complete')).toBeInTheDocument()
  })

  it('shows failed file count when present', () => {
    mockUseBatchUpload.mockReturnValue({
      ...baseHook,
      status: 'partial',
      overallProgress: 66,
      stats: { ...baseHook.stats, totalFiles: 3, completedFiles: 2, failedFiles: 1 },
    })
    render(<BatchProgressBar />)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('failed')).toBeInTheDocument()
  })

  it('hides details when showDetails is false', () => {
    mockUseBatchUpload.mockReturnValue({
      ...baseHook,
      status: 'completed',
      overallProgress: 100,
      stats: { ...baseHook.stats, totalFiles: 2, completedFiles: 2 },
    })
    render(<BatchProgressBar showDetails={false} />)
    expect(screen.queryByText('complete')).not.toBeInTheDocument()
  })
})
