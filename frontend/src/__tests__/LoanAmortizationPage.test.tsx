/**
 * Sprint 625: Loan Amortization page tests.
 */
import LoanAmortizationPage from '@/app/tools/loan-amortization/page'
import { apiPost } from '@/utils/apiClient'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'solo' },
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
    token: 'test-token',
  })),
}))

const mockApiDownload = jest.fn()
const mockDownloadBlob = jest.fn()

jest.mock('@/utils/apiClient', () => ({
  apiPost: jest.fn(),
  apiDownload: (...args: unknown[]) => mockApiDownload(...args),
  downloadBlob: (...args: unknown[]) => mockDownloadBlob(...args),
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>

const sampleResponse = {
  schedule: [
    {
      period_number: 1,
      payment_date: '2026-01-01',
      beginning_balance: '200000',
      scheduled_payment: '1200',
      interest: '1000',
      principal: '200',
      extra_principal: '0.00',
      ending_balance: '199800',
    },
    {
      period_number: 2,
      payment_date: '2026-02-01',
      beginning_balance: '199800',
      scheduled_payment: '1200',
      interest: '999',
      principal: '201',
      extra_principal: '500.00',
      ending_balance: '199099',
    },
  ],
  annual_summary: [
    {
      year_index: 1,
      calendar_year: 2026,
      total_payments: '14400',
      total_interest: '11988',
      total_principal: '2412',
      ending_balance: '197588',
    },
  ],
  inputs: {},
  total_interest: '231000',
  total_payments: '431000',
  payoff_date: '2056-01-01',
  journal_entry_templates: [
    {
      description: 'Periodic payment',
      debits: [
        { account: 'Interest Expense', amount: '1000' },
        { account: 'Notes Payable', amount: '200' },
      ],
      credits: [{ account: 'Cash', amount: '1200' }],
    },
  ],
}

describe('LoanAmortizationPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, status: 200, data: sampleResponse })
  })

  it('renders hero header with default form values', () => {
    render(<LoanAmortizationPage />)
    expect(screen.getByText('Loan Amortization')).toBeInTheDocument()
    expect(screen.getByDisplayValue('200000')).toBeInTheDocument()
    expect(screen.getByDisplayValue('6.0')).toBeInTheDocument()
    expect(screen.getByDisplayValue('360')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Generate Schedule/i })).toBeInTheDocument()
  })

  it('shows the balloon amount field only when balloon method is selected', () => {
    render(<LoanAmortizationPage />)
    expect(screen.queryByText('Balloon Amount ($)')).not.toBeInTheDocument()

    const methodSelect = screen.getByDisplayValue('Standard (level payment)') as HTMLSelectElement
    fireEvent.change(methodSelect, { target: { value: 'balloon' } })

    expect(screen.getByText('Balloon Amount ($)')).toBeInTheDocument()
  })

  it('submits with the correct payload and converts annual rate to decimal string', async () => {
    render(<LoanAmortizationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Generate Schedule/i }))

    await waitFor(() => expect(mockApiPost).toHaveBeenCalled())
    const [endpoint, token, payload] = mockApiPost.mock.calls[0]
    expect(endpoint).toBe('/audit/loan-amortization')
    expect(token).toBe('test-token')
    expect(payload).toMatchObject({
      principal: '200000',
      annual_rate: '0.06',
      term_periods: 360,
      frequency: 'monthly',
      method: 'standard',
      extra_payments: [],
    })
  })

  it('includes an extra-payment entry when both period and amount are provided', async () => {
    render(<LoanAmortizationPage />)
    const periodInputs = screen.getAllByPlaceholderText(/e\.g\./i)
    const [periodInput, amountInput] = periodInputs
    fireEvent.change(periodInput, { target: { value: '12' } })
    fireEvent.change(amountInput, { target: { value: '5000' } })

    fireEvent.click(screen.getByRole('button', { name: /Generate Schedule/i }))
    await waitFor(() => expect(mockApiPost).toHaveBeenCalled())
    const [, , payload] = mockApiPost.mock.calls[0]
    expect(payload).toMatchObject({
      extra_payments: [{ period_number: 12, amount: '5000' }],
    })
  })

  it('renders summary, annual table, schedule, and journal entry templates on success', async () => {
    render(<LoanAmortizationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Generate Schedule/i }))

    await waitFor(() => expect(screen.getByText('Summary')).toBeInTheDocument())
    expect(screen.getByText('Annual Summary')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Period-by-Period Schedule/i })).toBeInTheDocument()
    expect(screen.getByText('Suggested Journal Entries')).toBeInTheDocument()
    expect(screen.getByText('Periodic payment')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download XLSX/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download PDF/i })).toBeInTheDocument()
  })

  it('surfaces the error when apiPost returns ok=false', async () => {
    mockApiPost.mockResolvedValueOnce({ ok: false, status: 400, error: 'invalid loan' })
    render(<LoanAmortizationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Generate Schedule/i }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('invalid loan'))
    expect(screen.queryByText('Summary')).not.toBeInTheDocument()
  })

  it('delegates CSV/XLSX/PDF export to apiDownload + downloadBlob', async () => {
    mockApiDownload.mockResolvedValue({
      ok: true,
      blob: new Blob(['bytes']),
      filename: 'loan_amortization_schedule.csv',
    })

    render(<LoanAmortizationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Generate Schedule/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /Download CSV/i }))
    await waitFor(() => expect(mockApiDownload).toHaveBeenCalledTimes(1))

    fireEvent.click(screen.getByRole('button', { name: /Download XLSX/i }))
    await waitFor(() => expect(mockApiDownload).toHaveBeenCalledTimes(2))

    fireEvent.click(screen.getByRole('button', { name: /Download PDF/i }))
    await waitFor(() => expect(mockApiDownload).toHaveBeenCalledTimes(3))

    const endpoints = mockApiDownload.mock.calls.map((call) => String(call[0]))
    expect(endpoints[0]).toBe('/audit/loan-amortization/export.csv')
    expect(endpoints[1]).toBe('/audit/loan-amortization/export.xlsx')
    expect(endpoints[2]).toBe('/audit/loan-amortization/export.pdf')

    expect(mockApiDownload.mock.calls[0][1]).toBe('test-token')
    expect(mockApiDownload.mock.calls[0][2]).toEqual(expect.objectContaining({ method: 'POST' }))

    expect(mockDownloadBlob).toHaveBeenCalledTimes(3)
  })

  it('shows an error when an export response is not ok', async () => {
    mockApiDownload.mockResolvedValue({ ok: false, error: 'CSV export failed' })

    render(<LoanAmortizationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Generate Schedule/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument())

    fireEvent.click(screen.getByRole('button', { name: /Download CSV/i }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('CSV export failed'))
    expect(mockDownloadBlob).not.toHaveBeenCalled()
  })
})
