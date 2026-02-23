/**
 * Portfolio page tests
 *
 * Tests client portfolio: CRUD modals, client grid, empty state,
 * delete confirmation, loading state.
 *
 * Sprint 385: Updated to use WorkspaceContext (Phase LII refactor).
 * Auth redirect now handled by (workspace)/layout.tsx, not the page.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => '/portfolio',
}))

const mockCreateClient = jest.fn()
const mockUpdateClient = jest.fn()
const mockDeleteClient = jest.fn()
const mockRefreshClients = jest.fn()

jest.mock('@/contexts/WorkspaceContext', () => ({
  useWorkspaceContext: jest.fn(() => ({
    clients: [],
    clientsTotalCount: 0,
    clientsLoading: false,
    clientsError: null,
    industries: ['Technology', 'Manufacturing', 'Healthcare'],
    createClient: mockCreateClient,
    updateClient: mockUpdateClient,
    deleteClient: mockDeleteClient,
    refreshClients: mockRefreshClients,
    engagements: [],
    engagementsLoading: false,
    engagementsError: null,
    activeClient: null,
    setActiveClient: jest.fn(),
    activeEngagement: null,
    setActiveEngagement: jest.fn(),
    currentView: 'portfolio' as const,
    setCurrentView: jest.fn(),
    contextPaneCollapsed: true,
    toggleContextPane: jest.fn(),
    insightRailCollapsed: true,
    toggleInsightRail: jest.fn(),
    quickSwitcherOpen: false,
    setQuickSwitcherOpen: jest.fn(),
  })),
}))

jest.mock('@/components/portfolio', () => ({
  ClientCard: ({ client, onEdit, onDelete }: any) => (
    <div data-testid={`client-card-${client.id}`}>
      <span>{client.name}</span>
      <button onClick={() => onEdit(client)}>Edit</button>
      <button onClick={() => onDelete(client)}>Delete</button>
    </div>
  ),
  CreateClientModal: ({ isOpen, onClose }: any) =>
    isOpen ? <div data-testid="create-modal">Create Modal <button onClick={onClose}>Close</button></div> : null,
  EditClientModal: ({ isOpen, client, onClose }: any) =>
    isOpen ? <div data-testid="edit-modal">Edit {client?.name} <button onClick={onClose}>Close</button></div> : null,
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

import PortfolioPage from '@/app/(workspace)/portfolio/page'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

const mockUseWorkspaceContext = useWorkspaceContext as jest.Mock

const defaultContext = {
  clients: [],
  clientsTotalCount: 0,
  clientsLoading: false,
  clientsError: null,
  industries: ['Technology', 'Manufacturing', 'Healthcare'],
  createClient: mockCreateClient,
  updateClient: mockUpdateClient,
  deleteClient: mockDeleteClient,
  refreshClients: mockRefreshClients,
  engagements: [],
  engagementsLoading: false,
  engagementsError: null,
  activeClient: null,
  setActiveClient: jest.fn(),
  activeEngagement: null,
  setActiveEngagement: jest.fn(),
  currentView: 'portfolio' as const,
  setCurrentView: jest.fn(),
  contextPaneCollapsed: true,
  toggleContextPane: jest.fn(),
  insightRailCollapsed: true,
  toggleInsightRail: jest.fn(),
  quickSwitcherOpen: false,
  setQuickSwitcherOpen: jest.fn(),
}

const sampleClients = [
  { id: 1, name: 'Acme Corp', industry: 'Technology', fiscal_year_end: '12-31', created_at: '2025-01-01' },
  { id: 2, name: 'Widget Inc', industry: 'Manufacturing', fiscal_year_end: '06-30', created_at: '2025-02-01' },
]

describe('PortfolioPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseWorkspaceContext.mockReturnValue(defaultContext)
  })

  it('renders page header', () => {
    render(<PortfolioPage />)
    expect(screen.getByRole('heading', { name: 'Client Portfolio' })).toBeInTheDocument()
  })

  it('shows empty state when no clients', () => {
    render(<PortfolioPage />)
    expect(screen.getByText('No Clients Yet')).toBeInTheDocument()
    expect(screen.getByText('Add Your First Client')).toBeInTheDocument()
  })

  it('shows client count in subtitle', () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clients: sampleClients,
      clientsTotalCount: 2,
    })
    render(<PortfolioPage />)
    expect(screen.getByText('2 clients in your portfolio')).toBeInTheDocument()
  })

  it('renders client cards when clients exist', () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clients: sampleClients,
      clientsTotalCount: 2,
    })
    render(<PortfolioPage />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Widget Inc')).toBeInTheDocument()
  })

  it('opens create modal on New Client button click', async () => {
    const user = userEvent.setup()
    render(<PortfolioPage />)

    const newClientButton = screen.getByText('New Client')
    await user.click(newClientButton)

    expect(screen.getByTestId('create-modal')).toBeInTheDocument()
  })

  it('opens create modal from empty state CTA', async () => {
    const user = userEvent.setup()
    render(<PortfolioPage />)

    const addButton = screen.getByText('Add Your First Client')
    await user.click(addButton)

    expect(screen.getByTestId('create-modal')).toBeInTheDocument()
  })

  it('shows delete confirmation modal', async () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clients: sampleClients,
      clientsTotalCount: 2,
    })
    const user = userEvent.setup()
    render(<PortfolioPage />)

    // Click delete on first client
    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(screen.getByText('Delete Client')).toBeInTheDocument()
    expect(screen.getByText('This action cannot be undone')).toBeInTheDocument()
    expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()
    expect(screen.getAllByText('Acme Corp').length).toBeGreaterThanOrEqual(2)
  })

  it('calls deleteClient on confirm and closes modal on success', async () => {
    mockDeleteClient.mockResolvedValue(true)
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clients: sampleClients,
      clientsTotalCount: 2,
    })
    const user = userEvent.setup()
    render(<PortfolioPage />)

    // Open delete confirmation
    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    // The last "Delete" button should be the confirmation one
    const confirmButtons = screen.getAllByText('Delete')
    const confirmDelete = confirmButtons[confirmButtons.length - 1]
    await user.click(confirmDelete)

    await waitFor(() => {
      expect(mockDeleteClient).toHaveBeenCalledWith(1)
    })
  })

  it('shows error state with retry button', () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clientsError: 'Failed to load clients',
    })
    render(<PortfolioPage />)
    expect(screen.getByText('Failed to load clients')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('calls refreshClients on retry button click', async () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clientsError: 'Failed to load clients',
    })
    const user = userEvent.setup()
    render(<PortfolioPage />)

    await user.click(screen.getByText('Try Again'))
    expect(mockRefreshClients).toHaveBeenCalled()
  })

  it('shows loading skeleton when clients are loading', () => {
    mockUseWorkspaceContext.mockReturnValue({
      ...defaultContext,
      clientsLoading: true,
    })
    render(<PortfolioPage />)
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })
})
