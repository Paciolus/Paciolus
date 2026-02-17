/**
 * Sprint 277: ZeroStorageNotice component tests
 *
 * Tests the shared zero-storage reassurance notice displayed below upload zones.
 * Covers: text content, lock icon SVG, custom className.
 */
import React from 'react'
import { render, screen } from '@/test-utils'

import { ZeroStorageNotice } from '@/components/shared/ZeroStorageNotice'

describe('ZeroStorageNotice', () => {
  it('renders zero-storage text', () => {
    render(<ZeroStorageNotice />)
    expect(
      screen.getByText(
        'Zero-Storage: Your data is processed in-memory and never saved.'
      )
    ).toBeInTheDocument()
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
