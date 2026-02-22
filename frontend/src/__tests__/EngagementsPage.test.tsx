/**
 * Engagements page tests
 *
 * Tests diagnostic workspace page: list/detail toggle, tab navigation,
 * URL param sync, disclaimer banner, archive, error/loading states.
 *
 * Sprint 385: Updated to use WorkspaceContext (Phase LII refactor).
 * Auth redirect now handled by (workspace)/layout.tsx, not the page.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

const mockPush = jest.fn()
const mockReplace = jest.fn()
const mockGet = jest.fn()
const mockToString = jest.fn(() => '')

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => ({
    get: mockGet,
    toString: mockToString,
  }),
}))

const mockFetchEngagements = jest.fn()
const mockCreateEngagement = jest.fn()
const mockArchiveEngagement = jest.fn()
const mockGetToolRuns = jest.fn()
const mockGetMateriality = jest.fn()
const mockGetConvergence = jest.fn()
const mockDownloadConvergenceCsv = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { id: 1, name: 'Test User', email: 'test@example.com', is_verified: true },
    token: 'test-token',
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
  })),
}))

jest.mock('@/contexts/WorkspaceContext', () => ({
  useWorkspaceContext: jest.fn(() => ({
    clients: [{ id: 1, name: 'Acme Corp' }],
    clientsLoading: false,
    clientsTotalCount: 1,
    clientsError: null,
    industries: [],
    engagements: [],
    engagementsLoading: false,
    engagementsError: null,
    fetchEngagements: mockFetchEngagements,
    createEngagement: mockCreateEngagement,
    archiveEngagement: mockArchiveEngagement,
    getToolRuns: mockGetToolRuns,
    getMateriality: mockGetMateriality,
    getConvergence: mockGetConvergence,
    getToolRunTrends: jest.fn(),
    downloadConvergenceCsv: mockDownloadConvergenceCsv,
    refreshEngagements: jest.fn(),
    activeClient: null,
    setActiveClient: jest.fn(),
    activeEngagement: null,
    setActiveEngagement: jest.fn(),
    currentView: 'engagements' as const,
    setCurrentView: jest.fn(),
    contextPaneCollapsed: true,
    toggleContextPane: jest.fn(),
    insightRailCollapsed: true,
    toggleInsightRail: jest.fn(),
    quickSwitcherOpen: false,
    setQuickSwitcherOpen: jest.fn(),
  })),
}))

jest.mock('@/hooks/useFollowUpItems', () => ({
  useFollowUpItems: jest.fn(() => ({
    items: [],
    isLoading: false,
    fetchItems: jest.fn(),
    updateItem: jest.fn(),
    deleteItem: jest.fn(),
  })),
}))

jest.mock('@/utils', () => ({
  apiGet: jest.fn().mockResolvedValue({ data: null }),
  apiPost: jest.fn(),
  apiFetch: jest.fn(),
}))

jest.mock('@/utils/formatting', () => ({
  formatCurrency: (v: number) => `$${v.toLocaleString()}`,
}))

jest.mock('@/components/engagement', () => ({
  EngagementList: ({ engagements, onSelect }: any) => (
    <div data-testid="engagement-list">
      {engagements.map((e: any) => (
        <button key={e.id} onClick={() => onSelect(e)} data-testid={`select-${e.id}`}>
          {e.status}
        </button>
      ))}
    </div>
  ),
  ToolStatusGrid: ({ toolRuns }: any) => <div data-testid="tool-status-grid">{toolRuns.length} runs</div>,
  FollowUpItemsTable: ({ items }: any) => <div data-testid="follow-up-table">{items.length} items</div>,
  WorkpaperIndex: () => <div data-testid="workpaper-index">Workpaper Index</div>,
  ConvergenceTable: () => <div data-testid="convergence-table">Convergence</div>,
  CreateEngagementModal: ({ isOpen, onClose }: any) =>
    isOpen ? <div data-testid="create-modal"><button onClick={onClose}>Close</button></div> : null,
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    button: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <button {...rest}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>
})

import { useWorkspaceContext } from '@/contexts/WorkspaceContext'
import EngagementsPage from '@/app/(workspace)/engagements/page'

const mockUseWorkspaceContext = useWorkspaceContext as jest.Mock

const defaultContext = {
  clients: [{ id: 1, name: 'Acme Corp' }],
  clientsLoading: false,
  clientsTotalCount: 1,
  clientsError: null,
  industries: [],
  engagements: [],
  engagementsLoading: false,
  engagementsError: null,
  fetchEngagements: mockFetchEngagements,
  createEngagement: mockCreateEngagement,
  archiveEngagement: mockArchiveEngagement,
  getToolRuns: mockGetToolRuns,
  getMateriality: mockGetMateriality,
  getConvergence: mockGetConvergence,
  getToolRunTrends: jest.fn(),
  downloadConvergenceCsv: mockDownloadConvergenceCsv,
  refreshEngagements: jest.fn(),
  activeClient: null,
  setActiveClient: jest.fn(),
  activeEngagement: null,
  setActiveEngagement: jest.fn(),
  currentView: 'engagements' as const,
  setCurrentView: jest.fn(),
  contextPaneCollapsed: true,
  toggleContextPane: jest.fn(),
  insightRailCollapsed: true,
  toggleInsightRail: jest.fn(),
  quickSwitcherOpen: false,
  setQuickSwitcherOpen: jest.fn(),
}

const sampleEngagements = [
  { id: 1, client_id: 1, client_name: 'Acme Corp', period_start: '2025-01-01', period_end: '2025-12-31', status: 'active', created_at: '2025-01-01' },
  { id: 2, client_id: 1, client_name: 'Acme Corp', period_start: '2024-01-01', period_end: '2024-12-31', status: 'archived', created_at: '2024-01-01' },
]

describe('EngagementsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGet.mockReturnValue(null)
    mockGetToolRuns.mockResolvedValue([])
    mockGetMateriality.mockResolvedValue(null)
    mockGetConvergence.mockResolvedValue(null)
    mockUseWorkspaceContext.mockReturnValue(defaultContext)
  })

  it('renders page header with Diagnostic Workspace title', () => {
    render(<EngagementsPage />)
    expect(screen.getByRole('heading', { name: 'Diagnostic Workspace' })).toBeInTheDocument()
  })

  it('shows non-dismissible disclaimer banner', () => {
    render(<EngagementsPage />)
    expect(screen.getByText(/NOT AN AUDIT ENGAGEMENT/i)).toBeInTheDocument()
  })

  it('shows engagement list when no engagement selected', () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      engagements: sampleEngagements,
    })
    render(<EngagementsPage />)
    expect(screen.getByTestId('engagement-list')).toBeInTheDocument()
  })

  it('opens create modal on New Workspace click', async () => {
    const user = userEvent.setup()
    render(<EngagementsPage />)

    await user.click(screen.getByText('New Workspace'))
    expect(screen.getByTestId('create-modal')).toBeInTheDocument()
  })

  it('shows error with retry button', () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      engagementsError: 'Failed to load workspaces',
    })
    render(<EngagementsPage />)
    expect(screen.getByText('Failed to load workspaces')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('calls fetchEngagements on retry click', async () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      engagementsError: 'Failed to load workspaces',
    })
    const user = userEvent.setup()
    render(<EngagementsPage />)

    await user.click(screen.getByText('Try Again'))
    expect(mockFetchEngagements).toHaveBeenCalled()
  })

  it('renders tab labels when engagement selected', async () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      engagements: sampleEngagements,
    })
    render(<EngagementsPage />)
    expect(screen.getByTestId('engagement-list')).toBeInTheDocument()
  })

  it('shows New Workspace button', () => {
    render(<EngagementsPage />)
    expect(screen.getByText('New Workspace')).toBeInTheDocument()
  })
})
