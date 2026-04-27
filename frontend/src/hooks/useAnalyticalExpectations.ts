/**
 * Sprint 728b — useAnalyticalExpectations hook (ISA 520).
 *
 * Mirrors useFollowUpItems pattern — engagement-scoped list/create
 * + item-scoped update/archive.
 */

'use client';

import { useState, useCallback } from 'react';
import { useAuthSession } from '@/contexts/AuthSessionContext';
import type {
  AnalyticalExpectation,
  AnalyticalExpectationListResponse,
  AnalyticalExpectationCreateInput,
  AnalyticalExpectationUpdateInput,
} from '@/types/analytical-expectations';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/utils';

export interface UseAnalyticalExpectationsReturn {
  items: AnalyticalExpectation[];
  totalCount: number;
  isLoading: boolean;
  error: string | null;
  fetchItems: (engagementId: number, resultStatus?: string, targetType?: string) => Promise<void>;
  createItem: (
    engagementId: number,
    data: AnalyticalExpectationCreateInput,
  ) => Promise<AnalyticalExpectation | null>;
  updateItem: (
    expectationId: number,
    data: AnalyticalExpectationUpdateInput,
  ) => Promise<AnalyticalExpectation | null>;
  archiveItem: (expectationId: number) => Promise<boolean>;
}

export function useAnalyticalExpectations(): UseAnalyticalExpectationsReturn {
  const { token, isAuthenticated } = useAuthSession();

  const [items, setItems] = useState<AnalyticalExpectation[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(
    async (engagementId: number, resultStatus?: string, targetType?: string) => {
      if (!isAuthenticated || !token) {
        setItems([]);
        setTotalCount(0);
        return;
      }

      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (resultStatus) params.append('result_status', resultStatus);
      if (targetType) params.append('target_type', targetType);
      const qs = params.toString();
      const url = `/engagements/${engagementId}/analytical-expectations${qs ? `?${qs}` : ''}`;

      const { data, error: apiError, ok } = await apiGet<AnalyticalExpectationListResponse>(
        url,
        token,
        { skipCache: true },
      );

      if (!ok) {
        setError(apiError || 'Failed to load expectations');
        setItems([]);
        setTotalCount(0);
      } else if (data) {
        setItems(data.items);
        setTotalCount(data.total_count);
      }
      setIsLoading(false);
    },
    [token, isAuthenticated],
  );

  const createItem = useCallback(
    async (
      engagementId: number,
      data: AnalyticalExpectationCreateInput,
    ): Promise<AnalyticalExpectation | null> => {
      if (!token) return null;
      const url = `/engagements/${engagementId}/analytical-expectations`;
      const { data: created, error: apiError, ok } = await apiPost<AnalyticalExpectation>(
        url,
        token,
        data,
      );
      if (!ok) {
        setError(apiError || 'Failed to create expectation');
        return null;
      }
      if (created) {
        setItems(prev => [...prev, created]);
        setTotalCount(prev => prev + 1);
      }
      return created ?? null;
    },
    [token],
  );

  const updateItem = useCallback(
    async (
      expectationId: number,
      data: AnalyticalExpectationUpdateInput,
    ): Promise<AnalyticalExpectation | null> => {
      if (!token) return null;
      const url = `/analytical-expectations/${expectationId}`;
      const { data: updated, error: apiError, ok } = await apiPatch<AnalyticalExpectation>(
        url,
        token,
        data,
      );
      if (!ok) {
        setError(apiError || 'Failed to update expectation');
        return null;
      }
      if (updated) {
        setItems(prev => prev.map(i => (i.id === expectationId ? updated : i)));
      }
      return updated ?? null;
    },
    [token],
  );

  const archiveItem = useCallback(
    async (expectationId: number): Promise<boolean> => {
      if (!token) return false;
      const { ok, error: apiError } = await apiDelete(
        `/analytical-expectations/${expectationId}`,
        token,
      );
      if (!ok) {
        setError(apiError || 'Failed to delete expectation');
        return false;
      }
      setItems(prev => prev.filter(i => i.id !== expectationId));
      setTotalCount(prev => Math.max(0, prev - 1));
      return true;
    },
    [token],
  );

  return {
    items,
    totalCount,
    isLoading,
    error,
    fetchItems,
    createItem,
    updateItem,
    archiveItem,
  };
}
