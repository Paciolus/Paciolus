/**
 * Pricing Page tests
 *
 * Validates tier card rendering, CTA links, comparison table structure,
 * FAQ content, plan estimator, and billing toggle after Enterprise tier removal.
 */
import React from 'react'
import PricingPage from '@/app/(marketing)/pricing/page'
import { render, screen, within, fireEvent } from '@/test-utils'

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

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

describe('PricingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ── Card rendering ────────────────────────────────

  it('renders 2 tier cards: Solo and Team', () => {
    render(<PricingPage />)
    const headings = screen.getAllByRole('heading', { level: 3 })
    const tierNames = headings.map(h => h.textContent)
    expect(tierNames).toContain('Solo')
    expect(tierNames).toContain('Team')
  })

  it('does NOT render a "Free" or "Enterprise" tier card', () => {
    render(<PricingPage />)
    const headings = screen.getAllByRole('heading', { level: 3 })
    const tierNames = headings.map(h => h.textContent)
    expect(tierNames).not.toContain('Free')
    expect(tierNames).not.toContain('Enterprise')
  })

  // ── Paid tier CTAs ────────────────────────────────

  it('Solo CTA links to /register?plan=solo&interval=monthly', () => {
    render(<PricingPage />)
    const soloLinks = screen.getAllByRole('link', { name: 'Start Free Trial' })
    const hrefs = soloLinks.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/register?plan=solo&interval=monthly')
  })

  it('Team CTA links to /register?plan=team&interval=monthly', () => {
    render(<PricingPage />)
    const teamLinks = screen.getAllByRole('link', { name: 'Start Free Trial' })
    const hrefs = teamLinks.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/register?plan=team&interval=monthly')
  })

  // ── "forever free" absent ─────────────────────────

  it('"forever free" does not appear anywhere on the page', () => {
    const { container } = render(<PricingPage />)
    expect(container.textContent).not.toMatch(/forever free/i)
  })

  // ── Comparison table ──────────────────────────────

  it('comparison table has correct 2-column headers (Solo, Team)', () => {
    render(<PricingPage />)
    const table = screen.getByRole('table')
    const headers = within(table).getAllByRole('columnheader')
    const headerTexts = headers.map(h => h.textContent)
    expect(headerTexts).toContain('Solo')
    expect(headerTexts).toContain('Team')
    expect(headerTexts).not.toContain('Free')
    expect(headerTexts).not.toContain('Enterprise')
  })

  // ── FAQ ───────────────────────────────────────────

  it('FAQ does not include "exceed the free tier limits" question', () => {
    const { container } = render(<PricingPage />)
    expect(container.textContent).not.toMatch(/exceed the free tier/i)
  })

  it('FAQ does not reference Enterprise', () => {
    const { container } = render(<PricingPage />)
    expect(container.textContent).not.toMatch(/enterprise/i)
  })

  // ── Plan estimator ────────────────────────────────

  it('plan estimator recommends Solo (not Free) for minimal inputs', () => {
    render(<PricingPage />)
    // Default inputs: uploads=1-5, tools=tb-only, teamSize=solo → should recommend Solo
    const recommendation = screen.getByText(/Based on your needs, we recommend/)
    expect(recommendation.textContent).toContain('Solo')
    expect(recommendation.textContent).not.toContain('Free')
  })

  // ── Billing toggle ────────────────────────────────

  it('billing toggle switches to annual prices', () => {
    render(<PricingPage />)
    const annualButton = screen.getByRole('button', { name: 'Annual' })
    fireEvent.click(annualButton)
    // Solo annual = $500
    expect(screen.getByText('$500')).toBeInTheDocument()
    // Team annual = $1,300
    expect(screen.getByText('$1,300')).toBeInTheDocument()
  })

  it('billing toggle switches back to monthly prices', () => {
    render(<PricingPage />)
    // Switch to annual first
    fireEvent.click(screen.getByRole('button', { name: 'Annual' }))
    // Switch back to monthly
    fireEvent.click(screen.getByRole('button', { name: 'Monthly' }))
    // Solo monthly = $50
    expect(screen.getByText('$50')).toBeInTheDocument()
    // Team monthly = $130
    expect(screen.getByText('$130')).toBeInTheDocument()
  })

  // ── Hero copy ─────────────────────────────────────

  it('hero subtitle describes the platform', () => {
    render(<PricingPage />)
    expect(
      screen.getByText('Twelve tools. Zero financial data stored. One platform. Pick the plan that matches your practice.')
    ).toBeInTheDocument()
  })

  it('hero trial line says "Every plan includes"', () => {
    render(<PricingPage />)
    expect(
      screen.getByText(/Every plan includes a 7-day free trial/)
    ).toBeInTheDocument()
  })
})
