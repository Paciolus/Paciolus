/**
 * Sprint 277: UploadHandlingNotice component tests
 *
 * Tests the shared zero-storage reassurance notice displayed below upload zones.
 * Covers: text content, lock icon SVG, custom className.
 */
import React from 'react'
import { UploadHandlingNotice } from '@/components/shared/UploadHandlingNotice'
import { render, screen } from '@/test-utils'


describe('UploadHandlingNotice', () => {
  it('says what happens to uploads and links to what is kept (Sprint 841)', () => {
    render(<UploadHandlingNotice />)
    expect(screen.getByText(/Your uploaded files are processed in memory and not kept after analysis\. We save your account, client list, analysis summaries and anything you enter in an engagement\./)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'See exactly what we keep' })).toHaveAttribute('href', '/trust#transparency')
  })

  it('renders lock icon (svg element)', () => {
    const { container } = render(<UploadHandlingNotice />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveClass('w-4', 'h-4')
  })

  it('applies custom className', () => {
    const { container } = render(<UploadHandlingNotice className="mt-4 opacity-75" />)
    // The className is applied to the outermost wrapper div
    const wrapper = container.firstElementChild
    expect(wrapper).toHaveClass('mt-4')
    expect(wrapper).toHaveClass('opacity-75')
  })
})
