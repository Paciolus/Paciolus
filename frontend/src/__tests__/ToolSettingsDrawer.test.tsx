/**
 * ToolSettingsDrawer component tests
 *
 * Tests: rendering drawer when open, closed state, title display,
 * close button, save button, tool-specific content.
 */
import { ToolSettingsDrawer } from '@/components/shared/ToolSettingsDrawer'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('@/hooks/useSettings', () => ({
  useSettings: () => ({
    practiceSettings: null,
    updatePracticeSettings: jest.fn().mockResolvedValue(true),
  }),
}))

jest.mock('@/components/settings/TestingConfigSection', () => ({
  TestingConfigSection: (props: any) => <div data-testid="testing-config">{props.title}</div>,
}))

jest.mock('@/types/settings', () => ({
  DEFAULT_JE_TESTING_CONFIG: {},
  JE_TESTING_PRESETS: {},
  JE_PRESET_LABELS: {},
  JE_PRESET_DESCRIPTIONS: {},
  DEFAULT_AP_TESTING_CONFIG: {},
  AP_TESTING_PRESETS: {},
  AP_PRESET_LABELS: {},
  AP_PRESET_DESCRIPTIONS: {},
  DEFAULT_PAYROLL_TESTING_CONFIG: {},
  PAYROLL_TESTING_PRESETS: {},
  PAYROLL_PRESET_LABELS: {},
  PAYROLL_PRESET_DESCRIPTIONS: {},
  DEFAULT_THREE_WAY_MATCH_CONFIG: {},
  THREE_WAY_MATCH_PRESETS: {},
  TWM_PRESET_LABELS: {},
  TWM_PRESET_DESCRIPTIONS: {},
}))

describe('ToolSettingsDrawer', () => {
  const onClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders nothing when closed', () => {
    const { container } = render(<ToolSettingsDrawer toolKey="je" open={false} onClose={onClose} />)
    expect(container.textContent).toBe('')
  })

  it('renders JE testing title when open', () => {
    render(<ToolSettingsDrawer toolKey="je" open={true} onClose={onClose} />)
    expect(screen.getByText('Journal Entry Testing Settings')).toBeInTheDocument()
  })

  it('renders AP testing title', () => {
    render(<ToolSettingsDrawer toolKey="ap" open={true} onClose={onClose} />)
    expect(screen.getByText('AP Testing Settings')).toBeInTheDocument()
  })

  it('renders Payroll testing title', () => {
    render(<ToolSettingsDrawer toolKey="payroll" open={true} onClose={onClose} />)
    expect(screen.getByText('Payroll Testing Settings')).toBeInTheDocument()
  })

  it('renders Three-Way Match title', () => {
    render(<ToolSettingsDrawer toolKey="three_way_match" open={true} onClose={onClose} />)
    expect(screen.getByText('Three-Way Match Settings')).toBeInTheDocument()
  })

  it('has close button', () => {
    render(<ToolSettingsDrawer toolKey="je" open={true} onClose={onClose} />)
    const closeBtn = screen.getByLabelText('Close settings')
    expect(closeBtn).toBeInTheDocument()
    fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalled()
  })

  it('has Save Settings button', () => {
    render(<ToolSettingsDrawer toolKey="je" open={true} onClose={onClose} />)
    expect(screen.getByText('Save Settings')).toBeInTheDocument()
  })

  it('shows subtitle text', () => {
    render(<ToolSettingsDrawer toolKey="je" open={true} onClose={onClose} />)
    expect(screen.getByText('Adjust thresholds for this tool')).toBeInTheDocument()
  })
})
