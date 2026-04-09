/**
 * ShareExportModal component tests
 *
 * Tests: closed state, open rendering, create share link,
 * cancel button, copy button, passcode input, single-use checkbox.
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

  it('shows plan-based expiration notice', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText(/expire based on your plan/)).toBeInTheDocument()
  })

  it('shows Create Share Link button initially', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByText('Create Share Link')).toBeInTheDocument()
  })

  it('calls onShare when Create Share Link is clicked', async () => {
    render(<ShareExportModal {...defaultProps} />)
    fireEvent.click(screen.getByText('Create Share Link'))
    await waitFor(() => {
      expect(defaultProps.onShare).toHaveBeenCalledWith('trial_balance', 'pdf', 'base64data', undefined)
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

  it('renders passcode input field', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByLabelText(/passcode/i)).toBeInTheDocument()
  })

  it('renders single-use checkbox', () => {
    render(<ShareExportModal {...defaultProps} />)
    expect(screen.getByLabelText(/single-use/i)).toBeInTheDocument()
  })

  it('passes passcode and singleUse options to onShare', async () => {
    render(<ShareExportModal {...defaultProps} />)

    // Set passcode
    const passcodeInput = screen.getByLabelText(/passcode/i)
    fireEvent.change(passcodeInput, { target: { value: 'test1234' } })

    // Check single-use
    const checkbox = screen.getByLabelText(/single-use/i)
    fireEvent.click(checkbox)

    fireEvent.click(screen.getByText('Create Share Link'))
    await waitFor(() => {
      expect(defaultProps.onShare).toHaveBeenCalledWith(
        'trial_balance',
        'pdf',
        'base64data',
        { passcode: 'test1234', singleUse: true },
      )
    })
  })

  it('disables create button when passcode is 1-3 chars', () => {
    render(<ShareExportModal {...defaultProps} />)
    const passcodeInput = screen.getByLabelText(/passcode/i)
    fireEvent.change(passcodeInput, { target: { value: 'ab' } })
    expect(screen.getByText('Create Share Link')).toBeDisabled()
  })

  it('shows passcode security note after creation', async () => {
    render(<ShareExportModal {...defaultProps} />)
    const passcodeInput = screen.getByLabelText(/passcode/i)
    fireEvent.change(passcodeInput, { target: { value: 'secret99' } })

    fireEvent.click(screen.getByText('Create Share Link'))
    await waitFor(() => {
      expect(screen.getByText(/share the passcode separately/i)).toBeInTheDocument()
    })
  })
})
