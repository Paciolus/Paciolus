/**
 * BatchUploadPanel component tests
 *
 * Tests: rendering, title/description props, Zero-Storage notice,
 * and context provider wrapping.
 */
import { BatchUploadPanel } from '@/components/batch/BatchUploadPanel'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))

// Mock BatchUploadProvider and all child components
jest.mock('@/contexts/BatchUploadContext', () => ({
  BatchUploadProvider: ({ children }: any) => <div data-testid="batch-provider">{children}</div>,
}))

jest.mock('@/components/batch/BatchDropZone', () => ({
  BatchDropZone: () => <div data-testid="batch-drop-zone">DropZone</div>,
}))

jest.mock('@/components/batch/FileQueueList', () => ({
  FileQueueList: () => <div data-testid="file-queue-list">FileQueue</div>,
}))

jest.mock('@/components/batch/BatchProgressBar', () => ({
  BatchProgressBar: () => <div data-testid="batch-progress-bar">ProgressBar</div>,
}))

jest.mock('@/components/batch/BatchUploadControls', () => ({
  BatchUploadControls: () => <div data-testid="batch-upload-controls">Controls</div>,
}))


describe('BatchUploadPanel', () => {
  it('renders with default title and description', () => {
    render(<BatchUploadPanel />)
    expect(screen.getByText('Batch Upload')).toBeInTheDocument()
    expect(screen.getByText('Upload multiple trial balance files for batch processing.')).toBeInTheDocument()
  })

  it('renders with custom title and description', () => {
    render(<BatchUploadPanel title="Custom Title" description="Custom desc" />)
    expect(screen.getByText('Custom Title')).toBeInTheDocument()
    expect(screen.getByText('Custom desc')).toBeInTheDocument()
  })

  it('wraps content in BatchUploadProvider', () => {
    render(<BatchUploadPanel />)
    expect(screen.getByTestId('batch-provider')).toBeInTheDocument()
  })

  it('renders all child components', () => {
    render(<BatchUploadPanel />)
    expect(screen.getByTestId('batch-drop-zone')).toBeInTheDocument()
    expect(screen.getByTestId('file-queue-list')).toBeInTheDocument()
    expect(screen.getByTestId('batch-progress-bar')).toBeInTheDocument()
    expect(screen.getByTestId('batch-upload-controls')).toBeInTheDocument()
  })

  it('shows Zero-Storage notice', () => {
    render(<BatchUploadPanel />)
    expect(screen.getByText('Zero-Storage Processing')).toBeInTheDocument()
    expect(screen.getByText(/Files are processed in memory only/)).toBeInTheDocument()
  })
})
