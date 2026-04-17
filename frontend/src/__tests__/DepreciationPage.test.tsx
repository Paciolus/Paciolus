/**
 * Sprint 626: Depreciation Calculator page tests.
 */
import DepreciationPage from '@/app/tools/depreciation/page'
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

jest.mock('@/utils/apiClient', () => ({
  apiPost: jest.fn(),
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockApiPost = apiPost as jest.MockedFunction<typeof apiPost>

const sampleResponse = {
  inputs: {},
  book_schedule: [
    {
      year_index: 1,
      calendar_year: 2026,
      beginning_book_value: '10000',
      depreciation: '2000',
      accumulated_depreciation: '2000',
      ending_book_value: '8000',
    },
  ],
  tax_schedule: [
    {
      year_index: 1,
      calendar_year: 2026,
      beginning_book_value: '10000',
      depreciation: '2000',
      accumulated_depreciation: '2000',
      ending_book_value: '8000',
    },
  ],
  book_tax_comparison: [
    {
      year_index: 1,
      book_depreciation: '2000',
      tax_depreciation: '2000',
      timing_difference: '0',
      deferred_tax_change: '0',
      cumulative_deferred_tax: '0',
    },
  ],
  total_book_depreciation: '10000',
  total_tax_depreciation: '10000',
  cumulative_deferred_tax: '0',
}

describe('DepreciationPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, status: 200, data: sampleResponse })
  })

  it('renders the hero header and default form values', () => {
    render(<DepreciationPage />)
    expect(screen.getByText('Depreciation Calculator')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Office Equipment')).toBeInTheDocument()
    expect(screen.getByDisplayValue('10000')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Calculate Schedule/i })).toBeInTheDocument()
  })

  it('shows MACRS property class + convention only when a MACRS system is selected', () => {
    render(<DepreciationPage />)
    expect(screen.getByText('MACRS Property Class')).toBeInTheDocument()

    const macrsSelect = screen.getByDisplayValue('GDS 200% DB') as HTMLSelectElement
    fireEvent.change(macrsSelect, { target: { value: '' } })

    expect(screen.queryByText('MACRS Property Class')).not.toBeInTheDocument()
    expect(screen.queryByText('MACRS Convention')).not.toBeInTheDocument()
  })

  it('shows DB factor input only for declining balance method', () => {
    render(<DepreciationPage />)
    expect(screen.queryByText(/DB Factor/i)).not.toBeInTheDocument()

    const bookMethod = screen.getByDisplayValue('Straight-Line') as HTMLSelectElement
    fireEvent.change(bookMethod, { target: { value: 'declining_balance' } })

    expect(screen.getByText(/DB Factor/i)).toBeInTheDocument()
  })

  it('submits with the form payload and converts tax rate to a decimal string', async () => {
    render(<DepreciationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Schedule/i }))

    await waitFor(() => expect(mockApiPost).toHaveBeenCalled())
    const [endpoint, token, payload] = mockApiPost.mock.calls[0]
    expect(endpoint).toBe('/audit/depreciation')
    expect(token).toBe('test-token')
    expect(payload).toMatchObject({
      asset_name: 'Office Equipment',
      cost: '10000',
      salvage_value: '0',
      useful_life_years: 5,
      book_method: 'straight_line',
      macrs_system: 'gds_200db',
      macrs_property_class: 5,
      tax_rate: '0.21',
    })
  })

  it('renders the result tables and summary cards on success', async () => {
    render(<DepreciationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Schedule/i }))

    await waitFor(() => expect(screen.getByText('Book Schedule')).toBeInTheDocument())
    expect(screen.getByText('Tax (MACRS) Schedule')).toBeInTheDocument()
    expect(screen.getByText('Book vs Tax Timing')).toBeInTheDocument()
    expect(screen.getByText('Total Book Depreciation')).toBeInTheDocument()
    expect(screen.getByText('Cumulative Deferred Tax')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()
  })

  it('surfaces an error message when apiPost returns ok=false', async () => {
    mockApiPost.mockResolvedValueOnce({ ok: false, status: 400, error: 'bad inputs' })
    render(<DepreciationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Schedule/i }))

    await waitFor(() => expect(screen.getByText('bad inputs')).toBeInTheDocument())
    expect(screen.queryByText('Book Schedule')).not.toBeInTheDocument()
  })

  it('invokes fetch with Bearer token when downloading CSV', async () => {
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['csv'], { type: 'text/csv' }),
    })
    global.fetch = fetchMock as unknown as typeof fetch
    // jsdom doesn't implement URL.createObjectURL
    const createUrl = jest.fn(() => 'blob:mock')
    const revokeUrl = jest.fn()
    Object.defineProperty(URL, 'createObjectURL', { value: createUrl, configurable: true })
    Object.defineProperty(URL, 'revokeObjectURL', { value: revokeUrl, configurable: true })

    render(<DepreciationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Schedule/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Download CSV/i }))

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/audit/depreciation/export.csv')
    expect((init as RequestInit).method).toBe('POST')
    expect((init as RequestInit).headers).toMatchObject({
      Authorization: 'Bearer test-token',
      'X-Requested-With': 'XMLHttpRequest',
    })
    expect(createUrl).toHaveBeenCalled()
    expect(revokeUrl).toHaveBeenCalled()
  })
})
