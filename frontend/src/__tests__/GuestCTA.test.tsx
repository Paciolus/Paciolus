/**
 * Sprint 277: GuestCTA component tests
 *
 * Tests the shared sign-in prompt displayed on tool pages for unauthenticated visitors.
 * Covers: heading, description, Sign In link, Create Account link.
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

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: any) => (
    <a href={href} {...rest}>
      {children}
    </a>
  )
})

import { GuestCTA } from '@/components/shared/GuestCTA'

describe('GuestCTA', () => {
  it('renders "Sign in to get started" heading', () => {
    render(<GuestCTA description="Upload your trial balance to begin." />)
    expect(
      screen.getByRole('heading', { name: 'Sign in to get started' })
    ).toBeInTheDocument()
  })

  it('renders description text', () => {
    render(<GuestCTA description="Upload your trial balance to begin." />)
    expect(
      screen.getByText('Upload your trial balance to begin.')
    ).toBeInTheDocument()
  })

  it('renders Sign In link pointing to /login', () => {
    render(<GuestCTA description="Test description" />)
    const signInLink = screen.getByRole('link', { name: 'Sign In' })
    expect(signInLink).toBeInTheDocument()
    expect(signInLink).toHaveAttribute('href', '/login')
  })

  it('renders Create Account link pointing to /register', () => {
    render(<GuestCTA description="Test description" />)
    const createLink = screen.getByRole('link', { name: 'Create Account' })
    expect(createLink).toBeInTheDocument()
    expect(createLink).toHaveAttribute('href', '/register')
  })
})
