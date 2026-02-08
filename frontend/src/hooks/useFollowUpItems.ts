/**
 * Paciolus useFollowUpItems Hook
 * Sprint 100: Follow-Up Items UI
 *
 * CRUD hook for follow-up items, following useEngagement pattern.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Follow-up item data fetched from API, stored in React state only
 * - Narrative descriptions only — no account numbers, amounts, or PII
 */

'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiGet, apiPost, apiPut, apiDelete, isAuthError } from '@/utils';
import type {
  FollowUpItem,
  FollowUpItemCreateInput,
  FollowUpItemUpdateInput,
  FollowUpSummary,
} from '@/types/engagement';

export interface UseFollowUpItemsReturn {
  items: FollowUpItem[];
  summary: FollowUpSummary | null;
  isLoading: boolean;
  error: string | null;
  fetchItems: (engagementId: number, severity?: string, disposition?: string, toolSource?: string) => Promise<void>;
  createItem: (engagementId: number, data: FollowUpItemCreateInput) => Promise<FollowUpItem | null>;
  updateItem: (itemId: number, data: FollowUpItemUpdateInput) => Promise<FollowUpItem | null>;
  deleteItem: (itemId: number) => Promise<boolean>;
  fetchSummary: (engagementId: number) => Promise<FollowUpSummary | null>;
}

export function useFollowUpItems(): UseFollowUpItemsReturn {
  const { token, isAuthenticated } = useAuth();

  const [items, setItems] = useState<FollowUpItem[]>([]);
  const [summary, setSummary] = useState<FollowUpSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async (
    engagementId: number,
    severity?: string,
    disposition?: string,
    toolSource?: string,
  ) => {
    if (!isAuthenticated || !token) {
      setItems([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (disposition) params.append('disposition', disposition);
    if (toolSource) params.append('tool_source', toolSource);

    const qs = params.toString();
    const url = `/engagements/${engagementId}/follow-up-items${qs ? `?${qs}` : ''}`;

    const { data, error: apiError, ok, status: httpStatus } = await apiGet<FollowUpItem[]>(
      url,
      token,
      { skipCache: true },
    );

    if (!ok) {
      if (isAuthError(httpStatus)) {
        setError('Session expired. Please log in again.');
      } else {
        setError(apiError || 'Failed to fetch follow-up items');
      }
      setIsLoading(false);
      return;
    }

    setItems(data || []);
    setIsLoading(false);
  }, [isAuthenticated, token]);

  const createItem = useCallback(async (
    engagementId: number,
    data: FollowUpItemCreateInput,
  ): Promise<FollowUpItem | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setIsLoading(true);
    setError(null);

    const { data: newItem, error: apiError, ok } = await apiPost<FollowUpItem>(
      `/engagements/${engagementId}/follow-up-items`,
      token,
      data as unknown as Record<string, unknown>,
    );

    if (!ok || !newItem) {
      setError(apiError || 'Failed to create follow-up item');
      setIsLoading(false);
      return null;
    }

    setItems(prev => [newItem, ...prev]);
    setIsLoading(false);
    return newItem;
  }, [isAuthenticated, token]);

  const updateItem = useCallback(async (
    itemId: number,
    data: FollowUpItemUpdateInput,
  ): Promise<FollowUpItem | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setError(null);

    const { data: updated, error: apiError, ok } = await apiPut<FollowUpItem>(
      `/follow-up-items/${itemId}`,
      token,
      data as unknown as Record<string, unknown>,
    );

    if (!ok || !updated) {
      setError(apiError || 'Failed to update follow-up item');
      return null;
    }

    setItems(prev => prev.map(item => item.id === itemId ? updated : item));
    return updated;
  }, [isAuthenticated, token]);

  const deleteItem = useCallback(async (itemId: number): Promise<boolean> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return false;
    }

    setError(null);

    const { error: apiError, ok } = await apiDelete(`/follow-up-items/${itemId}`, token);

    if (!ok) {
      setError(apiError || 'Failed to delete follow-up item');
      return false;
    }

    setItems(prev => prev.filter(item => item.id !== itemId));
    return true;
  }, [isAuthenticated, token]);

  const fetchSummary = useCallback(async (
    engagementId: number,
  ): Promise<FollowUpSummary | null> => {
    if (!isAuthenticated || !token) {
      return null;
    }

    const { data, ok } = await apiGet<FollowUpSummary>(
      `/engagements/${engagementId}/follow-up-items/summary`,
      token,
      { skipCache: true },
    );

    if (!ok || !data) {
      return null;
    }

    setSummary(data);
    return data;
  }, [isAuthenticated, token]);

  return {
    items,
    summary,
    isLoading,
    error,
    fetchItems,
    createItem,
    updateItem,
    deleteItem,
    fetchSummary,
  };
}
