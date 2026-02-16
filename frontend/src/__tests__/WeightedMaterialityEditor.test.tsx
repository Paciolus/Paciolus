/**
 * WeightedMaterialityEditor component tests
 *
 * Tests: toggle on/off, effective threshold calculation,
 * weight adjustment, reset to defaults, and disabled state.
 */
import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, custom, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { WeightedMaterialityEditor } from '@/components/sensitivity/WeightedMaterialityEditor'
import type { WeightedMaterialityConfig } from '@/types/settings'
import { DEFAULT_ACCOUNT_WEIGHTS } from '@/types/settings'

// ─── Fixtures ──────────────────────────────────────────────────────────────────

const enabledConfig: WeightedMaterialityConfig = {
  enabled: true,
  account_weights: { ...DEFAULT_ACCOUNT_WEIGHTS },
  balance_sheet_weight: 1.0,
  income_statement_weight: 0.9,
}

const disabledConfig: WeightedMaterialityConfig = {
  ...enabledConfig,
  enabled: false,
}

const defaultProps = {
  config: enabledConfig,
  baseThreshold: 10000,
  onChange: jest.fn(),
  disabled: false,
}

describe('WeightedMaterialityEditor', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ─── Header & Toggle ───────────────────────────────────────────────

  it('renders header with title', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    expect(screen.getByText('Weighted Materiality by Account Type')).toBeInTheDocument()
  })

  it('shows disabled explanation when config is off', () => {
    render(<WeightedMaterialityEditor {...defaultProps} config={disabledConfig} />)
    expect(screen.getByText(/uniform threshold is applied/)).toBeInTheDocument()
  })

  it('does not show disabled explanation when config is on', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    expect(screen.queryByText(/uniform threshold is applied/)).not.toBeInTheDocument()
  })

  it('calls onChange to toggle enabled state', async () => {
    const user = userEvent.setup()
    render(<WeightedMaterialityEditor {...defaultProps} />)

    // Click the toggle button (it's the button in the header area without text)
    const toggleButton = screen.getAllByRole('button').find(btn =>
      btn.className.includes('rounded-full')
    )!
    await user.click(toggleButton)

    expect(defaultProps.onChange).toHaveBeenCalledWith(
      expect.objectContaining({ enabled: false })
    )
  })

  // ─── Category Display ──────────────────────────────────────────────

  it('shows all 5 account categories when enabled', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    // Each category appears in both category list and effective thresholds preview
    expect(screen.getAllByText('Assets').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Liabilities').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Equity').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Revenue').length).toBeGreaterThanOrEqual(2)
    expect(screen.getAllByText('Expenses').length).toBeGreaterThanOrEqual(2)
  })

  it('does not show categories when disabled', () => {
    render(<WeightedMaterialityEditor {...defaultProps} config={disabledConfig} />)
    expect(screen.queryByText('Account Category Weights')).not.toBeInTheDocument()
  })

  // ─── Effective Threshold Preview ────────────────────────────────────

  it('shows base threshold in effective thresholds section', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    expect(screen.getByText(/Base: \$10,000/)).toBeInTheDocument()
  })

  it('calculates correct effective threshold for assets (weight 1.0, BS weight 1.0)', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    // Assets: base / (1.0 * 1.0) = $10,000
    // This appears in both category row and effective thresholds preview
    const thresholds = screen.getAllByText('$10,000')
    expect(thresholds.length).toBeGreaterThanOrEqual(1)
  })

  it('calculates correct effective threshold for equity (weight 1.5, BS weight 1.0)', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    // Equity: 10000 / (1.5 * 1.0) = 6666.67 → Math.round(...*100)/100 = $6,666.67
    const thresholds = screen.getAllByText('$6,666.67')
    expect(thresholds.length).toBeGreaterThanOrEqual(1)
  })

  // ─── Statement Weight Controls ──────────────────────────────────────

  it('shows balance sheet and income statement weight controls', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    expect(screen.getByText('Balance Sheet Weight')).toBeInTheDocument()
    expect(screen.getByText('Income Statement Weight')).toBeInTheDocument()
  })

  it('displays current weight values', () => {
    render(<WeightedMaterialityEditor {...defaultProps} />)
    // 1.0x appears in balance sheet weight + asset + unknown weights
    expect(screen.getAllByText('1.0x').length).toBeGreaterThanOrEqual(1)
    // 0.9x is unique to income statement weight
    expect(screen.getAllByText('0.9x').length).toBeGreaterThanOrEqual(1)
  })

  // ─── Category Expansion ─────────────────────────────────────────────

  it('expands category detail on click', async () => {
    const user = userEvent.setup()
    render(<WeightedMaterialityEditor {...defaultProps} />)

    // Click the Assets category button
    const assetButtons = screen.getAllByRole('button')
    const assetButton = assetButtons.find(b => b.textContent?.includes('Assets'))!
    await user.click(assetButton)

    // Should show Low/High labels and slider
    expect(screen.getByText('Low')).toBeInTheDocument()
    expect(screen.getByText('High')).toBeInTheDocument()
  })

  // ─── Reset ──────────────────────────────────────────────────────────

  it('calls onChange with default weights when Reset is clicked', async () => {
    const user = userEvent.setup()
    const customConfig = {
      ...enabledConfig,
      account_weights: { ...DEFAULT_ACCOUNT_WEIGHTS, asset: 3.0 },
    }
    render(<WeightedMaterialityEditor {...defaultProps} config={customConfig} />)

    await user.click(screen.getByText('Reset to defaults'))

    expect(defaultProps.onChange).toHaveBeenCalledWith(
      expect.objectContaining({
        account_weights: expect.objectContaining({ asset: 1.0 }),
        balance_sheet_weight: 1.0,
        income_statement_weight: 0.9,
      })
    )
  })

  // ─── Disabled State ─────────────────────────────────────────────────

  it('disables toggle and category buttons when disabled prop is true', () => {
    render(<WeightedMaterialityEditor {...defaultProps} disabled={true} />)
    const buttons = screen.getAllByRole('button')
    buttons.forEach(btn => {
      expect(btn).toBeDisabled()
    })
  })
})
