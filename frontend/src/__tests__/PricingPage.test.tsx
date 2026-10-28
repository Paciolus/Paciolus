/**
 * Pricing Page tests
 *
 * Validates tier card rendering, CTA links, comparison table structure,
 * FAQ content, plan estimator, and billing toggle for Solo/Professional/Enterprise.
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

  it('renders 3 tier cards: Solo, Professional, Enterprise', () => {
    render(<PricingPage />)
    const headings = screen.getAllByRole('heading', { level: 3 })
    const tierNames = headings.map(h => h.textContent)
    expect(tierNames).toContain('Solo')
    expect(tierNames).toContain('Professional')
    expect(tierNames).toContain('Enterprise')
  })

  it('does NOT render a "Free" or "Team" or "Organization" tier card', () => {
    render(<PricingPage />)
    const headings = screen.getAllByRole('heading', { level: 3 })
    const tierNames = headings.map(h => h.textContent)
    expect(tierNames).not.toContain('Free')
    expect(tierNames).not.toContain('Team')
    expect(tierNames).not.toContain('Organization')
  })

  // ── Enterprise card ───────────────────────────────

  it('Enterprise card shows $1,000 monthly price', () => {
    render(<PricingPage />)
    expect(screen.getByText('$1,000')).toBeInTheDocument()
  })

  // Sprint 858: Professional/Enterprise are sales-only while
  // SELF_SERVE_TEAM_TIERS_ENABLED is off — their cards say "Contact us".
  it('Enterprise card CTA is Contact us, not a self-serve sign-up', () => {
    render(<PricingPage />)
    const trialHrefs = screen.getAllByRole('link', { name: 'Start Free Trial' }).map(l => l.getAttribute('href'))
    expect(trialHrefs).not.toContain('/register?plan=enterprise&interval=monthly')
    const contactLinks = screen.getAllByRole('link', { name: 'Contact us' })
    expect(contactLinks.length).toBeGreaterThanOrEqual(2)
    contactLinks.forEach(l => expect(l).toHaveAttribute('href', '/contact?inquiry=Organization'))
  })

  // ── Paid tier CTAs ────────────────────────────────

  it('Solo CTA links to /register?plan=solo&interval=monthly', () => {
    render(<PricingPage />)
    const soloLinks = screen.getAllByRole('link', { name: 'Start Free Trial' })
    const hrefs = soloLinks.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/register?plan=solo&interval=monthly')
  })

  it('Professional CTA is Contact us; only Solo offers a self-serve trial', () => {
    render(<PricingPage />)
    const trialHrefs = screen.getAllByRole('link', { name: 'Start Free Trial' }).map(l => l.getAttribute('href'))
    expect(trialHrefs).not.toContain('/register?plan=professional&interval=monthly')
    expect(trialHrefs.filter(h => h?.startsWith('/register?plan='))).toEqual(['/register?plan=solo&interval=monthly'])
  })

  it('does not promise a free trial on every paid plan', () => {
    const { container } = render(<PricingPage />)
    expect(container.textContent).not.toMatch(/Every paid plan starts with/)
    expect(container.textContent).toMatch(/Solo starts with a 7-day free trial/)
  })

  // ── "forever free" absent ─────────────────────────

  it('"forever free" does not appear anywhere on the page', () => {
    const { container } = render(<PricingPage />)
    expect(container.textContent).not.toMatch(/forever free/i)
  })

  // ── Comparison table ──────────────────────────────

  it('comparison table has correct 5-column headers (Feature, Free, Solo, Professional, Enterprise)', () => {
    render(<PricingPage />)
    const table = screen.getByRole('table')
    const headers = within(table).getAllByRole('columnheader')
    const headerTexts = headers.map(h => h.textContent)
    expect(headerTexts).toContain('Solo')
    expect(headerTexts).toContain('Professional')
    expect(headerTexts).toContain('Enterprise')
    expect(headerTexts).not.toContain('Team')
    expect(headerTexts).not.toContain('Organization')
  })

  it('comparison table promises no unstaffed support tiers (Sprint 842)', () => {
    render(<PricingPage />)
    expect(screen.queryByText('Dedicated Account Manager')).not.toBeInTheDocument()
    expect(screen.queryByText(/Custom SLA/)).not.toBeInTheDocument()
  })

  // ── FAQ ───────────────────────────────────────────

  it('FAQ includes "What does Enterprise include beyond Professional?" question', () => {
    render(<PricingPage />)
    expect(
      screen.getByText('What does Enterprise include beyond Professional?')
    ).toBeInTheDocument()
  })

  it('FAQ does not include "exceed the free tier limits" question', () => {
    const { container } = render(<PricingPage />)
    expect(container.textContent).not.toMatch(/exceed the free tier/i)
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
    const annualButton = screen.getByRole('radio', { name: 'Annual' })
    fireEvent.click(annualButton)
    // Solo annual = $1,000
    expect(screen.getByText('$1,000')).toBeInTheDocument()
    // Professional annual = $5,000
    expect(screen.getByText('$5,000')).toBeInTheDocument()
    // Enterprise annual = $10,000
    expect(screen.getByText('$10,000')).toBeInTheDocument()
  })

  it('billing toggle switches back to monthly prices', () => {
    render(<PricingPage />)
    // Switch to annual first
    fireEvent.click(screen.getByRole('radio', { name: 'Annual' }))
    // Switch back to monthly
    fireEvent.click(screen.getByRole('radio', { name: 'Monthly' }))
    // Solo monthly = $100
    expect(screen.getByText('$100')).toBeInTheDocument()
    // Professional monthly = $500
    expect(screen.getByText('$500')).toBeInTheDocument()
    // Enterprise monthly = $1,000
    expect(screen.getByText('$1,000')).toBeInTheDocument()
  })

  // ── Hero copy ─────────────────────────────────────

  it('hero subtitle describes the platform', () => {
    render(<PricingPage />)
    expect(
      screen.getByText('Eighteen tools. Uploads not kept. One platform. Pick the plan that matches your practice.')
    ).toBeInTheDocument()
  })

  it('hero trial line discloses that a card is required (Sprint 842)', () => {
    render(<PricingPage />)
    expect(
      screen.getByText(/7-day free trial\. A card is required/)
    ).toBeInTheDocument()
  })
})
