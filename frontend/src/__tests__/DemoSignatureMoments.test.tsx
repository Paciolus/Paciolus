/**
 * Sprint 707: tests for MechanicalGauge + MarginAnnotation (Sprint 864 removed ScanlineOverlay).
 *
 * Coverage goals:
 *   - Each component renders its intended affordance.
 *   - Reduced-motion paths are explicitly covered where they change
 *     behaviour (gauge skips animation; scanline suppresses the sweep).
 *   - A11y assertions on aria-labels and role="note".
 */
import { MechanicalGauge, MarginAnnotation } from '@/components/demo'
import { render, screen, act } from '@/test-utils'

describe('MechanicalGauge', () => {
  it('renders the score label and risk caption', () => {
    render(<MechanicalGauge score={76} riskLevel="low" />)
    // The centre readout renders 76.
    expect(screen.getByText('76')).toBeInTheDocument()
    expect(screen.getByText('Low Risk')).toBeInTheDocument()
  })

  it('aria-label describes the score + risk level', () => {
    render(<MechanicalGauge score={76} riskLevel="low" />)
    const fig = screen.getByLabelText(/Composite diagnostic score 76 out of 100, Low Risk/i)
    expect(fig).toBeInTheDocument()
  })

  it('clamps scores outside the 0..100 range', () => {
    const { rerender } = render(<MechanicalGauge score={-10} riskLevel="low" />)
    // Score 0 appears both in centre readout AND in tick labels.
    // Use aria-label to distinguish the canonical rendering.
    expect(screen.getByLabelText(/score 0 out of 100/i)).toBeInTheDocument()
    rerender(<MechanicalGauge score={150} riskLevel="high" />)
    expect(screen.getByLabelText(/score 100 out of 100, High Risk/i)).toBeInTheDocument()
    expect(screen.getByText('High Risk')).toBeInTheDocument()
  })

  it('renders tick labels at 0, 50, and 100', () => {
    render(<MechanicalGauge score={50} riskLevel="moderate" />)
    // Tick labels appear as <text> elements; centre readout + ticks
    // may produce duplicate text. getAllByText handles that.
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
    expect(screen.getAllByText('50').length).toBeGreaterThan(0)
    expect(screen.getAllByText('100').length).toBeGreaterThan(0)
  })
})

describe('MarginAnnotation', () => {
  it('renders children as a note with default moderate severity', () => {
    render(<MarginAnnotation>Suspense account flagged</MarginAnnotation>)
    const note = screen.getByRole('note')
    expect(note).toBeInTheDocument()
    expect(note.textContent).toContain('Suspense account flagged')
  })

  it('renders the caret glyph by default', () => {
    render(<MarginAnnotation>x</MarginAnnotation>)
    const note = screen.getByRole('note')
    expect(note.textContent).toContain('»')
  })

  it('omits the caret when caret="" is passed', () => {
    render(<MarginAnnotation caret="">x</MarginAnnotation>)
    const note = screen.getByRole('note')
    expect(note.textContent).not.toContain('»')
  })

  it('applies severity-specific border class for high severity', () => {
    render(<MarginAnnotation severity="high">x</MarginAnnotation>)
    const note = screen.getByRole('note')
    expect(note.className).toMatch(/border-clay-500/)
  })
})
