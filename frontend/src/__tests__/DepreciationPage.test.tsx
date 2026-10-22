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

    const macrsSelect = screen.getByDisplayValue(/GDS 200% DB/) as HTMLSelectElement
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

  it('delegates CSV download to apiDownload + downloadBlob', async () => {
    const blob = new Blob(['csv'], { type: 'text/csv' })
    mockApiDownload.mockResolvedValue({ ok: true, blob, filename: 'depreciation_Office_Equipment.csv' })

    render(<DepreciationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate Schedule/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Download CSV/i }))

    await waitFor(() => expect(mockApiDownload).toHaveBeenCalled())
    expect(mockApiDownload).toHaveBeenCalledWith(
      '/audit/depreciation/export.csv',
      'test-token',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(mockDownloadBlob).toHaveBeenCalledWith(blob, 'depreciation_Office_Equipment.csv')
  })
  // ===========================================================================
  // Sprint 795 — the form must not be able to assemble a combination the
  // backend refuses.
  //
  // Until 2026-10-22 this dropdown offered "GDS 150% DB" and "GDS Straight-Line"
  // for any property class, and the backend ignored the selection entirely —
  // all three returned the 200% declining-balance table. The backend now
  // rejects combinations it has no published table for, so an option left in
  // the UI becomes a 400 the user cannot act on.
  // ===========================================================================

  it('offers no MACRS system the backend cannot compute', () => {
    render(<DepreciationPage />)
    const macrsSelect = screen.getByDisplayValue(/GDS 200% DB/) as HTMLSelectElement
    const values = Array.from(macrsSelect.options).map((o) => o.value)

    expect(values).toEqual(['', 'gds_200db', 'gds_150db'])
    // The straight-line election has no table in this release; offering it
    // produced 200% DB figures labelled as straight line.
    expect(values).not.toContain('gds_sl')
  })

  it('scopes property classes to the selected system', () => {
    render(<DepreciationPage />)
    const macrsSelect = screen.getByDisplayValue(/GDS 200% DB/) as HTMLSelectElement

    const classSelect = () =>
      screen.getByRole('combobox', { name: /MACRS Property Class/i }) as HTMLSelectElement

    // 200% DB covers 3/5/7/10-year property.
    expect(Array.from(classSelect().options).map((o) => o.value)).toEqual(['3', '5', '7', '10'])

    // 150% DB covers 15/20-year property, and the class resets to a valid one.
    fireEvent.change(macrsSelect, { target: { value: 'gds_150db' } })
    expect(Array.from(classSelect().options).map((o) => o.value)).toEqual(['15', '20'])
    expect(classSelect().value).toBe('15')
  })

  it('offers mid-quarter only for 200% DB five-year property', () => {
    render(<DepreciationPage />)
    const macrsSelect = screen.getByDisplayValue(/GDS 200% DB/) as HTMLSelectElement
    const conventionSelect = () =>
      screen.getByRole('combobox', { name: /MACRS Convention/i }) as HTMLSelectElement
    const classSelect = () =>
      screen.getByRole('combobox', { name: /MACRS Property Class/i }) as HTMLSelectElement

    // Default is 200% DB / 5-year — mid-quarter available.
    expect(Array.from(conventionSelect().options).map((o) => o.value)).toContain('mid_quarter')

    // 7-year property has no mid-quarter table.
    fireEvent.change(classSelect(), { target: { value: '7' } })
    expect(Array.from(conventionSelect().options).map((o) => o.value)).not.toContain('mid_quarter')

    // Nor does 150% DB.
    fireEvent.change(macrsSelect, { target: { value: 'gds_150db' } })
    expect(Array.from(conventionSelect().options).map((o) => o.value)).not.toContain('mid_quarter')
  })

  it('never offers the mid-month convention', () => {
    render(<DepreciationPage />)
    const conventionSelect = screen.getByRole('combobox', {
      name: /MACRS Convention/i,
    }) as HTMLSelectElement
    // Mid-month applies to 27.5/39-year real property, for which no table
    // exists. The old backend path computed mid-month straight line over the
    // asset's *book* life and returned a plausible-looking, meaningless
    // schedule.
    expect(Array.from(conventionSelect.options).map((o) => o.value)).not.toContain('mid_month')
  })

  it('resets the convention when the selection makes mid-quarter invalid', () => {
    render(<DepreciationPage />)
    const classSelect = () =>
      screen.getByRole('combobox', { name: /MACRS Property Class/i }) as HTMLSelectElement
    const conventionSelect = () =>
      screen.getByRole('combobox', { name: /MACRS Convention/i }) as HTMLSelectElement

    fireEvent.change(conventionSelect(), { target: { value: 'mid_quarter' } })
    expect(conventionSelect().value).toBe('mid_quarter')

    // Moving off 5-year property must not leave mid_quarter selected, or the
    // next submit is a 400.
    fireEvent.change(classSelect(), { target: { value: '10' } })
    expect(conventionSelect().value).toBe('half_year')
  })
})
