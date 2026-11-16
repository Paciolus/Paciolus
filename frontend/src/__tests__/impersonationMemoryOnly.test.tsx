/**
 * Sprint 872 (AZ-13): impersonation state lives in memory only.
 *
 * The admin customer page used to write the impersonation access token, the
 * customer's email and the expiry to sessionStorage, where any script on the
 * origin could read them. Now: starting and ending impersonation writes
 * nothing to browser storage, ending still revokes server-side, and logging
 * out clears the state. A reload simply loses it (the admin starts again).
 */
import { act } from 'react'
import { readFileSync } from 'fs'
import { join } from 'path'
import { ImpersonationBanner } from '@/components/shared/ImpersonationBanner'
import { beginSession, endSession } from '@/utils/sessionScope'
import { startImpersonation, getImpersonation } from '@/lib/impersonationState'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

const mockApiPost = jest.fn()
jest.mock('@/utils/apiClient', () => ({ apiPost: (...args: unknown[]) => mockApiPost(...args) }))
jest.mock('@/contexts/AuthSessionContext', () => ({ useAuthSession: () => ({ token: 'admin-tok' }) }))

const CUSTOMER = { token: 'imp-secret-tok', email: 'customer@client-firm.test' }

let setItemSpy: jest.SpyInstance

beforeEach(() => {
  sessionStorage.clear()
  localStorage.clear()
  mockApiPost.mockReset()
  setItemSpy = jest.spyOn(Storage.prototype, 'setItem')
  // endSession navigates via window.location.href; jsdom only logs that.
  jest.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  jest.restoreAllMocks()
  act(() => { endSession() })
})

function storageHolds(value: string): boolean {
  const all = [sessionStorage, localStorage].flatMap(s =>
    Array.from({ length: s.length }, (_, i) => `${s.key(i)}=${s.getItem(s.key(i)!)}`))
  return all.some(entry => entry.includes(value))
}

function start() {
  act(() => {
    startImpersonation({
      token: CUSTOMER.token,
      email: CUSTOMER.email,
      expiresAt: new Date(Date.now() + 600_000).toISOString(),
    })
  })
}

describe('AZ-13: impersonation is held in memory only', () => {
  it('starting and ending impersonation writes no token or email to browser storage', async () => {
    mockApiPost.mockResolvedValue({ ok: true })
    render(<ImpersonationBanner />)

    start()
    expect(await screen.findByText(CUSTOMER.email)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'End Session' }))
    await waitFor(() => expect(screen.queryByText(CUSTOMER.email)).not.toBeInTheDocument())

    // Server-side revocation still happens, with the in-memory token.
    expect(mockApiPost).toHaveBeenCalledWith('/internal/admin/impersonate/stop', 'admin-tok', { token: CUSTOMER.token })
    expect(getImpersonation()).toBeNull()

    for (const call of setItemSpy.mock.calls) {
      expect(String(call[1])).not.toContain(CUSTOMER.token)
      expect(String(call[1])).not.toContain(CUSTOMER.email)
      expect(String(call[0])).not.toMatch(/impersonat/i)
    }
    expect(storageHolds(CUSTOMER.token)).toBe(false)
    expect(storageHolds(CUSTOMER.email)).toBe(false)
  })

  it('keeps the in-memory token when server-side revocation fails', async () => {
    mockApiPost.mockResolvedValue({ ok: false })
    render(<ImpersonationBanner />)
    start()
    fireEvent.click(await screen.findByRole('button', { name: 'End Session' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Could not end the session/))
    expect(getImpersonation()?.token).toBe(CUSTOMER.token)
  })

  it('logging out clears impersonation state', async () => {
    act(() => { beginSession(1) })
    render(<ImpersonationBanner />)
    start()
    expect(await screen.findByText(CUSTOMER.email)).toBeInTheDocument()

    act(() => { endSession() })
    await waitFor(() => expect(screen.queryByText(CUSTOMER.email)).not.toBeInTheDocument())
    expect(getImpersonation()).toBeNull()
  })

  it('neither the admin page nor the banner touches browser storage', () => {
    const files = [
      'src/app/internal/admin/customers/[orgId]/page.tsx',
      'src/components/shared/ImpersonationBanner.tsx',
      'src/lib/impersonationState.ts',
    ]
    for (const file of files) {
      const src = readFileSync(join(process.cwd(), file), 'utf-8')
      expect({ file, usesStorage: /sessionStorage|localStorage/.test(src) }).toEqual({ file, usesStorage: false })
    }
  })
})
