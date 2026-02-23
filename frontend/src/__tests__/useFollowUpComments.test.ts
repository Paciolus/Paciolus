/**
 * Sprint 276: useFollowUpComments hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useFollowUpComments } from '@/hooks/useFollowUpComments'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiPatch = jest.fn()
const mockApiDelete = jest.fn()
const mockIsAuthError = jest.fn(() => false)

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
  isAuthError: (...args: unknown[]) => mockIsAuthError(...args),
}))


const mockUseAuth = useAuth as jest.Mock

const mockComment = {
  id: 1,
  follow_up_item_id: 5,
  content: 'Initial review completed',
  author: 'auditor@test.com',
  created_at: '2026-02-10T10:00:00Z',
  updated_at: '2026-02-10T10:00:00Z',
}

describe('useFollowUpComments', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
    mockApiGet.mockResolvedValue({
      ok: true,
      data: [mockComment],
    })
  })

  it('initializes with empty comments', () => {
    const { result } = renderHook(() => useFollowUpComments())
    expect(result.current.comments).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchComments calls apiGet with item ID', async () => {
    const { result } = renderHook(() => useFollowUpComments())

    await act(async () => {
      await result.current.fetchComments(5)
    })

    expect(mockApiGet).toHaveBeenCalledWith(
      '/follow-up-items/5/comments',
      'test-token',
      { skipCache: true }
    )
    expect(result.current.comments).toEqual([mockComment])
  })

  it('fetchComments handles auth error', async () => {
    mockIsAuthError.mockReturnValue(true)
    mockApiGet.mockResolvedValue({ ok: false, error: 'Unauthorized', status: 401 })

    const { result } = renderHook(() => useFollowUpComments())

    await act(async () => {
      await result.current.fetchComments(5)
    })

    expect(mockIsAuthError).toHaveBeenCalledWith(401)
    expect(result.current.error).toBe('Session expired. Please log in again.')
  })

  it('createComment calls apiPost and appends to comments', async () => {
    const newComment = { ...mockComment, id: 2, content: 'Follow-up note' }
    mockApiPost.mockResolvedValue({ ok: true, data: newComment })

    const { result } = renderHook(() => useFollowUpComments())

    // Populate with existing comments
    await act(async () => {
      await result.current.fetchComments(5)
    })

    let created: unknown
    await act(async () => {
      created = await result.current.createComment(5, { content: 'Follow-up note' })
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/follow-up-items/5/comments',
      'test-token',
      expect.objectContaining({ content: 'Follow-up note' })
    )
    expect(created).toEqual(newComment)
    // New comment appended (not prepended)
    expect(result.current.comments).toHaveLength(2)
    expect(result.current.comments[1]).toEqual(newComment)
  })

  it('updateComment calls apiPatch and replaces comment in list', async () => {
    const updated = { ...mockComment, content: 'Revised note' }
    mockApiPatch.mockResolvedValue({ ok: true, data: updated })

    const { result } = renderHook(() => useFollowUpComments())

    // Populate
    await act(async () => {
      await result.current.fetchComments(5)
    })

    let returnedComment: unknown
    await act(async () => {
      returnedComment = await result.current.updateComment(1, { content: 'Revised note' })
    })

    expect(mockApiPatch).toHaveBeenCalledWith(
      '/comments/1',
      'test-token',
      expect.objectContaining({ content: 'Revised note' })
    )
    expect(returnedComment).toEqual(updated)
    expect(result.current.comments[0].content).toBe('Revised note')
  })

  it('deleteComment calls apiDelete and removes from list', async () => {
    mockApiDelete.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useFollowUpComments())

    // Populate
    await act(async () => {
      await result.current.fetchComments(5)
    })
    expect(result.current.comments).toHaveLength(1)

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.deleteComment(1)
    })

    expect(mockApiDelete).toHaveBeenCalledWith('/comments/1', 'test-token')
    expect(success).toBe(true)
    expect(result.current.comments).toHaveLength(0)
  })

  it('returns null/false when not authenticated', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useFollowUpComments())

    let createResult: unknown
    let deleteResult: boolean | undefined
    await act(async () => {
      createResult = await result.current.createComment(5, { content: 'test' })
    })
    await act(async () => {
      deleteResult = await result.current.deleteComment(1)
    })

    expect(createResult).toBeNull()
    expect(deleteResult).toBe(false)
    expect(result.current.error).toBe('Not authenticated')
    expect(mockApiPost).not.toHaveBeenCalled()
    expect(mockApiDelete).not.toHaveBeenCalled()
  })

  it('error state set on API failure', async () => {
    mockIsAuthError.mockReturnValue(false)
    mockApiPost.mockResolvedValue({ ok: false, error: 'Validation failed' })

    const { result } = renderHook(() => useFollowUpComments())

    let created: unknown
    await act(async () => {
      created = await result.current.createComment(5, { content: '' })
    })

    expect(created).toBeNull()
    expect(result.current.error).toBe('Validation failed')
  })
})
