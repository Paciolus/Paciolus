/**
 * PeriodFileDropZone component tests
 *
 * Tests: idle state, file selected, loading, success, error,
 * disabled state, and drag-drop handling.
 */
import userEvent from '@testing-library/user-event'
import { PeriodFileDropZone, type PeriodState } from '@/components/multiPeriod/PeriodFileDropZone'
import { render, screen, fireEvent } from '@/test-utils'

const idlePeriod: PeriodState = { file: null, status: 'idle', result: null, error: null }
const loadingPeriod: PeriodState = { file: new File([''], 'tb.csv'), status: 'loading', result: null, error: null }
const successPeriod: PeriodState = { file: new File([''], 'tb-2024.csv'), status: 'success', result: {}, error: null }
const errorPeriod: PeriodState = { file: new File([''], 'bad.csv'), status: 'error', result: null, error: 'Invalid format' }
const fileSelectedPeriod: PeriodState = { file: new File([''], 'ready.csv'), status: 'idle', result: null, error: null }

const defaultProps = {
  label: 'Current Period',
  period: idlePeriod,
  onFileSelect: jest.fn(),
  disabled: false,
}

describe('PeriodFileDropZone', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ─── States ─────────────────────────────────────────────────────────

  it('shows idle state with upload instructions', () => {
    render(<PeriodFileDropZone {...defaultProps} />)
    expect(screen.getByText('Current Period')).toBeInTheDocument()
    expect(screen.getByText('Drop CSV or Excel file')).toBeInTheDocument()
    expect(screen.getByText('or click to browse')).toBeInTheDocument()
  })

  it('shows loading state with spinner', () => {
    render(<PeriodFileDropZone {...defaultProps} period={loadingPeriod} />)
    expect(screen.getByText('Auditing...')).toBeInTheDocument()
  })

  it('shows success state with filename', () => {
    render(<PeriodFileDropZone {...defaultProps} period={successPeriod} />)
    expect(screen.getByText('tb-2024.csv')).toBeInTheDocument()
    expect(screen.getByText('Audit complete')).toBeInTheDocument()
  })

  it('shows error state with message', () => {
    render(<PeriodFileDropZone {...defaultProps} period={errorPeriod} />)
    expect(screen.getByText('Invalid format')).toBeInTheDocument()
  })

  it('shows file selected state with "Ready to audit"', () => {
    render(<PeriodFileDropZone {...defaultProps} period={fileSelectedPeriod} />)
    expect(screen.getByText('ready.csv')).toBeInTheDocument()
    expect(screen.getByText('Ready to audit')).toBeInTheDocument()
  })

  // ─── Disabled ───────────────────────────────────────────────────────

  it('shows disabled styling when disabled', () => {
    const { container } = render(<PeriodFileDropZone {...defaultProps} disabled={true} />)
    const dropZone = container.querySelector('.opacity-50')
    expect(dropZone).toBeTruthy()
  })

  // ─── Drag and Drop ─────────────────────────────────────────────────

  it('calls onFileSelect when file is dropped', () => {
    const { container } = render(<PeriodFileDropZone {...defaultProps} />)
    const dropZone = container.querySelector('.border-dashed')!

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    })

    expect(defaultProps.onFileSelect).toHaveBeenCalledWith(file)
  })

  it('does not call onFileSelect when disabled and file is dropped', () => {
    const { container } = render(<PeriodFileDropZone {...defaultProps} disabled={true} />)
    const dropZone = container.querySelector('.border-dashed')!

    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    })

    expect(defaultProps.onFileSelect).not.toHaveBeenCalled()
  })
})
