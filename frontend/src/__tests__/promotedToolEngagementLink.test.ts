/**
 * Sprint 791: the six promoted tools' hooks must send `engagement_id`.
 *
 * Sprint 787b wired the six backends to accept `engagement_id` in the request
 * body, and nothing in the product put it there — none of these hooks contained
 * the string `engagement` at all. So a practitioner working inside an active
 * engagement produced runs that were filed nowhere, and the workpaper index,
 * the Anomaly Summary coverage fraction and the completion gate were counting a
 * population the UI could not populate.
 *
 * These tests assert the property **through the hook**, by inspecting what
 * reached `fetch`. That matters more than it sounds: the tell that Sprint 787b
 * was incomplete is that its backend tests constructed `engagement_id` in the
 * payload themselves. A test that supplies the thing the product is supposed to
 * supply proves nothing about the product.
 *
 * Scope note: the nine testing tools behind `createTestingHook` were *not*
 * affected. They delegate to `useAuditUpload`, which has auto-injected the
 * field since Sprint 103. `createTestingHook.ts` having no engagement
 * references is evidence of delegation, not of a defect.
 */
import { renderHook, act } from '@testing-library/react'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useBookToTax } from '@/hooks/useBookToTax'
import { useCashFlowProjector } from '@/hooks/useCashFlowProjector'
import { useForm1099 } from '@/hooks/useForm1099'
import { useIntercompanyElimination } from '@/hooks/useIntercompanyElimination'
import { useSOD } from '@/hooks/useSOD'
import { useW2Reconciliation } from '@/hooks/useW2Reconciliation'

const mockFetch = jest.fn()
global.fetch = mockFetch

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({ token: 'test-token', user: { is_verified: true } })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))

// Keep the real module — cachePlugin.ts imports hours()/minutes() from it and
// a wholesale mock breaks the apiClient import chain.
jest.mock('@/utils/constants', () => ({
  ...jest.requireActual('@/utils/constants'),
  API_URL: 'http://localhost:8000',
}))

const mockEngagementContext = useOptionalEngagementContext as jest.Mock

/** One minimal, schema-valid payload per tool, plus the call that posts it. */
const TOOLS = [
  {
    name: 'Segregation of Duties',
    endpoint: '/audit/sod/analyze',
    useHook: useSOD,
    run: (api: ReturnType<typeof useSOD>) =>
      api.analyze({ user_assignments: [], role_permissions: [], extra_rules: [] }),
  },
  {
    name: 'Intercompany Elimination',
    endpoint: '/audit/intercompany-elimination',
    useHook: useIntercompanyElimination,
    run: (api: ReturnType<typeof useIntercompanyElimination>) =>
      api.analyze({ entities: [], tolerance: '1.00' }),
  },
  {
    name: 'W-2/W-3 Reconciliation',
    endpoint: '/audit/w2-reconciliation',
    useHook: useW2Reconciliation,
    run: (api: ReturnType<typeof useW2Reconciliation>) =>
      api.analyze({
        tax_year: 2025,
        employees: [],
        w2_drafts: [],
        form_941_quarters: [],
        tolerance: '1.00',
      }),
  },
  {
    name: 'Form 1099 Preparation',
    endpoint: '/audit/form-1099',
    useHook: useForm1099,
    run: (api: ReturnType<typeof useForm1099>) =>
      api.analyze({ tax_year: 2025, vendors: [], payments: [] }),
  },
  {
    name: 'Book-to-Tax Reconciliation',
    endpoint: '/audit/book-to-tax',
    useHook: useBookToTax,
    run: (api: ReturnType<typeof useBookToTax>) =>
      api.analyze({
        tax_year: 2025,
        book_pretax_income: '0',
        total_assets: '0',
        federal_tax_rate: '0.21',
        state_tax_rate: '0',
        adjustments: [],
        rollforward: { beginning_dta: '0', beginning_dtl: '0' },
      }),
  },
  {
    name: 'Cash Flow Projector',
    endpoint: '/audit/cash-flow-projector',
    useHook: useCashFlowProjector,
    run: (api: ReturnType<typeof useCashFlowProjector>) =>
      api.project({
        opening_balance: '0',
        start_date: '2026-01-01',
        ar_aging: { current: '0', days_1_30: '0', days_31_60: '0', days_61_90: '0', days_over_90: '0' },
        ap_aging: { current: '0', days_1_30: '0', days_31_60: '0', days_61_90: '0', days_over_90: '0' },
        recurring_flows: [],
        min_safe_cash: null,
      }),
  },
] as const

/** The body that actually reached fetch, parsed. */
function postedBody(): Record<string, unknown> {
  expect(mockFetch).toHaveBeenCalled()
  const [, init] = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
  return JSON.parse(init.body as string)
}

function postedUrl(): string {
  const [url] = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
  return url as string
}

describe('Sprint 791: promoted-tool hooks carry the engagement link', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // jest.clearAllMocks() does not reset mockReturnValue — re-set every time.
    mockEngagementContext.mockReturnValue(null)
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({}),
    })
  })

  describe.each(TOOLS.map((t) => [t.name, t] as const))('%s', (_name, tool) => {
    it('sends engagement_id when an engagement is active', async () => {
      const refreshToolRuns = jest.fn()
      const triggerLinkToast = jest.fn()
      mockEngagementContext.mockReturnValue({
        engagementId: 42,
        refreshToolRuns,
        triggerLinkToast,
      })

      const { result } = renderHook(() => tool.useHook())
      await act(async () => { await tool.run(result.current as any) })

      expect(postedUrl()).toContain(tool.endpoint)
      expect(postedBody()).toMatchObject({ engagement_id: 42 })
    })

    it('omits engagement_id when no engagement is active', async () => {
      mockEngagementContext.mockReturnValue(null)

      const { result } = renderHook(() => tool.useHook())
      await act(async () => { await tool.run(result.current as any) })

      // undefined must not survive JSON.stringify — an explicit null would be
      // a different thing on the wire and Optional[int] would reject it.
      expect(postedBody()).not.toHaveProperty('engagement_id')
    })

    it('refreshes the workspace after a successful linked run', async () => {
      const refreshToolRuns = jest.fn()
      const triggerLinkToast = jest.fn()
      mockEngagementContext.mockReturnValue({
        engagementId: 7,
        refreshToolRuns,
        triggerLinkToast,
      })

      const { result } = renderHook(() => tool.useHook())
      await act(async () => { await tool.run(result.current as any) })

      // Mirrors useAuditUpload: without this the workpaper list the
      // practitioner is looking at still shows the pre-run state.
      expect(refreshToolRuns).toHaveBeenCalled()
      expect(triggerLinkToast).toHaveBeenCalledWith(_name)
    })

    it('does not refresh the workspace when there is no engagement', async () => {
      const refreshToolRuns = jest.fn()
      const triggerLinkToast = jest.fn()
      mockEngagementContext.mockReturnValue({
        engagementId: null,
        refreshToolRuns,
        triggerLinkToast,
      })

      const { result } = renderHook(() => tool.useHook())
      await act(async () => { await tool.run(result.current as any) })

      expect(refreshToolRuns).not.toHaveBeenCalled()
      expect(triggerLinkToast).not.toHaveBeenCalled()
    })
  })

  it('covers every tool Sprint 787b wired', () => {
    // Sprint 787b wired exactly six routes. If a seventh is wired without a
    // hook case here, the sprint's acceptance bar silently stops covering it —
    // the same failure that left the original six unwired behind a sprint
    // marked complete.
    expect(TOOLS.map((t) => t.endpoint).sort()).toEqual(
      [
        '/audit/book-to-tax',
        '/audit/cash-flow-projector',
        '/audit/form-1099',
        '/audit/intercompany-elimination',
        '/audit/sod/analyze',
        '/audit/w2-reconciliation',
      ].sort()
    )
  })
})
