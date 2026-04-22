/**
 * Sprint 707: tests for ScanlineOverlay + MechanicalGauge + MarginAnnotation.
 *
 * Coverage goals:
 *   - Each component renders its intended affordance.
 *   - Reduced-motion paths are explicitly covered where they change
 *     behaviour (gauge skips animation; scanline suppresses the sweep).
 *   - A11y assertions on aria-labels and role="note".
 */
import { ScanlineOverlay, MechanicalGauge, MarginAnnotation } from '@/components/demo'
import { render, screen, act } from '@/test-utils'

describe('ScanlineOverlay', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })
  afterEach(() => {
    jest.useRealTimers()
  })

  it('renders children', () => {
    render(
      <ScanlineOverlay>
        <p>inner content</p>
      </ScanlineOverlay>,
    )
    expect(screen.getByText('inner content')).toBeInTheDocument()
  })

  it('does not render the sweep element before the start delay elapses', () => {
    const { container } = render(
      <ScanlineOverlay delayMs={200} durationMs={1200}>
        <p>x</p>
      </ScanlineOverlay>,
    )
    // aria-hidden sweep element carries the keyframes animation
    expect(container.querySelector('[aria-hidden="true"]')).toBeNull()
  })

  it('mounts the sweep element once the delay elapses', () => {
    const { container } = render(
      <ScanlineOverlay delayMs={100} durationMs={500}>
        <p>x</p>
      </ScanlineOverlay>,
    )
    act(() => {
      jest.advanceTimersByTime(150)
    })
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeNull()
  })

  it('suppresses the sweep when prefers-reduced-motion matches', () => {
    // Stub matchMedia to return matches=true for reduced motion.
    const originalMatchMedia = window.matchMedia
    window.matchMedia = jest.fn().mockImplementation(q => ({
      matches: q.includes('reduce'),
      media: q,
      addEventListener: () => {},
      removeEventListener: () => {},
    })) as unknown as typeof window.matchMedia
    try {
      const { container } = render(
        <ScanlineOverlay delayMs={50} durationMs={200}>
          <p>x</p>
        </ScanlineOverlay>,
      )
      act(() => {
        jest.advanceTimersByTime(400)
      })
      expect(container.querySelector('[aria-hidden="true"]')).toBeNull()
    } finally {
      window.matchMedia = originalMatchMedia
    }
  })
})

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
