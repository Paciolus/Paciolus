/**
 * ExportOptionsPanel Component Tests
 * Sprint 55: Frontend Test Foundation
 *
 * Tests for the ExportOptionsPanel component that handles export functionality.
 */

import { render, screen } from '@/test-utils'
import { ExportOptionsPanel } from '@/components/export/ExportOptionsPanel'
import { sampleAuditResult } from '@/test-utils/fixtures'

describe('ExportOptionsPanel', () => {
  const defaultProps = {
    auditResult: sampleAuditResult,
    filename: 'test-file',
  }

  describe('rendering', () => {
    it('renders the panel header', () => {
      render(<ExportOptionsPanel {...defaultProps} />)
      expect(screen.getByText('Export Diagnostic')).toBeInTheDocument()
    })

    it('renders the subtitle', () => {
      render(<ExportOptionsPanel {...defaultProps} />)
      expect(screen.getByText('PDF, Excel, or CSV formats')).toBeInTheDocument()
    })
  })

  describe('expansion', () => {
    it('expands when header is clicked', async () => {
      const { user } = render(<ExportOptionsPanel {...defaultProps} />)

      // Initially, export buttons should not be visible
      expect(screen.queryByText('Export PDF')).not.toBeInTheDocument()

      // Click to expand
      const header = screen.getByText('Export Diagnostic')
      await user.click(header)

      // Now export buttons should be visible
      expect(screen.getByText('Export PDF')).toBeInTheDocument()
      expect(screen.getByText('Export Excel')).toBeInTheDocument()
    })

    it('shows workpaper fields when expanded', async () => {
      const { user } = render(<ExportOptionsPanel {...defaultProps} />)

      // Click to expand
      await user.click(screen.getByText('Export Diagnostic'))

      // Workpaper fields should be visible
      expect(screen.getByText('Prepared By')).toBeInTheDocument()
      expect(screen.getByText('Reviewed By')).toBeInTheDocument()
      expect(screen.getByText('Date')).toBeInTheDocument()
    })

    it('shows CSV export buttons when expanded', async () => {
      const { user } = render(<ExportOptionsPanel {...defaultProps} />)

      // Click to expand
      await user.click(screen.getByText('Export Diagnostic'))

      // CSV buttons should be visible
      expect(screen.getByText('CSV Trial Balance')).toBeInTheDocument()
      expect(screen.getByText('CSV Anomalies')).toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('disables the panel when disabled prop is true', () => {
      render(<ExportOptionsPanel {...defaultProps} disabled />)

      const header = screen.getByRole('button')
      expect(header).toBeDisabled()
    })
  })

  describe('workpaper fields', () => {
    it('allows entering prepared by name', async () => {
      const { user } = render(<ExportOptionsPanel {...defaultProps} />)

      // Expand the panel
      await user.click(screen.getByText('Export Diagnostic'))

      // Find and fill the Prepared By input
      const preparedByInput = screen.getByPlaceholderText('Your name')
      await user.type(preparedByInput, 'John Doe')

      expect(preparedByInput).toHaveValue('John Doe')
    })

    it('allows entering reviewed by name', async () => {
      const { user } = render(<ExportOptionsPanel {...defaultProps} />)

      // Expand the panel
      await user.click(screen.getByText('Export Diagnostic'))

      // Find and fill the Reviewed By input
      const reviewedByInput = screen.getByPlaceholderText('Reviewer name')
      await user.type(reviewedByInput, 'Jane Smith')

      expect(reviewedByInput).toHaveValue('Jane Smith')
    })
  })
})
