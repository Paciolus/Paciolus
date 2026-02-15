/**
 * FileDropZone component tests
 *
 * Tests drag-and-drop file upload zone used in 9 tool pages.
 * Covers: rendering states, drag events, click-to-upload, keyboard a11y, disabled state, file-selected feedback.
 */
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { FileDropZone } from '@/components/shared/FileDropZone'

const defaultProps = {
  label: 'Upload File',
  hint: 'Drag & drop your CSV or Excel file',
  file: null as File | null,
  onFileSelect: jest.fn(),
}

describe('FileDropZone', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders label and hint when no file selected', () => {
    render(<FileDropZone {...defaultProps} />)
    expect(screen.getByText('Upload File')).toBeInTheDocument()
    expect(screen.getByText('Drag & drop your CSV or Excel file')).toBeInTheDocument()
    expect(screen.getByText('CSV or Excel (.xlsx)')).toBeInTheDocument()
  })

  it('shows file name when file is selected', () => {
    const file = new File(['data'], 'trial_balance.csv', { type: 'text/csv' })
    render(<FileDropZone {...defaultProps} file={file} />)
    expect(screen.getByText('trial_balance.csv')).toBeInTheDocument()
    // Hint should NOT be visible when file is selected
    expect(screen.queryByText('Drag & drop your CSV or Excel file')).not.toBeInTheDocument()
  })

  it('has correct aria-label for accessibility', () => {
    render(<FileDropZone {...defaultProps} />)
    expect(screen.getByRole('button', { name: 'Upload File file upload' })).toBeInTheDocument()
  })

  it('calls onFileSelect when file is dropped', () => {
    const onFileSelect = jest.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} />)

    const dropZone = screen.getByRole('button', { name: 'Upload File file upload' })
    const file = new File(['data'], 'test.csv', { type: 'text/csv' })

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    })

    expect(onFileSelect).toHaveBeenCalledWith(file)
  })

  it('does not call onFileSelect on drop when disabled', () => {
    const onFileSelect = jest.fn()
    render(<FileDropZone {...defaultProps} onFileSelect={onFileSelect} disabled />)

    const dropZone = screen.getByRole('button', { name: 'Upload File file upload' })
    const file = new File(['data'], 'test.csv', { type: 'text/csv' })

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file] },
    })

    expect(onFileSelect).not.toHaveBeenCalled()
  })

  it('sets aria-disabled when disabled', () => {
    render(<FileDropZone {...defaultProps} disabled />)
    const dropZone = screen.getByRole('button', { name: 'Upload File file upload' })
    expect(dropZone).toHaveAttribute('aria-disabled', 'true')
    expect(dropZone).toHaveAttribute('tabindex', '-1')
  })

  it('is focusable when enabled (tabindex=0)', () => {
    render(<FileDropZone {...defaultProps} />)
    const dropZone = screen.getByRole('button', { name: 'Upload File file upload' })
    expect(dropZone).toHaveAttribute('tabindex', '0')
  })

  it('triggers file input on Enter key press', () => {
    // Mock document.createElement for input
    const mockClick = jest.fn()
    const originalCreateElement = document.createElement.bind(document)
    jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'input') {
        const input = originalCreateElement(tag)
        Object.defineProperty(input, 'click', { value: mockClick })
        return input
      }
      return originalCreateElement(tag)
    })

    render(<FileDropZone {...defaultProps} />)
    const dropZone = screen.getByRole('button', { name: 'Upload File file upload' })
    fireEvent.keyDown(dropZone, { key: 'Enter' })

    expect(mockClick).toHaveBeenCalled()
    jest.restoreAllMocks()
  })

  it('triggers file input on Space key press', () => {
    const mockClick = jest.fn()
    const originalCreateElement = document.createElement.bind(document)
    jest.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'input') {
        const input = originalCreateElement(tag)
        Object.defineProperty(input, 'click', { value: mockClick })
        return input
      }
      return originalCreateElement(tag)
    })

    render(<FileDropZone {...defaultProps} />)
    const dropZone = screen.getByRole('button', { name: 'Upload File file upload' })
    fireEvent.keyDown(dropZone, { key: ' ' })

    expect(mockClick).toHaveBeenCalled()
    jest.restoreAllMocks()
  })

  it('renders custom icon when provided', () => {
    render(
      <FileDropZone
        {...defaultProps}
        icon={<span data-testid="custom-icon">Custom</span>}
      />
    )
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })
})
