/** Sprint 844: download-your-data and delete-account controls. */
import { AccountDataSection } from '@/components/settings/AccountDataSection'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

const mockApiPost = jest.fn()
const mockApiDownload = jest.fn()
const mockLogout = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiPost: (...a: unknown[]) => mockApiPost(...a),
  apiDownload: (...a: unknown[]) => mockApiDownload(...a),
  downloadBlob: jest.fn(),
}))
jest.mock('@/contexts/AuthSessionContext', () => ({ useAuthSession: () => ({ token: 'tok', logout: mockLogout }) }))

describe('AccountDataSection', () => {
  beforeEach(() => {
    mockApiPost.mockReset()
    mockApiDownload.mockReset()
    mockLogout.mockReset()
  })

  it('delete stays disabled until password and DELETE are entered', () => {
    render(<AccountDataSection />)
    const button = screen.getByRole('button', { name: 'Delete my account' })
    expect(button).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'pw' } })
    fireEvent.change(screen.getByLabelText('Type DELETE to confirm'), { target: { value: 'delete' } })
    expect(button).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Type DELETE to confirm'), { target: { value: 'DELETE' } })
    expect(button).toBeEnabled()
  })

  it('shows the server error and does not log out when deletion is refused', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'You own an organization that still has other members.' })
    render(<AccountDataSection />)
    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'pw' } })
    fireEvent.change(screen.getByLabelText('Type DELETE to confirm'), { target: { value: 'DELETE' } })
    fireEvent.click(screen.getByRole('button', { name: 'Delete my account' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/other members/))
    expect(mockApiPost).toHaveBeenCalledWith('/auth/account/delete', 'tok', { password: 'pw', confirm: 'DELETE' })
    expect(mockLogout).not.toHaveBeenCalled()
  })

  it('downloads the export', async () => {
    mockApiDownload.mockResolvedValue({ ok: true, blob: new Blob(['{}']) })
    render(<AccountDataSection />)
    fireEvent.click(screen.getByRole('button', { name: 'Download my data' }))
    await waitFor(() => expect(mockApiDownload).toHaveBeenCalledWith('/auth/account/export', 'tok'))
  })
})
