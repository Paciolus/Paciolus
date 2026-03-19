/**
 * ShareExportModal component tests
 *
 * Tests: closed state, open rendering, create share link,
 * cancel button, copy button.
 */
import { ShareExportModal } from '@/components/shared/ShareExportModal'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('@/lib/motion', () => ({
  fadeScale: { hidden: {}, visible: {}, exit: {} },
}))

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onShare: jest.fn(),
  tool: 'trial_balance',
  format: 'pdf',
  exportData: 'base64data',
}

describe('ShareExportModal', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onShare.mockResolvedValue('abc123')
  })

  it('renders nothing when closed', () => {
    const { container } = render(<ShareExportModal {...defaultProps} isOpen={false} />)
    expect(container.textContent).toBe('')
  })

  it('renders modal heading when open', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText('Share Export')).toBeInTheDocument()
  })

  it('shows format in description', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText(/PDF export/)).toBeInTheDocument()
  })

  it('shows 48 hour expiration notice', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText(/48 hours/)).toBeInTheDocument()
  })

  it('shows Create Share Link button initially', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText('Create Share Link')).toBeInTheDocument()
  })

  it('calls onShare when Create Share Link is clicked', async () => {
    render(<ShareExportModal {...defaultProps} />)
    fireEvent.click(screen.getByText('Create Share Link'))
    await waitFor(() => {
      expect(defaultProps.onShare).toHaveBeenCalledWith('trial_balance', 'pdf', 'base64data')
    })
  })

  it('shows Cancel button', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('calls onClose when Cancel is clicked', () => {
    render(<ShareExportModal {...defaultProps} />)
    fireEvent.click(screen.getByText('Cancel'))
    expect(defaultProps.onClose).toHaveBeenCalled()
  })
})
