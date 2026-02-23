/**
 * TestingConfigSection component tests
 *
 * Tests: preset selection, threshold changes, toggle controls,
 * auto-switch to custom preset on manual change.
 */
import userEvent from '@testing-library/user-event'
import { TestingConfigSection } from '@/components/settings/TestingConfigSection'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))


// Concrete types for testing
type TestPreset = 'conservative' | 'moderate' | 'aggressive' | 'custom'
interface TestConfig {
  threshold: number
  sample_rate: number
  enable_benford: boolean
}

const presetLabels: Record<TestPreset, string> = {
  conservative: 'Conservative',
  moderate: 'Moderate',
  aggressive: 'Aggressive',
  custom: 'Custom',
}

const presetDescriptions: Record<TestPreset, string> = {
  conservative: 'Lower sensitivity, fewer flags',
  moderate: 'Balanced sensitivity',
  aggressive: 'Higher sensitivity, more flags',
  custom: 'Custom configuration',
}

const presetConfigs: Partial<Record<TestPreset, Partial<TestConfig>>> = {
  conservative: { threshold: 50000, sample_rate: 0.05 },
  moderate: { threshold: 25000, sample_rate: 0.10 },
  aggressive: { threshold: 10000, sample_rate: 0.20 },
}

const defaultConfig: TestConfig = {
  threshold: 25000,
  sample_rate: 0.10,
  enable_benford: true,
}

const thresholds = [
  { key: 'threshold', label: 'Materiality Threshold', description: 'Minimum amount to flag', prefix: '$' },
  { key: 'sample_rate', label: 'Sample Rate', description: 'Percentage of entries to sample', suffix: '%', displayScale: 100, step: 1, min: 1, max: 50 },
]

const toggles = [
  { key: 'enable_benford', label: "Benford's Law Analysis" },
]

const defaultProps = {
  title: 'JE Testing Config',
  description: 'Configure journal entry testing parameters',
  delay: 0,
  presetLabels,
  presetDescriptions,
  presetConfigs,
  defaultConfig,
  currentPreset: 'moderate' as TestPreset,
  currentConfig: defaultConfig,
  onPresetChange: jest.fn(),
  onConfigChange: jest.fn(),
  thresholds,
  toggles,
}

describe('TestingConfigSection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders title and description', () => {
    render(<TestingConfigSection {...defaultProps} />)
    expect(screen.getByText('JE Testing Config')).toBeInTheDocument()
    expect(screen.getByText('Configure journal entry testing parameters')).toBeInTheDocument()
  })

  it('shows all preset buttons', () => {
    render(<TestingConfigSection {...defaultProps} />)
    expect(screen.getByText('Conservative')).toBeInTheDocument()
    expect(screen.getByText('Moderate')).toBeInTheDocument()
    expect(screen.getByText('Aggressive')).toBeInTheDocument()
    expect(screen.getByText('Custom')).toBeInTheDocument()
  })

  it('shows current preset description', () => {
    render(<TestingConfigSection {...defaultProps} />)
    expect(screen.getByText('Balanced sensitivity')).toBeInTheDocument()
  })

  it('calls onPresetChange and onConfigChange when preset is clicked', async () => {
    const user = userEvent.setup()
    render(<TestingConfigSection {...defaultProps} />)

    await user.click(screen.getByText('Aggressive'))

    expect(defaultProps.onPresetChange).toHaveBeenCalledWith('aggressive')
    expect(defaultProps.onConfigChange).toHaveBeenCalledWith(
      expect.objectContaining({ threshold: 10000, sample_rate: 0.20 })
    )
  })

  it('shows threshold fields with labels', () => {
    render(<TestingConfigSection {...defaultProps} />)
    expect(screen.getByText('Materiality Threshold')).toBeInTheDocument()
    expect(screen.getByText('Sample Rate')).toBeInTheDocument()
  })

  it('displays threshold values with display scale', () => {
    render(<TestingConfigSection {...defaultProps} />)
    // sample_rate 0.10 * displayScale 100 = 10
    const inputs = screen.getAllByRole('spinbutton')
    const sampleInput = inputs.find(i => (i as HTMLInputElement).value === '10')
    expect(sampleInput).toBeDefined()
  })

  it('switches to custom preset when threshold is changed', async () => {
    const user = userEvent.setup()
    render(<TestingConfigSection {...defaultProps} />)

    const inputs = screen.getAllByRole('spinbutton')
    await user.clear(inputs[0])
    await user.type(inputs[0], '30000')

    expect(defaultProps.onPresetChange).toHaveBeenCalledWith('custom')
  })

  it('shows toggle controls', () => {
    render(<TestingConfigSection {...defaultProps} />)
    expect(screen.getByText("Benford's Law Analysis")).toBeInTheDocument()
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeChecked()
  })

  it('switches to custom preset when toggle is changed', async () => {
    const user = userEvent.setup()
    render(<TestingConfigSection {...defaultProps} />)

    await user.click(screen.getByRole('checkbox'))

    expect(defaultProps.onPresetChange).toHaveBeenCalledWith('custom')
    expect(defaultProps.onConfigChange).toHaveBeenCalledWith(
      expect.objectContaining({ enable_benford: false })
    )
  })
})
