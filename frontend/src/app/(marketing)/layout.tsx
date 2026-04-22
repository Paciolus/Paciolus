'use client'

import { MarketingNav, MarketingFooter } from '@/components/marketing'

/**
 * Marketing Route Group Layout — shared nav + footer for all public pages.
 *
 * Wraps: homepage, about, approach, contact, pricing, privacy, terms, trust.
 * Route groups are URL-transparent — paths remain /about, /pricing, etc.
 *
 * Sprint 703: the outer wrapper carries `.marketing-type`, which sets
 * `font-variant-numeric: oldstyle-nums proportional-nums` as the default
 * for marketing prose. Tables, `.font-mono` surfaces, and anything with a
 * `.tabular` / Tailwind `tabular-nums` class override back to tabular
 * lining figures — those overrides live in `globals.css`.
 *
 * Marketing Route Group
 */
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="marketing-type">
      <MarketingNav />
      {children}
      <MarketingFooter />
    </div>
  )
}
