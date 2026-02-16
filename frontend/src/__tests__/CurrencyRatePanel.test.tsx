/**
 * CurrencyRatePanel component tests
 *
 * Tests: collapse/expand, mode switching (upload vs manual),
 * manual rate entry validation, file upload zone, error display,
 * active rates summary, and clear functionality.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

const mockUploadRateTable = jest.fn()
const mockAddSingleRate = jest.fn()
const mockClearRates = jest.fn()
const mockRefreshStatus = jest.fn()

jest.mock('@/hooks/useCurrencyRates', () => ({
  useCurrencyRates: jest.fn(() => ({
    rateStatus: null,
    uploadStatus: 'idle' as const,
    error: '',
    uploadRateTable: mockUploadRateTable,
    addSingleRate: mockAddSingleRate,
    clearRates: mockClearRates,
    refreshStatus: mockRefreshStatus,
  })),
}))

import { useCurrencyRates } from '@/hooks/useCurrencyRates'
import { CurrencyRatePanel } from '@/components/currencyRates/CurrencyRatePanel'

const mockUseCurrencyRates = useCurrencyRates as jest.Mock

describe('CurrencyRatePanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUploadRateTable.mockResolvedValue(true)
    mockAddSingleRate.mockResolvedValue(true)
    mockClearRates.mockResolvedValue(true)
    mockRefreshStatus.mockResolvedValue(undefined)
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: null,
      uploadStatus: 'idle' as const,
      error: '',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
  })

  // ─── Collapse / Expand ──────────────────────────────────────────────

  it('renders collapsed with header text', () => {
    render(<CurrencyRatePanel />)
    expect(screen.getByText('Multi-Currency Conversion')).toBeInTheDocument()
    expect(screen.getByText('Optional')).toBeInTheDocument()
  })

  it('does not show body content when collapsed', () => {
    render(<CurrencyRatePanel />)
    expect(screen.queryByLabelText('Presentation Currency:')).not.toBeInTheDocument()
  })

  it('expands on header click and calls refreshStatus', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)

    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(mockRefreshStatus).toHaveBeenCalledTimes(1)
    expect(screen.getByLabelText('Presentation Currency:')).toBeInTheDocument()
  })

  it('collapses on second header click', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)

    await user.click(screen.getByText('Multi-Currency Conversion'))
    expect(screen.getByLabelText('Presentation Currency:')).toBeInTheDocument()

    await user.click(screen.getByText('Multi-Currency Conversion'))
    expect(screen.queryByLabelText('Presentation Currency:')).not.toBeInTheDocument()
  })

  // ─── Rate Badge ─────────────────────────────────────────────────────

  it('shows rate count badge when rates are loaded', () => {
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: { has_rates: true, rate_count: 5, presentation_currency: 'USD', currency_pairs: ['EUR/USD'] },
      uploadStatus: 'idle' as const,
      error: '',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
    render(<CurrencyRatePanel />)
    expect(screen.getByText('5 rates loaded')).toBeInTheDocument()
    expect(screen.getByText('USD')).toBeInTheDocument()
  })

  it('shows singular "rate" for count of 1', () => {
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: { has_rates: true, rate_count: 1, presentation_currency: 'EUR', currency_pairs: [] },
      uploadStatus: 'idle' as const,
      error: '',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
    render(<CurrencyRatePanel />)
    expect(screen.getByText('1 rate loaded')).toBeInTheDocument()
  })

  // ─── Presentation Currency ──────────────────────────────────────────

  it('shows presentation currency selector with common currencies', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    const select = screen.getByLabelText('Presentation Currency:')
    expect(select).toHaveValue('USD')

    const options = select.querySelectorAll('option')
    const optionValues = Array.from(options).map(o => o.textContent)
    expect(optionValues).toContain('EUR')
    expect(optionValues).toContain('GBP')
    expect(optionValues).toContain('JPY')
  })

  // ─── Mode Switching ─────────────────────────────────────────────────

  it('shows upload mode by default', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(screen.getByText('Drop a CSV or Excel file with exchange rates')).toBeInTheDocument()
  })

  it('switches to manual entry mode', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    expect(screen.getByLabelText('From')).toBeInTheDocument()
    expect(screen.getByLabelText('To')).toBeInTheDocument()
    expect(screen.getByLabelText('Rate')).toBeInTheDocument()
  })

  it('switches back to upload mode', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))
    await user.click(screen.getByText('Upload CSV'))

    expect(screen.getByText('Drop a CSV or Excel file with exchange rates')).toBeInTheDocument()
  })

  // ─── Upload Mode ────────────────────────────────────────────────────

  it('shows uploading state during file upload', async () => {
    const user = userEvent.setup()
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: null,
      uploadStatus: 'loading' as const,
      error: '',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(screen.getByText('Uploading...')).toBeInTheDocument()
  })

  it('shows column format hint in upload zone', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(screen.getByText('Columns: effective_date, from_currency, to_currency, rate')).toBeInTheDocument()
  })

  // ─── Manual Entry ───────────────────────────────────────────────────

  it('uppercases and limits currency code input to 3 characters', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    const fromInput = screen.getByLabelText('From')
    await user.type(fromInput, 'euro')

    // Should uppercase and limit to 3 chars
    expect(fromInput).toHaveValue('EUR')
  })

  it('disables Add Rate button when fields are empty', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    const addButton = screen.getByRole('button', { name: 'Add Rate' })
    expect(addButton).toBeDisabled()
  })

  it('enables Add Rate button when all fields are filled', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    await user.type(screen.getByLabelText('From'), 'EUR')
    await user.type(screen.getByLabelText('Rate'), '1.0523')

    const addButton = screen.getByRole('button', { name: 'Add Rate' })
    expect(addButton).not.toBeDisabled()
  })

  it('calls addSingleRate with correct arguments on form submit', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    await user.type(screen.getByLabelText('From'), 'EUR')
    await user.type(screen.getByLabelText('Rate'), '1.0523')

    await user.click(screen.getByRole('button', { name: 'Add Rate' }))

    expect(mockAddSingleRate).toHaveBeenCalledWith('EUR', 'USD', '1.0523', 'USD')
  })

  it('clears fromCurrency and manualRate after successful submission', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    await user.type(screen.getByLabelText('From'), 'EUR')
    await user.type(screen.getByLabelText('Rate'), '1.0523')
    await user.click(screen.getByRole('button', { name: 'Add Rate' }))

    await waitFor(() => {
      expect(screen.getByLabelText('From')).toHaveValue('')
      expect(screen.getByLabelText('Rate')).toHaveValue('')
    })
  })

  it('does not clear fields when submission fails', async () => {
    mockAddSingleRate.mockResolvedValue(false)
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Manual Entry'))

    await user.type(screen.getByLabelText('From'), 'EUR')
    await user.type(screen.getByLabelText('Rate'), '1.05')
    await user.click(screen.getByRole('button', { name: 'Add Rate' }))

    await waitFor(() => {
      expect(screen.getByLabelText('From')).toHaveValue('EUR')
    })
  })

  // ─── Error Display ──────────────────────────────────────────────────

  it('shows error alert when error is present', async () => {
    const user = userEvent.setup()
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: null,
      uploadStatus: 'error' as const,
      error: 'Invalid CSV format',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(screen.getByRole('alert')).toHaveTextContent('Invalid CSV format')
  })

  // ─── Active Rates Summary ──────────────────────────────────────────

  it('shows active rates summary with currency pairs', async () => {
    const user = userEvent.setup()
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: { has_rates: true, rate_count: 3, presentation_currency: 'USD', currency_pairs: ['EUR/USD', 'GBP/USD'] },
      uploadStatus: 'idle' as const,
      error: '',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText(/rates? active/)).toBeInTheDocument()
    expect(screen.getByText('(EUR/USD, GBP/USD)')).toBeInTheDocument()
  })

  it('calls clearRates when Clear button is clicked', async () => {
    const user = userEvent.setup()
    mockUseCurrencyRates.mockReturnValue({
      rateStatus: { has_rates: true, rate_count: 2, presentation_currency: 'USD', currency_pairs: [] },
      uploadStatus: 'idle' as const,
      error: '',
      uploadRateTable: mockUploadRateTable,
      addSingleRate: mockAddSingleRate,
      clearRates: mockClearRates,
      refreshStatus: mockRefreshStatus,
    })
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))
    await user.click(screen.getByText('Clear'))

    expect(mockClearRates).toHaveBeenCalledTimes(1)
  })

  // ─── Help Text ──────────────────────────────────────────────────────

  it('shows help text about session-scoped rates', async () => {
    const user = userEvent.setup()
    render(<CurrencyRatePanel />)
    await user.click(screen.getByText('Multi-Currency Conversion'))

    expect(screen.getByText(/Rates are session-scoped and never stored/)).toBeInTheDocument()
  })
})
