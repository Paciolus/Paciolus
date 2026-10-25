/**
 * Pricing single source of truth — Sprint 818.
 *
 * The pricing page, checkout and the upgrade modal each re-declared prices,
 * seat counts and seat rates, and the copies had drifted (the pricing page's
 * "Most Popular" badge existed only in its own copy). They now read
 * `@/domain/pricing`. The Terms of Service tier table stays literal on purpose
 * — it is a versioned legal document, so a price change should be a
 * deliberate edit to it — and this test fails when the two disagree.
 */

import * as fs from 'fs'
import * as path from 'path'
import {
  SEAT_CONFIGS,
  baseSeats,
  getTier,
  maxAdditionalSeats,
  seatPriceDollars,
  tierPriceDollars,
  tiers,
} from '@/domain/pricing'

const SRC = path.resolve(__dirname, '..')
const read = (...parts: string[]) => fs.readFileSync(path.join(SRC, ...parts), 'utf-8')

describe('domain/pricing id-keyed lookups', () => {
  it('resolve every paid tier by backend id', () => {
    expect(tiers.map(t => t.internalId)).toEqual(['solo', 'professional', 'enterprise'])
    expect(getTier('professional')?.badge).toBeUndefined() // Sprint 842: no "Most Popular" claim
    expect(getTier('free')).toBeUndefined()
  })

  it('derive prices and seats from the tier and seat tables', () => {
    expect(tierPriceDollars('solo', 'monthly')).toBe(100)
    expect(tierPriceDollars('enterprise', 'annual')).toBe(10000)
    expect(baseSeats('solo')).toBe(1)
    expect(baseSeats('professional')).toBe(SEAT_CONFIGS[0]!.baseSeats)
    expect(maxAdditionalSeats('professional')).toBe(SEAT_CONFIGS[0]!.maxSeats - SEAT_CONFIGS[0]!.baseSeats)
    expect(maxAdditionalSeats('solo')).toBe(0)
    expect(seatPriceDollars('enterprise', 'annual')).toBe(SEAT_CONFIGS[1]!.seatAnnual)
    expect(seatPriceDollars('solo', 'monthly')).toBe(0)
  })
})

describe('no surface re-declares pricing', () => {
  it.each([
    ['app/(marketing)/pricing/page.tsx'],
    ['app/(auth)/checkout/page.tsx'],
    ['components/billing/UpgradeModal.tsx'],
  ])('%s holds no price, seat or tier literals', file => {
    const source = read(...file.split('/'))
    expect(source).not.toMatch(/monthlyPrice\s*:|seatMonthly\s*:|baseSeats\s*:/)
    for (const tier of tiers) {
      expect(source).not.toContain(`$${tier.monthlyPrice.toLocaleString()}/mo`)
      expect(source).not.toContain(`$${tier.annualPrice.toLocaleString()}/yr`)
    }
  })

  it('Terms of Service tier table matches the domain prices', () => {
    const terms = read('app', '(marketing)', 'terms', 'page.tsx')
    for (const tier of tiers) {
      expect(terms).toContain(
        `$${tier.monthlyPrice.toLocaleString('en-US')}/mo or $${tier.annualPrice.toLocaleString('en-US')}/yr`,
      )
    }
  })
})
