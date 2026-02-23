/**
 * Sprint 277: SectionHeader component tests
 *
 * Tests the shared section header component used across analytics sections.
 * Covers: title, subtitle, icon, badge, className.
 */
import React from 'react'
import { SectionHeader } from '@/components/shared/SectionHeader'
import { render, screen } from '@/test-utils'

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


describe('SectionHeader', () => {
  it('renders title in heading', () => {
    render(<SectionHeader title="Key Metrics" />)
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Key Metrics')
  })

  it('renders subtitle when provided', () => {
    render(<SectionHeader title="Key Metrics" subtitle="Last 12 months" />)
    expect(screen.getByText('Last 12 months')).toBeInTheDocument()
  })

  it('renders icon when provided', () => {
    render(
      <SectionHeader
        title="Key Metrics"
        icon={<span data-testid="custom-icon">IC</span>}
      />
    )
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })

  it('renders badge when provided', () => {
    render(
      <SectionHeader
        title="Key Metrics"
        badge={<span data-testid="status-badge">Active</span>}
      />
    )
    expect(screen.getByTestId('status-badge')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('does not render subtitle when not provided', () => {
    const { container } = render(<SectionHeader title="Key Metrics" />)
    // subtitle is rendered in a <p> tag — should not exist
    const paragraphs = container.querySelectorAll('p')
    expect(paragraphs).toHaveLength(0)
  })

  it('applies className', () => {
    const { container } = render(
      <SectionHeader title="Key Metrics" className="extra-spacing" />
    )
    // The className is applied to the outermost flex div
    const headerDiv = container.querySelector('.extra-spacing')
    expect(headerDiv).toBeInTheDocument()
  })
})
