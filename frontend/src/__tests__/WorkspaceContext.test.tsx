/**
 * Sprint 548: WorkspaceContext tests.
 */
import { renderHook, act } from '@testing-library/react'
import { WorkspaceProvider, useWorkspaceContext } from '@/contexts/WorkspaceContext'

const mockClients = [
  { id: 1, user_id: 1, name: 'Acme Corp', industry: 'technology' as const, fiscal_year_end: '12-31', created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z', settings: '{}' },
]
const mockEngagements = [
  { id: 1, client_id: 1, status: 'active' as const, period_start: '2025-01-01', period_end: '2025-12-31', materiality_basis: null, materiality_percentage: null, materiality_amount: null, performance_materiality_factor: 0.75, trivial_threshold_factor: 0.05, created_by: 1, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
]

jest.mock('@/hooks/useClients', () => ({
  useClients: () => ({
    clients: mockClients,
    totalCount: 1,
    isLoading: false,
    error: null,
    industries: [{ value: 'technology', label: 'Technology' }],
    createClient: jest.fn(),
    updateClient: jest.fn(),
    deleteClient: jest.fn(),
    refresh: jest.fn(),
  }),
}))

jest.mock('@/hooks/useEngagement', () => ({
  useEngagement: () => ({
    engagements: mockEngagements,
    isLoading: false,
    error: null,
    fetchEngagements: jest.fn(),
    createEngagement: jest.fn(),
    archiveEngagement: jest.fn(),
    getToolRuns: jest.fn().mockResolvedValue([]),
    getMateriality: jest.fn().mockResolvedValue(null),
    getConvergence: jest.fn().mockResolvedValue(null),
    getToolRunTrends: jest.fn().mockResolvedValue([]),
    downloadConvergenceCsv: jest.fn(),
    refresh: jest.fn(),
  }),
}))

function wrapper({ children }: { children: React.ReactNode }) {
  return <WorkspaceProvider>{children}</WorkspaceProvider>
}

describe('WorkspaceContext', () => {
  it('provides client data to consumers', () => {
    const { result } = renderHook(() => useWorkspaceContext(), { wrapper })
    expect(result.current.clients).toEqual(mockClients)
    expect(result.current.clientsTotalCount).toBe(1)
    expect(result.current.clientsLoading).toBe(false)
  })

  it('provides engagement data to consumers', () => {
    const { result } = renderHook(() => useWorkspaceContext(), { wrapper })
    expect(result.current.engagements).toEqual(mockEngagements)
    expect(result.current.engagementsLoading).toBe(false)
  })

  it('throws when used outside of provider', () => {
    // Suppress console.error for this test
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => {
      renderHook(() => useWorkspaceContext())
    }).toThrow('useWorkspaceContext must be used within a WorkspaceProvider')
    spy.mockRestore()
  })

  it('manages active client selection', () => {
    const { result } = renderHook(() => useWorkspaceContext(), { wrapper })
    expect(result.current.activeClient).toBeNull()

    act(() => {
      result.current.setActiveClient(mockClients[0])
    })
    expect(result.current.activeClient).toEqual(mockClients[0])
  })

  it('manages active engagement selection', () => {
    const { result } = renderHook(() => useWorkspaceContext(), { wrapper })
    expect(result.current.activeEngagement).toBeNull()

    act(() => {
      result.current.setActiveEngagement(mockEngagements[0])
    })
    expect(result.current.activeEngagement).toEqual(mockEngagements[0])
  })

  it('toggles context pane', () => {
    const { result } = renderHook(() => useWorkspaceContext(), { wrapper })
    expect(result.current.contextPaneCollapsed).toBe(true)

    act(() => {
      result.current.toggleContextPane()
    })
    expect(result.current.contextPaneCollapsed).toBe(false)
  })

  it('manages current view state', () => {
    const { result } = renderHook(() => useWorkspaceContext(), { wrapper })
    expect(result.current.currentView).toBe('portfolio')

    act(() => {
      result.current.setCurrentView('engagements')
    })
    expect(result.current.currentView).toBe('engagements')
  })
})
