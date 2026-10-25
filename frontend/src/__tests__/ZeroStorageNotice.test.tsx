/**
 * Sprint 277: ZeroStorageNotice component tests
 *
 * Tests the shared zero-storage reassurance notice displayed below upload zones.
 * Covers: text content, lock icon SVG, custom className.
 */
import React from 'react'
import { ZeroStorageNotice } from '@/components/shared/ZeroStorageNotice'
import { render, screen } from '@/test-utils'


describe('ZeroStorageNotice', () => {
  it('says what happens to uploads and links to what is kept (Sprint 841)', () => {
    render(<ZeroStorageNotice />)
    expect(screen.getByText(/Your uploaded files are processed in memory and not kept after analysis\./)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'See exactly what we keep' })).toHaveAttribute('href', '/trust#transparency')
  })

  it('renders lock icon (svg element)', () => {
    const { container } = render(<ZeroStorageNotice />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
    expect(svg).toHaveClass('w-4', 'h-4')
  })

  it('applies custom className', () => {
    const { container } = render(<ZeroStorageNotice className="mt-4 opacity-75" />)
    // The className is applied to the outermost wrapper div
    const wrapper = container.firstElementChild
    expect(wrapper).toHaveClass('mt-4')
    expect(wrapper).toHaveClass('opacity-75')
  })
})
