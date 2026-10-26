/**
 * Sprint 840 / PR #232 review: End Session revokes server-side before
 * discarding the token, and keeps it if the revocation fails.
 */
import { ImpersonationBanner } from '@/components/shared/ImpersonationBanner'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

const mockApiPost = jest.fn()
jest.mock('@/utils/apiClient', () => ({ apiPost: (...args: unknown[]) => mockApiPost(...args) }))
jest.mock('@/contexts/AuthSessionContext', () => ({ useAuthSession: () => ({ token: 'admin-tok' }) }))

function seed() {
  sessionStorage.setItem('impersonation_token', 'imp-tok')
  sessionStorage.setItem('impersonation_email', 'client@example.com')
  sessionStorage.setItem('impersonation_expires', new Date(Date.now() + 600_000).toISOString())
}

describe('ImpersonationBanner', () => {
  beforeEach(() => {
    sessionStorage.clear()
    mockApiPost.mockReset()
  })

  it('keeps the token and shows an error when revocation fails', async () => {
    seed()
    mockApiPost.mockResolvedValue({ ok: false })
    render(<ImpersonationBanner />)
    fireEvent.click(screen.getByRole('button', { name: 'End Session' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Could not end the session/))
    expect(mockApiPost).toHaveBeenCalledWith('/internal/admin/impersonate/stop', 'admin-tok', { token: 'imp-tok' })
    expect(sessionStorage.getItem('impersonation_token')).toBe('imp-tok')
  })

  it('clears the token only after the server confirms', async () => {
    seed()
    mockApiPost.mockResolvedValue({ ok: true })
    render(<ImpersonationBanner />)
    fireEvent.click(screen.getByRole('button', { name: 'End Session' }))
    await waitFor(() => expect(sessionStorage.getItem('impersonation_token')).toBeNull())
  })
})
