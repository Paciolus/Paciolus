/**
 * Sprint 889 (CEO brief 14D, review TQ-09): the JE page's success state, built
 * from a response that is valid against the backend's JETestingResponse
 * (checked by backend/tests/test_sprint_889_frontend_fixtures_match_schemas.py)
 * and rendered with the real score card and result grid — not stubs fed empty
 * objects the backend would reject.
 */
import JournalEntryTestingPage from '@/app/tools/journal-entry-testing/page'
import { useJETesting } from '@/hooks/useJETesting'
import { render, screen } from '@/test-utils'
import jeTestingResponse from './fixtures/je-testing-response.json'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'enterprise' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useJETesting', () => ({ useJETesting: jest.fn() }))

jest.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: jest.fn(() => ({
    isDragging: false, fileInputRef: { current: null },
    handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: jest.fn(),
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, handleExportMemo: jest.fn(), handleExportCSV: jest.fn() })),
}))

// Real JEScoreCard and TestResultGrid; only the heavy or unrelated panels are stubbed.
jest.mock('@/components/jeTesting', () => ({
  ...jest.requireActual('@/components/jeTesting'),
  BenfordChart: () => <div data-testid="benford-chart">Benford</div>,
  FlaggedEntryTable: () => <div data-testid="flagged-table">Flagged</div>,
  SamplingPanel: () => <div data-testid="sampling-panel">Sampling</div>,
  HolidayCalendarPanel: () => <div data-testid="holiday-calendar-panel">Holiday calendar</div>,
}))
jest.mock('@/components/jeTesting/BenfordChart', () => ({
  BenfordChart: () => <div data-testid="benford-chart">Benford</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractJEProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: () => ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useInView: () => true,
  useReducedMotion: () => true,
  useMotionValue: (v: number) => ({ get: () => v, set: jest.fn(), on: () => () => {} }),
  useSpring: (v: unknown) => v,
  useTransform: () => 0,
  animate: () => ({ stop: jest.fn() }),
}))

describe('JournalEntryTestingPage — success state from a valid response', () => {
  beforeEach(() => {
    ;(useJETesting as jest.Mock).mockReturnValue({
      status: 'success', error: null, runTests: jest.fn(), reset: jest.fn(), result: jeTestingResponse,
    })
  })

  it('renders the real score card from the composite score', () => {
    render(<JournalEntryTestingPage />)
    expect(screen.getByText(/19 tests analyzed 1,200 GL lines/)).toBeInTheDocument()
    expect(screen.getByText('36')).toBeInTheDocument()
    expect(screen.getByText('3.0%')).toBeInTheDocument()
  })

  it('renders the real result grid with the flagged test', () => {
    render(<JournalEntryTestingPage />)
    expect(screen.getAllByText('Round Dollar Amounts').length).toBeGreaterThan(0)
  })
})
