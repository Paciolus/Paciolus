/**
 * Sprint 840 / PR #232 review: End Session revokes server-side before
 * discarding the token, and keeps it if the revocation fails.
 * Sprint 872 (AZ-13): the token is held in memory (`lib/impersonationState`),
 * not sessionStorage — see impersonationMemoryOnly.test.tsx.
 */
import { act } from 'react'
import { ImpersonationBanner } from '@/components/shared/ImpersonationBanner'
import { clearImpersonation, getImpersonation, startImpersonation } from '@/lib/impersonationState'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

const mockApiPost = jest.fn()
jest.mock('@/utils/apiClient', () => ({ apiPost: (...args: unknown[]) => mockApiPost(...args) }))
jest.mock('@/contexts/AuthSessionContext', () => ({ useAuthSession: () => ({ token: 'admin-tok' }) }))

function seed() {
  act(() => {
    startImpersonation({
      token: 'imp-tok',
      email: 'client@example.com',
      expiresAt: new Date(Date.now() + 600_000).toISOString(),
    })
  })
}

describe('ImpersonationBanner', () => {
  beforeEach(() => {
    act(() => { clearImpersonation() })
    mockApiPost.mockReset()
    jest.spyOn(console, 'error').mockImplementation(() => {}) // jsdom: navigation not implemented
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('keeps the token and shows an error when revocation fails', async () => {
    mockApiPost.mockResolvedValue({ ok: false })
    render(<ImpersonationBanner />)
    seed()
    fireEvent.click(screen.getByRole('button', { name: 'End Session' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Could not end the session/))
    expect(mockApiPost).toHaveBeenCalledWith('/internal/admin/impersonate/stop', 'admin-tok', { token: 'imp-tok' })
    expect(getImpersonation()?.token).toBe('imp-tok')
  })

  it('clears the token only after the server confirms', async () => {
    mockApiPost.mockResolvedValue({ ok: true })
    render(<ImpersonationBanner />)
    seed()
    fireEvent.click(screen.getByRole('button', { name: 'End Session' }))
    await waitFor(() => expect(getImpersonation()).toBeNull())
  })
})
