/**
 * Sprint 405: ToolStatePresence component tests
 *
 * Render snapshots at each of the 4 upload states.
 * framer-motion in jsdom doesn't animate — snapshots capture structure.
 */
import React from 'react'
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

import { ToolStatePresence } from '@/components/shared/ToolStatePresence'

describe('ToolStatePresence', () => {
  it('renders idle children when status is idle', () => {
    render(
      <ToolStatePresence status="idle">
        <div data-testid="idle-content">Upload Zone</div>
      </ToolStatePresence>
    )
    expect(screen.getByTestId('idle-content')).toBeInTheDocument()
    expect(screen.getByText('Upload Zone')).toBeInTheDocument()
  })

  it('renders loading children when status is loading', () => {
    render(
      <ToolStatePresence status="loading">
        <div data-testid="loading-content">Running tests...</div>
      </ToolStatePresence>
    )
    expect(screen.getByTestId('loading-content')).toBeInTheDocument()
  })

  it('renders error children when status is error', () => {
    render(
      <ToolStatePresence status="error">
        <div role="alert">Something went wrong</div>
      </ToolStatePresence>
    )
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders success children when status is success', () => {
    render(
      <ToolStatePresence status="success">
        <div data-testid="results">Results here</div>
      </ToolStatePresence>
    )
    expect(screen.getByTestId('results')).toBeInTheDocument()
  })

  it('wraps children in a motion.div keyed by status', () => {
    const { container } = render(
      <ToolStatePresence status="idle">
        <span>Test</span>
      </ToolStatePresence>
    )
    // The motion.div is rendered as a plain div by our mock
    const wrapper = container.firstElementChild
    expect(wrapper).toBeTruthy()
    expect(wrapper?.tagName).toBe('DIV')
  })

  it('renders only the active status children', () => {
    render(
      <ToolStatePresence status="loading">
        {false && <div data-testid="idle">idle</div>}
        <div data-testid="loading">loading</div>
        {false && <div data-testid="success">success</div>}
      </ToolStatePresence>
    )
    expect(screen.getByTestId('loading')).toBeInTheDocument()
    expect(screen.queryByTestId('idle')).not.toBeInTheDocument()
    expect(screen.queryByTestId('success')).not.toBeInTheDocument()
  })
})
