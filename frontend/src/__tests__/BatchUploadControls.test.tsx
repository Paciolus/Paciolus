/**
 * BatchUploadControls component tests
 *
 * Tests: rendering buttons based on state, process all, cancel,
 * retry failed, clear queue, empty state.
 */
import { BatchUploadControls } from '@/components/batch/BatchUploadControls'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    button: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <button {...rest}>{children}</button>,
  },
}))

const mockProcessAll = jest.fn().mockResolvedValue(undefined)
const mockClearQueue = jest.fn()
const mockCancelProcessing = jest.fn()
const mockRetryFailed = jest.fn().mockResolvedValue(undefined)

const mockUseBatchUpload = jest.fn()

jest.mock('@/hooks/useBatchUpload', () => ({
  useBatchUpload: () => mockUseBatchUpload(),
}))

describe('BatchUploadControls', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseBatchUpload.mockReturnValue({
      processAll: mockProcessAll,
      clearQueue: mockClearQueue,
      cancelProcessing: mockCancelProcessing,
      retryFailed: mockRetryFailed,
      canProcess: true,
      hasFailedFiles: false,
      hasFiles: true,
      isProcessing: false,
    })
  })

  it('renders nothing when no files', () => {
    mockUseBatchUpload.mockReturnValue({
      processAll: mockProcessAll,
      clearQueue: mockClearQueue,
      cancelProcessing: mockCancelProcessing,
      retryFailed: mockRetryFailed,
      canProcess: false,
      hasFailedFiles: false,
      hasFiles: false,
      isProcessing: false,
    })
    const { container } = render(<BatchUploadControls />)
    expect(container.firstChild).toBeNull()
  })

  it('shows Process All button when can process', () => {
    render(<BatchUploadControls />)
    expect(screen.getByText('Process All')).toBeInTheDocument()
  })

  it('shows Clear Queue button when not processing', () => {
    render(<BatchUploadControls />)
    expect(screen.getByText('Clear Queue')).toBeInTheDocument()
  })

  it('calls processAll when Process All is clicked', () => {
    render(<BatchUploadControls />)
    fireEvent.click(screen.getByText('Process All'))
    expect(mockProcessAll).toHaveBeenCalled()
  })

  it('calls clearQueue when Clear Queue is clicked', () => {
    render(<BatchUploadControls />)
    fireEvent.click(screen.getByText('Clear Queue'))
    expect(mockClearQueue).toHaveBeenCalled()
  })

  it('shows Cancel button during processing', () => {
    mockUseBatchUpload.mockReturnValue({
      processAll: mockProcessAll,
      clearQueue: mockClearQueue,
      cancelProcessing: mockCancelProcessing,
      retryFailed: mockRetryFailed,
      canProcess: false,
      hasFailedFiles: false,
      hasFiles: true,
      isProcessing: true,
    })
    render(<BatchUploadControls />)
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    expect(screen.queryByText('Process All')).not.toBeInTheDocument()
  })

  it('shows Retry Failed button when there are failed files', () => {
    mockUseBatchUpload.mockReturnValue({
      processAll: mockProcessAll,
      clearQueue: mockClearQueue,
      cancelProcessing: mockCancelProcessing,
      retryFailed: mockRetryFailed,
      canProcess: true,
      hasFailedFiles: true,
      hasFiles: true,
      isProcessing: false,
    })
    render(<BatchUploadControls />)
    expect(screen.getByText('Retry Failed')).toBeInTheDocument()
  })
})
