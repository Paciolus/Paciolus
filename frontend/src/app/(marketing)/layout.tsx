'use client'

import { MarketingNav, MarketingFooter } from '@/components/marketing'
import { IntelligenceCanvas } from '@/components/shared'

/**
 * Marketing Route Group Layout — shared nav + footer for all public pages.
 *
 * Wraps: homepage, about, approach, contact, pricing, privacy, terms, trust.
 * Route groups are URL-transparent — paths remain /about, /pricing, etc.
 *
 * Sprint 205: Phase XXVII — Marketing Route Group
 * IntelligenceCanvas: Ambient particle background (marketing variant)
 */
export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <IntelligenceCanvas variant="marketing" />
      <MarketingNav />
      {children}
      <MarketingFooter />
    </>
  )
}
