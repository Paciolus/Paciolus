/**
 * Sprint 837: the results view shows the threshold notice, the payees below the
 * year's threshold, and the thresholds applied with their basis.
 */
import { Form1099Results } from '@/components/form1099/Form1099Results'
import type { Form1099Response } from '@/types/form1099'
import { render, screen } from '@/test-utils'

const base: Form1099Response = {
  tax_year: 2026,
  candidates: [],
  data_quality: [],
  w9_collection_list: [],
  summary: {},
}

describe('Form1099Results — Sprint 837 threshold transparency', () => {
  it('renders the notice, the below-threshold list and the thresholds applied', () => {
    render(
      <Form1099Results
        result={{
          ...base,
          notices: ['The inflation-adjusted threshold for 2027 is not in Paciolus.'],
          below_threshold_payees: [
            {
              vendor_id: 'V1',
              vendor_name: 'Acme Consulting',
              form_type: '1099-NEC',
              total: '1500.00',
              box_amounts: [],
              reason: 'Below the 2026 reporting threshold — not required, shown for review.',
            },
          ],
          thresholds: {
            tax_year: 2026,
            figures_from_tax_year: 2026,
            confirm_against: 'Confirm against the IRS Instructions for Forms 1099-MISC, 1099-NEC and 1099-INT for 2026.',
            items: [
              {
                form_type: '1099-NEC',
                box: 1,
                description: 'Nonemployee compensation',
                amount: '2000.00',
                basis: 'IRC §6041A; One Big Beautiful Bill Act (2025)',
                needs_confirmation: false,
              },
              {
                form_type: '1099-MISC',
                box: 10,
                description: 'Gross proceeds paid to an attorney',
                amount: '600.00',
                basis: 'IRC §6045(f)',
                needs_confirmation: true,
              },
            ],
          },
        }}
      />,
    )
    expect(screen.getByText(/not in Paciolus/)).toBeInTheDocument()
    expect(screen.getByText(/Below the 2026 Reporting Threshold/)).toBeInTheDocument()
    expect(screen.getByText('Acme Consulting')).toBeInTheDocument()
    expect(screen.getByText('Thresholds Applied')).toBeInTheDocument()
    expect(screen.getByText('Nonemployee compensation')).toBeInTheDocument()
    expect(screen.getByText('Confirm')).toBeInTheDocument()
  })

  it('omits the new sections for a response without them', () => {
    render(<Form1099Results result={base} />)
    expect(screen.queryByText('Thresholds Applied')).not.toBeInTheDocument()
    expect(screen.queryByText(/Reporting Threshold/)).not.toBeInTheDocument()
  })
})
