/**
 * Practice Settings page tests
 *
 * Tests the most complex settings page: materiality formula, weighted materiality,
 * testing config sections (JE/AP/Payroll/TWM), display preferences, export settings, save.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockUpdatePracticeSettings = jest.fn()
const mockPreviewMateriality = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { name: 'Test User', email: 'test@example.com', is_verified: true },
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
  })),
}))

jest.mock('@/hooks/useSettings', () => ({
  useSettings: jest.fn(() => ({
    practiceSettings: {
      default_materiality: { type: 'fixed', value: 500, min_threshold: null, max_threshold: null },
      show_immaterial_by_default: false,
      default_fiscal_year_end: '12-31',
      auto_save_summaries: true,
      default_export_format: 'pdf',
      weighted_materiality: null,
      je_testing_config: null,
      ap_testing_config: null,
      payroll_testing_config: null,
      three_way_match_config: null,
    },
    isLoading: false,
    error: null,
    updatePracticeSettings: mockUpdatePracticeSettings,
    previewMateriality: mockPreviewMateriality,
  })),
}))

jest.mock('@/components/auth/ProfileDropdown', () => ({
  ProfileDropdown: () => <div data-testid="profile-dropdown">Profile</div>,
}))

jest.mock('@/components/settings/TestingConfigSection', () => ({
  TestingConfigSection: ({ title, children }: any) => (
    <div data-testid={`testing-config-${title.toLowerCase().replace(/[^a-z]/g, '-')}`}>
      <h3>{title}</h3>
      {children}
    </div>
  ),
}))

jest.mock('@/components/sensitivity', () => ({
  WeightedMaterialityEditor: ({ config, onChange }: any) => (
    <div data-testid="weighted-materiality-editor">Weighted Editor</div>
  ),
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    span: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <span {...rest}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>
})

import { useSettings } from '@/hooks/useSettings'
import PracticeSettingsPage from '@/app/settings/practice/page'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock
const mockUseSettings = useSettings as jest.Mock

describe('PracticeSettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPreviewMateriality.mockResolvedValue({ threshold: 500 })
    mockUpdatePracticeSettings.mockResolvedValue(true)
    mockUseAuth.mockReturnValue({
      user: { name: 'Test User', email: 'test@example.com', is_verified: true },
      isAuthenticated: true,
      isLoading: false,
      logout: jest.fn(),
    })
    mockUseSettings.mockReturnValue({
      practiceSettings: {
        default_materiality: { type: 'fixed', value: 500, min_threshold: null, max_threshold: null },
        show_immaterial_by_default: false,
        default_fiscal_year_end: '12-31',
        auto_save_summaries: true,
        default_export_format: 'pdf',
        weighted_materiality: null,
        je_testing_config: null,
        ap_testing_config: null,
        payroll_testing_config: null,
        three_way_match_config: null,
      },
      isLoading: false,
      error: null,
      updatePracticeSettings: mockUpdatePracticeSettings,
      previewMateriality: mockPreviewMateriality,
    })
  })

  it('renders page header and breadcrumb', () => {
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Practice Configuration')).toBeInTheDocument()
    // "Practice Settings" appears in both nav breadcrumb and page — verify at least one exists
    expect(screen.getAllByText('Practice Settings').length).toBeGreaterThanOrEqual(1)
  })

  it('shows materiality formula section', () => {
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Default Materiality Formula')).toBeInTheDocument()
    expect(screen.getByText('Calculation Method')).toBeInTheDocument()
  })

  it('shows weighted materiality editor', () => {
    render(<PracticeSettingsPage />)
    expect(screen.getByTestId('weighted-materiality-editor')).toBeInTheDocument()
  })

  it('renders all 4 testing config sections', () => {
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Journal Entry Testing')).toBeInTheDocument()
    expect(screen.getByText('AP Payment Testing')).toBeInTheDocument()
    expect(screen.getByText('Payroll & Employee Testing')).toBeInTheDocument()
    expect(screen.getByText('Three-Way Match')).toBeInTheDocument()
  })

  it('shows display preferences with checkboxes', () => {
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Display Preferences')).toBeInTheDocument()
    expect(screen.getByText('Show immaterial items by default')).toBeInTheDocument()
    expect(screen.getByText('Auto-save diagnostic summaries')).toBeInTheDocument()
  })

  it('shows export settings section', () => {
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Export Settings')).toBeInTheDocument()
    expect(screen.getByText('Default Export Format')).toBeInTheDocument()
    expect(screen.getByText('Default Fiscal Year End')).toBeInTheDocument()
  })

  it('shows materiality preview when available', async () => {
    mockPreviewMateriality.mockResolvedValue({ threshold: 5000 })
    render(<PracticeSettingsPage />)

    await waitFor(() => {
      expect(screen.getByText('Calculated Threshold')).toBeInTheDocument()
    })
  })

  it('saves settings on button click', async () => {
    const user = userEvent.setup()
    render(<PracticeSettingsPage />)

    const saveButton = screen.getByText('Save All Settings')
    await user.click(saveButton)

    await waitFor(() => {
      expect(mockUpdatePracticeSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          default_materiality: expect.objectContaining({ type: 'fixed', value: 500 }),
          show_immaterial_by_default: false,
          default_fiscal_year_end: '12-31',
          auto_save_summaries: true,
          default_export_format: 'pdf',
        })
      )
    })
  })

  it('shows success message after saving', async () => {
    mockUpdatePracticeSettings.mockResolvedValue(true)
    const user = userEvent.setup()
    render(<PracticeSettingsPage />)

    const saveButton = screen.getByText('Save All Settings')
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText('Settings saved successfully!')).toBeInTheDocument()
    })
  })

  it('shows Saving... text while submitting', async () => {
    mockUpdatePracticeSettings.mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    render(<PracticeSettingsPage />)

    const saveButton = screen.getByText('Save All Settings')
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })
  })

  it('shows loading spinner when settings are loading', () => {
    mockUseSettings.mockReturnValue({
      practiceSettings: null,
      isLoading: true,
      error: null,
      updatePracticeSettings: mockUpdatePracticeSettings,
      previewMateriality: mockPreviewMateriality,
    })
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Loading settings...')).toBeInTheDocument()
  })

  it('shows error message when settings fail to load', () => {
    mockUseSettings.mockReturnValue({
      practiceSettings: {
        default_materiality: { type: 'fixed', value: 500, min_threshold: null, max_threshold: null },
        show_immaterial_by_default: false,
        default_fiscal_year_end: '12-31',
        auto_save_summaries: true,
        default_export_format: 'pdf',
      },
      isLoading: false,
      error: 'Failed to load settings',
      updatePracticeSettings: mockUpdatePracticeSettings,
      previewMateriality: mockPreviewMateriality,
    })
    render(<PracticeSettingsPage />)
    expect(screen.getByText('Failed to load settings')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      logout: jest.fn(),
    })
    render(<PracticeSettingsPage />)
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('shows min/max thresholds for percentage formula type', async () => {
    mockUseSettings.mockReturnValue({
      practiceSettings: {
        default_materiality: { type: 'percentage_revenue', value: 5, min_threshold: 1000, max_threshold: 50000 },
        show_immaterial_by_default: false,
        default_fiscal_year_end: '12-31',
        auto_save_summaries: true,
        default_export_format: 'pdf',
      },
      isLoading: false,
      error: null,
      updatePracticeSettings: mockUpdatePracticeSettings,
      previewMateriality: mockPreviewMateriality,
    })
    render(<PracticeSettingsPage />)

    expect(screen.getByText('Minimum Floor ($)')).toBeInTheDocument()
    expect(screen.getByText('Maximum Cap ($)')).toBeInTheDocument()
  })
})
