/**
 * Sprint 277: CollapsibleSection component tests
 *
 * Tests the shared collapsible toggle component used across analytics sections.
 * Covers: rendering states, toggle behavior, item count, children visibility, className.
 */
import React from 'react'
import { render, screen, fireEvent } from '@/test-utils'

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

import { CollapsibleSection } from '@/components/shared/CollapsibleSection'

const defaultProps = {
  label: 'Advanced Metrics',
  isExpanded: false,
  onToggle: jest.fn(),
  children: <div data-testid="section-content">Collapsed content here</div>,
}

describe('CollapsibleSection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders toggle button with "Show" when collapsed', () => {
    render(<CollapsibleSection {...defaultProps} isExpanded={false} />)
    expect(screen.getByText(/Show Advanced Metrics/)).toBeInTheDocument()
    expect(screen.queryByText(/Hide Advanced Metrics/)).not.toBeInTheDocument()
  })

  it('renders toggle button with "Hide" when expanded', () => {
    render(<CollapsibleSection {...defaultProps} isExpanded={true} />)
    expect(screen.getByText(/Hide Advanced Metrics/)).toBeInTheDocument()
    expect(screen.queryByText(/Show Advanced Metrics/)).not.toBeInTheDocument()
  })

  it('shows item count when provided', () => {
    render(<CollapsibleSection {...defaultProps} itemCount={5} />)
    expect(screen.getByText('(5 available)')).toBeInTheDocument()
  })

  it('calls onToggle when button clicked', () => {
    const onToggle = jest.fn()
    render(<CollapsibleSection {...defaultProps} onToggle={onToggle} />)

    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('renders children when expanded', () => {
    render(<CollapsibleSection {...defaultProps} isExpanded={true} />)
    expect(screen.getByTestId('section-content')).toBeInTheDocument()
    expect(screen.getByText('Collapsed content here')).toBeInTheDocument()
  })

  it('does not render children when collapsed', () => {
    render(<CollapsibleSection {...defaultProps} isExpanded={false} />)
    expect(screen.queryByTestId('section-content')).not.toBeInTheDocument()
  })

  it('applies contentClassName when provided', () => {
    const { container } = render(
      <CollapsibleSection
        {...defaultProps}
        isExpanded={true}
        contentClassName="custom-class-name"
      />
    )
    // The contentClassName is applied to the inner div wrapping children
    const innerDiv = container.querySelector('.custom-class-name')
    expect(innerDiv).toBeInTheDocument()
  })
})
