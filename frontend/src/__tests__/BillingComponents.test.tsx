/**
 * Billing Component Tests — Phase LIX billing refresh.
 *
 * Tests PlanCard, CancelModal, UpgradeModal rendering by tier/status/interval,
 * trial messaging, cancel-at-period-end copy, and upgrade CTA destinations.
 */
import React from 'react'
import { CancelModal } from '@/components/billing/CancelModal'
import { PlanCard } from '@/components/billing/PlanCard'
import { UpgradeModal } from '@/components/billing/UpgradeModal'
import { render, screen, fireEvent } from '@/test-utils'

// ── Mocks ─────────────────────────────────────────────────────────

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

jest.mock('@/utils/themeUtils', () => ({
  MODAL_OVERLAY_VARIANTS: {},
  MODAL_CONTENT_VARIANTS: {},
}))

// ── PlanCard ──────────────────────────────────────────────────────

describe('PlanCard', () => {
  const futureDate = '2026-04-15T12:00:00Z'

  // ── Tier display names ──────────────────────────────────────

  it('renders "Free" for free tier', () => {
    render(
      <PlanCard tier="free" status="active" interval={null} periodEnd={null} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Free')
  })

  it('renders "Solo" for solo tier', () => {
    render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Solo')
  })

  it('renders "Team" for team tier', () => {
    render(
      <PlanCard tier="team" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Team')
  })

  it('renders "Solo" for deprecated professional tier', () => {
    render(
      <PlanCard tier="professional" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Solo')
  })

  // ── Status badges ───────────────────────────────────────────

  it('shows "Active" badge for active status', () => {
    render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('shows "Trialing" badge for trialing status', () => {
    render(
      <PlanCard tier="team" status="trialing" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Trialing')).toBeInTheDocument()
  })

  it('shows "Past Due" badge for past_due status', () => {
    render(
      <PlanCard tier="solo" status="past_due" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Past Due')).toBeInTheDocument()
  })

  it('shows "Canceled" badge for canceled status', () => {
    render(
      <PlanCard tier="solo" status="canceled" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Canceled')).toBeInTheDocument()
  })

  // ── Billing interval ───────────────────────────────────────

  it('shows "Billed monthly" for monthly interval', () => {
    render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Billed monthly')).toBeInTheDocument()
  })

  it('shows "Billed annually" for annual interval', () => {
    render(
      <PlanCard tier="team" status="active" interval="annual" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Billed annually')).toBeInTheDocument()
  })

  it('does not show billing interval for free tier', () => {
    render(
      <PlanCard tier="free" status="active" interval={null} periodEnd={null} cancelAtPeriodEnd={false} />
    )
    expect(screen.queryByText(/Billed/)).not.toBeInTheDocument()
  })

  // ── Trial messaging ────────────────────────────────────────

  it('shows trial conversion message when trialing', () => {
    render(
      <PlanCard tier="team" status="trialing" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText(/7-day free trial converts to a paid subscription/)).toBeInTheDocument()
    expect(screen.getByText('April 15, 2026')).toBeInTheDocument()
  })

  it('does not show trial conversion message when active', () => {
    render(
      <PlanCard tier="team" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.queryByText(/7-day free trial/)).not.toBeInTheDocument()
  })

  it('shows next billing date when active (not trialing)', () => {
    render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.getByText('Next billing date:')).toBeInTheDocument()
  })

  it('does not show next billing date when trialing (trial block replaces it)', () => {
    render(
      <PlanCard tier="team" status="trialing" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={false} />
    )
    expect(screen.queryByText('Next billing date:')).not.toBeInTheDocument()
  })

  // ── Cancel-at-period-end messaging ─────────────────────────

  it('shows cancel-at-period-end warning with date', () => {
    render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={true} />
    )
    expect(screen.getByText(/subscription will end on/)).toBeInTheDocument()
    expect(screen.getByText(/lose access to paid features/)).toBeInTheDocument()
  })

  it('does not contain "revert to the Free plan" in cancel warning', () => {
    const { container } = render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={true} />
    )
    expect(container.textContent).not.toMatch(/revert to the Free plan/i)
    expect(container.textContent).not.toMatch(/revert to Free/i)
  })

  it('does not show next billing date when cancel_at_period_end is true', () => {
    render(
      <PlanCard tier="solo" status="active" interval="monthly" periodEnd={futureDate} cancelAtPeriodEnd={true} />
    )
    expect(screen.queryByText('Next billing date:')).not.toBeInTheDocument()
  })
})

// ── CancelModal ───────────────────────────────────────────────────

describe('CancelModal', () => {
  const futureDate = '2026-04-15T12:00:00Z'
  const onConfirm = jest.fn().mockResolvedValue(true)
  const onClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    onConfirm.mockResolvedValue(true)
  })

  // ── Active subscription cancel ─────────────────────────────

  it('shows "Cancel Subscription" heading for active status', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Cancel Subscription')
  })

  it('shows period-end access message for active subscription', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByText(/continue to have access/)).toBeInTheDocument()
    expect(screen.getByText('April 15, 2026')).toBeInTheDocument()
  })

  it('does not contain "revert to the Free plan" messaging', () => {
    const { container } = render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(container.textContent).not.toMatch(/revert to the Free plan/i)
    expect(container.textContent).not.toMatch(/revert to Free/i)
  })

  it('shows "lose access to paid features" instead of Free revert', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByText(/lose access to paid features/)).toBeInTheDocument()
  })

  it('shows "Keep Plan" and "Cancel Subscription" buttons for active', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByRole('button', { name: 'Keep Plan' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel Subscription' })).toBeInTheDocument()
  })

  // ── Trial cancel ───────────────────────────────────────────

  it('shows "Cancel Trial" heading for trialing status', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="trialing" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Cancel Trial')
  })

  it('shows trial-specific copy mentioning no charge', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="trialing" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByText(/cancel your free trial/)).toBeInTheDocument()
    expect(screen.getByText(/will not be charged/)).toBeInTheDocument()
  })

  it('shows "No payment method will be charged" for trial cancel', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="trialing" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByText(/No payment method will be charged/)).toBeInTheDocument()
  })

  it('does not show period-end access block for trial cancel', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="trialing" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.queryByText(/continue to have access/)).not.toBeInTheDocument()
  })

  it('shows "Keep Trial" and "Cancel Trial" buttons for trialing', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="trialing" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(screen.getByRole('button', { name: 'Keep Trial' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel Trial' })).toBeInTheDocument()
  })

  // ── Interaction ────────────────────────────────────────────

  it('calls onConfirm when confirm button clicked', async () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel Subscription' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when keep button clicked', () => {
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Keep Plan' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('shows error when onConfirm returns false', async () => {
    onConfirm.mockResolvedValue(false)
    render(
      <CancelModal isOpen={true} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel Subscription' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/Failed to cancel/)
  })

  // ── Closed state ───────────────────────────────────────────

  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <CancelModal isOpen={false} periodEnd={futureDate} status="active" onConfirm={onConfirm} onClose={onClose} />
    )
    expect(container.textContent).toBe('')
  })
})

// ── UpgradeModal ──────────────────────────────────────────────────

describe('UpgradeModal', () => {
  const onClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ── Tier card rendering ────────────────────────────────────

  it('renders 2 tier cards: Solo, Team', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    const headings = screen.getAllByRole('heading', { level: 3 })
    const names = headings.map(h => h.textContent)
    expect(names).toContain('Solo')
    expect(names).toContain('Team')
  })

  it('shows "7-day free trial" feature for each tier', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    const trialItems = screen.getAllByText('7-day free trial')
    expect(trialItems).toHaveLength(2)
  })

  // ── CTA labels for free users (trial eligible) ─────────────

  it('shows "Start Free Trial" CTAs when current tier is free', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    const trialLinks = screen.getAllByRole('link', { name: 'Start Free Trial' })
    expect(trialLinks.length).toBe(2) // Solo, Team
  })

  // ── CTA labels for paid users (upgrade, not trial) ─────────

  it('shows "Upgrade" CTAs when current tier is solo', () => {
    render(<UpgradeModal currentTier="solo" isOpen={true} onClose={onClose} />)
    const upgradeLinks = screen.getAllByRole('link', { name: 'Upgrade' })
    expect(upgradeLinks.length).toBe(1) // Team
  })

  // ── CTA checkout destinations ──────────────────────────────

  it('Solo CTA links to /checkout?plan=solo&interval=monthly', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    const links = screen.getAllByRole('link', { name: 'Start Free Trial' })
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/checkout?plan=solo&interval=monthly')
  })

  it('Team CTA links to /checkout?plan=team&interval=monthly', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    const links = screen.getAllByRole('link', { name: 'Start Free Trial' })
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/checkout?plan=team&interval=monthly')
  })

  it('annual toggle changes CTA links to annual interval', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: /Annual/ }))
    const links = screen.getAllByRole('link', { name: 'Start Free Trial' })
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/checkout?plan=solo&interval=annual')
    expect(hrefs).toContain('/checkout?plan=team&interval=annual')
  })

  // ── Current plan badge ─────────────────────────────────────

  it('shows "Current" badge on current tier', () => {
    render(<UpgradeModal currentTier="solo" isOpen={true} onClose={onClose} />)
    expect(screen.getByText('Current')).toBeInTheDocument()
  })

  it('shows "Active" text on current tier card', () => {
    render(<UpgradeModal currentTier="solo" isOpen={true} onClose={onClose} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  // ── Downgrade prevention ───────────────────────────────────

  it('does not show upgrade link for downgrade tiers', () => {
    render(<UpgradeModal currentTier="team" isOpen={true} onClose={onClose} />)
    // Solo and Team (current) should not have upgrade links — no tiers above team
    expect(screen.queryAllByRole('link', { name: 'Upgrade' })).toHaveLength(0)
  })

  // ── Seat pricing visibility ────────────────────────────────

  it('shows seat pricing info for Team tier (monthly)', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    expect(screen.getAllByText(/\$80\/seat\/mo/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/\$70\/seat\/mo/).length).toBeGreaterThan(0)
  })

  it('shows seat pricing info for annual interval', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: /Annual/ }))
    expect(screen.getAllByText(/\$800\/seat\/yr/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/\$700\/seat\/yr/).length).toBeGreaterThan(0)
  })

  // ── Billing toggle pricing ─────────────────────────────────

  it('shows monthly prices by default', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    expect(screen.getByText('$50/mo')).toBeInTheDocument()
    expect(screen.getByText('$130/mo')).toBeInTheDocument()
  })

  it('shows annual prices after toggle', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    fireEvent.click(screen.getByRole('button', { name: /Annual/ }))
    expect(screen.getByText('$500/yr')).toBeInTheDocument()
    expect(screen.getByText('$1,300/yr')).toBeInTheDocument()
  })

  // ── Compare link ───────────────────────────────────────────

  it('has link to /pricing for plan comparison', () => {
    render(<UpgradeModal currentTier="free" isOpen={true} onClose={onClose} />)
    const compareLink = screen.getByRole('link', { name: /Compare all plans/ })
    expect(compareLink).toHaveAttribute('href', '/pricing')
  })

  // ── Closed state ───────────────────────────────────────────

  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <UpgradeModal currentTier="free" isOpen={false} onClose={onClose} />
    )
    expect(container.textContent).toBe('')
  })
})
