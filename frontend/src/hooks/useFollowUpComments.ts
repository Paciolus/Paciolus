'use client';

/**
 * useFollowUpComments Hook — Sprint 113
 *
 * CRUD operations for follow-up item comments.
 * Narrative-only, Zero-Storage compliant.
 */

import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiGet, apiPost, apiPatch, apiDelete, isAuthError } from '@/utils';
import type {
  FollowUpComment,
  FollowUpCommentCreateInput,
  FollowUpCommentUpdateInput,
} from '@/types/engagement';

export interface UseFollowUpCommentsReturn {
  comments: FollowUpComment[];
  isLoading: boolean;
  error: string | null;
  fetchComments: (itemId: number) => Promise<void>;
  createComment: (itemId: number, data: FollowUpCommentCreateInput) => Promise<FollowUpComment | null>;
  updateComment: (commentId: number, data: FollowUpCommentUpdateInput) => Promise<FollowUpComment | null>;
  deleteComment: (commentId: number) => Promise<boolean>;
}

export function useFollowUpComments(): UseFollowUpCommentsReturn {
  const { token, isAuthenticated } = useAuth();

  const [comments, setComments] = useState<FollowUpComment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchComments = useCallback(async (itemId: number) => {
    if (!isAuthenticated || !token) {
      setComments([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    const { data, error: apiError, ok, status: httpStatus } = await apiGet<FollowUpComment[]>(
      `/follow-up-items/${itemId}/comments`,
      token,
      { skipCache: true },
    );

    if (!ok) {
      if (isAuthError(httpStatus)) {
        setError('Session expired. Please log in again.');
      } else {
        setError(apiError || 'Failed to fetch comments');
      }
      setIsLoading(false);
      return;
    }

    setComments(data || []);
    setIsLoading(false);
  }, [isAuthenticated, token]);

  const createComment = useCallback(async (
    itemId: number,
    data: FollowUpCommentCreateInput,
  ): Promise<FollowUpComment | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setError(null);

    const { data: newComment, error: apiError, ok } = await apiPost<FollowUpComment>(
      `/follow-up-items/${itemId}/comments`,
      token,
      data as unknown as Record<string, unknown>,
    );

    if (!ok || !newComment) {
      setError(apiError || 'Failed to create comment');
      return null;
    }

    setComments(prev => [...prev, newComment]);
    return newComment;
  }, [isAuthenticated, token]);

  const updateComment = useCallback(async (
    commentId: number,
    data: FollowUpCommentUpdateInput,
  ): Promise<FollowUpComment | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setError(null);

    const { data: updated, error: apiError, ok } = await apiPatch<FollowUpComment>(
      `/comments/${commentId}`,
      token,
      data as unknown as Record<string, unknown>,
    );

    if (!ok || !updated) {
      setError(apiError || 'Failed to update comment');
      return null;
    }

    setComments(prev => prev.map(c => c.id === commentId ? updated : c));
    return updated;
  }, [isAuthenticated, token]);

  const deleteComment = useCallback(async (commentId: number): Promise<boolean> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return false;
    }

    setError(null);

    const { error: apiError, ok } = await apiDelete(`/comments/${commentId}`, token);

    if (!ok) {
      setError(apiError || 'Failed to delete comment');
      return false;
    }

    setComments(prev => prev.filter(c => c.id !== commentId));
    return true;
  }, [isAuthenticated, token]);

  return {
    comments,
    isLoading,
    error,
    fetchComments,
    createComment,
    updateComment,
    deleteComment,
  };
}
