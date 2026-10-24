/**
 * SavedSettingsNotice + payroll key normalisation (Sprint 836)
 *
 * Saved testing settings now reach the engines; the results view must say
 * which thresholds differed from the Paciolus defaults and which saved
 * settings were not applied.
 */
import { SavedSettingsNotice } from '@/components/shared/SavedSettingsNotice'
import { DEFAULT_PAYROLL_TESTING_CONFIG, normalizePayrollTestingConfig } from '@/types/settings'
import { render, screen } from '@/test-utils'

describe('SavedSettingsNotice', () => {
  it('renders nothing when every threshold was a default', () => {
    const { container } = render(<SavedSettingsNotice tool="je" applied={{}} ignored={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing for results from before the fields existed', () => {
    const { container } = render(<SavedSettingsNotice tool="ap" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('lists changed thresholds with their defaults', () => {
    render(
      <SavedSettingsNotice
        tool="je"
        applied={{ round_amount_threshold: 50000, single_user_volume_pct: 0.15, weekend_posting_enabled: false }}
      />,
    )
    expect(screen.getByText('3 thresholds differed from Paciolus defaults on this run')).toBeInTheDocument()
    expect(screen.getByText('$50,000')).toBeInTheDocument()
    expect(screen.getByText('$10,000')).toBeInTheDocument()
    expect(screen.getByText('15%')).toBeInTheDocument()
    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText(/Weekend Postings/)).toBeInTheDocument()
  })

  it('uses the singular for one change', () => {
    render(<SavedSettingsNotice tool="three_way_match" applied={{ date_window_days: 60 }} />)
    expect(screen.getByText('1 threshold differed from Paciolus defaults on this run')).toBeInTheDocument()
    expect(screen.getByText('60 d')).toBeInTheDocument()
  })

  it('reports ignored settings with their reasons', () => {
    render(
      <SavedSettingsNotice
        tool="payroll"
        ignored={[{ key: 'retired_threshold', reason: 'Not a setting this tool recognises.' }]}
      />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('1 saved setting was not applied')
    expect(screen.getByText('retired_threshold')).toBeInTheDocument()
    expect(screen.getByText(/Not a setting this tool recognises/)).toBeInTheDocument()
  })
})

describe('normalizePayrollTestingConfig', () => {
  it('maps legacy toggle names to the engine names', () => {
    const out = normalizePayrollTestingConfig({ check_gap_enabled: false, benford_enabled: false, round_amount_threshold: 5000 })
    expect(out).toEqual({ check_number_gap_enabled: false, enable_benford: false, round_amount_threshold: 5000 })
  })

  it('keeps the engine name when both are present', () => {
    expect(normalizePayrollTestingConfig({ ghost_enabled: false, enable_ghost: true })).toEqual({ enable_ghost: true })
  })

  it('keeps a legacy choice when merged over the defaults', () => {
    const merged = { ...DEFAULT_PAYROLL_TESTING_CONFIG, ...normalizePayrollTestingConfig({ duplicate_tax_enabled: false }) }
    expect(merged.enable_tax_id_duplicates).toBe(false)
    expect('duplicate_tax_enabled' in merged).toBe(false)
  })
})
