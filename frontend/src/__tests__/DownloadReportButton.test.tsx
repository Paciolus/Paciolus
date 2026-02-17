/**
 * Sprint 277: DownloadReportButton component tests
 *
 * Tests the export button used for PDF diagnostic summary downloads.
 * Covers: rendering, disabled state, download flow, error handling, loading state, zero-storage hint.
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any
            ) => R.createElement(tag, { ...rest, ref })
          ),
      }
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/utils/apiClient', () => ({
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

import { DownloadReportButton } from '@/components/export/DownloadReportButton'

const defaultProps = {
  auditResult: {
    status: 'complete',
    balanced: true,
    total_debits: 100000,
    total_credits: 100000,
    difference: 0,
  } as any,
  filename: 'Test_Report.pdf',
  token: 'test-token',
}

describe('DownloadReportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['pdf-data'], { type: 'application/pdf' }),
      filename: 'Report.pdf',
      error: null,
    })
  })

  it('renders "Export Diagnostic Summary" text', () => {
    render(<DownloadReportButton {...defaultProps} />)
    expect(screen.getByText('Export Diagnostic Summary')).toBeInTheDocument()
  })

  it('button is disabled when disabled prop is true', () => {
    render(<DownloadReportButton {...defaultProps} disabled={true} />)
    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
  })

  it('calls apiDownload on click', async () => {
    render(<DownloadReportButton {...defaultProps} />)

    const button = screen.getByRole('button')
    fireEvent.click(button)

    await waitFor(() => {
      expect(mockApiDownload).toHaveBeenCalledTimes(1)
      expect(mockApiDownload).toHaveBeenCalledWith(
        '/export/pdf',
        'test-token',
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('calls downloadBlob with blob and filename on success', async () => {
    const blob = new Blob(['pdf-content'], { type: 'application/pdf' })
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob,
      filename: 'Downloaded_Report.pdf',
      error: null,
    })

    render(<DownloadReportButton {...defaultProps} />)

    fireEvent.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'Downloaded_Report.pdf')
    })
  })

  it('shows error message on download failure', async () => {
    mockApiDownload.mockResolvedValue({
      ok: false,
      blob: null,
      filename: null,
      error: 'Server unavailable',
    })

    render(<DownloadReportButton {...defaultProps} />)

    fireEvent.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('Server unavailable')).toBeInTheDocument()
    })
  })

  it('shows "Generating Diagnostic Summary..." during loading', async () => {
    // Make apiDownload hang so we can observe the loading state
    let resolveDownload: (value: any) => void
    mockApiDownload.mockReturnValue(
      new Promise((resolve) => {
        resolveDownload = resolve
      })
    )

    render(<DownloadReportButton {...defaultProps} />)

    fireEvent.click(screen.getByRole('button'))

    await waitFor(() => {
      expect(screen.getByText('Generating Diagnostic Summary...')).toBeInTheDocument()
    })

    // Resolve so the test cleans up
    resolveDownload!({
      ok: true,
      blob: new Blob(),
      filename: 'Report.pdf',
      error: null,
    })

    await waitFor(() => {
      expect(screen.queryByText('Generating Diagnostic Summary...')).not.toBeInTheDocument()
    })
  })

  it('shows Zero-Storage hint when idle', () => {
    render(<DownloadReportButton {...defaultProps} />)
    expect(
      screen.getByText('Zero-Storage: Summary generated on-demand, never stored')
    ).toBeInTheDocument()
  })
})
