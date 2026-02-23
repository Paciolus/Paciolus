/**
 * PdfExtractionPreview component tests
 *
 * Tests: quality metrics rendering, remediation hints, proceed button state,
 * callbacks, sample data table, modal visibility.
 */
import userEvent from '@testing-library/user-event'
import { PdfExtractionPreview } from '@/components/shared/PdfExtractionPreview'
import type { PdfPreviewResult } from '@/types/pdf'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, custom, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


// ─── Fixtures ──────────────────────────────────────────────────────────────────

const highConfidenceResult: PdfPreviewResult = {
  filename: 'trial-balance-2025.pdf',
  page_count: 3,
  tables_found: 1,
  extraction_confidence: 0.85,
  header_confidence: 0.9,
  numeric_density: 0.7,
  row_consistency: 0.95,
  column_names: ['Account', 'Debit', 'Credit', 'Balance'],
  sample_rows: [
    { Account: '1000 Cash', Debit: '50,000.00', Credit: '10,000.00', Balance: '40,000.00' },
    { Account: '2000 AP', Debit: '3,000.00', Credit: '18,000.00', Balance: '(15,000.00)' },
  ],
  remediation_hints: [],
  passes_quality_gate: true,
}

const lowConfidenceResult: PdfPreviewResult = {
  filename: 'scanned-report.pdf',
  page_count: 5,
  tables_found: 1,
  extraction_confidence: 0.35,
  header_confidence: 0.3,
  numeric_density: 0.15,
  row_consistency: 0.6,
  column_names: ['Col A', 'Col B'],
  sample_rows: [
    { 'Col A': 'text', 'Col B': '123' },
  ],
  remediation_hints: [
    'Column headers could not be reliably detected. Export the data as CSV or Excel from your source system for best results.',
    'Very few numeric values were detected. The PDF may contain scanned images rather than extractable text.',
  ],
  passes_quality_gate: false,
}

const noTableResult: PdfPreviewResult = {
  filename: 'text-only.pdf',
  page_count: 1,
  tables_found: 0,
  extraction_confidence: 0.0,
  header_confidence: 0.0,
  numeric_density: 0.0,
  row_consistency: 0.0,
  column_names: [],
  sample_rows: [],
  remediation_hints: ['No tables were detected in the PDF.'],
  passes_quality_gate: false,
}

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onConfirm: jest.fn(),
  previewResult: highConfidenceResult,
}

describe('PdfExtractionPreview', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ─── Visibility ─────────────────────────────────────────────────────

  describe('visibility', () => {
    it('renders when isOpen is true', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText('PDF Extraction Preview')).toBeInTheDocument()
    })

    it('does not render when isOpen is false', () => {
      render(<PdfExtractionPreview {...defaultProps} isOpen={false} />)
      expect(screen.queryByText('PDF Extraction Preview')).not.toBeInTheDocument()
    })

    it('displays filename and page count', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText(/trial-balance-2025\.pdf/)).toBeInTheDocument()
      expect(screen.getByText(/3 pages/)).toBeInTheDocument()
    })
  })

  // ─── Quality Metrics ─────────────────────────────────────────────────

  describe('quality metrics', () => {
    it('displays extraction confidence percentage', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText(/85%/)).toBeInTheDocument()
    })

    it('displays confidence label for high confidence', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText(/High/)).toBeInTheDocument()
    })

    it('displays three metric bars', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText('Headers')).toBeInTheDocument()
      expect(screen.getByText('Numeric data')).toBeInTheDocument()
      expect(screen.getByText('Row consistency')).toBeInTheDocument()
    })

    it('displays individual metric percentages', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText('90%')).toBeInTheDocument()  // header_confidence
      expect(screen.getByText('70%')).toBeInTheDocument()  // numeric_density
      expect(screen.getByText('95%')).toBeInTheDocument()  // row_consistency
    })

    it('displays tables found count', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText(/1 table detected/)).toBeInTheDocument()
    })
  })

  // ─── Remediation Hints ─────────────────────────────────────────────────

  describe('remediation hints', () => {
    it('shows remediation hints when quality gate fails', () => {
      render(<PdfExtractionPreview {...defaultProps} previewResult={lowConfidenceResult} />)
      expect(screen.getByText('Quality below threshold')).toBeInTheDocument()
      expect(screen.getByText(/Column headers could not be reliably detected/)).toBeInTheDocument()
    })

    it('does not show remediation box when quality gate passes', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.queryByText('Quality below threshold')).not.toBeInTheDocument()
    })

    it('shows all remediation hints for low confidence', () => {
      render(<PdfExtractionPreview {...defaultProps} previewResult={lowConfidenceResult} />)
      expect(screen.getByText(/Column headers could not/)).toBeInTheDocument()
      expect(screen.getByText(/Very few numeric values/)).toBeInTheDocument()
    })
  })

  // ─── Proceed Button ─────────────────────────────────────────────────

  describe('proceed button', () => {
    it('is enabled when quality gate passes', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      const proceedBtn = screen.getByRole('button', { name: /proceed/i })
      expect(proceedBtn).not.toBeDisabled()
    })

    it('is disabled when quality gate fails', () => {
      render(<PdfExtractionPreview {...defaultProps} previewResult={lowConfidenceResult} />)
      const proceedBtn = screen.getByRole('button', { name: /proceed/i })
      expect(proceedBtn).toBeDisabled()
    })

    it('calls onConfirm when clicked', async () => {
      const user = userEvent.setup()
      render(<PdfExtractionPreview {...defaultProps} />)
      await user.click(screen.getByRole('button', { name: /proceed/i }))
      expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1)
    })

    it('does not call onConfirm when disabled', async () => {
      const user = userEvent.setup()
      render(<PdfExtractionPreview {...defaultProps} previewResult={lowConfidenceResult} />)
      await user.click(screen.getByRole('button', { name: /proceed/i }))
      expect(defaultProps.onConfirm).not.toHaveBeenCalled()
    })
  })

  // ─── Cancel Button ─────────────────────────────────────────────────

  describe('cancel button', () => {
    it('calls onClose when cancel is clicked', async () => {
      const user = userEvent.setup()
      render(<PdfExtractionPreview {...defaultProps} />)
      await user.click(screen.getByRole('button', { name: /cancel/i }))
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
    })
  })

  // ─── Sample Data Table ─────────────────────────────────────────────────

  describe('sample data table', () => {
    it('renders column headers', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText('Account')).toBeInTheDocument()
      expect(screen.getByText('Debit')).toBeInTheDocument()
      expect(screen.getByText('Credit')).toBeInTheDocument()
      expect(screen.getByText('Balance')).toBeInTheDocument()
    })

    it('renders sample rows', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText('1000 Cash')).toBeInTheDocument()
      expect(screen.getByText('50,000.00')).toBeInTheDocument()
      expect(screen.getByText('2000 AP')).toBeInTheDocument()
    })

    it('renders correct number of rows', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByText(/2 rows/)).toBeInTheDocument()
    })

    it('does not render table when no columns', () => {
      render(<PdfExtractionPreview {...defaultProps} previewResult={noTableResult} />)
      expect(screen.queryByText('Account')).not.toBeInTheDocument()
    })
  })

  // ─── Modal Accessibility ─────────────────────────────────────────────

  describe('accessibility', () => {
    it('has dialog role', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('has aria-modal attribute', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true')
    })

    it('has aria-labelledby pointing to title', () => {
      render(<PdfExtractionPreview {...defaultProps} />)
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-labelledby', 'pdf-preview-title')
      expect(document.getElementById('pdf-preview-title')).toHaveTextContent('PDF Extraction Preview')
    })
  })
})
