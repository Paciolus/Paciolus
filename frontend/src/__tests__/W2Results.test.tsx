/**
 * Sprint 826 (W1/W2): the W-2 results view must show catch-up checks that
 * could not run — never a silent skip.
 */
import { W2Results } from '@/components/w2Reconciliation/W2Results'
import type { W2ReconciliationResponse } from '@/types/w2Reconciliation'
import { render, screen } from '@/test-utils'

const baseResult: W2ReconciliationResponse = {
  tax_year: 2026,
  employee_discrepancies: [],
  form_941_mismatches: [],
  w3_totals: {
    total_federal_wages: '0',
    total_federal_withholding: '0',
    total_ss_wages: '0',
    total_ss_tax_withheld: '0',
    total_medicare_wages: '0',
    total_medicare_tax_withheld: '0',
    employee_count: 0,
  },
  summary: {},
}

describe('W2Results — checks not run', () => {
  it('renders each check-not-run notice with its affected employees', () => {
    render(
      <W2Results
        result={{
          ...baseResult,
          checks_not_run: [
            {
              check: 'hsa_catchup_55',
              reason: 'limit_not_supplied',
              employee_ids: ['H1', 'H2'],
              message:
                'HSA age-55 catch-up check not run — the IRC §223(b)(3) limit for tax year 2026 was not supplied.',
            },
          ],
        }}
      />,
    )
    expect(screen.getByRole('status', { name: 'Checks not run' })).toBeInTheDocument()
    expect(screen.getByText(/HSA age-55 catch-up check not run/)).toBeInTheDocument()
    expect(screen.getByText('H1, H2')).toBeInTheDocument()
  })

  it('renders no notice section when every check ran', () => {
    render(<W2Results result={{ ...baseResult, checks_not_run: [] }} />)
    expect(screen.queryByRole('status', { name: 'Checks not run' })).not.toBeInTheDocument()
  })

  it('tolerates a response without the field', () => {
    render(<W2Results result={baseResult} />)
    expect(screen.queryByRole('status', { name: 'Checks not run' })).not.toBeInTheDocument()
  })
})

describe('W2Results — Sprint 846 W-3 and Form 941 tie-out', () => {
  it('says there is no W-3 instead of showing zero totals', () => {
    render(<W2Results result={{ ...baseResult, w3_totals: null, summary: { employee_count: 3 } }} />)
    expect(screen.getByText(/No draft W-2s supplied/)).toBeInTheDocument()
    expect(screen.queryByText('Federal wages')).not.toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('labels each 941 mismatch with what it was compared with', () => {
    render(
      <W2Results
        result={{
          ...baseResult,
          form_941_mismatches: [
            {
              quarter: null,
              compared_with: 'w3',
              kind: 'federal_wages',
              severity: 'high',
              expected: '90000.00',
              actual: '100000.00',
              difference: '10000.00',
              message: 'Sum of 4 quarters of Form 941 federal wages disagrees with the W-3 total of the draft W-2s.',
            },
          ],
        }}
      />,
    )
    expect(screen.getByText(/4-quarter total vs W-3/)).toBeInTheDocument()
  })

  it('omits the catch-up sentence when only a 941 check did not run', () => {
    render(
      <W2Results
        result={{
          ...baseResult,
          checks_not_run: [
            {
              check: 'form_941_annual_tieout',
              reason: 'form_941_quarters_incomplete',
              employee_ids: [],
              message: 'Form 941 annual tie-out not run — no Form 941 for Q4.',
            },
          ],
        }}
      />,
    )
    expect(screen.getByText(/no Form 941 for Q4/)).toBeInTheDocument()
    expect(screen.queryByText(/excess contributions/)).not.toBeInTheDocument()
  })
})
