'use client'

import { MarketingNav, MarketingFooter } from '@/components/marketing'

/**
 * Marketing Route Group Layout — shared nav + footer for all public pages.
 *
 * Wraps: homepage, about, approach, contact, pricing, privacy, terms, trust.
 * Route groups are URL-transparent — paths remain /about, /pricing, etc.
 *
 * Sprint 205: Phase XXVII — Marketing Route Group
 */
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="overflow-x-hidden">
      <MarketingNav />
      {children}
      <MarketingFooter />
    </div>
  )
}
