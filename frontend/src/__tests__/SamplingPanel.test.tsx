/**
 * SamplingPanel component tests
 *
 * Tests: 3-step wizard (configure → preview → results),
 * criteria selection, dual sampling modes, API calls,
 * strata display, error handling, and reset flow.
 */
import userEvent from '@testing-library/user-event'
import { SamplingPanel } from '@/components/jeTesting/SamplingPanel'
import type { SamplingPreview, SamplingResult } from '@/types/jeTesting'
import { render, screen, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const mockApiPost = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiPost: (...args: any[]) => mockApiPost(...args),
}))


// ─── Fixtures ──────────────────────────────────────────────────────────────────

const mockFile = new File(['test data'], 'journal-entries.csv', { type: 'text/csv' })

const mockPreview: SamplingPreview = {
  strata: [
    { name: 'Cash', criteria: 'account', population_size: 100 },
    { name: 'Revenue', criteria: 'account', population_size: 250 },
    { name: 'Expenses', criteria: 'account', population_size: 50 },
  ],
  total_population: 400,
  stratify_by: ['account'],
}

const mockResult: SamplingResult = {
  total_population: 400,
  total_sampled: 40,
  strata: [
    { name: 'Cash', criteria: 'account', population_size: 100, sample_size: 10, sampled_rows: [] },
    { name: 'Revenue', criteria: 'account', population_size: 250, sample_size: 25, sampled_rows: [] },
    { name: 'Expenses', criteria: 'account', population_size: 50, sample_size: 5, sampled_rows: [] },
  ],
  sampled_entries: [],
  sampling_seed: 'abc123def456ghi789jkl012mno345',
  parameters: {
    stratify_by: ['account'],
    sample_rate: 0.10,
    fixed_per_stratum: null,
  },
}

const defaultProps = {
  file: mockFile,
  token: 'test-token',
}

describe('SamplingPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, data: mockPreview })
  })

  // ─── Null State ─────────────────────────────────────────────────────

  it('returns null when no file is provided', () => {
    const { container } = render(<SamplingPanel file={null} token="test-token" />)
    expect(container.firstChild).toBeNull()
  })

  // ─── Step 1: Configure ──────────────────────────────────────────────

  it('shows configure step by default with header', () => {
    render(<SamplingPanel {...defaultProps} />)
    expect(screen.getByText('Stratified Sampling')).toBeInTheDocument()
    expect(screen.getByText('PCAOB AS 2315 / ISA 530 compliant')).toBeInTheDocument()
  })

  it('shows step indicators (1, 2, 3)', () => {
    render(<SamplingPanel {...defaultProps} />)
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows all 4 criteria buttons', () => {
    render(<SamplingPanel {...defaultProps} />)
    expect(screen.getByText('Account')).toBeInTheDocument()
    expect(screen.getByText('Amount Range')).toBeInTheDocument()
    expect(screen.getByText('Period')).toBeInTheDocument()
    expect(screen.getByText('User')).toBeInTheDocument()
  })

  it('has Account and Amount Range selected by default', () => {
    render(<SamplingPanel {...defaultProps} />)
    const accountBtn = screen.getByText('Account')
    const amountBtn = screen.getByText('Amount Range')
    // Selected criteria have sage styling
    expect(accountBtn.className).toContain('bg-sage')
    expect(amountBtn.className).toContain('bg-sage')
  })

  it('toggles criterion off when clicked', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByText('Account'))
    // After toggling off, Account should lose sage styling
    expect(screen.getByText('Account').className).not.toContain('bg-sage')
  })

  it('toggles criterion on when clicked', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByText('Period'))
    expect(screen.getByText('Period').className).toContain('bg-sage')
  })

  // ─── Sampling Mode ──────────────────────────────────────────────────

  it('shows Sample Rate mode selected by default', () => {
    render(<SamplingPanel {...defaultProps} />)
    const sampleRateRadio = screen.getByRole('radio', { name: /Sample Rate/i })
    expect(sampleRateRadio).toBeChecked()
  })

  it('switches to Fixed per Stratum mode', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    const fixedRadio = screen.getByRole('radio', { name: /Fixed per Stratum/i })
    await user.click(fixedRadio)
    expect(fixedRadio).toBeChecked()
  })

  // ─── Preview Button ─────────────────────────────────────────────────

  it('disables Preview Strata button when no criteria selected', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    // Deselect default criteria
    await user.click(screen.getByText('Account'))
    await user.click(screen.getByText('Amount Range'))

    const previewBtn = screen.getByRole('button', { name: 'Preview Strata' })
    expect(previewBtn).toBeDisabled()
  })

  it('shows Preview Strata button enabled by default', () => {
    render(<SamplingPanel {...defaultProps} />)
    const previewBtn = screen.getByRole('button', { name: 'Preview Strata' })
    expect(previewBtn).not.toBeDisabled()
  })

  // ─── Step 2: Preview ────────────────────────────────────────────────

  it('transitions to preview step after successful API call', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      expect(screen.getByText(/strata found across/)).toBeInTheDocument()
      expect(screen.getByText('Execute Sampling')).toBeInTheDocument()
    })
  })

  it('calls API with correct FormData for preview', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith(
        '/audit/journal-entries/sample/preview',
        'test-token',
        expect.any(FormData)
      )
    })
  })

  it('shows strata table in preview step', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      expect(screen.getByText('Cash')).toBeInTheDocument()
      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Expenses')).toBeInTheDocument()
    })
  })

  it('shows estimated sample sizes in preview', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      // With 10% sample rate: Cash=10, Revenue=25, Expenses=5
      expect(screen.getByText('Est. Sample')).toBeInTheDocument()
    })
  })

  it('shows Back button in preview step', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument()
    })
  })

  it('returns to configure step when Back is clicked', async () => {
    const user = userEvent.setup()
    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))
    await waitFor(() => {
      expect(screen.getByText('Back')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Back'))
    expect(screen.getByRole('button', { name: 'Preview Strata' })).toBeInTheDocument()
  })

  // ─── Step 3: Results ────────────────────────────────────────────────

  it('transitions to results step after Execute Sampling', async () => {
    const user = userEvent.setup()
    // First call returns preview, second returns result
    mockApiPost
      .mockResolvedValueOnce({ ok: true, data: mockPreview })
      .mockResolvedValueOnce({ ok: true, data: mockResult })

    render(<SamplingPanel {...defaultProps} />)

    // Step 1 → Step 2
    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))
    await waitFor(() => {
      expect(screen.getByText('Execute Sampling')).toBeInTheDocument()
    })

    // Step 2 → Step 3
    await user.click(screen.getByRole('button', { name: 'Execute Sampling' }))

    await waitFor(() => {
      // Results step shows "New Sample" button (unique to results step)
      expect(screen.getByText('New Sample')).toBeInTheDocument()
      // Shows the Rate column header (only in results table, not preview)
      expect(screen.getByText('Rate')).toBeInTheDocument()
    })
  })

  it('shows summary stats in results step', async () => {
    const user = userEvent.setup()
    mockApiPost
      .mockResolvedValueOnce({ ok: true, data: mockPreview })
      .mockResolvedValueOnce({ ok: true, data: mockResult })

    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))
    await waitFor(() => expect(screen.getByText('Execute Sampling')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Execute Sampling' }))

    await waitFor(() => {
      expect(screen.getByText('New Sample')).toBeInTheDocument()
      expect(screen.getByText('40')).toBeInTheDocument() // total_sampled
    })
  })

  it('shows sampling seed in results step', async () => {
    const user = userEvent.setup()
    mockApiPost
      .mockResolvedValueOnce({ ok: true, data: mockPreview })
      .mockResolvedValueOnce({ ok: true, data: mockResult })

    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))
    await waitFor(() => expect(screen.getByText('Execute Sampling')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Execute Sampling' }))

    await waitFor(() => {
      expect(screen.getByText('Sampling Seed')).toBeInTheDocument()
      expect(screen.getByText('abc123def456ghi7...')).toBeInTheDocument()
    })
  })

  it('resets to configure step when New Sample is clicked', async () => {
    const user = userEvent.setup()
    mockApiPost
      .mockResolvedValueOnce({ ok: true, data: mockPreview })
      .mockResolvedValueOnce({ ok: true, data: mockResult })

    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))
    await waitFor(() => expect(screen.getByText('Execute Sampling')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Execute Sampling' }))
    await waitFor(() => expect(screen.getByText('New Sample')).toBeInTheDocument())

    await user.click(screen.getByText('New Sample'))
    expect(screen.getByRole('button', { name: 'Preview Strata' })).toBeInTheDocument()
  })

  // ─── Error Handling ─────────────────────────────────────────────────

  it('shows error message when preview API fails', async () => {
    const user = userEvent.setup()
    mockApiPost.mockResolvedValue({ ok: false, error: 'File parsing failed' })

    render(<SamplingPanel {...defaultProps} />)
    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      expect(screen.getByText('File parsing failed')).toBeInTheDocument()
    })
  })

  it('shows error when API throws', async () => {
    const user = userEvent.setup()
    mockApiPost.mockRejectedValue(new Error('Network error'))

    render(<SamplingPanel {...defaultProps} />)
    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })

  // ─── Loading States ─────────────────────────────────────────────────

  it('shows loading text during preview', async () => {
    const user = userEvent.setup()
    mockApiPost.mockReturnValue(new Promise(() => {})) // never resolves

    render(<SamplingPanel {...defaultProps} />)
    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))

    expect(screen.getByText('Loading preview...')).toBeInTheDocument()
  })

  it('shows loading text during sampling execution', async () => {
    const user = userEvent.setup()
    mockApiPost
      .mockResolvedValueOnce({ ok: true, data: mockPreview })
      .mockReturnValueOnce(new Promise(() => {})) // never resolves

    render(<SamplingPanel {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Preview Strata' }))
    await waitFor(() => expect(screen.getByText('Execute Sampling')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: 'Execute Sampling' }))

    expect(screen.getByText('Running CSPRNG sampling...')).toBeInTheDocument()
  })
})
