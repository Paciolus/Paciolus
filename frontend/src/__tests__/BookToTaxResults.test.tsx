/**
 * Sprint 889 (CEO brief 14F): a loss year is never shown as a complete provision.
 * The fixture is the engine's own output for a 100,000 book and tax loss at 21%
 * (backend book_to_tax_engine.calculate_book_to_tax(...).to_dict()).
 */
import { BookToTaxResults } from '@/components/bookToTax/BookToTaxResults'
import type { BookToTaxResponse } from '@/types/bookToTax'
import { render, screen } from '@/test-utils'
import lossResponse from './fixtures/book-to-tax-loss-response.json'

describe('BookToTaxResults — loss year', () => {
  it('labels the provision not complete and shows the NOL limitation', () => {
    render(<BookToTaxResults result={lossResponse as BookToTaxResponse} />)
    expect(screen.getByText('Tax Provision (not complete)')).toBeInTheDocument()
    expect(
      screen.getByText(/no net operating loss deferred tax asset or valuation allowance has been computed/),
    ).toBeInTheDocument()
    expect(screen.getByText(/no input for net operating loss carryforwards/)).toBeInTheDocument()
  })

  it('a profitable year keeps the plain heading and the standing scope note', () => {
    const profit: BookToTaxResponse = {
      ...(lossResponse as BookToTaxResponse),
      tax_provision: {
        ...(lossResponse as BookToTaxResponse).tax_provision,
        is_complete: true,
        limitations: [(lossResponse as BookToTaxResponse).tax_provision.limitations[1]],
      },
    }
    render(<BookToTaxResults result={profit} />)
    expect(screen.getByText('Tax Provision')).toBeInTheDocument()
    expect(screen.queryByText(/valuation allowance has been computed/)).not.toBeInTheDocument()
    expect(screen.getByText(/no input for net operating loss carryforwards/)).toBeInTheDocument()
  })
})
