/**
 * CommentThread component tests
 *
 * Tests: loading state, empty state, comment rendering, reply form,
 * submit button states, comment input.
 */
import { CommentThread } from '@/components/engagement/CommentThread'
import { render, screen, fireEvent } from '@/test-utils'

const mockFetchComments = jest.fn()
const mockCreateComment = jest.fn()
const mockDeleteComment = jest.fn()

jest.mock('@/hooks/useFollowUpComments', () => ({
  useFollowUpComments: () => ({
    comments: mockComments,
    isLoading: mockIsLoading,
    error: mockError,
    fetchComments: mockFetchComments,
    createComment: mockCreateComment,
    deleteComment: mockDeleteComment,
  }),
}))

let mockComments: any[] = []
let mockIsLoading = false
let mockError: string | null = null

describe('CommentThread', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockComments = []
    mockIsLoading = false
    mockError = null
  })

  it('shows loading state', () => {
    mockIsLoading = true
    render(<CommentThread itemId={1} />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows empty state when no comments', () => {
    render(<CommentThread itemId={1} />)
    expect(screen.getByText('No comments yet')).toBeInTheDocument()
  })

  it('shows error message', () => {
    mockError = 'Failed to load comments'
    render(<CommentThread itemId={1} />)
    expect(screen.getByText('Failed to load comments')).toBeInTheDocument()
  })

  it('renders comment text', () => {
    mockComments = [
      { id: 1, user_id: 10, author_name: 'Alice', comment_text: 'Test comment', created_at: '2026-01-15T10:00:00Z', parent_comment_id: null },
    ]
    render(<CommentThread itemId={1} />)
    expect(screen.getByText('Test comment')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })

  it('renders comment count in heading', () => {
    mockComments = [
      { id: 1, user_id: 10, author_name: 'Alice', comment_text: 'Comment 1', created_at: '2026-01-15T10:00:00Z', parent_comment_id: null },
      { id: 2, user_id: 11, author_name: 'Bob', comment_text: 'Comment 2', created_at: '2026-01-15T11:00:00Z', parent_comment_id: null },
    ]
    render(<CommentThread itemId={1} />)
    // The heading includes "Comments (2)" as inline text
    expect(screen.getByText(/Comments/)).toHaveTextContent('Comments (2)')
  })

  it('shows add comment input', () => {
    render(<CommentThread itemId={1} />)
    expect(screen.getByPlaceholderText('Add a comment...')).toBeInTheDocument()
  })

  it('shows Send button', () => {
    render(<CommentThread itemId={1} />)
    expect(screen.getByText('Send')).toBeInTheDocument()
  })

  it('disables Send when input is empty', () => {
    render(<CommentThread itemId={1} />)
    const sendBtn = screen.getByText('Send')
    expect(sendBtn).toBeDisabled()
  })

  it('fetches comments on mount', () => {
    render(<CommentThread itemId={42} />)
    expect(mockFetchComments).toHaveBeenCalledWith(42)
  })
})
