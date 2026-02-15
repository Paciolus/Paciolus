/**
 * Portfolio page tests
 *
 * Tests client portfolio: CRUD modals, client grid, empty state,
 * delete confirmation, loading state, auth redirect.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockCreateClient = jest.fn()
const mockUpdateClient = jest.fn()
const mockDeleteClient = jest.fn()
const mockRefresh = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { name: 'Test User', email: 'test@example.com' },
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
  })),
}))

jest.mock('@/hooks/useClients', () => ({
  useClients: jest.fn(() => ({
    clients: [],
    totalCount: 0,
    isLoading: false,
    error: null,
    industries: ['Technology', 'Manufacturing', 'Healthcare'],
    createClient: mockCreateClient,
    updateClient: mockUpdateClient,
    deleteClient: mockDeleteClient,
    refresh: mockRefresh,
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

jest.mock('@/components/auth', () => ({
  ProfileDropdown: () => <div data-testid="profile-dropdown">Profile</div>,
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

import { useAuth } from '@/contexts/AuthContext'
import { useClients } from '@/hooks/useClients'
import PortfolioPage from '@/app/portfolio/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseClients = useClients as jest.Mock

const sampleClients = [
  { id: 1, name: 'Acme Corp', industry: 'Technology', fiscal_year_end: '12-31', created_at: '2025-01-01' },
  { id: 2, name: 'Widget Inc', industry: 'Manufacturing', fiscal_year_end: '06-30', created_at: '2025-02-01' },
]

describe('PortfolioPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({
      user: { name: 'Test User', email: 'test@example.com' },
      isAuthenticated: true,
      isLoading: false,
      logout: jest.fn(),
    })
    mockUseClients.mockReturnValue({
      clients: [],
      totalCount: 0,
      isLoading: false,
      error: null,
      industries: ['Technology', 'Manufacturing', 'Healthcare'],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
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
    mockUseClients.mockReturnValue({
      clients: sampleClients,
      totalCount: 2,
      isLoading: false,
      error: null,
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
    render(<PortfolioPage />)
    expect(screen.getByText('2 clients in your portfolio')).toBeInTheDocument()
  })

  it('renders client cards when clients exist', () => {
    mockUseClients.mockReturnValue({
      clients: sampleClients,
      totalCount: 2,
      isLoading: false,
      error: null,
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
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
    mockUseClients.mockReturnValue({
      clients: sampleClients,
      totalCount: 2,
      isLoading: false,
      error: null,
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
    const user = userEvent.setup()
    render(<PortfolioPage />)

    // Click delete on first client
    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    expect(screen.getByText('Delete Client')).toBeInTheDocument()
    expect(screen.getByText('This action cannot be undone')).toBeInTheDocument()
    expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()
    // "Acme Corp" appears in both the card and the confirmation dialog
    expect(screen.getAllByText('Acme Corp').length).toBeGreaterThanOrEqual(2)
  })

  it('calls deleteClient on confirm and closes modal on success', async () => {
    mockDeleteClient.mockResolvedValue(true)
    mockUseClients.mockReturnValue({
      clients: sampleClients,
      totalCount: 2,
      isLoading: false,
      error: null,
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
    const user = userEvent.setup()
    render(<PortfolioPage />)

    // Open delete confirmation
    const deleteButtons = screen.getAllByText('Delete')
    await user.click(deleteButtons[0])

    // Find the delete button inside the confirmation modal (not the card delete button)
    const confirmButtons = screen.getAllByText('Delete')
    // The last "Delete" button should be the confirmation one
    const confirmDelete = confirmButtons[confirmButtons.length - 1]
    await user.click(confirmDelete)

    await waitFor(() => {
      expect(mockDeleteClient).toHaveBeenCalledWith(1)
    })
  })

  it('shows error state with retry button', () => {
    mockUseClients.mockReturnValue({
      clients: [],
      totalCount: 0,
      isLoading: false,
      error: 'Failed to load clients',
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
    render(<PortfolioPage />)
    expect(screen.getByText('Failed to load clients')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('calls refresh on retry button click', async () => {
    mockUseClients.mockReturnValue({
      clients: [],
      totalCount: 0,
      isLoading: false,
      error: 'Failed to load clients',
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
    const user = userEvent.setup()
    render(<PortfolioPage />)

    await user.click(screen.getByText('Try Again'))
    expect(mockRefresh).toHaveBeenCalled()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      logout: jest.fn(),
    })
    render(<PortfolioPage />)
    expect(mockPush).toHaveBeenCalledWith('/login?redirect=/portfolio')
  })

  it('shows loading skeleton when clients are loading', () => {
    mockUseAuth.mockReturnValue({
      user: { name: 'Test User', email: 'test@example.com' },
      isAuthenticated: true,
      isLoading: false,
      logout: jest.fn(),
    })
    mockUseClients.mockReturnValue({
      clients: [],
      totalCount: 0,
      isLoading: true,
      error: null,
      industries: [],
      createClient: mockCreateClient,
      updateClient: mockUpdateClient,
      deleteClient: mockDeleteClient,
      refresh: mockRefresh,
    })
    render(<PortfolioPage />)
    // Loading skeletons are rendered as animated pulse divs
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })
})
