/**
 * Sprint 890 (CEO brief 15D): every converted figure is shown with its rate, the rate's date and
 * its source, under a label that says it is a convenience conversion.
 */
import { CurrencyConversionSection } from '@/components/trialBalance/CurrencyConversionSection'
import type { TBCurrencyConversion } from '@/types/diagnostic'
import { render, screen, within } from '@/test-utils'

const data: TBCurrencyConversion = {
  method: 'convenience_single_closing_rate',
  label: 'Convenience conversion: ... This is not translation under ASC 830 or IAS 21, ...',
  presentation_currency: 'USD',
  converted_count: 1,
  unconverted_count: 1,
  rows: [
    {
      account: 'Cash - Euro Account', currency: 'EUR', original_amount: 1000, converted_amount: 1100,
      rate: '1.10', rate_date: '2026-10-31', rate_source: 'Your rate table (uploaded 2026-11-01)', issue: null,
    },
    {
      account: 'Accounts Payable - UK', currency: 'GBP', original_amount: -500, converted_amount: null,
      rate: null, rate_date: null, rate_source: null, issue: 'missing_rate',
    },
  ],
}

it('shows the label and, beside each converted figure, its rate, date and source', () => {
  render(<CurrencyConversionSection data={data} />)
  expect(screen.getByText(/not translation under ASC 830 or IAS 21/)).toBeInTheDocument()
  const eurRow = screen.getByText('Cash - Euro Account').closest('tr') as HTMLElement
  expect(within(eurRow).getByText('1.10')).toBeInTheDocument()
  expect(within(eurRow).getByText('2026-10-31')).toBeInTheDocument()
  expect(within(eurRow).getByText('Your rate table (uploaded 2026-11-01)')).toBeInTheDocument()
  expect(within(eurRow).getByText('1,100.00')).toBeInTheDocument()
})

it('says why an account was not converted', () => {
  render(<CurrencyConversionSection data={data} />)
  const gbpRow = screen.getByText('Accounts Payable - UK').closest('tr') as HTMLElement
  expect(within(gbpRow).getByText('No rate for this currency in your table')).toBeInTheDocument()
})
