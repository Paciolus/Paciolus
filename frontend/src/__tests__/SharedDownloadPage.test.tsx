/**
 * Sprint 699: Public share-receive page tests.
 *
 * Pins the Sprint 696+698 download contract from the recipient's side:
 *  - GET that returns 200 → download triggers, no passcode UI shown.
 *  - GET that returns 403 → passcode prompt appears; submitting POSTs
 *    {"passcode": "..."} to /{token}/download.
 *  - 429 response → lockout view with Retry-After countdown.
 *  - 410 / 404 → terminal error states (no passcode form).
 */
import SharedDownloadPage from '@/app/shared/[token]/page'
import { render, screen, fireEvent, waitFor, act } from '@/test-utils'

const mockFetch = jest.fn()
global.fetch = mockFetch as unknown as typeof fetch

let currentToken = 'abc123'

jest.mock('next/navigation', () => ({
  useParams: () => ({ token: currentToken }),
}))

let createUrl: jest.Mock
let revokeUrl: jest.Mock
let appendSpy: jest.SpyInstance
let removeSpy: jest.SpyInstance

beforeEach(() => {
  jest.clearAllMocks()
  jest.useFakeTimers()
  createUrl = jest.fn(() => 'blob:fake-url')
  revokeUrl = jest.fn()
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl })
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeUrl })
  appendSpy = jest.spyOn(document.body, 'appendChild')
  removeSpy = jest.spyOn(document.body, 'removeChild')
})

afterEach(() => {
  appendSpy.mockRestore()
  removeSpy.mockRestore()
  jest.useRealTimers()
})

function renderPage(token = 'abc123') {
  currentToken = token
  return render(<SharedDownloadPage />)
}

describe('SharedDownloadPage', () => {
  it('downloads immediately when the share does not require a passcode', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      blob: async () => new Blob(['bytes']),
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="tb.csv"' }),
    })

    renderPage()

    await waitFor(() => expect(createUrl).toHaveBeenCalledTimes(1))
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/export-sharing/abc123'),
      expect.objectContaining({ method: 'GET', credentials: 'omit' }),
    )
    expect(await screen.findByText(/Download started/i)).toBeInTheDocument()
  })

  it('shows the passcode form when GET returns 403', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'This share link requires a passcode.' }),
      headers: new Headers(),
    })

    renderPage()

    expect(await screen.findByLabelText(/Passcode/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download/i })).toBeDisabled()
  })

  it('POSTs the passcode as a JSON body and downloads on 200', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'passcode required' }),
      headers: new Headers(),
    })
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      blob: async () => new Blob(['bytes']),
      headers: new Headers({ 'Content-Disposition': 'attachment; filename="tb.csv"' }),
    })

    renderPage('tok-xyz')
    const input = await screen.findByLabelText(/Passcode/i)
    fireEvent.change(input, { target: { value: 'letmein' } })
    fireEvent.click(screen.getByRole('button', { name: /Download/i }))

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(2))
    const [url, init] = mockFetch.mock.calls[1]
    expect(String(url)).toContain('/export-sharing/tok-xyz/download')
    expect(init).toMatchObject({
      method: 'POST',
      credentials: 'omit',
      body: JSON.stringify({ passcode: 'letmein' }),
    })
    expect(init.headers).toMatchObject({ 'Content-Type': 'application/json' })
    expect(await screen.findByText(/Download started/i)).toBeInTheDocument()
  })

  it('surfaces the server error message on 403 invalid passcode', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'requires a passcode' }),
      headers: new Headers(),
    })
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'Invalid passcode.' }),
      headers: new Headers(),
    })

    renderPage()
    const input = await screen.findByLabelText(/Passcode/i)
    fireEvent.change(input, { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /Download/i }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Invalid passcode.'))
    // Passcode field should be cleared so the user can try again.
    expect((screen.getByLabelText(/Passcode/i) as HTMLInputElement).value).toBe('')
  })

  it('switches to the lockout view on 429 and parses Retry-After', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'passcode required' }),
      headers: new Headers(),
    })
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => ({ detail: 'Too many attempts' }),
      headers: new Headers({ 'Retry-After': '75' }),
    })

    renderPage()
    const input = await screen.findByLabelText(/Passcode/i)
    fireEvent.change(input, { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /Download/i }))

    expect(await screen.findByText(/Too many failed attempts/i)).toBeInTheDocument()
    // Retry-After: 75s → "1m 15s" rendered in the countdown mono span.
    expect(screen.getByText(/1m 15s/)).toBeInTheDocument()
    // The passcode form must be gone — the recipient cannot retry mid-lockout.
    expect(screen.queryByLabelText(/^Passcode/i)).not.toBeInTheDocument()
  })

  it('shows the expired state when the backend returns 410', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 410,
      json: async () => ({ detail: 'expired' }),
      headers: new Headers(),
    })
    renderPage()
    expect(await screen.findByText(/This link has expired/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Passcode/i)).not.toBeInTheDocument()
  })

  it('shows the not-found state when the backend returns 404', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'not found' }),
      headers: new Headers(),
    })
    renderPage()
    expect(await screen.findByText(/Share link unavailable/i)).toBeInTheDocument()
  })
})
