/**
 * Sprint 847 (security review M4): changing the email address needs the
 * current password, because the email is where password resets are sent.
 */
import ProfileSettingsPage from '@/app/settings/profile/page'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

const mockUpdateProfile = jest.fn()
// Stable identity: the page re-seeds its form whenever `user` changes.
const mockUser = { name: 'Pat Auditor', email: 'pat@example.com', pending_email: null }

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}))

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
  })),
}))

jest.mock('@/contexts/UserProfileContext', () => ({
  useUserProfile: () => ({
    updateProfile: (...args: unknown[]) => mockUpdateProfile(...args),
    changePassword: jest.fn(),
  }),
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('ProfileSettingsPage — email change', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUpdateProfile.mockResolvedValue({ success: true })
  })

  it('does not ask for a password while the email is unchanged', () => {
    render(<ProfileSettingsPage />)
    expect(screen.queryByLabelText('Current Password', { selector: '#profile-email-password' })).toBeNull()
  })

  it('requires the current password before an email change can be saved', async () => {
    render(<ProfileSettingsPage />)

    fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'new@example.com' } })
    const save = screen.getByRole('button', { name: 'Save Profile' })
    const passwordInput = screen.getByLabelText('Current Password', { selector: '#profile-email-password' })
    expect(save).toBeDisabled()

    fireEvent.change(passwordInput, { target: { value: 'my-password' } })
    expect(save).toBeEnabled()
    fireEvent.click(save)

    await waitFor(() =>
      expect(mockUpdateProfile).toHaveBeenCalledWith({ email: 'new@example.com', current_password: 'my-password' })
    )
  })

  it('sends a name-only change without a password', async () => {
    render(<ProfileSettingsPage />)

    fireEvent.change(screen.getByLabelText('Display Name'), { target: { value: 'Pat Q. Auditor' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Profile' }))

    await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalledWith({ name: 'Pat Q. Auditor' }))
  })
})
