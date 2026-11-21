/**
 * Sprint 891 (CEO brief 16B): the pricing page's figures come from the plan file and are the
 * figures it showed before the move (the old literals, pinned here).
 */
import { comparisonRows, SEAT_CONFIGS, tiers, uploadsPerMonth, seatsLabel } from '@/domain/pricing'

it('seat configs are unchanged', () => {
  expect(SEAT_CONFIGS).toEqual([
    { label: 'Professional', baseSeats: 7, maxSeats: 20, seatMonthly: 65, seatAnnual: 650, baseMonthly: 500, baseAnnual: 5000 },
    { label: 'Enterprise', baseSeats: 20, maxSeats: 100, seatMonthly: 45, seatAnnual: 450, baseMonthly: 1000, baseAnnual: 10000 },
  ])
})

it('tier prices are unchanged', () => {
  expect(tiers.map(t => [t.name, t.monthlyPrice, t.annualPrice])).toEqual([
    ['Solo', 100, 1000],
    ['Professional', 500, 5000],
    ['Enterprise', 1000, 10000],
  ])
})

it('comparison rows are unchanged', () => {
  const row = (f: string) => comparisonRows.find(r => r.feature === f)!
  expect(row('Monthly uploads')).toMatchObject({ free: '10', solo: '100', professional: '500', enterprise: 'Unlimited' })
  expect(row('Clients')).toMatchObject({ free: '3', solo: 'Unlimited', professional: 'Unlimited', enterprise: 'Unlimited' })
  expect(row('Team Seats')).toMatchObject({ free: '1', solo: '1', professional: '7 (up to 20)', enterprise: '20 (up to 100)' })
  expect(row('Diagnostic Workspace')).toMatchObject({ free: false, solo: true, professional: true, enterprise: true })
  expect(row('Export Sharing')).toMatchObject({ free: false, solo: false, professional: true, enterprise: true })
  expect(row('Admin Dashboard')).toMatchObject({ free: false, solo: false, professional: true, enterprise: true })
  expect(row('Activity Logs')).toMatchObject({ free: false, solo: false, professional: true, enterprise: true })
  expect(row('Custom PDF Branding')).toMatchObject({ free: false, solo: false, professional: false, enterprise: true })
})

it('feature lines read as before', () => {
  expect(uploadsPerMonth('solo')).toBe('100')
  expect(seatsLabel('professional')).toBe('7 (up to 20)')
  const solo = tiers.find(t => t.name === 'Solo')!
  expect(solo.features.map(f => f.text)).toContain('100 uploads per month')
  const pro = tiers.find(t => t.name === 'Professional')!
  expect(pro.features.map(f => f.text)).toEqual(expect.arrayContaining(['500 uploads per month', '7 seats included (up to 20)']))
  expect(pro.priceSubtitle('annual')).toBe('per year, 7 seats included')
})
